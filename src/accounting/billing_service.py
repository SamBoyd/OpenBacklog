import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.accounting.billing_command_handlers import BillingCommandHandler
from src.accounting.billing_query_service import BillingQueryService
from src.accounting.billing_state_machine import (
    AccountStatusResponse,
    BalanceStatusWithPreview,
    UsageImpactSimulation,
)
from src.accounting.event_store import EventStore
from src.accounting.models import PendingTopup, PendingTopupStatus, UserAccountDetails
from src.models import User

logger = logging.getLogger(__name__)


class BillingServiceException(Exception):
    pass


MONTHLY_SUBSCRIPTION_COST = 500


class BillingService:
    """
    Event-driven service for managing user billing accounts and financial transactions.

    The BillingService provides a high-level interface for billing operations using
    an event-sourced architecture. All state changes are handled through command
    handlers that generate domain events, ensuring consistency and auditability.

    Key responsibilities:
    - Processing subscription lifecycle operations (signup, cancel, reactivate)
    - Handling balance management (top-ups, refunds)
    - Recording usage with hybrid billing model (credits + balance)
    - Managing billing cycle resets and chargeback detection
    - Delegating read operations to specialized query services

    The service maintains data integrity by:
    - Using event-sourced command handlers for all write operations
    - Maintaining a complete audit trail through domain events
    - Ensuring atomic operations with optimistic concurrency control
    - Providing fast reads through denormalized views

    Attributes:
        db (Session): SQLAlchemy database session
        event_store (EventStore): Event storage for billing domain events
        command_handler (BillingCommandHandler): Handles all write operations
        query_service (BillingQueryService): Handles all read operations
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_store = EventStore(db)
        self.command_handler = BillingCommandHandler(self.event_store, db)
        self.query_service = BillingQueryService(db)

    # Subscription lifecycle methods
    def signup_subscription(self, user: User, external_id: str) -> UserAccountDetails:
        """
        Create monthly subscription, transition NEW → ACTIVE_SUBSCRIPTION

        Args:
            user: The user to create subscription for
            external_id: External reference ID (e.g., Stripe subscription ID)
        """
        self.command_handler.handle_signup_subscription(user.id, external_id)

        # Return updated account details
        self.db.refresh(user.account_details)
        return user.account_details

    def cancel_subscription(self, user: User, external_id: str) -> UserAccountDetails:
        """
        Cancel subscription, transition ACTIVE_SUBSCRIPTION → NO_SUBSCRIPTION

        Args:
            user: The user to cancel subscription for
            external_id: External reference ID (e.g., cancellation reason)
        """
        self.command_handler.handle_cancel_subscription(user.id, external_id)

        # Return updated account details
        self.db.refresh(user.account_details)
        return user.account_details

    def reactivate_subscription(
        self, user: User, external_id: str
    ) -> UserAccountDetails:
        """
        Reactivate subscription, transition NO_SUBSCRIPTION → ACTIVE_SUBSCRIPTION

        Args:
            user: The user to reactivate subscription for
            external_id: External reference ID (e.g., Stripe subscription ID)
        """
        self.command_handler.handle_signup_subscription(user.id, external_id)

        # Return updated account details
        self.db.refresh(user.account_details)
        return user.account_details

    # Billing cycle management
    def start_new_billing_cycle(self, user: User) -> UserAccountDetails:
        """
        Reset monthly billing cycle, transition METERED_BILLING/SUSPENDED → ACTIVE_SUBSCRIPTION

        Args:
            user: The user to reset billing cycle for
        """
        self.command_handler.handle_start_billing_cycle(user.id)

        # Return updated account details
        self.db.refresh(user.account_details)
        return user.account_details

    # Usage balance (top-up) management
    def topup_balance(
        self,
        user: User,
        amount_cents: int,
        external_id: str,
        invoice_download_url: Optional[str] = None,
    ) -> UserAccountDetails:
        """
        Add usage balance, SUSPENDED → METERED_BILLING if applicable

        Args:
            user: The user to top up balance for
            amount_cents: Amount to add in cents
            external_id: External reference ID
            invoice_download_url: Optional download URL for invoice
        """
        self.command_handler.handle_topup_balance(
            user.id, amount_cents, external_id, invoice_download_url
        )

        # Return updated account details
        self.db.refresh(user.account_details)
        return user.account_details

    def record_usage(
        self, user: User, amount_cents: float, external_id: str
    ) -> UserAccountDetails:
        """
        Record usage with hybrid logic: deducts from included credits first, then from usage balance

        Args:
            user: The user recording usage
            amount_cents: Amount to record as usage (positive value)
            external_id: External reference ID
        """
        self.command_handler.handle_record_usage(user.id, amount_cents, external_id)

        # Return updated account details
        self.db.refresh(user.account_details)
        return user.account_details

    # Refund management
    def process_full_refund(self, user: User, external_id: str) -> UserAccountDetails:
        """
        Full refund - orchestrates both subscription + balance refunds and then cancels the subscription

        Args:
            user: The user to process refund for
            external_id: External reference ID for the refund
        """
        account_details = user.account_details

        # Process both subscription and balance refunds
        if account_details.balance_cents > 0:
            self._refund_balance(user, account_details.balance_cents, external_id)

        return self.cancel_subscription(user, external_id)

    def process_balance_refund(
        self, user: User, external_id: str
    ) -> UserAccountDetails:
        """
        Process balance refund.
        """
        return self._refund_balance(
            user, user.account_details.balance_cents, external_id
        )

    def _refund_balance(
        self, user: User, amount_cents: float, external_id: str
    ) -> UserAccountDetails:
        """
        Internal method for refunding usage balance.

        Args:
            user: The user to refund balance for
            amount_cents: Amount to refund in cents (positive value)
            external_id: External reference ID
        """
        self.command_handler.handle_process_balance_refund(
            user.id, amount_cents, external_id
        )

        # Return updated account details
        self.db.refresh(user.account_details)
        return user.account_details

    def detect_chargeback(self, user: User, external_id: str) -> UserAccountDetails:
        """
        Handle fraud/chargeback detection, transition any state → CLOSED.

        Args:
            user: The user to close account for
            external_id: External reference ID for the chargeback
        """
        self.command_handler.handle_detect_chargeback(user.id, external_id)

        # Return updated account details
        self.db.refresh(user.account_details)
        return user.account_details

    def create_pending_topup(
        self, user_id: uuid.UUID, session_id: str, amount_cents: int
    ) -> PendingTopup:
        """
        Creates a pending top-up record when a user initiates a top-up.

        Args:
            user_id: The UUID of the user
            session_id: The Stripe checkout session ID
            amount_cents: The top-up amount in cents

        Returns:
            PendingTopup: The created pending top-up record
        """
        if amount_cents <= 0:
            raise ValueError("Top-up amount must be positive")

        # Check if a pending top-up already exists for this session
        existing_pending = (
            self.db.query(PendingTopup)
            .filter(PendingTopup.session_id == session_id)
            .first()
        )

        if existing_pending:
            logger.info(f"Pending top-up already exists for session {session_id}")
            return existing_pending

        pending_topup = PendingTopup()
        pending_topup.user_id = user_id  # type: ignore
        pending_topup.session_id = session_id
        pending_topup.amount_cents = amount_cents
        pending_topup.status = PendingTopupStatus.PENDING

        self.db.add(pending_topup)
        self.db.commit()
        self.db.refresh(pending_topup)

        logger.info(
            f"Created pending top-up for user {user_id}: "
            f"session {session_id}, amount {amount_cents} cents"
        )

        return pending_topup

    def process_pending_topup(
        self, session_id: str, download_url: Optional[str], success: bool = True
    ) -> UserAccountDetails:
        """
        Processes a pending top-up when the Stripe webhook confirms payment status.

        Args:
            session_id: The Stripe checkout session ID
            success: Whether the payment was successful (True) or failed (False)
            download_url: Optional download URL for the Stripe invoice

        Returns:
            UserAccountDetails: The updated account details (only for successful payments)

        Raises:
            ValueError: If pending top-up not found or already processed
        """
        pending_topup = (
            self.db.query(PendingTopup)
            .filter(PendingTopup.session_id == session_id)
            .first()
        )

        if not pending_topup:
            raise ValueError(f"No pending top-up found for session {session_id}")

        if pending_topup.status != PendingTopupStatus.PENDING:
            logger.warning(
                f"Pending top-up for session {session_id} already processed "
                f"with status {pending_topup.status}"
            )
            # Return the account details without processing again
            return pending_topup.user.account_details

        try:
            if success:
                # Process the top-up using the existing logic
                account_details = self.topup_balance(
                    user=pending_topup.user,
                    amount_cents=pending_topup.amount_cents,
                    external_id=session_id,
                    invoice_download_url=download_url,
                )

                # Mark the pending top-up as completed
                pending_topup.status = PendingTopupStatus.COMPLETED
                pending_topup.completed_at = datetime.now()

                account_details.balance_cents = (
                    account_details.balance_cents + pending_topup.amount_cents
                )
                self.db.add(account_details)

                logger.info(
                    f"Successfully processed pending top-up for session {session_id}: "
                    f"user {pending_topup.user_id}, amount {pending_topup.amount_cents} cents"
                )

                return account_details
            else:
                # Mark the pending top-up as failed
                pending_topup.status = PendingTopupStatus.FAILED

                logger.info(
                    f"Marked pending top-up as failed for session {session_id}: "
                    f"user {pending_topup.user_id}, amount {pending_topup.amount_cents} cents"
                )

                # Return the account details without any changes
                return pending_topup.user.account_details

        except Exception as e:
            # Mark the pending top-up as failed
            pending_topup.status = PendingTopupStatus.FAILED
            self.db.add(pending_topup)
            self.db.commit()

            logger.error(
                f"Failed to process pending top-up for session {session_id}: {e}"
            )
            raise

        finally:
            # Always save the status change
            self.db.add(pending_topup)
            self.db.commit()

    # Status & analytics methods - delegated to query service
    def get_account_status_detailed(self, user: User) -> AccountStatusResponse:
        """Delegate to query service for account status."""
        return self.query_service.get_account_status_detailed(user)

    def can_afford_request(self, user: User, estimated_cost_cents: float) -> bool:
        """Delegate to query service for affordability check."""
        return self.query_service.can_afford_request(user, estimated_cost_cents)

    def simulate_usage_impact(
        self, user: User, estimated_cost_cents: float
    ) -> UsageImpactSimulation:
        """Delegate to query service for usage impact simulation."""
        return self.query_service.simulate_usage_impact(user, estimated_cost_cents)

    def get_balance_status_with_preview(
        self, user: User, estimated_cost_cents: float
    ) -> BalanceStatusWithPreview:
        """Delegate to query service for balance status with preview."""
        return self.query_service.get_balance_status_with_preview(
            user, estimated_cost_cents
        )
