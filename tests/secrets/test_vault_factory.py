"""Unit tests for src.secrets.vault_factory module."""

import logging
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.secrets.vault_factory import get_vault, reset_vault


class TestGetVault:
    """Tests for get_vault() factory function."""

    @pytest.fixture(autouse=True)
    def cleanup_vault(self):
        """Reset vault instance before each test."""
        reset_vault()
        yield
        reset_vault()

    def test_get_vault_returns_vault_interface_instance(self):
        """Test that get_vault returns an instance implementing VaultInterface."""
        from src.secrets.vault_interface import VaultInterface

        vault = get_vault()
        assert isinstance(vault, VaultInterface)

    def test_get_vault_singleton_pattern(self):
        """Test that get_vault returns the same instance on repeated calls."""
        vault1 = get_vault()
        vault2 = get_vault()
        assert vault1 is vault2

    @patch("src.config.settings")
    def test_get_vault_creates_file_vault_when_type_is_file(self, mock_settings):
        """Test that get_vault creates FileVault when vault_type is 'file'."""
        mock_settings.vault_type = "file"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = "/app/secrets"

        reset_vault()
        vault = get_vault()

        from src.secrets.file_vault import FileVault

        assert isinstance(vault, FileVault)

    @patch("src.config.settings")
    def test_get_vault_creates_hashicorp_vault_when_type_is_hashicorp(
        self, mock_settings
    ):
        """Test that get_vault creates HashicorpVault when vault_type is 'hashicorp'."""
        mock_settings.vault_type = "hashicorp"
        mock_settings.environment = "development"

        reset_vault()
        vault = get_vault()

        from src.secrets.hashicorp_vault import HashicorpVault

        assert isinstance(vault, HashicorpVault)

    @patch("src.config.settings")
    def test_get_vault_handles_mixed_case_vault_type(self, mock_settings):
        """Test that get_vault handles mixed case vault_type correctly."""
        mock_settings.vault_type = "FILE"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = "/app/secrets"

        reset_vault()
        vault = get_vault()

        from src.secrets.file_vault import FileVault

        assert isinstance(vault, FileVault)

    @patch("src.config.settings")
    def test_get_vault_raises_error_for_unknown_vault_type(self, mock_settings):
        """Test that get_vault raises ValueError for unknown vault type."""
        mock_settings.vault_type = "unknown_type"
        mock_settings.environment = "development"

        reset_vault()
        with pytest.raises(ValueError) as exc_info:
            get_vault()

        assert "Unknown vault type: unknown_type" in str(exc_info.value)
        assert "Must be 'hashicorp' or 'file'" in str(exc_info.value)

    @patch("src.config.settings")
    def test_get_vault_raises_runtime_error_for_file_vault_in_production(
        self, mock_settings
    ):
        """Test that get_vault raises RuntimeError when file vault is used in production."""
        mock_settings.vault_type = "file"
        mock_settings.environment = "production"
        mock_settings.secrets_dir = "/app/secrets"

        reset_vault()
        with pytest.raises(RuntimeError) as exc_info:
            get_vault()

        assert "File-based vault cannot be used in production" in str(exc_info.value)
        assert "Set VAULT_TYPE=hashicorp for production environments" in str(
            exc_info.value
        )

    @patch("src.config.settings")
    def test_get_vault_allows_file_vault_in_development(self, mock_settings):
        """Test that get_vault allows file vault in development environment."""
        mock_settings.vault_type = "file"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = "/app/secrets"

        reset_vault()
        vault = get_vault()

        from src.secrets.file_vault import FileVault

        assert isinstance(vault, FileVault)

    @patch("src.config.settings")
    def test_get_vault_allows_hashicorp_vault_in_production(self, mock_settings):
        """Test that get_vault allows HashiCorp vault in production."""
        mock_settings.vault_type = "hashicorp"
        mock_settings.environment = "production"

        reset_vault()
        vault = get_vault()

        from src.secrets.hashicorp_vault import HashicorpVault

        assert isinstance(vault, HashicorpVault)

    @patch("src.config.settings")
    def test_get_vault_initializes_vault_instance(self, mock_settings):
        """Test that get_vault calls initialize() on the vault instance."""
        mock_settings.vault_type = "file"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = "/app/secrets"

        reset_vault()

        with patch("src.secrets.file_vault.FileVault.initialize") as mock_init:
            vault = get_vault()
            mock_init.assert_called_once()

    @patch("src.config.settings")
    def test_get_vault_logs_file_vault_creation(self, mock_settings, caplog):
        """Test that get_vault logs when creating file-based vault."""
        mock_settings.vault_type = "file"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = "/app/secrets"

        reset_vault()

        with caplog.at_level(logging.INFO):
            get_vault()

        assert "Creating file-based vault instance" in caplog.text

    @patch("src.config.settings")
    def test_get_vault_logs_hashicorp_vault_creation(self, mock_settings, caplog):
        """Test that get_vault logs when creating HashiCorp vault."""
        mock_settings.vault_type = "hashicorp"
        mock_settings.environment = "development"

        reset_vault()

        with caplog.at_level(logging.INFO):
            get_vault()

        assert "Creating HashiCorp Vault instance" in caplog.text

    @patch("src.config.settings")
    def test_get_vault_passes_secrets_dir_to_file_vault(self, mock_settings):
        """Test that get_vault passes secrets_dir setting to FileVault."""
        expected_dir = "/custom/secrets/path"
        mock_settings.vault_type = "file"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = expected_dir

        reset_vault()

        with patch("src.secrets.file_vault.FileVault") as mock_file_vault:
            get_vault()
            mock_file_vault.assert_called_once_with(secrets_dir=expected_dir)

    @patch("src.config.settings")
    def test_get_vault_with_multiple_reset_cycles(self, mock_settings):
        """Test that reset_vault properly clears singleton for different configurations."""
        mock_settings.vault_type = "file"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = "/app/secrets"

        # First call
        reset_vault()
        vault1 = get_vault()
        from src.secrets.file_vault import FileVault

        assert isinstance(vault1, FileVault)

        # Reset and change type
        reset_vault()
        mock_settings.vault_type = "hashicorp"
        vault2 = get_vault()
        from src.secrets.hashicorp_vault import HashicorpVault

        assert isinstance(vault2, HashicorpVault)
        assert vault1 is not vault2


