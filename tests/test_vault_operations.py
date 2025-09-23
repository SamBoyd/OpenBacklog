import os
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
from hamcrest import assert_that, calling, equal_to, instance_of, is_, raises
from hvac.exceptions import VaultError

from src.config import settings
from src.key_vault import (
    get_vault_client,
    initialize_vault_client,
    retrieve_api_key_from_vault,
    store_api_key_in_vault,
)


class TestVaultClientSingleton:
    """Test suite for the Vault client singleton pattern"""

    def setup_method(self):
        """Reset the _vault_client before each test to ensure test isolation."""
        from src import key_vault

        key_vault._vault_client_details = None
        key_vault._vault_available = True  # Set vault as available for these tests

    def teardown_method(self):
        """Reset the _vault_client after each test to ensure test isolation."""
        from src import key_vault

        key_vault._vault_client_details = None
        key_vault._vault_available = False  # Reset vault availability

    @pytest.fixture
    def mock_vault_client_details(self):
        """Fixture to create a mock Vault client details object."""
        mock_client = MagicMock()
        mock_client.is_authenticated = MagicMock(return_value=True)
        mock_details = (mock_client, time.time() + 60, True)

        with patch("src.key_vault._vault_client_details", mock_details):
            yield mock_details

    @patch("src.key_vault._create_authenticated_client")
    def test_get_vault_client_returns_existing_authenticated_client(
        self, mock_create_client, mock_vault_client_details
    ):
        """Test that get_vault_client returns the existing client if it's authenticated."""
        # Execute
        result = get_vault_client()

        # Verify
        mock_create_client.assert_not_called()
        assert_that(result, is_(mock_vault_client_details[0]))

    @patch("src.key_vault._vault_client_details", None)
    @patch("src.key_vault._create_authenticated_client")
    def test_get_vault_client_creates_new_when_none_exists(self, mock_create_client):
        """Test that get_vault_client creates a new client when none exists."""
        # Create a mock client to be returned
        mock_new_client = MagicMock()
        mock_create_client.return_value = (mock_new_client, datetime.now(), True)

        # Execute
        with patch("src.key_vault._vault_client_details", None):
            result = get_vault_client()

        # Verify
        assert_that(result, is_(mock_new_client))
        mock_create_client.assert_called_once()

    @patch("src.key_vault._create_authenticated_client")
    def test_get_vault_client_recreates_when_not_authenticated(
        self, mock_create_client
    ):
        """Test that get_vault_client creates a new client when the existing one isn't authenticated."""
        # Setup - create a mock non-authenticated client
        mock_old_client = MagicMock()
        mock_old_client.is_authenticated.return_value = False

        # Create a mock client to be returned
        mock_new_client = MagicMock()
        mock_create_client.return_value = (mock_new_client, datetime.now(), True)

        # Execute
        with patch("src.key_vault._vault_client_details", (mock_old_client, 0, False)):
            result = get_vault_client()

        # Verify
        assert_that(result, is_(mock_new_client))
        mock_create_client.assert_called_once()

    @patch("src.key_vault._create_authenticated_client")
    def test_initialize_vault_client(self, mock_create_client):
        """Test that initialize_vault_client properly initializes the client."""
        # Create a mock client to be returned
        mock_new_client = MagicMock()
        mock_create_client.return_value = (mock_new_client, datetime.now(), True)

        # Execute
        with patch("src.key_vault._vault_client_details", None):
            result = initialize_vault_client()

        # Verify
        assert_that(result, is_(None))
        mock_create_client.assert_called_once()


