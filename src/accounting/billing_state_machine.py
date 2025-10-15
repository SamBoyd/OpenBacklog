"""
Event-Sourced Billing State Machine.

This module implements an event-sourced finite state machine for managing billing
account states. Instead of directly mutating state, the FSM generates domain events
that represent all billing operations.
All monetary amounts are stored in cents to avoid floating point precision issues.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from src.accounting.billing_events import (
    BalanceRefundEvent,
    BalanceTopUpEvent,
    BalanceUsageEvent,
    BillingEvent,
    ChargebackDetectedEvent,
    CreditUsageEvent,
    MonthlyCreditsResetEvent,
    StateTransitionEvent,
    SubscriptionCancelEvent,
    SubscriptionSignupEvent,
)
from src.accounting.billing_transitions import billing_fsm_transitions
from src.accounting.models import UserAccountStatus

try:
    from transitions import Machine
except ImportError:
    Machine = None


class BillingFSMInvalidTransitionError(Exception):
    """
    Exception raised when an invalid transition is attempted.
    """

    pass


class BillingStateValidator:
    """
    Validator class that uses pytransitions to validate state transitions.

    This class provides validation for billing state changes without directly
    mutating state, allowing the FSM to remain focused on event generation.
    """

    def __init__(self):
        """Initialize the state validator with pytransitions machine."""
        if Machine is None:
            raise ImportError(
                "pytransitions library is required for BillingStateValidator. "
                "Install with: pip install transitions"
            )

        # Create a simple validation object with just state tracking
        class ValidationState:
            def __init__(self):
                self.state = UserAccountStatus.NEW
                self.usage_balance = 0.0

            def has_usage_balance(self):
                return self.usage_balance > 0

            def has_zero_usage_balance(self):
                return self.usage_balance <= 0

        self.validator_obj = ValidationState()

        # Initialize pytransitions machine for validation
        self.machine = Machine(
            model=self.validator_obj,
            states=list(UserAccountStatus),
            transitions=billing_fsm_transitions,
            initial=UserAccountStatus.NEW,
        )

    def can_transition(
        self, from_state: UserAccountStatus, trigger: str, **kwargs: Any
    ) -> bool:
        """
        Check if a transition is valid.

        Args:
            from_state: Current state
            trigger: Trigger method name
            **kwargs: Additional context (e.g., usage_balance)

        Returns:
            True if transition is valid, False otherwise
        """
        try:
            # Set up validator state
            self.validator_obj.state = from_state
            self.validator_obj.usage_balance = kwargs.get("usage_balance", 0.0)

            # Try the transition on the validator
            trigger_method = getattr(self.validator_obj, trigger, None)
            if trigger_method and callable(trigger_method):
                return trigger_method()
            else:
                return False

        except Exception:
            return False

    def validate_transition(
        self, from_state: UserAccountStatus, trigger: str, **kwargs: Any
    ) -> None:
        """
        Validate a transition and raise an exception if invalid.

        Args:
            from_state: Current state
            trigger: Trigger method name
            **kwargs: Additional context

        Raises:
            BillingFSMInvalidTransitionError: If transition is not valid
        """
        if not self.can_transition(from_state, trigger, **kwargs):
            raise BillingFSMInvalidTransitionError(
                f"Invalid transition: cannot '{trigger}' from state {from_state.value}"
            )


@dataclass
class UsageBreakdown:
    """
    Breakdown of how usage was applied in the hybrid billing model.

    Attributes:
        total_amount: Total usage amount requested
        credits_used: Amount deducted from monthly credits
        balance_used: Amount deducted from usage balance
    """

    total_amount: float
    credits_used: float
    balance_used: float


@dataclass
class AccountStatusResponse:
    """
    Response object for account status information with computed properties.

    Attributes:
        state: Current subscription/billing state
        usage_balance_cents: Current usage balance in cents
        usage_balance_dollars: Current usage balance in dollars
        monthly_credits_cents: Remaining monthly AI credits in cents
        monthly_credits_dollars: Remaining monthly AI credits in dollars
        has_active_subscription: Whether user has any active subscription
        is_suspended: Whether account is suspended due to zero balance
        is_closed: Whether account is permanently closed
        has_usage_balance: Whether user has positive usage balance
        subscription_only: Whether user only has subscription without usage balance
        using_metered_billing: Whether user is in metered billing state
        no_subscription: Whether user has no active subscription
    """

    state: UserAccountStatus
    usage_balance_cents: float
    usage_balance_dollars: float
    monthly_credits_cents: int
    monthly_credits_dollars: float
    has_active_subscription: bool
    is_suspended: bool
    is_closed: bool
    has_usage_balance: bool
    subscription_only: bool
    using_metered_billing: bool
    no_subscription: bool


@dataclass
class EnforcementDecision:
    """
    Decision object for billing enforcement actions.

    Attributes:
        action: The enforcement action to take (allow, reject, allow_with_warning, allow_with_suspension)
        reason: The reason for this decision (sufficient_balance, insufficient_balance, etc.)
        message: Optional user-facing message explaining the decision
    """

    action: str
    reason: str
    message: Optional[str] = None


@dataclass
class UsageImpactSimulation:
    """
    Simulation of usage impact on billing account.

    Attributes:
        current_usage_balance_cents: Current usage balance in cents before the request
        current_status: Current account status before the request
        current_monthly_credits_used: Monthly credits used before the request
        remaining_monthly_credits: Monthly credits remaining before the request
        estimated_cost_cents: The estimated cost of the request in cents
        projected_usage_balance_cents: Projected usage balance after the request
        projected_monthly_credits_used: Projected monthly credits used after the request
        projected_status: Projected account status after the request
        would_be_suspended: Whether the request would suspend the account
        would_be_metered: Whether the request would put account in metered billing
        would_be_low_balance: Whether the request would result in low balance warning
    """

    current_usage_balance_cents: float
    current_status: UserAccountStatus
    current_monthly_credits_used: float
    remaining_monthly_credits: float
    estimated_cost_cents: float
    projected_usage_balance_cents: float
    projected_monthly_credits_used: float
    projected_status: UserAccountStatus
    would_be_suspended: bool
    would_be_metered: bool
    would_be_low_balance: bool


@dataclass
class BalanceStatusWithPreview:
    """
    Comprehensive balance status including preview of request impact.

    Attributes:
        current_status: Current account status details
        usage_impact: Usage simulation results from simulate_usage_impact
        can_afford: Whether the user can afford the estimated request cost
        top_up_needed_cents: Amount needed to top up if request is not affordable (in cents)
        top_up_needed_dollars: Amount needed to top up if request is not affordable (in dollars)
        enforcement_decision: The enforcement decision for this request
    """

    current_status: AccountStatusResponse
    usage_impact: UsageImpactSimulation
    can_afford: bool
    top_up_needed_cents: int
    top_up_needed_dollars: float
    enforcement_decision: EnforcementDecision


@dataclass
class BillingStateMachine:
    """
    Event-sourced billing state machine for subscription-based accounts.

    This FSM generates domain events instead of directly mutating state.
    State is reconstructed by applying events from the event store.

    Attributes:
        user_id: User ID this FSM instance belongs to (required for event generation)
        usage_balance: Current usage balance in cents (computed from events)
        state: Current subscription/billing state (computed from events)
        monthly_credits_cents: AI credits included with monthly subscription (default $5)
        monthly_credits_used: AI credits used this billing cycle (computed from events)
        version: Event version for optimistic concurrency control
        validator: State transition validator
    """

    user_id: uuid.UUID
    usage_balance: float = 0
    state: UserAccountStatus = UserAccountStatus.NEW
    monthly_credits_cents: int = 0  # $5 worth of included AI credits
    monthly_credits_used: int = 0  # Credits used this cycle
    validator: Optional[BillingStateValidator] = None

    def __init__(
        self,
        user_id: uuid.UUID,
        validator: Optional[BillingStateValidator] = None,
        version: int = 0,
    ):
        # Always start from defaults to keep validator and FSM aligned
        self.user_id = user_id
        self.usage_balance = 0
        self.state = UserAccountStatus.NEW
        self.monthly_credits_cents = 0
        self.monthly_credits_used = 0
        self.validator = validator
        self.version = version

        self.__post_init__()

    def __post_init__(self):
        """Initialize the validator after dataclass initialization."""
        if self.validator is None:
            try:
                self.validator = BillingStateValidator()
            except ImportError:
                # If pytransitions is not available, validator will be None
                # and validation will be skipped
                self.validator = None

    def apply_event(self, event: BillingEvent) -> None:
        """
        Apply a single event to update FSM state.

        Args:
            event: The billing event to apply
        """
        if isinstance(event, CreditUsageEvent):
            self.monthly_credits_used += event.amount_cents
        elif isinstance(event, BalanceUsageEvent):
            self.usage_balance -= event.amount_cents
        elif isinstance(event, StateTransitionEvent):
            self.state = event.to_state
        elif isinstance(event, BalanceTopUpEvent):
            self.usage_balance += event.amount_cents
        elif isinstance(event, MonthlyCreditsResetEvent):
            self.monthly_credits_used = 0
        elif isinstance(event, BalanceRefundEvent):
            self.usage_balance -= event.amount_cents
        elif isinstance(event, SubscriptionSignupEvent):
            # Update monthly credits if provided via signup event
            self.monthly_credits_cents = event.monthly_credits_cents
        elif isinstance(event, SubscriptionCancelEvent):
            # Cancel event itself doesn't change state - StateTransitionEvent does
            self.monthly_credits_cents = 0
        elif isinstance(event, ChargebackDetectedEvent):
            # Chargeback event itself doesn't change state - StateTransitionEvent does
            self.monthly_credits_cents = 0
            self.usage_balance = 0

        # increment version after applying any event
        self.version += 1

    def apply_events(self, events: Sequence[BillingEvent]) -> None:
        """
        Apply a list of events to update FSM state.

        Args:
            events: List of events to apply in order
        """
        for event in events:
            self.apply_event(event)

    def signup_subscription(self, external_id: str = "manual") -> List[BillingEvent]:
        """
        Generate events for subscription signup.

        Args:
            external_id: External reference (e.g., Stripe subscription ID)

        Returns:
            List of events representing subscription signup and state transition

        Raises:
            BillingFSMInvalidTransitionError: If transition is not valid
        """
        # Validate the transition if validator is available
        if self.validator:
            self.validator.validate_transition(
                from_state=self.state,
                trigger="do_signup_subscription",
                usage_balance=self.usage_balance,
            )

        events: List[BillingEvent] = []

        # Generate subscription signup event
        events.append(
            SubscriptionSignupEvent(
                event_id=uuid.uuid4(),
                user_id=self.user_id,
                created_at=datetime.now(),
                external_id=external_id,
            )
        )

        # Generate state transition event to ACTIVE_SUBSCRIPTION
        events.append(
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=self.user_id,
                created_at=datetime.now(),
                from_state=self.state,
                to_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                reason="SIGNUP_SUBSCRIPTION",
            )
        )

        return events

    def cancel_subscription(
        self, external_id: str = "manual", reason: str = "USER_REQUESTED"
    ) -> Sequence[BillingEvent]:
        """
        Generate events for subscription cancellation.

        Args:
            external_id: External reference (e.g., cancellation ID)
            reason: Reason for cancellation

        Returns:
            List of events representing subscription cancellation and state transition

        Raises:
            BillingFSMInvalidTransitionError: If transition is not valid
        """
        # Validate the transition if validator is available
        if self.validator:
            self.validator.validate_transition(
                from_state=self.state,
                trigger="do_cancel_subscription",
                usage_balance=self.usage_balance,
            )

        events: Sequence[BillingEvent] = []

        # Generate subscription cancel event
        events.append(
            SubscriptionCancelEvent(
                event_id=uuid.uuid4(),
                user_id=self.user_id,
                created_at=datetime.now(),
                external_id=external_id,
                reason=reason,
            )
        )

        # Generate state transition event to NO_SUBSCRIPTION
        events.append(
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=self.user_id,
                created_at=datetime.now(),
                from_state=self.state,
                to_state=UserAccountStatus.NO_SUBSCRIPTION,
                reason="CANCEL_SUBSCRIPTION",
            )
        )

        return events

    def skip_subscription(
        self, external_id: str = "onboarding"
    ) -> Sequence[BillingEvent]:
        """
        Generate events for skipping subscription (free tier onboarding).

        Transitions NEW → NO_SUBSCRIPTION for users who complete onboarding
        without signing up for a paid subscription.

        Args:
            external_id: External reference (e.g., onboarding completion ID)

        Returns:
            List of events representing onboarding completion and state transition

        Raises:
            BillingFSMInvalidTransitionError: If transition is not valid
        """
        # Validate the transition if validator is available
        if self.validator:
            self.validator.validate_transition(
                from_state=self.state,
                trigger="do_skip_subscription",
                usage_balance=self.usage_balance,
            )

        events: Sequence[BillingEvent] = []

        # Generate state transition event to NO_SUBSCRIPTION
        # We don't need a separate event type for this - just use StateTransitionEvent
        events.append(
            StateTransitionEvent(
                event_id=uuid.uuid4(),
                user_id=self.user_id,
                created_at=datetime.now(),
                from_state=self.state,
                to_state=UserAccountStatus.NO_SUBSCRIPTION,
                reason="SKIP_SUBSCRIPTION",
            )
        )

        return events

    # Usage and billing methods
    def record_usage(
        self, amount_cents: float, external_id: str
    ) -> Sequence[BillingEvent]:
        """
        Generate events for usage recording with hybrid billing model.

        For hybrid model: deducts from included credits first, then from usage balance.

        Args:
            amount_cents: Usage amount in cents
            external_id: External identifier for the usage (e.g. request ID)

        Returns:
            List of events representing the usage recording

        Raises:
            BillingFSMInvalidTransitionError: If transition is not valid
        """
        if amount_cents <= 0:
            raise ValueError("Usage amount must be positive")

        # Basic validation - can we record usage from current state?
        if self.validator:
            # Check if usage_recorded transition is valid from current state
            try:
                self.validator.validate_transition(
                    from_state=self.state,
                    trigger="usage_recorded",
                    usage_balance=self.usage_balance,
                )
            except BillingFSMInvalidTransitionError:
                # If direct usage_recorded fails, this state doesn't support usage recording
                raise BillingFSMInvalidTransitionError(
                    f"Cannot record usage from state {self.state.value}"
                )

        events: Sequence[BillingEvent] = []

        # For ACTIVE_SUBSCRIPTION, account for monthly credits first
        if self.state == UserAccountStatus.ACTIVE_SUBSCRIPTION:
            remaining_monthly_credits = (
                self.monthly_credits_cents - self.monthly_credits_used
            )

            if amount_cents < remaining_monthly_credits:
                # Usage covered entirely by monthly credits
                events.append(
                    CreditUsageEvent(
                        event_id=uuid.uuid4(),
                        user_id=self.user_id,
                        created_at=datetime.now(),
                        amount_cents=amount_cents,
                        external_id=external_id,
                    )
                )
                # No state transition - stay in ACTIVE_SUBSCRIPTION
            else:
                # Usage exceeds remaining monthly credits - split usage
                credits_used = remaining_monthly_credits
                balance_used = amount_cents - credits_used

                # Use up remaining monthly credits
                if credits_used > 0:
                    events.append(
                        CreditUsageEvent(
                            event_id=uuid.uuid4(),
                            user_id=self.user_id,
                            created_at=datetime.now(),
                            amount_cents=credits_used,
                            external_id=f"{external_id}_credits",
                        )
                    )

                # Deduct overflow from usage balance
                events.append(
                    BalanceUsageEvent(
                        event_id=uuid.uuid4(),
                        user_id=self.user_id,
                        created_at=datetime.now(),
                        amount_cents=balance_used,
                        external_id=f"{external_id}_balance",
                    )
                )

                # Determine new state based on resulting balance
                projected_balance = self.usage_balance - balance_used
                new_state = (
                    UserAccountStatus.METERED_BILLING
                    if projected_balance > 0
                    else UserAccountStatus.SUSPENDED
                )

                # Generate state transition event
                events.append(
                    StateTransitionEvent(
                        event_id=uuid.uuid4(),
                        user_id=self.user_id,
                        created_at=datetime.now(),
                        from_state=self.state,
                        to_state=new_state,
                        reason="USAGE_RECORDED",
                    )
                )
        else:
            # For other states, directly deduct from usage balance
            events.append(
                BalanceUsageEvent(
                    event_id=uuid.uuid4(),
                    user_id=self.user_id,
                    created_at=datetime.now(),
                    amount_cents=amount_cents,
                    external_id=external_id,
                )
            )

            # Only trigger transition if we're in METERED_BILLING
            if self.state == UserAccountStatus.METERED_BILLING:
                projected_balance = self.usage_balance - amount_cents
                if projected_balance <= 0:
                    # Transition to SUSPENDED
                    events.append(
                        StateTransitionEvent(
                            event_id=uuid.uuid4(),
                            user_id=self.user_id,
                            created_at=datetime.now(),
                            from_state=self.state,
                            to_state=UserAccountStatus.SUSPENDED,
                            reason="USAGE_RECORDED",
                        )
                    )

        return events

    def topup_usage_balance(
        self,
        amount_cents: int,
        external_id: str,
        invoice_download_url: Optional[str] = None,
    ) -> Sequence[BillingEvent]:
        """
        Generate events for usage balance top-up.

        Args:
            amount_cents: Amount to add to usage balance in cents
            external_id: External identifier (e.g. Stripe payment intent ID)
            invoice_download_url: Optional URL for invoice download

        Returns:
            List of events representing the balance top-up

        Raises:
            BillingFSMInvalidTransitionError: If transition is not valid
        """
        if amount_cents <= 0:
            raise ValueError("Top-up amount must be positive")

        # Validate topup transition if validator is available
        if self.validator:
            self.validator.validate_transition(
                from_state=self.state,
                trigger="topup_balance",
                usage_balance=self.usage_balance,
            )

        events: Sequence[BillingEvent] = []

        # Generate balance top-up event
        events.append(
            BalanceTopUpEvent(
                event_id=uuid.uuid4(),
                user_id=self.user_id,
                created_at=datetime.now(),
                amount_cents=int(amount_cents),
                external_id=external_id,
                invoice_url=invoice_download_url,
            )
        )

        # Generate state transition if currently suspended
        if self.state == UserAccountStatus.SUSPENDED:
            events.append(
                StateTransitionEvent(
                    event_id=uuid.uuid4(),
                    user_id=self.user_id,
                    created_at=datetime.now(),
                    from_state=self.state,
                    to_state=UserAccountStatus.METERED_BILLING,
                    reason="TOPUP_BALANCE",
                )
            )

        return events

    def start_new_billing_cycle(self) -> Sequence[BillingEvent]:
        """
        Generate events for starting a new billing cycle.

        Returns:
            List of events representing monthly credits reset and state transition

        Raises:
            BillingFSMInvalidTransitionError: If transition is not valid
        """
        # Validate billing cycle transition if validator is available
        if self.validator:
            self.validator.validate_transition(
                from_state=self.state,
                trigger="start_billing_cycle",
                usage_balance=self.usage_balance,
            )

        events: Sequence[BillingEvent] = []

        # Generate monthly credits reset event
        events.append(
            MonthlyCreditsResetEvent(
                event_id=uuid.uuid4(), user_id=self.user_id, created_at=datetime.now()
            )
        )

        # Generate state transition back to ACTIVE_SUBSCRIPTION for eligible states
        if self.state in [
            UserAccountStatus.METERED_BILLING,
            UserAccountStatus.SUSPENDED,
        ]:
            events.append(
                StateTransitionEvent(
                    event_id=uuid.uuid4(),
                    user_id=self.user_id,
                    created_at=datetime.now(),
                    from_state=self.state,
                    to_state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                    reason="START_BILLING_CYCLE",
                )
            )

        return events

    def process_balance_refund(
        self,
        amount_cents: float,
        external_id: str = "manual_refund",
        reason: str = "CUSTOMER_REQUEST",
    ) -> Sequence[BillingEvent]:
        """
        Generate events for processing a balance refund.

        Args:
            amount_cents: Amount to refund in cents (positive value)

        Returns:
            List of events representing the refund

        Raises:
            BillingFSMInvalidTransitionError: If refund amount is invalid
        """
        if amount_cents <= 0:
            raise BillingFSMInvalidTransitionError("Refund amount must be positive")

        # Validate that refund doesn't exceed available balance
        if amount_cents > self.usage_balance:
            raise BillingFSMInvalidTransitionError(
                f"Cannot refund {amount_cents} cents when balance is only {self.usage_balance} cents"
            )

        events: Sequence[BillingEvent] = []

        # Generate balance refund event
        events.append(
            BalanceRefundEvent(
                event_id=uuid.uuid4(),
                user_id=self.user_id,
                created_at=datetime.now(),
                amount_cents=int(amount_cents),
                external_id=external_id,
                reason=reason,
            )
        )

        # Generate state transition if balance would become zero or negative
        if self.state == UserAccountStatus.METERED_BILLING:
            projected_balance = self.usage_balance - amount_cents
            if projected_balance <= 0:
                events.append(
                    StateTransitionEvent(
                        event_id=uuid.uuid4(),
                        user_id=self.user_id,
                        created_at=datetime.now(),
                        from_state=self.state,
                        to_state=UserAccountStatus.SUSPENDED,
                        reason="REFUND_BALANCE",
                    )
                )

        return events

    def detect_chargeback(
        self, external_id: str = "chargeback", amount_cents: int = 0
    ) -> Sequence[BillingEvent]:
        """
        Generate events for chargeback detection and account closure.

        Returns:
            List of events representing chargeback detection and state transition

        Raises:
            BillingFSMInvalidTransitionError: If transition is not valid
        """
        # Validate chargeback transition if validator is available
        # Note: chargeback is typically allowed from any state (*)
        if self.validator:
            self.validator.validate_transition(
                from_state=self.state,
                trigger="chargeback_detected",
                usage_balance=self.usage_balance,
            )

        events: Sequence[BillingEvent] = []

        # Generate chargeback detected event
        events.append(
            ChargebackDetectedEvent(
                event_id=uuid.uuid4(),
                user_id=self.user_id,
                created_at=datetime.now(),
                external_id=external_id,
                amount_cents=amount_cents,
            )
        )

        # Generate state transition event if not already closed
        if self.state != UserAccountStatus.CLOSED:
            events.append(
                StateTransitionEvent(
                    event_id=uuid.uuid4(),
                    user_id=self.user_id,
                    created_at=datetime.now(),
                    from_state=self.state,
                    to_state=UserAccountStatus.CLOSED,
                    reason="CHARGEBACK_DETECTED",
                )
            )

        return events

    def get_account_status(self) -> AccountStatusResponse:
        """
        Get current account status information with computed properties.

        Returns:
            AccountStatusResponse containing subscription state, balances, and computed properties
        """
        return AccountStatusResponse(
            state=self.state,
            usage_balance_cents=self.usage_balance,
            usage_balance_dollars=self.usage_balance / 100.0,
            monthly_credits_cents=self.monthly_credits_used,
            monthly_credits_dollars=self.monthly_credits_used / 100.0,
            # Computed properties
            has_active_subscription=self.state
            in [
                UserAccountStatus.ACTIVE_SUBSCRIPTION,
                UserAccountStatus.METERED_BILLING,
                UserAccountStatus.SUSPENDED,
            ],
            is_suspended=self.state == UserAccountStatus.SUSPENDED,
            is_closed=self.state == UserAccountStatus.CLOSED,
            has_usage_balance=self.usage_balance > 0,
            subscription_only=self.state == UserAccountStatus.ACTIVE_SUBSCRIPTION
            and self.usage_balance == 0,
            using_metered_billing=self.state == UserAccountStatus.METERED_BILLING,
            no_subscription=self.state == UserAccountStatus.NO_SUBSCRIPTION,
        )


class BillingStateMachineManager:
    """
    Manager class for handling multiple billing accounts and their state machines.
    """

    def __init__(self):
        """Initialize the billing state machine manager."""
        self.accounts: Dict[str, BillingStateMachine] = {}

    def create_account(
        self, account_id: str, user_id: uuid.UUID
    ) -> BillingStateMachine:
        """
        Create a new billing account with event-sourced model.

        Args:
            account_id: Unique identifier for the account (for manager tracking)
            user_id: User UUID for event generation

        Returns:
            Created BillingStateMachine instance
        """
        if account_id in self.accounts:
            raise ValueError(f"Account {account_id} already exists")

        account = BillingStateMachine(
            user_id=user_id,
            version=0,
        )

        self.accounts[account_id] = account
        return account

    def get_account(self, account_id: str) -> Optional[BillingStateMachine]:
        """
        Get an account by ID.

        Args:
            account_id: Account identifier

        Returns:
            BillingAccount instance or None if not found
        """
        return self.accounts.get(account_id)

    def close_account(self, account_id: str, reason: str = "manual_closure"):
        """
        Close an account (mark as closed due to fraud/chargeback).

        Args:
            account_id: Account identifier
            reason: Reason for closure
        """
        account = self.get_account(account_id)
        if account:
            if reason == "chargeback":
                # Generate and apply chargeback events
                events = account.detect_chargeback()
                account.apply_events(events)
            else:
                # For manual closure, apply a direct state change
                # In a real system, you'd want to generate and persist these events too
                account.state = UserAccountStatus.CLOSED

    def get_all_accounts_status(self) -> Dict[str, AccountStatusResponse]:
        """
        Get status of all accounts.

        Returns:
            Dictionary mapping account IDs to their status information
        """
        return {
            account_id: account.get_account_status()
            for account_id, account in self.accounts.items()
        }
