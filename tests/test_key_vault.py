import base64
import time
from unittest.mock import Mock, call, patch

import hvac
import pytest
from hamcrest import (
    assert_that,
    calling,
    equal_to,
    has_properties,
    instance_of,
    is_,
    is_not,
    raises,
)
from hvac.exceptions import InvalidRequest, VaultError

# Import functions and globals to test/mock
from src import key_vault
from src.key_vault import (
    _RENEWAL_THRESHOLD_SECONDS,
    _create_authenticated_client,
    get_vault_client,
    initialize_vault_client,
    retrieve_api_key_from_vault,
    store_api_key_in_vault,
)


@pytest.fixture(autouse=True)
def reset_vault_client_details(monkeypatch):
    """Fixture to reset the global _vault_client_details and _vault_available before each test."""
    # Use monkeypatch to set the global variables in the key_vault module
    monkeypatch.setattr(key_vault, "_vault_client_details", None, raising=False)
    monkeypatch.setattr(key_vault, "_vault_available", False, raising=False)
    yield  # Test runs here
    # Optional: Clean up after test if needed, though resetting at start is usually sufficient
    monkeypatch.setattr(key_vault, "_vault_client_details", None, raising=False)
    monkeypatch.setattr(key_vault, "_vault_available", False, raising=False)


@pytest.fixture
def mock_hvac_client():
    """Fixture to create a mock hvac.Client."""
    client = Mock(spec=hvac.Client)
    client.is_authenticated.return_value = True
    # Mock the auth.token namespace and renew_self method
    client.auth.token.renew_self = Mock()
    return client


@pytest.fixture
def mock_create_authenticated_client(mock_hvac_client):
    """Fixture to patch _create_authenticated_client."""
    with patch("src.key_vault._create_authenticated_client") as mock_create:
        # Default mock return: authenticated, expires in 1 hour, renewable
        mock_create.return_value = (mock_hvac_client, time.time() + 3600, True)
        yield mock_create


@pytest.fixture
def mock_time():
    """Fixture to patch time.time."""
    with patch("src.key_vault.time") as mock_time_module:
        # Set a fixed current time for predictability
        mock_time_module.time.return_value = 1700000000.0  # Example fixed timestamp
        yield mock_time_module


