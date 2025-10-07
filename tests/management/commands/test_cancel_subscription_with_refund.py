import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.accounting.accounting_controller import SubscriptionCancellationResult
from src.models import User


class TestCancelSubscriptionWithRefund:
    """Unit tests for cancel_subscription_with_refund management command."""

    @pytest.mark.asyncio
    async def test_execute_with_email_success(self, session: Session, user: User):
        """Test successful subscription cancellation using email."""
        from src.management.commands.cancel_subscription_with_refund import execute

        # Ensure user has stripe_customer_id
        user.account_details.stripe_customer_id = "cus_test123"
        session.add(user.account_details)
        session.commit()

        # Mock all dependencies
        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            # Setup mocks
            mock_get_db.return_value = iter([session])

            mock_result = SubscriptionCancellationResult(
                billing_cancelled=True,
                stripe_cancelled=True,
                refunds_processed=1,
                total_refunded_cents=500,
                success=True,
                details="Refunded 500 cents",
            )
            mock_cancel.return_value = mock_result

            # Execute command
            await execute(email=user.email)

            # Verify controller function was called with correct parameters
            mock_cancel.assert_called_once()
            call_args = mock_cancel.call_args
            assert call_args[1]["user"].email == user.email
            assert call_args[1]["db"] == session
            assert call_args[1]["refund_last_n_days"] == 30

    @pytest.mark.asyncio
    async def test_execute_with_user_id_success(self, session: Session, user: User):
        """Test successful subscription cancellation using user ID."""
        from src.management.commands.cancel_subscription_with_refund import execute

        # Ensure user has stripe_customer_id
        user.account_details.stripe_customer_id = "cus_test123"
        session.add(user.account_details)
        session.commit()

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            mock_get_db.return_value = iter([session])

            mock_result = SubscriptionCancellationResult(
                billing_cancelled=True,
                stripe_cancelled=True,
                refunds_processed=1,
                total_refunded_cents=500,
                success=True,
                details="Refunded 500 cents",
            )
            mock_cancel.return_value = mock_result

            await execute(user_id=str(user.id))

            mock_cancel.assert_called_once()
            call_args = mock_cancel.call_args
            assert call_args[1]["user"].id == user.id

    @pytest.mark.asyncio
    async def test_execute_with_failed_cancellation(self, session: Session, user: User):
        """Test handling of failed subscription cancellation."""
        from src.management.commands.cancel_subscription_with_refund import execute

        # Ensure user has stripe_customer_id
        user.account_details.stripe_customer_id = "cus_test123"
        session.add(user.account_details)
        session.commit()

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            mock_get_db.return_value = iter([session])

            mock_result = SubscriptionCancellationResult(
                billing_cancelled=False,
                stripe_cancelled=False,
                refunds_processed=0,
                total_refunded_cents=0,
                success=False,
                error="Stripe operation failed",
            )
            mock_cancel.return_value = mock_result

            await execute(email=user.email)

            mock_cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_validates_no_parameters(self):
        """Test that execute raises ValueError when neither email nor user_id provided."""
        from src.management.commands.cancel_subscription_with_refund import execute

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
        ):

            with pytest.raises(
                ValueError, match="Either --email or --user-id must be provided"
            ):
                await execute()

    @pytest.mark.asyncio
    async def test_execute_validates_both_parameters(self):
        """Test that execute raises ValueError when both email and user_id provided."""
        from src.management.commands.cancel_subscription_with_refund import execute

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
        ):

            with pytest.raises(
                ValueError, match="Provide either --email or --user-id, not both"
            ):
                await execute(email="test@example.com", user_id="some-uuid")

    @pytest.mark.asyncio
    async def test_execute_user_not_found_by_email(self, session: Session):
        """Test handling when user is not found by email."""
        from src.management.commands.cancel_subscription_with_refund import execute

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            mock_get_db.return_value = iter([session])

            await execute(email="nonexistent@example.com")

            # Should not call the controller function
            mock_cancel.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_user_not_found_by_id(self, session: Session):
        """Test handling when user is not found by ID."""
        from src.management.commands.cancel_subscription_with_refund import execute

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            mock_get_db.return_value = iter([session])

            fake_uuid = str(uuid.uuid4())
            await execute(user_id=fake_uuid)

            mock_cancel.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_invalid_user_id_format(self, session: Session):
        """Test handling of invalid user ID format."""
        from src.management.commands.cancel_subscription_with_refund import execute

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            mock_get_db.return_value = iter([session])

            await execute(user_id="invalid-uuid-format")

            mock_cancel.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_user_without_stripe_customer_id(
        self, session: Session, user: User
    ):
        """Test handling when user has no Stripe customer ID."""
        from src.management.commands.cancel_subscription_with_refund import execute

        # Remove stripe_customer_id from user
        user.account_details.stripe_customer_id = None
        session.add(user.account_details)
        session.commit()

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            mock_get_db.return_value = iter([session])

            await execute(email=user.email)

            # Should not call the controller function
            mock_cancel.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_handles_unexpected_exception(
        self, session: Session, user: User
    ):
        """Test handling of unexpected exceptions during cancellation."""
        from src.management.commands.cancel_subscription_with_refund import execute

        # Ensure user has stripe_customer_id
        user.account_details.stripe_customer_id = "cus_test123"
        session.add(user.account_details)
        session.commit()

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.capture_ai_exception"
            ) as mock_capture,
        ):

            mock_get_db.return_value = iter([session])
            mock_cancel.side_effect = Exception("Unexpected error")

            # Should not raise exception, should handle it gracefully
            await execute(email=user.email)

            # Verify exception was captured
            mock_capture.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_partial_refund(self, session: Session, user: User):
        """Test cancellation with partial refund (some invoices failed)."""
        from src.management.commands.cancel_subscription_with_refund import execute

        # Ensure user has stripe_customer_id
        user.account_details.stripe_customer_id = "cus_test123"
        session.add(user.account_details)
        session.commit()

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            mock_get_db.return_value = iter([session])

            mock_result = SubscriptionCancellationResult(
                billing_cancelled=True,
                stripe_cancelled=True,
                refunds_processed=2,
                total_refunded_cents=300,
                success=True,
                details="Refunded 300 cents from 2 invoices",
            )
            mock_cancel.return_value = mock_result

            await execute(email=user.email)

            mock_cancel.assert_called_once()
            call_args = mock_cancel.call_args
            assert call_args[1]["refund_last_n_days"] == 30

    @pytest.mark.asyncio
    async def test_execute_email_case_insensitive(self, session: Session, user: User):
        """Test that email lookup is case-insensitive."""
        from src.management.commands.cancel_subscription_with_refund import execute

        # Ensure user has stripe_customer_id
        user.account_details.stripe_customer_id = "cus_test123"
        session.add(user.account_details)
        session.commit()

        with (
            patch(
                "src.management.commands.cancel_subscription_with_refund.get_db"
            ) as mock_get_db,
            patch(
                "src.management.commands.cancel_subscription_with_refund.cancel_subscription_with_refund"
            ) as mock_cancel,
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_operation_context"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.add_breadcrumb"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.track_ai_metrics"
            ),
            patch(
                "src.management.commands.cancel_subscription_with_refund.set_user_context"
            ),
        ):

            mock_get_db.return_value = iter([session])

            mock_result = SubscriptionCancellationResult(
                billing_cancelled=True,
                stripe_cancelled=True,
                refunds_processed=1,
                total_refunded_cents=500,
                success=True,
            )
            mock_cancel.return_value = mock_result

            # Use uppercase email
            await execute(email=user.email.upper())

            # Should still find the user and call cancel
            mock_cancel.assert_called_once()
