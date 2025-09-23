from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to

from src.accounting.billing_state_machine import (
    AccountStatusResponse,
    BalanceStatusWithPreview,
    EnforcementDecision,
    UsageImpactSimulation,
)
from src.accounting.models import UserAccountStatus
from src.ai.ai_service import check_user_can_afford_request
from src.models import (
    APIProvider,
    ContextDocument,
    Initiative,
    InitiativeType,
    Task,
    TaskStatus,
    TaskType,
    UserKey,
)


@pytest.fixture
def initiative(session, user, workspace) -> Initiative:
    """Create a real Initiative object in the test database"""
    initiative = Initiative(
        title="Test Initiative",
        description="This is a test initiative for AI improvement",
        status=TaskStatus.TO_DO,
        type=InitiativeType.FEATURE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id=user.id,
        workspace_id=workspace.id,
    )

    session.add(initiative)
    session.commit()
    session.refresh(initiative)
    return initiative


@pytest.fixture
def task(session, initiative, user, workspace) -> Task:
    """Create a real Task object in the test database"""
    task = Task(
        title="Test Task",
        identifier="test-task-123",
        description="This is a test task for AI improvement",
        status=TaskStatus.TO_DO,
        type=TaskType.CODING,
        initiative_id=initiative.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id=user.id,
        workspace_id=workspace.id,
    )

    initiative.tasks.append(task)
    session.add(initiative)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def valid_user_key(session, user) -> UserKey:
    """Create a valid UserKey object in the test database."""
    key = UserKey()
    key.user_id = user.id
    key.provider = APIProvider.LITELLM
    key.is_valid = True
    key.last_validated_at = datetime.now()
    key.redacted_key = "sk-***1234"
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


@pytest.fixture
def invalid_user_key(session, user) -> UserKey:
    """Create an invalid UserKey object in the test database."""
    key = UserKey()
    key.user_id = user.id
    key.provider = APIProvider.LITELLM
    key.is_valid = False
    key.last_validated_at = datetime.now() - timedelta(days=10)
    key.redacted_key = "sk-***1234"
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