class TestVaultClientManagement:
    """Test suite for Vault client lifecycle management (get_vault_client)."""

    def test_get_vault_client_initial_call(
        self, mock_create_authenticated_client, mock_hvac_client, mock_time, monkeypatch
    ):
        """Case 1: Test first call initializes client via _create_authenticated_client."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        initial_expiry = mock_time.time() + 3600
        mock_create_authenticated_client.return_value = (
            mock_hvac_client,
            initial_expiry,
            True,
        )

        # Act
        client = get_vault_client()

        # Assert
        mock_create_authenticated_client.assert_called_once()
        assert_that(client, is_(mock_hvac_client))
        # Check internal state
        assert_that(key_vault._vault_client_details, is_not(None))
        assert_that(key_vault._vault_client_details[0], is_(mock_hvac_client))
        assert_that(key_vault._vault_client_details[1], equal_to(initial_expiry))
        assert_that(key_vault._vault_client_details[2], is_(True))

    def test_get_vault_client_not_authenticated(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Case 1 variant: Test re-authentication if client.is_authenticated() is False."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        # Set up an initial state with a client that reports not authenticated
        initial_mock_client = Mock(spec=hvac.Client)
        initial_mock_client.is_authenticated.return_value = False
        initial_expiry = mock_time.time() + 3600
        monkeypatch.setattr(
            key_vault,
            "_vault_client_details",
            (initial_mock_client, initial_expiry, True),
        )

        # _create_authenticated_client will return a *new* mock client
        new_mock_client = Mock(spec=hvac.Client)
        new_mock_client.is_authenticated.return_value = True
        new_expiry = mock_time.time() + 7200  # Different expiry for distinction
        mock_create_authenticated_client.return_value = (
            new_mock_client,
            new_expiry,
            True,
        )

        # Act
        client = get_vault_client()

        # Assert
        mock_create_authenticated_client.assert_called_once()
        assert_that(client, is_(new_mock_client))
        assert_that(client, is_not(initial_mock_client))
        # Check internal state updated
        assert_that(key_vault._vault_client_details[0], is_(new_mock_client))
        assert_that(key_vault._vault_client_details[1], equal_to(new_expiry))

    def test_get_vault_client_token_expired(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Case 2: Test re-authentication if token is expired."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        # Set up initial state with an expired token
        initial_mock_client = Mock(spec=hvac.Client)
        initial_mock_client.is_authenticated.return_value = (
            True  # Assume it was valid before expiry check
        )
        expired_time = mock_time.time() - 60  # 1 minute ago
        monkeypatch.setattr(
            key_vault,
            "_vault_client_details",
            (initial_mock_client, expired_time, True),
        )

        # _create_authenticated_client will return a new mock client
        new_mock_client = Mock(spec=hvac.Client)
        new_mock_client.is_authenticated.return_value = True
        new_expiry = mock_time.time() + 3600
        mock_create_authenticated_client.return_value = (
            new_mock_client,
            new_expiry,
            True,
        )

        # Act
        client = get_vault_client()

        # Assert
        mock_create_authenticated_client.assert_called_once()
        assert_that(client, is_(new_mock_client))
        # Check internal state updated
        assert_that(key_vault._vault_client_details[0], is_(new_mock_client))
        assert_that(key_vault._vault_client_details[1], equal_to(new_expiry))

    def test_get_vault_client_valid_token_no_renewal_needed(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Test returns existing client if token is valid and not near expiry."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        # Set up initial state with a valid, far-from-expiry token
        initial_expiry = mock_time.time() + 3600  # Expires in 1 hour
        monkeypatch.setattr(
            key_vault,
            "_vault_client_details",
            (mock_hvac_client, initial_expiry, True),
        )
        mock_create_authenticated_client.reset_mock()  # Reset because fixture might have called it

        # Act
        client = get_vault_client()

        # Assert
        mock_create_authenticated_client.assert_not_called()
        mock_hvac_client.auth.token.renew_self.assert_not_called()
        assert_that(client, is_(mock_hvac_client))
        # Check internal state remains unchanged
        assert_that(key_vault._vault_client_details[0], is_(mock_hvac_client))
        assert_that(key_vault._vault_client_details[1], equal_to(initial_expiry))
        assert_that(key_vault._vault_client_details[2], is_(True))

    def test_get_vault_client_nearing_expiry_successful_renewal(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Case 3: Test successful renewal when token is nearing expiry."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        # Expires just within the renewal threshold
        initial_expiry = mock_time.time() + _RENEWAL_THRESHOLD_SECONDS - 60
        monkeypatch.setattr(
            key_vault,
            "_vault_client_details",
            (mock_hvac_client, initial_expiry, True),
        )
        mock_create_authenticated_client.reset_mock()

        # Mock the renewal response
        new_lease_duration = 7200  # e.g., renewed for 2 hours
        renewal_response = {
            "auth": {"lease_duration": new_lease_duration, "renewable": True}
        }
        mock_hvac_client.auth.token.renew_self.return_value = renewal_response
        expected_new_expiry = mock_time.time() + new_lease_duration

        # Act
        client = get_vault_client()

        # Assert
        mock_create_authenticated_client.assert_not_called()
        mock_hvac_client.auth.token.renew_self.assert_called_once()
        assert_that(
            client, is_(mock_hvac_client)
        )  # Should return the same client instance
        # Check internal state updated after renewal
        assert_that(key_vault._vault_client_details[0], is_(mock_hvac_client))
        assert_that(key_vault._vault_client_details[1], equal_to(expected_new_expiry))
        assert_that(key_vault._vault_client_details[2], is_(True))  # Still renewable

    def test_get_vault_client_nearing_expiry_renewal_fails_invalid_request(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Case 3: Test renewal failure (InvalidRequest, e.g., max TTL) marks as non-renewable."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        initial_expiry = mock_time.time() + _RENEWAL_THRESHOLD_SECONDS - 60
        monkeypatch.setattr(
            key_vault,
            "_vault_client_details",
            (mock_hvac_client, initial_expiry, True),
        )
        mock_create_authenticated_client.reset_mock()

        # Mock renewal failure
        mock_hvac_client.auth.token.renew_self.side_effect = InvalidRequest(
            "max ttl reached"
        )

        # Act
        client = get_vault_client()

        # Assert
        mock_create_authenticated_client.assert_not_called()
        mock_hvac_client.auth.token.renew_self.assert_called_once()
        assert_that(client, is_(mock_hvac_client))
        # Check internal state: expiry unchanged, marked non-renewable
        assert_that(key_vault._vault_client_details[0], is_(mock_hvac_client))
        assert_that(key_vault._vault_client_details[1], equal_to(initial_expiry))
        assert_that(
            key_vault._vault_client_details[2], is_(False)
        )  # Marked non-renewable

    def test_get_vault_client_nearing_expiry_renewal_fails_vault_error(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Case 3: Test renewal failure (VaultError) keeps original state."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        initial_expiry = mock_time.time() + _RENEWAL_THRESHOLD_SECONDS - 60
        monkeypatch.setattr(
            key_vault,
            "_vault_client_details",
            (mock_hvac_client, initial_expiry, True),
        )
        mock_create_authenticated_client.reset_mock()

        # Mock renewal failure
        mock_hvac_client.auth.token.renew_self.side_effect = VaultError(
            "connection error"
        )

        # Act
        client = get_vault_client()

        # Assert
        mock_create_authenticated_client.assert_not_called()
        mock_hvac_client.auth.token.renew_self.assert_called_once()
        assert_that(client, is_(mock_hvac_client))
        # Check internal state: unchanged
        assert_that(key_vault._vault_client_details[0], is_(mock_hvac_client))
        assert_that(key_vault._vault_client_details[1], equal_to(initial_expiry))
        assert_that(key_vault._vault_client_details[2], is_(True))

    def test_get_vault_client_nearing_expiry_renewal_fails_generic_exception(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Case 3: Test renewal failure with generic exception keeps original state."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        initial_expiry = mock_time.time() + _RENEWAL_THRESHOLD_SECONDS - 60
        monkeypatch.setattr(
            key_vault,
            "_vault_client_details",
            (mock_hvac_client, initial_expiry, True),
        )
        mock_create_authenticated_client.reset_mock()

        # Mock renewal failure with generic exception
        mock_hvac_client.auth.token.renew_self.side_effect = Exception(
            "Some unexpected error"
        )

        # Act - get client with patched logger to verify logging
        with patch("src.key_vault.logger") as mock_logger:
            client = get_vault_client()

            # Assert logging happened correctly
            mock_logger.error.assert_called_once_with(
                "Unexpected error during Vault token renewal: Some unexpected error"
            )

        # Assert client behavior
        mock_create_authenticated_client.assert_not_called()
        mock_hvac_client.auth.token.renew_self.assert_called_once()
        assert_that(client, is_(mock_hvac_client))

        # Check internal state: unchanged
        assert_that(key_vault._vault_client_details[0], is_(mock_hvac_client))
        assert_that(key_vault._vault_client_details[1], equal_to(initial_expiry))
        assert_that(key_vault._vault_client_details[2], is_(True))

    def test_get_vault_client_nearing_expiry_not_renewable(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Test renewal is skipped if token is nearing expiry but not renewable."""
        # Arrange
        # Set vault as available for this test
        monkeypatch.setattr(key_vault, "_vault_available", True)
        initial_expiry = mock_time.time() + _RENEWAL_THRESHOLD_SECONDS - 60
        monkeypatch.setattr(
            key_vault,
            "_vault_client_details",
            (mock_hvac_client, initial_expiry, False),  # Not renewable
        )
        mock_create_authenticated_client.reset_mock()

        # Act
        client = get_vault_client()

        # Assert
        mock_create_authenticated_client.assert_not_called()
        mock_hvac_client.auth.token.renew_self.assert_not_called()  # Renewal should not be attempted
        assert_that(client, is_(mock_hvac_client))
        # Check internal state: unchanged
        assert_that(key_vault._vault_client_details[0], is_(mock_hvac_client))
        assert_that(key_vault._vault_client_details[1], equal_to(initial_expiry))
        assert_that(key_vault._vault_client_details[2], is_(False))

    def test_get_vault_client_reauthentication_failure_propagates(
        self, mock_create_authenticated_client, monkeypatch
    ):
        """Test that exceptions during re-authentication return None and mark vault unavailable."""
        # Arrange
        # Set vault as available initially but force re-auth
        monkeypatch.setattr(key_vault, "_vault_available", True)
        monkeypatch.setattr(key_vault, "_vault_client_details", None)  # Force re-auth
        mock_create_authenticated_client.side_effect = RuntimeError("Auth Failed")

        # Act
        client = get_vault_client()

        # Assert
        # Should return None and mark vault as unavailable
        assert_that(client, is_(None))
        assert_that(key_vault._vault_available, is_(False))
        mock_create_authenticated_client.assert_called_once()

    def test_initialize_vault_client(
        self, mock_create_authenticated_client, mock_hvac_client, mock_time
    ):
        """Test initialize_vault_client calls _create_authenticated_client and sets details."""
        # Arrange
        initial_expiry = mock_time.time() + 3600
        mock_create_authenticated_client.return_value = (
            mock_hvac_client,
            initial_expiry,
            True,
        )

        # Act
        initialize_vault_client()

        # Assert
        mock_create_authenticated_client.assert_called_once()
        assert_that(key_vault._vault_client_details, is_not(None))
        assert_that(key_vault._vault_client_details[0], is_(mock_hvac_client))
        assert_that(key_vault._vault_client_details[1], equal_to(initial_expiry))
        assert_that(key_vault._vault_client_details[2], is_(True))
        assert_that(key_vault._vault_available, is_(True))


