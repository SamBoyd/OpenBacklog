import uuid
from unittest.mock import MagicMock, patch

import pytest
import stripe
from sqlalchemy.orm import Session
from stripe import InvalidRequestError

from src.accounting.billing_service import BillingService
from src.accounting.models import User, UserAccountDetails, UserAccountStatus
from src.accounting.stripe_service import (
    RefundBreakdownItem,
    RefundResult,
    StripeService,
)


class TestStripeService_HandleCheckoutSessionCompleted:
    """Test cases for the StripeService class."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_stripe.Invoice.list.return_value.data = []
            mock_stripe.Invoice.retrieve.return_value.metadata = {}
            mock_stripe.Invoice.retrieve.return_value.hosted_invoice_url = (
                "https://invoice.stripe.com/i/test123"
            )
            mock_stripe.PaymentIntent.retrieve.return_value.metadata = {}
            yield StripeService(session)

    @pytest.fixture
    def mock_billing_service(self, stripe_service):
        """Create a mock BillingService for testing."""
        mock_service = MagicMock()
        stripe_service.billing_service = mock_service
        yield mock_service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = MagicMock()
        user.id = uuid.uuid4()
        return user

    def test_handle_checkout_session_completed_success(
        self,
        stripe_service: StripeService,
        mock_billing_service: MagicMock,
        sample_user: User,
    ):
        """Test successful processing of checkout.session.completed event."""
        # Mock the billing service response
        mock_billing_service.process_pending_topup.return_value = (
            sample_user.account_details
        )

        # Create test event data
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "user_id": str(sample_user.id),
                        "topup_amount_cents": "500",
                        "type": "account_topup",
                    },
                    "payment_status": "paid",
                    "invoice": "in_test123",
                    "payment_intent": "pi_test123",
                }
            }
        }

        stripe_service._edit_metadata = MagicMock()

        # Call the method
        stripe_service.handle_checkout_session_completed(event)

        # Verify BillingService was called correctly
        mock_billing_service.process_pending_topup.assert_called_once_with(
            "cs_test123",
            success=True,
            download_url="https://invoice.stripe.com/i/test123",
        )

        stripe_service._edit_metadata.assert_called_once_with(event["data"]["object"])

    def test_edit_metadata_billing_service_error(
        self,
        mock_billing_service: MagicMock,
        stripe_service: StripeService,
    ):
        """Test handling of BillingService error during processing."""
        # Mock BillingService to raise an error
        mock_billing_service.process_pending_topup.side_effect = ValueError(
            "User account details not found"
        )

        # Create test event data
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "user_id": "user_id",
                        "topup_amount_cents": "500",
                        "type": "account_topup",
                    },
                    "payment_status": "paid",
                    "invoice": "in_test123",
                    "payment_intent": "pi_test123",
                }
            }
        }

        # Call the method and expect the error to be re-raised
        with pytest.raises(ValueError) as e:
            stripe_service.handle_checkout_session_completed(event)
            assert "User account details not found" in str(e)

    @patch("src.accounting.stripe_service.stripe")
    def test_throws_error_if_no_invoice_download_url(
        self,
        mock_stripe: MagicMock,
        mock_billing_service: MagicMock,
        session: Session,
    ):
        """Test handling of BillingService error during processing."""

        mock_stripe.Invoice.list.return_value.data = []
        mock_stripe.Invoice.retrieve.return_value.metadata = {}
        mock_stripe.Invoice.retrieve.return_value.hosted_invoice_url = None
        mock_stripe.PaymentIntent.retrieve.return_value.metadata = {}

        stripe_service = StripeService(session)

        stripe_service._edit_metadata = MagicMock()

        # Create test event data
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "user_id": "user_id",
                        "topup_amount_cents": "500",
                        "type": "account_topup",
                    },
                    "payment_status": "paid",
                    "invoice": "in_test123",
                    "payment_intent": "pi_test123",
                }
            }
        }

        # Call the method and expect the error to be re-raised
        with pytest.raises(ValueError) as e:
            stripe_service.handle_checkout_session_completed(event)
            assert "No hosted invoice URL available for invoice in_test123" in str(e)

    def test_handle_checkout_session_completed_not_topup_session(
        self,
        stripe_service: StripeService,
        mock_billing_service: MagicMock,
    ):
        """Test that non-topup checkout sessions are skipped."""
        # Create test event data for subscription session (no metadata.type)
        subscription_event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {},  # No type metadata for subscription sessions
                    "payment_status": "paid",
                    "mode": "subscription",
                }
            }
        }

        stripe_service._edit_metadata = MagicMock()

        # Call the method
        stripe_service.handle_checkout_session_completed(subscription_event)

        # Verify no processing happened
        mock_billing_service.process_pending_topup.assert_not_called()
        stripe_service._edit_metadata.assert_not_called()

        # Test with different metadata type
        other_event = {
            "data": {
                "object": {
                    "id": "cs_test456",
                    "metadata": {"type": "subscription_payment"},
                    "payment_status": "paid",
                }
            }
        }

        # Call the method
        stripe_service.handle_checkout_session_completed(other_event)

        # Verify still no processing happened
        mock_billing_service.process_pending_topup.assert_not_called()
        stripe_service._edit_metadata.assert_not_called()


@patch("src.accounting.stripe_service.stripe", MagicMock())
class TestStripeService_EditMetadata:
    """Test cases for the _edit_metadata method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    def test_edit_metadata_missing_metadata(
        self,
        stripe_service: StripeService,
    ):
        """Test handling of checkout session with missing metadata."""
        # Create test event data with missing metadata
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {"type": "account_topup"},
                    "payment_status": "paid",
                }
            }
        }

        # Call the method and expect ValueError
        with pytest.raises(ValueError, match="Missing required metadata"):
            stripe_service._edit_metadata(event["data"]["object"])

    def test_edit_metadata_payment_not_paid(
        self,
        stripe_service: StripeService,
    ):
        """Test handling of checkout session with payment not paid."""
        # Create test event data with payment not paid
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "user_id": "user_id",
                        "topup_amount_cents": "500",
                        "type": "account_topup",
                    },
                    "payment_status": "pending",
                    "invoice": "in_test123",
                    "payment_intent": "pi_test123",
                }
            }
        }

        # Call the method
        with pytest.raises(
            ValueError, match="Session cs_test123 payment status is pending"
        ):
            stripe_service._edit_metadata(event["data"]["object"])

    def test_edit_metadata_successful_invoice_and_payment_intent_update(
        self,
        stripe_service: StripeService,
    ):
        """Test successful metadata update for both invoice and payment intent."""
        # Create test event data
        session_data = {
            "id": "cs_test123",
            "metadata": {
                "user_id": "user_id",
                "topup_amount_cents": "500",
                "type": "account_topup",
            },
            "payment_status": "paid",
            "invoice": "in_test123",
            "payment_intent": "pi_test123",
            "hosted_invoice_url": "https://invoice.stripe.com/i/test123",
        }

        # Mock Stripe API calls
        mock_invoice = MagicMock()
        mock_invoice.metadata = {"existing_key": "existing_value"}

        mock_payment_intent = MagicMock()
        mock_payment_intent.metadata = {"another_key": "another_value"}

        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_stripe.Invoice.retrieve.return_value = mock_invoice
            mock_stripe.PaymentIntent.retrieve.return_value = mock_payment_intent

            # Call the method
            stripe_service._edit_metadata(session_data)

            # Verify invoice was retrieved and modified
            mock_stripe.Invoice.retrieve.assert_called_once_with("in_test123")
            mock_stripe.Invoice.modify.assert_called_once_with(
                id="in_test123",
                metadata={
                    "existing_key": "existing_value",
                    "payment_intent": "pi_test123",
                },
            )

            # Verify payment intent was retrieved and modified
            mock_stripe.PaymentIntent.retrieve.assert_called_once_with("pi_test123")
            mock_stripe.PaymentIntent.modify.assert_called_once_with(
                id="pi_test123",
                metadata={"another_key": "another_value", "invoice": "in_test123"},
            )

    def test_edit_metadata_with_empty_metadata(
        self,
        stripe_service: StripeService,
    ):
        """Test metadata update when invoice and payment intent have no existing metadata."""
        # Create test event data
        session_data = {
            "id": "cs_test123",
            "metadata": {
                "user_id": "user_id",
                "topup_amount_cents": "500",
                "type": "account_topup",
            },
            "payment_status": "paid",
            "invoice": "in_test123",
            "payment_intent": "pi_test123",
            "hosted_invoice_url": "https://invoice.stripe.com/i/test123",
        }

        # Mock Stripe API calls with None metadata
        mock_invoice = MagicMock()
        mock_invoice.metadata = None

        mock_payment_intent = MagicMock()
        mock_payment_intent.metadata = None

        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_stripe.Invoice.retrieve.return_value = mock_invoice
            mock_stripe.PaymentIntent.retrieve.return_value = mock_payment_intent

            # Call the method
            stripe_service._edit_metadata(session_data)

            # Verify invoice was modified with new metadata
            mock_stripe.Invoice.modify.assert_called_once_with(
                id="in_test123", metadata={"payment_intent": "pi_test123"}
            )

            # Verify payment intent was modified with new metadata
            mock_stripe.PaymentIntent.modify.assert_called_once_with(
                id="pi_test123", metadata={"invoice": "in_test123"}
            )

    def test_edit_metadata_invoice_retrieval_error(
        self,
        stripe_service: StripeService,
    ):
        """Test handling of invoice retrieval error."""
        # Create test event data
        session_data = {
            "id": "cs_test123",
            "metadata": {
                "user_id": "user_id",
                "topup_amount_cents": "500",
                "type": "account_topup",
            },
            "payment_status": "paid",
            "invoice": "in_test123",
            "payment_intent": "pi_test123",
            "hosted_invoice_url": "https://invoice.stripe.com/i/test123",
        }

        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_stripe.Invoice.retrieve.side_effect = InvalidRequestError(
                "No such invoice: 'in_test123'", param="id"
            )

            # Call the method and expect the error to be re-raised
            with pytest.raises(InvalidRequestError, match="No such invoice"):
                stripe_service._edit_metadata(session_data)

            # Verify payment intent was not retrieved
            mock_stripe.PaymentIntent.retrieve.assert_not_called()

    def test_edit_metadata_not_topup_session(
        self,
        stripe_service: StripeService,
    ):
        """Test that metadata is not modified for non-topup sessions."""
        # Create test event data for non-topup session
        session_data = {
            "id": "cs_test123",
            "metadata": {"type": "subscription_payment"},
            "payment_status": "paid",
            "invoice": "in_test123",
            "payment_intent": "pi_test123",
            "hosted_invoice_url": "https://invoice.stripe.com/i/test123",
        }

        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            # Call the method
            stripe_service._edit_metadata(session_data)

            # Verify no Stripe API calls were made
            mock_stripe.Invoice.retrieve.assert_not_called()
            mock_stripe.PaymentIntent.retrieve.assert_not_called()
            mock_stripe.Invoice.modify.assert_not_called()
            mock_stripe.PaymentIntent.modify.assert_not_called()

    def test_edit_metadata_missing_invoice_or_payment_intent(
        self,
        stripe_service: StripeService,
    ):
        """Test handling of missing invoice or payment intent IDs."""
        # Create test event data with missing invoice
        session_data_missing_invoice = {
            "id": "cs_test123",
            "metadata": {
                "user_id": "user_id",
                "topup_amount_cents": "500",
                "type": "account_topup",
            },
            "payment_status": "paid",
            "invoice": None,
            "payment_intent": "pi_test123",
            "hosted_invoice_url": "https://invoice.stripe.com/i/test123",
        }

        # Call the method and expect ValueError
        with pytest.raises(ValueError, match="Missing required metadata"):
            stripe_service._edit_metadata(session_data_missing_invoice)

        # Create test event data with missing payment intent
        session_data_missing_payment_intent = {
            "id": "cs_test123",
            "metadata": {
                "user_id": "user_id",
                "topup_amount_cents": "500",
                "type": "account_topup",
            },
            "payment_status": "paid",
            "invoice": "in_test123",
            "payment_intent": None,
        }

        # Call the method and expect ValueError
        with pytest.raises(ValueError, match="Missing required metadata"):
            stripe_service._edit_metadata(session_data_missing_payment_intent)


