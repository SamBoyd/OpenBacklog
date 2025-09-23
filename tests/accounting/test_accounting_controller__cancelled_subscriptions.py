from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

import src.accounting.accounting_controller as accounting_controller
from src.accounting.accounting_controller import (
    SubscriptionCancellationResult,
    get_overdue_subscription_cancellations,
    process_overdue_subscription_cancellation,
)
from src.accounting.billing_service import BillingServiceException
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.accounting.stripe_service import CancellationRefundResult
from src.models import User

# ---------------------------------------------------------------------------
# Helper fixtures and classes
# ---------------------------------------------------------------------------


class _FakeBillingServiceForCancellation:
    """Billing service stub for subscription cancellation tests."""

    def __init__(self, db: Session):
        self.db = db

    def cancel_subscription(self, user: User, external_id: str):
        return SimpleNamespace(
            balance_cents=0, status=UserAccountStatus.NO_SUBSCRIPTION
        )

    def reactivate_subscription(self, user: User, external_id: str):
        return SimpleNamespace(
            balance_cents=0, status=UserAccountStatus.ACTIVE_SUBSCRIPTION
        )


# ---------------------------------------------------------------------------
# Tests for get_overdue_subscription_cancellations
# ---------------------------------------------------------------------------


def test_get_overdue_subscription_cancellations_basic(session: Session, user: User):
    """Test finding overdue subscription cancellations."""
    # Setup user with overdue cancellation
    user.account_details.subscription_cancel_at = datetime.now() - timedelta(hours=1)
    user.account_details.subscription_canceled_at = None
    user.account_details.subscription_cancel_at_period_end = True
    session.add(user.account_details)
    session.commit()

    # Call function
    overdue_users = get_overdue_subscription_cancellations(session)

    # Verify results
    assert len(overdue_users) == 1
    assert overdue_users[0].id == user.id


def test_get_overdue_subscription_cancellations_filters_already_cancelled(
    session: Session, user: User, other_user: User
):
    """Test that already cancelled subscriptions are excluded."""
    # Setup first user with overdue but not yet cancelled
    user.account_details.subscription_cancel_at = datetime.now() - timedelta(hours=1)
    user.account_details.subscription_canceled_at = None
    user.account_details.subscription_cancel_at_period_end = True
    session.add(user.account_details)

    # Setup second user with overdue but already cancelled
    other_user.account_details.subscription_cancel_at = datetime.now() - timedelta(
        hours=1
    )
    other_user.account_details.subscription_canceled_at = datetime.now() - timedelta(
        minutes=30
    )
    session.add(other_user.account_details)
    session.commit()

    # Call function
    overdue_users = get_overdue_subscription_cancellations(session)

    # Verify only uncancelled user is returned
    assert len(overdue_users) == 1
    assert overdue_users[0].id == user.id


def test_get_overdue_subscription_cancellations_filters_future_cancellations(
    session: Session, user: User
):
    """Test that future cancellation dates are excluded."""
    # Setup user with future cancellation date
    user.account_details.subscription_cancel_at = datetime.now() + timedelta(hours=1)
    user.account_details.subscription_canceled_at = None
    user.account_details.subscription_cancel_at_period_end = True
    session.add(user.account_details)
    session.commit()

    # Call function
    overdue_users = get_overdue_subscription_cancellations(session)

    # Verify no results
    assert len(overdue_users) == 0


def test_get_overdue_subscription_cancellations_with_limit(
    session: Session, user: User, other_user: User
):
    """Test that limit parameter works correctly."""
    # Setup both users with overdue cancellations
    user.account_details.subscription_cancel_at = datetime.now() - timedelta(hours=1)
    user.account_details.subscription_canceled_at = None
    user.account_details.subscription_cancel_at_period_end = True
    session.add(user.account_details)

    other_user.account_details.subscription_cancel_at = datetime.now() - timedelta(
        hours=2
    )
    other_user.account_details.subscription_canceled_at = None
    other_user.account_details.subscription_cancel_at_period_end = True
    session.add(other_user.account_details)
    session.commit()

    # Call function with limit
    overdue_users = get_overdue_subscription_cancellations(session, limit=1)

    # Verify only one result
    assert len(overdue_users) == 1


def test_get_overdue_subscription_cancellations_empty_result(
    session: Session, user: User
):
    """Test handling when no overdue cancellations exist."""
    # Setup user with no cancellation scheduled
    user.account_details.subscription_cancel_at = None
    user.account_details.subscription_canceled_at = None
    user.account_details.subscription_cancel_at_period_end = None
    session.add(user.account_details)
    session.commit()

    # Call function
    overdue_users = get_overdue_subscription_cancellations(session)

    # Verify empty results
    assert len(overdue_users) == 0


# ---------------------------------------------------------------------------
# Tests for process_overdue_subscription_cancellation
# ---------------------------------------------------------------------------


def test_process_overdue_subscription_cancellation_success(
    session: Session, user: User
):
    """Test successful processing of overdue subscription cancellation."""
    # Setup user with Stripe customer ID
    user.account_details.stripe_customer_id = "cus_test123"
    session.add(user.account_details)
    session.commit()

    # Mock the services
    with patch(
        "src.accounting.accounting_controller.BillingService",
        _FakeBillingServiceForCancellation,
    ):
        # Call function
        result = process_overdue_subscription_cancellation(user, session)

    # Verify success
    assert result.success is True
    assert result.billing_cancelled is True
    assert result.stripe_cancelled is True
    assert result.error is None