class TestVaultAvailability:
    """Test suite for vault availability tracking."""

    def test_initialize_vault_client_success_sets_available(
        self, mock_create_authenticated_client, mock_hvac_client, mock_time
    ):
        """Test initialize_vault_client sets _vault_available to True on success."""
        # Arrange
        initial_expiry = mock_time.time() + 3600
        mock_create_authenticated_client.return_value = (
            mock_hvac_client,
            initial_expiry,
            True,
        )

        # Act
        initialize_vault_client()

        # Assert
        assert_that(key_vault._vault_available, is_(True))
        assert_that(key_vault._vault_client_details, is_not(None))

    def test_initialize_vault_client_failure_sets_unavailable(
        self, mock_create_authenticated_client
    ):
        """Test initialize_vault_client sets _vault_available to False on failure."""
        # Arrange
        mock_create_authenticated_client.side_effect = RuntimeError(
            "Vault connection failed"
        )

        # Act
        initialize_vault_client()  # Should not raise exception

        # Assert
        assert_that(key_vault._vault_available, is_(False))
        assert_that(key_vault._vault_client_details, is_(None))

    def test_get_vault_client_returns_none_when_unavailable(self, monkeypatch):
        """Test get_vault_client returns None when vault is marked unavailable."""
        # Arrange
        monkeypatch.setattr(key_vault, "_vault_available", False)

        # Act
        client = get_vault_client()

        # Assert
        assert_that(client, is_(None))

    def test_get_vault_client_marks_unavailable_on_auth_failure(
        self, mock_create_authenticated_client, monkeypatch
    ):
        """Test get_vault_client marks vault unavailable when re-authentication fails."""
        # Arrange
        monkeypatch.setattr(key_vault, "_vault_available", True)
        monkeypatch.setattr(key_vault, "_vault_client_details", None)
        mock_create_authenticated_client.side_effect = RuntimeError("Auth failed")

        # Act
        client = get_vault_client()

        # Assert
        assert_that(client, is_(None))
        assert_that(key_vault._vault_available, is_(False))

    def test_get_vault_client_marks_unavailable_on_expiry_reauth_failure(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Test get_vault_client marks vault unavailable when expired token re-auth fails."""
        # Arrange
        expired_time = mock_time.time() - 60
        monkeypatch.setattr(key_vault, "_vault_available", True)
        monkeypatch.setattr(
            key_vault, "_vault_client_details", (mock_hvac_client, expired_time, True)
        )
        mock_create_authenticated_client.side_effect = RuntimeError("Auth failed")

        # Act
        client = get_vault_client()

        # Assert
        assert_that(client, is_(None))
        assert_that(key_vault._vault_available, is_(False))


class TestStoreApiKeyInVault:
    """Test suite for store_api_key_in_vault graceful degradation."""

    def test_store_api_key_returns_none_when_vault_unavailable(self, monkeypatch):
        """Test store_api_key_in_vault returns None when vault is unavailable."""
        # Arrange
        monkeypatch.setattr(key_vault, "_vault_available", False)

        # Act
        result = store_api_key_in_vault("test/path", "test-key")

        # Assert
        assert_that(result, is_(None))

    def test_store_api_key_returns_path_when_successful(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Test store_api_key_in_vault returns path when successful."""
        # Arrange
        monkeypatch.setattr(key_vault, "_vault_available", True)
        initial_expiry = mock_time.time() + 3600
        monkeypatch.setattr(
            key_vault, "_vault_client_details", (mock_hvac_client, initial_expiry, True)
        )
        mock_create_authenticated_client.reset_mock()

        # Act
        result = store_api_key_in_vault("test/path", "test-key")

        # Assert
        assert_that(result, equal_to("test/path"))
        mock_hvac_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="test/path", secret={"api_key": "test-key"}
        )

    def test_store_api_key_validates_input_types(self):
        """Test store_api_key_in_vault validates input parameter types."""
        # Act & Assert
        assert_that(
            calling(store_api_key_in_vault).with_args(123, "key"),
            raises(TypeError, "Path and API key must be strings"),
        )
        assert_that(
            calling(store_api_key_in_vault).with_args("path", 123),
            raises(TypeError, "Path and API key must be strings"),
        )

    def test_store_api_key_validates_input_values(self):
        """Test store_api_key_in_vault validates input parameter values."""
        # Act & Assert
        assert_that(
            calling(store_api_key_in_vault).with_args("", "key"),
            raises(ValueError, "Path and API key cannot be empty"),
        )
        assert_that(
            calling(store_api_key_in_vault).with_args("path", ""),
            raises(ValueError, "Path and API key cannot be empty"),
        )


