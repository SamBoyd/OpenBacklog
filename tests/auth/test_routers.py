"""
Comprehensive test suite for authentication routers.
"""

import uuid
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient
from hamcrest import (
    assert_that,
    equal_to,
    has_property,
    instance_of,
    is_,
    none,
    not_none,
)

from src.auth.providers.base import (
    AuthProvider,
    AuthResult,
    TokenPair,
    TokenValidation,
    UserInfo,
)
from src.auth.routers import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    _get_cookie_settings,
    _get_or_create_user_from_auth_result,
    _set_auth_cookie,
    auth_router,
)
from src.models import OAuthAccount, User


class MockAuthProvider(AuthProvider):
    """Mock auth provider for testing."""

    def __init__(self):
        self.provider_name = "test"
        self.mock_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
            is_active=True,
            is_verified=True,
        )
        self.mock_tokens = TokenPair(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token",
            expires_in=3600,
        )
        self.mock_user_info = UserInfo(
            email="test@example.com",
            sub="test_sub_123",
            name="Test User",
            email_verified=True,
        )

    async def get_authorization_url(
        self, redirect_uri: str, state: Optional[str] = None
    ) -> str:
        return f"https://example.com/auth?redirect_uri={redirect_uri}&state={state}"

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        if username == "valid@example.com" and password == "correct_password":
            return self.mock_user
        return None

    async def create_tokens(self, user: User) -> TokenPair:
        return self.mock_tokens

    async def handle_callback(
        self, code: str, redirect_uri: str, state: Optional[str] = None
    ) -> AuthResult:
        return AuthResult(tokens=self.mock_tokens, user_info=self.mock_user_info)

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        return self.mock_tokens

    async def get_user_info(self, access_token: str) -> Optional[UserInfo]:
        if access_token == "valid_token":
            return self.mock_user_info
        return None

    async def register_user(
        self, email: str, password: str, name: Optional[str] = None
    ) -> Optional[User]:
        return User(
            id=uuid.uuid4(), email=email, name=name, is_active=True, is_verified=False
        )

    async def auto_login_dev_user(self) -> Optional[User]:
        return self.mock_user

    async def validate_token(self, token: str) -> TokenValidation:
        if token == "valid_token":
            return TokenValidation(
                valid=True,
                user_id=str(self.mock_user.id),
                claims={"sub": str(self.mock_user.id), "email": self.mock_user.email},
            )
        return TokenValidation(valid=False, error="Invalid token")


@pytest.fixture
def mock_auth_provider():
    """Create mock auth provider."""
    return MockAuthProvider()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("src.auth.routers.settings") as mock:
        mock.environment = "development"
        mock.app_url = "http://localhost:8000"
        yield mock


@pytest.fixture
def mock_templates():
    """Mock templates for testing."""
    with patch("src.auth.routers.templates") as mock:
        mock.TemplateResponse = MagicMock(return_value=HTMLResponse("mocked template"))
        yield mock