@pytest.fixture
def context_document(session, user, workspace) -> ContextDocument:
    """Create a ContextDocument for testing."""
    doc = ContextDocument(
        title="Test Context Doc",
        content="This is the shared context for the workspace.",
        user_id=user.id,
        workspace_id=workspace.id,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


class TestCheckUserBalanceForRequest:

    @patch("src.ai.ai_service.BillingService")
    def test__user_has_no_subscription(self, mock_billing_service, user, session):
        """Test that the user has no subscription."""
        # Setup
        mock_billing_service.return_value = MagicMock()
        mock_billing_service.return_value.get_account_status_detailed.return_value = (
            AccountStatusResponse(
                state=UserAccountStatus.NO_SUBSCRIPTION,
                usage_balance_cents=0,
                usage_balance_dollars=0.00,
                monthly_credits_cents=0,
                monthly_credits_dollars=0.00,
                has_active_subscription=False,
                is_suspended=False,
                is_closed=False,
                has_usage_balance=False,
                subscription_only=False,
                using_metered_billing=False,
                no_subscription=True,
            )
        )

        # Execute
        result = check_user_can_afford_request(user, [], session)
        assert_that(result.can_proceed, equal_to(False))
        assert result.balance_warning is None

    @patch("src.ai.ai_service.BillingService")
    def test__user_is_suspended(self, mock_billing_service, user, session):
        """Test that the user is suspended."""
        # Setup
        mock_billing_service.return_value = MagicMock()
        mock_billing_service.return_value.get_account_status_detailed.return_value = (
            AccountStatusResponse(
                state=UserAccountStatus.SUSPENDED,
                usage_balance_cents=0,
                usage_balance_dollars=0.00,
                monthly_credits_cents=0,
                monthly_credits_dollars=0.00,
                has_active_subscription=True,
                is_suspended=True,
                is_closed=False,
                has_usage_balance=False,
                subscription_only=False,
                using_metered_billing=False,
                no_subscription=False,
            )
        )

        # Execute
        result = check_user_can_afford_request(user, [], session)
        assert_that(result.can_proceed, equal_to(False))
        assert result.balance_warning is None

    @patch("src.ai.ai_service.BillingService")
    def test__user_is_closed(self, mock_billing_service, user, session):
        """Test that the user is closed."""
        # Setup
        mock_billing_service.return_value = MagicMock()
        mock_billing_service.return_value.get_account_status_detailed.return_value = (
            AccountStatusResponse(
                state=UserAccountStatus.CLOSED,
                usage_balance_cents=0,
                usage_balance_dollars=0.00,
                monthly_credits_cents=0,
                monthly_credits_dollars=0.00,
                has_active_subscription=False,
                is_suspended=False,
                is_closed=True,
                has_usage_balance=False,
                subscription_only=False,
                using_metered_billing=False,
                no_subscription=False,
            )
        )

        # Execute
        result = check_user_can_afford_request(user, [], session)
        assert_that(result.can_proceed, equal_to(False))
        assert result.balance_warning is None

    @patch("src.ai.ai_service.create_cost_estimator")
    @patch("src.ai.ai_service.BillingService")
    def test__user_can_afford_request(
        self, mock_billing_service, mock_create_cost_estimator, user, session
    ):
        """Test that the user can afford the request."""
        # Setup
        mock_billing_service.return_value = MagicMock()
        mock_billing_service.return_value.get_account_status_detailed.return_value = (
            AccountStatusResponse(
                state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                usage_balance_cents=1000,
                usage_balance_dollars=10.00,
                monthly_credits_cents=1000,
                monthly_credits_dollars=10.00,
                has_active_subscription=True,
                is_suspended=False,
                is_closed=False,
                has_usage_balance=True,
                subscription_only=False,
                using_metered_billing=False,
                no_subscription=False,
            )
        )
        mock_billing_service.return_value.get_balance_status_with_preview.return_value = {
            "current_status": {
                "balance_cents": 1000,
                "balance_dollars": 10.00,
            },
            "enforcement_decision": {
                "action": "allow",
                "reason": "sufficient_balance",
                "message": "User has sufficient balance",
            },
            "top_up_needed_cents": 0,
            "top_up_needed_dollars": 0.00,
        }
        mock_create_cost_estimator.return_value = MagicMock()
        mock_create_cost_estimator.return_value.estimate_request_cost_cents.return_value = (
            100
        )

        # Execute
        result = check_user_can_afford_request(user, [], session)
        assert_that(result.can_proceed, equal_to(True))

    @patch("src.ai.ai_service.create_cost_estimator")
    @patch("src.ai.ai_service.BillingService")
    def test__user_cannot_afford_request(
        self, mock_billing_service, mock_create_cost_estimator, user, session
    ):
        """Test that the user cannot afford the request."""
        # Setup
        mock_billing_service.return_value = MagicMock()
        mock_billing_service.return_value.get_account_status_detailed.return_value = (
            AccountStatusResponse(
                state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                usage_balance_cents=100,
                usage_balance_dollars=1.00,
                monthly_credits_cents=0,
                monthly_credits_dollars=0.00,
                has_active_subscription=True,
                is_suspended=False,
                is_closed=False,
                has_usage_balance=True,
                subscription_only=False,
                using_metered_billing=False,
                no_subscription=False,
            )
        )

        mock_billing_service.return_value.get_balance_status_with_preview.return_value = BalanceStatusWithPreview(
            current_status=AccountStatusResponse(
                state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                usage_balance_cents=100,
                usage_balance_dollars=1.00,
                monthly_credits_cents=0,
                monthly_credits_dollars=0.00,
                has_active_subscription=True,
                is_suspended=False,
                is_closed=False,
                has_usage_balance=True,
                subscription_only=False,
                using_metered_billing=False,
                no_subscription=False,
            ),
            usage_impact=UsageImpactSimulation(
                current_usage_balance_cents=100,
                current_status=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                current_monthly_credits_used=0,
                remaining_monthly_credits=0,
                estimated_cost_cents=1000,
                projected_usage_balance_cents=100,
                projected_monthly_credits_used=0,
                projected_status=UserAccountStatus.ACTIVE_SUBSCRIPTION,
                would_be_suspended=False,
                would_be_metered=False,
                would_be_low_balance=False,
            ),
            can_afford=False,
            top_up_needed_cents=900,
            top_up_needed_dollars=9.00,
            enforcement_decision=EnforcementDecision(
                action="reject",
                reason="insufficient_balance",
                message="User does not have enough balance",
            ),
        )
        mock_create_cost_estimator.return_value = MagicMock()
        mock_create_cost_estimator.return_value.estimate_request_cost_cents.return_value = (
            1000
        )

        # Execute
        result = check_user_can_afford_request(user, [], session)

        assert_that(result.can_proceed, equal_to(False))
        assert result.balance_warning is not None
        assert_that(result.balance_warning.has_warning, equal_to(True))
        assert_that(
            result.balance_warning.warning_type, equal_to("insufficient_balance")
        )
        assert_that(
            result.balance_warning.message,
            equal_to("User does not have enough balance"),
        )
        assert_that(result.balance_warning.current_balance_cents, equal_to(100))
        assert_that(result.balance_warning.current_balance_dollars, equal_to(1.00))
        assert_that(result.balance_warning.estimated_cost_cents, equal_to(1000))
        assert_that(result.balance_warning.estimated_cost_dollars, equal_to(10.00))
        assert_that(result.balance_warning.top_up_needed_cents, equal_to(900))
        assert_that(result.balance_warning.top_up_needed_dollars, equal_to(9.00))
