"""
Simple username/password authentication provider.
"""

import logging
from typing import Optional

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_db
from src.models import OAuthAccount, User

from ..jwt_utils import (
    create_refresh_token,
    create_unified_jwt,
    validate_jwt,
    validate_refresh_token,
)
from .base import AuthProvider, AuthResult, TokenPair, TokenValidation, UserInfo

logger = logging.getLogger(__name__)


class SimpleAuthProvider(AuthProvider):
    """Simple username/password authentication provider for open source deployments."""

    def __init__(self):
        """Initialize simple auth provider."""
        pass

    async def get_authorization_url(
        self, redirect_uri: str, state: Optional[str] = None, **kwargs
    ) -> str:
        """
        Simple auth doesn't use OAuth, so this returns a login page URL.

        Args:
            redirect_uri: Where to redirect after login
            state: State parameter (unused for simple auth)

        Returns:
            URL to login form
        """
        # For simple auth, we redirect to a login form
        login_url = "/auth/login"

        return login_url

    async def handle_callback(
        self, code: str, redirect_uri: str, state: Optional[str] = None, **kwargs
    ) -> AuthResult:
        """
        Simple auth doesn't use callbacks.
        This method shouldn't be called for simple auth.
        """
        raise NotImplementedError("Simple auth doesn't use OAuth callbacks")

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/password.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        try:
            async for db in get_async_db():
                # Look up user by email (username)
                from sqlalchemy import select

                result = await db.execute(
                    select(User).filter(User.email == username.lower())
                )
                user = result.scalar_one_or_none()

                if not user:
                    return None

                # Check password
                if not user.hashed_password:
                    return None

                if not self._verify_password(password, user.hashed_password):
                    return None

                return user

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def create_tokens(self, user: User) -> TokenPair:
        """Create tokens for authenticated user."""
        access_token = create_unified_jwt(user=user)
        refresh_token = create_refresh_token(user)

        # Store access token in database
        await self._store_access_token(str(user.id), access_token)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,  # 1 hour
            token_type="Bearer",
        )

    async def validate_token(self, token: str) -> TokenValidation:
        """Validate JWT token."""
        # First check if token exists in database (not revoked)
        if not await self._token_exists_in_db(token):
            return TokenValidation(valid=False, error="Token not found or revoked")

        try:
            claims = validate_jwt(token)
            return TokenValidation(valid=True, user_id=claims.get("sub"), claims=claims)
        except Exception as e:
            return TokenValidation(valid=False, error=str(e))

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token."""
        user_id = validate_refresh_token(refresh_token)
        if not user_id:
            raise ValueError("Invalid refresh token")

        # Get user from database
        async for db in get_async_db():
            user = await db.get(User, user_id)
            if not user:
                raise ValueError("User not found")

            return await self.create_tokens(user)

    async def get_user_info(self, token: str) -> Optional[UserInfo]:
        """Get user info from token."""
        validation = await self.validate_token(token)
        if not validation.valid or not validation.claims:
            return None

        claims = validation.claims
        return UserInfo(
            email=claims.get("email", ""),
            sub=claims.get("sub", ""),
            name=claims.get("name"),
            email_verified=claims.get("email_verified", True),
        )

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    async def register_user(
        self, email: str, password: str, name: Optional[str] = None
    ) -> Optional[User]:
        """
        Register a new user.

        Args:
            email: User email
            password: Plain text password
            name: Optional user name

        Returns:
            Created user or None if registration failed
        """
        try:
            async for db in get_async_db():
                # Check if user already exists
                from sqlalchemy import select

                result = await db.execute(
                    select(User).filter(User.email == email.lower())
                )
                existing = result.scalar_one_or_none()
                if existing:
                    logger.warning(
                        f"Registration attempt of existing user email {existing.email}"
                    )
                    return None

                # Create new user
                user = User(
                    email=email.lower(),
                    hashed_password=self.hash_password(password),
                    is_active=True,
                    is_verified=True,  # Auto-verify for simple auth
                    is_superuser=False,
                )

                db.add(user)
                await db.commit()
                await db.refresh(user)

                oauth_account = OAuthAccount(
                    oauth_name="simple_auth",
                    access_token="",
                    account_id="simple_auth",
                    account_email=email.lower(),
                    user=user,
                )
                db.add(oauth_account)
                await db.commit()

                logger.info(f"Created new user: {email}")
                return user

        except Exception as e:
            logger.exception(f"User registration error: {e}")
            return None

    async def change_password(
        self, user: User, old_password: str, new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user: User to change password for
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully
        """
        try:
            # Verify old password
            if not user.hashed_password or not self._verify_password(
                old_password, user.hashed_password
            ):
                return False

            async for db in get_async_db():
                user.hashed_password = self.hash_password(new_password)
                await db.commit()
                return True

        except Exception as e:
            logger.error(f"Password change error: {e}")
            return False
