"""
Unit tests for MCPAuthFactory.

Tests the factory pattern implementation for initializing MCP authentication
providers based on environment configuration (test, dev, or auth0 modes).
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.mcp_server.auth_factory import (
    MCPAuthFactory,
    get_mcp_auth_factory,
    reset_mcp_auth_factory,
)
from src.mcp_server.providers.dev import DevMCPAuthProvider


class TestMCPAuthFactoryTestMode:
    """Test MCPAuthFactory in test environment mode."""

    def test_test_mode_returns_none_providers(self):
        """Test that test mode returns None for all auth providers."""
        factory = MCPAuthFactory()

        with patch("src.config.settings.environment", "test"):
            auth_provider, well_known_routes, mcp_auth_context_provider = (
                factory.initialize()
            )

            assert auth_provider is None
            assert well_known_routes == {}
            assert mcp_auth_context_provider is None

    def test_test_mode_idempotent(self):
        """Test that multiple initialize calls return the same result."""
        factory = MCPAuthFactory()

        with patch("src.config.settings.environment", "test"):
            result1 = factory.initialize()
            result2 = factory.initialize()

            assert result1 == result2
            assert result1[0] is None  # auth_provider
            assert result1[1] == {}  # well_known_routes
            assert result1[2] is None  # mcp_auth_context_provider


class TestMCPAuthFactoryDevMode:
    """Test MCPAuthFactory in development mode."""

    def test_dev_mode_returns_dev_provider(self):
        """Test that dev mode creates and returns DevMCPAuthProvider."""
        factory = MCPAuthFactory()

        with (
            patch("src.config.settings.environment", "development"),
            patch("src.config.settings.mcp_auth_mode", "dev"),
        ):
            auth_provider, well_known_routes, mcp_auth_context_provider = (
                factory.initialize()
            )

            assert auth_provider is None  # No FastMCP auth for dev
            assert well_known_routes == {}
            assert isinstance(mcp_auth_context_provider, DevMCPAuthProvider)

    def test_dev_mode_creates_single_provider_instance(self):
        """Test that dev mode creates only one instance across calls."""
        factory = MCPAuthFactory()

        with (
            patch("src.config.settings.environment", "development"),
            patch("src.config.settings.mcp_auth_mode", "dev"),
        ):
            _, _, provider1 = factory.initialize()
            _, _, provider2 = factory.initialize()

            # Same object returned on second call (cached by initialize check)
            assert provider1 is provider2

    def test_dev_mode_getter_methods_work(self):
        """Test that getter methods work correctly in dev mode."""
        factory = MCPAuthFactory()

        with (
            patch("src.config.settings.environment", "development"),
            patch("src.config.settings.mcp_auth_mode", "dev"),
        ):
            provider = factory.get_mcp_auth_context_provider()
            assert isinstance(provider, DevMCPAuthProvider)

            auth_provider = factory.get_auth_provider()
            assert auth_provider is None

            routes = factory.get_well_known_routes()
            assert routes == {}


class TestMCPAuthFactoryAuth0Mode:
    """Test MCPAuthFactory in Auth0 production mode."""

    def test_auth0_mode_creates_providers(self):
        """Test that auth0 mode initializes all required providers."""
        factory = MCPAuthFactory()

        with (
            patch("src.config.settings.environment", "production"),
            patch("src.config.settings.mcp_auth_mode", "auth0"),
            patch("src.config.settings.mcp_server_auth0_domain", "example.auth0.com"),
            patch("src.config.settings.mcp_server_auth0_client_id", "test_client_id"),
            patch("src.config.settings.mcp_server_auth0_client_secret", "test_secret"),
            patch("src.config.settings.mcp_server_auth0_audience", "test_audience"),
            patch("src.config.settings.mcp_server_domain", "https://example.com"),
            patch(
                "src.config.settings.mcp_oauth_storage_encryption_key",
                "n-JixMFChxEXE8fNom6f6vmfU8NhPHl0COQ9SPjX6J4=",
            ),
            patch("src.config.settings.mcp_oauth_jwt_signing_key", "test_jwt_key"),
            patch(
                "src.mcp_server.storage.PostgreSQLMCPStorage"
            ) as mock_postgres_storage,
            patch(
                "key_value.aio.wrappers.encryption.FernetEncryptionWrapper"
            ) as mock_encryption_wrapper,
            patch(
                "fastmcp.server.auth.providers.auth0.Auth0Provider"
            ) as mock_auth0_provider,
            patch(
                "src.mcp_server.providers.auth0.Auth0MCPAuthProvider"
            ) as mock_auth0_mcp_provider,
            patch("src.db.async_session_maker"),
        ):
            # Mock the auth0 provider to have get_well_known_routes method
            mock_auth0_provider_instance = MagicMock()
            mock_auth0_provider_instance.get_well_known_routes.return_value = {
                "issuer": "https://example.auth0.com/",
                "authorization_endpoint": "https://example.auth0.com/authorize",
            }
            mock_auth0_provider.return_value = mock_auth0_provider_instance

            auth_provider, well_known_routes, mcp_auth_context_provider = (
                factory.initialize()
            )

            # Verify Auth0Provider was created
            assert auth_provider is mock_auth0_provider_instance
            # Verify well-known routes were fetched
            assert well_known_routes == {
                "issuer": "https://example.auth0.com/",
                "authorization_endpoint": "https://example.auth0.com/authorize",
            }
            # Verify MCP auth context provider was created
            assert mcp_auth_context_provider is not None

    def test_auth0_mode_uses_correct_settings(self):
        """Test that Auth0Provider is configured with correct settings."""
        factory = MCPAuthFactory()

        with (
            patch("src.config.settings.environment", "production"),
            patch("src.config.settings.mcp_auth_mode", "auth0"),
            patch("src.config.settings.mcp_server_auth0_domain", "my.auth0.com"),
            patch("src.config.settings.mcp_server_auth0_client_id", "my_client_id"),
            patch("src.config.settings.mcp_server_auth0_client_secret", "my_secret"),
            patch("src.config.settings.mcp_server_auth0_audience", "my_audience"),
            patch("src.config.settings.mcp_server_domain", "https://myapp.com"),
            patch(
                "src.config.settings.mcp_oauth_storage_encryption_key",
                "n-JixMFChxEXE8fNom6f6vmfU8NhPHl0COQ9SPjX6J4=",
            ),
            patch("src.config.settings.mcp_oauth_jwt_signing_key", "my_jwt_key"),
            patch(
                "src.mcp_server.storage.PostgreSQLMCPStorage"
            ) as mock_postgres_storage,
            patch(
                "key_value.aio.wrappers.encryption.FernetEncryptionWrapper"
            ) as mock_encryption_wrapper,
            patch(
                "fastmcp.server.auth.providers.auth0.Auth0Provider"
            ) as mock_auth0_provider,
            patch(
                "src.mcp_server.providers.auth0.Auth0MCPAuthProvider"
            ) as mock_auth0_mcp_provider,
            patch("src.db.async_session_maker"),
        ):
            mock_auth0_provider_instance = MagicMock()
            mock_auth0_provider_instance.get_well_known_routes.return_value = {}
            mock_auth0_provider.return_value = mock_auth0_provider_instance

            factory.initialize()

            # Verify Auth0Provider was called with correct arguments
            mock_auth0_provider.assert_called_once()
            call_kwargs = mock_auth0_provider.call_args[1]

            assert (
                call_kwargs["config_url"]
                == "https://my.auth0.com/.well-known/openid-configuration"
            )
            assert call_kwargs["client_id"] == "my_client_id"
            assert call_kwargs["client_secret"] == "my_secret"
            assert call_kwargs["audience"] == "my_audience"
            assert call_kwargs["base_url"] == "https://myapp.com/mcp"
            assert call_kwargs["issuer_url"] == "https://myapp.com"


class TestMCPAuthFactoryGlobalInstance:
    """Test the global MCPAuthFactory instance and its accessors."""

    def test_get_mcp_auth_factory_returns_singleton(self):
        """Test that get_mcp_auth_factory returns the same instance."""
        factory1 = get_mcp_auth_factory()
        factory2 = get_mcp_auth_factory()

        assert factory1 is factory2

    def test_reset_mcp_auth_factory_clears_state(self):
        """Test that reset_mcp_auth_factory resets the global instance."""
        factory = get_mcp_auth_factory()

        with patch("src.config.settings.environment", "test"):
            factory.initialize()
            assert factory._initialized is True

            reset_mcp_auth_factory()
            assert factory._initialized is False
            assert factory._auth_provider is None
            assert factory._mcp_auth_context_provider is None
            assert factory._well_known_routes == {}


class TestMCPAuthFactoryReset:
    """Test factory reset functionality."""

    def test_reset_clears_cached_providers(self):
        """Test that reset clears all cached state."""
        factory = MCPAuthFactory()

        with (
            patch("src.config.settings.environment", "development"),
            patch("src.config.settings.mcp_auth_mode", "dev"),
        ):
            provider1 = factory.get_mcp_auth_context_provider()
            assert provider1 is not None

            factory.reset()

            assert factory._initialized is False
            assert factory._auth_provider is None
            assert factory._mcp_auth_context_provider is None

    def test_reset_allows_reinitialization_with_different_settings(self):
        """Test that after reset, factory can be reinitialized with different settings."""
        factory = MCPAuthFactory()

        # First initialize in test mode
        with patch("src.config.settings.environment", "test"):
            auth_provider1, _, mcp_provider1 = factory.initialize()
            assert mcp_provider1 is None

        # Reset and reinitialize in dev mode
        factory.reset()

        with (
            patch("src.config.settings.environment", "development"),
            patch("src.config.settings.mcp_auth_mode", "dev"),
        ):
            auth_provider2, _, mcp_provider2 = factory.initialize()
            assert isinstance(mcp_provider2, DevMCPAuthProvider)


class TestMCPAuthFactoryLazyInitialization:
    """Test lazy initialization through getter methods."""

    def test_getter_methods_trigger_initialization(self):
        """Test that getter methods trigger initialization if not yet done."""
        factory = MCPAuthFactory()

        with patch("src.config.settings.environment", "test"):
            assert factory._initialized is False

            # Call a getter without calling initialize
            result = factory.get_auth_provider()
            assert result is None
            assert factory._initialized is True

    def test_all_getters_available_after_lazy_init(self):
        """Test that all getters work correctly after lazy initialization."""
        factory = MCPAuthFactory()

        with (
            patch("src.config.settings.environment", "development"),
            patch("src.config.settings.mcp_auth_mode", "dev"),
        ):
            # Access through different getters
            auth_provider = factory.get_auth_provider()
            well_known_routes = factory.get_well_known_routes()
            mcp_auth_context_provider = factory.get_mcp_auth_context_provider()

            assert auth_provider is None
            assert well_known_routes == {}
            assert isinstance(mcp_auth_context_provider, DevMCPAuthProvider)
            assert factory._initialized is True
