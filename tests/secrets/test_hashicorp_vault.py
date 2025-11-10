"""Unit tests for src.secrets.hashicorp_vault module."""

import logging
import os
import time
from typing import Optional, Tuple
from unittest.mock import MagicMock, Mock, patch

import hvac
import pytest
from hvac.exceptions import InvalidRequest, VaultError

from src.secrets.hashicorp_vault import HashicorpVault


class TestHashicorpVaultInitialization:
    """Tests for HashicorpVault initialization."""

    def test_hashicorp_vault_constructor(self):
        """Test that HashicorpVault constructor initializes correctly."""
        vault = HashicorpVault()

        assert vault is not None
        assert isinstance(vault, HashicorpVault)
        assert vault._vault_available is False
        assert vault._vault_client_details is None

    def test_hashicorp_vault_implements_vault_interface(self):
        """Test that HashicorpVault implements VaultInterface."""
        from src.secrets.vault_interface import VaultInterface

        vault = HashicorpVault()
        assert isinstance(vault, VaultInterface)

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_initialize_success(self, mock_create_client):
        """Test successful initialization of Vault client."""
        mock_client = MagicMock()
        mock_expiry = time.time() + 3600
        mock_renewable = True
        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        vault = HashicorpVault()
        vault.initialize()

        assert vault._vault_available is True
        assert vault._vault_client_details is not None
        mock_create_client.assert_called_once()

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_initialize_logs_success(self, mock_create_client, caplog):
        """Test that initialize logs success message."""
        mock_client = MagicMock()
        mock_expiry = time.time() + 3600
        mock_renewable = True
        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        vault = HashicorpVault()
        with caplog.at_level(logging.INFO):
            vault.initialize()

        assert "successfully initialized" in caplog.text.lower()

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_initialize_handles_exception(self, mock_create_client):
        """Test that initialize handles exceptions gracefully."""
        mock_create_client.side_effect = RuntimeError("Connection failed")

        vault = HashicorpVault()
        vault.initialize()

        assert vault._vault_available is False
        assert vault._vault_client_details is None

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_initialize_logs_error(self, mock_create_client, caplog):
        """Test that initialize logs error when client creation fails."""
        mock_create_client.side_effect = RuntimeError("Connection failed")

        vault = HashicorpVault()
        with caplog.at_level(logging.ERROR):
            vault.initialize()

        assert "failed" in caplog.text.lower()