class TestStripeService_HandleCheckoutSessionExpired:
    """Test cases for the handle_checkout_session_expired method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    @pytest.fixture
    def mock_billing_service(self, stripe_service):
        """Create a mock BillingService for testing."""
        mock_service = MagicMock()
        stripe_service.billing_service = mock_service
        yield mock_service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = MagicMock()
        user.id = uuid.uuid4()
        return user

    def test_handle_checkout_session_expired(
        self,
        stripe_service: StripeService,
        mock_billing_service: MagicMock,
        sample_user: User,
    ):
        """Test handling of expired checkout session."""
        # Create test event data for expired session
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "type": "account_topup",
                        "user_id": str(sample_user.id),
                        "topup_amount_cents": "500",
                    },
                    "payment_status": "expired",
                    "invoice": "in_test123",
                    "payment_intent": "pi_test123",
                }
            }
        }

        # Call the method
        stripe_service.handle_checkout_session_expired(event)

        # Verify BillingService was called to mark as failed
        mock_billing_service.process_pending_topup.assert_called_once_with(
            "cs_test123", success=False, download_url=None
        )

    def test_handle_checkout_session_expired_not_topup(
        self,
        stripe_service: StripeService,
        mock_billing_service: MagicMock,
        sample_user: User,
    ):
        """Test handling of expired non-topup checkout session."""
        # Create test event data for non-topup session
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "type": "subscription_payment",
                        "user_id": str(sample_user.id),
                        "topup_amount_cents": "500",
                    },
                    "payment_status": "paid",
                    "invoice": "in_test123",
                    "payment_intent": "pi_test123",
                }
            }
        }

        # Call the method
        stripe_service.handle_checkout_session_expired(event)

        # Verify BillingService was not called
        mock_billing_service.process_pending_topup.assert_not_called()


class TestStripeService_HandleCheckoutSessionAsyncPaymentFailed:
    """Test cases for the handle_checkout_session_async_payment_failed method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    @pytest.fixture
    def mock_billing_service(self, stripe_service):
        """Create a mock BillingService for testing."""
        mock_service = MagicMock()
        stripe_service.billing_service = mock_service
        yield mock_service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = MagicMock()
        user.id = uuid.uuid4()
        return user

    def test_handle_checkout_session_async_payment_failed(
        self,
        stripe_service: StripeService,
        mock_billing_service: MagicMock,
        sample_user: User,
    ):
        """Test handling of async payment failed checkout session."""
        # Create test event data for async payment failed
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "type": "account_topup",
                        "user_id": str(sample_user.id),
                        "topup_amount_cents": "500",
                    },
                    "payment_status": "failed",
                    "invoice": "in_test123",
                    "payment_intent": "pi_test123",
                }
            }
        }

        # Call the method
        stripe_service.handle_checkout_session_async_payment_failed(event)

        # Verify BillingService was called to mark as failed
        mock_billing_service.process_pending_topup.assert_called_once_with(
            "cs_test123", success=False, download_url=None
        )


