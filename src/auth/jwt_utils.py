"""
JWT utilities for unified token creation and validation.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Dict, Optional

import jwt
from jose.exceptions import JWTError

from src.config import settings
from src.models import User

logger = logging.getLogger(__name__)


def create_unified_jwt(
    user: User,
    lifetime_seconds: Optional[int] = None,
    secret: Optional[str] = None,
    algorithm: str = "HS256",
    key_id: Optional[str] = None,
) -> str:
    """
    Create a unified JWT token that works for both FastAPI Users and PostgREST.

    Args:
        user: User to create token for
        lifetime_seconds: Token lifetime in seconds
        secret: JWT secret key
        algorithm: JWT algorithm
        key_id: Optional key identifier for tracking specific tokens

    Returns:
        Encoded JWT token
    """
    if lifetime_seconds is None:
        lifetime_seconds = settings.dev_jwt_lifetime_seconds

    if secret is None:
        secret = settings.dev_jwt_secret

    now = datetime.now(UTC)
    exp = now + timedelta(seconds=lifetime_seconds)

    sub = str(user.id)

    # Create unified claims for both FastAPI Users and PostgREST
    claims = {
        # Standard JWT claims
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        # FastAPI Users claims
        "email": user.email,
        "email_verified": user.is_verified,
        # PostgREST claims
        "role": settings.postgrest_authenticated_role,
        # Auth0 compatibility claims
        "https://samboyd.dev/role": settings.postgrest_authenticated_role,
        "https://samboyd.dev/type": "accessToken",
        "type": "accessToken",
        "scope": "openid profile email offline_access",
    }

    # Add key_id if provided (for tracking specific tokens)
    if key_id is not None:
        claims["key_id"] = key_id

    return jwt.encode(claims, secret, algorithm=algorithm)


def validate_jwt(
    token: str,
    secret: Optional[str] = None,
    algorithm: str = "HS256",
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
) -> Dict:
    """
    Validate and decode a JWT token.

    Args:
        token: JWT token to validate
        secret: Secret key for validation
        algorithm: JWT algorithm
        audience: Expected audience
        issuer: Expected issuer

    Returns:
        Decoded claims dictionary

    Raises:
        JWTError: If token is invalid
    """
    if secret is None:
        if hasattr(settings, "dev_jwt_secret"):
            secret = settings.dev_jwt_secret
        else:
            secret = "dev-secret-key"

    options = {}
    if audience is None:
        options["verify_aud"] = False
    if issuer is None:
        options["verify_iss"] = False

    try:
        return jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            audience=audience,
            issuer=issuer,
            options=options,
        )
    except jwt.InvalidTokenError as e:
        raise JWTError(f"Invalid token: {e}")


def extract_user_id_from_jwt(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token without validation.

    Args:
        token: JWT token

    Returns:
        User ID from sub claim, or None if not found
    """
    try:
        # Decode without verification to get claims
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("sub")
    except Exception:
        return None


def create_refresh_token(user: User, secret: Optional[str] = None) -> str:
    """
    Create a refresh token for the user.

    Args:
        user: User to create refresh token for
        secret: Secret key for signing

    Returns:
        Encoded refresh token
    """
    if secret is None:
        if hasattr(settings, "dev_jwt_secret"):
            secret = settings.dev_jwt_secret
        else:
            secret = "dev-secret-key"

    now = datetime.now(UTC)
    exp = now + timedelta(days=30)  # Refresh tokens last 30 days

    claims = {
        "sub": str(user.id),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "refresh_token",
    }

    return jwt.encode(claims, secret, algorithm="HS256")


def validate_refresh_token(token: str, secret: Optional[str] = None) -> Optional[str]:
    """
    Validate refresh token and return user ID.

    Args:
        token: Refresh token to validate
        secret: Secret key for validation

    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        claims = validate_jwt(token, secret=secret)
        if claims.get("type") != "refresh_token":
            return None
        return claims.get("sub")
    except JWTError:
        return None
