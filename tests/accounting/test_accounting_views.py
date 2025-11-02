"""
Tests for accounting views.

This module tests the billing onboarding functionality including the
OpenMeter service integration and API endpoints.
"""

import uuid
from datetime import datetime
from unittest.mock import ANY, Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.accounting.accounting_controller import SubscriptionCancellationResult
from src.accounting.accounting_views import RefundResult
from src.accounting.models import (
    PendingTopup,
    PendingTopupStatus,
    UserAccountDetails,
    UserAccountStatus,
)
from src.main import app
from src.models import User
from src.views import dependency_to_override


class TestGetUserAccountDetails:
    """Test cases for get user account details endpoint."""

    def test_get_user_account_details_success(
        self, test_client: TestClient, user: User, session: Session
    ):
        """Test successful retrieval of user account details."""
        # Make the request
        response = test_client.get("/api/accounting/user-account-details")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["balanceCents"] == 0
        assert data["status"] == "ACTIVE_SUBSCRIPTION"
        assert data["onboardingCompleted"] == True
        assert data["monthlyCreditsTotal"] == 0
        assert data["monthlyCreditsUsed"] == 0
        assert data["subscriptionCancelAt"] is None
        assert data["subscriptionCanceledAt"] is None
        assert data["subscriptionCancelAtPeriodEnd"] is None

    def test_get_user_account_details_new_user(self, session: Session):
        user = User(
            id=uuid.uuid4(),  # Explicitly set UUID if needed, or let DB handle it
            name="Rachel Stevenson",
            email="rachel@gmail.com",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
            is_verified=True,
            last_logged_in=datetime.now(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        app.dependency_overrides[dependency_to_override] = lambda: user
        test_client = TestClient(app)

        # Make the request
        response = test_client.get("/api/accounting/user-account-details")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["balanceCents"] == 0
        assert data["status"] == "NEW"
        assert data["monthlyCreditsTotal"] == 0
        assert data["monthlyCreditsUsed"] == 0
        assert data["subscriptionCancelAt"] is None
        assert data["subscriptionCanceledAt"] is None
        assert data["subscriptionCancelAtPeriodEnd"] is None

        # Verify user account details were created
        account_details: UserAccountDetails = (
            session.query(UserAccountDetails)
            .filter(UserAccountDetails.user_id == user.id)
            .first()
        )
        assert account_details is not None
        assert account_details.balance_cents == 0.0
        assert account_details.status == UserAccountStatus.NEW
        assert account_details.stripe_customer_id is None
        assert account_details.onboarding_completed is False
        assert account_details.subscription_cancel_at is None
        assert account_details.subscription_canceled_at is None
        assert account_details.subscription_cancel_at_period_end is None
        assert account_details.monthly_credits_total == 0
        assert account_details.monthly_credits_used == 0
        assert account_details.next_billing_cycle_starts is None

        app.dependency_overrides.pop(dependency_to_override, None)


class TestCompleteOnboarding:
    """Test cases for complete onboarding endpoint."""

    def test_complete_onboarding_success(
        self, test_client: TestClient, user: User, session: Session
    ):
        """Test successful onboarding completion transitions NEW to NO_SUBSCRIPTION."""
        # Setup: User starts in NEW state with onboarding not completed
        user.account_details.status = UserAccountStatus.NEW
        user.account_details.onboarding_completed = False
        session.add(user.account_details)
        session.commit()

        # Make the request
        response = test_client.post("/api/accounting/complete-onboarding")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["onboardingCompleted"] == True

        # Verify database was updated
        session.refresh(user.account_details)
        assert user.account_details.onboarding_completed == True
        # Verify state transitioned from NEW to NO_SUBSCRIPTION
        assert user.account_details.status == UserAccountStatus.NO_SUBSCRIPTION

    def test_complete_onboarding_already_completed(
        self, test_client: TestClient, user: User, session: Session
    ):
        """Test onboarding completion when already completed (idempotent)."""
        # User already has onboarding completed from fixture
        assert user.account_details.onboarding_completed == True

        # Make the request
        response = test_client.post("/api/accounting/complete-onboarding")

        # Should still succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["onboardingCompleted"] == True

        # Verify database state is still correct
        session.refresh(user.account_details)
        assert user.account_details.onboarding_completed == True


class TestProcessRefund:
    """Test cases for process refund endpoint."""

    @patch("src.accounting.accounting_views.accounting_controller.process_refund")
    def test_process_refund_success(
        self, mock_process_refund: Mock, test_client: TestClient
    ):
        """Test successful refund processing."""

        mock_process_refund.return_value = RefundResult(
            success=True,
            details="Refund processed successfully",
        )

        response = test_client.post(
            "/api/accounting/refund", json={"amount_cents": 1000}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["details"] == "Refund processed successfully"

    @patch("src.accounting.accounting_views.accounting_controller.process_refund")
    def test_process_refund_failure(
        self, mock_process_refund: Mock, test_client: TestClient
    ):
        """Test refund processing failure."""
        mock_process_refund.return_value = RefundResult(
            success=False, details="User account not found"
        )

        response = test_client.post(
            "/api/accounting/refund", json={"amount_cents": 1000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["details"] == "User account not found"


class TestGetPendingTopup:
    """Test cases for get pending topup endpoint."""

    def test_get_pending_topup_success(
        self, test_client: TestClient, user: User, session: Session
    ):
        # Add a pending topup for the user
        pending_topup = PendingTopup()
        pending_topup.user_id = user.id
        pending_topup.session_id = "sess_123"
        pending_topup.amount_cents = 1500
        pending_topup.status = PendingTopupStatus.PENDING
        session.add(pending_topup)
        session.commit()

        response = test_client.get("/api/accounting/pending-topup")
        assert response.status_code == 200
        data = response.json()
        assert data["userId"] == str(user.id)
        assert data["sessionId"] == "sess_123"
        assert data["amountCents"] == 1500
        assert data["status"] == "PENDING"
        assert data["completedAt"] is None

    def test_get_pending_topup_not_found(
        self, test_client: TestClient, user: User, session: Session
    ):
        # No pending topup for the user
        response = test_client.get("/api/accounting/pending-topup")
        assert response.status_code == 404
        data = response.json()
        assert "Not found" in data["detail"]


class TestGetUserTransactions:
    """Test cases for get user transactions endpoint."""

    def test_get_user_transactions_empty(
        self, test_client: TestClient, user: User, session: Session
    ):
        """Test retrieving transactions when user has no billing events."""
        response = test_client.get("/api/accounting/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["transactions"] == []
        assert data["total_count"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_next"] == False

    def test_get_user_transactions_with_events(
        self, test_client: TestClient, user: User, session: Session
    ):
        """Test retrieving transactions when user has billing events."""
        import uuid
        from datetime import datetime

        from src.accounting.models import BillingEventRecord

        # Create a few test billing event records
        event1 = BillingEventRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            event_type="BALANCE_TOPUP",
            event_data={
                "event_id": str(uuid.uuid4()),
                "user_id": str(user.id),
                "created_at": "2024-01-15T10:00:00",
                "amount_cents": 1000.0,
                "external_id": "stripe_session_123",
                "invoice_url": "https://example.com/invoice.pdf",
            },
            version=1,
            created_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        event2 = BillingEventRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            event_type="CREDIT_USAGE",
            event_data={
                "event_id": str(uuid.uuid4()),
                "user_id": str(user.id),
                "created_at": "2024-01-16T11:00:00",
                "amount_cents": 50.0,
                "external_id": "ai_request_456",
            },
            version=2,
            created_at=datetime(2024, 1, 16, 11, 0, 0),
        )

        event3 = BillingEventRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            event_type="BALANCE_REFUND",
            event_data={
                "event_id": str(uuid.uuid4()),
                "user_id": str(user.id),
                "created_at": "2024-01-17T12:00:00",
                "amount_cents": 200.0,
                "external_id": "refund_789",
                "reason": "CUSTOMER_REQUEST",
            },
            version=3,
            created_at=datetime(2024, 1, 17, 12, 0, 0),
        )

        # State transition event should be filtered out of the results
        event4 = BillingEventRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            event_type="STATE_TRANSITION",
            event_data={
                "event_id": str(uuid.uuid4()),
                "user_id": str(user.id),
                "created_at": "2024-01-18T13:00:00",
                "amount_cents": 0.0,
                "external_id": "state_transition_123",
            },
            version=4,
        )

        session.add_all([event1, event2, event3, event4])
        session.commit()

        # Test retrieving transactions
        response = test_client.get("/api/accounting/transactions")

        assert response.status_code == 200
        data = response.json()

        # Should have 3 transactions, ordered by created_at DESC (newest first)
        assert len(data["transactions"]) == 3
        assert data["total_count"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_next"] == False

        # Check that transactions are ordered by created_at DESC (newest first)
        assert data["transactions"][0]["createdAt"] == "2024-01-17T12:00:00"
        assert data["transactions"][1]["createdAt"] == "2024-01-16T11:00:00"
        assert data["transactions"][2]["createdAt"] == "2024-01-15T10:00:00"

        # Check transaction data conversion
        refund_tx = data["transactions"][0]  # Most recent (refund)
        assert refund_tx["amountCents"] == 200.0
        assert refund_tx["source"] == "BALANCE_REFUND"
        assert refund_tx["externalId"] == "refund_789"
        assert refund_tx["downloadUrl"] is None

        usage_tx = data["transactions"][1]  # Middle (usage)
        assert usage_tx["amountCents"] == 50.0
        assert usage_tx["source"] == "CREDIT_USAGE"
        assert usage_tx["externalId"] == "ai_request_456"

        topup_tx = data["transactions"][2]  # Oldest (topup)
        assert topup_tx["amountCents"] == 1000.0
        assert topup_tx["source"] == "BALANCE_TOPUP"
        assert topup_tx["externalId"] == "stripe_session_123"
        assert topup_tx["downloadUrl"] == "https://example.com/invoice.pdf"

    def test_get_user_transactions_pagination(
        self, test_client: TestClient, user: User, session: Session
    ):
        """Test transaction pagination."""
        import uuid
        from datetime import datetime

        from src.accounting.models import BillingEventRecord

        # Create 25 test events (more than default page size of 20)
        events = []
        for i in range(25):
            event = BillingEventRecord(
                id=uuid.uuid4(),
                user_id=user.id,
                event_type="CREDIT_USAGE",
                event_data={
                    "event_id": str(uuid.uuid4()),
                    "user_id": str(user.id),
                    "created_at": f"2024-01-{i+1:02d}T10:00:00",
                    "amount_cents": float(i * 10),
                    "external_id": f"request_{i}",
                },
                version=i + 1,
                created_at=datetime(2024, 1, min(i + 1, 31), 10, 0, 0),
            )
            events.append(event)

        session.add_all(events)
        session.commit()

        # Test first page (default page_size=20)
        response = test_client.get("/api/accounting/transactions")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 20
        assert data["total_count"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_next"] == True

        # Test second page
        response = test_client.get("/api/accounting/transactions?page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5  # Remaining 5 events
        assert data["total_count"] == 25
        assert data["page"] == 2
        assert data["page_size"] == 20
        assert data["has_next"] == False

        # Test custom page size
        response = test_client.get("/api/accounting/transactions?page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 10
        assert data["total_count"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["has_next"] == True

    def test_get_user_transactions_corrupted_event(
        self, test_client: TestClient, user: User, session: Session
    ):
        """Test handling of corrupted billing events."""
        import uuid
        from datetime import datetime

        from src.accounting.models import BillingEventRecord

        # Create a corrupted event with invalid event data
        corrupted_event = BillingEventRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            event_type="INVALID_EVENT_TYPE",  # Invalid event type
            event_data={"invalid": "data"},
            version=1,
            created_at=datetime.now(),
        )

        # Create a valid event
        valid_event = BillingEventRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            event_type="CREDIT_USAGE",
            event_data={
                "event_id": str(uuid.uuid4()),
                "user_id": str(user.id),
                "created_at": "2024-01-15T10:00:00",
                "amount_cents": 50.0,
                "external_id": "valid_request",
            },
            version=2,
            created_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        session.add_all([corrupted_event, valid_event])
        session.commit()

        # Should return only the valid transaction, corrupted one should be skipped
        response = test_client.get("/api/accounting/transactions")
        assert response.status_code == 200
        data = response.json()

        assert len(data["transactions"]) == 1  # Only valid event returned
        assert data["total_count"] == 2  # Total count includes corrupted event
        assert data["transactions"][0]["externalId"] == "valid_request"

    def test_get_user_transactions_no_amount_event(
        self, test_client: TestClient, user: User, session: Session
    ):
        """Test handling of events without amount_cents."""
        import uuid
        from datetime import datetime

        from src.accounting.models import BillingEventRecord

        # Create event without amount (like MONTHLY_CREDITS_RESET)
        event = BillingEventRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            event_type="SUBSCRIPTION_CANCEL",
            event_data={
                "event_id": str(uuid.uuid4()),
                "user_id": str(user.id),
                "created_at": "2024-01-15T10:00:00",
                "external_id": "subscription_cancel_123",
            },
            version=1,
            created_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        session.add(event)
        session.commit()

        response = test_client.get("/api/accounting/transactions")
        assert response.status_code == 200
        data = response.json()

        assert len(data["transactions"]) == 1
        assert (
            data["transactions"][0]["amountCents"] == 0.0
        )  # Default to 0 if no amount
        assert data["transactions"][0]["source"] == "SUBSCRIPTION_CANCEL"
        assert data["transactions"][0]["externalId"] == "subscription_cancel_123"
