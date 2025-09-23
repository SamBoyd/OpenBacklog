"""
Test suite for AuthModule class.
"""

import uuid
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from hamcrest import (
    assert_that,
    equal_to,
    has_property,
    instance_of,
    is_,
    none,
    not_none,
)
from sqlalchemy.orm import Session

from src.auth.auth_module import AuthModule, get_auth_module, initialize_auth
from src.auth.providers import TokenValidation
from src.models import User


class TestAuthModule:
    """Test cases for AuthModule class."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        return MagicMock(spec=FastAPI)

    @pytest.fixture
    def mock_auth_provider(self):
        """Create a mock auth provider."""
        provider = MagicMock()
        provider.get_provider_name.return_value = "test_provider"
        return provider

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = MagicMock()
        request.cookies = {}
        return request

    @pytest.fixture
    def sample_user(self, session):
        """Create a sample user for testing."""
        return User(
            id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
            is_active=True,
            is_verified=True,
        )

    @pytest.fixture
    def auth_module(self, mock_app, mock_auth_provider) -> AuthModule:
        """Create AuthModule instance with mocked dependencies."""
        with (
            patch(
                "src.auth.auth_module.get_auth_provider",
                return_value=mock_auth_provider,
            ),
            patch("src.auth.auth_module.get_provider_type", return_value="test"),
            patch("src.auth.auth_module.auth_router"),
        ):
            return AuthModule(mock_app)

    def test_auth_module_initialization(self, mock_app, mock_auth_provider):
        """Test AuthModule initialization."""
        with (
            patch(
                "src.auth.auth_module.get_auth_provider",
                return_value=mock_auth_provider,
            ),
            patch("src.auth.auth_module.get_provider_type", return_value="test"),
            patch("src.auth.auth_module.auth_router") as mock_router,
        ):

            auth_module = AuthModule(mock_app)

            assert_that(auth_module.app, is_(mock_app))
            assert_that(auth_module.provider, is_(mock_auth_provider))
            mock_app.include_router.assert_called_once_with(mock_router)

    @pytest.mark.asyncio
    async def test_get_current_user_with_bearer_token(
        self,
        session: Session,
        auth_module: AuthModule,
        mock_request: MagicMock,
        sample_user: User,
    ):
        """Test get_current_user with valid bearer token."""
        # Setup
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_token"
        )
        validation = TokenValidation(valid=True, user_id=str(sample_user.id))

        auth_module.provider.validate_token = AsyncMock(
            side_effect=lambda token: validation
        )

        with patch.object(auth_module, "_get_user_by_id", return_value=sample_user):
            result = await auth_module.get_current_user(
                mock_request, session, credentials
            )

            assert_that(result, is_(sample_user))
            auth_module.provider.validate_token.assert_called_once_with("valid_token")
            auth_module._get_user_by_id.assert_called_once_with(
                str(sample_user.id), session
            )

    @pytest.mark.asyncio
    async def test_get_current_user_with_cookie_token(
        self,
        session: Session,
        auth_module: AuthModule,
        mock_request: MagicMock,
        sample_user: User,
    ):
        """Test get_current_user with valid cookie token."""
        # Setup
        mock_request.cookies = {"access_token": "cookie_token"}
        validation = TokenValidation(valid=True, user_id=str(sample_user.id))

        auth_module.provider.validate_token = AsyncMock(
            side_effect=lambda token: validation
        )

        with patch.object(auth_module, "_get_user_by_id", return_value=sample_user):
            result = await auth_module.get_current_user(mock_request, session, None)

            assert_that(result, is_(sample_user))
            auth_module.provider.validate_token.assert_called_once_with("cookie_token")

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(
        self, session: Session, auth_module: AuthModule, mock_request: MagicMock
    ):
        """Test get_current_user with no token provided."""
        result = await auth_module.get_current_user(mock_request, session, None)

        assert_that(result, is_(none()))
        auth_module.provider.validate_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self, session: Session, auth_module: AuthModule, mock_request: MagicMock
    ):
        """Test get_current_user with invalid token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )
        validation = TokenValidation(valid=False, user_id=None)

        auth_module.provider.validate_token.return_value = validation

        result = await auth_module.get_current_user(mock_request, session, credentials)

        assert_that(result, is_(none()))

    @pytest.mark.asyncio
    async def test_get_current_user_validation_exception(
        self, session: Session, auth_module: AuthModule, mock_request: MagicMock
    ):
        """Test get_current_user when token validation raises exception."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="error_token"
        )
        auth_module.provider.validate_token.side_effect = Exception("Validation error")

        result = await auth_module.get_current_user(mock_request, session, credentials)

        assert_that(result, is_(none()))

    @pytest.mark.asyncio
    async def test_require_auth_success(
        self,
        session: Session,
        auth_module: AuthModule,
        mock_request: MagicMock,
        sample_user: User,
    ):
        """Test require_auth with valid authentication."""
        with patch.object(auth_module, "get_current_user", return_value=sample_user):
            result = await auth_module.require_auth(mock_request, session, None)

            assert_that(result, is_(sample_user))

    @pytest.mark.asyncio
    async def test_require_auth_failure(
        self, session: Session, auth_module: AuthModule, mock_request: MagicMock
    ):
        """Test require_auth with no authentication."""
        with patch.object(auth_module, "get_current_user", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await auth_module.require_auth(mock_request, session, None)

            assert_that(exc_info.value.status_code, equal_to(401))
            assert_that(exc_info.value.detail, equal_to("Authentication required"))

    @pytest.mark.asyncio
    async def test_validate_token(self, session: Session, auth_module):
        """Test validate_token method."""
        expected_validation = TokenValidation(valid=True, user_id="user123")
        auth_module.provider.validate_token = AsyncMock(
            side_effect=lambda token: expected_validation
        )

        result = await auth_module.validate_token("test_token")

        assert_that(result, is_(expected_validation))
        auth_module.provider.validate_token.assert_called_once_with("test_token")

    @pytest.mark.asyncio
    async def test_create_tokens_for_user(self, auth_module, sample_user):
        """Test create_tokens_for_user method."""
        expected_tokens = {"access_token": "token123", "refresh_token": "refresh123"}
        auth_module.provider.create_tokens = AsyncMock(
            side_effect=lambda user: expected_tokens
        )

        result = await auth_module.create_tokens_for_user(sample_user)

        assert_that(result, is_(expected_tokens))
        auth_module.provider.create_tokens.assert_called_once_with(sample_user)

    def test_get_provider_info_basic(self, auth_module):
        """Test get_provider_info with basic provider."""
        with patch("src.auth.auth_module.get_provider_type", return_value="basic"):
            result = auth_module.get_provider_info()

            expected = {
                "provider_type": "basic",
                "provider_name": "test_provider",
                "supports_oauth": True,
                "supports_password_auth": True,
            }

            assert_that(result, equal_to(expected))

    def test_get_provider_info_with_oauth(self, auth_module):
        """Test get_provider_info with OAuth-capable provider."""
        auth_module.provider.get_authorization_url = MagicMock()

        with patch("src.auth.auth_module.get_provider_type", return_value="oauth"):
            result = auth_module.get_provider_info()

            assert_that(result["supports_oauth"], is_(True))

    def test_get_provider_info_with_password_auth(self, auth_module):
        """Test get_provider_info with password auth capable provider."""
        auth_module.provider.authenticate_user = MagicMock()

        with patch("src.auth.auth_module.get_provider_type", return_value="password"):
            result = auth_module.get_provider_info()

            assert_that(result["supports_password_auth"], is_(True))

    def test_get_user_by_id_success(self, session: Session, auth_module, user):
        """Test _get_user_by_id with successful database lookup."""

        result = auth_module._get_user_by_id(str(user.id), session)
        assert_that(result, is_(user))

    def test_get_user_by_id_not_found(self, session: Session, auth_module):
        """Test _get_user_by_id when user not found."""
        mock_db = AsyncMock()
        mock_db.get.return_value = None

        with patch("src.db.get_async_db") as mock_get_db:
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            result = auth_module._get_user_by_id("nonexistent_id", session)

            assert_that(result, is_(none()))

    def test_get_user_by_id_database_error(self, session: Session, auth_module):
        """Test _get_user_by_id when database raises exception."""
        with patch("src.db.get_async_db") as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            result = auth_module._get_user_by_id("user_id", session)

            assert_that(result, is_(none()))


#  TODO: some mocking in this test class is breaking other tests
@pytest.mark.skip
class TestAuthModuleGlobalFunctions:
    """Test cases for global auth module functions."""

    def test_initialize_auth(self):
        """Test initialize_auth function."""
        mock_app = MagicMock(spec=FastAPI)

        with patch("src.auth.auth_module.AuthModule") as mock_auth_module_class:
            mock_instance = MagicMock()
            mock_auth_module_class.return_value = mock_instance

            result = initialize_auth(mock_app)

            assert_that(result, is_(mock_instance))
            mock_auth_module_class.assert_called_once_with(mock_app)

    def test_get_auth_module_success(self):
        """Test get_auth_module when module is initialized."""
        import src.auth.auth_module

        mock_app = MagicMock(spec=FastAPI)

        with patch("src.auth.auth_module.AuthModule") as mock_auth_module_class:
            mock_instance = MagicMock()
            mock_auth_module_class.return_value = mock_instance

            with patch.object(src.auth.auth_module, "_auth_module", None):
                # Initialize first
                initialize_auth(mock_app)

                # Then get
                result = get_auth_module()

                assert_that(result, is_(mock_instance))

    def test_get_auth_module_not_initialized(self):
        """Test get_auth_module when module is not initialized."""
        # Reset global state
        import src.auth.auth_module

        with patch.object(src.auth.auth_module, "_auth_module", None):
            # src.auth.auth_module._auth_module = None

            with pytest.raises(RuntimeError) as exc_info:
                get_auth_module()

            assert_that(
                str(exc_info.value),
                equal_to("Auth module not initialized. Call initialize_auth() first."),
            )

    @pytest.mark.asyncio
    async def test_dependency_get_current_user(self, sample_user):
        """Test get_current_user dependency function."""
        from src.auth.auth_module import get_current_user

        mock_request = MagicMock()
        mock_auth_module = AsyncMock()
        mock_auth_module.get_current_user.return_value = sample_user

        with patch(
            "src.auth.auth_module.get_auth_module", return_value=mock_auth_module
        ):
            result = await get_current_user(mock_request, None)

            assert_that(result, is_(sample_user))
            mock_auth_module.get_current_user.assert_called_once_with(
                mock_request, None
            )

    @pytest.mark.asyncio
    async def test_dependency_require_auth(self, sample_user):
        """Test require_auth dependency function."""
        from src.auth.auth_module import require_auth

        mock_request = MagicMock()
        mock_auth_module = AsyncMock()
        mock_auth_module.require_auth.return_value = sample_user

        with patch(
            "src.auth.auth_module.get_auth_module", return_value=mock_auth_module
        ):
            result = await require_auth(mock_request, None)

            assert_that(result, is_(sample_user))
            mock_auth_module.require_auth.assert_called_once_with(mock_request, None)

    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self, sample_user):
        """Test get_current_active_user with active user."""
        from src.auth.auth_module import get_current_active_user

        sample_user.is_active = True
        result = await get_current_active_user(sample_user)

        assert_that(result, is_(sample_user))

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self, sample_user):
        """Test get_current_active_user with inactive user."""
        from src.auth.auth_module import get_current_active_user

        sample_user.is_active = False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(sample_user)

        assert_that(exc_info.value.status_code, equal_to(400))
        assert_that(exc_info.value.detail, equal_to("Inactive user"))

    @pytest.mark.asyncio
    async def test_get_current_verified_user_success(self, sample_user):
        """Test get_current_verified_user with verified user."""
        from src.auth.auth_module import get_current_verified_user

        sample_user.is_verified = True
        result = await get_current_verified_user(sample_user)

        assert_that(result, is_(sample_user))

    @pytest.mark.asyncio
    async def test_get_current_verified_user_unverified(self, sample_user):
        """Test get_current_verified_user with unverified user."""
        from src.auth.auth_module import get_current_verified_user

        sample_user.is_verified = False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_verified_user(sample_user)

        assert_that(exc_info.value.status_code, equal_to(400))
        assert_that(exc_info.value.detail, equal_to("Unverified user"))

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
            is_active=True,
            is_verified=True,
        )
