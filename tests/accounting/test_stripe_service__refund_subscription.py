from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session
from stripe import InvalidRequestError

from src.accounting.models import UserAccountDetails
from src.accounting.stripe_service import (
    CancellationRefundResult,
    RefundResult,
    StripeService,
)


class FindActiveSubscription:
    """Test cases for find_active_subscription method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    @patch("src.accounting.stripe_service.stripe")
    def test_find_active_subscription_success(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test successful retrieval of active subscription."""
        # Mock subscription data
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_subscription.customer = "cus_test123"

        mock_stripe.Subscription.list.return_value.data = [mock_subscription]

        # Call the method
        result = stripe_service.find_active_subscription("cus_test123")

        assert result is not None

        # Verify Stripe API was called correctly
        mock_stripe.Subscription.list.assert_called_once_with(
            customer="cus_test123", status="active", limit=1
        )

        # Verify correct subscription returned
        assert result == mock_subscription
        assert result.id == "sub_test123"

    @patch("src.accounting.stripe_service.stripe")
    def test_find_active_subscription_no_subscriptions(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when customer has no active subscriptions."""
        mock_stripe.Subscription.list.return_value.data = []

        result = stripe_service.find_active_subscription("cus_test123")

        # Verify API call
        mock_stripe.Subscription.list.assert_called_once_with(
            customer="cus_test123", status="active", limit=1
        )

        # Should return None when no subscriptions
        assert result is None

    @patch("src.accounting.stripe_service.stripe")
    def test_find_active_subscription_multiple_subscriptions(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when customer has multiple active subscriptions - returns first."""
        mock_subscription1 = MagicMock()
        mock_subscription1.id = "sub_first"
        mock_subscription2 = MagicMock()
        mock_subscription2.id = "sub_second"

        mock_stripe.Subscription.list.return_value.data = [
            mock_subscription1,
            mock_subscription2,
        ]

        result = stripe_service.find_active_subscription("cus_test123")

        assert result is not None

        # Should return first subscription
        assert result == mock_subscription1
        assert result.id == "sub_first"

    @patch("src.accounting.stripe_service.stripe")
    def test_find_active_subscription_stripe_error(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test handling of Stripe API error."""
        mock_stripe.Subscription.list.side_effect = InvalidRequestError(
            "No such customer", param="customer"
        )

        # Should propagate Stripe error
        with pytest.raises(InvalidRequestError, match="No such customer"):
            stripe_service.find_active_subscription("cus_invalid")


class CancelSubscription:
    """Test cases for cancel_subscription method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_subscription_success(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test successful subscription cancellation."""
        # Mock canceled subscription response
        mock_canceled_subscription = MagicMock()
        mock_canceled_subscription.id = "sub_test123"
        mock_canceled_subscription.status = "canceled"
        mock_canceled_subscription.canceled_at = 1640995200

        mock_stripe.Subscription.delete.return_value = mock_canceled_subscription

        # Call the method
        result = stripe_service.cancel_subscription("sub_test123")

        # Verify Stripe API was called correctly
        mock_stripe.Subscription.delete.assert_called_once_with("sub_test123")

        # Verify correct response
        assert result == mock_canceled_subscription
        assert result.id == "sub_test123"
        assert result.status == "canceled"

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_subscription_invalid_subscription(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test cancellation of non-existent subscription."""
        mock_stripe.Subscription.delete.side_effect = InvalidRequestError(
            "No such subscription", param="id"
        )

        # Should propagate Stripe error
        with pytest.raises(InvalidRequestError, match="No such subscription"):
            stripe_service.cancel_subscription("sub_invalid")

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_subscription_already_canceled(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test cancellation of already canceled subscription."""
        mock_stripe.Subscription.delete.side_effect = InvalidRequestError(
            "This subscription has already been canceled", param="id"
        )

        # Should propagate Stripe error for already canceled
        with pytest.raises(InvalidRequestError, match="already been canceled"):
            stripe_service.cancel_subscription("sub_already_canceled")

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_subscription_stripe_api_error(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test handling of general Stripe API error."""
        mock_stripe.Subscription.delete.side_effect = Exception("Network error")

        # Should propagate general error
        with pytest.raises(Exception, match="Network error"):
            stripe_service.cancel_subscription("sub_test123")


class GetPaidInvoicesWithFilters:
    """Test cases for get_paid_invoices_with_filters method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    def _create_mock_invoice(
        self,
        invoice_id: str,
        subscription_id: Optional[str] = None,
        created_timestamp: Optional[int] = None,
    ):
        """Helper to create mock invoice with consistent structure."""
        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id
        mock_invoice.subscription = subscription_id
        mock_invoice.amount_paid = 1000
        mock_invoice.created = created_timestamp or 1640995200
        return mock_invoice

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_with_filters_no_filters(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test basic functionality without filters (equivalent to get_paid_invoices)."""
        mock_invoice1 = self._create_mock_invoice(
            "in_test1", created_timestamp=1640995200
        )
        mock_invoice2 = self._create_mock_invoice(
            "in_test2", created_timestamp=1640995300
        )

        mock_stripe.Invoice.list.return_value.data = [mock_invoice1, mock_invoice2]

        result = stripe_service.get_paid_invoices_with_filters("cus_test123")

        # Verify API call
        mock_stripe.Invoice.list.assert_called_once_with(
            customer="cus_test123", status="paid", limit=100
        )

        # Should return invoices sorted by creation date (newest first)
        assert len(result) == 2
        assert result[0] == mock_invoice2  # Newer invoice first
        assert result[1] == mock_invoice1

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_with_filters_subscription_filter(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test filtering by subscription ID."""
        mock_invoice1 = self._create_mock_invoice("in_test1", "sub_target")
        mock_invoice2 = self._create_mock_invoice("in_test2", "sub_target")

        mock_stripe.Invoice.list.return_value.data = [mock_invoice1, mock_invoice2]

        result = stripe_service.get_paid_invoices_with_filters(
            "cus_test123", subscription_id="sub_target"
        )

        # Verify API call includes subscription filter
        mock_stripe.Invoice.list.assert_called_once_with(
            customer="cus_test123", status="paid", limit=100, subscription="sub_target"
        )

        # Should return filtered invoices (Stripe does the filtering)
        assert len(result) == 2
        assert all(invoice.subscription == "sub_target" for invoice in result)

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_with_filters_date_filter(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test filtering by date (last N days)."""
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)

        # Recent invoice (within 30 days)
        mock_invoice1 = self._create_mock_invoice(
            "in_recent", created_timestamp=int((now - timedelta(days=10)).timestamp())
        )

        mock_stripe.Invoice.list.return_value.data = [mock_invoice1]

        result = stripe_service.get_paid_invoices_with_filters(
            "cus_test123", since_days=30
        )

        # Verify API call includes date filter (approximate timestamp)
        expected_timestamp = int(thirty_days_ago.timestamp())
        call_args = mock_stripe.Invoice.list.call_args
        assert call_args[1]["customer"] == "cus_test123"
        assert call_args[1]["status"] == "paid"
        assert call_args[1]["limit"] == 100
        assert "created" in call_args[1]
        assert "gte" in call_args[1]["created"]
        # Allow some tolerance for timestamp calculation
        assert abs(call_args[1]["created"]["gte"] - expected_timestamp) < 2

        # Should return filtered invoice (Stripe does the filtering)
        assert len(result) == 1
        assert result[0] == mock_invoice1

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_with_filters_combined_filters(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test combining subscription and date filters."""
        now = datetime.now()
        recent_timestamp = int((now - timedelta(days=10)).timestamp())

        mock_invoice1 = self._create_mock_invoice(
            "in_target_recent", "sub_target", recent_timestamp
        )

        mock_stripe.Invoice.list.return_value.data = [mock_invoice1]

        result = stripe_service.get_paid_invoices_with_filters(
            "cus_test123", subscription_id="sub_target", since_days=30
        )

        # Verify API call includes both filters
        call_args = mock_stripe.Invoice.list.call_args
        assert call_args[1]["customer"] == "cus_test123"
        assert call_args[1]["status"] == "paid"
        assert call_args[1]["limit"] == 100
        assert call_args[1]["subscription"] == "sub_target"
        assert "created" in call_args[1]
        assert "gte" in call_args[1]["created"]

        # Should return filtered invoice (Stripe does the filtering)
        assert len(result) == 1
        assert result[0] == mock_invoice1
        assert result[0].subscription == "sub_target"

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_with_filters_no_results(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when filters return no matching invoices."""
        mock_stripe.Invoice.list.return_value.data = []

        result = stripe_service.get_paid_invoices_with_filters(
            "cus_test123", subscription_id="sub_nonexistent"
        )

        assert result == []

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_with_filters_stripe_error(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test handling of Stripe API error."""
        mock_stripe.Invoice.list.side_effect = InvalidRequestError(
            "No such customer", param="customer"
        )

        # Should propagate Stripe error
        with pytest.raises(InvalidRequestError, match="No such customer"):
            stripe_service.get_paid_invoices_with_filters("cus_invalid")


class CancelAndRefundSubscription:
    """Test cases for cancel_and_refund_subscription orchestration method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    def _create_mock_subscription(self, subscription_id: str = "sub_test123"):
        """Helper to create mock subscription."""
        mock_subscription = MagicMock()
        mock_subscription.id = subscription_id
        mock_subscription.status = "active"
        return mock_subscription

    def _create_mock_invoice(self, invoice_id: str, amount_paid: int = 2500):
        """Helper to create mock invoice."""
        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id
        mock_invoice.amount_paid = amount_paid
        mock_invoice.created = 1640995200
        return mock_invoice

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_and_refund_subscription_full_success(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test successful end-to-end cancellation and refund."""
        # Mock subscription
        mock_subscription = self._create_mock_subscription()
        mock_stripe.Subscription.list.return_value.data = [mock_subscription]

        # Mock canceled subscription
        mock_canceled = MagicMock()
        mock_canceled.id = "sub_test123"
        mock_canceled.status = "canceled"
        mock_stripe.Subscription.delete.return_value = mock_canceled

        # Mock most recent invoice
        mock_invoice = self._create_mock_invoice("in_test123")
        # First call for finding subscription, second call for getting recent invoice
        mock_stripe.Invoice.list.side_effect = [
            MagicMock(data=[mock_invoice]),  # Recent invoice call
        ]

        # Mock no existing credit notes (invoice not yet refunded)
        mock_stripe.CreditNote.list.return_value.data = []

        # Mock refund processing
        with patch.object(stripe_service, "process_refunds") as mock_process:
            refund_result = RefundResult(
                invoice_id="in_test123",
                credit_note_id="cn_test123",
                amount_cents=2500,
                status="succeeded",
                success=True,
            )
            mock_process.return_value = [refund_result]

            # Call the method
            result = stripe_service.cancel_and_refund_subscription(
                "cus_test123", refund_last_n_days=30
            )

            # Verify result
            assert isinstance(result, CancellationRefundResult)
            assert result.success is True
            assert result.subscription_cancelled is True
            assert result.subscription_id == "sub_test123"
            assert len(result.refunds_processed) == 1
            assert result.total_refunded_cents == 2500
            assert result.error is None

            # Verify the invoice list call for getting recent invoice
            mock_stripe.Invoice.list.assert_called_with(
                customer="cus_test123",
                subscription="sub_test123",
                status="paid",
                limit=1,
            )

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_and_refund_subscription_no_active_subscription(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when customer has no active subscription."""
        mock_stripe.Subscription.list.return_value.data = []

        result = stripe_service.cancel_and_refund_subscription("cus_test123")

        # Verify error result
        assert isinstance(result, CancellationRefundResult)
        assert result.success is False
        assert result.subscription_cancelled is False
        assert result.subscription_id is None
        assert len(result.refunds_processed) == 0
        assert result.total_refunded_cents == 0
        assert "No active subscription found" in result.error

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_and_refund_subscription_cancel_fails(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when subscription cancellation fails."""
        # Mock active subscription found
        mock_subscription = self._create_mock_subscription()
        mock_stripe.Subscription.list.return_value.data = [mock_subscription]

        # Mock cancellation failure
        mock_stripe.Subscription.delete.side_effect = InvalidRequestError(
            "Cannot cancel subscription", param="id"
        )

        result = stripe_service.cancel_and_refund_subscription("cus_test123")

        # Verify error result
        assert isinstance(result, CancellationRefundResult)
        assert result.success is False
        assert result.subscription_cancelled is False
        assert result.subscription_id == "sub_test123"
        assert len(result.refunds_processed) == 0
        assert result.total_refunded_cents == 0
        assert "Failed to cancel subscription" in result.error

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_and_refund_subscription_no_recent_invoices(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when subscription is canceled but no recent invoices exist."""
        # Mock subscription operations
        mock_subscription = self._create_mock_subscription()
        mock_stripe.Subscription.list.return_value.data = [mock_subscription]

        mock_canceled = MagicMock()
        mock_canceled.id = "sub_test123"
        mock_canceled.status = "canceled"
        mock_stripe.Subscription.delete.return_value = mock_canceled

        # Mock no recent invoices
        mock_stripe.Invoice.list.return_value.data = []

        result = stripe_service.cancel_and_refund_subscription("cus_test123")

        # Verify partial success result
        assert isinstance(result, CancellationRefundResult)
        assert result.success is True  # Cancellation succeeded
        assert result.subscription_cancelled is True
        assert result.subscription_id == "sub_test123"
        assert len(result.refunds_processed) == 0
        assert result.total_refunded_cents == 0
        assert result.error is None

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_and_refund_subscription_invoice_already_refunded(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when the most recent invoice already has credit notes (already refunded)."""
        # Mock subscription operations
        mock_subscription = self._create_mock_subscription()
        mock_stripe.Subscription.list.return_value.data = [mock_subscription]

        mock_canceled = MagicMock()
        mock_canceled.id = "sub_test123"
        mock_canceled.status = "canceled"
        mock_stripe.Subscription.delete.return_value = mock_canceled

        # Mock most recent invoice
        mock_invoice = self._create_mock_invoice("in_test123")
        mock_stripe.Invoice.list.return_value.data = [mock_invoice]

        # Mock existing credit notes (invoice already refunded)
        mock_credit_note = MagicMock()
        mock_credit_note.id = "cn_existing123"
        mock_stripe.CreditNote.list.return_value.data = [mock_credit_note]

        result = stripe_service.cancel_and_refund_subscription("cus_test123")

        # Verify success but no refund processed
        assert isinstance(result, CancellationRefundResult)
        assert result.success is True
        assert result.subscription_cancelled is True
        assert result.subscription_id == "sub_test123"
        assert len(result.refunds_processed) == 0
        assert result.total_refunded_cents == 0
        assert result.error is None

        # Verify credit note check was made
        mock_stripe.CreditNote.list.assert_called_once_with(
            invoice="in_test123", limit=1
        )

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_and_refund_subscription_invoice_retrieval_fails(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when subscription cancels but invoice retrieval fails."""
        # Mock subscription operations
        mock_subscription = self._create_mock_subscription()
        mock_stripe.Subscription.list.return_value.data = [mock_subscription]

        mock_canceled = MagicMock()
        mock_canceled.id = "sub_test123"
        mock_canceled.status = "canceled"
        mock_stripe.Subscription.delete.return_value = mock_canceled

        # Mock invoice retrieval failure in the refund method
        with patch.object(
            stripe_service, "refund_most_recent_subscription_invoice"
        ) as mock_refund:
            mock_refund.side_effect = InvalidRequestError(
                "Unable to retrieve invoices", param="customer"
            )

            result = stripe_service.cancel_and_refund_subscription("cus_test123")

            # Verify partial failure (subscription canceled, refund failed)
            assert isinstance(result, CancellationRefundResult)
            assert result.success is False  # Refund failure causes overall failure
            assert result.subscription_cancelled is True
            assert result.subscription_id == "sub_test123"
            assert len(result.refunds_processed) == 0
            assert result.total_refunded_cents == 0
            assert "Subscription canceled but refund failed" in result.error

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_and_refund_subscription_refund_processing_fails(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when everything works until refund processing fails."""
        # Mock subscription operations
        mock_subscription = self._create_mock_subscription()
        mock_stripe.Subscription.list.return_value.data = [mock_subscription]

        mock_canceled = MagicMock()
        mock_canceled.id = "sub_test123"
        mock_canceled.status = "canceled"
        mock_stripe.Subscription.delete.return_value = mock_canceled

        # Mock most recent invoice
        mock_invoice = self._create_mock_invoice("in_test123")
        mock_stripe.Invoice.list.return_value.data = [mock_invoice]

        # Mock no existing credit notes
        mock_stripe.CreditNote.list.return_value.data = []

        # Mock refund processing failure
        with patch.object(stripe_service, "process_refunds") as mock_process:
            # Refund processing raises error
            mock_process.side_effect = Exception("Refund processing error")

            result = stripe_service.cancel_and_refund_subscription("cus_test123")

            # Verify partial failure (subscription canceled, refund failed)
            assert result.success is False
            assert result.subscription_cancelled is True
            assert result.subscription_id == "sub_test123"
            assert len(result.refunds_processed) == 0
            assert result.total_refunded_cents == 0
            assert "Subscription canceled but refund failed" in result.error

    @patch("src.accounting.stripe_service.stripe")
    def test_cancel_and_refund_subscription_find_subscription_error(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when finding active subscription raises an error."""
        mock_stripe.Subscription.list.side_effect = InvalidRequestError(
            "No such customer", param="customer"
        )

        result = stripe_service.cancel_and_refund_subscription("cus_invalid")

        # Verify error result
        assert isinstance(result, CancellationRefundResult)
        assert result.success is False
        assert result.subscription_cancelled is False
        assert result.subscription_id is None
        assert len(result.refunds_processed) == 0
        assert result.total_refunded_cents == 0
        assert "Unexpected error: No such customer" in result.error


class RefundMostRecentSubscriptionInvoice:
    """Test cases for refund_most_recent_subscription_invoice method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    def _create_mock_invoice(
        self, invoice_id: str = "in_test123", amount_paid: int = 2500
    ):
        """Helper to create mock invoice."""
        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id
        mock_invoice.amount_paid = amount_paid
        mock_invoice.amount_due = amount_paid
        return mock_invoice

    @patch("src.accounting.stripe_service.stripe")
    def test_refund_most_recent_subscription_invoice_success(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test successful refund of most recent invoice."""
        # Mock invoice retrieval
        mock_invoice = self._create_mock_invoice()
        mock_stripe.Invoice.list.return_value.data = [mock_invoice]

        # Mock no existing credit notes (not already refunded)
        mock_stripe.CreditNote.list.return_value.data = []

        # Mock refund processing
        with patch.object(stripe_service, "process_refunds") as mock_process:
            refund_result = RefundResult(
                invoice_id="in_test123",
                credit_note_id="cn_test123",
                amount_cents=2500,
                status="succeeded",
                success=True,
            )
            mock_process.return_value = [refund_result]

            # Call the method
            result = stripe_service.refund_most_recent_subscription_invoice(
                subscription_id="sub_test123", stripe_customer_id="cus_test123"
            )

            # Verify result
            assert len(result) == 1
            assert result[0] == refund_result
            assert result[0].success is True
            assert result[0].amount_cents == 2500

            # Verify API calls
            mock_stripe.Invoice.list.assert_called_once_with(
                customer="cus_test123",
                subscription="sub_test123",
                status="paid",
                limit=1,
            )
            mock_stripe.CreditNote.list.assert_called_once_with(
                invoice="in_test123", limit=1
            )

            # Verify refund breakdown passed to process_refunds
            mock_process.assert_called_once()
            breakdown = mock_process.call_args[0][0]
            assert len(breakdown) == 1
            assert breakdown[0].invoice_id == "in_test123"
            assert breakdown[0].refund_amount_cents == 2500

    @patch("src.accounting.stripe_service.stripe")
    def test_refund_most_recent_subscription_invoice_no_invoices(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when subscription has no paid invoices."""
        # Mock no invoices found
        mock_stripe.Invoice.list.return_value.data = []

        result = stripe_service.refund_most_recent_subscription_invoice(
            subscription_id="sub_test123", stripe_customer_id="cus_test123"
        )

        # Verify empty result
        assert result == []

        # Verify API call was made
        mock_stripe.Invoice.list.assert_called_once_with(
            customer="cus_test123", subscription="sub_test123", status="paid", limit=1
        )

        # Credit note check should not be called
        mock_stripe.CreditNote.list.assert_not_called()

    @patch("src.accounting.stripe_service.stripe")
    def test_refund_most_recent_subscription_invoice_already_refunded(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when invoice already has credit notes (already refunded)."""
        # Mock invoice retrieval
        mock_invoice = self._create_mock_invoice()
        mock_stripe.Invoice.list.return_value.data = [mock_invoice]

        # Mock existing credit note (already refunded)
        mock_credit_note = MagicMock()
        mock_credit_note.id = "cn_existing123"
        mock_stripe.CreditNote.list.return_value.data = [mock_credit_note]

        result = stripe_service.refund_most_recent_subscription_invoice(
            subscription_id="sub_test123", stripe_customer_id="cus_test123"
        )

        # Verify empty result (no new refund)
        assert result == []

        # Verify credit note check was made
        mock_stripe.CreditNote.list.assert_called_once_with(
            invoice="in_test123", limit=1
        )

    @patch("src.accounting.stripe_service.stripe")
    def test_refund_most_recent_subscription_invoice_invoice_retrieval_fails(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when invoice retrieval fails."""
        mock_stripe.Invoice.list.side_effect = InvalidRequestError(
            "No such subscription", param="subscription"
        )

        # Should propagate the error
        with pytest.raises(InvalidRequestError, match="No such subscription"):
            stripe_service.refund_most_recent_subscription_invoice(
                subscription_id="sub_invalid", stripe_customer_id="cus_test123"
            )

    @patch("src.accounting.stripe_service.stripe")
    def test_refund_most_recent_subscription_invoice_refund_processing_fails(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when refund processing fails."""
        # Mock invoice retrieval
        mock_invoice = self._create_mock_invoice()
        mock_stripe.Invoice.list.return_value.data = [mock_invoice]

        # Mock no existing credit notes
        mock_stripe.CreditNote.list.return_value.data = []

        # Mock refund processing failure
        with patch.object(stripe_service, "process_refunds") as mock_process:
            mock_process.side_effect = Exception("Refund processing error")

            # Should propagate the error
            with pytest.raises(Exception, match="Refund processing error"):
                stripe_service.refund_most_recent_subscription_invoice(
                    subscription_id="sub_test123", stripe_customer_id="cus_test123"
                )


class HandleSubscriptionDeletedThroughStripePortal:
    """Test cases for handle_subscription_deleted_through_stripe_portal method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    def _create_mock_event(
        self, subscription_id: str = "sub_test123", customer_id: str = "cus_test123"
    ):
        """Helper to create mock webhook event."""
        return {"data": {"object": {"id": subscription_id, "customer": customer_id}}}

    @patch("src.accounting.stripe_service.stripe")
    def test_handle_subscription_deleted_success(
        self, mock_stripe: Mock, stripe_service: StripeService, session: Session
    ):
        """Test successful subscription deletion handling."""
        from src.models import User

        # Create test user
        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="password",
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        user_account_details = UserAccountDetails(
            user=user, stripe_customer_id="cus_test123"
        )
        session.add(user_account_details)
        session.commit()
        session.refresh(user_account_details)

        # Mock event
        event = self._create_mock_event()

        # Mock Stripe customer retrieval
        mock_customer = MagicMock()
        mock_customer.email = "test@example.com"
        mock_stripe.Customer.retrieve.return_value = mock_customer

        # Mock billing service cancellation
        mock_billing_service = stripe_service.billing_service
        with patch.object(mock_billing_service, "cancel_subscription") as mock_cancel:
            # Mock refund processing
            with patch.object(
                stripe_service, "refund_most_recent_subscription_invoice"
            ) as mock_refund:
                refund_result = RefundResult(
                    invoice_id="in_test123",
                    credit_note_id="cn_test123",
                    amount_cents=2500,
                    status="succeeded",
                    success=True,
                )
                mock_refund.return_value = [refund_result]

                # Call the method
                stripe_service.handle_subscription_deleted_through_stripe_portal(event)

                # Verify Stripe customer retrieval
                mock_stripe.Customer.retrieve.assert_called_once_with("cus_test123")

                # Verify billing service cancellation
                mock_cancel.assert_called_once()
                cancel_args = mock_cancel.call_args
                assert cancel_args[1]["user"] == user
                assert "portal_cancel_sub_test123_" in cancel_args[1]["external_id"]

                # Verify refund processing
                mock_refund.assert_called_once_with(
                    subscription_id="sub_test123", stripe_customer_id="cus_test123"
                )

    @patch("src.accounting.stripe_service.stripe")
    def test_handle_subscription_deleted_no_customer_id(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when subscription event has no customer ID."""
        event = {
            "data": {
                "object": {
                    "id": "sub_test123"
                    # Missing customer field
                }
            }
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="No customer ID found"):
            stripe_service.handle_subscription_deleted_through_stripe_portal(event)

    @patch("src.accounting.stripe_service.stripe")
    def test_handle_subscription_deleted_user_not_found(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when no user found with customer email."""
        event = self._create_mock_event()

        # Mock customer retrieval
        mock_customer = MagicMock()
        mock_customer.email = "nonexistent@example.com"
        mock_stripe.Customer.retrieve.return_value = mock_customer

        # Should return early without error
        stripe_service.handle_subscription_deleted_through_stripe_portal(event)

        # Verify customer was retrieved
        mock_stripe.Customer.retrieve.assert_called_once_with("cus_test123")

    @patch("src.accounting.stripe_service.stripe")
    def test_handle_subscription_deleted_billing_service_fails_but_continues_refund(
        self, mock_stripe: Mock, stripe_service: StripeService, session: Session
    ):
        """Test when billing service cancellation fails but refund continues."""
        from src.models import User

        # Create test user
        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="password",
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        user_account_details = UserAccountDetails(
            user=user, stripe_customer_id="cus_test123"
        )
        session.add(user_account_details)
        session.commit()
        session.refresh(user_account_details)

        event = self._create_mock_event()

        # Mock customer retrieval
        mock_customer = MagicMock()
        mock_customer.email = "test@example.com"
        mock_stripe.Customer.retrieve.return_value = mock_customer

        # Mock billing service failure
        mock_billing_service = stripe_service.billing_service
        with patch.object(mock_billing_service, "cancel_subscription") as mock_cancel:
            mock_cancel.side_effect = Exception("Billing service error")

            # Mock successful refund
            with patch.object(
                stripe_service, "refund_most_recent_subscription_invoice"
            ) as mock_refund:
                mock_refund.return_value = []

                # Should not raise error despite billing failure
                stripe_service.handle_subscription_deleted_through_stripe_portal(event)

                # Verify both were attempted
                mock_cancel.assert_called_once()
                mock_refund.assert_called_once()

    @patch("src.accounting.stripe_service.stripe")
    def test_handle_subscription_deleted_refund_fails_but_does_not_raise(
        self, mock_stripe: Mock, stripe_service: StripeService, session: Session
    ):
        """Test when refund processing fails but webhook succeeds."""
        from src.models import User

        # Create test user
        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="password",
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        event = self._create_mock_event()

        # Mock customer retrieval
        mock_customer = MagicMock()
        mock_customer.email = "test@example.com"
        mock_stripe.Customer.retrieve.return_value = mock_customer

        # Mock billing service success
        mock_cancel = Mock()
        stripe_service.billing_service.cancel_subscription = mock_cancel
        # Mock refund failure
        with patch.object(
            stripe_service, "refund_most_recent_subscription_invoice"
        ) as mock_refund:
            mock_refund.side_effect = Exception("Refund error")

            # Should not raise error despite refund failure
            stripe_service.handle_subscription_deleted_through_stripe_portal(event)

            # Verify both were attempted
            mock_cancel.assert_called_once()
            mock_refund.assert_called_once()

    @patch("src.accounting.stripe_service.stripe")
    def test_handle_subscription_deleted_stripe_error(
        self, mock_stripe: Mock, stripe_service: StripeService
    ):
        """Test when Stripe customer retrieval fails."""
        event = self._create_mock_event()

        # Mock Stripe error
        mock_stripe.Customer.retrieve.side_effect = InvalidRequestError(
            "No such customer", param="id"
        )

        # Should propagate Stripe error
        with pytest.raises(InvalidRequestError, match="No such customer"):
            stripe_service.handle_subscription_deleted_through_stripe_portal(event)
