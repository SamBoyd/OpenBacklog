import asyncio
import logging
import math
import os
import time
from datetime import datetime, timezone
from textwrap import dedent
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from src.accounting.billing_service import BillingService
from src.accounting.billing_state_machine import AccountStatusResponse
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.accounting.openmeter_service import OpenMeterService

logger = logging.getLogger(__name__)

LITELLM_LOG_LEVEL = os.getenv("LITELLM_LOG_LEVEL", "INFO")
if LITELLM_LOG_LEVEL == "DEBUG":
    logger.setLevel(logging.DEBUG)

logger.info(f"LITELLM_LOG_LEVEL: {LITELLM_LOG_LEVEL}")
logger.info(f"litellm log level: {logger.getEffectiveLevel()}")

logger.debug("test debug log line")
# Configuration
SYNC_INTERVAL_SECONDS = 60  # Run every minute


COST_PRECISION = 7  # 7 decimal places for cost precision


class UsageTracker:
    def __init__(
        self,
        openmeter_service: OpenMeterService,
        db_session: sessionmaker[Session],
    ):
        self.openmeter = openmeter_service
        self.db_session = db_session
        self.running = False

    def get_active_users(self) -> List[UserAccountDetails]:
        """Get all users with ACTIVE or LOW_BALANCE status."""
        session: Session = self.db_session()
        try:
            stmt = select(UserAccountDetails).where(
                UserAccountDetails.status.in_(
                    [
                        UserAccountStatus.ACTIVE_SUBSCRIPTION,
                        UserAccountStatus.METERED_BILLING,
                        UserAccountStatus.SUSPENDED,
                    ]
                )
            )
            return list(session.scalars(stmt).all())
        finally:
            session.close()

    def _format_rfc3339(self, dt: Optional[datetime]) -> Optional[str]:
        """Format datetime to RFC 3339 format with 'Z' suffix for UTC."""
        if dt is None:
            return None

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

            # Format to RFC 3339 with 'Z' suffix
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _round_cost_to_precision(self, cost: float) -> float:
        """Round up cost to the precision specified by COST_PRECISION."""
        exp = 10**COST_PRECISION
        return math.ceil(cost * exp) / exp

    def get_current_usage_cost(
        self,
        user_id: str,
        meter_slug: str,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
    ) -> float:
        """Query OpenMeter for current cumulative cost in cents"""
        try:
            # Convert the provided datetimes to RFC 3339 format expected by the
            # OpenMeter API. If the value is already a string we assume it is in
            # the correct RFC 3339 format.
            iso_from = self._format_rfc3339(from_time)
            iso_to = self._format_rfc3339(to_time)

            # Build arguments dynamically so that we only include ``to_time`` if it
            # was explicitly provided.  This keeps unit-tests that assert on
            # specific keyword arguments working as before when ``to_time`` is not
            # supplied.
            query_kwargs = {
                "subject": user_id,
                "meter_slug": meter_slug,
                "from_time": iso_from,
                "to_time": iso_to,
                "window_size": "MINUTE",  # Finer granularity for partial-day usage
            }

            usage_result = self.openmeter.query_usage(**query_kwargs)

            # Sum up all usage data points to get total
            total_cost_dollars = 0
            for data_point in usage_result.data:
                if "value" in data_point:
                    total_cost_dollars += data_point["value"]

            total_cost_cents = self._round_cost_to_precision(total_cost_dollars * 100)

            logger.debug(
                dedent(
                    f"""
                        openmeter query for user {user_id}
                        meter {meter_slug}
                        from {iso_from} 
                        to {iso_to}
                        total cost in cents: {total_cost_cents}
                        data: {usage_result.data}
                    """
                )
            )

            return total_cost_cents
        except Exception as e:
            logger.error(
                f"Failed to query usage for user {user_id}, meter {meter_slug}: {e}"
            )
            return 0

    def process_user_usage(self, user_account_details: UserAccountDetails) -> bool:
        """Process usage for a single user. Returns True if state changed."""
        # Store user_id early to avoid detached instance issues
        user_id = str(user_account_details.user_id)
        # user = user_account_details.user

        try:
            # Capture a single timestamp for the query window
            query_end_time = datetime.now(timezone.utc)

            # Query the cost meter directly
            current_total_cost: float = self.get_current_usage_cost(
                user_id,
                "cost_total",
                from_time=user_account_details.last_usage_query_time,
                to_time=query_end_time,
            )

            # "current_total_cost" already represents the amount of **new** usage
            # (in cents) accrued since the last time we ran because the query window
            # is built from ``user.last_usage_query_time`` (exclusive) up to the
            # current time (inclusive). Therefore no further delta calculation is
            # required – the value returned from ``get_current_usage_cost`` *is* the
            # incremental cost we need to record.

            incremental_cost_cents: float = current_total_cost

            if incremental_cost_cents <= 0:
                logger.debug(f"No new usage for user {user_id}")
                return False

            logger.info(
                f"Processing usage for user {user_id}: {incremental_cost_cents} cents"
            )

            # Get a new session for this operation
            session = self.db_session()
            try:
                # Store initial state for comparison
                initial_status = user_account_details.status

                # Get the User object fresh from the current session to avoid detached instance issues
                from src.models import User

                user = session.get(User, user_account_details.user_id)
                if not user:
                    raise ValueError(f"User {user_id} not found")

                # Use BillingService to record usage with proper state management
                billing_service = BillingService(session)
                # Use a composite external id to avoid collisions if we ever query
                # additional meters in the future.
                formatted_amount = self._round_cost_to_precision(incremental_cost_cents)
                external_id = f"cost_total:{formatted_amount}"

                # Record usage through billing service (handles state transitions automatically)
                updated_account: UserAccountDetails = billing_service.record_usage(
                    user=user,
                    amount_cents=incremental_cost_cents,
                    external_id=external_id,
                )

                # Update usage tracking fields – accumulate total cost so we still
                # have a running tally available for analytics/debugging purposes.
                updated_account.last_total_cost = (
                    user_account_details.last_total_cost or 0
                ) + incremental_cost_cents
                updated_account.last_usage_query_time = query_end_time

                session.merge(updated_account)
                session.commit()

                # Check if state changed
                state_changed = initial_status != updated_account.status
                if state_changed:
                    logger.warning(
                        f"User {user_id} state changed from {initial_status} to {updated_account.status} (balance: ${updated_account.balance_cents/100:.2f})"
                    )

                return state_changed

            except Exception as e:
                session.rollback()
                logger.exception(f"Failed to update usage for user {user_id}: {e}")
                raise
            finally:
                session.close()

        except Exception as e:
            logger.exception(f"Error processing usage for user {user_id}: {e}")
            return False

    def sync_usage_once(self) -> None:
        """Run a single sync cycle for all active users."""
        logger.info("Starting usage sync cycle")
        start_time = time.time()

        active_users = self.get_active_users()
        logger.info(f"Found {len(active_users)} active users to sync")

        users_with_state_change = 0
        total_processed = 0

        for user in active_users:
            try:
                state_changed = self.process_user_usage(user)
                if state_changed:
                    users_with_state_change += 1
                total_processed += 1
            except Exception as e:
                logger.error(f"Failed to process user {user.user_id}: {e}")

        elapsed = time.time() - start_time
        logger.info(
            f"Usage sync completed: {total_processed} users processed, "
            f"{users_with_state_change} state changes, {elapsed:.2f}s elapsed"
        )

    async def run_continuous(
        self, interval_seconds: int = SYNC_INTERVAL_SECONDS
    ) -> None:
        """Run the usage tracker continuously."""
        self.running = True
        logger.info(
            f"Starting continuous usage tracking (interval: {interval_seconds}s)"
        )

        while self.running:
            try:
                self.sync_usage_once()
            except Exception as e:
                logger.error(f"Error in usage sync cycle: {e}")

            await asyncio.sleep(interval_seconds)

        logger.info("Usage tracker stopped")

    def stop(self) -> None:
        """Stop the continuous usage tracking."""
        self.running = False
