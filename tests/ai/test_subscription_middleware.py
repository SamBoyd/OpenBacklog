"""
Unit tests for subscription middleware.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from hamcrest import assert_that, equal_to, has_string

from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.ai.subscription_middleware import require_active_subscription
from src.models import User


@pytest.mark.asyncio
async def test_require_active_subscription_allows_active_subscription(session):
    """Test that users with ACTIVE_SUBSCRIPTION status can access AI features"""
    # Create user with ACTIVE_SUBSCRIPTION status
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Set account status to ACTIVE_SUBSCRIPTION
    user.account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
    session.add(user.account_details)
    session.commit()

    # Call the middleware
    result = await require_active_subscription(user=user, db=session)

    # Should return the user without raising an exception
    assert_that(result.id, equal_to(user.id))


@pytest.mark.asyncio
async def test_require_active_subscription_allows_metered_billing(session):
    """Test that users with METERED_BILLING status can access AI features"""
    # Create user with METERED_BILLING status
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="metered@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Set account status to METERED_BILLING
    user.account_details.status = UserAccountStatus.METERED_BILLING
    session.add(user.account_details)
    session.commit()

    # Call the middleware
    result = await require_active_subscription(user=user, db=session)

    # Should return the user without raising an exception
    assert_that(result.id, equal_to(user.id))


@pytest.mark.asyncio
async def test_require_active_subscription_denies_no_subscription(session):
    """Test that users with NO_SUBSCRIPTION status are denied access"""
    # Create user with NO_SUBSCRIPTION status
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="nosub@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Set account status to NO_SUBSCRIPTION
    user.account_details.status = UserAccountStatus.NO_SUBSCRIPTION
    session.add(user.account_details)
    session.commit()

    # Call the middleware and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await require_active_subscription(user=user, db=session)

    # Verify the exception details
    assert_that(exc_info.value.status_code, equal_to(403))
    assert_that(
        exc_info.value.detail,
        equal_to(
            "AI features require a subscription. Visit /workspace/billing to subscribe."
        ),
    )


@pytest.mark.asyncio
async def test_require_active_subscription_denies_new_user(session):
    """Test that users with NEW status are denied access"""
    # Create user with NEW status
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="new@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Set account status to NEW
    user.account_details.status = UserAccountStatus.NEW
    session.add(user.account_details)
    session.commit()

    # Call the middleware and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await require_active_subscription(user=user, db=session)

    # Verify the exception details
    assert_that(exc_info.value.status_code, equal_to(403))


@pytest.mark.asyncio
async def test_require_active_subscription_denies_suspended(session):
    """Test that users with SUSPENDED status are denied access"""
    # Create user with SUSPENDED status
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="suspended@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Set account status to SUSPENDED
    user.account_details.status = UserAccountStatus.SUSPENDED
    session.add(user.account_details)
    session.commit()

    # Call the middleware and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await require_active_subscription(user=user, db=session)

    # Verify the exception details
    assert_that(exc_info.value.status_code, equal_to(403))


@pytest.mark.asyncio
async def test_require_active_subscription_denies_closed(session):
    """Test that users with CLOSED status are denied access"""
    # Create user with CLOSED status
    user = User(
        id=uuid.uuid4(),
        name="Test User",
        email="closed@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Set account status to CLOSED
    user.account_details.status = UserAccountStatus.CLOSED
    session.add(user.account_details)
    session.commit()

    # Call the middleware and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await require_active_subscription(user=user, db=session)

    # Verify the exception details
    assert_that(exc_info.value.status_code, equal_to(403))