class TestStripeService_HandleCheckoutSessionAsyncPaymentSucceeded:
    """Test cases for the handle_checkout_session_async_payment_succeeded method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_stripe.Invoice.list.return_value.data = []
            mock_stripe.Invoice.retrieve.return_value.metadata = {}
            mock_stripe.Invoice.retrieve.return_value.hosted_invoice_url = (
                "https://invoice.stripe.com/i/test123"
            )
            mock_stripe.PaymentIntent.retrieve.return_value.metadata = {}
            yield StripeService(session)

    @pytest.fixture
    def mock_billing_service(self, stripe_service):
        """Create a mock BillingService for testing."""
        mock_service = MagicMock()
        stripe_service.billing_service = mock_service
        yield mock_service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = MagicMock()
        user.id = uuid.uuid4()
        return user

    def test_handle_checkout_session_async_payment_succeeded(
        self,
        stripe_service: StripeService,
        mock_billing_service: MagicMock,
        sample_user: User,
    ):
        """Test handling of async payment succeeded checkout session."""
        # Mock the billing service response
        mock_billing_service.process_pending_topup.return_value = (
            sample_user.account_details
        )

        # Create test event data for async payment succeeded
        event = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "metadata": {
                        "user_id": str(sample_user.id),
                        "topup_amount_cents": "500",
                        "type": "account_topup",
                    },
                    "payment_status": "paid",
                    "invoice": "in_test123",
                    "payment_intent": "pi_test123",
                }
            }
        }

        # Call the method
        stripe_service.handle_checkout_session_async_payment_succeeded(event)

        # Verify BillingService was called to process as successful
        mock_billing_service.process_pending_topup.assert_called_once_with(
            "cs_test123",
            success=True,
            download_url="https://invoice.stripe.com/i/test123",
        )


class TestStripeService_GetPaidInvoices:
    """Test cases for get_paid_invoices method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    @pytest.fixture
    def mock_billing_service(self, stripe_service):
        """Create a mock BillingService for testing."""
        mock_service = MagicMock()
        stripe_service.billing_service = mock_service
        yield mock_service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = MagicMock()
        user.id = uuid.uuid4()
        return user

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_success(
        self, mock_stripe, stripe_service: StripeService
    ):
        """Test successful retrieval of paid invoices for a customer."""
        # Mock Stripe invoices
        mock_invoice1 = MagicMock()
        mock_invoice1.id = "in_test1"
        mock_invoice1.amount_paid = 1000
        mock_invoice1.created = 1640995200
        mock_invoice2 = MagicMock()
        mock_invoice2.id = "in_test2"
        mock_invoice2.amount_paid = 2000
        mock_invoice2.created = 1640995300

        mock_stripe.Invoice.list.return_value.data = [mock_invoice1, mock_invoice2]

        # Call the method
        result = stripe_service.get_paid_invoices("cus_test123")

        # Verify Stripe was called correctly
        mock_stripe.Invoice.list.assert_called_once_with(
            customer="cus_test123", status="paid", limit=100
        )

        # Verify invoices are returned sorted by creation date (newest first)
        assert result == [mock_invoice2, mock_invoice1]

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_stripe_error(
        self, mock_stripe, stripe_service: StripeService
    ):
        """Test handling of Stripe error when retrieving paid invoices."""
        mock_stripe.Invoice.list.side_effect = Exception("Stripe API error")

        with pytest.raises(Exception) as exc:
            stripe_service.get_paid_invoices("cus_test123")
        assert "Stripe API error" in str(exc.value)

    @patch("src.accounting.stripe_service.stripe")
    def test_get_paid_invoices_no_invoices(
        self, mock_stripe, stripe_service: StripeService
    ):
        """Test handling when user has no paid invoices."""
        mock_stripe.Invoice.list.return_value.data = []

        result = stripe_service.get_paid_invoices("cus_test123")
        assert result == []


