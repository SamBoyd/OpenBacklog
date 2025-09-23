"""
Base authentication provider interface and data models.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from src.models import AccessToken, User


@dataclass
class UserInfo:
    """User information from auth provider."""

    email: str
    sub: str  # Subject/user identifier from provider
    name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = True


@dataclass
class TokenPair:
    """Access and refresh token pair."""

    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"


@dataclass
class TokenValidation:
    """Token validation result."""

    valid: bool
    user_id: Optional[str] = None
    claims: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class AuthResult:
    """Authentication result from callback."""

    user_info: UserInfo
    tokens: TokenPair
    user: Optional[User] = None  # Populated after user lookup/creation


class AuthProvider(ABC):
    """
    Abstract base class for authentication providers.

    All auth providers must implement these methods to provide
    a consistent interface for different authentication strategies.
    """

    @abstractmethod
    async def get_authorization_url(
        self, redirect_uri: str, state: Optional[str] = None, **kwargs
    ) -> str:
        """
        Generate authorization URL for OAuth flow.

        Args:
            redirect_uri: Where to redirect after auth
            state: State parameter for CSRF protection
            **kwargs: Provider-specific parameters

        Returns:
            Authorization URL to redirect user to
        """
        pass

    @abstractmethod
    async def handle_callback(
        self, code: str, redirect_uri: str, state: Optional[str] = None, **kwargs
    ) -> AuthResult:
        """
        Handle OAuth callback and exchange code for tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Original redirect URI
            state: State parameter for validation
            **kwargs: Provider-specific parameters

        Returns:
            AuthResult with user info and tokens
        """
        pass

    @abstractmethod
    async def create_tokens(self, user: User) -> TokenPair:
        """
        Create access and refresh tokens for a user.

        Args:
            user: User to create tokens for

        Returns:
            TokenPair with access and refresh tokens
        """
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> TokenValidation:
        """
        Validate an access token and extract claims.

        Args:
            token: Access token to validate

        Returns:
            TokenValidation with validation result
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New TokenPair with fresh access token
        """
        pass

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/password.

        Default implementation returns None (not supported).
        Override for providers that support password auth.

        Args:
            username: Username or email
            password: Password

        Returns:
            User if authentication successful, None otherwise
        """
        return None

    async def get_user_info(self, token: str) -> Optional[UserInfo]:
        """
        Get user information from access token.

        Default implementation validates token and extracts claims.
        Override for providers that need to make additional API calls.

        Args:
            token: Access token

        Returns:
            UserInfo if token is valid, None otherwise
        """
        validation = await self.validate_token(token)
        if not validation.valid or not validation.claims:
            return None

        claims = validation.claims
        return UserInfo(
            email=claims.get("email", ""),
            sub=claims.get("sub", ""),
            name=claims.get("name"),
            picture=claims.get("picture"),
            email_verified=claims.get("email_verified", True),
        )

    def get_provider_name(self) -> str:
        """Get human-readable provider name."""
        return self.__class__.__name__.replace("Provider", "")

    async def _store_access_token(self, user_id: str, token: str) -> None:
        """
        Store access token in database.

        Args:
            user_id: User ID to store token for
            token: Access token to store
        """
        try:
            from sqlalchemy import delete

            from src.db import get_async_db

            logger = logging.getLogger(__name__)

            async for db in get_async_db():
                # Insert new token
                access_token = AccessToken(
                    token=token, user_id=user_id, created_at=datetime.now()
                )
                db.add(access_token)
                await db.commit()

                logger.debug(f"Stored access token for user {user_id}")
                break

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to store access token for user {user_id}: {e}")

    async def _revoke_tokens_for_user(self, user_id: str) -> None:
        """
        Revoke all tokens for a user.

        Args:
            user_id: User ID to revoke tokens for
        """
        try:
            from sqlalchemy import delete

            from src.db import get_async_db

            logger = logging.getLogger(__name__)

            async for db in get_async_db():
                result = await db.execute(
                    delete(AccessToken).where(AccessToken.user_id == user_id)
                )
                await db.commit()

                logger.info(f"Revoked {result.rowcount} tokens for user {user_id}")
                break

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to revoke tokens for user {user_id}: {e}")

    async def _token_exists_in_db(self, token: str) -> bool:
        """
        Check if token exists in database.

        Args:
            token: Token to check

        Returns:
            True if token exists, False otherwise
        """
        try:
            from sqlalchemy import select

            from src.db import get_async_db

            async for db in get_async_db():
                result = await db.execute(
                    select(AccessToken).where(AccessToken.token == token)
                )
                access_token = result.scalar_one_or_none()
                return access_token is not None

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to check token existence: {e}")
            return False

    async def auto_login_dev_user(self) -> Optional[User]:
        raise NotImplementedError("Base class called")

    async def register_user(
        self, email: str, password: str, name: Optional[str] = None
    ) -> Optional[User]:
        raise NotImplementedError("Base class called")
