"""Abstract base class for vault implementations."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class VaultInterface(ABC):
    """Abstract interface for secret storage backends."""

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the vault connection and authenticate if needed.

        Should handle all setup, authentication, and connection initialization.
        Should not raise exceptions - log errors and mark as unavailable instead.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if vault is available and ready to use.

        Returns:
            bool: True if vault is available, False otherwise.
        """
        pass

    @abstractmethod
    def store_secret(self, path: str, value: dict) -> Optional[str]:
        """
        Store a secret at the given path.

        Args:
            path (str): The path where the secret should be stored (e.g., "secret/data/{user_id}/api_keys/openai")
            value (dict): The secret value as a dictionary (e.g., {"api_key": "sk-..."})

        Returns:
            Optional[str]: The path where the secret was stored, or None if vault unavailable.

        Raises:
            ValueError: If path or value is empty/invalid.
            TypeError: If inputs are not correct types.
            RuntimeError: If storing fails (wrapped from backend-specific exceptions).
        """
        pass

    @abstractmethod
    def retrieve_secret(self, path: str) -> Optional[dict]:
        """
        Retrieve a secret from the given path.

        Args:
            path (str): The path where the secret is stored.

        Returns:
            Optional[dict]: The secret value as a dictionary, or None if vault unavailable.

        Raises:
            ValueError: If path is empty/invalid.
            TypeError: If input is not correct type.
            RuntimeError: If retrieval fails (wrapped from backend-specific exceptions).
        """
        pass

    # Convenience methods for API key storage (backward compatibility)

    def store_api_key_in_vault(self, path: str, key: str) -> Optional[str]:
        """
        Store an API key in vault (convenience wrapper).

        Args:
            path (str): The path in vault where the API key should be stored.
            key (str): The API key to store.

        Returns:
            Optional[str]: The path where the API key was stored, or None if vault unavailable.
        """
        return self.store_secret(path, {"api_key": key})

    def retrieve_api_key_from_vault(self, vault_path: str) -> Optional[str]:
        """
        Retrieve an API key from vault (convenience wrapper).

        Args:
            vault_path (str): The path in vault where the API key is stored.

        Returns:
            Optional[str]: The retrieved API key, or None if vault unavailable.
        """
        secret = self.retrieve_secret(vault_path)
        if secret is None:
            return None
        return secret.get("api_key")