class TestHashicorpVaultCreateAuthenticatedClient:
    """Tests for _create_authenticated_client method."""

    @patch("src.secrets.hashicorp_vault.hvac.Client")
    @patch("src.secrets.hashicorp_vault.os.path.exists")
    @patch("builtins.open", create=True)
    @patch("src.config.settings")
    def test_create_authenticated_client_success(
        self, mock_settings, mock_open, mock_exists, mock_hvac_client
    ):
        """Test successful creation of authenticated Vault client."""
        # Setup mock configuration
        mock_settings.vault_url = "https://vault.example.com"
        mock_settings.vault_cert_path = "/path/to/cert.pem"
        mock_settings.vault_cert_key_path = "/path/to/key.pem"
        mock_settings.vault_verify_cert = True
        mock_settings.vault_role_id_path = "/path/to/role_id"
        mock_settings.vault_secret_id_path = "/path/to/secret_id"

        # Setup mock client and file reading
        mock_client = MagicMock()
        mock_hvac_client.return_value = mock_client
        mock_exists.return_value = True

        # Mock file reads
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.return_value.read.side_effect = [
            "test-role-id",
            "test-secret-id",
        ]
        mock_open.return_value = mock_file_handle

        # Mock authentication response
        mock_client.is_authenticated.return_value = True
        mock_client.auth.approle.login.return_value = {
            "auth": {
                "lease_duration": 3600,
                "renewable": True,
            }
        }

        # Call method
        vault = HashicorpVault()
        client, expiry, renewable = vault._create_authenticated_client()

        # Assert
        assert client == mock_client
        assert isinstance(expiry, float)
        assert expiry > time.time()
        assert renewable is True
        mock_client.auth.approle.login.assert_called_once()

    @patch("src.config.settings")
    def test_create_authenticated_client_missing_role_id_file(self, mock_settings):
        """Test error when role_id file is missing."""
        mock_settings.vault_url = "https://vault.example.com"
        mock_settings.vault_role_id_path = "/nonexistent/role_id"

        with patch("src.secrets.hashicorp_vault.os.path.exists", return_value=False):
            vault = HashicorpVault()
            with pytest.raises(ValueError) as exc_info:
                vault._create_authenticated_client()

            assert "RoleID file not found" in str(exc_info.value)

    @patch("src.secrets.hashicorp_vault.os.path.exists", return_value=True)
    @patch("builtins.open", create=True)
    @patch("src.config.settings")
    def test_create_authenticated_client_empty_role_id(
        self, mock_settings, mock_open, mock_exists
    ):
        """Test error when role_id file is empty."""
        mock_settings.vault_url = "https://vault.example.com"
        mock_settings.vault_role_id_path = "/path/to/role_id"

        # Mock empty file read
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.return_value.read.return_value = ""
        mock_open.return_value = mock_file_handle

        vault = HashicorpVault()
        with pytest.raises(ValueError) as exc_info:
            vault._create_authenticated_client()

        assert "RoleID file exists but is empty" in str(exc_info.value)

    @patch("src.secrets.hashicorp_vault.hvac.Client")
    @patch("src.secrets.hashicorp_vault.os.path.exists")
    @patch("builtins.open", create=True)
    @patch("src.config.settings")
    def test_create_authenticated_client_missing_secret_id(
        self, mock_settings, mock_open, mock_exists, mock_hvac_client
    ):
        """Test error when both wrapping token and secret_id file are missing."""
        mock_settings.vault_url = "https://vault.example.com"
        mock_settings.vault_role_id_path = "/path/to/role_id"
        mock_settings.vault_secret_id_path = "/path/to/secret_id"

        # Mock file exists for role_id but not for secret_id
        mock_exists.side_effect = [True, False]

        # Mock file read for role_id
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.return_value.read.return_value = "test-role-id"
        mock_open.return_value = mock_file_handle

        # No wrapping token env var
        with patch.dict(os.environ, {}, clear=True):
            vault = HashicorpVault()
            with pytest.raises(ValueError) as exc_info:
                vault._create_authenticated_client()

            assert "Could not obtain SecretID" in str(exc_info.value)

    @patch("src.secrets.hashicorp_vault.hvac.Client")
    @patch("src.secrets.hashicorp_vault.os.path.exists")
    @patch("builtins.open", create=True)
    @patch("src.config.settings")
    def test_create_authenticated_client_with_wrapping_token(
        self, mock_settings, mock_open, mock_exists, mock_hvac_client
    ):
        """Test client creation with wrapping token for SecretID."""
        mock_settings.vault_url = "https://vault.example.com"
        mock_settings.vault_cert_path = "/path/to/cert.pem"
        mock_settings.vault_cert_key_path = "/path/to/key.pem"
        mock_settings.vault_verify_cert = True
        mock_settings.vault_role_id_path = "/path/to/role_id"
        mock_settings.vault_secret_id_path = "/path/to/secret_id"

        # Create a single mock client for both temp and permanent use
        mock_client = MagicMock()
        mock_hvac_client.return_value = mock_client

        # Mock file operations - role_id exists, secret_id doesn't
        # First call checks role_id (returns True), second call checks secret_id (returns False)
        mock_exists.side_effect = [True, False]
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.return_value.read.return_value = "test-role-id"
        mock_open.return_value = mock_file_handle

        # Mock wrapping token unwrap
        mock_client.sys.unwrap.return_value = {"data": {"secret_id": "test-secret-id"}}

        # Mock authentication
        mock_client.is_authenticated.return_value = True
        mock_client.auth.approle.login.return_value = {
            "auth": {
                "lease_duration": 3600,
                "renewable": True,
            }
        }

        # Set wrapping token env var
        with patch.dict(os.environ, {"VAULT_WRAPPING_TOKEN": "test-wrapping-token"}):
            vault = HashicorpVault()
            client, expiry, renewable = vault._create_authenticated_client()

            # Verify we got a valid authenticated client
            assert client is not None
            assert isinstance(expiry, float)
            assert expiry > time.time()
            assert renewable is True
            # Verify unwrap was called on the temp client
            mock_client.sys.unwrap.assert_called_once()

    @patch("src.secrets.hashicorp_vault.hvac.Client")
    @patch("src.secrets.hashicorp_vault.os.path.exists")
    @patch("builtins.open", create=True)
    @patch("src.config.settings")
    def test_create_authenticated_client_unwrap_failure_falls_back_to_file(
        self, mock_settings, mock_open, mock_exists, mock_hvac_client
    ):
        """Test that unwrap failure falls back to secret_id file."""
        mock_settings.vault_url = "https://vault.example.com"
        mock_settings.vault_cert_path = "/path/to/cert.pem"
        mock_settings.vault_cert_key_path = "/path/to/key.pem"
        mock_settings.vault_verify_cert = True
        mock_settings.vault_role_id_path = "/path/to/role_id"
        mock_settings.vault_secret_id_path = "/path/to/secret_id"

        # Create a single mock client
        mock_client = MagicMock()
        mock_hvac_client.return_value = mock_client

        # Mock file operations - secret_id file exists
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.return_value.read.side_effect = [
            "test-role-id",
            "test-secret-id",
        ]
        mock_open.return_value = mock_file_handle

        # Mock unwrap failure - falls back to file
        mock_client.sys.unwrap.side_effect = Exception("Unwrap failed")

        # Mock authentication
        mock_client.is_authenticated.return_value = True
        mock_client.auth.approle.login.return_value = {
            "auth": {
                "lease_duration": 3600,
                "renewable": True,
            }
        }

        with patch.dict(os.environ, {"VAULT_WRAPPING_TOKEN": "test-wrapping-token"}):
            vault = HashicorpVault()
            client, expiry, renewable = vault._create_authenticated_client()

            # Verify we got a valid authenticated client
            assert client is not None
            assert isinstance(expiry, float)
            assert expiry > time.time()
            assert renewable is True
            # Verify the unwrap was attempted
            mock_client.sys.unwrap.assert_called_once()
            # Verify authentication was performed with file-based secret_id
            mock_client.auth.approle.login.assert_called_once_with(
                role_id="test-role-id", secret_id="test-secret-id"
            )

    @patch("src.secrets.hashicorp_vault.hvac.Client")
    @patch("src.secrets.hashicorp_vault.os.path.exists")
    @patch("builtins.open", create=True)
    @patch("src.config.settings")
    def test_create_authenticated_client_authentication_failure(
        self, mock_settings, mock_open, mock_exists, mock_hvac_client
    ):
        """Test error when authentication fails."""
        mock_settings.vault_url = "https://vault.example.com"
        mock_settings.vault_cert_path = "/path/to/cert.pem"
        mock_settings.vault_cert_key_path = "/path/to/key.pem"
        mock_settings.vault_verify_cert = True
        mock_settings.vault_role_id_path = "/path/to/role_id"
        mock_settings.vault_secret_id_path = "/path/to/secret_id"

        # Setup mock client
        mock_client = MagicMock()
        mock_hvac_client.return_value = mock_client

        # Mock file operations
        mock_exists.return_value = True
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.return_value.read.side_effect = [
            "test-role-id",
            "test-secret-id",
        ]
        mock_open.return_value = mock_file_handle

        # Mock authentication failure
        mock_client.is_authenticated.return_value = False
        mock_client.auth.approle.login.return_value = {}

        vault = HashicorpVault()
        with pytest.raises(RuntimeError) as exc_info:
            vault._create_authenticated_client()

        assert "Failed to authenticate with Vault" in str(exc_info.value)