class TestVaultClient:
    """Test suite for the Vault client initialization function"""

    def setup_method(self):
        """Reset the _vault_client before each test to ensure test isolation."""
        from src import key_vault

        key_vault._vault_client_details = None
        key_vault._vault_available = True  # Set vault as available for these tests

    def teardown_method(self):
        """Reset the _vault_client after each test to ensure test isolation."""
        from src import key_vault

        key_vault._vault_client_details = None
        key_vault._vault_available = False  # Reset vault availability

    @patch("src.key_vault.os.path.exists")
    @patch("src.key_vault.open", new_callable=mock_open, read_data="test-role-id")
    @patch("src.key_vault.os.environ.get")
    @patch("src.key_vault.hvac.Client")
    def test_get_vault_client_success_with_wrapping_token(
        self, mock_client_class, mock_env_get, mock_file, mock_exists
    ):
        """Test successful Vault client initialization with wrapping token."""
        # Set up mocks for the two client instances we'll need
        mock_temp_client = MagicMock()
        mock_client = MagicMock()

        # Configure the first client (temp client for unwrapping)
        mock_client.sys.unwrap.return_value = {"data": {"secret_id": "test-secret-id"}}

        # Configure the second client (main client that will be returned)
        mock_temp_client.is_authenticated.return_value = True

        # Set up the side effect to return our mocks in sequence
        mock_client_class.side_effect = [mock_temp_client, mock_client]

        # Mock environment and file operations
        mock_env_get.return_value = "test-wrapping-token"
        mock_exists.return_value = True

        # Call function
        result = get_vault_client()

        # Verify the correct interactions occurred
        mock_exists.assert_called_with(settings.vault_role_id_path)
        mock_file.assert_called_with(settings.vault_role_id_path, "r")

        # Check that the second client (mock_client) was properly used
        mock_temp_client.auth.approle.login.assert_called_once_with(
            role_id="test-role-id", secret_id="test-secret-id"
        )
        mock_temp_client.is_authenticated.assert_called_once()

        # Verify the temp client was used for unwrapping
        mock_client.sys.unwrap.assert_called_once()

    @patch("src.key_vault.os.path.exists")
    @patch("src.key_vault.open", new_callable=mock_open)
    @patch("src.key_vault.os.environ.get")
    @patch("src.key_vault.hvac.Client")
    def test_get_vault_client_success_with_secret_id_file(
        self, mock_client_class, mock_env_get, mock_file, mock_exists
    ):
        """Test successful Vault client initialization with secret ID file."""
        # Set up mocks
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        # Mock file reads for role_id and secret_id
        mock_file.side_effect = [
            mock_open(read_data="test-role-id").return_value,
            mock_open(read_data="test-secret-id").return_value,
        ]

        # Mock environment and file operations
        mock_env_get.return_value = None  # No wrapping token
        mock_exists.side_effect = [True, True]  # Both files exist

        # Call function
        result = get_vault_client()

        # Assertions
        assert_that(result, is_(mock_client))
        assert mock_exists.call_count == 2
        assert mock_file.call_count == 2
        mock_client.auth.approle.login.assert_called_once_with(
            role_id="test-role-id", secret_id="test-secret-id"
        )
        mock_client.is_authenticated.assert_called_once()

    @patch("src.key_vault.os.path.exists")
    @patch("src.key_vault.hvac.Client")
    def test_get_vault_client_missing_role_id_file(
        self, mock_client_class, mock_exists
    ):
        """Test handling of missing role_id file."""
        # Set up mocks
        mock_exists.return_value = False

        # With graceful degradation, this should return None and mark vault unavailable
        result = get_vault_client()
        from src import key_vault

        assert_that(result, is_(None))
        assert_that(key_vault._vault_available, is_(False))

    @patch("src.key_vault.os.path.exists")
    @patch("src.key_vault.open", new_callable=mock_open, read_data="")
    @patch("src.key_vault.hvac.Client")
    def test_get_vault_client_empty_role_id_file(
        self, mock_client_class, mock_file, mock_exists
    ):
        """Test handling of empty role_id file."""
        # Set up mocks
        mock_exists.return_value = True

        # With graceful degradation, this should return None and mark vault unavailable
        result = get_vault_client()
        from src import key_vault

        assert_that(result, is_(None))
        assert_that(key_vault._vault_available, is_(False))

    @patch("src.key_vault.os.path.exists")
    @patch("src.key_vault.open", new_callable=mock_open, read_data="test-role-id")
    @patch("src.key_vault.os.environ.get")
    @patch("src.key_vault.hvac.Client")
    def test_get_vault_client_unwrap_failure_no_secret_id_file(
        self, mock_client_class, mock_env_get, mock_file, mock_exists
    ):
        """Test handling of unwrap failure and missing secret_id file."""
        # Set up mocks
        mock_temp_client = MagicMock()
        mock_temp_client.sys.unwrap.side_effect = Exception("Unwrap failed")
        mock_client_class.return_value = mock_temp_client

        # Mock environment and file operations
        mock_env_get.return_value = "test-wrapping-token"
        mock_exists.side_effect = [True, False]  # role_id exists, secret_id doesn't

        # With graceful degradation, this should return None and mark vault unavailable
        result = get_vault_client()
        from src import key_vault

        assert_that(result, is_(None))
        assert_that(key_vault._vault_available, is_(False))

    @patch("src.key_vault.os.path.exists")
    @patch("src.key_vault.open", new_callable=mock_open)
    @patch("src.key_vault.os.environ.get")
    @patch("src.key_vault.hvac.Client")
    def test_get_vault_client_authentication_failure(
        self, mock_client_class, mock_env_get, mock_file, mock_exists
    ):
        """Test handling of authentication failure."""
        # Set up mocks
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = False
        mock_client_class.return_value = mock_client

        # Mock file reads
        mock_file.side_effect = [
            mock_open(read_data="test-role-id").return_value,
            mock_open(read_data="test-secret-id").return_value,
        ]

        # Mock environment and file operations
        mock_env_get.return_value = None
        mock_exists.side_effect = [True, True]

        # With graceful degradation, this should return None and mark vault unavailable
        result = get_vault_client()
        from src import key_vault

        assert_that(result, is_(None))
        assert_that(key_vault._vault_available, is_(False))

    @patch("src.key_vault.os.path.exists")
    @patch("src.key_vault.open", new_callable=mock_open)
    @patch("src.key_vault.os.environ.get")
    @patch("src.key_vault.hvac.Client")
    def test_get_vault_client_login_exception(
        self, mock_client_class, mock_env_get, mock_file, mock_exists
    ):
        """Test exception during login process."""
        # Set up mocks
        mock_client = MagicMock()
        mock_client.auth.approle.login.side_effect = Exception("Login failed")
        mock_client_class.return_value = mock_client

        # Mock file reads
        mock_file.side_effect = [
            mock_open(read_data="test-role-id").return_value,
            mock_open(read_data="test-secret-id").return_value,
        ]

        # Mock environment and file operations
        mock_env_get.return_value = None
        mock_exists.side_effect = [True, True]

        # With graceful degradation, this should return None and mark vault unavailable
        result = get_vault_client()
        from src import key_vault

        assert_that(result, is_(None))
        assert_that(key_vault._vault_available, is_(False))


