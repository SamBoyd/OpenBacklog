"""
DEPRECATED: This module is deprecated and will be removed in a future release.

Please use src.secrets.vault_factory.get_vault() instead to access the vault instance.
The vault abstraction layer in src.secrets now supports both HashiCorp Vault and
file-based storage for development environments.

Migration guide:
    Old: from src.key_vault import initialize_vault_client, retrieve_api_key_from_vault
    New: from src.secrets import get_vault
         vault = get_vault()
         api_key = vault.retrieve_api_key_from_vault(path)
"""

import base64
import logging
import os
import time
from typing import Optional, Tuple

import hvac
import sentry_sdk
from cryptography.fernet import Fernet
from hvac.exceptions import InvalidRequest, VaultError
from sqlalchemy import False_

from src.config import settings
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    set_operation_context,
    track_ai_metrics,
)

# For now, using hardcoded key (will be replaced with proper key management later)
# This is a valid Fernet key generated with Fernet.generate_key() and decoded to string

logger = logging.getLogger(__name__)
logger.warning(
    "src.key_vault is deprecated. Use src.secrets.vault_factory.get_vault() instead."
)

# Store client, expiry timestamp (UTC), and renewable status
_vault_client_details: Optional[Tuple[hvac.Client, float, bool]] = None
_RENEWAL_THRESHOLD_SECONDS = 900  # Renew 15 minutes before expiry
_vault_available = False  # Track vault availability


def _create_authenticated_client() -> Tuple[hvac.Client, float, bool]:
    """
    Creates an authenticated Vault client and returns client, expiry time, and renewable status.

    The function expects:
    1. RoleID to be delivered by Puppet to a file at settings.vault_role_id_path
    2. A wrapping token for SecretID to be available in VAULT_WRAPPING_TOKEN env var
       or a SecretID file at /etc/app/vault_secret_id

    Returns:
        Tuple[hvac.Client, float, bool]: Authenticated client, expiry timestamp, renewable status

    Raises:
        RuntimeError: If authentication fails
        ValueError: If required credentials cannot be found
    """
    try:
        # Create a client to connect to Vault
        client = hvac.Client(
            url=settings.vault_url,
            cert=(settings.vault_cert_path, settings.vault_cert_key_path),
            verify=settings.vault_verify_cert,
        )

        # Get role_id from file placed by Puppet
        if not os.path.exists(settings.vault_role_id_path):
            raise ValueError(f"RoleID file not found at {settings.vault_role_id_path}")

        with open(settings.vault_role_id_path, "r") as f:
            role_id = f.read().strip()

        if not role_id:
            raise ValueError("RoleID file exists but is empty")

        # Try to get SecretID from wrapping token first
        secret_id = None
        wrapping_token = os.environ.get("VAULT_WRAPPING_TOKEN")

        if wrapping_token:
            # Create a temporary client with the wrapping token
            temp_client = hvac.Client(url=settings.vault_url)
            temp_client.token = wrapping_token

            # Unwrap to get the secret_id
            try:
                unwrap_response = temp_client.sys.unwrap()
                secret_id = unwrap_response["data"]["secret_id"]
                logger.info("Successfully unwrapped SecretID from wrapping token")
            except Exception as e:
                logger.warning(f"Failed to unwrap SecretID: {str(e)}")

        # If no wrapping token or unwrapping failed, try the file
        if not secret_id:
            secret_id_path = settings.vault_secret_id_path
            if os.path.exists(secret_id_path):
                with open(secret_id_path, "r") as f:
                    secret_id = f.read().strip()
                logger.info("Retrieved SecretID from file")

        if not secret_id:
            raise ValueError("Could not obtain SecretID from wrapping token or file")

        # Authenticate using AppRole
        logger.info("Authenticating with Vault using AppRole")
        # Avoid logging secret_id in production environments if possible
        # logger.info(f"RoleID: {role_id}")
        # logger.info(f"SecretID: {secret_id[:4]}...") # Log only prefix if needed

        auth_response = client.auth.approle.login(role_id=role_id, secret_id=secret_id)

        if not client.is_authenticated():
            raise RuntimeError(f"Failed to authenticate with Vault: {auth_response}")

        lease_duration = auth_response["auth"]["lease_duration"]
        renewable = auth_response["auth"]["renewable"]
        # Calculate expiry time as UTC timestamp
        expiry_time = time.time() + lease_duration

        logger.info(
            f"Successfully authenticated. Token TTL: {lease_duration}s, Renewable: {renewable}"
        )
        return client, expiry_time, renewable
    except ValueError as ve:
        logger.error(f"Vault authentication credential error: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Failed to authenticate with Vault: {str(e)}")
        raise RuntimeError("Failed to authenticate with Vault") from e


