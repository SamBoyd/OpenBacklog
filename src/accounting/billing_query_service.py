# src/accounting/billing_query_service.py
import math
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.accounting.billing_state_machine import (
    AccountStatusResponse,
    BalanceStatusWithPreview,
    EnforcementDecision,
    UsageImpactSimulation,
)
from src.accounting.billing_state_reconstructor import BillingStateReconstructor
from src.accounting.models import UserAccountStatus
from src.models import User


class BillingQueryService:
    """
    Service for querying billing account information without modifying state.

    Handles read-only operations like checking affordability, simulating usage impact,
    and providing account status details. Separated from BillingService to maintain
    clear separation of concerns between query and command operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_fsm(self, user: User):
        """Get billing FSM state for a user, preferring reconstruction from history."""
        return BillingStateReconstructor.reconstruct_billing_fsm_from_history(
            self.db, user
        )

    def get_account_status_detailed(self, user: User) -> AccountStatusResponse:
        """
        Get comprehensive status: subscription status, included credits remaining, usage balance, state

        Args:
            user: The user to get status for

        Returns:
            Dictionary with computed subscription state and balances
        """
        fsm = self._get_fsm(user)
        return fsm.get_account_status()

    def can_afford_request(self, user: User, estimated_cost_cents: float) -> bool:
        """
        Check if a user can afford a specific request cost (includes subscription credits + usage balance).

        Args:
            user: The user
            estimated_cost_cents: The estimated cost in cents

        Returns:
            bool: True if the user can afford the request, False otherwise
        """
        # SUSPENDED users cannot afford any requests
        if user.account_details.status == UserAccountStatus.SUSPENDED:
            return False

        fsm = self._get_fsm(user)

        # For subscription users, they have monthly credits available
        if fsm.state == UserAccountStatus.ACTIVE_SUBSCRIPTION:
            # Check if remaining monthly credits can cover the cost
            remaining_monthly_credits = (
                fsm.monthly_credits_cents - fsm.monthly_credits_used
            )
            if estimated_cost_cents <= remaining_monthly_credits:
                return True
            # If not fully covered by credits, check if usage balance can cover overflow
            overflow_amount = estimated_cost_cents - remaining_monthly_credits
            return fsm.usage_balance >= overflow_amount

        # For usage balance only, check if they have enough balance
        projected_balance = fsm.usage_balance - estimated_cost_cents
        return projected_balance >= 0

    def simulate_usage_impact(
        self, user: User, estimated_cost_cents: float
    ) -> UsageImpactSimulation:
        """
        Simulate what would happen if a user incurred a specific cost in the subscription model.

        Args:
            user: The user
            estimated_cost_cents: The estimated cost in cents

        Returns:
            UsageImpactSimulation containing current status, projected balance, and projected status
        """
        fsm = self._get_fsm(user)

        current_balance = fsm.usage_balance
        current_monthly_credits_used = fsm.monthly_credits_used
        remaining_monthly_credits = (
            fsm.monthly_credits_cents - current_monthly_credits_used
        )

        # Simulate the usage logic from FSM
        projected_balance = current_balance
        projected_monthly_credits_used = current_monthly_credits_used
        projected_status = fsm.state

        if fsm.state == UserAccountStatus.ACTIVE_SUBSCRIPTION:
            if estimated_cost_cents <= remaining_monthly_credits:
                # Usage covered entirely by monthly credits - no balance change, no state change
                projected_monthly_credits_used += int(estimated_cost_cents)
            else:
                # Usage exceeds remaining monthly credits
                credits_to_use = remaining_monthly_credits
                overflow_amount = estimated_cost_cents - credits_to_use

                # Use up remaining monthly credits and deduct overflow from balance
                projected_monthly_credits_used += credits_to_use
                projected_balance -= overflow_amount

                # Determine new state based on resulting balance
                if projected_balance > 0:
                    projected_status = UserAccountStatus.METERED_BILLING
                else:
                    projected_status = UserAccountStatus.SUSPENDED
        elif fsm.state == UserAccountStatus.METERED_BILLING:
            # Already using paid credits - deduct directly from balance
            projected_balance -= estimated_cost_cents
            if projected_balance <= 0:
                projected_status = UserAccountStatus.SUSPENDED
        else:
            # For other states (NO_SUBSCRIPTION, SUSPENDED, CLOSED), deduct from balance
            projected_balance -= estimated_cost_cents

        # Calculate low balance warning threshold ($1.00)
        low_balance_threshold = 100  # $1.00 in cents
        would_be_low_balance = (
            projected_status
            not in [UserAccountStatus.SUSPENDED, UserAccountStatus.CLOSED]
            and projected_balance < low_balance_threshold
        )

        return UsageImpactSimulation(
            current_usage_balance_cents=current_balance,
            current_status=fsm.state,
            current_monthly_credits_used=float(current_monthly_credits_used),
            remaining_monthly_credits=float(remaining_monthly_credits),
            estimated_cost_cents=float(estimated_cost_cents),
            projected_usage_balance_cents=float(projected_balance),
            projected_monthly_credits_used=float(projected_monthly_credits_used),
            projected_status=projected_status,
            would_be_suspended=projected_status == UserAccountStatus.SUSPENDED,
            would_be_metered=projected_status == UserAccountStatus.METERED_BILLING,
            would_be_low_balance=would_be_low_balance,
        )

    def get_balance_status_with_preview(
        self, user: User, estimated_cost_cents: float
    ) -> BalanceStatusWithPreview:
        """
        Get comprehensive balance status including preview of request impact.

        Args:
            user: The user
            estimated_cost_cents: The estimated cost in cents

        Returns:
            BalanceStatusWithPreview object containing balance status and request impact preview
        """
        # Get current status
        current_status = self.get_account_status_detailed(user)

        # Get usage impact simulation
        usage_impact = self.simulate_usage_impact(user, estimated_cost_cents)

        # Determine if request is affordable
        can_afford = self.can_afford_request(user, estimated_cost_cents)

        # Calculate top-up amount needed if request is not affordable
        top_up_needed = 0
        if not can_afford:
            # Calculate amount needed to get to $5 balance after the request
            target_balance_after_request = 500  # $5.00 in cents
            required_balance_before_request = (
                target_balance_after_request + estimated_cost_cents
            )
            top_up_needed = max(
                0, required_balance_before_request - current_status.usage_balance_cents
            )

        return BalanceStatusWithPreview(
            current_status=current_status,
            usage_impact=usage_impact,
            can_afford=can_afford,
            top_up_needed_cents=math.ceil(top_up_needed),
            top_up_needed_dollars=top_up_needed / 100.0,
            enforcement_decision=self._get_enforcement_decision(
                usage_impact, can_afford
            ),
        )

    def _get_enforcement_decision(
        self, usage_impact: UsageImpactSimulation, can_afford: bool
    ) -> EnforcementDecision:
        """
        Determine the enforcement decision based on usage impact and affordability.

        Args:
            usage_impact: UsageImpactSimulation from simulate_usage_impact
            can_afford: Boolean indicating if user can afford the request

        Returns:
            EnforcementDecision object containing enforcement decision and reasoning
        """
        current_status = usage_impact.current_status
        projected_balance = usage_impact.projected_usage_balance_cents
        would_be_suspended = usage_impact.would_be_suspended
        would_be_low_balance = usage_impact.would_be_low_balance

        # If user is already suspended, reject
        if current_status == UserAccountStatus.SUSPENDED:
            return EnforcementDecision(
                action="reject",
                reason="account_suspended",
                message="Your account is suspended. Please add funds to continue using the service.",
            )

        # If user cannot afford the request, reject
        if not can_afford:
            return EnforcementDecision(
                action="reject",
                reason="insufficient_balance",
                message=f"Insufficient balance. This request would put your account ${abs(projected_balance)/100:.2f} over the limit.",
            )

        # If request would suspend the user but is within tolerance, allow with warning
        if would_be_suspended:
            return EnforcementDecision(
                action="allow_with_suspension",
                reason="request_will_suspend",
                message="This request will suspend your account. Please add funds to continue using the service.",
            )

        # If request would put user in low balance, allow with warning
        if would_be_low_balance:
            return EnforcementDecision(
                action="allow_with_warning",
                reason="low_balance_warning",
                message="Your account balance is getting low. Consider adding funds to avoid service interruption.",
            )

        # Normal case - allow request
        return EnforcementDecision(
            action="allow",
            reason="sufficient_balance",
            message=None,
        )
