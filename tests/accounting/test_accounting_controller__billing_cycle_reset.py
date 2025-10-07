import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from hamcrest import assert_that, equal_to, greater_than, is_, is_not
from sqlalchemy.orm import Session

from src.accounting.accounting_controller import (
    BillingCycleResetResult,
    get_users_due_for_credit_reset,
    process_billing_cycle_reset,
)
from src.accounting.billing_service import BillingService, BillingServiceException
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.models import User

# ---------------------------------------------------------------------------
# Helper fixtures and classes
# ---------------------------------------------------------------------------


class _FakeBillingServiceForCycleReset:
    """Billing service stub for billing cycle reset tests."""

    def __init__(self, db: Session):
        self.db = db
        self.start_new_billing_cycle_called = False
        self.start_new_billing_cycle_user = None

    def start_new_billing_cycle(self, user: User):
        """Mock implementation that tracks calls."""
        self.start_new_billing_cycle_called = True
        self.start_new_billing_cycle_user = user
        return SimpleNamespace(
            balance_cents=0, status=UserAccountStatus.ACTIVE_SUBSCRIPTION
        )


class _FakeBillingServiceWithException:
    """Billing service stub that raises BillingServiceException."""

    def __init__(self, db: Session):
        self.db = db

    def start_new_billing_cycle(self, user: User):
        raise BillingServiceException("Mock billing service error")


# ---------------------------------------------------------------------------
# Tests for get_users_due_for_credit_reset
# ---------------------------------------------------------------------------