def initialize_vault_client():
    """
    Initialize the Vault client and unwrap the token at startup.
    This function should be called during application startup to ensure
    the wrapping token is unwrapped early in the application lifecycle.

    This function will not raise exceptions - if vault initialization fails,
    it will log the error and mark vault as unavailable.
    """
    global _vault_client_details, _vault_available
    logger.info("Initializing Vault client at startup")
    try:
        _vault_client_details = _create_authenticated_client()
        _vault_available = True
        logger.info("Vault client successfully initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Vault client: {e}")
        _vault_available = False
        _vault_client_details = None
    # Note: In a real async app, you might start a background renewal task here


def get_vault_client() -> Optional[hvac.Client]:
    """
    Returns an authenticated Vault client, attempting renewal if close to expiry.
    Returns None if vault is unavailable.

    Returns:
        Optional[hvac.Client]: An authenticated Vault client, or None if unavailable.
    """
    global _vault_client_details, _vault_available

    # If vault was marked as unavailable, don't try to reconnect
    if not _vault_available:
        return None

    current_time = time.time()

    # Case 1: No client or client explicitly logged out/token revoked externally
    if _vault_client_details is None or not _vault_client_details[0].is_authenticated():
        logger.info(
            "Vault client not authenticated or not initialized. Re-authenticating."
        )
        try:
            _vault_client_details = _create_authenticated_client()
            _vault_available = True
            return _vault_client_details[0]
        except (RuntimeError, ValueError) as e:
            logger.error(f"Failed to re-authenticate Vault client: {e}")
            _vault_available = False
            return None

    client, expiry_time, renewable = _vault_client_details

    # Case 2: Token has expired
    if current_time >= expiry_time:
        logger.info("Vault token has expired. Re-authenticating.")
        try:
            _vault_client_details = _create_authenticated_client()
            _vault_available = True
            return _vault_client_details[0]
        except (RuntimeError, ValueError) as e:
            logger.error(f"Failed to re-authenticate Vault client after expiry: {e}")
            _vault_available = False
            return None

    # Case 3: Token is nearing expiry and is renewable
    if renewable and (expiry_time - current_time) < _RENEWAL_THRESHOLD_SECONDS:
        logger.info("Vault token nearing expiry. Attempting renewal.")
        try:
            renew_response = client.auth.token.renew_self()
            new_lease_duration = renew_response["auth"]["lease_duration"]
            new_expiry_time = time.time() + new_lease_duration
            new_renewable = renew_response["auth"]["renewable"]
            _vault_client_details = (client, new_expiry_time, new_renewable)
            logger.info(
                f"Vault token successfully renewed. New TTL: {new_lease_duration}s, Renewable: {new_renewable}"
            )
        except InvalidRequest as e:
            # Common if max_ttl is reached or token is no longer renewable
            logger.warning(
                f"Vault token renewal failed (possibly max_ttl reached or token revoked): {str(e)}"
            )
            # Mark token non-renewable in our state to prevent further attempts
            _vault_client_details = (client, expiry_time, False)
        except VaultError as e:
            logger.error(f"Vault token renewal failed due to Vault error: {str(e)}")
            # Keep current client, rely on expiry check next time or re-auth
        except Exception as e:
            logger.error(f"Unexpected error during Vault token renewal: {str(e)}")
            # Keep current client, rely on expiry check next time or re-auth

    # Return the current client (potentially after successful renewal or if no action needed)
    # Ensure we always return the client object from the tuple
    return _vault_client_details[0]


def store_api_key_in_vault(path: str, key: str) -> Optional[str]:
    """
    Stores an API key in HashiCorp Vault's KV secret store.

    Args:
        path (str): The path in Vault where the API key should be stored.
        key (str): The API key to store (can be plaintext or encrypted).

    Returns:
        Optional[str]: The path where the API key was stored, or None if vault unavailable.

    Raises:
        ValueError: If path or key is empty or None.
        TypeError: If inputs are not strings.
        RuntimeError: If storing in Vault fails.
    """
    if not isinstance(path, str) or not isinstance(key, str):
        raise TypeError("Path and API key must be strings")

    if not path or not key:
        raise ValueError("Path and API key cannot be empty")

    try:
        # Get an authenticated client
        vault_client = get_vault_client()

        if vault_client is None:
            logger.warning(f"Vault unavailable, cannot store API key at path: {path}")
            return None

        if not vault_client.is_authenticated():
            raise RuntimeError("Vault client is not authenticated")

        # Store the key in the KV secrets engine
        vault_client.secrets.kv.v2.create_or_update_secret(
            path=path, secret={"api_key": key}
        )

        logger.info(f"API key successfully stored at path: {path}")
        return path

    except VaultError as ve:
        logger.error(f"Vault operation failed: {str(ve)}")
        raise RuntimeError(f"Failed to store API key in Vault: {str(ve)}") from ve
    except Exception as e:
        logger.error(f"Unexpected error storing API key in Vault: {str(e)}")
        raise RuntimeError(
            f"Failed to store API key in Vault due to an unexpected error"
        ) from e


