# pytest file for litellm_service.py
from unittest.mock import MagicMock, patch

import pytest
import responses
from hvac.exceptions import VaultError

from src.config import settings
from src.litellm_service import (
    LITELLM_API_URL,
    create_litellm_user,
    get_litellm_user_info,
    regenerate_litellm_master_key,
    retrieve_litellm_key_for_user,
    retrieve_litellm_master_key,
)


class TestLiteLLMService:
    """Test cases for the LiteLLM service functions."""

    def test_retrieve_litellm_master_key_success(self):
        """
        Test successful retrieval of LiteLLM master key
        """
        result = retrieve_litellm_master_key()

        assert result == settings.litellm_master_key


@responses.activate
class TestRegenerateLiteLLMMasterKey:
    """Test cases for the regenerate_litellm_master_key function."""

    @patch("src.litellm_service.get_vault")
    @patch("src.litellm_service.uuid.uuid4")
    def test_regenerate_litellm_master_key_success(self, mock_uuid, mock_get_vault):
        """
        Test successful regeneration of LiteLLM master key.

        This test verifies that the function generates a new key with the correct format,
        stores it in the vault, and returns the retrieved key.
        """
        # Arrange
        mock_uuid.return_value = "test-uuid-12345"
        expected_new_key = "sk-proj-test-uuid-12345"
        mock_vault = MagicMock()
        mock_vault.store_api_key_in_vault.return_value = (
            settings.litellm_master_key_vault_path
        )
        mock_get_vault.return_value = mock_vault

        # Use responses to mock the requests.post  to f"{LITELLM_API_URL}/key/regenerate"
        responses.add(
            responses.POST,
            f"{LITELLM_API_URL}/key/regenerate",
            json={
                "key": settings.litellm_master_key,
                "new_master_key": expected_new_key,
            },
        )

        # Act
        result = regenerate_litellm_master_key()

        # Assert
        mock_uuid.assert_called_once()
        mock_vault.store_api_key_in_vault.assert_called_once_with(
            settings.litellm_master_key_vault_path, expected_new_key
        )


class TestRetrieveLiteLLMKeyForUser:
    """Test cases for the retrieve_litellm_key_for_user function."""

    @patch("src.litellm_service.get_vault")
    def test_retrieve_litellm_key_for_user_success(
        self, mock_get_vault, session, user, test_user_key
    ):
        """Test successful retrieval of LiteLLM key for a user."""
        expected_key = "test-litellm-key-12345"
        mock_vault = MagicMock()
        mock_vault.retrieve_api_key_from_vault.return_value = expected_key
        mock_get_vault.return_value = mock_vault

        result = retrieve_litellm_key_for_user(user, session)

        mock_vault.retrieve_api_key_from_vault.assert_called_once_with(
            test_user_key.vault_path
        )
        assert result == expected_key

    @patch("src.litellm_service.get_vault")
    def test_retrieve_litellm_key_for_user_no_key(self, mock_get_vault, session, user):
        """Test retrieval when user has no LiteLLM key."""
        mock_vault = MagicMock()
        mock_get_vault.return_value = mock_vault

        result = retrieve_litellm_key_for_user(user, session)

        assert result is None
        mock_vault.retrieve_api_key_from_vault.assert_not_called()

    @patch("src.litellm_service.get_vault")
    def test_retrieve_litellm_key_for_user_vault_error(
        self, mock_get_vault, session, user, test_user_key
    ):
        """Test handling of VaultError when retrieving user key."""
        mock_vault = MagicMock()
        mock_vault.retrieve_api_key_from_vault.side_effect = VaultError(
            "Vault connection failed"
        )
        mock_get_vault.return_value = mock_vault

        with pytest.raises(VaultError, match="Vault connection failed"):
            retrieve_litellm_key_for_user(user, session)

        mock_vault.retrieve_api_key_from_vault.assert_called_once_with(
            test_user_key.vault_path
        )


class TestGetLiteLLMUserInfo:
    """Test cases for the get_litellm_user_info function."""

    @patch("src.litellm_service.requests.get")
    def test_get_litellm_user_info_success(self, mock_get, user):
        """Test successful retrieval of LiteLLM user info."""
        expected_response = {"user_id": str(user.id), "key": "test-key", "usage": 0}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = get_litellm_user_info(user, "test-master-key")

        mock_get.assert_called_once_with(
            f"{settings.litellm_url}/user/info?user_id={user.id}",
            headers={
                "Authorization": "Bearer test-master-key",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        assert result == expected_response

    @patch("src.litellm_service.requests.get")
    def test_get_litellm_user_info_error(self, mock_get, user):
        """Test handling of error response from LiteLLM API."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "User not found"
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to get user info from LiteLLM"):
            get_litellm_user_info(user, "test-master-key")

        mock_get.assert_called_once()


class TestCreateLiteLLMUser:
    """Test cases for the create_litellm_user function."""

    @patch("src.litellm_service.requests.post")
    def test_create_litellm_user_success(self, mock_post, user):
        """Test successful creation of LiteLLM user."""
        expected_key = "sk-proj-test-key-12345"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": expected_key}
        mock_post.return_value = mock_response

        result = create_litellm_user(user, "test-master-key")

        mock_post.assert_called_once_with(
            f"{settings.litellm_url}/user/new",
            headers={"Authorization": "Bearer test-master-key"},
            timeout=30,
            json={"user_id": str(user.id)},
        )
        assert result == expected_key

    @patch("src.litellm_service.requests.post")
    def test_create_litellm_user_error(self, mock_post, user):
        """Test handling of error response from LiteLLM API."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid request"
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to create user in LiteLLM"):
            create_litellm_user(user, "test-master-key")

        mock_post.assert_called_once()

    @patch("src.litellm_service.requests.post")
    def test_create_litellm_user_missing_key(self, mock_post, user):
        """Test handling of response with missing key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": None}
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to create user in LiteLLM"):
            create_litellm_user(user, "test-master-key")

        mock_post.assert_called_once()