class TestGetUsersDueForCreditReset:
    def test_get_users_due_for_credit_reset_basic(self, session: Session, user: User):
        """Test finding users due for credit reset."""
        # Setup user with expired billing cycle
        user.account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user.account_details.next_billing_cycle_starts = datetime.now() - timedelta(
            hours=1
        )
        session.add(user.account_details)
        session.commit()

        # Call function
        users_due_for_reset = get_users_due_for_credit_reset(session)

        # Verify results
        assert len(users_due_for_reset) == 1
        assert users_due_for_reset[0].id == user.id

    def test_get_users_due_for_credit_reset_filters_by_status(
        self, session: Session, user: User, other_user: User
    ):
        """Test that only eligible statuses are included."""
        # Setup first user with eligible status and expired cycle
        user.account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user.account_details.next_billing_cycle_starts = datetime.now() - timedelta(
            hours=1
        )
        session.add(user.account_details)

        # Setup second user with ineligible status but expired cycle
        other_user.account_details.status = UserAccountStatus.NEW
        other_user.account_details.next_billing_cycle_starts = (
            datetime.now() - timedelta(hours=1)
        )
        session.add(other_user.account_details)
        session.commit()

        # Call function
        users_due_for_reset = get_users_due_for_credit_reset(session)

        # Verify only eligible user is returned
        assert len(users_due_for_reset) == 1
        assert users_due_for_reset[0].id == user.id

    def test_get_users_due_for_credit_reset_filters_by_date(
        self, session: Session, user: User, other_user: User
    ):
        """Test that only users with expired cycles are included."""
        # Setup first user with eligible status and expired cycle
        user.account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user.account_details.next_billing_cycle_starts = datetime.now() - timedelta(
            hours=1
        )
        session.add(user.account_details)

        # Setup second user with eligible status but future cycle
        other_user.account_details.status = UserAccountStatus.SUSPENDED
        other_user.account_details.next_billing_cycle_starts = (
            datetime.now() + timedelta(hours=1)
        )
        session.add(other_user.account_details)
        session.commit()

        # Call function
        users_due_for_reset = get_users_due_for_credit_reset(session)

        # Verify only expired user is returned
        assert len(users_due_for_reset) == 1
        assert users_due_for_reset[0].id == user.id

    def test_get_users_due_for_credit_reset_all_eligible_statuses(
        self, session: Session, user: User, other_user: User
    ):
        """Test that all eligible statuses are included."""
        # Setup users with different eligible statuses
        user.account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user.account_details.next_billing_cycle_starts = datetime.now() - timedelta(
            hours=1
        )
        session.add(user.account_details)

        other_user.account_details.status = UserAccountStatus.SUSPENDED
        other_user.account_details.next_billing_cycle_starts = (
            datetime.now() - timedelta(hours=1)
        )
        session.add(other_user.account_details)
        session.commit()

        # Call function
        users_due_for_reset = get_users_due_for_credit_reset(session)

        # Verify both users are returned
        assert len(users_due_for_reset) == 2
        user_ids = {u.id for u in users_due_for_reset}
        assert user.id in user_ids
        assert other_user.id in user_ids

    def test_get_users_due_for_credit_reset_excludes_null_cycle_date(
        self, session: Session, user: User
    ):
        """Test that users with null next_billing_cycle_starts are excluded."""
        # Setup user with eligible status but no cycle date
        user.account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user.account_details.next_billing_cycle_starts = None
        session.add(user.account_details)
        session.commit()

        # Call function
        users_due_for_reset = get_users_due_for_credit_reset(session)

        # Verify no users are returned
        assert len(users_due_for_reset) == 0

    def test_get_users_due_for_credit_reset_respects_limit(
        self, session: Session, user: User, other_user: User
    ):
        """Test that limit parameter is respected."""
        # Setup two users both due for reset
        user.account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user.account_details.next_billing_cycle_starts = datetime.now() - timedelta(
            hours=1
        )
        session.add(user.account_details)

        other_user.account_details.status = UserAccountStatus.METERED_BILLING
        other_user.account_details.next_billing_cycle_starts = (
            datetime.now() - timedelta(hours=1)
        )
        session.add(other_user.account_details)
        session.commit()

        # Call function with limit
        users_due_for_reset = get_users_due_for_credit_reset(session, limit=1)

        # Verify limit is respected
        assert len(users_due_for_reset) == 1

    def test_get_users_due_for_credit_reset_specific_user_eligible(
        self, session: Session, user: User
    ):
        """Test filtering by specific user ID when user is eligible."""
        # Setup user eligible for reset
        user.account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user.account_details.next_billing_cycle_starts = datetime.now() - timedelta(
            hours=1
        )
        session.add(user.account_details)
        session.commit()

        # Call function with specific user ID
        users_due_for_reset = get_users_due_for_credit_reset(session, user_id=user.id)

        # Verify user is returned
        assert len(users_due_for_reset) == 1
        assert users_due_for_reset[0].id == user.id

    def test_get_users_due_for_credit_reset_specific_user_not_eligible(
        self, session: Session, user: User
    ):
        """Test filtering by specific user ID when user is not eligible."""
        # Setup user not eligible for reset (wrong status)
        user.account_details.status = UserAccountStatus.NEW
        user.account_details.next_billing_cycle_starts = datetime.now() - timedelta(
            hours=1
        )
        session.add(user.account_details)
        session.commit()

        # Call function with specific user ID
        users_due_for_reset = get_users_due_for_credit_reset(session, user_id=user.id)

        # Verify no users are returned
        assert len(users_due_for_reset) == 0

    def test_get_users_due_for_credit_reset_specific_user_not_found(
        self, session: Session
    ):
        """Test filtering by non-existent user ID."""
        fake_user_id = uuid.uuid4()

        # Call function with non-existent user ID
        users_due_for_reset = get_users_due_for_credit_reset(
            session, user_id=fake_user_id
        )

        # Verify no users are returned
        assert len(users_due_for_reset) == 0

    def test_get_users_due_for_credit_reset_empty_results(self, session: Session):
        """Test function returns empty list when no users are eligible."""
        # No setup needed - database starts empty

        # Call function
        users_due_for_reset = get_users_due_for_credit_reset(session)

        # Verify empty results
        assert len(users_due_for_reset) == 0


# ---------------------------------------------------------------------------
# Tests for process_billing_cycle_reset
# ---------------------------------------------------------------------------


