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
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    set_operation_context,
    set_user_context,
    track_ai_metrics,
)

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
        add_breadcrumb(
            "Retrieving active users for usage tracking",
            category="usage_tracker.users",
        )

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
            active_users = list(session.scalars(stmt).all())

            add_breadcrumb(
                f"Found {len(active_users)} active users",
                category="usage_tracker.users",
                data={"user_count": len(active_users)},
            )

            track_ai_metrics("usage_tracker.active_users.count", len(active_users))

            return active_users

        except Exception as e:
            add_breadcrumb(
                "Failed to retrieve active users",
                category="usage_tracker.users",
                level="error",
                data={"error": str(e)},
            )

            capture_ai_exception(
                e,
                operation_type="usage_tracker_get_active_users",
                extra_context={"method": "get_active_users"},
            )

            track_ai_metrics("usage_tracker.active_users.error", 1)
            raise
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
        start_time = time.time()

        add_breadcrumb(
            f"Querying OpenMeter usage for user {user_id}",
            category="usage_tracker.openmeter",
            data={
                "user_id": user_id,
                "meter_slug": meter_slug,
                "from_time": str(from_time) if from_time else None,
                "to_time": str(to_time) if to_time else None,
            },
        )

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
            data_points_count = len(usage_result.data)
            for data_point in usage_result.data:
                if "value" in data_point:
                    total_cost_dollars += data_point["value"]

            total_cost_cents = self._round_cost_to_precision(total_cost_dollars * 100)

            # Calculate query duration
            query_duration_ms = (time.time() - start_time) * 1000

            add_breadcrumb(
                f"OpenMeter query successful for user {user_id}",
                category="usage_tracker.openmeter",
                data={
                    "user_id": user_id,
                    "total_cost_cents": total_cost_cents,
                    "data_points": data_points_count,
                    "duration_ms": query_duration_ms,
                },
            )

            track_ai_metrics(
                "usage_tracker.openmeter.query.success",
                1,
                tags={"meter_slug": meter_slug},
            )
            track_ai_metrics(
                "usage_tracker.openmeter.query.duration_ms", query_duration_ms
            )
            track_ai_metrics(
                "usage_tracker.openmeter.query.cost_cents", total_cost_cents
            )

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
            query_duration_ms = (time.time() - start_time) * 1000

            logger.error(
                f"Failed to query usage for user {user_id}, meter {meter_slug}: {e}"
            )

            add_breadcrumb(
                f"OpenMeter query failed for user {user_id}",
                category="usage_tracker.openmeter",
                level="error",
                data={
                    "user_id": user_id,
                    "meter_slug": meter_slug,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": query_duration_ms,
                },
            )

            capture_ai_exception(
                e,
                operation_type="usage_tracker_openmeter_query",
                extra_context={
                    "user_id": user_id,
                    "meter_slug": meter_slug,
                    "from_time": str(from_time) if from_time else None,
                    "to_time": str(to_time) if to_time else None,
                },
            )

            track_ai_metrics(
                "usage_tracker.openmeter.query.error",
                1,
                tags={
                    "meter_slug": meter_slug,
                    "error_type": type(e).__name__,
                },
            )

            return 0

    def process_user_usage(self, user_account_details: UserAccountDetails) -> bool:
        """Process usage for a single user. Returns True if state changed."""
        # Store user_id early to avoid detached instance issues
        user_id = str(user_account_details.user_id)
        start_time = time.time()

        add_breadcrumb(
            f"Processing usage for user {user_id}",
            category="usage_tracker.user_processing",
            data={
                "user_id": user_id,
                "current_status": (
                    user_account_details.status.value
                    if user_account_details.status
                    else "unknown"
                ),
                "last_query_time": (
                    str(user_account_details.last_usage_query_time)
                    if user_account_details.last_usage_query_time
                    else None
                ),
            },
        )

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
                add_breadcrumb(
                    f"No new usage for user {user_id}",
                    category="usage_tracker.user_processing",
                    data={
                        "user_id": user_id,
                        "incremental_cost_cents": incremental_cost_cents,
                    },
                )
                track_ai_metrics("usage_tracker.user_processing.no_usage", 1)
                return False

            logger.info(
                f"Processing usage for user {user_id}: {incremental_cost_cents} cents"
            )

            add_breadcrumb(
                f"Processing {incremental_cost_cents} cents usage for user {user_id}",
                category="usage_tracker.user_processing",
                data={
                    "user_id": user_id,
                    "incremental_cost_cents": incremental_cost_cents,
                },
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

                # Set user context for monitoring
                set_user_context(user)

                # Use BillingService to record usage with proper state management
                billing_service = BillingService(session)
                # Use a composite external id to avoid collisions if we ever query
                # additional meters in the future.
                formatted_amount = self._round_cost_to_precision(incremental_cost_cents)
                external_id = f"cost_total:{formatted_amount}"

                add_breadcrumb(
                    f"Recording usage through billing service for user {user_id}",
                    category="usage_tracker.billing",
                    data={
                        "user_id": user_id,
                        "amount_cents": incremental_cost_cents,
                        "external_id": external_id,
                        "initial_status": (
                            initial_status.value if initial_status else "unknown"
                        ),
                    },
                )

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

                    add_breadcrumb(
                        f"User {user_id} account status changed",
                        category="usage_tracker.state_change",
                        level="warning",
                        data={
                            "user_id": user_id,
                            "old_status": (
                                initial_status.value if initial_status else "unknown"
                            ),
                            "new_status": (
                                updated_account.status.value
                                if updated_account.status
                                else "unknown"
                            ),
                            "balance_cents": updated_account.balance_cents,
                            "incremental_cost_cents": incremental_cost_cents,
                        },
                    )

                    track_ai_metrics(
                        "usage_tracker.user_processing.state_changed",
                        1,
                        tags={
                            "old_status": (
                                initial_status.value if initial_status else "unknown"
                            ),
                            "new_status": (
                                updated_account.status.value
                                if updated_account.status
                                else "unknown"
                            ),
                        },
                    )

                # Calculate processing duration
                processing_duration_ms = (time.time() - start_time) * 1000

                add_breadcrumb(
                    f"User {user_id} processing completed successfully",
                    category="usage_tracker.user_processing",
                    data={
                        "user_id": user_id,
                        "state_changed": state_changed,
                        "final_status": (
                            updated_account.status.value
                            if updated_account.status
                            else "unknown"
                        ),
                        "duration_ms": processing_duration_ms,
                    },
                )

                track_ai_metrics(
                    "usage_tracker.user_processing.success",
                    1,
                    tags={
                        "state_changed": "true" if state_changed else "false",
                        "final_status": (
                            updated_account.status.value
                            if updated_account.status
                            else "unknown"
                        ),
                    },
                )
                track_ai_metrics(
                    "usage_tracker.user_processing.duration_ms", processing_duration_ms
                )
                track_ai_metrics(
                    "usage_tracker.user_processing.cost_processed_cents",
                    incremental_cost_cents,
                )

                return state_changed

            except Exception as e:
                session.rollback()
                logger.exception(f"Failed to update usage for user {user_id}: {e}")

                add_breadcrumb(
                    f"Database transaction failed for user {user_id}",
                    category="usage_tracker.user_processing",
                    level="error",
                    data={
                        "user_id": user_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "incremental_cost_cents": incremental_cost_cents,
                    },
                )

                capture_ai_exception(
                    e,
                    operation_type="usage_tracker_user_processing_db",
                    extra_context={
                        "user_id": user_id,
                        "incremental_cost_cents": incremental_cost_cents,
                        "operation": "database_transaction",
                    },
                )

                track_ai_metrics(
                    "usage_tracker.user_processing.db_error",
                    1,
                    tags={"error_type": type(e).__name__},
                )

                raise
            finally:
                session.close()

        except Exception as e:
            logger.exception(f"Error processing usage for user {user_id}: {e}")

            processing_duration_ms = (time.time() - start_time) * 1000

            add_breadcrumb(
                f"User {user_id} processing failed",
                category="usage_tracker.user_processing",
                level="error",
                data={
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": processing_duration_ms,
                },
            )

            capture_ai_exception(
                e,
                operation_type="usage_tracker_user_processing",
                extra_context={
                    "user_id": user_id,
                    "operation": "process_user_usage",
                },
            )

            track_ai_metrics(
                "usage_tracker.user_processing.error",
                1,
                tags={"error_type": type(e).__name__},
            )

            return False

    def sync_usage_once(self) -> None:
        """Run a single sync cycle for all active users."""
        logger.info("Starting usage sync cycle")
        start_time = time.time()

        # Set operation context for this sync cycle
        set_operation_context(
            "usage_tracker_sync_cycle",
            details={"sync_type": "single_cycle"},
        )

        add_breadcrumb(
            "Starting usage sync cycle",
            category="usage_tracker.sync",
        )

        track_ai_metrics("usage_tracker.sync_cycle.started", 1)

        try:
            active_users = self.get_active_users()
            logger.info(f"Found {len(active_users)} active users to sync")

            users_with_state_change = 0
            total_processed = 0
            users_with_errors = 0

            for user in active_users:
                try:
                    state_changed = self.process_user_usage(user)
                    if state_changed:
                        users_with_state_change += 1
                    total_processed += 1
                except Exception as e:
                    logger.error(f"Failed to process user {user.user_id}: {e}")
                    users_with_errors += 1

                    add_breadcrumb(
                        f"Failed to process user {user.user_id}",
                        category="usage_tracker.sync",
                        level="error",
                        data={
                            "user_id": str(user.user_id),
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )

                    track_ai_metrics(
                        "usage_tracker.sync_cycle.user_error",
                        1,
                        tags={"error_type": type(e).__name__},
                    )

            elapsed = time.time() - start_time
            logger.info(
                f"Usage sync completed: {total_processed} users processed, "
                f"{users_with_state_change} state changes, {elapsed:.2f}s elapsed"
            )

            # Add comprehensive summary breadcrumb
            add_breadcrumb(
                "Usage sync cycle completed",
                category="usage_tracker.sync",
                data={
                    "total_active_users": len(active_users),
                    "total_processed": total_processed,
                    "users_with_state_change": users_with_state_change,
                    "users_with_errors": users_with_errors,
                    "duration_seconds": elapsed,
                    "success_rate": (
                        (total_processed - users_with_errors) / len(active_users)
                        if len(active_users) > 0
                        else 1.0
                    ),
                },
            )

            # Track comprehensive metrics
            track_ai_metrics("usage_tracker.sync_cycle.completed", 1)
            track_ai_metrics("usage_tracker.sync_cycle.duration_seconds", elapsed)
            track_ai_metrics("usage_tracker.sync_cycle.users_total", len(active_users))
            track_ai_metrics(
                "usage_tracker.sync_cycle.users_processed", total_processed
            )
            track_ai_metrics(
                "usage_tracker.sync_cycle.users_state_changed", users_with_state_change
            )
            track_ai_metrics("usage_tracker.sync_cycle.users_errors", users_with_errors)

            # Calculate and track success rate
            success_rate = (
                (total_processed - users_with_errors) / len(active_users)
                if len(active_users) > 0
                else 1.0
            )
            track_ai_metrics("usage_tracker.sync_cycle.success_rate", success_rate)

            set_operation_context(
                "usage_tracker_sync_cycle",
                details={
                    "total_users": len(active_users),
                    "processed_users": total_processed,
                    "state_changes": users_with_state_change,
                    "errors": users_with_errors,
                    "duration_seconds": elapsed,
                },
                duration_ms=elapsed * 1000,
                success=True,
            )

        except Exception as e:
            elapsed = time.time() - start_time

            logger.exception(f"Usage sync cycle failed: {e}")

            add_breadcrumb(
                "Usage sync cycle failed",
                category="usage_tracker.sync",
                level="error",
                data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_seconds": elapsed,
                },
            )

            capture_ai_exception(
                e,
                operation_type="usage_tracker_sync_cycle",
                extra_context={
                    "sync_type": "single_cycle",
                    "duration_seconds": elapsed,
                },
            )

            track_ai_metrics(
                "usage_tracker.sync_cycle.failed",
                1,
                tags={"error_type": type(e).__name__},
            )

            set_operation_context(
                "usage_tracker_sync_cycle",
                duration_ms=elapsed * 1000,
                success=False,
            )

            # Re-raise the exception to maintain existing behavior
            raise

    async def run_continuous(
        self, interval_seconds: int = SYNC_INTERVAL_SECONDS
    ) -> None:
        """Run the usage tracker continuously."""
        self.running = True
        logger.info(
            f"Starting continuous usage tracking (interval: {interval_seconds}s)"
        )

        # Set operation context for continuous running
        set_operation_context(
            "usage_tracker_continuous",
            details={
                "interval_seconds": interval_seconds,
                "mode": "continuous",
            },
        )

        add_breadcrumb(
            "Starting continuous usage tracking",
            category="usage_tracker.continuous",
            data={"interval_seconds": interval_seconds},
        )

        track_ai_metrics(
            "usage_tracker.continuous.started",
            1,
            tags={"interval": str(interval_seconds)},
        )

        cycle_count = 0

        while self.running:
            cycle_start_time = time.time()
            cycle_count += 1

            add_breadcrumb(
                f"Starting sync cycle #{cycle_count}",
                category="usage_tracker.continuous",
                data={"cycle_number": cycle_count},
            )

            try:
                self.sync_usage_once()

                cycle_duration = time.time() - cycle_start_time
                add_breadcrumb(
                    f"Sync cycle #{cycle_count} completed successfully",
                    category="usage_tracker.continuous",
                    data={
                        "cycle_number": cycle_count,
                        "cycle_duration_seconds": cycle_duration,
                    },
                )

                track_ai_metrics(
                    "usage_tracker.continuous.cycle_completed",
                    1,
                    tags={"cycle_number": str(cycle_count)},
                )

            except Exception as e:
                cycle_duration = time.time() - cycle_start_time
                logger.error(f"Error in usage sync cycle: {e}")

                add_breadcrumb(
                    f"Sync cycle #{cycle_count} failed",
                    category="usage_tracker.continuous",
                    level="error",
                    data={
                        "cycle_number": cycle_count,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "cycle_duration_seconds": cycle_duration,
                    },
                )

                capture_ai_exception(
                    e,
                    operation_type="usage_tracker_continuous_cycle",
                    extra_context={
                        "cycle_number": cycle_count,
                        "interval_seconds": interval_seconds,
                        "cycle_duration_seconds": cycle_duration,
                    },
                )

                track_ai_metrics(
                    "usage_tracker.continuous.cycle_error",
                    1,
                    tags={
                        "error_type": type(e).__name__,
                        "cycle_number": str(cycle_count),
                    },
                )

            # Sleep before next cycle
            add_breadcrumb(
                f"Waiting {interval_seconds}s before next cycle",
                category="usage_tracker.continuous",
                data={
                    "interval_seconds": interval_seconds,
                    "next_cycle": cycle_count + 1,
                },
            )

            await asyncio.sleep(interval_seconds)

        logger.info("Usage tracker stopped")

        add_breadcrumb(
            "Continuous usage tracking stopped",
            category="usage_tracker.continuous",
            data={
                "total_cycles": cycle_count,
                "final_state": "stopped_gracefully",
            },
        )

        track_ai_metrics(
            "usage_tracker.continuous.stopped",
            1,
            tags={"total_cycles": str(cycle_count)},
        )

        set_operation_context(
            "usage_tracker_continuous",
            details={
                "total_cycles": cycle_count,
                "final_state": "stopped_gracefully",
            },
            success=True,
        )

    def stop(self) -> None:
        """Stop the continuous usage tracking."""
        self.running = False