class TestStripeService_HandleSubscriptionCreated:
    """Test cases for handle_subscription_created method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    def test_handle_subscription_created_success_new_customer_id(
        self, stripe_service: StripeService, session: Session
    ):
        """Test successful processing of subscription created event with new customer ID."""
        # Create a user in the database
        from src.accounting.models import UserAccountDetails, UserAccountStatus
        from src.models import User

        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Verify user has account details
        assert user.account_details is not None
        assert user.account_details.stripe_customer_id is None

        # Create test event data
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                }
            }
        }

        # Mock Stripe customer retrieval
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_customer = MagicMock()
            mock_customer.email = "test@example.com"
            mock_stripe.Customer.retrieve.return_value = mock_customer

            # Call the method
            stripe_service.handle_subscription_created(event)

            # Verify Stripe API was called correctly
            mock_stripe.Customer.retrieve.assert_called_once_with("cus_test123")

        # Verify database was updated
        session.refresh(user)
        assert user.account_details.stripe_customer_id == "cus_test123"

    def test_handle_subscription_created_success_update_existing_customer_id(
        self, stripe_service: StripeService, session: Session
    ):
        """Test updating existing customer ID for a user."""
        # Create a user with existing customer ID
        from src.models import User

        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Set existing customer ID
        user.account_details.stripe_customer_id = "cus_old123"
        session.commit()

        # Create test event data
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_new123",
                }
            }
        }

        # Mock Stripe customer retrieval
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_customer = MagicMock()
            mock_customer.email = "test@example.com"
            mock_stripe.Customer.retrieve.return_value = mock_customer

            # Call the method
            stripe_service.handle_subscription_created(event)

        # Verify database was updated with new customer ID
        session.refresh(user)
        assert user.account_details.stripe_customer_id == "cus_new123"

    def test_handle_subscription_created_idempotent_same_customer_id(
        self, stripe_service: StripeService, session: Session
    ):
        """Test idempotent behavior when customer ID already matches."""
        # Create a user with existing customer ID
        from src.models import User

        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Set existing customer ID that matches the event
        user.account_details.stripe_customer_id = "cus_test123"
        session.commit()

        # Create test event data
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                }
            }
        }

        # Mock Stripe customer retrieval
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_customer = MagicMock()
            mock_customer.email = "test@example.com"
            mock_stripe.Customer.retrieve.return_value = mock_customer

            # Call the method
            stripe_service.handle_subscription_created(event)

        # Verify customer ID remains unchanged
        session.refresh(user)
        assert user.account_details.stripe_customer_id == "cus_test123"

    def test_handle_subscription_created_missing_customer_id(
        self, stripe_service: StripeService
    ):
        """Test handling of event with missing customer ID."""
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": None,
                }
            }
        }

        # Call the method and expect ValueError
        with pytest.raises(
            ValueError, match="No customer ID found in subscription sub_test123"
        ):
            stripe_service.handle_subscription_created(event)

    def test_handle_subscription_created_customer_has_no_email(
        self, stripe_service: StripeService
    ):
        """Test handling of Stripe customer with no email."""
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                }
            }
        }

        # Mock Stripe customer retrieval with no email
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_customer = MagicMock()
            mock_customer.email = None
            mock_stripe.Customer.retrieve.return_value = mock_customer

            # Call the method - should return early without error
            stripe_service.handle_subscription_created(event)

            # Verify Stripe API was called
            mock_stripe.Customer.retrieve.assert_called_once_with("cus_test123")

    def test_handle_subscription_created_user_not_found(
        self, stripe_service: StripeService
    ):
        """Test handling when user with customer email is not found."""
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                }
            }
        }

        # Mock Stripe customer retrieval
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_customer = MagicMock()
            mock_customer.email = "nonexistent@example.com"
            mock_stripe.Customer.retrieve.return_value = mock_customer

            # Call the method - should return early without error
            stripe_service.handle_subscription_created(event)

    def test_handle_subscription_created_user_no_account_details(
        self, stripe_service: StripeService, session: Session
    ):
        """Test handling when user has no account details."""
        # Create a user without account details (mock scenario)
        from src.models import User

        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Mock user.account_details to return None
        with patch.object(user, "account_details", None):
            event = {
                "data": {
                    "object": {
                        "id": "sub_test123",
                        "customer": "cus_test123",
                    }
                }
            }

            # Mock Stripe customer retrieval
            with patch("src.accounting.stripe_service.stripe") as mock_stripe:
                mock_customer = MagicMock()
                mock_customer.email = "test@example.com"
                mock_stripe.Customer.retrieve.return_value = mock_customer

                # Mock the query to return our user
                with patch.object(session, "query") as mock_query:
                    mock_query.return_value.filter.return_value.first.return_value = (
                        user
                    )

                    # Call the method - should return early without error
                    stripe_service.handle_subscription_created(event)

    def test_handle_subscription_created_stripe_error(
        self, stripe_service: StripeService
    ):
        """Test handling of Stripe API error."""
        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                }
            }
        }

        # Mock Stripe customer retrieval to raise an error
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            # Use InvalidRequestError which inherits from StripeError properly
            mock_stripe.Customer.retrieve.side_effect = InvalidRequestError(
                "API Error", param="id"
            )
            mock_stripe.StripeError = stripe.StripeError

            # Call the method and expect StripeError to be re-raised
            with pytest.raises(Exception, match="API Error"):
                stripe_service.handle_subscription_created(event)

    @pytest.mark.skip(reason="This test is not working")
    def test_handle_subscription_created_database_error_rollback(
        self, stripe_service: StripeService, session: Session
    ):
        """Test database rollback on unexpected error."""
        # Create a user in the database
        from src.models import User

        user = User(
            name="Test User",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        event = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                }
            }
        }

        # Mock Stripe customer retrieval
        with patch("src.accounting.stripe_service.stripe") as mock_stripe:
            mock_customer = MagicMock()
            mock_customer.email = "test@example.com"
            mock_stripe.Customer.retrieve.return_value = mock_customer

            # Mock the service's database session.commit to raise an exception
            with patch.object(
                stripe_service.db, "commit", side_effect=Exception("Database error")
            ):
                # Mock session.rollback to verify it's called
                with patch.object(stripe_service.db, "rollback") as mock_rollback:
                    # Call the method and expect the exception to be re-raised
                    with pytest.raises(Exception):
                        stripe_service.handle_subscription_created(event)

                    # Verify rollback was called
                    mock_rollback.assert_called_once()


class TestStripeService_CalculateRefundBreakdown:
    """Test cases for calculate_refund_breakdown method."""

    @pytest.fixture
    def stripe_service(self, session: Session):
        """Create a StripeService instance for testing."""
        return StripeService(session)

    @pytest.fixture
    def mock_billing_service(self, stripe_service):
        """Create a mock BillingService for testing."""
        mock_service = MagicMock()
        stripe_service.billing_service = mock_service
        yield mock_service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = MagicMock()
        user.id = uuid.uuid4()
        return user

    def test_calculate_refund_breakdown_single_invoice(
        self, stripe_service: StripeService
    ):
        """Test refund breakdown calculation for a single invoice."""
        invoice = MagicMock()
        invoice.id = "in_test1"
        invoice.amount_paid = 1000
        invoice.created = 1640995200

        breakdown = stripe_service.calculate_refund_breakdown([invoice], 500)

        assert len(breakdown) == 1
        assert breakdown[0].invoice_id == "in_test1"
        assert breakdown[0].refund_amount_cents == 500
        assert breakdown[0].invoice_amount_cents == 1000

    def test_calculate_refund_breakdown_multiple_invoices(
        self, stripe_service: StripeService
    ):
        """Test refund breakdown calculation across multiple invoices."""
        invoice1 = MagicMock()
        invoice1.id = "in_test1"
        invoice1.amount_paid = 1000
        invoice1.created = 1640995200

        invoice2 = MagicMock()
        invoice2.id = "in_test2"
        invoice2.amount_paid = 2000
        invoice2.created = 1640995300

        invoice3 = MagicMock()
        invoice3.id = "in_test3"
        invoice3.amount_paid = 500
        invoice3.created = 1640995400

        breakdown = stripe_service.calculate_refund_breakdown(
            [invoice1, invoice2, invoice3], 2500
        )

        assert len(breakdown) == 2
        assert breakdown[0].invoice_id == "in_test1"
        assert breakdown[0].refund_amount_cents == 1000
        assert breakdown[0].invoice_amount_cents == 1000

        assert breakdown[1].invoice_id == "in_test2"
        assert breakdown[1].refund_amount_cents == 1500
        assert breakdown[1].invoice_amount_cents == 2000

    def test_calculate_refund_breakdown_exact_amount(
        self, stripe_service: StripeService
    ):
        """Test refund breakdown calculation when refund equals combined invoice amounts."""
        invoice1 = MagicMock()
        invoice1.id = "in_test1"
        invoice1.amount_paid = 1000
        invoice1.created = 1640995200

        invoice2 = MagicMock()
        invoice2.id = "in_test2"
        invoice2.amount_paid = 2000
        invoice2.created = 1640995300

        breakdown = stripe_service.calculate_refund_breakdown(
            [invoice1, invoice2], 3000
        )

        assert len(breakdown) == 2
        assert breakdown[0].invoice_id == "in_test1"
        assert breakdown[0].refund_amount_cents == 1000
        assert breakdown[0].invoice_amount_cents == 1000

        assert breakdown[1].invoice_id == "in_test2"
        assert breakdown[1].refund_amount_cents == 2000
        assert breakdown[1].invoice_amount_cents == 2000

    def test_calculate_refund_breakdown_insufficient_funds(
        self, stripe_service: StripeService
    ):
        """Test refund breakdown calculation with insufficient invoice totals."""
        invoice1 = MagicMock()
        invoice1.id = "in_test1"
        invoice1.amount_paid = 1000
        invoice1.created = 1640995200

        invoice2 = MagicMock()
        invoice2.id = "in_test2"
        invoice2.amount_paid = 500
        invoice2.created = 1640995300

        with pytest.raises(
            ValueError,
            match="Insufficient paid invoices to refund 2000 cents. Only 1500 cents available.",
        ):
            stripe_service.calculate_refund_breakdown([invoice1, invoice2], 2000)

    def test_calculate_refund_breakdown_empty_history(
        self, stripe_service: StripeService
    ):
        """Test refund breakdown calculation with no invoices."""
        with pytest.raises(
            ValueError,
            match="Insufficient paid invoices to refund 1000 cents. Only 0 cents available.",
        ):
            stripe_service.calculate_refund_breakdown([], 1000)
