"""
Factory for initializing MCP authentication providers based on environment configuration.

This module handles the creation and configuration of authentication providers
for the MCP server, following the factory pattern similar to vault_factory.py.

Supports three authentication modes:
- test: No authentication (used in testing)
- dev: Development mode using DevMCPAuthProvider (no token validation)
- auth0: Production mode using Auth0MCPAuthProvider with OAuth
"""

import logging
from typing import Any, Dict, Optional, Tuple

from src.config import settings
from src.mcp_server.providers.base import MCPAuthProvider

logger = logging.getLogger(__name__)


class MCPAuthFactory:
    """Factory for creating and managing MCP authentication providers."""

    def __init__(self):
        """Initialize the factory with no cached provider."""
        self._auth_provider: Optional[Any] = None
        self._mcp_auth_context_provider: Optional[MCPAuthProvider] = None
        self._well_known_routes: Dict[str, Any] = {}
        self._initialized = False

    def initialize(
        self,
    ) -> Tuple[Optional[Any], Dict[str, Any], Optional[MCPAuthProvider]]:
        """
        Initialize the appropriate auth provider based on settings.

        Returns:
            Tuple of (auth_provider, well_known_routes, mcp_auth_context_provider)
            where each component may be None depending on the configured mode.

        Raises:
            Exception: If initialization fails due to missing configuration.
        """
        if self._initialized:
            return (
                self._auth_provider,
                self._well_known_routes,
                self._mcp_auth_context_provider,
            )

        if settings.environment == "test":
            # No auth in test mode
            self._auth_provider = None
            self._well_known_routes = {}
            self._mcp_auth_context_provider = None
            logger.debug("MCP auth factory configured for test mode")

        elif settings.mcp_auth_mode == "dev":
            # Development mode: use dev user for all requests, no token validation
            from src.mcp_server.providers.dev import DevMCPAuthProvider

            self._auth_provider = None  # No FastMCP auth needed for dev
            self._well_known_routes = {}
            self._mcp_auth_context_provider = DevMCPAuthProvider()
            logger.info("MCP auth factory configured for development mode")

        else:
            # Production mode: use Auth0 OAuth provider
            from cryptography.fernet import Fernet
            from fastmcp.server.auth.providers.auth0 import Auth0Provider
            from key_value.aio.wrappers.encryption import FernetEncryptionWrapper

            from src.db import async_session_maker
            from src.mcp_server.providers.auth0 import Auth0MCPAuthProvider
            from src.mcp_server.storage import PostgreSQLMCPStorage

            # Initialize PostgreSQL storage backend for OAuth tokens
            postgres_storage = PostgreSQLMCPStorage(async_session_maker)

            # Wrap storage with encryption for security
            client_storage = FernetEncryptionWrapper(
                key_value=postgres_storage,
                fernet=Fernet(settings.mcp_oauth_storage_encryption_key.encode()),
            )

            # Configure Auth0 OAuth authentication
            # Users authenticate via browser redirect to Auth0 login page
            # Client credentials are stored server-side only (never distributed to users)
            # After initial login, tokens are cached locally on the user's machine
            # Tokens are persisted in PostgreSQL with encryption for security
            self._auth_provider = Auth0Provider(
                config_url=f"https://{settings.mcp_server_auth0_domain}/.well-known/openid-configuration",
                client_id=settings.mcp_server_auth0_client_id,
                client_secret=settings.mcp_server_auth0_client_secret,
                audience=settings.mcp_server_auth0_audience,
                base_url=f"{settings.mcp_server_domain}/mcp",
                issuer_url=f"{settings.mcp_server_domain}",
                jwt_signing_key=settings.mcp_oauth_jwt_signing_key,
                client_storage=client_storage,
            )

            self._well_known_routes = self._auth_provider.get_well_known_routes(
                mcp_path="/mcp"
            )
            self._mcp_auth_context_provider = Auth0MCPAuthProvider()
            logger.info("MCP auth factory configured for Auth0 production mode")

        self._initialized = True
        return (
            self._auth_provider,
            self._well_known_routes,
            self._mcp_auth_context_provider,
        )

    def get_auth_provider(self) -> Optional[Any]:
        """Get the FastMCP auth provider."""
        if not self._initialized:
            self.initialize()
        return self._auth_provider

    def get_mcp_auth_context_provider(self) -> Optional[MCPAuthProvider]:
        """Get the MCP auth context provider."""
        if not self._initialized:
            self.initialize()
        return self._mcp_auth_context_provider

    def get_well_known_routes(self) -> Dict[str, Any]:
        """Get OAuth well-known routes (empty if not using OAuth)."""
        if not self._initialized:
            self.initialize()
        return self._well_known_routes

    def reset(self) -> None:
        """Reset the factory to uninitialized state (for testing)."""
        self._auth_provider = None
        self._mcp_auth_context_provider = None
        self._well_known_routes = {}
        self._initialized = False
        logger.debug("MCP auth factory reset")


# Global factory instance
_mcp_auth_factory = MCPAuthFactory()


def get_mcp_auth_factory() -> MCPAuthFactory:
    """Get the global MCP auth factory instance."""
    return _mcp_auth_factory


def reset_mcp_auth_factory() -> None:
    """Reset the global MCP auth factory (primarily for testing)."""
    _mcp_auth_factory.reset()
