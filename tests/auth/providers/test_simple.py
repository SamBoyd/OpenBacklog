"""
Unit tests for simple authentication provider.
"""

from unittest.mock import AsyncMock, Mock, patch

import bcrypt
import pytest

from src.auth.providers.base import TokenPair, TokenValidation, UserInfo
from src.auth.providers.simple import SimpleAuthProvider
from src.models import OAuthAccount, User


class TestSimpleAuthProvider:
    """Test SimpleAuthProvider implementation."""

    @pytest.fixture
    def provider(self):
        """Create SimpleAuthProvider instance."""
        return SimpleAuthProvider()

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, provider):
        """Test authorization URL generation for simple auth."""
        url = await provider.get_authorization_url(
            redirect_uri="http://localhost/callback", state="test_state"
        )

        assert url == "/auth/login"

    @pytest.mark.asyncio
    async def test_handle_callback_not_implemented(self, provider):
        """Test handle_callback raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Simple auth doesn't use OAuth callbacks"
        ):
            await provider.handle_callback("code", "redirect_uri")

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, provider):
        """Test successful user authentication."""
        user = Mock(spec=User)
        user.email = "test@example.com"
        user.hashed_password = "hashed_password"

        with (
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch.object(provider, "_verify_password") as mock_verify,
        ):

            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            mock_verify.return_value = True

            result = await provider.authenticate_user("test@example.com", "password")

            assert result == user
            mock_verify.assert_called_once_with("password", "hashed_password")

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, provider):
        """Test authentication with user not found."""
        with patch("src.auth.providers.simple.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            result = await provider.authenticate_user(
                "nonexistent@example.com", "password"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_no_password(self, provider):
        """Test authentication with user that has no password."""
        user = Mock(spec=User)
        user.email = "test@example.com"
        user.hashed_password = None

        with patch("src.auth.providers.simple.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            result = await provider.authenticate_user("test@example.com", "password")

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, provider):
        """Test authentication with wrong password."""
        user = Mock(spec=User)
        user.email = "test@example.com"
        user.hashed_password = "hashed_password"

        with (
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch.object(provider, "_verify_password") as mock_verify,
        ):

            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = user
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            mock_verify.return_value = False

            result = await provider.authenticate_user(
                "test@example.com", "wrong_password"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_error(self, provider):
        """Test authentication with database error."""
        with (
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch("src.auth.providers.simple.logger") as mock_logger,
        ):

            mock_get_db.side_effect = Exception("Database error")

            result = await provider.authenticate_user("test@example.com", "password")

            assert result is None
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tokens(self, provider):
        """Test token creation for user."""
        user = Mock(spec=User)
        user.id = "user_123"

        with (
            patch("src.auth.providers.simple.create_unified_jwt") as mock_create_jwt,
            patch(
                "src.auth.providers.simple.create_refresh_token"
            ) as mock_create_refresh,
            patch.object(provider, "_store_access_token") as mock_store,
        ):

            mock_create_jwt.return_value = "access_123"
            mock_create_refresh.return_value = "refresh_456"

            tokens = await provider.create_tokens(user)

            assert tokens.access_token == "access_123"
            assert tokens.refresh_token == "refresh_456"
            assert tokens.expires_in == 3600
            assert tokens.token_type == "Bearer"

            mock_create_jwt.assert_called_once_with(user=user)
            mock_create_refresh.assert_called_once_with(user)
            mock_store.assert_called_once_with("user_123", "access_123")

    @pytest.mark.asyncio
    async def test_validate_token_not_in_db(self, provider):
        """Test token validation when token not in database."""
        with patch.object(provider, "_token_exists_in_db") as mock_exists:
            mock_exists.return_value = False

            validation = await provider.validate_token("token_123")

            assert validation.valid is False
            assert validation.error == "Token not found or revoked"

    @pytest.mark.asyncio
    async def test_validate_token_success(self, provider):
        """Test successful token validation."""
        claims = {"sub": "user_123", "email": "test@example.com"}

        with (
            patch.object(provider, "_token_exists_in_db") as mock_exists,
            patch("src.auth.providers.simple.validate_jwt") as mock_validate,
        ):

            mock_exists.return_value = True
            mock_validate.return_value = claims

            validation = await provider.validate_token("token_123")

            assert validation.valid is True
            assert validation.user_id == "user_123"
            assert validation.claims == claims

    @pytest.mark.asyncio
    async def test_validate_token_error(self, provider):
        """Test token validation with error."""
        with (
            patch.object(provider, "_token_exists_in_db") as mock_exists,
            patch("src.auth.providers.simple.validate_jwt") as mock_validate,
        ):

            mock_exists.return_value = True
            mock_validate.side_effect = Exception("Invalid token")

            validation = await provider.validate_token("token_123")

            assert validation.valid is False
            assert validation.error == "Invalid token"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, provider):
        """Test successful token refresh."""
        user = Mock(spec=User)
        user.id = "user_123"

        new_tokens = TokenPair(
            access_token="new_access_123", refresh_token="new_refresh_456"
        )

        with (
            patch(
                "src.auth.providers.simple.validate_refresh_token"
            ) as mock_validate_refresh,
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch.object(provider, "create_tokens") as mock_create_tokens,
        ):

            mock_validate_refresh.return_value = "user_123"

            mock_db = AsyncMock()
            mock_db.get.return_value = user

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            mock_create_tokens.return_value = new_tokens

            result = await provider.refresh_token("refresh_123")

            assert result == new_tokens
            mock_validate_refresh.assert_called_once_with("refresh_123")
            mock_create_tokens.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, provider):
        """Test token refresh with invalid refresh token."""
        with patch(
            "src.auth.providers.simple.validate_refresh_token"
        ) as mock_validate_refresh:
            mock_validate_refresh.return_value = None

            with pytest.raises(ValueError, match="Invalid refresh token"):
                await provider.refresh_token("invalid_refresh")

    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(self, provider):
        """Test token refresh when user not found."""
        with (
            patch(
                "src.auth.providers.simple.validate_refresh_token"
            ) as mock_validate_refresh,
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
        ):

            mock_validate_refresh.return_value = "user_123"

            mock_db = AsyncMock()
            mock_db.get.return_value = None

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            with pytest.raises(ValueError, match="User not found"):
                await provider.refresh_token("refresh_123")

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, provider):
        """Test getting user info from valid token."""
        claims = {
            "email": "test@example.com",
            "sub": "user_123",
            "name": "Test User",
            "email_verified": True,
        }

        with patch.object(provider, "validate_token") as mock_validate:
            mock_validate.return_value = TokenValidation(valid=True, claims=claims)

            user_info = await provider.get_user_info("token_123")

            assert user_info.email == "test@example.com"
            assert user_info.sub == "user_123"
            assert user_info.name == "Test User"
            assert user_info.email_verified is True

    @pytest.mark.asyncio
    async def test_get_user_info_invalid_token(self, provider):
        """Test getting user info from invalid token."""
        with patch.object(provider, "validate_token") as mock_validate:
            mock_validate.return_value = TokenValidation(valid=False)

            user_info = await provider.get_user_info("invalid_token")
            assert user_info is None

    @pytest.mark.asyncio
    async def test_get_user_info_no_claims(self, provider):
        """Test getting user info when validation has no claims."""
        with patch.object(provider, "validate_token") as mock_validate:
            mock_validate.return_value = TokenValidation(valid=True, claims=None)

            user_info = await provider.get_user_info("token_123")
            assert user_info is None

    def test_hash_password(self, provider):
        """Test password hashing."""
        password = "test_password"
        hashed = provider.hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_success(self, provider):
        """Test successful password verification."""
        password = "test_password"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

        result = provider._verify_password(password, hashed)
        assert result is True

    def test_verify_password_failure(self, provider):
        """Test failed password verification."""
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

        result = provider._verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_password_error(self, provider):
        """Test password verification with error."""
        result = provider._verify_password("password", "invalid_hash")
        assert result is False

    @pytest.mark.asyncio
    async def test_register_user_success(self, provider):
        """Test successful user registration."""
        with (
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch.object(provider, "hash_password") as mock_hash,
        ):

            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None  # No existing user
            mock_db.execute.return_value = mock_result
            mock_db.add = Mock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            mock_hash.return_value = "hashed_password"

            user = await provider.register_user(
                "test@example.com", "password", "Test User"
            )

            assert user is not None
            assert user.email == "test@example.com"
            assert user.hashed_password == "hashed_password"
            assert user.is_active is True
            assert user.is_verified is True

            mock_hash.assert_called_once_with("password")
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
            mock_db.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_register_user_already_exists(self, provider):
        """Test user registration when user already exists."""
        existing_user = Mock(spec=User)
        existing_user.email = "test@example.com"

        with (
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch("src.auth.providers.simple.logger") as mock_logger,
        ):

            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = existing_user
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            user = await provider.register_user("test@example.com", "password")

            assert user is None
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_error(self, provider):
        """Test user registration with database error."""
        with (
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch("src.auth.providers.simple.logger") as mock_logger,
        ):

            mock_get_db.side_effect = Exception("Database error")

            user = await provider.register_user("test@example.com", "password")

            assert user is None
            mock_logger.exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_success(self, provider):
        """Test successful password change."""
        user = Mock(spec=User)
        user.hashed_password = "old_hashed_password"

        with (
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch.object(provider, "_verify_password") as mock_verify,
            patch.object(provider, "hash_password") as mock_hash,
        ):

            mock_db = AsyncMock()

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"

            result = await provider.change_password(
                user, "old_password", "new_password"
            )

            assert result is True
            assert user.hashed_password == "new_hashed_password"
            mock_verify.assert_called_once_with("old_password", "old_hashed_password")
            mock_hash.assert_called_once_with("new_password")
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, provider):
        """Test password change with wrong old password."""
        user = Mock(spec=User)
        user.hashed_password = "old_hashed_password"

        with patch.object(provider, "_verify_password") as mock_verify:
            mock_verify.return_value = False

            result = await provider.change_password(
                user, "wrong_old_password", "new_password"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_change_password_no_existing_password(self, provider):
        """Test password change when user has no existing password."""
        user = Mock(spec=User)
        user.hashed_password = None

        result = await provider.change_password(user, "old_password", "new_password")

        assert result is False

    @pytest.mark.asyncio
    async def test_change_password_error(self, provider):
        """Test password change with error."""
        user = Mock(spec=User)
        user.hashed_password = "old_hashed_password"

        with (
            patch("src.auth.providers.simple.get_async_db") as mock_get_db,
            patch.object(provider, "_verify_password") as mock_verify,
            patch("src.auth.providers.simple.logger") as mock_logger,
        ):

            mock_verify.return_value = True
            mock_get_db.side_effect = Exception("Database error")

            result = await provider.change_password(
                user, "old_password", "new_password"
            )

            assert result is False
            mock_logger.error.assert_called_once()
