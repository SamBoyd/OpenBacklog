"""File-based vault implementation for development environments."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from src.secrets.vault_interface import VaultInterface

logger = logging.getLogger(__name__)


class FileVault(VaultInterface):
    """File-based secret storage for development environments."""

    def __init__(self, secrets_dir: str = "/app/secrets"):
        """
        Initialize the file-based vault.

        Args:
            secrets_dir (str): Directory where secrets will be stored.
        """
        self.secrets_dir = Path(secrets_dir)
        self._available = False

    def initialize(self) -> None:
        """
        Initialize the file vault by creating the secrets directory.
        Does not raise exceptions - logs errors and marks as unavailable.
        """
        logger.info(f"Initializing file-based vault at {self.secrets_dir}")
        try:
            self.secrets_dir.mkdir(parents=True, exist_ok=True)
            self._available = True
            logger.info("File-based vault successfully initialized")
        except Exception as e:
            logger.error(f"Failed to initialize file vault: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if vault is available."""
        return self._available

    def _get_secret_file_path(self, path: str) -> Path:
        """
        Convert a vault path to a file path.

        Vault paths use forward slashes (e.g., "secret/data/user-id/api_keys/openai")
        File paths replace slashes with nested directories and add .json extension.

        Args:
            path (str): The vault path.

        Returns:
            Path: The file system path.
        """
        # Convert vault path to file path
        # secret/data/user-id/api_keys/openai -> secret/data/user-id/api_keys/openai.json
        file_path = self.secrets_dir / f"{path}.json"
        return file_path

    def store_secret(self, path: str, value: dict) -> Optional[str]:
        """
        Store a secret in a JSON file.

        Args:
            path (str): The path where the secret should be stored.
            value (dict): The secret value as a dictionary.

        Returns:
            Optional[str]: The path where the secret was stored, or None if unavailable.

        Raises:
            ValueError: If path or value is empty/invalid.
            TypeError: If inputs are not correct types.
            RuntimeError: If storing fails.
        """
        if not isinstance(path, str) or not isinstance(value, dict):
            raise TypeError("Path must be string and value must be dict")

        if not path or not value:
            raise ValueError("Path and value cannot be empty")

        if not self._available:
            logger.warning(
                f"File vault unavailable, cannot store secret at path: {path}"
            )
            return None

        try:
            file_path = self._get_secret_file_path(path)

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the secret to file as JSON
            with open(file_path, "w") as f:
                json.dump(value, f, indent=2)

            logger.info(f"Secret successfully stored at path: {path}")
            return path

        except Exception as e:
            logger.error(f"Failed to store secret in file vault: {str(e)}")
            raise RuntimeError(f"Failed to store secret in file vault: {str(e)}") from e

    def retrieve_secret(self, path: str) -> Optional[dict]:
        """
        Retrieve a secret from a JSON file.

        Args:
            path (str): The path where the secret is stored.

        Returns:
            Optional[dict]: The secret value as a dictionary, or None if unavailable.

        Raises:
            ValueError: If path is empty/invalid.
            TypeError: If input is not correct type.
            RuntimeError: If retrieval fails.
        """
        if not isinstance(path, str):
            raise TypeError("Vault path must be a string")

        if not path:
            raise ValueError("Vault path cannot be empty")

        if not self._available:
            logger.warning(
                f"File vault unavailable, cannot retrieve secret from path: {path}"
            )
            return None

        try:
            file_path = self._get_secret_file_path(path)

            # Check if file exists
            if not file_path.exists():
                raise KeyError(f"No secret found at path: {path}")

            # Read the secret from file
            with open(file_path, "r") as f:
                secret_data = json.load(f)

            logger.info(f"Secret successfully retrieved from path: {path}")
            return secret_data

        except FileNotFoundError as e:
            logger.error(f"Secret file not found: {str(e)}")
            raise RuntimeError(f"Secret not found at path: {path}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode secret JSON: {str(e)}")
            raise RuntimeError(f"Invalid JSON in secret file at path: {path}") from e
        except Exception as e:
            logger.error(f"Failed to retrieve secret from file vault: {str(e)}")
            raise RuntimeError(
                f"Failed to retrieve secret from file vault: {str(e)}"
            ) from e
