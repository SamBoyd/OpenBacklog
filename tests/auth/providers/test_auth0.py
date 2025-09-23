"""
Unit tests for Auth0 authentication provider.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import jwt
import pytest
from jose.exceptions import JWTError

from src.auth.providers.auth0 import Auth0Provider
from src.auth.providers.base import AuthResult, TokenPair, TokenValidation, UserInfo
from src.models import OAuthAccount, User


class TestAuth0Provider:
    """Test Auth0Provider implementation."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for Auth0."""
        with patch("src.auth.providers.auth0.settings") as mock_settings:
            mock_settings.auth0_client_id = "test_client_id"
            mock_settings.auth0_client_secret = "test_client_secret"
            mock_settings.auth0_domain = "test.auth0.com"
            mock_settings.auth0_audience = "http://localhost:8000"
            mock_settings.app_url = "http://localhost:8000"
            mock_settings.cookie_lifetime_seconds = 3600
            yield mock_settings

    @pytest.fixture
    def provider(self, mock_settings):
        """Create Auth0Provider instance with mocked settings."""
        with patch("src.auth.providers.auth0.httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"keys": []}
            mock_get.return_value = mock_response

            return Auth0Provider()

    def test_init_missing_settings(self):
        """Test initialization fails with missing settings."""
        with patch("src.auth.providers.auth0.settings") as mock_settings:
            mock_settings.auth0_client_id = None
            mock_settings.auth0_client_secret = "secret"
            mock_settings.auth0_domain = "domain"

            with pytest.raises(ValueError, match="Auth0 settings not configured"):
                Auth0Provider()

    def test_init_success(self, mock_settings):
        """Test successful initialization."""
        with patch("src.auth.providers.auth0.httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"keys": []}
            mock_get.return_value = mock_response

            provider = Auth0Provider()

            assert provider.client_id == "test_client_id"
            assert provider.client_secret == "test_client_secret"
            assert provider.domain == "test.auth0.com"
            assert provider.audience == "http://localhost:8000"
            assert provider.issuer == "https://test.auth0.com/"

    def test_fetch_jwks_success(self, mock_settings):
        """Test successful JWKS fetching."""
        jwks_data = {
            "keys": [
                {
                    "kid": "test_kid",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test_n",
                    "e": "AQAB",
                }
            ]
        }

        with patch("src.auth.providers.auth0.httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = jwks_data
            mock_get.return_value = mock_response

            provider = Auth0Provider()
            assert provider._jwks_cache == jwks_data

    def test_fetch_jwks_failure(self, mock_settings):
        """Test JWKS fetching failure."""
        with patch("src.auth.providers.auth0.httpx.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Network error")

            provider = Auth0Provider()
            assert provider._jwks_cache is None

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, provider):
        """Test authorization URL generation."""
        url = await provider.get_authorization_url(
            redirect_uri="http://localhost/callback", state="test_state"
        )

        assert "https://test.auth0.com/authorize" in url
        assert "client_id=test_client_id" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in url  # URL encoded
        assert "state=test_state" in url
        assert "scope=openid+profile+email+offline_access" in url

    @pytest.mark.asyncio
    async def test_get_authorization_url_no_state(self, provider):
        """Test authorization URL generation without state."""
        url = await provider.get_authorization_url(
            redirect_uri="http://localhost/callback"
        )

        assert "state=" not in url

    @pytest.mark.asyncio
    async def test_handle_callback(self, provider):
        """Test OAuth callback handling."""
        oauth_token = {
            "access_token": "access_123",
            "refresh_token": "refresh_456",
            "expires_in": 3600,
            "token_type": "Bearer",
            "id_token": "id_token_123",
        }

        user_info = UserInfo(
            email="test@example.com", sub="auth0|123456", name="Test User"
        )

        with (
            patch.object(provider, "_exchange_code_for_token") as mock_exchange,
            patch.object(provider, "_get_user_info_from_token") as mock_user_info,
        ):

            mock_exchange.return_value = oauth_token
            mock_user_info.return_value = user_info

            result = await provider.handle_callback(
                code="auth_code", redirect_uri="http://localhost/callback"
            )

            assert isinstance(result, AuthResult)
            assert result.user_info == user_info
            assert result.tokens.access_token == "access_123"
            assert result.tokens.refresh_token == "refresh_456"

    @pytest.mark.asyncio
    async def test_create_tokens(self, provider):
        """Test token creation for user."""
        user = Mock(spec=User)
        user.id = "user_123"

        with (
            patch("src.auth.providers.auth0.create_unified_jwt") as mock_create_jwt,
            patch(
                "src.auth.providers.auth0.create_refresh_token"
            ) as mock_create_refresh,
            patch.object(provider, "_store_access_token") as mock_store,
        ):

            mock_create_jwt.return_value = "unified_jwt_123"
            mock_create_refresh.return_value = "refresh_123"

            tokens = await provider.create_tokens(user)

            assert tokens.access_token == "unified_jwt_123"
            assert tokens.refresh_token == "refresh_123"
            assert tokens.expires_in == 3600
            assert tokens.token_type == "Bearer"

            mock_store.assert_called_once_with("user_123", "unified_jwt_123")

    @pytest.mark.asyncio
    async def test_validate_token_not_in_db(self, provider):
        """Test token validation when token not in database."""
        with patch.object(provider, "_token_exists_in_db") as mock_exists:
            mock_exists.return_value = False

            validation = await provider.validate_token("token_123")

            assert validation.valid is False
            assert validation.error == "Token not found or revoked"

    @pytest.mark.asyncio
    async def test_validate_token_auth0_success(self, provider):
        """Test successful Auth0 token validation."""
        claims = {
            "sub": "auth0|123456",
            "email": "test@example.com",
            "exp": datetime.now().timestamp() + 3600,
        }

        with (
            patch.object(provider, "_token_exists_in_db") as mock_exists,
            patch.object(provider, "_validate_auth0_token") as mock_validate,
            patch.object(
                provider, "_resolve_user_id_from_oauth_account"
            ) as mock_resolve,
        ):

            mock_exists.return_value = True
            mock_validate.return_value = claims
            mock_resolve.return_value = "user_123"

            validation = await provider.validate_token("token_123")

            assert validation.valid is True
            assert validation.user_id == "user_123"
            assert validation.claims == claims

    @pytest.mark.asyncio
    async def test_validate_token_auth0_no_user(self, provider):
        """Test Auth0 token validation when user not found."""
        claims = {"sub": "auth0|123456"}

        with (
            patch.object(provider, "_token_exists_in_db") as mock_exists,
            patch.object(provider, "_validate_auth0_token") as mock_validate,
            patch.object(
                provider, "_resolve_user_id_from_oauth_account"
            ) as mock_resolve,
        ):

            mock_exists.return_value = True
            mock_validate.return_value = claims
            mock_resolve.return_value = None

            validation = await provider.validate_token("token_123")

            assert validation.valid is False
            assert "OAuth account not found" in validation.error

    @pytest.mark.asyncio
    async def test_validate_token_unified_jwt(self, provider):
        """Test validation falling back to unified JWT."""
        claims = {"sub": "user_123", "email": "test@example.com"}  # UUID format

        with (
            patch.object(provider, "_token_exists_in_db") as mock_exists,
            patch.object(provider, "_validate_auth0_token") as mock_validate_auth0,
            patch("src.auth.providers.auth0.validate_jwt") as mock_validate_jwt,
            patch("uuid.UUID") as mock_uuid,
        ):

            mock_exists.return_value = True
            mock_validate_auth0.side_effect = Exception("Not Auth0 token")
            mock_validate_jwt.return_value = claims
            mock_uuid.return_value = True  # Valid UUID

            validation = await provider.validate_token("token_123")

            assert validation.valid is True
            assert validation.user_id == "user_123"
            assert validation.claims == claims

    @pytest.mark.asyncio
    async def test_validate_token_jwt_error(self, provider):
        """Test token validation with JWT error."""
        with (
            patch.object(provider, "_token_exists_in_db") as mock_exists,
            patch.object(provider, "_validate_auth0_token") as mock_validate_auth0,
            patch("src.auth.providers.auth0.validate_jwt") as mock_validate_jwt,
        ):

            mock_exists.return_value = True
            mock_validate_auth0.side_effect = Exception("Not Auth0 token")
            mock_validate_jwt.side_effect = JWTError("Invalid token")

            validation = await provider.validate_token("token_123")

            assert validation.valid is False
            assert validation.error == "Invalid token"

    @pytest.mark.asyncio
    async def test_refresh_token(self, provider):
        """Test token refresh."""
        refresh_response = {
            "access_token": "new_access_123",
            "refresh_token": "new_refresh_456",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value=refresh_response)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            tokens = await provider.refresh_token("refresh_123")

            assert tokens.access_token == "new_access_123"
            assert tokens.refresh_token == "new_refresh_456"
            assert tokens.expires_in == 3600

    @pytest.mark.asyncio
    async def test_get_user_info_from_claims(self, provider):
        """Test getting user info from token claims."""
        claims = {
            "email": "test@example.com",
            "sub": "auth0|123456",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
            "email_verified": True,
        }

        with patch.object(provider, "validate_token") as mock_validate:
            mock_validate.return_value = TokenValidation(valid=True, claims=claims)

            user_info = await provider.get_user_info("token_123")

            assert user_info.email == "test@example.com"
            assert user_info.sub == "auth0|123456"
            assert user_info.name == "Test User"
            assert user_info.picture == "https://example.com/pic.jpg"
            assert user_info.email_verified is True

    @pytest.mark.asyncio
    async def test_get_user_info_from_userinfo_endpoint(self, provider):
        """Test getting user info from userinfo endpoint."""
        userinfo_response = {
            "email": "test@example.com",
            "sub": "auth0|123456",
            "name": "Test User",
        }

        with (
            patch.object(provider, "validate_token") as mock_validate,
            patch("httpx.AsyncClient") as mock_client,
        ):

            mock_validate.return_value = TokenValidation(valid=True, claims={})

            mock_client_instance = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value=userinfo_response)
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            user_info = await provider.get_user_info("token_123")

            assert user_info.email == "test@example.com"
            assert user_info.sub == "auth0|123456"
            assert user_info.name == "Test User"

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, provider):
        """Test exchanging authorization code for tokens."""
        token_response = {
            "access_token": "access_123",
            "refresh_token": "refresh_456",
            "expires_in": 3600,
            "token_type": "Bearer",
            "id_token": "id_token_123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value=token_response)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            oauth_token = await provider._exchange_code_for_token(
                "auth_code", "http://localhost/callback"
            )

            assert oauth_token["access_token"] == "access_123"
            assert oauth_token["refresh_token"] == "refresh_456"
            assert oauth_token["id_token"] == "id_token_123"

    @pytest.mark.asyncio
    async def test_get_user_info_from_token_id_token(self, provider):
        """Test extracting user info from ID token."""
        # Create a mock OAuth2Token that behaves like both dict and object
        oauth_token = Mock()
        oauth_token.__getitem__ = Mock(
            side_effect=lambda key: {
                "access_token": "access_123",
                "id_token": "id_token_123",
            }[key]
        )
        oauth_token.__contains__ = Mock(return_value=True)
        oauth_token.id_token = "id_token_123"

        claims = {
            "email": "test@example.com",
            "sub": "auth0|123456",
            "name": "Test User",
        }

        with patch.object(provider, "_validate_auth0_token") as mock_validate:
            mock_validate.return_value = claims

            user_info = await provider._get_user_info_from_token(oauth_token)

            assert user_info.email == "test@example.com"
            assert user_info.sub == "auth0|123456"
            assert user_info.name == "Test User"

    @pytest.mark.asyncio
    async def test_get_user_info_from_token_userinfo_fallback(self, provider):
        """Test falling back to userinfo endpoint."""
        # Create a mock OAuth2Token that behaves like both dict and object
        oauth_token = Mock()
        oauth_token.__getitem__ = Mock(
            side_effect=lambda key: {
                "access_token": "access_123",
                "id_token": "invalid_id_token",
            }[key]
        )
        oauth_token.__contains__ = Mock(return_value=True)
        oauth_token.id_token = "invalid_id_token"

        userinfo_response = {"email": "test@example.com", "sub": "auth0|123456"}

        with (
            patch.object(provider, "_validate_auth0_token") as mock_validate,
            patch("httpx.AsyncClient") as mock_client,
        ):

            mock_validate.side_effect = Exception("Invalid ID token")

            mock_client_instance = AsyncMock()
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value=userinfo_response)
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            user_info = await provider._get_user_info_from_token(oauth_token)

            assert user_info.email == "test@example.com"
            assert user_info.sub == "auth0|123456"

    @pytest.mark.asyncio
    async def test_validate_auth0_token_success(self, provider):
        """Test successful Auth0 token validation."""
        provider._jwks_cache = {
            "keys": [
                {
                    "kid": "test_kid",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test_n",
                    "e": "AQAB",
                }
            ]
        }

        claims = {"sub": "auth0|123456", "email": "test@example.com"}

        with (
            patch("jwt.get_unverified_header") as mock_header,
            patch("src.auth.providers.auth0.jose_jwt.decode") as mock_decode,
        ):

            mock_header.return_value = {"kid": "test_kid"}
            mock_decode.return_value = claims

            result = await provider._validate_auth0_token("token_123")

            assert result == claims

    @pytest.mark.asyncio
    async def test_validate_auth0_token_no_kid(self, provider):
        """Test Auth0 token validation with no key ID."""
        with patch("jwt.get_unverified_header") as mock_header:
            mock_header.return_value = {}

            result = await provider._validate_auth0_token("token_123")
            assert result is None

    @pytest.mark.asyncio
    async def test_validate_auth0_token_key_not_found(self, provider):
        """Test Auth0 token validation with key not found."""
        provider._jwks_cache = {"keys": []}

        with patch("jwt.get_unverified_header") as mock_header:
            mock_header.return_value = {"kid": "unknown_kid"}

            result = await provider._validate_auth0_token("token_123")
            assert result is None

    @pytest.mark.asyncio
    async def test_validate_auth0_token_jwt_error(self, provider):
        """Test Auth0 token validation with JWT error."""
        provider._jwks_cache = {
            "keys": [
                {
                    "kid": "test_kid",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test_n",
                    "e": "AQAB",
                }
            ]
        }

        with (
            patch("jwt.get_unverified_header") as mock_header,
            patch("src.auth.providers.auth0.jose_jwt.decode") as mock_decode,
        ):

            mock_header.return_value = {"kid": "test_kid"}
            mock_decode.side_effect = JWTError("Invalid token")

            result = await provider._validate_auth0_token("token_123")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_jwt_rsa_key_found(self, provider):
        """Test getting RSA key from JWKS."""
        provider._jwks_cache = {
            "keys": [
                {
                    "kid": "test_kid",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test_n",
                    "e": "AQAB",
                }
            ]
        }

        key = await provider._get_jwt_rsa_key("test_kid")

        assert key["kid"] == "test_kid"
        assert key["kty"] == "RSA"
        assert key["n"] == "test_n"

    @pytest.mark.asyncio
    async def test_get_jwt_rsa_key_not_found(self, provider):
        """Test getting RSA key when not found."""
        provider._jwks_cache = {"keys": []}

        key = await provider._get_jwt_rsa_key("unknown_kid")
        assert key is None

    @pytest.mark.asyncio
    async def test_resolve_user_id_from_oauth_account(self, provider):
        """Test resolving user ID from OAuth account."""
        with patch("src.db.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_oauth_account = Mock(spec=OAuthAccount)
            mock_oauth_account.user_id = "user_123"
            mock_result.scalar_one_or_none.return_value = mock_oauth_account
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            user_id = await provider._resolve_user_id_from_oauth_account("auth0|123456")

            assert user_id == "user_123"

    @pytest.mark.asyncio
    async def test_resolve_user_id_from_oauth_account_not_found(self, provider):
        """Test resolving user ID when OAuth account not found."""
        with patch("src.db.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            user_id = await provider._resolve_user_id_from_oauth_account("auth0|123456")

            assert user_id is None
