"""
Test suite for BillingQueryService with focus on simulate_usage_impact function.

This module contains comprehensive tests for the simulate_usage_impact method to identify
and validate billing simulation logic, particularly edge cases and potential bugs.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from hamcrest import (
    assert_that,
    close_to,
    equal_to,
    has_entries,
    has_key,
    instance_of,
    is_,
)
from sqlalchemy.orm import Session

from src.accounting.billing_query_service import BillingQueryService
from src.accounting.billing_state_machine import (
    AccountStatusResponse,
    UsageImpactSimulation,
)
from src.accounting.models import UserAccountStatus
from src.models import User


class TestBillingQueryServiceSimulateUsageImpact:
    """Test suite for the simulate_usage_impact method."""

    def _create_mock_fsm(
        self,
        state: UserAccountStatus,
        usage_balance: float = 0.0,
        monthly_credits_cents: int = 500,
        monthly_credits_used: int = 0,
    ) -> MagicMock:
        """Create a mock FSM with specified state and balances."""
        mock_fsm = MagicMock()
        mock_fsm.state = state
        mock_fsm.usage_balance = usage_balance
        mock_fsm.monthly_credits_cents = monthly_credits_cents
        mock_fsm.monthly_credits_used = monthly_credits_used
        return mock_fsm

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_active_subscription_usage_covered_by_credits(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test ACTIVE_SUBSCRIPTION with usage fully covered by remaining monthly credits."""
        # Setup: User has $5.00 credits, used $2.00, requesting $1.50
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=0.0,
            monthly_credits_cents=500,
            monthly_credits_used=200,  # $2.00 used
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 150.0)  # $1.50

        # Verify return type is UsageImpactSimulation
        assert_that(result, instance_of(UsageImpactSimulation))

        assert_that(result.current_usage_balance_cents, equal_to(0.0))
        assert_that(
            result.current_status, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )
        assert_that(result.current_monthly_credits_used, equal_to(200))
        assert_that(result.remaining_monthly_credits, equal_to(300))  # $3.00 remaining
        assert_that(result.estimated_cost_cents, equal_to(150.0))

        # Usage fully covered by credits - no state change, no balance change
        assert_that(result.projected_usage_balance_cents, equal_to(0.0))
        assert_that(result.projected_monthly_credits_used, equal_to(350))  # 200 + 150
        assert_that(
            result.projected_status, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )
        assert_that(result.would_be_suspended, is_(False))
        assert_that(result.would_be_metered, is_(False))
        assert_that(
            result.would_be_low_balance, is_(True)
        )  # only looks at account balance not included credits

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_active_subscription_usage_exceeds_credits_with_balance(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test ACTIVE_SUBSCRIPTION with usage exceeding credits but covered by balance."""
        # Setup: User has $5.00 credits, used $3.00, requesting $4.00, has $2.00 balance
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=200.0,  # $2.00 balance
            monthly_credits_cents=500,
            monthly_credits_used=300,  # $3.00 used
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 400.0)  # $4.00

        assert_that(result.current_usage_balance_cents, equal_to(200.0))
        assert_that(result.remaining_monthly_credits, equal_to(200))  # $2.00 remaining

        # $2.00 from credits, $2.00 from balance = $4.00 total
        assert_that(result.projected_monthly_credits_used, equal_to(500))  # 300 + 200
        assert_that(result.projected_usage_balance_cents, equal_to(0.0))  # 200 - 200
        assert_that(result.projected_status, equal_to(UserAccountStatus.SUSPENDED))
        assert_that(result.would_be_suspended, is_(True))
        assert_that(result.would_be_metered, is_(False))
        assert_that(result.would_be_low_balance, is_(False))  # $0.00 < $1.00

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_active_subscription_usage_causes_suspension(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test ACTIVE_SUBSCRIPTION with usage causing suspension due to insufficient balance."""
        # Setup: User has $5.00 credits, used $4.00, requesting $3.00, has $1.00 balance
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=100.0,  # $1.00 balance
            monthly_credits_cents=500,
            monthly_credits_used=400,  # $4.00 used
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 300.0)  # $3.00

        assert_that(result.remaining_monthly_credits, equal_to(100))  # $1.00 remaining

        # $1.00 from credits, $2.00 from balance but only $1.00 available
        assert_that(result.projected_monthly_credits_used, equal_to(500))  # 400 + 100
        assert_that(result.projected_usage_balance_cents, equal_to(-100.0))  # 100 - 200
        assert_that(result.projected_status, equal_to(UserAccountStatus.SUSPENDED))
        assert_that(result.would_be_suspended, is_(True))
        assert_that(result.would_be_metered, is_(False))
        assert_that(
            result.would_be_low_balance, is_(False)
        )  # Suspended users don't get low balance warning

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_metered_billing_normal_usage(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test METERED_BILLING with normal usage deduction."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance=500.0,  # $5.00 balance
            monthly_credits_cents=500,
            monthly_credits_used=500,  # Credits fully used
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 200.0)  # $2.00

        assert_that(result.current_status, equal_to(UserAccountStatus.METERED_BILLING))
        assert_that(result.projected_usage_balance_cents, equal_to(300.0))  # 500 - 200
        assert_that(
            result.projected_status, equal_to(UserAccountStatus.METERED_BILLING)
        )
        assert_that(result.would_be_suspended, is_(False))
        assert_that(result.would_be_metered, is_(True))
        assert_that(result.would_be_low_balance, is_(False))  # $3.00 > $1.00

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_metered_billing_causes_suspension(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test METERED_BILLING with usage causing suspension."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance=150.0,  # $1.50 balance
            monthly_credits_cents=500,
            monthly_credits_used=500,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 200.0)  # $2.00

        assert_that(result.projected_usage_balance_cents, equal_to(-50.0))  # 150 - 200
        assert_that(result.projected_status, equal_to(UserAccountStatus.SUSPENDED))
        assert_that(result.would_be_suspended, is_(True))
        assert_that(result.would_be_metered, is_(False))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_no_subscription_state(self, mock_get_fsm, session: Session, user: User):
        """Test NO_SUBSCRIPTION state behavior."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.NO_SUBSCRIPTION,
            usage_balance=300.0,  # $3.00 balance
            monthly_credits_cents=0,  # No credits without subscription
            monthly_credits_used=0,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 100.0)  # $1.00

        assert_that(result.current_status, equal_to(UserAccountStatus.NO_SUBSCRIPTION))
        assert_that(result.remaining_monthly_credits, equal_to(0))
        assert_that(result.projected_usage_balance_cents, equal_to(200.0))  # 300 - 100
        assert_that(
            result.projected_status, equal_to(UserAccountStatus.NO_SUBSCRIPTION)
        )
        assert_that(result.would_be_suspended, is_(False))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_suspended_state(self, mock_get_fsm, session: Session, user: User):
        """Test SUSPENDED state behavior."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.SUSPENDED,
            usage_balance=0.0,
            monthly_credits_cents=500,
            monthly_credits_used=500,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 100.0)  # $1.00

        assert_that(result.current_status, equal_to(UserAccountStatus.SUSPENDED))
        assert_that(result.projected_usage_balance_cents, equal_to(-100.0))  # 0 - 100
        assert_that(result.projected_status, equal_to(UserAccountStatus.SUSPENDED))
        assert_that(
            result.would_be_low_balance, is_(False)
        )  # Suspended users don't get warning

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_low_balance_warning_threshold(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test low balance warning at $1.00 threshold."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance=150.0,  # $1.50 balance
            monthly_credits_cents=500,
            monthly_credits_used=500,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 60.0)  # $0.60

        # Projected balance: $1.50 - $0.60 = $0.90 (< $1.00 threshold)
        assert_that(result.projected_usage_balance_cents, equal_to(90.0))
        assert_that(result.would_be_low_balance, is_(True))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_exactly_one_dollar_remaining(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test edge case with exactly $1.00 remaining after usage."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance=200.0,  # $2.00 balance
            monthly_credits_cents=500,
            monthly_credits_used=500,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 100.0)  # $1.00

        # Projected balance: $2.00 - $1.00 = $1.00 (exactly at threshold)
        assert_that(result.projected_usage_balance_cents, equal_to(100.0))
        assert_that(result.would_be_low_balance, is_(False))  # Not below threshold

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_zero_cost_usage(self, mock_get_fsm, session: Session, user: User):
        """Test edge case with zero cost."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=100.0,
            monthly_credits_cents=500,
            monthly_credits_used=200,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 0.0)

        # No changes should occur with zero cost
        assert_that(result.projected_usage_balance_cents, equal_to(100.0))
        assert_that(result.projected_monthly_credits_used, equal_to(200))
        assert_that(
            result.projected_status, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_precision_with_float_costs(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test precision handling with float costs."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=100.75,  # $1.0075
            monthly_credits_cents=500,
            monthly_credits_used=200,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 50.25)  # $0.5025

        # Test that float precision is maintained
        assert_that(result.estimated_cost_cents, equal_to(50.25))
        assert_that(
            result.projected_monthly_credits_used, equal_to(250)
        )  # Should cast to int: 200 + int(50.25) = 250
        assert_that(
            result.projected_usage_balance_cents, equal_to(100.75)
        )  # No change to balance

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_negative_remaining_credits_edge_case(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test edge case where monthly_credits_used > monthly_credits_cents (overdrawn credits)."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=300.0,
            monthly_credits_cents=500,
            monthly_credits_used=600,  # $6.00 used > $5.00 available (shouldn't happen but test edge case)
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 100.0)  # $1.00

        # Remaining credits should be negative: 500 - 600 = -100
        assert_that(result.remaining_monthly_credits, equal_to(-100))

        # Since remaining credits are negative, all usage should come from balance
        assert_that(result.projected_usage_balance_cents, equal_to(100.0))  # 300 - 100
        assert_that(
            result.projected_monthly_credits_used, equal_to(500)
        )  # No change to credits
        assert_that(
            result.projected_status, equal_to(UserAccountStatus.METERED_BILLING)
        )

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_return_value_types(self, mock_get_fsm, session: Session, user: User):
        """Test that all return values are of correct types."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=100.0,
            monthly_credits_cents=500,
            monthly_credits_used=200,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 150.0)

        # Verify types using hamcrest
        assert_that(result.current_usage_balance_cents, instance_of(float))
        assert_that(result.current_status, instance_of(UserAccountStatus))
        assert_that(result.current_monthly_credits_used, instance_of(float))
        assert_that(result.remaining_monthly_credits, instance_of(float))
        assert_that(result.estimated_cost_cents, instance_of(float))
        assert_that(result.projected_usage_balance_cents, instance_of(float))
        assert_that(result.projected_monthly_credits_used, instance_of(float))
        assert_that(result.projected_status, instance_of(UserAccountStatus))
        assert_that(result.would_be_suspended, instance_of(bool))
        assert_that(result.would_be_metered, instance_of(bool))
        assert_that(result.would_be_low_balance, instance_of(bool))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_closed_account_state(self, mock_get_fsm, session: Session, user: User):
        """Test CLOSED state behavior."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.CLOSED,
            usage_balance=1000.0,  # Even with balance, account is closed
            monthly_credits_cents=500,
            monthly_credits_used=100,
        )
        mock_get_fsm.return_value = mock_fsm

        query_service = BillingQueryService(session)
        result = query_service.simulate_usage_impact(user, 200.0)

        assert_that(result.current_status, equal_to(UserAccountStatus.CLOSED))
        assert_that(result.projected_usage_balance_cents, equal_to(800.0))  # 1000 - 200
        assert_that(
            result.projected_status, equal_to(UserAccountStatus.CLOSED)
        )  # State doesn't change
        assert_that(
            result.would_be_low_balance, is_(False)
        )  # Closed accounts don't get warnings


class TestBillingQueryServiceGetBalanceStatusWithPreview:
    """Test suite for the get_balance_status_with_preview method."""

    def _create_mock_fsm(
        self,
        state: UserAccountStatus,
        usage_balance: float = 0.0,
        monthly_credits_cents: int = 500,
        monthly_credits_used: int = 0,
    ) -> MagicMock:
        """Create a mock FSM with specified state and balances."""
        mock_fsm = MagicMock()
        mock_fsm.state = state
        mock_fsm.usage_balance = usage_balance
        mock_fsm.monthly_credits_cents = monthly_credits_cents
        mock_fsm.monthly_credits_used = monthly_credits_used
        return mock_fsm

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_can_afford_active_subscription_with_sufficient_credits(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test user can afford request using monthly credits only."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=100.0,  # $1.00 balance
            monthly_credits_cents=500,  # $5.00 credits
            monthly_credits_used=200,  # $2.00 used, $3.00 remaining
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status for current_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=100.0,
            usage_balance_dollars=1.0,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 150.0)  # $1.50

        # Should be able to afford with remaining credits
        assert_that(result.can_afford, is_(True))
        assert_that(result.top_up_needed_cents, equal_to(0))
        assert_that(result.enforcement_decision.action, equal_to("allow"))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_cannot_afford_insufficient_balance_and_credits(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test user cannot afford request due to insufficient balance and credits."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=50.0,  # $0.50 balance
            monthly_credits_cents=500,  # $5.00 credits
            monthly_credits_used=450,  # $4.50 used, $0.50 remaining
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=50.0,
            usage_balance_dollars=0.5,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 200.0)  # $2.00

        # Should not be able to afford ($0.50 credits + $0.50 balance = $1.00 < $2.00 needed)
        assert_that(result.can_afford, is_(False))
        assert_that(result.enforcement_decision.action, equal_to("reject"))
        assert_that(
            result.enforcement_decision.reason, equal_to("insufficient_balance")
        )

        # Should suggest top-up to reach $5 after the request
        # Need: $2.00 (request) + $5.00 (target) - $0.50 (current balance) = $6.50
        assert_that(result.top_up_needed_cents, equal_to(650))
        assert_that(result.top_up_needed_dollars, equal_to(6.50))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_request_will_suspend_account(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test request that will suspend the account but is within tolerance."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=100.0,  # $1.00 balance
            monthly_credits_cents=500,  # $5.00 credits
            monthly_credits_used=400,  # $4.00 used, $1.00 remaining
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=100.0,
            usage_balance_dollars=1.0,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 250.0)  # 21.50

        # Shouldnt be able to afford ($1.00 credits + $0.50 from balance = $1.50)
        assert_that(result.can_afford, is_(False))
        assert_that(result.enforcement_decision.action, equal_to("reject"))
        assert_that(
            result.enforcement_decision.reason, equal_to("insufficient_balance")
        )
        assert_that(
            result.enforcement_decision.message,
            equal_to(
                "Insufficient balance. This request would put your account $0.50 over the limit."
            ),
        )

        # Check usage impact shows suspension
        assert_that(result.usage_impact.would_be_suspended, is_(True))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_request_causes_low_balance_warning(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test request that causes low balance warning."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance=180.0,  # $1.80 balance
            monthly_credits_cents=500,
            monthly_credits_used=500,  # Credits fully used
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance_cents=180.0,
            usage_balance_dollars=1.8,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 90.0)  # $0.90

        # Should be able to afford but result in low balance ($1.80 - $0.90 = $0.90 < $1.00)
        assert_that(result.can_afford, is_(True))
        assert_that(result.enforcement_decision.action, equal_to("allow_with_warning"))
        assert_that(result.enforcement_decision.reason, equal_to("low_balance_warning"))
        assert_that(
            result.enforcement_decision.message,
            equal_to(
                "Your account balance is getting low. Consider adding funds to avoid service interruption."
            ),
        )

        # Check usage impact shows low balance
        assert_that(result.usage_impact.would_be_low_balance, is_(True))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_suspended_account_rejection(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test that suspended accounts are rejected."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.SUSPENDED,
            usage_balance=0.0,
            monthly_credits_cents=500,
            monthly_credits_used=500,
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.SUSPENDED,
            usage_balance_cents=0.0,
            usage_balance_dollars=0.0,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 50.0)  # $0.50

        assert_that(result.can_afford, is_(False))
        assert_that(result.enforcement_decision.action, equal_to("reject"))
        assert_that(result.enforcement_decision.reason, equal_to("account_suspended"))
        assert_that(
            result.enforcement_decision.message,
            equal_to(
                "Your account is suspended. Please add funds to continue using the service."
            ),
        )

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_zero_cost_request(self, mock_get_fsm, session: Session, user: User):
        """Test edge case with zero cost request."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=500.0,  # $5.00 balance
            monthly_credits_cents=500,
            monthly_credits_used=200,  # $2.00 used
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=500.0,
            usage_balance_dollars=5.0,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 0.0)

        # Should be able to afford zero cost
        assert_that(result.can_afford, is_(True))
        assert_that(result.top_up_needed_cents, equal_to(0))
        assert_that(result.enforcement_decision.action, equal_to("allow"))
        assert_that(result.enforcement_decision.reason, equal_to("sufficient_balance"))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_top_up_calculation_precision(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test top-up calculation precision with float values."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance=75.25,  # $0.7525 balance
            monthly_credits_cents=500,
            monthly_credits_used=500,
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance_cents=75.25,
            usage_balance_dollars=0.7525,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 100.50)  # $1.005

        # Cannot afford: need $1.005 but only have $0.7525
        assert_that(result.can_afford, is_(False))

        # Top-up calculation: ($1.005 + $5.00) - $0.7525 = $5.2525 = 525.25 cents
        expected_top_up = 526  # (100.50 + 500) - 75.25 = 525.25, rounded up to 526
        assert_that(result.top_up_needed_cents, close_to(expected_top_up, 0.01))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_return_value_structure_and_types(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test that return values have correct structure and types."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance=100.0,
            monthly_credits_cents=500,
            monthly_credits_used=200,
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=100.0,
            usage_balance_dollars=1.0,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 150.0)

        # Verify all required attributes are present
        assert_that(hasattr(result, "current_status"), is_(True))
        assert_that(hasattr(result, "usage_impact"), is_(True))
        assert_that(hasattr(result, "can_afford"), is_(True))
        assert_that(hasattr(result, "top_up_needed_cents"), is_(True))
        assert_that(hasattr(result, "top_up_needed_dollars"), is_(True))
        assert_that(hasattr(result, "enforcement_decision"), is_(True))

        # Verify types
        assert_that(result.can_afford, instance_of(bool))
        assert_that(result.top_up_needed_cents, instance_of(int))
        assert_that(result.top_up_needed_dollars, instance_of(float))
        assert_that(result.usage_impact, instance_of(UsageImpactSimulation))

        # Verify enforcement decision attributes
        assert_that(hasattr(result.enforcement_decision, "action"), is_(True))
        assert_that(hasattr(result.enforcement_decision, "reason"), is_(True))
        assert_that(hasattr(result.enforcement_decision, "message"), is_(True))

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_metered_billing_transitions_to_suspension(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test metered billing user whose request will cause suspension."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance=80.0,  # $0.80 balance
            monthly_credits_cents=500,
            monthly_credits_used=500,  # No credits available
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance_cents=80.0,
            usage_balance_dollars=0.8,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 100.0)  # $1.00

        # Should be able to afford but will cause suspension
        assert_that(result.can_afford, is_(False))
        assert_that(result.enforcement_decision.action, equal_to("reject"))
        assert_that(
            result.enforcement_decision.reason, equal_to("insufficient_balance")
        )
        assert_that(result.usage_impact.would_be_suspended, is_(True))
        assert_that(
            result.usage_impact.projected_usage_balance_cents, equal_to(-20.0)
        )  # 80 - 100

    @patch("src.accounting.billing_query_service.BillingQueryService._get_fsm")
    def test_edge_case_exactly_one_dollar_threshold(
        self, mock_get_fsm, session: Session, user: User
    ):
        """Test edge case where projected balance is exactly at $1.00 threshold."""
        mock_fsm = self._create_mock_fsm(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance=200.0,  # $2.00 balance
            monthly_credits_cents=500,
            monthly_credits_used=500,
        )
        mock_get_fsm.return_value = mock_fsm

        # Mock get_account_status
        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.METERED_BILLING,
            usage_balance_cents=200.0,
            usage_balance_dollars=2.0,
            monthly_credits_cents=500,
            monthly_credits_dollars=5.0,
            has_active_subscription=True,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=True,
            using_metered_billing=False,
            no_subscription=False,
            is_suspended=False,
        )
        mock_fsm.get_account_status.return_value = mock_account_status

        query_service = BillingQueryService(session)
        result = query_service.get_balance_status_with_preview(user, 100.0)  # $1.00

        # Should be able to afford and not trigger low balance warning ($2.00 - $1.00 = $1.00)
        assert_that(result.can_afford, is_(True))
        assert_that(result.enforcement_decision.action, equal_to("allow"))
        assert_that(result.enforcement_decision.reason, equal_to("sufficient_balance"))
        assert_that(result.usage_impact.would_be_low_balance, is_(False))
