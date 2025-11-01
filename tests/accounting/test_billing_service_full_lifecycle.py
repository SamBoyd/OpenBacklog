"""
Full lifecycle integration test for BillingService.

This test validates the complete user billing lifecycle from signup through refund,
testing all state transitions and balance management operations in a realistic scenario.
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.accounting.billing_service import BillingService
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.models import User


@pytest.fixture
def lifecycle_user(session: Session) -> User:
    """Create a user for lifecycle testing."""
    user = User(
        id=uuid.uuid4(),
        name="Lifecycle Test User",
        email=f"lifecycle_{uuid.uuid4().hex[:8]}@test.com",
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
    session.add(user_account_details)
    session.commit()
    session.refresh(user)

    return user


class TestBillingServiceFullLifecycle:
    """Test the complete billing lifecycle from signup to refund."""

    def test_full_billing_lifecycle(self, lifecycle_user: User, session: Session):
        """
        Test the complete billing lifecycle:
        1. User signs up for free tier
        2. User signs up for paid tier
        3. User cancels subscription
        4. User reactivates subscription
        5. User records multiple usages
        6. User starts new billing cycle
        7. User records multiple usages
        8. User starts new billing cycle
        9. User records usage until subscription balance exhausted
        10. User tries to record usage when balance exhausted
        11. User top-ups balance
        12. User records usage until balance exhausted
        13. User top-ups balance
        14. User records usage
        15. User starts new billing cycle
        16. User requests full refund (refunds balance AND cancels subscription)
        """
        billing_service = BillingService(session)

        # Step 1: User signs up for free tier
        account_details = billing_service.skip_subscription(
            lifecycle_user, "onboarding_complete_1"
        )
        assert account_details.status == UserAccountStatus.NO_SUBSCRIPTION
        assert account_details.balance_cents == 0
        assert account_details.monthly_credits_total == 0
        assert account_details.monthly_credits_used == 0

        # Step 2: User signs up for paid tier
        account_details = billing_service.signup_subscription(
            lifecycle_user, "stripe_sub_123"
        )
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION
        assert account_details.balance_cents == 0
        assert account_details.monthly_credits_total == 700
        assert account_details.monthly_credits_used == 0

        # Step 3: User cancels subscription
        account_details = billing_service.cancel_subscription(
            lifecycle_user, "cancel_reason_1"
        )
        assert account_details.status == UserAccountStatus.NO_SUBSCRIPTION
        assert account_details.balance_cents == 0
        assert account_details.monthly_credits_total == 0
        assert account_details.monthly_credits_used == 0

        # Step 4: User reactivates subscription
        account_details = billing_service.reactivate_subscription(
            lifecycle_user, "stripe_sub_456"
        )
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION
        assert account_details.balance_cents == 0
        assert account_details.monthly_credits_total == 700
        assert account_details.monthly_credits_used == 0

        # Step 5: User records multiple usages
        account_details = billing_service.record_usage(lifecycle_user, 100.0, "usage_1")
        assert account_details.monthly_credits_used == 100
        assert account_details.balance_cents == 0
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION

        account_details = billing_service.record_usage(lifecycle_user, 200.0, "usage_2")
        assert account_details.monthly_credits_used == 300
        assert account_details.balance_cents == 0
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION

        account_details = billing_service.record_usage(lifecycle_user, 150.0, "usage_3")
        assert account_details.monthly_credits_used == 450
        assert account_details.balance_cents == 0
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION

        # Step 6: User starts new billing cycle
        session.refresh(lifecycle_user.account_details)
        lifecycle_user.account_details.next_billing_cycle_starts = (
            datetime.now() - timedelta(days=1)
        )
        session.add(lifecycle_user.account_details)
        session.commit()

        account_details = billing_service.start_new_billing_cycle(lifecycle_user)
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION
        assert account_details.balance_cents == 0
        assert account_details.monthly_credits_used == 0
        assert account_details.monthly_credits_total == 700

        # Step 7: User records multiple usages
        account_details = billing_service.record_usage(lifecycle_user, 300.0, "usage_4")
        assert account_details.monthly_credits_used == 300
        assert account_details.balance_cents == 0

        account_details = billing_service.record_usage(lifecycle_user, 250.0, "usage_5")
        assert account_details.monthly_credits_used == 550
        assert account_details.balance_cents == 0

        # Step 8: User starts new billing cycle
        session.refresh(lifecycle_user.account_details)
        lifecycle_user.account_details.next_billing_cycle_starts = (
            datetime.now() - timedelta(days=1)
        )
        session.add(lifecycle_user.account_details)
        session.commit()

        account_details = billing_service.start_new_billing_cycle(lifecycle_user)
        assert account_details.monthly_credits_used == 0
        assert account_details.monthly_credits_total == 700

        # Step 9: User records usage until subscription balance exhausted
        account_details = billing_service.record_usage(lifecycle_user, 500.0, "usage_6")
        assert account_details.monthly_credits_used == 500
        assert account_details.balance_cents == 0
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION

        account_details = billing_service.record_usage(lifecycle_user, 250.0, "usage_7")
        # With 200 credits remaining (700 - 500), this uses 200 credits and 50 from balance
        assert account_details.monthly_credits_used == 700
        assert account_details.balance_cents == -50.0
        assert account_details.status == UserAccountStatus.SUSPENDED

        account_details = billing_service.record_usage(lifecycle_user, 100.0, "usage_8")
        # Now in SUSPENDED state, directly deducts from balance
        assert account_details.monthly_credits_used == 700
        assert account_details.balance_cents == -150.0
        assert account_details.status == UserAccountStatus.SUSPENDED

        # Step 10: User tries to record usage when balance exhausted
        account_details = billing_service.record_usage(lifecycle_user, 50.0, "usage_9")
        # Balance: -150 - 50 = -200
        assert account_details.balance_cents == -200.0
        assert account_details.status == UserAccountStatus.SUSPENDED

        # Step 11: User top-ups balance
        # Current balance is -200 (from step 10: -150 - 50)
        account_details = billing_service.topup_balance(
            lifecycle_user, 500, "topup_1", "https://invoice.url/1"
        )
        # Balance: -200 + 500 = 300
        assert account_details.balance_cents == 300.0
        assert account_details.status == UserAccountStatus.METERED_BILLING

        # Step 12: User records usage until balance exhausted
        # Current balance is 300 from topup
        account_details = billing_service.record_usage(
            lifecycle_user, 200.0, "usage_10"
        )
        assert account_details.balance_cents == 100.0
        assert account_details.status == UserAccountStatus.METERED_BILLING

        account_details = billing_service.record_usage(
            lifecycle_user, 100.0, "usage_11"
        )
        # When balance reaches 0, transitions to SUSPENDED
        assert account_details.balance_cents == 0.0
        assert account_details.status == UserAccountStatus.SUSPENDED

        account_details = billing_service.record_usage(lifecycle_user, 50.0, "usage_12")
        assert account_details.balance_cents == -50.0
        assert account_details.status == UserAccountStatus.SUSPENDED

        # Step 13: User top-ups balance
        # Current balance is -50 from step 12
        account_details = billing_service.topup_balance(
            lifecycle_user, 300, "topup_2", "https://invoice.url/2"
        )
        # Balance: -50 + 300 = 250
        assert account_details.balance_cents == 250.0
        assert account_details.status == UserAccountStatus.METERED_BILLING

        # Step 14: User records usage
        account_details = billing_service.record_usage(
            lifecycle_user, 100.0, "usage_13"
        )
        assert account_details.balance_cents == 150.0
        assert account_details.status == UserAccountStatus.METERED_BILLING

        # Step 15: User starts new billing cycle
        session.refresh(lifecycle_user.account_details)
        lifecycle_user.account_details.next_billing_cycle_starts = (
            datetime.now() - timedelta(days=1)
        )
        session.add(lifecycle_user.account_details)
        session.commit()

        account_details = billing_service.start_new_billing_cycle(lifecycle_user)
        assert account_details.monthly_credits_used == 0
        assert account_details.monthly_credits_total == 700
        assert account_details.status == UserAccountStatus.ACTIVE_SUBSCRIPTION
        assert account_details.balance_cents == 150.0

        # Step 16: User requests full refund
        # This should refund the balance AND cancel the subscription
        session.refresh(lifecycle_user.account_details)
        assert lifecycle_user.account_details.balance_cents == 150.0
        assert (
            lifecycle_user.account_details.status
            == UserAccountStatus.ACTIVE_SUBSCRIPTION
        )

        account_details = billing_service.process_full_refund(
            lifecycle_user, "refund_1"
        )
        # Assert both refund and cancellation happened
        assert account_details.balance_cents == 0.0
        assert account_details.status == UserAccountStatus.NO_SUBSCRIPTION
