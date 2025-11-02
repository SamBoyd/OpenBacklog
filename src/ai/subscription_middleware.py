"""
Middleware for enforcing subscription requirements on AI endpoints.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src.accounting.models import UserAccountStatus
from src.db import get_db
from src.models import User
from src.views import dependency_to_override


async def require_active_subscription(
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that ensures the user has an active subscription
    before allowing access to AI features.

    Args:
        user: The authenticated user from dependency_to_override
        db: Database session

    Returns:
        User: The authenticated user if they have an active subscription

    Raises:
        HTTPException: 403 Forbidden if user doesn't have an active subscription
    """
    # Check if user has account_details and check status
    if user.account_details:
        # Merge user into the current session if needed
        if user not in db:
            user = db.merge(user, load=False)

        # Allow access for ACTIVE_SUBSCRIPTION and METERED_BILLING statuses
        if user.account_details.status in [
            UserAccountStatus.ACTIVE_SUBSCRIPTION,
            UserAccountStatus.METERED_BILLING,
        ]:
            return user

    # Deny access for all other statuses
    raise HTTPException(
        status_code=403,
        detail="AI features require a subscription. Visit /workspace/billing to subscribe.",
    )