class TestStoreApiKeyInVault:
    """Test suite for storing API keys in Vault"""

    @patch("src.key_vault.get_vault_client")
    def test_store_api_key_success(self, mock_get_client):
        """Test successful storing of API key."""
        # Set up mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Call function
        path = "secret/api-keys/service1"
        key = "supersecretkey123"
        result = store_api_key_in_vault(path, key)

        # Assertions
        assert_that(result, equal_to(path))
        mock_get_client.assert_called_once()
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path=path, secret={"api_key": key}
        )

    def test_store_api_key_invalid_inputs(self):
        """Test validation of input parameters."""
        # Test with None path
        assert_that(
            calling(store_api_key_in_vault).with_args(None, "key"),
            raises(TypeError, pattern="Path and API key must be strings"),
        )

        # Test with None key
        assert_that(
            calling(store_api_key_in_vault).with_args("path", None),
            raises(TypeError, pattern="Path and API key must be strings"),
        )

        # Test with non-string path
        assert_that(
            calling(store_api_key_in_vault).with_args(123, "key"),
            raises(TypeError, pattern="Path and API key must be strings"),
        )

        # Test with empty path
        assert_that(
            calling(store_api_key_in_vault).with_args("", "key"),
            raises(ValueError, pattern="Path and API key cannot be empty"),
        )

        # Test with empty key
        assert_that(
            calling(store_api_key_in_vault).with_args("path", ""),
            raises(ValueError, pattern="Path and API key cannot be empty"),
        )

    @patch("src.key_vault.get_vault_client")
    def test_store_api_key_vault_error(self, mock_get_client):
        """Test handling of VaultError."""
        # Set up mock
        mock_client = MagicMock()
        vault_error = VaultError("Vault operation failed")
        mock_client.secrets.kv.v2.create_or_update_secret.side_effect = vault_error
        mock_get_client.return_value = mock_client

        # Assertions
        assert_that(
            calling(store_api_key_in_vault).with_args("path", "key"),
            raises(RuntimeError, pattern="Failed to store API key in Vault"),
        )

    @patch("src.key_vault.get_vault_client")
    def test_store_api_key_unexpected_exception(self, mock_get_client):
        """Test handling of unexpected exceptions."""
        # Set up mock
        mock_client = MagicMock()
        mock_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception(
            "Unexpected error"
        )
        mock_get_client.return_value = mock_client

        # Assertions
        assert_that(
            calling(store_api_key_in_vault).with_args("path", "key"),
            raises(
                RuntimeError,
                pattern="Failed to store API key in Vault due to an unexpected error",
            ),
        )

    @patch("src.key_vault.logger")
    @patch("src.key_vault.get_vault_client")
    def test_store_api_key_logs_error(self, mock_get_client, mock_logger):
        """Test that errors during storing are properly logged."""
        # Set up mock
        mock_client = MagicMock()
        mock_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception(
            "Test error"
        )
        mock_get_client.return_value = mock_client

        # Call function and catch expected exception
        try:
            store_api_key_in_vault("path", "key")
        except RuntimeError:
            pass

        # Verify log was called
        mock_logger.error.assert_called_once()