class TestHashicorpVaultAvailability:
    """Tests for is_available method."""

    def test_is_available_returns_false_initially(self):
        """Test that is_available returns False before initialization."""
        vault = HashicorpVault()
        assert vault.is_available() is False

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_is_available_returns_true_after_successful_initialization(
        self, mock_create_client
    ):
        """Test that is_available returns True after successful initialization."""
        mock_client = MagicMock()
        mock_expiry = time.time() + 3600
        mock_renewable = True
        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        vault = HashicorpVault()
        vault.initialize()

        assert vault.is_available() is True

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_is_available_returns_false_after_failed_initialization(
        self, mock_create_client
    ):
        """Test that is_available returns False after failed initialization."""
        mock_create_client.side_effect = RuntimeError("Connection failed")

        vault = HashicorpVault()
        vault.initialize()

        assert vault.is_available() is False


class TestHashicorpVaultGetVaultClient:
    """Tests for _get_vault_client method."""

    def test_get_vault_client_returns_none_when_unavailable(self):
        """Test that _get_vault_client returns None when vault is unavailable."""
        vault = HashicorpVault()
        client = vault._get_vault_client()

        assert client is None

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_get_vault_client_returns_authenticated_client(self, mock_create_client):
        """Test that _get_vault_client returns authenticated client."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True
        mock_expiry = time.time() + 3600
        mock_renewable = True
        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        vault = HashicorpVault()
        vault.initialize()

        client = vault._get_vault_client()
        assert client == mock_client

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_get_vault_client_re_authenticates_when_token_expired(
        self, mock_create_client
    ):
        """Test that _get_vault_client re-authenticates when token has expired."""
        mock_client1 = MagicMock(spec=hvac.Client)
        mock_client2 = MagicMock(spec=hvac.Client)
        mock_client2.is_authenticated.return_value = True

        # First call: expired token, second call: new authenticated client
        mock_expiry_past = time.time() - 100  # Already expired
        mock_expiry_future = time.time() + 3600  # Future expiry
        mock_renewable = True

        mock_create_client.side_effect = [
            (mock_client1, mock_expiry_past, mock_renewable),
            (mock_client2, mock_expiry_future, mock_renewable),
        ]

        vault = HashicorpVault()
        vault.initialize()

        # Force client details to have expired token
        vault._vault_client_details = (mock_client1, mock_expiry_past, mock_renewable)
        mock_client1.is_authenticated.return_value = True

        client = vault._get_vault_client()

        # Should have called create_authenticated_client again for re-auth
        assert mock_create_client.call_count == 2
        assert client == mock_client2

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_get_vault_client_renews_token_when_near_expiry(self, mock_create_client):
        """Test that _get_vault_client renews token when approaching expiry."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True

        # Token expires in 800 seconds (within renewal threshold of 900s)
        mock_expiry = time.time() + 800
        mock_renewable = True

        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        # Mock token renewal
        mock_client.auth.token.renew_self.return_value = {
            "auth": {
                "lease_duration": 3600,
                "renewable": True,
            }
        }

        vault = HashicorpVault()
        vault.initialize()

        client = vault._get_vault_client()

        assert client == mock_client
        mock_client.auth.token.renew_self.assert_called_once()

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_get_vault_client_handles_renewal_failure_gracefully(
        self, mock_create_client
    ):
        """Test that _get_vault_client handles renewal failure gracefully."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True

        # Token expires in 800 seconds
        mock_expiry = time.time() + 800
        mock_renewable = True

        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        # Mock renewal failure
        mock_client.auth.token.renew_self.side_effect = InvalidRequest(
            "Token max_ttl reached"
        )

        vault = HashicorpVault()
        vault.initialize()

        client = vault._get_vault_client()

        # Should still return client even though renewal failed
        assert client == mock_client

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_get_vault_client_handles_unauthenticated_client(self, mock_create_client):
        """Test that _get_vault_client re-authenticates when client becomes unauthenticated."""
        mock_client1 = MagicMock(spec=hvac.Client)
        mock_client2 = MagicMock(spec=hvac.Client)

        mock_expiry = time.time() + 3600
        mock_renewable = True

        mock_create_client.side_effect = [
            (mock_client1, mock_expiry, mock_renewable),
            (mock_client2, mock_expiry, mock_renewable),
        ]

        vault = HashicorpVault()
        vault.initialize()

        # Simulate client becoming unauthenticated
        mock_client1.is_authenticated.return_value = False
        mock_client2.is_authenticated.return_value = True

        client = vault._get_vault_client()

        assert client == mock_client2
        assert mock_create_client.call_count == 2


class TestHashicorpVaultStoreSecret:
    """Tests for store_secret method."""

    def test_store_secret_raises_type_error_for_invalid_path(self):
        """Test that store_secret raises TypeError for non-string path."""
        vault = HashicorpVault()

        with pytest.raises(TypeError) as exc_info:
            vault.store_secret(123, {"key": "value"})

        assert "Path must be string" in str(exc_info.value)

    def test_store_secret_raises_type_error_for_invalid_value(self):
        """Test that store_secret raises TypeError for non-dict value."""
        vault = HashicorpVault()

        with pytest.raises(TypeError) as exc_info:
            vault.store_secret("secret/path", "not a dict")

        assert "value must be dict" in str(exc_info.value)

    def test_store_secret_raises_value_error_for_empty_path(self):
        """Test that store_secret raises ValueError for empty path."""
        vault = HashicorpVault()

        with pytest.raises(ValueError) as exc_info:
            vault.store_secret("", {"key": "value"})

        assert "cannot be empty" in str(exc_info.value)

    def test_store_secret_raises_value_error_for_empty_value(self):
        """Test that store_secret raises ValueError for empty dict."""
        vault = HashicorpVault()

        with pytest.raises(ValueError) as exc_info:
            vault.store_secret("secret/path", {})

        assert "cannot be empty" in str(exc_info.value)

    def test_store_secret_returns_none_when_vault_unavailable(self):
        """Test that store_secret returns None when vault is unavailable."""
        vault = HashicorpVault()

        result = vault.store_secret("secret/path", {"key": "value"})

        assert result is None

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_store_secret_success(self, mock_get_client):
        """Test successful secret storage."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        result = vault.store_secret("secret/path", {"key": "value"})

        assert result == "secret/path"
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_store_secret_logs_success(self, mock_get_client, caplog):
        """Test that store_secret logs success."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        with caplog.at_level(logging.INFO):
            vault.store_secret("secret/path", {"key": "value"})

        assert "successfully stored" in caplog.text.lower()

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_store_secret_raises_runtime_error_on_vault_error(self, mock_get_client):
        """Test that store_secret raises RuntimeError on Vault operation failure."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.create_or_update_secret.side_effect = VaultError(
            "Vault error"
        )
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        with pytest.raises(RuntimeError) as exc_info:
            vault.store_secret("secret/path", {"key": "value"})

        assert "Failed to store secret in Vault" in str(exc_info.value)

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_store_secret_with_complex_data(self, mock_get_client):
        """Test storing secret with complex nested data."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        complex_data = {
            "api_key": "sk-test123",
            "config": {"model": "gpt-4", "max_tokens": 4096},
            "endpoints": ["api1.example.com", "api2.example.com"],
        }

        result = vault.store_secret("secret/openai", complex_data)

        assert result == "secret/openai"
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="secret/openai", secret=complex_data
        )


class TestHashicorpVaultRetrieveSecret:
    """Tests for retrieve_secret method."""

    def test_retrieve_secret_raises_type_error_for_non_string_path(self):
        """Test that retrieve_secret raises TypeError for non-string path."""
        vault = HashicorpVault()

        with pytest.raises(TypeError) as exc_info:
            vault.retrieve_secret(123)

        assert "must be a string" in str(exc_info.value)

    def test_retrieve_secret_raises_value_error_for_empty_path(self):
        """Test that retrieve_secret raises ValueError for empty path."""
        vault = HashicorpVault()

        with pytest.raises(ValueError) as exc_info:
            vault.retrieve_secret("")

        assert "cannot be empty" in str(exc_info.value)

    def test_retrieve_secret_returns_none_when_vault_unavailable(self):
        """Test that retrieve_secret returns None when vault is unavailable."""
        vault = HashicorpVault()

        result = vault.retrieve_secret("secret/path")

        assert result is None

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_retrieve_secret_success(self, mock_get_client):
        """Test successful secret retrieval."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test-key", "model": "gpt-4"}}
        }
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        result = vault.retrieve_secret("secret/path")

        assert result == {"api_key": "test-key", "model": "gpt-4"}

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_retrieve_secret_success_returns_data(self, mock_get_client):
        """Test that retrieve_secret successfully returns data."""
        mock_client = MagicMock()
        secret_data = {"key": "value", "nested": {"data": "test"}}
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": secret_data}
        }
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        result = vault.retrieve_secret("secret/path")

        assert result == secret_data
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="secret/path"
        )

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_retrieve_secret_raises_runtime_error_for_missing_secret(
        self, mock_get_client
    ):
        """Test that retrieve_secret raises RuntimeError for missing secret."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.secrets.kv.v2.read_secret_version.side_effect = VaultError(
            "Secret not found"
        )
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        with pytest.raises(RuntimeError) as exc_info:
            vault.retrieve_secret("secret/missing")

        assert "Failed to retrieve secret from Vault" in str(exc_info.value)

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_retrieve_secret_raises_error_for_invalid_response(self, mock_get_client):
        """Test that retrieve_secret raises error for invalid response format."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {}
        }  # Missing 'data' key in nested structure
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        with pytest.raises(RuntimeError) as exc_info:
            vault.retrieve_secret("secret/path")

        assert "Failed to retrieve secret from Vault" in str(exc_info.value)

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_retrieve_secret_with_complex_data(self, mock_get_client):
        """Test retrieving secret with complex nested data."""
        complex_data = {
            "api_key": "sk-test123",
            "config": {"model": "gpt-4", "max_tokens": 4096},
            "endpoints": ["api1.example.com", "api2.example.com"],
        }

        mock_client = MagicMock(spec=hvac.Client)
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": complex_data}
        }
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        result = vault.retrieve_secret("secret/openai")

        assert result == complex_data

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_retrieve_secret_logs_vault_error(self, mock_get_client, caplog):
        """Test that retrieve_secret logs VaultError."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.secrets.kv.v2.read_secret_version.side_effect = VaultError(
            "Connection refused"
        )
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError):
                vault.retrieve_secret("secret/path")

        assert "vault operation failed" in caplog.text.lower()

    @patch("src.secrets.hashicorp_vault.HashicorpVault._get_vault_client")
    def test_retrieve_secret_tracks_metrics_on_error(self, mock_get_client):
        """Test that retrieve_secret tracks metrics on error."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.secrets.kv.v2.read_secret_version.side_effect = VaultError(
            "Connection error"
        )
        mock_get_client.return_value = mock_client

        vault = HashicorpVault()
        vault._vault_available = True

        with patch("src.secrets.hashicorp_vault.track_ai_metrics") as mock_metrics:
            with pytest.raises(RuntimeError):
                vault.retrieve_secret("secret/path")

            mock_metrics.assert_called()


