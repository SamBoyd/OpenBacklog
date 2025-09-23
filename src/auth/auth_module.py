"""
Main auth module that provides simplified integration.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.db import get_db
from src.models import User

from .factory import get_auth_provider, get_provider_type
from .providers import TokenValidation
from .routers import auth_router

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for API authentication
security = HTTPBearer(auto_error=False)


class AuthModule:
    """Main authentication module."""

    def __init__(self, app: FastAPI):
        """Initialize auth module with FastAPI app."""
        self.app = app
        self.provider = get_auth_provider()

        # Include auth router
        app.include_router(auth_router)

        logger.info(f"Auth module initialized with provider: {get_provider_type()}")

    async def get_current_user(
        self,
        request: Request,
        db: Session,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> Optional[User]:
        """
        Get current authenticated user.

        Supports both cookie-based and bearer token authentication.
        """
        token = None

        # Try bearer token first
        if credentials:
            token = credentials.credentials
        else:
            # Fallback to cookie
            token = request.cookies.get("access_token")

        if not token:
            return None

        try:
            # Validate token
            validation = await self.provider.validate_token(token)
            if not validation.valid:
                return None

            # Get user from database using provided session
            user = self._get_user_by_id(validation.user_id, db)
            return user

        except Exception as e:
            logger.debug(f"Auth validation error: {e}")
            return None

    async def require_auth(
        self,
        request: Request,
        db: Session,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> User:
        """
        Require authentication, raise 401 if not authenticated.
        """
        user = await self.get_current_user(request, db, credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return user

    async def validate_token(self, token: str) -> TokenValidation:
        """Validate a token and return validation result."""
        return await self.provider.validate_token(token)

    async def create_tokens_for_user(self, user: User):
        """Create tokens for a user."""
        return await self.provider.create_tokens(user)

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current auth provider."""
        return {
            "provider_type": get_provider_type(),
            "provider_name": self.provider.get_provider_name(),
            "supports_oauth": hasattr(self.provider, "get_authorization_url"),
            "supports_password_auth": hasattr(self.provider, "authenticate_user"),
        }

    def _get_user_by_id(self, user_id: str, db: Session) -> Optional[User]:
        """Get user by ID from database using provided session."""
        try:
            from sqlalchemy.orm import selectinload

            user = (
                db.query(User)
                .options(selectinload(User.account_details))
                .filter(User.id == user_id)
                .first()
            )
            return user

        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None


# Global auth module instance
_auth_module: Optional[AuthModule] = None


def initialize_auth(app: FastAPI) -> AuthModule:
    """
    Initialize the auth module with FastAPI app.

    Args:
        app: FastAPI application instance

    Returns:
        AuthModule instance
    """
    global _auth_module
    _auth_module = AuthModule(app)
    return _auth_module


def get_auth_module() -> AuthModule:
    """
    Get the global auth module instance.

    Returns:
        AuthModule instance

    Raises:
        RuntimeError: If auth module not initialized
    """
    if _auth_module is None:
        raise RuntimeError("Auth module not initialized. Call initialize_auth() first.")
    return _auth_module


# Dependency functions for FastAPI routes
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """FastAPI dependency to get current user (optional)."""
    auth_module = get_auth_module()
    return await auth_module.get_current_user(request, db, credentials)


async def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to require authentication."""
    auth_module = get_auth_module()
    return await auth_module.require_auth(request, db, credentials)


# Legacy compatibility functions
async def get_current_active_user(user: User = Depends(require_auth)) -> User:
    """Legacy compatibility - get current active user."""
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_verified_user(user: User = Depends(require_auth)) -> User:
    """Legacy compatibility - get current verified user."""
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Unverified user")
    return user