@pytest.fixture
def test_app(mock_auth_provider, mock_settings, mock_templates):
    """Create test FastAPI app with auth router."""
    app = FastAPI()

    # Override dependencies directly in the app
    from src.auth.factory import get_auth_provider

    def get_mock_auth_provider():
        return mock_auth_provider

    app.dependency_overrides[get_auth_provider] = get_mock_auth_provider

    # Mock factory functions
    with patch(
        "src.auth.factory.AuthProviderFactory.get_provider_type", return_value="test"
    ):
        with patch(
            "src.auth.factory.AuthProviderFactory.is_oauth_provider", return_value=False
        ):
            with patch(
                "src.auth.factory.AuthProviderFactory.supports_password_auth",
                return_value=True,
            ):
                app.include_router(auth_router)
                yield app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestCookieHelpers:
    """Test cookie helper functions."""

    def test_get_cookie_settings_development(self):
        """Test cookie settings in development environment."""
        with patch("src.auth.routers.settings") as mock_settings:
            mock_settings.environment = "development"

            settings = _get_cookie_settings()

            assert_that(settings["httponly"], is_(False))
            assert_that(settings["secure"], is_(False))
            assert_that(settings["samesite"], equal_to("lax"))

    def test_get_cookie_settings_production(self):
        """Test cookie settings in production environment."""
        with patch("src.auth.routers.settings") as mock_settings:
            mock_settings.environment = "production"

            settings = _get_cookie_settings()

            assert_that(settings["httponly"], is_(True))
            assert_that(settings["secure"], is_(True))
            assert_that(settings["samesite"], equal_to("strict"))

    def test_set_auth_cookie(self):
        """Test setting authentication cookie."""
        response = MagicMock()

        with patch("src.auth.routers.settings") as mock_settings:
            mock_settings.environment = "development"
            mock_settings.app_domain = "app.localhost"
            _set_auth_cookie(response, "test_key", "test_value", 3600, "/test")

            response.set_cookie.assert_called_once_with(
                key="test_key",
                value="test_value",
                max_age=3600,
                path="/test",
                httponly=False,
                secure=False,
                samesite="lax",
                domain=".app.localhost",
            )


class TestAuthRoutes:
    """Test authentication route endpoints."""

    def test_get_login_url_success(self, client):
        """Test successful login URL generation."""
        response = client.get("/auth/login-url")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["authorization_url"], not_none())
        assert_that(data["provider_type"], equal_to("test"))
        assert_that(data["is_oauth"], is_(False))

    def test_get_login_url_with_params(self, client):
        """Test login URL with redirect_uri and state."""
        response = client.get(
            "/auth/login-url?redirect_uri=http://example.com&state=test_state"
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(
            "redirect_uri=http://example.com" in data["authorization_url"], is_(True)
        )
        assert_that("state=test_state" in data["authorization_url"], is_(True))

    def test_get_login_url_error_handling(self, test_app):
        """Test login URL error handling."""
        from src.auth.factory import get_auth_provider

        def get_error_provider():
            provider = MagicMock()
            provider.get_authorization_url.side_effect = Exception("Provider error")
            return provider

        test_app.dependency_overrides[get_auth_provider] = get_error_provider

        with TestClient(test_app) as client:
            response = client.get("/auth/login-url")
            assert_that(response.status_code, equal_to(500))

    def test_login_form_success(self, client):
        """Test login form rendering."""
        response = client.get("/auth/login")

        assert_that(response.status_code, equal_to(200))
        assert_that(
            response.headers["content-type"], equal_to("text/html; charset=utf-8")
        )

    def test_login_form_oauth_provider_error(self, client):
        """Test login form with OAuth provider (should fail)."""
        with patch("src.auth.routers.supports_password_auth", return_value=False):
            response = client.get("/auth/login")

            assert_that(response.status_code, equal_to(400))

    def test_login_success(self, client):
        """Test successful login."""
        login_data = {"username": "valid@example.com", "password": "correct_password"}

        response = client.post("/auth/login", json=login_data)

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["success"], is_(True))
        assert_that(data["message"], equal_to("Login successful"))
        assert_that(data["redirect_url"], not_none())

        # Check cookies are set
        cookies = response.headers["set-cookie"]
        assert_that("access_token" in cookies, is_(True))
        assert_that("refresh_token" in cookies, is_(True))

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {"username": "invalid@example.com", "password": "wrong_password"}

        response = client.post("/auth/login", json=login_data)

        assert_that(response.status_code, equal_to(401))

    def test_login_oauth_provider_error(self, client):
        """Test login with OAuth provider (should fail)."""
        with patch("src.auth.routers.supports_password_auth", return_value=False):
            login_data = {"username": "test@example.com", "password": "password"}

            response = client.post("/auth/login", json=login_data)

            assert_that(response.status_code, equal_to(400))

    def test_register_form_simple_auth(self, client):
        """Test registration form for simple auth."""
        with patch("src.auth.routers.get_provider_type", return_value="simple"):
            response = client.get("/auth/register")

            assert_that(response.status_code, equal_to(200))

    def test_register_form_auth0_error(self, client):
        """Test registration form with Auth0 (should fail)."""
        with patch("src.auth.routers.get_provider_type", return_value="auth0"):
            response = client.get("/auth/register")

            assert_that(response.status_code, equal_to(400))

    def test_register_form_dev_error(self, client):
        """Test registration form with dev provider (should fail)."""
        with patch("src.auth.routers.get_provider_type", return_value="dev"):
            response = client.get("/auth/register")

            assert_that(response.status_code, equal_to(400))

    def test_register_success(self, client):
        """Test successful registration."""
        with patch("src.auth.routers.get_provider_type", return_value="simple"):
            register_data = {
                "email": "newuser@example.com",
                "password": "secure_password",
                "name": "New User",
            }

            response = client.post("/auth/register", json=register_data)

            assert_that(response.status_code, equal_to(201))
            data = response.json()
            assert_that(data["success"], is_(True))
            assert_that(data["redirect_url"], equal_to("/workspace"))

    def test_register_auth0_error(self, client):
        """Test registration with Auth0 (should fail)."""
        with patch("src.auth.routers.get_provider_type", return_value="auth0"):
            register_data = {"email": "test@example.com", "password": "password"}

            response = client.post("/auth/register", json=register_data)

            assert_that(response.status_code, equal_to(400))

    def test_register_dev_error(self, client):
        """Test registration with dev provider (should fail)."""
        with patch("src.auth.routers.get_provider_type", return_value="dev"):
            register_data = {"email": "test@example.com", "password": "password"}

            response = client.post("/auth/register", json=register_data)

            assert_that(response.status_code, equal_to(400))


