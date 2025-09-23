import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session
from stripe import StripeError

from src.accounting.models import User, UserAccountDetails, UserAccountStatus
from src.accounting.stripe_service import StripeService


class TestStripeService_HandleSubscriptionUpdated:
    """Test cases for handle_subscription_updated method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    @pytest.fixture
    def user_account_details(self, session: Session):
        """Create a test user with account details."""
        user = User(
            id=uuid.uuid4(),
            name="Test User",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
            is_verified=True,
            last_logged_in=datetime.now(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Get the automatically created UserAccountDetails
        user_account_details = user.account_details
        user_account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        user_account_details.stripe_customer_id = "cus_test123"
        session.add(user_account_details)
        session.commit()
        session.refresh(user_account_details)

        return user_account_details

    def _create_subscription_event(
        self,
        subscription_id: str = "sub_test123",
        customer_id: str = "cus_test123",
        cancel_at: int = None,
        canceled_at: int = None,
        cancel_at_period_end: bool = None,
    ) -> dict:
        """Helper method to create subscription event data."""
        subscription_data = {
            "id": subscription_id,
            "customer": customer_id,
        }

        if cancel_at is not None:
            subscription_data["cancel_at"] = cancel_at
        if canceled_at is not None:
            subscription_data["canceled_at"] = canceled_at
        if cancel_at_period_end is not None:
            subscription_data["cancel_at_period_end"] = cancel_at_period_end

        return {"data": {"object": subscription_data}}

    # Subscription Cancellation Tests

    def test_handle_subscription_updated_with_cancel_at(
        self,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test subscription cancellation with cancel_at timestamp."""
        cancel_timestamp = int((datetime.now() + timedelta(days=30)).timestamp())
        event = self._create_subscription_event(
            cancel_at=cancel_timestamp, cancel_at_period_end=True
        )

        stripe_service.handle_subscription_updated(event)

        # Refresh the user account details from database
        session.refresh(user_account_details)

        assert user_account_details.subscription_cancel_at == datetime.fromtimestamp(
            cancel_timestamp
        )
        assert user_account_details.subscription_canceled_at is None
        assert user_account_details.subscription_cancel_at_period_end is True

    def test_handle_subscription_updated_with_canceled_at(
        self,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test subscription cancellation with canceled_at timestamp."""
        canceled_timestamp = int(datetime.now().timestamp())
        event = self._create_subscription_event(
            canceled_at=canceled_timestamp, cancel_at_period_end=False
        )

        stripe_service.handle_subscription_updated(event)

        # Refresh the user account details from database
        session.refresh(user_account_details)

        assert user_account_details.subscription_cancel_at is None
        assert user_account_details.subscription_canceled_at == datetime.fromtimestamp(
            canceled_timestamp
        )
        assert user_account_details.subscription_cancel_at_period_end is False

    def test_handle_subscription_updated_with_both_timestamps(
        self,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test subscription cancellation with both cancel_at and canceled_at timestamps."""
        cancel_timestamp = int((datetime.now() + timedelta(days=30)).timestamp())
        canceled_timestamp = int(datetime.now().timestamp())
        event = self._create_subscription_event(
            cancel_at=cancel_timestamp,
            canceled_at=canceled_timestamp,
            cancel_at_period_end=True,
        )

        stripe_service.handle_subscription_updated(event)

        # Refresh the user account details from database
        session.refresh(user_account_details)

        assert user_account_details.subscription_cancel_at == datetime.fromtimestamp(
            cancel_timestamp
        )
        assert user_account_details.subscription_canceled_at == datetime.fromtimestamp(
            canceled_timestamp
        )
        assert user_account_details.subscription_cancel_at_period_end is True

    # Subscription Reactivation Tests

    def test_handle_subscription_updated_reactivation_clears_cancellation(
        self,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test subscription reactivation clears existing cancellation data."""
        # Set up existing cancellation data
        user_account_details.subscription_cancel_at = datetime.now() + timedelta(
            days=30
        )
        user_account_details.subscription_canceled_at = datetime.now()
        user_account_details.subscription_cancel_at_period_end = True
        session.add(user_account_details)
        session.commit()

        # Create event with no cancellation data (reactivation)
        event = self._create_subscription_event()

        stripe_service.handle_subscription_updated(event)

        # Refresh the user account details from database
        session.refresh(user_account_details)

        assert user_account_details.subscription_cancel_at is None
        assert user_account_details.subscription_canceled_at is None
        assert user_account_details.subscription_cancel_at_period_end is None

    def test_handle_subscription_updated_no_op_when_no_prior_cancellation(
        self,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test no-op when no cancellation data exists and none is being added."""
        # Ensure no cancellation data exists
        assert user_account_details.subscription_cancel_at is None
        assert user_account_details.subscription_canceled_at is None
        assert user_account_details.subscription_cancel_at_period_end is None

        # Create event with no cancellation data
        event = self._create_subscription_event()

        stripe_service.handle_subscription_updated(event)

        # Refresh the user account details from database
        session.refresh(user_account_details)

        # Should remain unchanged
        assert user_account_details.subscription_cancel_at is None
        assert user_account_details.subscription_canceled_at is None
        assert user_account_details.subscription_cancel_at_period_end is None

    # Error Handling Tests

    def test_handle_subscription_updated_missing_customer_id(
        self, stripe_service: StripeService, user_account_details: UserAccountDetails
    ):
        """Test ValueError raised when customer ID is missing."""
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    # customer field is missing
                }
            }
        }

        with pytest.raises(
            ValueError, match="No customer ID found in subscription sub_test123"
        ):
            stripe_service.handle_subscription_updated(event)

    def test_handle_subscription_updated_customer_id_none(
        self, stripe_service: StripeService, user_account_details: UserAccountDetails
    ):
        """Test ValueError raised when customer ID is None."""
        event = self._create_subscription_event(customer_id=None)

        with pytest.raises(
            ValueError, match="No customer ID found in subscription sub_test123"
        ):
            stripe_service.handle_subscription_updated(event)

    def test_handle_subscription_updated_user_account_not_found(
        self, stripe_service: StripeService, caplog
    ):
        """Test handling when user account is not found - should log error and return."""
        event = self._create_subscription_event(customer_id="cus_nonexistent")

        # Should not raise exception, just log error and return
        stripe_service.handle_subscription_updated(event)

        assert (
            "No user account details found for customer cus_nonexistent" in caplog.text
        )
        assert "Subscription sub_test123 update cannot be processed" in caplog.text

    @patch("src.accounting.stripe_service.logger")
    def test_handle_subscription_updated_stripe_error(
        self,
        mock_logger,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
    ):
        """Test StripeError handling - should log and re-raise."""
        event = self._create_subscription_event(
            cancel_at=int(datetime.now().timestamp())
        )

        # Mock a StripeError during processing
        with patch.object(
            stripe_service.db, "commit", side_effect=StripeError("Stripe API error")
        ):
            with pytest.raises(StripeError):
                stripe_service.handle_subscription_updated(event)

        # Verify error was logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args_list[-1]
        assert "Stripe API error processing subscription update sub_test123" in str(
            error_call
        )

    @patch("src.accounting.stripe_service.logger")
    def test_handle_subscription_updated_database_error_with_rollback(
        self,
        mock_logger,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
    ):
        """Test database error handling - should rollback and re-raise."""
        event = self._create_subscription_event(
            cancel_at=int(datetime.now().timestamp())
        )

        # Mock rollback to track if it was called
        with patch.object(stripe_service.db, "rollback") as mock_rollback:
            # Mock a database error during commit
            with patch.object(
                stripe_service.db, "commit", side_effect=Exception("Database error")
            ):
                with pytest.raises(Exception, match="Database error"):
                    stripe_service.handle_subscription_updated(event)

        # Verify rollback was called
        mock_rollback.assert_called_once()

        # Verify error was logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args_list[-1]
        assert (
            "Unexpected error processing subscription update for subscription sub_test123"
            in str(error_call)
        )

    # Edge Cases

    def test_handle_subscription_updated_zero_timestamp(
        self,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test handling of zero timestamp (edge case) - should be treated as no cancellation."""
        event = self._create_subscription_event(cancel_at=0)

        stripe_service.handle_subscription_updated(event)

        # Refresh the user account details from database
        session.refresh(user_account_details)

        # Zero timestamp should be treated as falsy, so no cancellation data is set
        assert user_account_details.subscription_cancel_at is None
        assert user_account_details.subscription_canceled_at is None
        assert user_account_details.subscription_cancel_at_period_end is None

    def test_handle_subscription_updated_partial_cancellation_data(
        self,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
        session: Session,
    ):
        """Test handling of partial cancellation data."""
        event = self._create_subscription_event(
            cancel_at=int(datetime.now().timestamp()),
            # canceled_at is None
            cancel_at_period_end=True,
        )

        stripe_service.handle_subscription_updated(event)

        # Refresh the user account details from database
        session.refresh(user_account_details)

        assert user_account_details.subscription_cancel_at is not None
        assert user_account_details.subscription_canceled_at is None
        assert user_account_details.subscription_cancel_at_period_end is True

    @patch("src.accounting.stripe_service.logger")
    def test_handle_subscription_updated_logs_success(
        self,
        mock_logger,
        stripe_service: StripeService,
        user_account_details: UserAccountDetails,
    ):
        """Test that successful processing logs appropriate messages."""
        cancel_timestamp = int(datetime.now().timestamp())
        event = self._create_subscription_event(
            cancel_at=cancel_timestamp, cancel_at_period_end=True
        )

        stripe_service.handle_subscription_updated(event)

        # Verify info logs were called
        mock_logger.info.assert_called()
        info_calls = [str(call) for call in mock_logger.info.call_args_list]

        # Check for processing start log
        assert any(
            "Processing customer.subscription.updated event for subscription: sub_test123"
            in call
            for call in info_calls
        )

        # Check for cancellation details update log
        assert any(
            "Updated subscription cancellation details for user" in call
            for call in info_calls
        )

        # Check for success completion log
        assert any(
            "Successfully processed subscription.updated event for subscription sub_test123"
            in call
            for call in info_calls
        )