def retrieve_api_key_from_vault(vault_path: str) -> Optional[str]:
    """
    Retrieves an API key from HashiCorp Vault's KV secret store.

    Args:
        vault_path (str): The path in Vault where the API key is stored.

    Returns:
        Optional[str]: The retrieved API key, or None if vault unavailable.

    Raises:
        ValueError: If the vault_path is empty or None.
        TypeError: If the input is not a string.
        VaultError: If retrieval from Vault fails or key not found.
    """
    if not isinstance(vault_path, str):
        raise TypeError("Vault path must be a string")

    if not vault_path:
        raise ValueError("Vault path cannot be empty")

    try:
        # Get an authenticated client
        vault_client = get_vault_client()

        if vault_client is None:
            logger.warning(
                f"Vault unavailable, cannot retrieve API key from path: {vault_path}"
            )
            return None

        # Retrieve the secret from the KV secrets engine
        secret_response = vault_client.secrets.kv.v2.read_secret_version(
            path=vault_path
        )

        # Extract the API key from the response
        if "data" not in secret_response or "data" not in secret_response["data"]:
            raise KeyError(f"No data found at path: {vault_path}")

        secret_data = secret_response["data"]["data"]
        if "api_key" not in secret_data:
            raise KeyError(f"No API key found at path: {vault_path}")

        return secret_data["api_key"]

    except VaultError as ve:
        logger.error(f"Vault operation failed: {str(ve)}")
        add_breadcrumb(
            "Vault operation failed",
            category="vault.api_key",
            level="error",
            data={"vault_path": vault_path, "error": str(ve)},
        )

        set_operation_context(
            "vault_retrieve_api_key", {"vault_path": vault_path}, success=False
        )
        track_ai_metrics(
            "vault.api_key_retrieval.vault_error",
            1,
            tags={"vault_path": vault_path[:20]},
        )

        capture_ai_exception(
            ve,
            operation_type="vault_api_key_retrieval",
            extra_context={"vault_path": vault_path, "error_type": "vault_error"},
        )

        raise VaultError(
            "Could not retrieve your OpenAI API key. Please update your API key in the settings."
        ) from ve
    except KeyError as ke:
        logger.error(f"API key not found: {str(ke)}")
        add_breadcrumb(
            "API key not found in vault",
            category="vault.api_key",
            level="error",
            data={"vault_path": vault_path, "key_error": str(ke)},
        )

        set_operation_context(
            "vault_retrieve_api_key", {"vault_path": vault_path}, success=False
        )
        track_ai_metrics(
            "vault.api_key_retrieval.key_not_found",
            1,
            tags={"vault_path": vault_path[:20]},
        )

        capture_ai_exception(
            ke,
            operation_type="vault_api_key_retrieval",
            extra_context={"vault_path": vault_path, "error_type": "key_not_found"},
        )

        raise VaultError(
            "Could not retrieve your OpenAI API key. Please update your API key in the settings."
        ) from ke
    except Exception as e:
        logger.error(f"Unexpected error retrieving API key from Vault: {str(e)}")
        add_breadcrumb(
            "Unexpected vault error",
            category="vault.api_key",
            level="error",
            data={
                "vault_path": vault_path,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )

        set_operation_context(
            "vault_retrieve_api_key", {"vault_path": vault_path}, success=False
        )
        track_ai_metrics(
            "vault.api_key_retrieval.unexpected_error",
            1,
            tags={"vault_path": vault_path[:20], "error_type": type(e).__name__},
        )

        capture_ai_exception(
            e,
            operation_type="vault_api_key_retrieval",
            extra_context={"vault_path": vault_path, "error_type": "unexpected_error"},
        )

        raise VaultError(
            "Could not retrieve your OpenAI API key. Please update your API key in the settings."
        ) from e
