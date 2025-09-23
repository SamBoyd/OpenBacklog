"""
Unit tests for base authentication provider.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from src.auth.providers.base import (
    AuthProvider,
    AuthResult,
    TokenPair,
    TokenValidation,
    UserInfo,
)
from src.models import AccessToken, User


class TestAuthProvider:
    """Test the abstract AuthProvider base class."""

    def test_user_info_dataclass(self):
        """Test UserInfo dataclass creation."""
        user_info = UserInfo(
            email="test@example.com",
            sub="123456",
            name="Test User",
            picture="https://example.com/pic.jpg",
            email_verified=True,
        )

        assert user_info.email == "test@example.com"
        assert user_info.sub == "123456"
        assert user_info.name == "Test User"
        assert user_info.picture == "https://example.com/pic.jpg"
        assert user_info.email_verified is True

    def test_user_info_defaults(self):
        """Test UserInfo default values."""
        user_info = UserInfo(email="test@example.com", sub="123456")

        assert user_info.name is None
        assert user_info.picture is None
        assert user_info.email_verified is True

    def test_token_pair_dataclass(self):
        """Test TokenPair dataclass creation."""
        tokens = TokenPair(
            access_token="access_123",
            refresh_token="refresh_456",
            expires_in=3600,
            token_type="Bearer",
        )

        assert tokens.access_token == "access_123"
        assert tokens.refresh_token == "refresh_456"
        assert tokens.expires_in == 3600
        assert tokens.token_type == "Bearer"

    def test_token_pair_defaults(self):
        """Test TokenPair default values."""
        tokens = TokenPair(access_token="access_123")

        assert tokens.refresh_token is None
        assert tokens.expires_in is None
        assert tokens.token_type == "Bearer"

    def test_token_validation_dataclass(self):
        """Test TokenValidation dataclass creation."""
        validation = TokenValidation(
            valid=True,
            user_id="user_123",
            claims={"sub": "user_123", "email": "test@example.com"},
            error=None,
        )

        assert validation.valid is True
        assert validation.user_id == "user_123"
        assert validation.claims == {"sub": "user_123", "email": "test@example.com"}
        assert validation.error is None

    def test_token_validation_invalid(self):
        """Test TokenValidation for invalid token."""
        validation = TokenValidation(valid=False, error="Token expired")

        assert validation.valid is False
        assert validation.user_id is None
        assert validation.claims is None
        assert validation.error == "Token expired"

    def test_auth_result_dataclass(self):
        """Test AuthResult dataclass creation."""
        user_info = UserInfo(email="test@example.com", sub="123456")
        tokens = TokenPair(access_token="access_123")
        user = Mock(spec=User)

        result = AuthResult(user_info=user_info, tokens=tokens, user=user)

        assert result.user_info == user_info
        assert result.tokens == tokens
        assert result.user == user


class ConcreteAuthProvider(AuthProvider):
    """Concrete implementation for testing abstract methods."""

    async def get_authorization_url(self, redirect_uri: str, state=None, **kwargs):
        return f"https://auth.example.com/authorize?redirect_uri={redirect_uri}"

    async def handle_callback(self, code: str, redirect_uri: str, state=None, **kwargs):
        user_info = UserInfo(email="test@example.com", sub="123456")
        tokens = TokenPair(access_token="access_123")
        return AuthResult(user_info=user_info, tokens=tokens)

    async def create_tokens(self, user: User):
        return TokenPair(access_token="access_123", refresh_token="refresh_456")

    async def validate_token(self, token: str):
        if token == "valid_token":
            return TokenValidation(
                valid=True, user_id="user_123", claims={"sub": "user_123"}
            )
        return TokenValidation(valid=False, error="Invalid token")

    async def refresh_token(self, refresh_token: str):
        return TokenPair(access_token="new_access_123", refresh_token="new_refresh_456")


class TestConcreteAuthProvider:
    """Test concrete implementation methods."""

    @pytest.fixture
    def provider(self):
        """Create a concrete provider instance."""
        return ConcreteAuthProvider()

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, provider):
        """Test get_authorization_url implementation."""
        url = await provider.get_authorization_url("http://localhost/callback")
        assert "https://auth.example.com/authorize" in url
        assert "redirect_uri=http://localhost/callback" in url

    @pytest.mark.asyncio
    async def test_handle_callback(self, provider):
        """Test handle_callback implementation."""
        result = await provider.handle_callback(
            "auth_code", "http://localhost/callback"
        )

        assert isinstance(result, AuthResult)
        assert result.user_info.email == "test@example.com"
        assert result.tokens.access_token == "access_123"

    @pytest.mark.asyncio
    async def test_create_tokens(self, provider):
        """Test create_tokens implementation."""
        user = Mock(spec=User)
        tokens = await provider.create_tokens(user)

        assert isinstance(tokens, TokenPair)
        assert tokens.access_token == "access_123"
        assert tokens.refresh_token == "refresh_456"

    @pytest.mark.asyncio
    async def test_validate_token_valid(self, provider):
        """Test validate_token with valid token."""
        validation = await provider.validate_token("valid_token")

        assert validation.valid is True
        assert validation.user_id == "user_123"
        assert validation.claims == {"sub": "user_123"}
        assert validation.error is None

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, provider):
        """Test validate_token with invalid token."""
        validation = await provider.validate_token("invalid_token")

        assert validation.valid is False
        assert validation.error == "Invalid token"

    @pytest.mark.asyncio
    async def test_refresh_token(self, provider):
        """Test refresh_token implementation."""
        tokens = await provider.refresh_token("refresh_123")

        assert isinstance(tokens, TokenPair)
        assert tokens.access_token == "new_access_123"
        assert tokens.refresh_token == "new_refresh_456"

    @pytest.mark.asyncio
    async def test_authenticate_user_default(self, provider):
        """Test default authenticate_user returns None."""
        result = await provider.authenticate_user("username", "password")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_info_with_valid_token(self, provider):
        """Test get_user_info with valid token."""
        with patch.object(provider, "validate_token") as mock_validate:
            mock_validate.return_value = TokenValidation(
                valid=True,
                claims={
                    "email": "test@example.com",
                    "sub": "123456",
                    "name": "Test User",
                    "picture": "https://example.com/pic.jpg",
                    "email_verified": True,
                },
            )

            user_info = await provider.get_user_info("valid_token")

            assert user_info is not None
            assert user_info.email == "test@example.com"
            assert user_info.sub == "123456"
            assert user_info.name == "Test User"
            assert user_info.picture == "https://example.com/pic.jpg"
            assert user_info.email_verified is True

    @pytest.mark.asyncio
    async def test_get_user_info_with_invalid_token(self, provider):
        """Test get_user_info with invalid token."""
        with patch.object(provider, "validate_token") as mock_validate:
            mock_validate.return_value = TokenValidation(valid=False)

            user_info = await provider.get_user_info("invalid_token")
            assert user_info is None

    @pytest.mark.asyncio
    async def test_get_user_info_no_claims(self, provider):
        """Test get_user_info when validation has no claims."""
        with patch.object(provider, "validate_token") as mock_validate:
            mock_validate.return_value = TokenValidation(valid=True, claims=None)

            user_info = await provider.get_user_info("valid_token")
            assert user_info is None

    def test_get_provider_name(self, provider):
        """Test provider name extraction."""
        name = provider.get_provider_name()
        assert name == "ConcreteAuth"  # Removes "Provider" suffix

    @pytest.mark.asyncio
    async def test_store_access_token(self, provider):
        """Test storing access token in database."""
        with patch("src.db.get_async_db") as mock_get_db:

            mock_db = AsyncMock()
            mock_db.add = Mock()
            mock_db.commit = AsyncMock()

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            await provider._store_access_token("user_123", "token_abc")

            # Verify database operations were called
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

            # Verify the token created has the right properties
            token_arg = mock_db.add.call_args[0][0]
            assert token_arg.token == "token_abc"
            assert token_arg.user_id == "user_123"

    @pytest.mark.asyncio
    async def test_store_access_token_error(self, provider):
        """Test error handling in store access token."""
        with (
            patch("src.db.get_async_db") as mock_get_db,
            patch("src.auth.providers.base.logging") as mock_logging,
        ):

            mock_get_db.side_effect = Exception("Database error")

            # Should not raise exception
            await provider._store_access_token("user_123", "token_abc")

            # Should log error
            mock_logging.getLogger.return_value.error.assert_called()

    @pytest.mark.asyncio
    async def test_revoke_tokens_for_user(self, provider):
        """Test revoking all tokens for a user."""
        with (
            patch("src.db.get_async_db") as mock_get_db,
            patch("sqlalchemy.delete") as mock_delete,
        ):

            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.rowcount = 3
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            await provider._revoke_tokens_for_user("user_123")

            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_exists_in_db_true(self, provider):
        """Test token exists check when token is found."""
        with patch("src.db.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = Mock(spec=AccessToken)
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            exists = await provider._token_exists_in_db("token_abc")
            assert exists is True

    @pytest.mark.asyncio
    async def test_token_exists_in_db_false(self, provider):
        """Test token exists check when token is not found."""
        with patch("src.db.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            exists = await provider._token_exists_in_db("token_abc")
            assert exists is False

    @pytest.mark.asyncio
    async def test_token_exists_in_db_error(self, provider):
        """Test token exists check with database error."""
        with patch("src.db.get_async_db") as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            exists = await provider._token_exists_in_db("token_abc")
            assert exists is False

    @pytest.mark.asyncio
    async def test_auto_login_dev_user_not_implemented(self, provider):
        """Test auto_login_dev_user raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await provider.auto_login_dev_user()

    @pytest.mark.asyncio
    async def test_register_user_not_implemented(self, provider):
        """Test register_user raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await provider.register_user("test@example.com", "password", "Test User")
