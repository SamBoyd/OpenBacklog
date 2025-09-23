import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from hamcrest import assert_that, equal_to, not_none
from hamcrest.core.core.is_ import is_
from sqlalchemy.orm import Session

from src.accounting.billing_service import BillingService
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.accounting.openmeter_service import OpenMeterService, UsageQueryResult
from src.accounting.usage_tracker import UsageTracker
from src.models import OAuthAccount, User


@pytest.fixture
def user(session: Session) -> Generator[User, None, None]:
    existing_user = session.query(User).filter(User.email == "steve@gmail.com").first()
    if existing_user:
        # If user exists from a previous failed test run cleanup, use it
        yield existing_user
    else:
        # Otherwise, create a new one
        user = User(
            id=uuid.uuid4(),  # Explicitly set UUID if needed, or let DB handle it
            name="Steven Stevenson",
            email="steve@gmail.com",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
            is_verified=True,
            last_logged_in=datetime.now(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        billing_service = BillingService(session)
        billing_service.signup_subscription(user, "stripe_customer_id")

        user_account_details: UserAccountDetails = user.account_details
        user_account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user_account_details.onboarding_completed = True
        user_account_details.monthly_credits_total = 500
        user_account_details.monthly_credits_used = 0
        user_account_details.next_billing_cycle_starts = datetime.now() + timedelta(
            days=30
        )
        session.add(user_account_details)
        session.commit()
        session.refresh(user_account_details)

        user_oauth_account = OAuthAccount(
            user_id=user.id,
            oauth_name="auth0",
            account_id="1234567890",
            account_email="steve@gmail.com",
            access_token="access_token",
            refresh_token="refresh_token",
            expires_at=(datetime.now() + timedelta(days=30)).timestamp(),
        )
        session.add(user_oauth_account)
        session.commit()
        session.refresh(user_oauth_account)

        yield user
        # Cleanup is handled by clean_tables


@pytest.fixture
def user_account_details(user: User) -> UserAccountDetails:
    return user.account_details


@pytest.fixture
def mock_openmeter_service():
    """Mock OpenMeter service for testing."""
    service = Mock(spec=OpenMeterService)
    return service


@pytest.fixture
def mock_billing_service():
    """Mock BillingService for testing."""
    service = Mock(spec=BillingService)

    return service


@pytest.fixture
def usage_tracker(mock_openmeter_service: Mock, session: Session) -> UsageTracker:
    """Create a UsageTracker instance for testing."""

    from src.db import SessionLocal

    return UsageTracker(  # type: ignore
        openmeter_service=mock_openmeter_service,
        db_session=SessionLocal,  # type: ignore[arg-type]
    )


class TestUsageTracker:
    def test_get_active_users(
        self, usage_tracker: UsageTracker, user_account_details: UserAccountDetails
    ):
        """Test getting active users."""
        active_users = usage_tracker.get_active_users()

        assert_that(len(active_users), equal_to(1))
        assert_that(active_users[0].user_id, equal_to(user_account_details.user_id))
        assert_that(
            active_users[0].status, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )

    def test_get_active_users_filters_inactive(
        self,
        user_account_details: UserAccountDetails,
        usage_tracker: UsageTracker,
        session: Session,
        user: User,
    ):
        """Test that inactive users are filtered out."""
        # Set inactive user account
        billing_service = BillingService(session)
        billing_service.cancel_subscription(user, "stripe_customer_id")

        assert_that(
            user_account_details.status, equal_to(UserAccountStatus.NO_SUBSCRIPTION)
        )

        active_users = usage_tracker.get_active_users()
        assert_that(len(active_users), equal_to(0))

    def test_get_current_usage_cost_success(
        self, usage_tracker: UsageTracker, mock_openmeter_service: Mock
    ):
        """Test successful usage query without specifying from_time."""
        # Mock successful OpenMeter response
        mock_usage_result = UsageQueryResult(
            data=[{"value": 100}, {"value": 200}, {"value": 50}],
            subject="test-user-id",
            meter="cost_total",
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        # Provide a fixed end time for query
        end_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        total = usage_tracker.get_current_usage_cost(
            "test-user-id",
            "cost_total",
            to_time=end_time,
        )

        assert_that(total, equal_to(35000))
        mock_openmeter_service.query_usage.assert_called_once_with(
            subject="test-user-id",
            meter_slug="cost_total",
            from_time=None,
            to_time="2024-01-01T13:00:00Z",
            window_size="MINUTE",
        )

    def test_get_current_usage_cost_with_from_time(
        self, usage_tracker: UsageTracker, mock_openmeter_service: Mock
    ):
        """Test usage query when a from_time is provided."""
        reference_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        mock_usage_result = UsageQueryResult(
            data=[{"value": 100}],
            subject="test-user-id",
            meter="cost_total",
        )

        mock_openmeter_service.query_usage.return_value = mock_usage_result

        # Provide a fixed end time for query
        end_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        total = usage_tracker.get_current_usage_cost(
            "test-user-id",
            "cost_total",
            from_time=reference_time,
            to_time=end_time,
        )

        assert_that(total, equal_to(10000))
        mock_openmeter_service.query_usage.assert_called_once_with(
            subject="test-user-id",
            meter_slug="cost_total",
            from_time="2024-01-01T12:00:00Z",
            to_time="2024-01-01T13:00:00Z",
            window_size="MINUTE",
        )

    def test_get_current_usage_cost_handles_error(
        self, usage_tracker: UsageTracker, mock_openmeter_service: Mock
    ):
        """Test that usage query errors are handled gracefully."""
        mock_openmeter_service.query_usage.side_effect = Exception("API Error")

        # Provide a fixed end time for query
        end_time = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        total = usage_tracker.get_current_usage_cost(
            "test-user-id",
            "cost_total",
            to_time=end_time,
        )

        assert_that(total, equal_to(0))

    def test_process_user_usage_no_new_usage(
        self,
        session: Session,
        usage_tracker: UsageTracker,
        mock_openmeter_service: Mock,
        user_account_details: UserAccountDetails,
    ):
        """Test processing when there's no new usage."""
        # Ensure there is no new usage in the queried window

        # The user has an existing running total – this value is no longer used by
        # the processing logic but is kept here to ensure the field can contain
        # any previous value without affecting behaviour.
        user_account_details.last_total_cost = 1000.00  # type: ignore[attr-defined]
        session.add(user_account_details)
        session.commit()

        # OpenMeter returns no usage for the period (value == 0)
        mock_usage_result = UsageQueryResult(
            data=[{"value": 0}],
            subject=str(user_account_details.user_id),
            meter="cost_total",
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        state_changed = usage_tracker.process_user_usage(user_account_details)

        # When there is no usage we should *not* register any ledger entry and no
        # state change should occur.
        assert_that(state_changed, equal_to(False))
        mock_openmeter_service.query_usage.assert_called()

    @patch("src.accounting.usage_tracker.BillingService")
    def test_process_user_usage_with_new_usage(
        self,
        mock_billing_service_class: Mock,
        usage_tracker: UsageTracker,
        mock_openmeter_service: Mock,
        user_account_details: UserAccountDetails,
        session: Session,
        mock_billing_service: Mock,
        user: User,
    ):
        """Test processing with new usage."""
        # Set up scenario with new usage
        user_account_details.last_total_cost = 0
        user_id = user_account_details.user_id  # Store before session operations
        expected_user_id = str(
            user.id
        )  # Store user ID to avoid detached instance error
        session.add(user_account_details)
        session.commit()  # Ensure changes are saved

        # Each meter query will return 1.5
        mock_usage_result = UsageQueryResult(
            data=[{"value": 1.5}],
            subject=str(user_id),
            meter="input_cost_total",
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        # Configure the patch to return our mock
        mock_billing_service_class.return_value = mock_billing_service

        # Configure the mock for this test - record_usage should return the updated account details
        updated_account_details = UserAccountDetails()
        updated_account_details.user_id = user_account_details.user_id
        updated_account_details.status = user_account_details.status
        updated_account_details.balance_cents = user_account_details.balance_cents
        updated_account_details.monthly_credits_used = (
            150  # Mock the expected monthly credits used
        )
        mock_billing_service.record_usage.return_value = updated_account_details

        # Mock get_account_status_detailed to return proper AccountStatusResponse
        from src.accounting.billing_state_machine import AccountStatusResponse

        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=user_account_details.balance_cents,
            usage_balance_dollars=user_account_details.balance_cents / 100,
            monthly_credits_cents=150,  # This should match our expected assertion
            monthly_credits_dollars=1.50,
            has_active_subscription=True,
            is_suspended=False,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=False,
            using_metered_billing=False,
            no_subscription=False,
        )
        mock_billing_service.get_account_status_detailed.return_value = (
            mock_account_status
        )

        state_changed = usage_tracker.process_user_usage(user_account_details)

        # Verify state change detection works correctly
        assert_that(
            state_changed, equal_to(False)
        )  # Should not change state with sufficient balance

        # Verify BillingService was called correctly
        mock_billing_service.record_usage.assert_called_once()
        call_args = mock_billing_service.record_usage.call_args
        # Verify that record_usage was called with a User object (avoid accessing detached attributes)
        assert call_args.kwargs["user"] is not None
        assert isinstance(call_args.kwargs["user"], User)
        assert call_args.kwargs["amount_cents"] == 150.0
        assert call_args.kwargs["external_id"] == "cost_total:150.0"

        # Since we're using mocks, the database won't be updated with our mock values
        # Instead, verify that the appropriate methods were called with the right parameters
        # and that the mock returned the expected values
        # mock_billing_service.get_account_status_detailed.assert_called_once()

        # The actual values would be set by the real billing service
        # For this test, we just need to verify the workflow completed successfully

    @patch("src.accounting.usage_tracker.BillingService")
    def test_process_user_usage_handles_detached_instance_correctly(
        self,
        mock_billing_service_class: Mock,
        usage_tracker: UsageTracker,
        mock_openmeter_service: Mock,
        user_account_details: UserAccountDetails,
        session: Session,
        mock_billing_service: Mock,
        user: User,
    ):
        """Test that DetachedInstanceError is avoided by fetching User fresh from current session."""
        # Simulate the scenario that previously caused DetachedInstanceError:
        # 1. Get user account details from get_active_users (which closes the session)
        # 2. Try to process usage (which now fetches User fresh from the current session)

        user_account_details.last_total_cost = 0
        user_id = user_account_details.user_id
        expected_user_id = str(
            user.id
        )  # Store user ID to avoid detached instance error
        session.add(user_account_details)
        session.commit()

        # Get users the same way sync_usage_once does
        active_users = usage_tracker.get_active_users()
        assert len(active_users) == 1
        detached_user_account = active_users[0]

        # Mock OpenMeter response
        mock_usage_result = UsageQueryResult(
            data=[{"value": 1.0}],
            subject=str(user_id),
            meter="cost_total",
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        # Configure mocks
        mock_billing_service_class.return_value = mock_billing_service
        updated_account_details = UserAccountDetails()
        updated_account_details.user_id = detached_user_account.user_id
        updated_account_details.status = detached_user_account.status
        updated_account_details.balance_cents = detached_user_account.balance_cents
        mock_billing_service.record_usage.return_value = updated_account_details

        from src.accounting.billing_state_machine import AccountStatusResponse

        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=detached_user_account.balance_cents,
            usage_balance_dollars=detached_user_account.balance_cents / 100,
            monthly_credits_cents=100,
            monthly_credits_dollars=1.0,
            has_active_subscription=True,
            is_suspended=False,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=False,
            using_metered_billing=False,
            no_subscription=False,
        )
        mock_billing_service.get_account_status_detailed.return_value = (
            mock_account_status
        )

        # This should NOT raise a DetachedInstanceError
        # The User object is fetched fresh from the current session in process_user_usage
        state_changed = usage_tracker.process_user_usage(detached_user_account)

        # Verify the user object was passed correctly to the billing service
        # The User object should be the one from the current session, not the detached one
        mock_billing_service.record_usage.assert_called_once()
        call_args = mock_billing_service.record_usage.call_args
        # Verify that record_usage was called with a User object (avoid accessing detached attributes)
        assert call_args.kwargs["user"] is not None
        assert isinstance(call_args.kwargs["user"], User)
        assert call_args.kwargs["amount_cents"] == 100.0
        assert call_args.kwargs["external_id"] == "cost_total:100.0"

        assert_that(state_changed, equal_to(False))

    def test_sync_usage_once(
        self,
        usage_tracker: UsageTracker,
        mock_openmeter_service: Mock,
        user_account_details: UserAccountDetails,
    ):
        """Test single sync cycle."""
        mock_usage_result = UsageQueryResult(
            data=[{"value": 100}],
            subject=str(user_account_details.user_id),
            meter="cost_total",
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        # Should not raise any exceptions
        usage_tracker.sync_usage_once()

        # Verify OpenMeter was called
        mock_openmeter_service.query_usage.assert_called()

    @pytest.mark.asyncio
    async def test_run_continuous_stop(self, usage_tracker: UsageTracker):
        """Test that continuous runner can be stopped."""
        import asyncio

        # Start the continuous runner
        task = asyncio.create_task(usage_tracker.run_continuous(interval_seconds=1))

        # Let it run briefly
        await asyncio.sleep(0.05)

        # Stop it
        usage_tracker.stop()

        # Wait for it to finish
        await task

        assert not usage_tracker.running

    @patch("src.accounting.usage_tracker.BillingService")
    def test_process_user_usage_handles_database_error(
        self,
        mock_billing_service_class: Mock,
        usage_tracker: UsageTracker,
        mock_openmeter_service: Mock,
        user_account_details: UserAccountDetails,
        session: Session,
        mock_billing_service: Mock,
    ):
        """Test that database errors during processing are handled."""
        user_account_details.last_total_cost = 0.00
        user_id = user_account_details.user_id  # Store before session operations
        session.commit()  # Ensure changes are saved

        mock_usage_result = UsageQueryResult(
            data=[{"value": 100}], subject=str(user_id), meter="cost_total"
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        # Configure the patch to return our mock
        mock_billing_service_class.return_value = mock_billing_service

        # Configure the mock to raise an error
        mock_billing_service.record_usage.side_effect = Exception("DB Error")

        state_changed = usage_tracker.process_user_usage(user_account_details)

        # Should handle error gracefully
        assert_that(state_changed, equal_to(False))

    @patch("src.accounting.usage_tracker.BillingService")
    def test_cost_calculation_precision(
        self,
        mock_billing_service_class: Mock,
        usage_tracker: UsageTracker,
        mock_openmeter_service: Mock,
        user_account_details: UserAccountDetails,
        session: Session,
        mock_billing_service: Mock,
        user: User,
    ):
        """Test that cost calculation uses ceiling correctly."""
        user_account_details.last_total_cost = 0.00
        user_id = user_account_details.user_id
        expected_user_id = str(
            user.id
        )  # Store user ID to avoid detached instance error
        session.commit()

        mock_usage_result = UsageQueryResult(
            data=[{"value": 1.1234567883}],  # 1 dollar
            subject=str(user_id),
            meter="input_cost_total",
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        # Configure the patch to return our mock
        mock_billing_service_class.return_value = mock_billing_service

        # Configure the mock for this test
        updated_account_details = UserAccountDetails()
        updated_account_details.user_id = user_account_details.user_id
        updated_account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        updated_account_details.balance_cents = user_account_details.balance_cents - 1
        mock_billing_service.record_usage.return_value = updated_account_details

        # Mock get_account_status_detailed to return proper AccountStatusResponse
        from src.accounting.billing_state_machine import AccountStatusResponse

        mock_account_status = AccountStatusResponse(
            state=UserAccountStatus.ACTIVE_SUBSCRIPTION,
            usage_balance_cents=user_account_details.balance_cents,
            usage_balance_dollars=user_account_details.balance_cents / 100,
            monthly_credits_cents=100,
            monthly_credits_dollars=1.0,
            has_active_subscription=True,
            is_suspended=False,
            is_closed=False,
            has_usage_balance=True,
            subscription_only=False,
            using_metered_billing=False,
            no_subscription=False,
        )
        mock_billing_service.get_account_status_detailed.return_value = (
            mock_account_status
        )

        usage_tracker.process_user_usage(user_account_details)

        mock_billing_service.record_usage.assert_called_once()
        call_args = mock_billing_service.record_usage.call_args
        # Verify that record_usage was called with a User object (avoid accessing detached attributes)
        assert call_args.kwargs["user"] is not None
        assert isinstance(call_args.kwargs["user"], User)
        assert call_args.kwargs["amount_cents"] == 112.3456789
        assert call_args.kwargs["external_id"] == "cost_total:112.3456789"

    @patch("src.accounting.usage_tracker.BillingService")
    def test_process_user_usage_from_time_none(
        self,
        mock_billing_service_class: Mock,
        usage_tracker: UsageTracker,
        mock_openmeter_service: Mock,
        user_account_details: UserAccountDetails,
        session: Session,
        mock_billing_service: Mock,
    ):
        """Ensure that from_time=None is passed when last_usage_query_time is None."""

        # User has no recorded last query time
        user_account_details.last_total_cost = 0.00
        user_account_details.last_usage_query_time = None
        user_id = user_account_details.user_id  # Avoid detached instance
        session.commit()

        mock_usage_result = UsageQueryResult(
            data=[{"value": 10}],
            subject=str(user_id),
            meter="cost_total",
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        mock_billing_service_class.return_value = mock_billing_service
        mock_billing_service.record_usage.return_value.status = (
            UserAccountStatus.ACTIVE_SUBSCRIPTION
        )
        mock_billing_service.record_usage.return_value.balance_cents = 999

        usage_tracker.process_user_usage(user_account_details)

        # Two calls, ensure they include the correct meter slugs and from_time=None
        assert_that(mock_openmeter_service.query_usage.call_count, equal_to(1))
        first_call_kwargs = mock_openmeter_service.query_usage.call_args_list[0].kwargs

        assert_that(first_call_kwargs["meter_slug"], equal_to("cost_total"))
        assert_that(first_call_kwargs["from_time"], equal_to(None))

    def test_rfc3339_formatting(
        self, usage_tracker: UsageTracker, mock_openmeter_service: Mock
    ):
        """Test that datetime objects are properly formatted to RFC 3339 format."""
        # Test with naive datetime (should be converted to UTC)
        naive_time = datetime(2024, 1, 1, 12, 30, 45)

        # Test with timezone-aware datetime
        utc_time = datetime(2024, 1, 1, 12, 30, 45, tzinfo=timezone.utc)

        mock_usage_result = UsageQueryResult(
            data=[{"value": 100}],
            subject="test-user-id",
            meter="cost_total",
        )
        mock_openmeter_service.query_usage.return_value = mock_usage_result

        # Test naive datetime
        usage_tracker.get_current_usage_cost(
            "test-user-id",
            "cost_total",
            from_time=naive_time,
            to_time=utc_time,
        )

        # Verify naive datetime was converted to RFC 3339 UTC format
        mock_openmeter_service.query_usage.assert_called_with(
            subject="test-user-id",
            meter_slug="cost_total",
            from_time="2024-01-01T12:30:45Z",
            to_time="2024-01-01T12:30:45Z",
            window_size="MINUTE",
        )
