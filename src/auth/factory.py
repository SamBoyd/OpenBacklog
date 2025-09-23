"""
Authentication provider factory.
"""

import logging
from typing import Literal, Optional

from src.config import settings

from .providers import Auth0Provider, AuthProvider, DevAuthProvider, SimpleAuthProvider

logger = logging.getLogger(__name__)

# Auth provider type
AuthProviderType = Literal["auth0", "simple", "dev"]


class AuthProviderFactory:
    """Factory for creating authentication providers."""

    _instance: Optional[AuthProvider] = None
    _provider_type: Optional[AuthProviderType] = None

    @classmethod
    def get_provider(
        cls, provider_type: Optional[AuthProviderType] = None
    ) -> AuthProvider:
        """
        Get the authentication provider instance.

        Args:
            provider_type: Type of provider to create. If None, determines from settings.

        Returns:
            AuthProvider instance

        Raises:
            ValueError: If provider type is invalid or configuration is missing
        """
        # Determine provider type if not specified
        if provider_type is None:
            provider_type = cls._determine_provider_type()

        # Return cached instance if same type
        if cls._instance is not None and cls._provider_type == provider_type:
            return cls._instance

        # Create new provider instance
        cls._instance = cls._create_provider(provider_type)
        cls._provider_type = provider_type

        logger.info(f"Created auth provider: {provider_type}")
        return cls._instance

    @classmethod
    def _determine_provider_type(cls) -> AuthProviderType:
        """Determine provider type from settings."""
        # Check if we have an explicit auth_provider setting
        provider_setting = getattr(settings, "auth_provider", "auto")

        if provider_setting != "auto":
            # Explicit provider specified
            if provider_setting in ["auth0", "simple", "dev"]:
                return provider_setting
            else:
                logger.warning(
                    f"Unknown auth_provider '{provider_setting}', falling back to auto-detection"
                )

        # Auto-detect provider based on environment
        if settings.environment == "development":
            return "dev"

        # Check if Auth0 is configured (all required settings present and non-empty)
        if all(
            [
                getattr(settings, "auth0_client_id", "") != "",
                getattr(settings, "auth0_client_secret", "") != "",
                getattr(settings, "auth0_domain", "") != "",
            ]
        ):
            return "auth0"

        # Default to simple auth for open source deployments
        return "simple"

    @classmethod
    def _create_provider(cls, provider_type: AuthProviderType) -> AuthProvider:
        """Create provider instance of specified type."""
        if provider_type == "auth0":
            return Auth0Provider()
        elif provider_type == "simple":
            return SimpleAuthProvider()
        elif provider_type == "dev":
            return DevAuthProvider()
        else:
            raise ValueError(f"Unknown auth provider type: {provider_type}")

    @classmethod
    def reset(cls):
        """Reset the factory (for testing)."""
        cls._instance = None
        cls._provider_type = None

    @classmethod
    def get_provider_type(cls) -> Optional[AuthProviderType]:
        """Get the current provider type."""
        if cls._provider_type is None:
            cls._provider_type = cls._determine_provider_type()
        return cls._provider_type

    @classmethod
    def is_oauth_provider(cls) -> bool:
        """Check if current provider uses OAuth flow."""
        provider_type = cls.get_provider_type()
        return provider_type == "auth0"

    @classmethod
    def supports_registration(cls) -> bool:
        """Check if current provider supports user registration."""
        provider_type = cls.get_provider_type()
        return provider_type in ["simple", "dev"]

    @classmethod
    def supports_password_auth(cls) -> bool:
        """Check if current provider supports password authentication."""
        provider_type = cls.get_provider_type()
        return provider_type in ["simple", "dev"]


def get_auth_provider() -> AuthProvider:
    """
    Convenience function to get the current auth provider.

    Returns:
        AuthProvider instance
    """
    return AuthProviderFactory.get_provider()


def get_provider_type() -> AuthProviderType:
    """
    Get the current auth provider type.

    Returns:
        Current provider type
    """
    return AuthProviderFactory.get_provider_type()


def is_oauth_flow() -> bool:
    """
    Check if current auth provider uses OAuth flow.

    Returns:
        True if OAuth provider, False otherwise
    """
    return AuthProviderFactory.is_oauth_provider()


def supports_registration() -> bool:
    """
    Check if current provider supports user registration.

    Returns:
        True if registration is supported
    """
    return AuthProviderFactory.supports_registration()


def supports_password_auth() -> bool:
    """
    Check if current provider supports password authentication.

    Returns:
        True if password auth is supported
    """
    return AuthProviderFactory.supports_password_auth()
