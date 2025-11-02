"""
Billing Command Handlers for Event-Sourced Architecture.

This module implements command handlers that coordinate between the billing state machine
and event persistence, following the command pattern in event-sourced systems.

Command handlers are responsible for:
1. Loading current FSM state from event history
2. Generating new events via FSM methods
3. Persisting events atomically with optimistic concurrency
4. Updating denormalized views for fast queries
"""

import logging
import uuid
from datetime import datetime
from typing import Callable, Optional, Sequence

from sqlalchemy.orm import Session

from .billing_events import BillingEvent
from .billing_state_machine import BillingFSMInvalidTransitionError, BillingStateMachine
from .event_store import EventStore, OptimisticConcurrencyError
from .models import UserAccountDetails, UserAccountStatus

logger = logging.getLogger(__name__)


class BillingCommandError(Exception):
    """Base exception for billing command processing errors."""

    pass


class BillingCommandHandler:
    """
    Command handler for billing operations in event-sourced architecture.

    This class orchestrates the flow from commands → events → persistence,
    ensuring atomic operations and maintaining consistency between the event
    store and denormalized views.
    """

    def __init__(self, event_store: EventStore, db: Session):
        """
        Initialize command handler.

        Args:
            event_store: Event store for persisting and retrieving events
            db: Database session for updating denormalized views
        """
        self.event_store = event_store
        self.db = db

    def _execute_command(
        self,
        user_id: uuid.UUID,
        fsm_operation: Callable[[BillingStateMachine], Sequence[BillingEvent]],
        operation_name: str,
        success_message: str,
        log_level: str = "info",
    ) -> None:
        """
        Template method for executing billing commands.

        Handles the common workflow for all command operations:
        1. Reconstruct FSM from events
        2. Execute FSM operation to generate events
        3. Save events atomically with optimistic concurrency
        4. Update denormalized account details
        5. Log success and handle errors consistently

        Args:
            user_id: User ID to execute command for
            fsm_operation: Lambda that takes FSM and returns events
            operation_name: Human-readable operation name for error messages
            success_message: Success message template with {user_id} placeholder
            log_level: Log level for success message ("info" or "warning")

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If FSM operation is not valid
        """
        try:
            # Load current FSM state from events
            fsm = self._reconstruct_fsm(user_id)

            # Generate events via FSM operation
            events = fsm_operation(fsm)

            # Save events atomically
            self.event_store.save_events(user_id, list(events), fsm.version)

            # Update denormalized account details
            self._update_account_details(user_id)

            # Log success
            if log_level == "warning":
                logger.warning(success_message.format(user_id=user_id))
            else:
                logger.info(success_message.format(user_id=user_id))

        except BillingFSMInvalidTransitionError:
            # Re-raise FSM validation errors as-is
            raise
        except OptimisticConcurrencyError as e:
            raise BillingCommandError(
                f"Concurrency conflict {operation_name}: {e}"
            ) from e
        except Exception as e:
            raise BillingCommandError(f"Failed to {operation_name}: {e}") from e

    def handle_record_usage(
        self, user_id: uuid.UUID, amount_cents: float, external_id: str
    ) -> None:
        """
        Handle usage recording command.

        Args:
            user_id: User ID to record usage for
            amount_cents: Usage amount in cents
            external_id: External reference (e.g., AI request ID)

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If usage recording is not valid
        """
        self._execute_command(
            user_id=user_id,
            fsm_operation=lambda fsm: fsm.record_usage(amount_cents, external_id),
            operation_name="record usage",
            success_message=f"Successfully recorded usage of {amount_cents} cents for user {{user_id}}",
        )

    def handle_topup_balance(
        self,
        user_id: uuid.UUID,
        amount_cents: int,
        external_id: str,
        invoice_download_url: Optional[str] = None,
    ) -> None:
        """
        Handle balance top-up command.

        Args:
            user_id: User ID to top up balance for
            amount_cents: Amount to add in cents
            external_id: External reference (e.g., Stripe payment intent ID)
            invoice_download_url: Optional URL for invoice download

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If top-up is not valid
        """
        self._execute_command(
            user_id=user_id,
            fsm_operation=lambda fsm: fsm.topup_usage_balance(
                amount_cents, external_id, invoice_download_url
            ),
            operation_name="topping up balance",
            success_message=f"Successfully topped up {amount_cents} cents for user {{user_id}}",
        )

    def handle_signup_subscription(
        self, user_id: uuid.UUID, external_id: str = "manual"
    ) -> None:
        """
        Handle subscription signup command.

        Args:
            user_id: User ID to sign up for subscription
            external_id: External reference (e.g., Stripe subscription ID)

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If signup is not valid
        """
        self._execute_command(
            user_id=user_id,
            fsm_operation=lambda fsm: fsm.signup_subscription(external_id),
            operation_name="signing up subscription",
            success_message=f"Successfully signed up subscription for user {{user_id}}",
        )

    def handle_cancel_subscription(
        self,
        user_id: uuid.UUID,
        external_id: str = "manual",
        reason: str = "USER_REQUESTED",
    ) -> None:
        """
        Handle subscription cancellation command.

        Args:
            user_id: User ID to cancel subscription for
            external_id: External reference (e.g., cancellation ID)
            reason: Reason for cancellation

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If cancellation is not valid
        """
        self._execute_command(
            user_id=user_id,
            fsm_operation=lambda fsm: fsm.cancel_subscription(external_id, reason),
            operation_name="cancelling subscription",
            success_message=f"Successfully cancelled subscription for user {{user_id}}",
        )

    def handle_skip_subscription(
        self, user_id: uuid.UUID, external_id: str = "onboarding"
    ) -> None:
        """
        Handle skipping subscription command (free tier onboarding).

        Transitions NEW → NO_SUBSCRIPTION for users who complete onboarding
        without signing up for a paid subscription.

        Args:
            user_id: User ID to skip subscription for
            external_id: External reference (e.g., onboarding completion ID)

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If skip is not valid
        """
        self._execute_command(
            user_id=user_id,
            fsm_operation=lambda fsm: fsm.skip_subscription(external_id),
            operation_name="skipping subscription",
            success_message=f"Successfully skipped subscription for user {{user_id}}",
        )

    def handle_start_billing_cycle(self, user_id: uuid.UUID) -> None:
        """
        Handle billing cycle start command.

        Args:
            user_id: User ID to start new billing cycle for

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If cycle start is not valid
        """
        self._execute_command(
            user_id=user_id,
            fsm_operation=lambda fsm: fsm.start_new_billing_cycle(),
            operation_name="starting billing cycle",
            success_message=f"Successfully started new billing cycle for user {{user_id}}",
        )

    def handle_detect_chargeback(
        self, user_id: uuid.UUID, external_id: str = "chargeback", amount_cents: int = 0
    ) -> None:
        """
        Handle chargeback detection command.

        Args:
            user_id: User ID where chargeback was detected
            external_id: External reference (e.g., Stripe chargeback ID)
            amount_cents: Amount of the chargeback

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If chargeback handling is not valid
        """
        self._execute_command(
            user_id=user_id,
            fsm_operation=lambda fsm: fsm.detect_chargeback(external_id, amount_cents),
            operation_name="processing chargeback",
            success_message=f"Chargeback detected and account closed for user {{user_id}}, amount: {amount_cents}",
            log_level="warning",
        )

    def handle_process_balance_refund(
        self,
        user_id: uuid.UUID,
        amount_cents: float,
        external_id: str = "manual_refund",
        reason: str = "CUSTOMER_REQUEST",
    ) -> None:
        """
        Handle balance refund command.

        Args:
            user_id: User ID to process refund for
            amount_cents: Amount to refund in cents (positive value)
            external_id: External reference for the refund
            reason: Reason for the refund

        Raises:
            BillingCommandError: If command processing fails
            BillingFSMInvalidTransitionError: If refund is not valid
        """
        self._execute_command(
            user_id=user_id,
            fsm_operation=lambda fsm: fsm.process_balance_refund(
                amount_cents, external_id, reason
            ),
            operation_name="processing refund",
            success_message=f"Successfully processed refund of {amount_cents} cents for user {{user_id}}",
        )

    def _reconstruct_fsm(self, user_id: uuid.UUID) -> BillingStateMachine:
        """
        Reconstruct FSM from event history.

        Args:
            user_id: User ID to reconstruct FSM for

        Returns:
            BillingStateMachine with current state applied from events

        Raises:
            BillingCommandError: If FSM reconstruction fails
        """
        try:
            # Get all events for user
            events = self.event_store.get_events_for_user(user_id)

            # Create fresh FSM and apply all events
            fsm = BillingStateMachine(user_id=user_id)
            fsm.apply_events(events)

            return fsm

        except Exception as e:
            raise BillingCommandError(
                f"Failed to reconstruct FSM for user {user_id}: {e}"
            ) from e

    def _update_account_details(self, user_id: uuid.UUID) -> None:
        """
        Update denormalized account details based on generated events.

        This ensures the fast-query denormalized table stays in sync
        with the event store state.

        Args:
            user_id: User ID to update account details for
            events: Events that were just persisted
        """
        try:
            # Get the user's account details record
            account_details = (
                self.db.query(UserAccountDetails)
                .filter(UserAccountDetails.user_id == user_id)
                .first()
            )

            if not account_details:
                logger.warning(f"No account details found for user {user_id}")
                return

            # Reconstruct current FSM state to get latest values
            fsm = self._reconstruct_fsm(user_id)
            account_status = fsm.get_account_status()

            # Update denormalized fields
            account_details.status = account_status.state
            account_details.balance_cents = fsm.usage_balance
            account_details.monthly_credits_used = fsm.monthly_credits_used
            account_details.monthly_credits_total = fsm.monthly_credits_cents

            self.db.add(account_details)
            self.db.commit()

            logger.debug(f"Updated account details for user {user_id}")

        except Exception as e:
            # Log error but don't fail the command - the events are already persisted
            logger.error(f"Failed to update account details for user {user_id}: {e}")
            self.db.rollback()