class TestRetrieveApiKeyFromVault:
    """Test suite for retrieve_api_key_from_vault graceful degradation."""

    def test_retrieve_api_key_returns_none_when_vault_unavailable(self, monkeypatch):
        """Test retrieve_api_key_from_vault returns None when vault is unavailable."""
        # Arrange
        monkeypatch.setattr(key_vault, "_vault_available", False)

        # Act
        result = retrieve_api_key_from_vault("test/path")

        # Assert
        assert_that(result, is_(None))

    def test_retrieve_api_key_returns_key_when_successful(
        self, mock_create_authenticated_client, mock_hvac_client, monkeypatch, mock_time
    ):
        """Test retrieve_api_key_from_vault returns API key when successful."""
        # Arrange
        monkeypatch.setattr(key_vault, "_vault_available", True)
        initial_expiry = mock_time.time() + 3600
        monkeypatch.setattr(
            key_vault, "_vault_client_details", (mock_hvac_client, initial_expiry, True)
        )
        mock_create_authenticated_client.reset_mock()

        # Mock successful secret retrieval
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test-secret-key"}}
        }

        # Act
        result = retrieve_api_key_from_vault("test/path")

        # Assert
        assert_that(result, equal_to("test-secret-key"))
        mock_hvac_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="test/path"
        )

    def test_retrieve_api_key_validates_input_types(self):
        """Test retrieve_api_key_from_vault validates input parameter types."""
        # Act & Assert
        assert_that(
            calling(retrieve_api_key_from_vault).with_args(123),
            raises(TypeError, "Vault path must be a string"),
        )

    def test_retrieve_api_key_validates_input_values(self):
        """Test retrieve_api_key_from_vault validates input parameter values."""
        # Act & Assert
        assert_that(
            calling(retrieve_api_key_from_vault).with_args(""),
            raises(ValueError, "Vault path cannot be empty"),
        )
