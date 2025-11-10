"""HashiCorp Vault implementation of the vault interface."""

import logging
import os
import time
from typing import Optional, Tuple

import hvac
from hvac.exceptions import InvalidRequest, VaultError

from src.config import settings
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    set_operation_context,
    track_ai_metrics,
)
from src.secrets.vault_interface import VaultInterface

logger = logging.getLogger(__name__)

# Store client, expiry timestamp (UTC), and renewable status
_vault_client_details: Optional[Tuple[hvac.Client, float, bool]] = None
_RENEWAL_THRESHOLD_SECONDS = 900  # Renew 15 minutes before expiry


class HashicorpVault(VaultInterface):
    """HashiCorp Vault implementation."""

    def __init__(self):
        """Initialize the HashiCorp vault instance."""
        self._vault_available = False
        self._vault_client_details: Optional[Tuple[hvac.Client, float, bool]] = None

    def initialize(self) -> None:
        """
        Initialize the Vault client and authenticate at startup.
        Does not raise exceptions - logs errors and marks vault as unavailable.
        """
        logger.info("Initializing HashiCorp Vault client at startup")
        try:
            self._vault_client_details = self._create_authenticated_client()
            self._vault_available = True
            logger.info("HashiCorp Vault client successfully initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            self._vault_available = False
            self._vault_client_details = None

    def is_available(self) -> bool:
        """Check if vault is available and authenticated."""
        return self._vault_available

    def _create_authenticated_client(self) -> Tuple[hvac.Client, float, bool]:
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
                raise ValueError(
                    f"RoleID file not found at {settings.vault_role_id_path}"
                )

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
                raise ValueError(
                    "Could not obtain SecretID from wrapping token or file"
                )

            # Authenticate using AppRole
            logger.info("Authenticating with Vault using AppRole")
            auth_response = client.auth.approle.login(
                role_id=role_id, secret_id=secret_id
            )

            if not client.is_authenticated():
                raise RuntimeError(
                    f"Failed to authenticate with Vault: {auth_response}"
                )

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

    def _get_vault_client(self) -> Optional[hvac.Client]:
        """
        Returns an authenticated Vault client, attempting renewal if close to expiry.
        Returns None if vault is unavailable.

        Returns:
            Optional[hvac.Client]: An authenticated Vault client, or None if unavailable.
        """
        # If vault was marked as unavailable, don't try to reconnect
        if not self._vault_available:
            return None

        current_time = time.time()

        # Case 1: No client or client explicitly logged out/token revoked externally
        if (
            self._vault_client_details is None
            or not self._vault_client_details[0].is_authenticated()
        ):
            logger.info(
                "Vault client not authenticated or not initialized. Re-authenticating."
            )
            try:
                self._vault_client_details = self._create_authenticated_client()
                self._vault_available = True
                return self._vault_client_details[0]
            except (RuntimeError, ValueError) as e:
                logger.error(f"Failed to re-authenticate Vault client: {e}")
                self._vault_available = False
                return None

        client, expiry_time, renewable = self._vault_client_details

        # Case 2: Token has expired
        if current_time >= expiry_time:
            logger.info("Vault token has expired. Re-authenticating.")
            try:
                self._vault_client_details = self._create_authenticated_client()
                self._vault_available = True
                return self._vault_client_details[0]
            except (RuntimeError, ValueError) as e:
                logger.error(
                    f"Failed to re-authenticate Vault client after expiry: {e}"
                )
                self._vault_available = False
                return None

        # Case 3: Token is nearing expiry and is renewable
        if renewable and (expiry_time - current_time) < _RENEWAL_THRESHOLD_SECONDS:
            logger.info("Vault token nearing expiry. Attempting renewal.")
            try:
                renew_response = client.auth.token.renew_self()
                new_lease_duration = renew_response["auth"]["lease_duration"]
                new_expiry_time = time.time() + new_lease_duration
                new_renewable = renew_response["auth"]["renewable"]
                self._vault_client_details = (client, new_expiry_time, new_renewable)
                logger.info(
                    f"Vault token successfully renewed. New TTL: {new_lease_duration}s, Renewable: {new_renewable}"
                )
            except InvalidRequest as e:
                # Common if max_ttl is reached or token is no longer renewable
                logger.warning(
                    f"Vault token renewal failed (possibly max_ttl reached or token revoked): {str(e)}"
                )
                # Mark token non-renewable in our state to prevent further attempts
                self._vault_client_details = (client, expiry_time, False)
            except VaultError as e:
                logger.error(f"Vault token renewal failed due to Vault error: {str(e)}")
                # Keep current client, rely on expiry check next time or re-auth
            except Exception as e:
                logger.error(f"Unexpected error during Vault token renewal: {str(e)}")
                # Keep current client, rely on expiry check next time or re-auth

        # Return the current client (potentially after successful renewal or if no action needed)
        return self._vault_client_details[0]

    def store_secret(self, path: str, value: dict) -> Optional[str]:
        """
        Store a secret in HashiCorp Vault's KV secret store.

        Args:
            path (str): The path in Vault where the secret should be stored.
            value (dict): The secret value as a dictionary.

        Returns:
            Optional[str]: The path where the secret was stored, or None if vault unavailable.

        Raises:
            ValueError: If path or value is empty or None.
            TypeError: If inputs are not correct types.
            RuntimeError: If storing in Vault fails.
        """
        if not isinstance(path, str) or not isinstance(value, dict):
            raise TypeError("Path must be string and value must be dict")

        if not path or not value:
            raise ValueError("Path and value cannot be empty")

        try:
            vault_client = self._get_vault_client()

            if vault_client is None:
                logger.warning(
                    f"Vault unavailable, cannot store secret at path: {path}"
                )
                return None

            if not vault_client.is_authenticated():
                raise RuntimeError("Vault client is not authenticated")

            # Store the secret in the KV secrets engine
            vault_client.secrets.kv.v2.create_or_update_secret(path=path, secret=value)

            logger.info(f"Secret successfully stored at path: {path}")
            return path

        except Exception as e:
            logger.error(f"Failed to store secret in Vault: {str(e)}")
            raise RuntimeError(f"Failed to store secret in Vault: {str(e)}") from e

    def retrieve_secret(self, path: str) -> Optional[dict]:
        """
        Retrieve a secret from HashiCorp Vault's KV secret store.

        Args:
            path (str): The path in Vault where the secret is stored.

        Returns:
            Optional[dict]: The secret value as a dictionary, or None if vault unavailable.

        Raises:
            ValueError: If path is empty or None.
            TypeError: If input is not correct type.
            RuntimeError: If retrieval from Vault fails.
        """
        if not isinstance(path, str):
            raise TypeError("Vault path must be a string")

        if not path:
            raise ValueError("Vault path cannot be empty")

        try:
            vault_client = self._get_vault_client()

            if vault_client is None:
                logger.warning(
                    f"Vault unavailable, cannot retrieve secret from path: {path}"
                )
                return None

            # Retrieve the secret from the KV secrets engine
            secret_response = vault_client.secrets.kv.v2.read_secret_version(path=path)

            # Extract the secret from the response
            if "data" not in secret_response or "data" not in secret_response["data"]:
                raise KeyError(f"No data found at path: {path}")

            secret_data = secret_response["data"]["data"]
            return secret_data

        except VaultError as ve:
            logger.error(f"Vault operation failed: {str(ve)}")
            add_breadcrumb(
                "Vault operation failed",
                category="vault.retrieve",
                level="error",
                data={"path": path, "error": str(ve)},
            )

            set_operation_context(
                "vault_retrieve_secret", {"path": path}, success=False
            )
            track_ai_metrics(
                "vault.secret_retrieval.vault_error",
                1,
                tags={"path": path[:20]},
            )

            capture_ai_exception(
                ve,
                operation_type="vault_secret_retrieval",
                extra_context={"path": path, "error_type": "vault_error"},
            )

            raise RuntimeError(
                f"Failed to retrieve secret from Vault: {str(ve)}"
            ) from ve
        except KeyError as ke:
            logger.error(f"Secret not found: {str(ke)}")
            add_breadcrumb(
                "Secret not found in vault",
                category="vault.retrieve",
                level="error",
                data={"path": path, "key_error": str(ke)},
            )

            set_operation_context(
                "vault_retrieve_secret", {"path": path}, success=False
            )
            track_ai_metrics(
                "vault.secret_retrieval.key_not_found",
                1,
                tags={"path": path[:20]},
            )

            capture_ai_exception(
                ke,
                operation_type="vault_secret_retrieval",
                extra_context={"path": path, "error_type": "key_not_found"},
            )

            raise RuntimeError(
                f"Failed to retrieve secret from Vault: {str(ke)}"
            ) from ke
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret from Vault: {str(e)}")
            add_breadcrumb(
                "Unexpected vault error",
                category="vault.retrieve",
                level="error",
                data={
                    "path": path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            set_operation_context(
                "vault_retrieve_secret", {"path": path}, success=False
            )
            track_ai_metrics(
                "vault.secret_retrieval.unexpected_error",
                1,
                tags={"path": path[:20], "error_type": type(e).__name__},
            )

            capture_ai_exception(
                e,
                operation_type="vault_secret_retrieval",
                extra_context={"path": path, "error_type": "unexpected_error"},
            )

            raise RuntimeError(f"Failed to retrieve secret from Vault: {str(e)}") from e
