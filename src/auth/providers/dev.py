"""
Development authentication provider.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import get_async_db
from src.models import OAuthAccount, User

from ..jwt_utils import create_refresh_token, create_unified_jwt, validate_jwt
from .base import AuthProvider, AuthResult, TokenPair, TokenValidation, UserInfo

logger = logging.getLogger(__name__)


class DevAuthProvider(AuthProvider):
    """Development authentication provider with auto-login and test users."""

    def __init__(self):
        """Initialize dev auth provider."""
        self.dev_email = settings.dev_user_email
        self.dev_password = settings.dev_user_password
        self.oauth_account_name = settings.dev_jwt_oauth_account_name

    async def get_authorization_url(
        self, redirect_uri: str, state: Optional[str] = None, **kwargs
    ) -> str:
        """
        Dev auth can auto-login, so return a special dev login URL.

        Args:
            redirect_uri: Where to redirect after login
            state: State parameter

        Returns:
            Dev login URL that auto-logs in the dev user
        """
        dev_login_url = "/auth/dev-login?redirect_uri=/workspace"
        if state:
            dev_login_url += f"&state={state}"
        return dev_login_url

    async def handle_callback(
        self, code: str, redirect_uri: str, state: Optional[str] = None, **kwargs
    ) -> AuthResult:
        """
        Dev auth doesn't use real OAuth callbacks.
        This method shouldn't be called for dev auth.
        """
        raise NotImplementedError("Dev auth doesn't use OAuth callbacks")

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user (mainly for dev user).

        Args:
            username: Username or email
            password: Password

        Returns:
            User if authentication successful
        """
        # For dev mode, allow any username with dev password
        if password == self.dev_password:
            user = await self._get_or_create_dev_user(username)
            return user

        return None

    async def auto_login_dev_user(self) -> Optional[User]:
        """
        Auto-login the default dev user.

        Returns:
            Dev user instance
        """
        return await self._get_or_create_dev_user(self.dev_email)

    async def create_tokens(self, user: User) -> TokenPair:
        """Create tokens for dev user."""
        access_token = create_unified_jwt(
            user=user,
            lifetime_seconds=settings.dev_jwt_lifetime_seconds,
            secret=settings.dev_jwt_secret,
            algorithm=settings.dev_jwt_algorithm,
        )

        refresh_token = create_refresh_token(user, secret=settings.dev_jwt_secret)

        # Store access token in database
        await self._store_access_token(str(user.id), access_token)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.dev_jwt_lifetime_seconds,
            token_type="Bearer",  # nosec
        )

    async def validate_token(self, token: str) -> TokenValidation:
        """Validate dev JWT token."""
        # First check if token exists in database (not revoked)
        if not await self._token_exists_in_db(token):
            return TokenValidation(valid=False, error="Token not found or revoked")

        try:
            claims = validate_jwt(
                token,
                secret=settings.dev_jwt_secret,
                algorithm=settings.dev_jwt_algorithm,
            )
            return TokenValidation(valid=True, user_id=claims.get("sub"), claims=claims)
        except Exception as e:
            return TokenValidation(valid=False, error=str(e))

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh dev tokens."""
        from ..jwt_utils import validate_refresh_token

        user_id = validate_refresh_token(refresh_token, secret=settings.dev_jwt_secret)
        if not user_id:
            raise ValueError("Invalid refresh token")

        # Get user from database
        async for db in get_async_db():
            user = await db.get(User, user_id)
            if not user:
                raise ValueError("User not found")

            return await self.create_tokens(user)

    async def get_user_info(self, token: str) -> Optional[UserInfo]:
        """Get user info from dev token."""
        validation = await self.validate_token(token)
        if not validation.valid or not validation.claims:
            return None

        claims = validation.claims
        return UserInfo(
            email=claims.get("email", ""),
            sub=claims.get("sub", ""),
            name=claims.get("name", "Dev User"),
            email_verified=True,
        )

    async def _get_or_create_dev_user(self, email: str) -> User:
        """Get or create a dev user."""
        async for db in get_async_db():
            # Look for existing user
            from sqlalchemy import select

            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                # Create new dev user
                user = User(
                    email=email,
                    hashed_password="",  # Dev users don't need real passwords
                    is_active=True,
                    is_verified=True,
                    is_superuser=False,
                    name="Dev User",
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)

                oauth_account = OAuthAccount(
                    oauth_name="dev_user",
                    access_token="dev_user_access_token",  # nosec
                    account_id="dev_user",
                    account_email=email,
                    user=user,
                )
                db.add(oauth_account)
                await db.commit()

            return user

    async def _get_or_create_oauth_account(self, user: User) -> str:
        """Get or create OAuth account for dev user."""
        async for db in get_async_db():
            # Look for existing OAuth account
            from sqlalchemy import select

            result = await db.execute(
                select(OAuthAccount).filter(OAuthAccount.user_id == user.id)
            )
            oauth_account = result.scalar_one_or_none()

            if not oauth_account:
                # Create new OAuth account
                account_id = f"dev-{user.email}"

                # Create a temporary JWT for the OAuth account
                temp_jwt = create_unified_jwt(
                    user=user,
                    lifetime_seconds=settings.dev_jwt_lifetime_seconds,
                    secret=settings.dev_jwt_secret,
                )

                oauth_account = OAuthAccount(
                    oauth_name=self.oauth_account_name,
                    access_token=temp_jwt,
                    expires_at=(
                        datetime.now()
                        + timedelta(seconds=settings.dev_jwt_lifetime_seconds)
                    ).timestamp(),
                    refresh_token=temp_jwt,
                    account_id=account_id,
                    account_email=user.email,
                    user_id=user.id,
                )
                db.add(oauth_account)
                await db.commit()

            return oauth_account.account_id

    async def create_test_user(
        self, email: str, password: Optional[str] = None, name: Optional[str] = None
    ) -> User:
        """
        Create a test user for development.

        Args:
            email: User email
            password: Password (optional for dev)
            name: User name

        Returns:
            Created test user
        """
        async for db in get_async_db():
            # Check if user already exists
            from sqlalchemy import select

            result = await db.execute(select(User).filter(User.email == email))
            existing = result.scalar_one_or_none()
            if existing:
                return existing

            # Create test user
            user = User(
                email=email,
                hashed_password="",  # Test users don't need real passwords
                is_active=True,
                is_verified=True,
                is_superuser=False,
                name=name or "Test User",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Create OAuth account
            await self._get_or_create_oauth_account(user)

            return user