class TestResetVault:
    """Tests for reset_vault() function."""

    def test_reset_vault_clears_singleton_instance(self):
        """Test that reset_vault clears the singleton instance."""
        vault1 = get_vault()
        reset_vault()
        vault2 = get_vault()
        assert vault1 is not vault2

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up after each test."""
        yield
        reset_vault()

    def test_reset_vault_can_be_called_multiple_times(self):
        """Test that reset_vault can be safely called multiple times."""
        get_vault()
        reset_vault()
        reset_vault()  # Should not raise
        reset_vault()  # Should not raise

    def test_reset_vault_allows_creating_new_instance(self):
        """Test that after reset_vault, get_vault creates a new instance."""
        vault1 = get_vault()
        reset_vault()
        vault2 = get_vault()

        assert vault1 is not vault2


class TestVaultFactoryIntegration:
    """Integration tests for vault factory with actual implementations."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up after each test."""
        yield
        reset_vault()

    @patch("src.config.settings")
    def test_file_vault_integration(self, mock_settings, tmp_path):
        """Test integration with FileVault implementation."""
        mock_settings.vault_type = "file"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = str(tmp_path)

        reset_vault()
        vault = get_vault()

        # Verify vault is available after initialization
        assert vault.is_available() is True

    @patch("src.config.settings")
    def test_hashicorp_vault_integration_graceful_failure(self, mock_settings):
        """Test that HashiCorp vault fails gracefully when initialization fails."""
        mock_settings.vault_type = "hashicorp"
        mock_settings.environment = "development"

        reset_vault()
        vault = get_vault()

        # HashiCorp vault should be marked unavailable if initialization fails
        # (since it can't connect to actual Vault server in tests)
        assert vault.is_available() is False

    @patch("src.config.settings")
    def test_vault_factory_does_not_raise_on_failed_initialization(self, mock_settings):
        """Test that factory doesn't raise exceptions on vault initialization failure."""
        mock_settings.vault_type = "hashicorp"
        mock_settings.environment = "development"

        reset_vault()
        # Should not raise even though HashiCorp vault can't initialize
        vault = get_vault()
        assert vault is not None


class TestVaultFactoryErrorHandling:
    """Tests for error handling in vault factory."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up after each test."""
        yield
        reset_vault()

    @patch("src.config.settings")
    def test_production_safety_guard_exact_message(self, mock_settings):
        """Test that production safety guard provides clear error message."""
        mock_settings.vault_type = "file"
        mock_settings.environment = "production"
        mock_settings.secrets_dir = "/app/secrets"

        reset_vault()

        with pytest.raises(RuntimeError) as exc_info:
            get_vault()

        error_message = str(exc_info.value)
        assert "File-based vault" in error_message
        assert "production" in error_message
        assert "hashicorp" in error_message

    @patch("src.config.settings")
    def test_unknown_vault_type_error_includes_valid_options(self, mock_settings):
        """Test that unknown vault type error lists valid options."""
        mock_settings.vault_type = "invalid_type"
        mock_settings.environment = "development"

        reset_vault()

        with pytest.raises(ValueError) as exc_info:
            get_vault()

        error_message = str(exc_info.value)
        assert "hashicorp" in error_message
        assert "file" in error_message

    @patch("src.config.settings")
    def test_vault_type_case_insensitivity_with_error(self, mock_settings):
        """Test that vault_type comparison is case-insensitive."""
        # Test lowercase
        mock_settings.vault_type = "file"
        mock_settings.environment = "development"
        mock_settings.secrets_dir = "/app/secrets"

        reset_vault()
        from src.secrets.file_vault import FileVault

        vault = get_vault()
        assert isinstance(vault, FileVault)

        # Test uppercase
        reset_vault()
        mock_settings.vault_type = "FILE"
        vault = get_vault()
        assert isinstance(vault, FileVault)

        # Test mixed case
        reset_vault()
        mock_settings.vault_type = "FiLe"
        vault = get_vault()
        assert isinstance(vault, FileVault)
