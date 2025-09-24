"""
Auth0 authentication provider implementation.
"""

import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import HTTPException
from httpx_oauth.oauth2 import OAuth2, OAuth2Token
from jose import jwt as jose_jwt
from jose.exceptions import JWTError

from src.config import settings
from src.models import User

from ..jwt_utils import create_refresh_token, create_unified_jwt, validate_jwt
from .base import AuthProvider, AuthResult, TokenPair, TokenValidation, UserInfo

logger = logging.getLogger(__name__)


class Auth0Provider(AuthProvider):
    """Auth0 OAuth2 authentication provider."""

    def __init__(self):
        """Initialize Auth0 provider with settings."""
        if not all(
            [
                settings.auth0_client_id,
                settings.auth0_client_secret,
                settings.auth0_domain,
            ]
        ):
            raise ValueError("Auth0 settings not configured")

        self.client_id = settings.auth0_client_id
        self.client_secret = settings.auth0_client_secret
        self.domain = settings.auth0_domain
        self.audience = getattr(settings, "auth0_audience", f"{settings.app_url}")

        # Auth0 endpoints
        self.issuer = f"https://{self.domain}/"
        self.authorize_endpoint = f"{self.issuer}authorize"
        self.token_endpoint = f"{self.issuer}oauth/token"
        self.userinfo_endpoint = f"{self.issuer}userinfo"
        self.jwks_url = f"{self.issuer}.well-known/jwks.json"

        # OAuth scopes
        self.scope = "openid profile email offline_access"

        # Cache JWKS keys
        self._jwks_cache = None
        self._fetch_jwks()

    def _fetch_jwks(self):
        """Fetch and cache JWKS keys."""
        try:
            response = httpx.get(self.jwks_url)
            response.raise_for_status()
            self._jwks_cache = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            self._jwks_cache = None

    async def get_authorization_url(
        self, redirect_uri: str, state: Optional[str] = None, **kwargs
    ) -> str:
        """Generate Auth0 authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.scope,
            "audience": self.audience,
        }

        if state:
            params["state"] = state

        # Add any extra parameters
        params.update(kwargs)

        return f"{self.authorize_endpoint}?{urlencode(params)}"

    async def handle_callback(
        self, code: str, redirect_uri: str, state: Optional[str] = None, **kwargs
    ) -> AuthResult:
        """Handle Auth0 OAuth callback."""
        # Exchange code for tokens
        oauth_token: OAuth2Token = await self._exchange_code_for_token(
            code, redirect_uri
        )

        # Get user info from ID token or userinfo endpoint
        user_info = await self._get_user_info_from_token(oauth_token)

        # Create our unified tokens
        tokens = TokenPair(
            access_token=oauth_token["access_token"],
            refresh_token=oauth_token["refresh_token"],
            expires_in=oauth_token["expires_in"],
            token_type=oauth_token["token_type"],
        )

        return AuthResult(user_info=user_info, tokens=tokens)

    async def create_tokens(self, user: User) -> TokenPair:
        """Create unified tokens for a user."""
        # Always use user UUID as sub to avoid issues with multiple OAuth accounts
        access_token = create_unified_jwt(
            user=user,
            lifetime_seconds=getattr(
                settings, "cookie_lifetime_seconds", 3600 * 24 * 30
            ),
        )

        refresh_token = create_refresh_token(user)

        # Store access token in database
        await self._store_access_token(str(user.id), access_token)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=getattr(settings, "cookie_lifetime_seconds", 3600 * 24 * 30),
            token_type="Bearer",  # nosec
        )

    async def validate_token(self, token: str) -> TokenValidation:
        """Validate Auth0 JWT token."""
        # First check if token exists in database (not revoked)
        if not await self._token_exists_in_db(token):
            return TokenValidation(valid=False, error="Token not found or revoked")

        try:
            # First try to validate as Auth0 token
            claims = await self._validate_auth0_token(token)
            if claims:
                oauth_account_id = claims.get("sub")

                # For Auth0 tokens, resolve OAuth account ID to user UUID
                user_id = await self._resolve_user_id_from_oauth_account(
                    oauth_account_id
                )
                if not user_id:
                    # OAuth account not found in our database
                    return TokenValidation(
                        valid=False,
                        error=f"OAuth account not found: {oauth_account_id}",
                    )

                return TokenValidation(valid=True, user_id=user_id, claims=claims)
        except Exception as e:
            logger.debug(f"Auth0 token validation failed: {e}")

        # Fallback to unified token validation
        try:
            claims = validate_jwt(token)
            sub = claims.get("sub")

            # Check if sub is a UUID (user ID) or OAuth account ID
            try:
                # Try to parse as UUID - if it works, it's a user ID
                import uuid

                uuid.UUID(sub)
                user_id = sub  # Already a user UUID
            except (ValueError, TypeError):
                # Not a UUID, assume it's an OAuth account ID, resolve it
                user_id = await self._resolve_user_id_from_oauth_account(sub)
                if not user_id:
                    return TokenValidation(
                        valid=False, error=f"User not found for account: {sub}"
                    )

            return TokenValidation(valid=True, user_id=user_id, claims=claims)
        except JWTError as e:
            return TokenValidation(valid=False, error=str(e))

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Refresh Auth0 tokens."""
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_endpoint, json=payload)
            response.raise_for_status()
            token_data = response.json()

        return TokenPair(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", refresh_token),
            expires_in=token_data.get("expires_in"),
            token_type=token_data.get("token_type", "Bearer"),
        )

    async def get_user_info(self, token: str) -> Optional[UserInfo]:
        """Get user info from Auth0 token."""
        validation = await self.validate_token(token)
        if not validation.valid:
            return None

        # Try to get from token claims first
        claims = validation.claims
        if claims and "email" in claims:
            return UserInfo(
                email=claims["email"],
                sub=claims["sub"],
                name=claims.get("name"),
                picture=claims.get("picture"),
                email_verified=claims.get("email_verified", True),
            )

        # Fallback to userinfo endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_endpoint, headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    userinfo = response.json()
                    return UserInfo(
                        email=userinfo["email"],
                        sub=userinfo["sub"],
                        name=userinfo.get("name"),
                        picture=userinfo.get("picture"),
                        email_verified=userinfo.get("email_verified", True),
                    )
        except Exception as e:
            logger.error(f"Failed to get userinfo: {e}")

        return None

    async def _exchange_code_for_token(
        self, code: str, redirect_uri: str
    ) -> OAuth2Token:
        """Exchange authorization code for OAuth2 token."""
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "audience": self.audience,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_endpoint, json=payload)
            response.raise_for_status()
            token_data = response.json()

        logger.info(f"Receiving token data from Auth0: {token_data}")

        return OAuth2Token(
            dict(
                access_token=token_data["access_token"],
                expires_in=token_data.get("expires_in"),
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                id_token=token_data.get("id_token"),
                scope=token_data.get("scope"),
            )
        )

    async def _get_user_info_from_token(self, oauth_token: OAuth2Token) -> UserInfo:
        """Extract user info from OAuth token."""
        # Try ID token first
        if hasattr(oauth_token, "id_token") and oauth_token["id_token"]:
            try:
                claims = await self._validate_auth0_token(oauth_token["id_token"])
                if claims and "email" in claims:
                    return UserInfo(
                        email=claims["email"],
                        sub=claims["sub"],
                        name=claims.get("name"),
                        picture=claims.get("picture"),
                        email_verified=claims.get("email_verified", True),
                    )
            except Exception as e:
                logger.debug(f"Failed to parse ID token: {e}")

        # Fallback to userinfo endpoint with access token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {oauth_token['access_token']}"},
            )
            response.raise_for_status()
            userinfo = response.json()

        return UserInfo(
            email=userinfo["email"],
            sub=userinfo["sub"],
            name=userinfo.get("name"),
            picture=userinfo.get("picture"),
            email_verified=userinfo.get("email_verified", True),
        )

    async def _validate_auth0_token(self, token: str) -> Optional[Dict]:
        """Validate Auth0 JWT token using JWKS."""
        try:
            # Get unverified header to find key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            if not kid:
                return None

            # Find matching key in JWKS
            rsa_key = await self._get_jwt_rsa_key(kid)
            if not rsa_key:
                return None

            # Validate token
            return jose_jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
            )
        except JWTError:
            return None

    async def _get_jwt_rsa_key(self, kid: str) -> Optional[Dict]:
        """Get RSA key from JWKS for given key ID."""
        if not self._jwks_cache:
            self._fetch_jwks()

        if not self._jwks_cache:
            return None

        for key in self._jwks_cache.get("keys", []):
            if key.get("kid") == kid:
                return {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }

        return None

    async def _get_oauth_account_id(self, user: User) -> Optional[str]:
        """Get OAuth account ID for user from oauth_account table."""
        from sqlalchemy import select

        from src.db import get_async_db
        from src.models import OAuthAccount

        async for db in get_async_db():
            # Look up OAuth account for this user
            result = await db.execute(
                select(OAuthAccount).filter(
                    OAuthAccount.user_id == user.id, OAuthAccount.oauth_name == "auth0"
                )
            )
            oauth_account = result.scalar_one_or_none()

            if oauth_account:
                return oauth_account.account_id

            # Fallback to user ID if no OAuth account found
            return str(user.id)

    async def _resolve_user_id_from_oauth_account(
        self, oauth_account_id: str
    ) -> Optional[str]:
        """
        Resolve OAuth account ID to user UUID.

        Args:
            oauth_account_id: OAuth account ID (e.g., 'google-oauth2|123456')

        Returns:
            User UUID string if found, None otherwise
        """
        from sqlalchemy import select

        from src.db import get_async_db
        from src.models import OAuthAccount

        async for db in get_async_db():
            result = await db.execute(
                select(OAuthAccount).filter(
                    OAuthAccount.account_id == oauth_account_id,
                    OAuthAccount.oauth_name == "auth0",
                )
            )
            oauth_account = result.scalar_one_or_none()

            if oauth_account:
                return str(oauth_account.user_id)

            return None