class TestOAuthCallback:
    """Test OAuth callback endpoint."""

    def test_oauth_callback_success(self, test_app):
        """Test successful OAuth callback."""
        # Update the test app to use OAuth flow
        with patch(
            "src.auth.factory.AuthProviderFactory.is_oauth_provider", return_value=True
        ):
            with patch(
                "src.auth.routers._get_or_create_user_from_auth_result"
            ) as mock_get_user:
                mock_user = User(
                    id=uuid.uuid4(), email="test@example.com", name="Test User"
                )
                mock_get_user.return_value = mock_user

                with TestClient(test_app, follow_redirects=False) as client:
                    response = client.get(
                        "/auth/callback?code=test_code&state=test_state"
                    )

                    assert_that(response.status_code, equal_to(302))
                    assert_that(response.headers["location"], equal_to("/workspace"))

    def test_oauth_callback_not_oauth_error(self, client):
        """Test callback with non-OAuth provider (should fail)."""
        with patch("src.auth.routers.is_oauth_flow", return_value=False):
            response = client.get("/auth/callback?code=test_code")

            assert_that(response.status_code, equal_to(400))

    def test_oauth_callback_error_param(self, client):
        """Test callback with error parameter."""
        with patch("src.auth.routers.is_oauth_flow", return_value=True):
            response = client.get("/auth/callback?error=access_denied")

            assert_that(response.status_code, equal_to(400))

    def test_oauth_callback_missing_code(self, client):
        """Test callback without code parameter."""
        with patch("src.auth.routers.is_oauth_flow", return_value=True):
            response = client.get("/auth/callback")

            assert_that(response.status_code, equal_to(400))


