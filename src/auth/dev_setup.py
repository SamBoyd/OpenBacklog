import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import User

logger = logging.getLogger(__name__)


async def create_test_user(email: str, password: str, db: AsyncSession) -> User:
    """
    Create a test user for testing purposes.

    Note: This uses the new auth system's simple provider logic.
    """
    from src.auth.providers.simple import SimpleAuthProvider

    provider = SimpleAuthProvider()

    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == email.lower()))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Create new user
    user = User(
        email=email.lower(),
        hashed_password=provider.hash_password(password),
        is_active=True,
        is_verified=True,  # Auto-verify for test users
        is_superuser=False,
        name="Test User",
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user