class TestRetrieveApiKeyFromVault:
    """Test suite for retrieving API keys from Vault"""

    @patch("src.key_vault.get_vault_client")
    def test_retrieve_api_key_success(self, mock_get_client):
        """Test successful retrieval of API key."""
        # Set up mock
        mock_client = MagicMock()
        mock_response = {"data": {"data": {"api_key": "supersecretkey123"}}}
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Call function
        path = "secret/api-keys/service1"
        result = retrieve_api_key_from_vault(path)

        # Assertions
        assert_that(result, equal_to("supersecretkey123"))
        mock_get_client.assert_called_once()
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(path=path)

    def test_retrieve_api_key_invalid_inputs(self):
        """Test validation of input parameters."""
        # Test with None path
        assert_that(
            calling(retrieve_api_key_from_vault).with_args(None),
            raises(TypeError, pattern="Vault path must be a string"),
        )

        # Test with non-string path
        assert_that(
            calling(retrieve_api_key_from_vault).with_args(123),
            raises(TypeError, pattern="Vault path must be a string"),
        )

        # Test with empty path
        assert_that(
            calling(retrieve_api_key_from_vault).with_args(""),
            raises(ValueError, pattern="Vault path cannot be empty"),
        )

    @patch("src.key_vault.get_vault_client")
    def test_retrieve_api_key_missing_data_structure(self, mock_get_client):
        """Test handling of missing data structure in response."""
        # Missing outer data key
        mock_client = MagicMock()
        mock_response_no_data = {}
        mock_client.secrets.kv.v2.read_secret_version.return_value = (
            mock_response_no_data
        )
        mock_get_client.return_value = mock_client

        assert_that(
            calling(retrieve_api_key_from_vault).with_args("path"),
            raises(
                VaultError,
                pattern="Could not retrieve your OpenAI API key. Please update your API key in the settings.",
            ),
        )

        # Missing inner data key
        mock_response_no_inner_data = {"data": {}}
        mock_client.secrets.kv.v2.read_secret_version.return_value = (
            mock_response_no_inner_data
        )

        assert_that(
            calling(retrieve_api_key_from_vault).with_args("path"),
            raises(
                VaultError,
                pattern="Could not retrieve your OpenAI API key. Please update your API key in the settings.",
            ),
        )

    @patch("src.key_vault.get_vault_client")
    def test_retrieve_api_key_missing_key(self, mock_get_client):
        """Test handling of missing api_key in response data."""
        mock_client = MagicMock()
        mock_response = {"data": {"data": {"other_key": "value but no api_key"}}}
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response
        mock_get_client.return_value = mock_client

        assert_that(
            calling(retrieve_api_key_from_vault).with_args("path"),
            raises(
                VaultError,
                pattern="Could not retrieve your OpenAI API key. Please update your API key in the settings.",
            ),
        )

    @patch("src.key_vault.get_vault_client")
    def test_retrieve_api_key_vault_error(self, mock_get_client):
        """Test handling of VaultError."""
        # Import VaultError at the test level for the mock setup
        from hvac.exceptions import VaultError

        # Set up mock
        mock_client = MagicMock()
        vault_error = VaultError("Vault operation failed")
        mock_client.secrets.kv.v2.read_secret_version.side_effect = vault_error
        mock_get_client.return_value = mock_client

        # Assertions
        assert_that(
            calling(retrieve_api_key_from_vault).with_args("path"),
            raises(
                VaultError,
                pattern="Could not retrieve your OpenAI API key. Please update your API key in the settings.",
            ),
        )

    @patch("src.key_vault.get_vault_client")
    def test_retrieve_api_key_unexpected_exception(self, mock_get_client):
        """Test handling of unexpected exceptions."""
        # Set up mock
        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Unexpected error"
        )
        mock_get_client.return_value = mock_client

        # Assertions
        assert_that(
            calling(retrieve_api_key_from_vault).with_args("path"),
            raises(
                VaultError,
                pattern="Could not retrieve your OpenAI API key. Please update your API key in the settings.",
            ),
        )

    @patch("src.key_vault.logger")
    @patch("src.key_vault.get_vault_client")
    def test_retrieve_api_key_logs_error(self, mock_get_client, mock_logger):
        """Test that errors during retrieval are properly logged."""
        # Set up mock
        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Test error"
        )
        mock_get_client.return_value = mock_client

        # Call function and catch expected exception
        try:
            retrieve_api_key_from_vault("path")
        except VaultError:
            pass

        # Verify log was called
        mock_logger.error.assert_called_once()
