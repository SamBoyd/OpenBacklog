"""
Tests for authentication provider factory.
"""

from unittest.mock import Mock, patch

import pytest
from hamcrest import assert_that, equal_to, instance_of, is_, not_, not_none

from src.auth.factory import (
    AuthProviderFactory,
    get_auth_provider,
    get_provider_type,
    is_oauth_flow,
    supports_password_auth,
    supports_registration,
)
from src.auth.providers import Auth0Provider, DevAuthProvider, SimpleAuthProvider


class TestAuthProviderFactory:
    """Test cases for AuthProviderFactory class."""

    def setup_method(self):
        """Reset factory state before each test."""
        AuthProviderFactory.reset()

    def test_get_provider_creates_auth0_provider_when_specified(self):
        """Test that specifying 'auth0' creates Auth0Provider."""
        provider = AuthProviderFactory.get_provider("auth0")

        assert_that(provider, instance_of(Auth0Provider))
        assert_that(AuthProviderFactory.get_provider_type(), equal_to("auth0"))

    def test_get_provider_creates_simple_provider_when_specified(self):
        """Test that specifying 'simple' creates SimpleAuthProvider."""
        provider = AuthProviderFactory.get_provider("simple")

        assert_that(provider, instance_of(SimpleAuthProvider))
        assert_that(AuthProviderFactory.get_provider_type(), equal_to("simple"))

    def test_get_provider_creates_dev_provider_when_specified(self):
        """Test that specifying 'dev' creates DevAuthProvider."""
        provider = AuthProviderFactory.get_provider("dev")

        assert_that(provider, instance_of(DevAuthProvider))
        assert_that(AuthProviderFactory.get_provider_type(), equal_to("dev"))

    def test_get_provider_raises_error_for_invalid_type(self):
        """Test that invalid provider type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown auth provider type: invalid"):
            AuthProviderFactory.get_provider("invalid")

    def test_get_provider_caches_instance(self):
        """Test that provider instance is cached and reused."""
        provider1 = AuthProviderFactory.get_provider("simple")
        provider2 = AuthProviderFactory.get_provider("simple")

        assert_that(provider1, is_(provider2))

    def test_get_provider_creates_new_instance_when_type_changes(self):
        """Test that changing provider type creates new instance."""
        provider1 = AuthProviderFactory.get_provider("simple")
        provider2 = AuthProviderFactory.get_provider("auth0")

        assert_that(provider1, instance_of(SimpleAuthProvider))
        assert_that(provider2, instance_of(Auth0Provider))
        assert_that(provider1, is_(not_(provider2)))

    @patch("src.auth.factory.settings")
    def test_determine_provider_type_uses_explicit_setting(self, mock_settings):
        """Test that explicit auth_provider setting is used."""
        mock_settings.auth_provider = "auth0"

        provider_type = AuthProviderFactory._determine_provider_type()

        assert_that(provider_type, equal_to("auth0"))

    @patch("src.auth.factory.settings")
    def test_determine_provider_type_falls_back_on_invalid_setting(self, mock_settings):
        """Test fallback when invalid auth_provider setting is provided."""
        mock_settings.auth_provider = "invalid"
        mock_settings.environment = "production"
        mock_settings.auth0_client_id = ""
        mock_settings.auth0_client_secret = ""
        mock_settings.auth0_domain = ""

        provider_type = AuthProviderFactory._determine_provider_type()

        assert_that(provider_type, equal_to("simple"))

    @patch("src.auth.factory.settings")
    def test_determine_provider_type_uses_auth0_when_configured(self, mock_settings):
        """Test that Auth0 is used when all required settings are present."""
        mock_settings.auth_provider = "auto"
        mock_settings.environment = "production"
        mock_settings.auth0_client_id = "test_client_id"
        mock_settings.auth0_client_secret = "test_client_secret"
        mock_settings.auth0_domain = "test.auth0.com"

        provider_type = AuthProviderFactory._determine_provider_type()

        assert_that(provider_type, equal_to("auth0"))

    @patch("src.auth.factory.settings")
    def test_determine_provider_type_defaults_to_simple(self, mock_settings):
        """Test that simple auth is default when no other conditions are met."""
        mock_settings.auth_provider = "auto"
        mock_settings.environment = "production"
        mock_settings.auth0_client_id = ""
        mock_settings.auth0_client_secret = ""
        mock_settings.auth0_domain = ""

        provider_type = AuthProviderFactory._determine_provider_type()

        assert_that(provider_type, equal_to("simple"))

    @patch("src.auth.factory.settings")
    def test_determine_provider_type_ignores_empty_auth0_settings(self, mock_settings):
        """Test that empty Auth0 settings don't trigger Auth0 provider."""
        mock_settings.auth_provider = "auto"
        mock_settings.environment = "production"
        mock_settings.auth0_client_id = ""
        mock_settings.auth0_client_secret = "secret"
        mock_settings.auth0_domain = "domain.com"

        provider_type = AuthProviderFactory._determine_provider_type()

        assert_that(provider_type, equal_to("simple"))

    def test_reset_clears_cached_instance(self):
        """Test that reset clears cached provider instance."""
        AuthProviderFactory.get_provider("simple")
        assert_that(AuthProviderFactory._instance, not_none())

        AuthProviderFactory.reset()

        assert_that(AuthProviderFactory._instance, is_(None))
        assert_that(AuthProviderFactory._provider_type, is_(None))

    def test_is_oauth_provider_returns_true_for_auth0(self):
        """Test that is_oauth_provider returns True for Auth0."""
        AuthProviderFactory.get_provider("auth0")

        result = AuthProviderFactory.is_oauth_provider()

        assert_that(result, is_(True))

    def test_is_oauth_provider_returns_false_for_simple(self):
        """Test that is_oauth_provider returns False for simple auth."""
        AuthProviderFactory.get_provider("simple")

        result = AuthProviderFactory.is_oauth_provider()

        assert_that(result, is_(False))

    def test_is_oauth_provider_returns_false_for_dev(self):
        """Test that is_oauth_provider returns False for dev auth."""
        AuthProviderFactory.get_provider("dev")

        result = AuthProviderFactory.is_oauth_provider()

        assert_that(result, is_(False))

    def test_supports_registration_returns_true_for_simple(self):
        """Test that supports_registration returns True for simple auth."""
        AuthProviderFactory.get_provider("simple")

        result = AuthProviderFactory.supports_registration()

        assert_that(result, is_(True))

    def test_supports_registration_returns_true_for_dev(self):
        """Test that supports_registration returns True for dev auth."""
        AuthProviderFactory.get_provider("dev")

        result = AuthProviderFactory.supports_registration()

        assert_that(result, is_(True))

    def test_supports_registration_returns_false_for_auth0(self):
        """Test that supports_registration returns False for Auth0."""
        AuthProviderFactory.get_provider("auth0")

        result = AuthProviderFactory.supports_registration()

        assert_that(result, is_(False))

    def test_supports_password_auth_returns_true_for_simple(self):
        """Test that supports_password_auth returns True for simple auth."""
        AuthProviderFactory.get_provider("simple")

        result = AuthProviderFactory.supports_password_auth()

        assert_that(result, is_(True))

    def test_supports_password_auth_returns_true_for_dev(self):
        """Test that supports_password_auth returns True for dev auth."""
        AuthProviderFactory.get_provider("dev")

        result = AuthProviderFactory.supports_password_auth()

        assert_that(result, is_(True))

    def test_supports_password_auth_returns_false_for_auth0(self):
        """Test that supports_password_auth returns False for Auth0."""
        AuthProviderFactory.get_provider("auth0")

        result = AuthProviderFactory.supports_password_auth()

        assert_that(result, is_(False))


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def setup_method(self):
        """Reset factory state before each test."""
        AuthProviderFactory.reset()

    def test_get_auth_provider_returns_provider_instance(self):
        """Test that get_auth_provider returns a provider instance."""
        provider = get_auth_provider()

        assert_that(provider, not_none())

    def test_get_provider_type_returns_current_type(self):
        """Test that get_provider_type returns current provider type."""
        AuthProviderFactory.get_provider("auth0")

        provider_type = get_provider_type()

        assert_that(provider_type, equal_to("auth0"))

    def test_is_oauth_flow_returns_oauth_status(self):
        """Test that is_oauth_flow returns OAuth status."""
        AuthProviderFactory.get_provider("auth0")

        result = is_oauth_flow()

        assert_that(result, is_(True))

    def test_supports_registration_returns_registration_support(self):
        """Test that supports_registration returns registration support status."""
        AuthProviderFactory.get_provider("simple")

        result = supports_registration()

        assert_that(result, is_(True))

    def test_supports_password_auth_returns_password_support(self):
        """Test that supports_password_auth returns password support status."""
        AuthProviderFactory.get_provider("dev")

        result = supports_password_auth()

        assert_that(result, is_(True))

    @patch("src.auth.factory.settings")
    def test_convenience_functions_work_without_explicit_provider_creation(
        self, mock_settings
    ):
        """Test that convenience functions work even without explicit provider creation."""
        mock_settings.auth_provider = "simple"

        provider_type = get_provider_type()
        oauth_flow = is_oauth_flow()
        registration = supports_registration()
        password_auth = supports_password_auth()

        assert_that(provider_type, equal_to("simple"))
        assert_that(oauth_flow, is_(False))
        assert_that(registration, is_(True))
        assert_that(password_auth, is_(True))