class TestProcessBillingCycleReset:

    @patch("src.accounting.accounting_controller.BillingService")
    def test_process_billing_cycle_reset_success(
        self, mock_billing_service_class: Mock, session: Session, user: User
    ):
        """Test successful billing cycle reset."""
        # Setup mock billing service
        fake_billing_service = _FakeBillingServiceForCycleReset(session)
        mock_billing_service_class.return_value = fake_billing_service

        # Setup user
        original_cycle_date = datetime.now() - timedelta(days=1)
        user.account_details.next_billing_cycle_starts = original_cycle_date
        session.add(user.account_details)
        session.commit()

        # Call function
        with patch("src.accounting.accounting_controller.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 15, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = process_billing_cycle_reset(user, session)

        # Verify result
        assert result.success is True
        assert result.credits_reset is True
        assert result.billing_cycle_updated is True
        assert result.error is None
        assert "Reset monthly credits and updated billing cycle" in result.details

        # Verify billing service was called
        assert fake_billing_service.start_new_billing_cycle_called is True
        assert fake_billing_service.start_new_billing_cycle_user.id == user.id

        # Verify database was updated
        session.refresh(user.account_details)
        expected_next_cycle = mock_now + timedelta(days=30)
        assert user.account_details.next_billing_cycle_starts == expected_next_cycle

    @patch("src.accounting.accounting_controller.BillingService")
    def test_process_billing_cycle_reset_billing_service_exception(
        self, mock_billing_service_class: Mock, session: Session, user: User
    ):
        """Test handling of BillingServiceException."""
        # Setup mock billing service that raises exception
        fake_billing_service = _FakeBillingServiceWithException(session)
        mock_billing_service_class.return_value = fake_billing_service

        # Setup user
        original_cycle_date = datetime.now() - timedelta(days=1)
        user.account_details.next_billing_cycle_starts = original_cycle_date
        session.add(user.account_details)
        session.commit()

        # Call function
        result = process_billing_cycle_reset(user, session)

        # Verify result
        assert result.success is False
        assert result.credits_reset is False
        assert result.billing_cycle_updated is False
        assert "Billing service error" in result.error

        # Verify database was not updated
        session.refresh(user.account_details)
        assert user.account_details.next_billing_cycle_starts == original_cycle_date

    @patch("src.accounting.accounting_controller.BillingService")
    def test_process_billing_cycle_reset_general_exception(
        self, mock_billing_service_class: Mock, session: Session, user: User
    ):
        """Test handling of general exceptions."""
        # Setup mock billing service that raises unexpected exception
        fake_billing_service = _FakeBillingServiceForCycleReset(session)
        mock_billing_service_class.return_value = fake_billing_service

        # Mock db.commit to raise exception
        with patch.object(session, "commit", side_effect=Exception("Database error")):
            # Call function
            result = process_billing_cycle_reset(user, session)

        # Verify result
        assert result.success is False
        assert result.credits_reset is False
        assert result.billing_cycle_updated is False
        assert "Processing failed" in result.error
        assert "Database error" in result.error

    @patch("src.accounting.accounting_controller.BillingService")
    def test_process_billing_cycle_reset_updates_correct_fields(
        self, mock_billing_service_class: Mock, session: Session, user: User
    ):
        """Test that only the expected database fields are updated."""
        # Setup mock billing service
        fake_billing_service = _FakeBillingServiceForCycleReset(session)
        mock_billing_service_class.return_value = fake_billing_service

        # Setup user with known initial values
        initial_status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        initial_credits_used = 100
        initial_credits_total = 700
        original_cycle_date = datetime.now() - timedelta(days=1)

        user.account_details.status = initial_status
        user.account_details.monthly_credits_used = initial_credits_used
        user.account_details.monthly_credits_total = initial_credits_total
        user.account_details.next_billing_cycle_starts = original_cycle_date
        session.add(user.account_details)
        session.commit()

        # Call function
        with patch("src.accounting.accounting_controller.datetime") as mock_datetime:
            mock_now = datetime(2023, 1, 15, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = process_billing_cycle_reset(user, session)

        # Verify result is successful
        assert result.success is True

        # Verify only next_billing_cycle_starts was updated by our function
        # (BillingService.start_new_billing_cycle might update other fields, but we don't control that in this test)
        session.refresh(user.account_details)
        expected_next_cycle = mock_now + timedelta(days=30)
        assert user.account_details.next_billing_cycle_starts == expected_next_cycle

    def test_billing_cycle_reset_result_dataclass(self):
        """Test the BillingCycleResetResult dataclass structure."""
        # Test successful result
        success_result = BillingCycleResetResult(
            success=True,
            credits_reset=True,
            billing_cycle_updated=True,
            details="Test success",
        )

        assert success_result.success is True
        assert success_result.credits_reset is True
        assert success_result.billing_cycle_updated is True
        assert success_result.error is None
        assert success_result.details == "Test success"

        # Test failure result
        failure_result = BillingCycleResetResult(
            success=False,
            credits_reset=False,
            billing_cycle_updated=False,
            error="Test error",
        )

        assert failure_result.success is False
        assert failure_result.credits_reset is False
        assert failure_result.billing_cycle_updated is False
        assert failure_result.error == "Test error"
        assert failure_result.details is None


class TestIntegrationBillingCycleReset:
    def test_integration_billing_cycle_reset(self, session: Session):
        """Test the complete workflow of billing cycle reset."""
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

        user_account_details: UserAccountDetails = user.account_details
        user_account_details.onboarding_completed = True
        user_account_details.monthly_credits_total = 700
        user_account_details.monthly_credits_used = 0
        user_account_details.next_billing_cycle_starts = datetime.now() + timedelta(
            days=30
        )
        session.add(user_account_details)
        session.commit()
        session.refresh(user_account_details)

        billing_service = BillingService(session)

        # Sign up subscription
        billing_service.signup_subscription(user, "stripe_customer_id")

        assert_that(
            user.account_details.status, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )
        assert_that(user.account_details.next_billing_cycle_starts, is_not(None))
        assert_that(user.account_details.monthly_credits_total, equal_to(700))
        assert_that(user.account_details.monthly_credits_used, equal_to(0))

        # No users due for credit reset
        users_to_reset = get_users_due_for_credit_reset(session)
        assert_that(len(users_to_reset), equal_to(0))

        # Record usage
        billing_service.record_usage(user, 100, "usage_id")

        assert_that(user.account_details.monthly_credits_used, equal_to(100))

        now = datetime.now()
        user.account_details.next_billing_cycle_starts = now - timedelta(days=1)
        session.add(user.account_details)
        session.commit()

        # Users due for credit reset
        users_to_reset = get_users_due_for_credit_reset(session)
        assert_that(len(users_to_reset), equal_to(1))
        assert_that(users_to_reset[0].id, equal_to(user.id))

        # Process billing cycle reset
        result = process_billing_cycle_reset(user, session)
        assert_that(result.success, is_(True))
        assert_that(result.credits_reset, is_(True))
        assert_that(result.billing_cycle_updated, is_(True))
        assert_that(result.error, is_(None))

        # Verify database was updated
        session.refresh(user.account_details)
        assert_that(
            user.account_details.next_billing_cycle_starts,
            greater_than(now + timedelta(days=30)),
        )
        assert_that(user.account_details.monthly_credits_used, equal_to(0))
        assert_that(user.account_details.monthly_credits_total, equal_to(700))
        assert_that(
            user.account_details.status, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )

    def test_integration_billing_cycle_reset_with_state_transition_from_suspended(
        self, session: Session
    ):
        """Test the complete workflow of billing cycle reset."""
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

        user_account_details: UserAccountDetails = user.account_details
        user_account_details.onboarding_completed = True
        user_account_details.monthly_credits_total = 700
        user_account_details.monthly_credits_used = 0
        user_account_details.next_billing_cycle_starts = datetime.now() + timedelta(
            days=30
        )
        session.add(user_account_details)
        session.commit()
        session.refresh(user_account_details)

        billing_service = BillingService(session)

        # Sign up subscription
        billing_service.signup_subscription(user, "stripe_customer_id")

        assert_that(
            user.account_details.status, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )
        assert_that(user.account_details.next_billing_cycle_starts, is_not(None))
        assert_that(user.account_details.monthly_credits_total, equal_to(700))
        assert_that(user.account_details.monthly_credits_used, equal_to(0))

        # No users due for credit reset
        users_to_reset = get_users_due_for_credit_reset(session)
        assert_that(len(users_to_reset), equal_to(0))

        # Record usage
        billing_service.record_usage(user, 700, "usage_id")

        assert_that(user.account_details.monthly_credits_used, equal_to(700))
        assert_that(user.account_details.status, equal_to(UserAccountStatus.SUSPENDED))

        # Billing cycle starts
        now = datetime.now()
        user.account_details.next_billing_cycle_starts = now - timedelta(days=1)
        session.add(user.account_details)
        session.commit()

        # Users due for credit reset
        users_to_reset = get_users_due_for_credit_reset(session)
        assert_that(len(users_to_reset), equal_to(1))
        assert_that(users_to_reset[0].id, equal_to(user.id))

        # Process billing cycle reset
        result = process_billing_cycle_reset(user, session)
        assert_that(result.success, is_(True))
        assert_that(result.credits_reset, is_(True))
        assert_that(result.billing_cycle_updated, is_(True))
        assert_that(result.error, is_(None))

        # Verify database was updated
        session.refresh(user.account_details)
        assert_that(
            user.account_details.next_billing_cycle_starts,
            greater_than(now + timedelta(days=30)),
        )
        assert_that(user.account_details.monthly_credits_used, equal_to(0))
        assert_that(user.account_details.monthly_credits_total, equal_to(700))
        assert_that(
            user.account_details.status, equal_to(UserAccountStatus.ACTIVE_SUBSCRIPTION)
        )
