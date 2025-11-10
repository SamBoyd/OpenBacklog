"""Factory for creating and managing vault instances."""

import logging
from typing import Optional

from src.secrets.vault_interface import VaultInterface

logger = logging.getLogger(__name__)

# Global vault instance (singleton)
_vault_instance: Optional[VaultInterface] = None


def get_vault() -> VaultInterface:
    """
    Get or create the vault instance based on environment configuration.

    Returns the appropriate vault implementation (HashiCorp or file-based)
    based on the VAULT_TYPE environment variable and production safety checks.

    Returns:
        VaultInterface: The vault instance.

    Raises:
        RuntimeError: If file vault is used in production environment.
    """
    global _vault_instance

    if _vault_instance is not None:
        return _vault_instance

    from src.config import settings

    vault_type = settings.vault_type.lower()

    # Production safety guard
    if vault_type == "file" and settings.environment == "production":
        raise RuntimeError(
            "File-based vault cannot be used in production. "
            "Set VAULT_TYPE=hashicorp for production environments."
        )

    if vault_type == "file":
        logger.info("Creating file-based vault instance")
        from src.secrets.file_vault import FileVault

        _vault_instance = FileVault(secrets_dir=settings.secrets_dir)
    elif vault_type == "hashicorp":
        logger.info("Creating HashiCorp Vault instance")
        from src.secrets.hashicorp_vault import HashicorpVault

        _vault_instance = HashicorpVault()
    else:
        raise ValueError(
            f"Unknown vault type: {vault_type}. Must be 'hashicorp' or 'file'."
        )

    # Initialize the vault
    _vault_instance.initialize()

    return _vault_instance


def reset_vault() -> None:
    """
    Reset the global vault instance.

    Useful for testing to switch between vault types.
    """
    global _vault_instance
    _vault_instance = None