class TestHashicorpVaultIntegration:
    """Integration tests for HashicorpVault."""

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_store_and_retrieve_roundtrip(self, mock_create_client):
        """Test store and retrieve roundtrip."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True
        mock_expiry = time.time() + 3600
        mock_renewable = True
        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        secret_data = {"api_key": "test-key", "model": "gpt-4"}

        # Mock retrieve response
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": secret_data}
        }

        vault = HashicorpVault()
        vault.initialize()

        # Store secret
        store_result = vault.store_secret("secret/test", secret_data)
        assert store_result == "secret/test"

        # Retrieve secret
        retrieve_result = vault.retrieve_secret("secret/test")
        assert retrieve_result == secret_data

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_multiple_secrets_storage_and_retrieval(self, mock_create_client):
        """Test storing and retrieving multiple secrets."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True
        mock_expiry = time.time() + 3600
        mock_renewable = True
        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        vault = HashicorpVault()
        vault.initialize()

        # Store multiple secrets
        secrets = {
            "secret/openai": {"api_key": "sk-openai", "model": "gpt-4"},
            "secret/anthropic": {"api_key": "sk-anthropic", "model": "claude"},
        }

        for path, data in secrets.items():
            result = vault.store_secret(path, data)
            assert result == path

        # Verify storage was called for each secret
        assert mock_client.secrets.kv.v2.create_or_update_secret.call_count == 2

    @patch("src.secrets.hashicorp_vault.HashicorpVault._create_authenticated_client")
    def test_handles_token_renewal_during_operations(self, mock_create_client):
        """Test that vault handles token renewal during operations."""
        mock_client = MagicMock(spec=hvac.Client)
        mock_client.is_authenticated.return_value = True

        # Initial expiry close to threshold
        mock_expiry = time.time() + 800
        mock_renewable = True

        mock_create_client.return_value = (mock_client, mock_expiry, mock_renewable)

        # Mock renewal response
        mock_client.auth.token.renew_self.return_value = {
            "auth": {
                "lease_duration": 3600,
                "renewable": True,
            }
        }

        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }

        vault = HashicorpVault()
        vault.initialize()

        # Operation should trigger renewal
        result = vault.retrieve_secret("secret/path")

        assert result == {"key": "value"}
        mock_client.auth.token.renew_self.assert_called_once()