class TestLogoutAndRefresh:
    """Test logout and token refresh endpoints."""

    def test_logout_success(self, test_app):
        """Test successful logout."""
        with TestClient(test_app, follow_redirects=False) as client:
            response = client.post("/auth/logout")

            assert_that(response.status_code, equal_to(302))
            assert_that(response.headers["location"], equal_to("/"))

            # Check cookies are deleted - look for proper cookie deletion headers
            set_cookie_headers = response.headers.get_list("set-cookie") or []
            access_token_deleted = any(
                "access_token" in header and "Max-Age=0" in header
                for header in set_cookie_headers
            )
            refresh_token_deleted = any(
                "refresh_token" in header and "Max-Age=0" in header
                for header in set_cookie_headers
            )
            assert_that(access_token_deleted, is_(True))
            assert_that(refresh_token_deleted, is_(True))

    def test_refresh_token_success(self, client):
        """Test successful token refresh."""
        # Set refresh token cookie
        client.cookies.set("refresh_token", "valid_refresh_token")

        response = client.post("/auth/refresh")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["success"], is_(True))
        assert_that(data["message"], equal_to("Token refreshed"))

    def test_refresh_token_missing(self, client):
        """Test token refresh without refresh token."""
        response = client.post("/auth/refresh")

        assert_that(response.status_code, equal_to(401))


class TestUserInfo:
    """Test user info endpoint."""

    def test_get_current_user_success(self, client):
        """Test successful user info retrieval."""
        # Set access token cookie
        client.cookies.set("access_token", "valid_token")

        response = client.get("/auth/me")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["email"], equal_to("test@example.com"))
        assert_that(data["name"], equal_to("Test User"))
        assert_that(data["email_verified"], is_(True))

    def test_get_current_user_no_token(self, client):
        """Test user info without access token."""
        response = client.get("/auth/me")

        assert_that(response.status_code, equal_to(401))

    def test_get_current_user_invalid_token(self, client):
        """Test user info with invalid token."""
        client.cookies.set("access_token", "invalid_token")

        response = client.get("/auth/me")

        assert_that(response.status_code, equal_to(401))


class TestProviderInfo:
    """Test provider info endpoint."""

    def test_get_provider_info(self, client):
        """Test provider info retrieval."""
        response = client.get("/auth/provider-info")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["provider_type"], equal_to("test"))
        assert_that(data["is_oauth"], is_(False))
        assert_that(data["supports_registration"], is_(True))
        assert_that(data["supports_password_auth"], is_(True))


class TestDevLogin:
    """Test dev login endpoint."""

    def test_dev_login_success(self, test_app):
        """Test successful dev login."""
        with patch(
            "src.auth.factory.AuthProviderFactory.get_provider_type", return_value="dev"
        ):
            with TestClient(test_app, follow_redirects=False) as client:
                response = client.get("/auth/dev-login")

                assert_that(response.status_code, equal_to(302))
                assert_that(response.headers["location"], equal_to("/workspace"))

    def test_dev_login_non_dev_provider(self, client):
        """Test dev login with non-dev provider (should fail)."""
        with patch("src.auth.routers.get_provider_type", return_value="simple"):
            response = client.get("/auth/dev-login")

            assert_that(response.status_code, equal_to(400))

    def test_dev_login_with_redirect(self, test_app):
        """Test dev login with custom redirect."""
        with patch(
            "src.auth.factory.AuthProviderFactory.get_provider_type", return_value="dev"
        ):
            with TestClient(test_app, follow_redirects=False) as client:
                response = client.get("/auth/dev-login?redirect_uri=/custom")

                assert_that(response.status_code, equal_to(302))
                assert_that(response.headers["location"], equal_to("/custom"))


class TestDatabaseHelper:
    """Test database helper function."""

    def test_database_helper_function_exists(self):
        """Test that the database helper function exists and is callable."""
        # Just test that the function exists and can be imported
        from src.auth.routers import _get_or_create_user_from_auth_result

        assert_that(_get_or_create_user_from_auth_result, not_none())

        # Test that the required classes can be imported
        from src.models import OAuthAccount, User

        assert_that(User, not_none())
        assert_that(OAuthAccount, not_none())
