"""
Unit tests for development authentication provider.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.auth.providers.base import AuthResult, TokenPair, TokenValidation, UserInfo
from src.auth.providers.dev import DevAuthProvider
from src.models import OAuthAccount, User


class TestDevAuthProvider:
    """Test DevAuthProvider implementation."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for dev auth."""
        with patch("src.auth.providers.dev.settings") as mock_settings:
            mock_settings.dev_user_email = "dev@example.com"
            mock_settings.dev_user_password = "dev_password"
            mock_settings.dev_jwt_oauth_account_name = "dev_oauth"
            mock_settings.dev_jwt_lifetime_seconds = 3600
            mock_settings.dev_jwt_secret = "dev_secret"
            mock_settings.dev_jwt_algorithm = "HS256"
            yield mock_settings

    @pytest.fixture
    def provider(self, mock_settings):
        """Create DevAuthProvider instance."""
        return DevAuthProvider()

    def test_init(self, provider, mock_settings):
        """Test provider initialization."""
        assert provider.dev_email == "dev@example.com"
        assert provider.dev_password == "dev_password"
        assert provider.oauth_account_name == "dev_oauth"

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, provider):
        """Test authorization URL generation for dev auth."""
        url = await provider.get_authorization_url(
            redirect_uri="http://localhost/callback", state="test_state"
        )

        assert "/auth/dev-login" in url
        assert "redirect_uri=/workspace" in url
        assert "state=test_state" in url

    @pytest.mark.asyncio
    async def test_get_authorization_url_no_state(self, provider):
        """Test authorization URL generation without state."""
        url = await provider.get_authorization_url(
            redirect_uri="http://localhost/callback"
        )

        assert "/auth/dev-login" in url
        assert "state=" not in url

    @pytest.mark.asyncio
    async def test_handle_callback_not_implemented(self, provider):
        """Test handle_callback raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Dev auth doesn't use OAuth callbacks"
        ):
            await provider.handle_callback("code", "redirect_uri")

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, provider):
        """Test successful user authentication with dev password."""
        mock_user = Mock(spec=User)

        with patch.object(provider, "_get_or_create_dev_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            result = await provider.authenticate_user(
                "test@example.com", "dev_password"
            )

            assert result == mock_user
            mock_get_user.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, provider):
        """Test authentication failure with wrong password."""
        result = await provider.authenticate_user("test@example.com", "wrong_password")
        assert result is None

    @pytest.mark.asyncio
    async def test_auto_login_dev_user(self, provider):
        """Test auto-login functionality."""
        mock_user = Mock(spec=User)

        with patch.object(provider, "_get_or_create_dev_user") as mock_get_user:
            mock_get_user.return_value = mock_user

            result = await provider.auto_login_dev_user()

            assert result == mock_user
            mock_get_user.assert_called_once_with("dev@example.com")

    @pytest.mark.asyncio
    async def test_create_tokens(self, provider):
        """Test token creation for dev user."""
        user = Mock(spec=User)
        user.id = "user_123"

        with (
            patch("src.auth.providers.dev.create_unified_jwt") as mock_create_jwt,
            patch("src.auth.providers.dev.create_refresh_token") as mock_create_refresh,
            patch.object(provider, "_store_access_token") as mock_store,
        ):

            mock_create_jwt.return_value = "dev_jwt_123"
            mock_create_refresh.return_value = "refresh_123"

            tokens = await provider.create_tokens(user)

            assert tokens.access_token == "dev_jwt_123"
            assert tokens.refresh_token == "refresh_123"
            assert tokens.expires_in == 3600
            assert tokens.token_type == "Bearer"

            mock_create_jwt.assert_called_once_with(
                user=user, lifetime_seconds=3600, secret="dev_secret", algorithm="HS256"
            )
            mock_create_refresh.assert_called_once_with(user, secret="dev_secret")
            mock_store.assert_called_once_with("user_123", "dev_jwt_123")

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
        claims = {
            "sub": "user_123",
            "email": "dev@example.com",
            "exp": datetime.now().timestamp() + 3600,
        }

        with (
            patch.object(provider, "_token_exists_in_db") as mock_exists,
            patch("src.auth.providers.dev.validate_jwt") as mock_validate,
        ):

            mock_exists.return_value = True
            mock_validate.return_value = claims

            validation = await provider.validate_token("token_123")

            assert validation.valid is True
            assert validation.user_id == "user_123"
            assert validation.claims == claims

            mock_validate.assert_called_once_with(
                "token_123", secret="dev_secret", algorithm="HS256"
            )

    @pytest.mark.asyncio
    async def test_validate_token_error(self, provider):
        """Test token validation with error."""
        with (
            patch.object(provider, "_token_exists_in_db") as mock_exists,
            patch("src.auth.providers.dev.validate_jwt") as mock_validate,
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
            patch("src.auth.jwt_utils.validate_refresh_token") as mock_validate_refresh,
            patch("src.auth.providers.dev.get_async_db") as mock_get_db,
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
            mock_validate_refresh.assert_called_once_with(
                "refresh_123", secret="dev_secret"
            )
            mock_create_tokens.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, provider):
        """Test token refresh with invalid refresh token."""
        with patch(
            "src.auth.jwt_utils.validate_refresh_token"
        ) as mock_validate_refresh:
            mock_validate_refresh.return_value = None

            with pytest.raises(ValueError, match="Invalid refresh token"):
                await provider.refresh_token("invalid_refresh")

    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(self, provider):
        """Test token refresh when user not found."""
        with (
            patch("src.auth.jwt_utils.validate_refresh_token") as mock_validate_refresh,
            patch("src.auth.providers.dev.get_async_db") as mock_get_db,
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
        claims = {"email": "dev@example.com", "sub": "user_123", "name": "Dev User"}

        with patch.object(provider, "validate_token") as mock_validate:
            mock_validate.return_value = TokenValidation(valid=True, claims=claims)

            user_info = await provider.get_user_info("token_123")

            assert user_info.email == "dev@example.com"
            assert user_info.sub == "user_123"
            assert user_info.name == "Dev User"
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

    @pytest.mark.asyncio
    async def test_get_or_create_dev_user_existing(self, provider):
        """Test getting existing dev user."""
        existing_user = Mock(spec=User)
        existing_user.email = "dev@example.com"

        with patch("src.auth.providers.dev.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = existing_user
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            user = await provider._get_or_create_dev_user("dev@example.com")

            assert user == existing_user

    @pytest.mark.asyncio
    async def test_get_or_create_dev_user_new(self, provider):
        """Test creating new dev user."""
        with patch("src.auth.providers.dev.get_async_db") as mock_get_db:
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

            # Create a real test without full mocking since the function needs to create actual objects
            user = await provider._get_or_create_dev_user("test@example.com")

            assert user is not None
            assert user.email == "test@example.com"
            assert user.name == "Dev User"
            assert user.is_active is True
            assert user.is_verified is True
            assert user.hashed_password == ""

            # Verify database operations were called
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
            mock_db.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_get_or_create_oauth_account_existing(self, provider):
        """Test getting existing OAuth account."""
        user = Mock(spec=User)
        user.id = "user_123"

        existing_account = Mock(spec=OAuthAccount)
        existing_account.account_id = "dev-existing@example.com"

        with patch("src.auth.providers.dev.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = existing_account
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            account_id = await provider._get_or_create_oauth_account(user)

            assert account_id == "dev-existing@example.com"

    @pytest.mark.asyncio
    async def test_get_or_create_oauth_account_new(self, provider):
        """Test creating new OAuth account."""
        # Create a real-looking user object that can be serialized
        user = Mock()
        user.id = "user_123"
        user.email = "dev@example.com"
        user.is_verified = True
        user.is_active = True
        user.is_superuser = False

        with (
            patch("src.auth.providers.dev.get_async_db") as mock_get_db,
            patch("src.auth.jwt_utils.create_unified_jwt") as mock_create_jwt,
        ):

            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None  # No existing account
            mock_db.execute.return_value = mock_result
            mock_db.add = Mock()
            mock_db.commit = AsyncMock()

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            mock_create_jwt.return_value = "temp_jwt_123"

            account_id = await provider._get_or_create_oauth_account(user)

            assert account_id == "dev-dev@example.com"
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_test_user_new(self, provider):
        """Test creating new test user."""
        with (
            patch("src.auth.providers.dev.get_async_db") as mock_get_db,
            patch.object(provider, "_get_or_create_oauth_account") as mock_oauth,
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

            mock_oauth.return_value = "oauth_account_id"

            user = await provider.create_test_user(
                email="test@example.com", name="Test User"
            )

            assert user is not None
            assert user.email == "test@example.com"
            assert user.name == "Test User"
            mock_oauth.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_create_test_user_existing(self, provider):
        """Test creating test user when user already exists."""
        existing_user = Mock(spec=User)
        existing_user.email = "test@example.com"

        with patch("src.auth.providers.dev.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = existing_user
            mock_db.execute.return_value = mock_result

            # Mock async generator
            async def mock_db_generator():
                yield mock_db

            mock_get_db.return_value = mock_db_generator()

            user = await provider.create_test_user("test@example.com")

            assert user == existing_user
