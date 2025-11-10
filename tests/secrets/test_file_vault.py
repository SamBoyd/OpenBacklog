"""Unit tests for src.secrets.file_vault module."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.secrets.file_vault import FileVault
from src.secrets.vault_interface import VaultInterface


class TestFileVaultInitialization:
    """Tests for FileVault initialization."""

    def test_file_vault_initializes_with_default_path(self):
        """Test that FileVault initializes with default secrets_dir."""
        vault = FileVault()
        assert vault.secrets_dir == Path("/app/secrets")
        assert vault._available is False

    def test_file_vault_initializes_with_custom_path(self):
        """Test that FileVault initializes with custom secrets_dir."""
        custom_path = "/custom/secrets/path"
        vault = FileVault(secrets_dir=custom_path)
        assert vault.secrets_dir == Path(custom_path)
        assert vault._available is False

    def test_file_vault_implements_vault_interface(self):
        """Test that FileVault implements VaultInterface."""
        vault = FileVault()
        assert isinstance(vault, VaultInterface)

    def test_file_vault_is_not_available_initially(self):
        """Test that vault is marked unavailable before initialization."""
        vault = FileVault()
        assert vault.is_available() is False


class TestFileVaultInitializeMethod:
    """Tests for FileVault.initialize() method."""

    def test_initialize_creates_directory_successfully(self, tmp_path):
        """Test that initialize() creates the secrets directory."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        assert tmp_path.exists()
        assert vault.is_available() is True

    def test_initialize_marks_vault_available(self, tmp_path):
        """Test that initialize() marks vault as available on success."""
        vault = FileVault(secrets_dir=str(tmp_path))
        assert vault.is_available() is False

        vault.initialize()

        assert vault.is_available() is True

    def test_initialize_with_existing_directory(self, tmp_path):
        """Test that initialize() handles existing directory gracefully."""
        # Pre-create the directory
        tmp_path.mkdir(parents=True, exist_ok=True)

        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        assert tmp_path.exists()
        assert vault.is_available() is True

    def test_initialize_creates_nested_directories(self, tmp_path):
        """Test that initialize() creates nested directory paths."""
        nested_path = tmp_path / "nested" / "secrets" / "path"
        vault = FileVault(secrets_dir=str(nested_path))

        vault.initialize()

        assert nested_path.exists()
        assert vault.is_available() is True

    def test_initialize_logs_info_on_success(self, tmp_path, caplog):
        """Test that initialize() logs info message on success."""
        vault = FileVault(secrets_dir=str(tmp_path))

        with caplog.at_level(logging.INFO):
            vault.initialize()

        assert "Initializing file-based vault" in caplog.text
        assert "successfully initialized" in caplog.text

    def test_initialize_handles_permission_error(self, caplog):
        """Test that initialize() handles permission errors gracefully."""
        vault = FileVault(secrets_dir="/root/cannot/access/this")

        with caplog.at_level(logging.ERROR):
            vault.initialize()

        assert vault.is_available() is False
        assert "Failed to initialize file vault" in caplog.text

    def test_initialize_does_not_raise_exceptions(self):
        """Test that initialize() never raises exceptions."""
        vault = FileVault(secrets_dir="/invalid/path/that/cannot/be/created")
        # Should not raise
        vault.initialize()
        assert vault.is_available() is False


class TestFileVaultStoreSecret:
    """Tests for FileVault.store_secret() method."""

    @pytest.fixture
    def initialized_vault(self, tmp_path):
        """Create an initialized vault for testing."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()
        return vault

    def test_store_secret_creates_json_file(self, initialized_vault):
        """Test that store_secret() creates a JSON file."""
        path = "user/api_keys/openai"
        value = {"api_key": "sk-test123"}

        result = initialized_vault.store_secret(path, value)

        assert result == path
        # Verify file was created
        file_path = initialized_vault.secrets_dir / f"{path}.json"
        assert file_path.exists()

    def test_store_secret_writes_correct_json(self, initialized_vault):
        """Test that store_secret() writes correct JSON content."""
        path = "user/credentials/db"
        value = {"username": "admin", "password": "secret"}

        initialized_vault.store_secret(path, value)

        file_path = initialized_vault.secrets_dir / f"{path}.json"
        with open(file_path, "r") as f:
            stored_data = json.load(f)

        assert stored_data == value

    def test_store_secret_creates_nested_directories(self, initialized_vault):
        """Test that store_secret() creates nested directories."""
        path = "deeply/nested/path/to/secret"
        value = {"key": "value"}

        initialized_vault.store_secret(path, value)

        file_path = initialized_vault.secrets_dir / f"{path}.json"
        assert file_path.exists()
        assert file_path.parent.exists()

    def test_store_secret_overwrites_existing_file(self, initialized_vault):
        """Test that store_secret() overwrites existing secrets."""
        path = "user/api_keys/openai"
        old_value = {"api_key": "old_key"}
        new_value = {"api_key": "new_key"}

        initialized_vault.store_secret(path, old_value)
        initialized_vault.store_secret(path, new_value)

        file_path = initialized_vault.secrets_dir / f"{path}.json"
        with open(file_path, "r") as f:
            stored_data = json.load(f)

        assert stored_data == new_value

    def test_store_secret_with_complex_nested_dict(self, initialized_vault):
        """Test that store_secret() handles complex nested structures."""
        path = "complex/secret"
        value = {
            "api_key": "test",
            "nested": {
                "level1": {"level2": "value"},
                "list": [1, 2, 3],
            },
        }

        initialized_vault.store_secret(path, value)

        file_path = initialized_vault.secrets_dir / f"{path}.json"
        with open(file_path, "r") as f:
            stored_data = json.load(f)

        assert stored_data == value

    def test_store_secret_raises_type_error_for_invalid_path(self, initialized_vault):
        """Test that store_secret() raises TypeError for non-string path."""
        with pytest.raises(TypeError) as exc_info:
            initialized_vault.store_secret(123, {"key": "value"})

        assert "Path must be string" in str(exc_info.value)

    def test_store_secret_raises_type_error_for_invalid_value(self, initialized_vault):
        """Test that store_secret() raises TypeError for non-dict value."""
        with pytest.raises(TypeError) as exc_info:
            initialized_vault.store_secret("path/to/secret", "not_a_dict")

        assert "value must be dict" in str(exc_info.value)

    def test_store_secret_raises_value_error_for_empty_path(self, initialized_vault):
        """Test that store_secret() raises ValueError for empty path."""
        with pytest.raises(ValueError) as exc_info:
            initialized_vault.store_secret("", {"key": "value"})

        assert "Path and value cannot be empty" in str(exc_info.value)

    def test_store_secret_raises_value_error_for_empty_value(self, initialized_vault):
        """Test that store_secret() raises ValueError for empty value dict."""
        with pytest.raises(ValueError) as exc_info:
            initialized_vault.store_secret("path/to/secret", {})

        assert "Path and value cannot be empty" in str(exc_info.value)

    def test_store_secret_returns_none_when_unavailable(self, tmp_path):
        """Test that store_secret() returns None when vault is unavailable."""
        vault = FileVault(secrets_dir=str(tmp_path))
        # Don't initialize, so vault is unavailable
        assert vault.is_available() is False

        result = vault.store_secret("path/to/secret", {"key": "value"})

        assert result is None

    def test_store_secret_logs_warning_when_unavailable(self, tmp_path, caplog):
        """Test that store_secret() logs warning when unavailable."""
        vault = FileVault(secrets_dir=str(tmp_path))

        with caplog.at_level(logging.WARNING):
            vault.store_secret("path/to/secret", {"key": "value"})

        assert "File vault unavailable" in caplog.text

    def test_store_secret_logs_success(self, initialized_vault, caplog):
        """Test that store_secret() logs success message."""
        with caplog.at_level(logging.INFO):
            initialized_vault.store_secret("test/path", {"key": "value"})

        assert "Secret successfully stored" in caplog.text

    def test_store_secret_raises_runtime_error_on_write_failure(
        self, initialized_vault
    ):
        """Test that store_secret() raises RuntimeError on write failure."""
        with patch("builtins.open", side_effect=IOError("Cannot write file")):
            with pytest.raises(RuntimeError) as exc_info:
                initialized_vault.store_secret("test/path", {"key": "value"})

            assert "Failed to store secret" in str(exc_info.value)


class TestFileVaultRetrieveSecret:
    """Tests for FileVault.retrieve_secret() method."""

    @pytest.fixture
    def vault_with_secret(self, tmp_path):
        """Create a vault with a pre-stored secret."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        # Store a test secret
        test_secret = {"api_key": "sk-test123", "model": "gpt-4"}
        vault.store_secret("user/api_keys/openai", test_secret)

        return vault

    def test_retrieve_secret_returns_correct_data(self, vault_with_secret):
        """Test that retrieve_secret() returns stored secret data."""
        expected = {"api_key": "sk-test123", "model": "gpt-4"}

        result = vault_with_secret.retrieve_secret("user/api_keys/openai")

        assert result == expected

    def test_retrieve_secret_with_complex_nested_data(self, tmp_path):
        """Test that retrieve_secret() handles complex nested structures."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        original_data = {
            "db": {
                "host": "localhost",
                "port": 5432,
                "credentials": {"user": "admin", "pass": "secret"},
            },
            "cache": ["redis1", "redis2"],
        }

        vault.store_secret("complex/nested", original_data)
        result = vault.retrieve_secret("complex/nested")

        assert result == original_data

    def test_retrieve_secret_raises_type_error_for_non_string_path(
        self, vault_with_secret
    ):
        """Test that retrieve_secret() raises TypeError for non-string path."""
        with pytest.raises(TypeError) as exc_info:
            vault_with_secret.retrieve_secret(123)

        assert "Vault path must be a string" in str(exc_info.value)

    def test_retrieve_secret_raises_value_error_for_empty_path(self, vault_with_secret):
        """Test that retrieve_secret() raises ValueError for empty path."""
        with pytest.raises(ValueError) as exc_info:
            vault_with_secret.retrieve_secret("")

        assert "Vault path cannot be empty" in str(exc_info.value)

    def test_retrieve_secret_raises_runtime_error_for_missing_secret(
        self, vault_with_secret
    ):
        """Test that retrieve_secret() raises RuntimeError for missing secret."""
        with pytest.raises(RuntimeError) as exc_info:
            vault_with_secret.retrieve_secret("nonexistent/path")

        assert "No secret found" in str(exc_info.value) or "Secret not found" in str(
            exc_info.value
        )

    def test_retrieve_secret_raises_runtime_error_for_invalid_json(self, tmp_path):
        """Test that retrieve_secret() raises RuntimeError for invalid JSON."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        # Write invalid JSON directly
        file_path = tmp_path / "invalid_secret.json"
        file_path.write_text("{ invalid json }")

        with pytest.raises(RuntimeError) as exc_info:
            vault.retrieve_secret("invalid_secret")

        assert "Invalid JSON" in str(exc_info.value)

    def test_retrieve_secret_returns_none_when_unavailable(self, tmp_path):
        """Test that retrieve_secret() returns None when vault is unavailable."""
        vault = FileVault(secrets_dir=str(tmp_path))
        # Don't initialize, so vault is unavailable

        result = vault.retrieve_secret("path/to/secret")

        assert result is None

    def test_retrieve_secret_logs_warning_when_unavailable(self, tmp_path, caplog):
        """Test that retrieve_secret() logs warning when unavailable."""
        vault = FileVault(secrets_dir=str(tmp_path))

        with caplog.at_level(logging.WARNING):
            vault.retrieve_secret("path/to/secret")

        assert "File vault unavailable" in caplog.text

    def test_retrieve_secret_logs_success(self, vault_with_secret, caplog):
        """Test that retrieve_secret() logs success message."""
        with caplog.at_level(logging.INFO):
            vault_with_secret.retrieve_secret("user/api_keys/openai")

        assert "Secret successfully retrieved" in caplog.text

    def test_retrieve_secret_logs_error_for_missing_secret(
        self, vault_with_secret, caplog
    ):
        """Test that retrieve_secret() logs error for missing secret."""
        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError):
                vault_with_secret.retrieve_secret("nonexistent/path")

        assert (
            "Failed to retrieve secret from file vault" in caplog.text
            or "Secret not found" in caplog.text
        )

    def test_retrieve_secret_raises_runtime_error_on_read_failure(
        self, vault_with_secret
    ):
        """Test that retrieve_secret() raises RuntimeError on read failure."""
        with patch("builtins.open", side_effect=IOError("Cannot read file")):
            with pytest.raises(RuntimeError) as exc_info:
                vault_with_secret.retrieve_secret("user/api_keys/openai")

            assert "Failed to retrieve secret" in str(exc_info.value)


class TestFileVaultIntegration:
    """Integration tests for FileVault."""

    def test_store_and_retrieve_roundtrip(self, tmp_path):
        """Test that stored secrets can be retrieved correctly."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        original_data = {
            "api_key": "sk-test123",
            "model": "gpt-4",
            "tokens": [1, 2, 3],
        }

        # Store and retrieve
        vault.store_secret("user/openai", original_data)
        retrieved_data = vault.retrieve_secret("user/openai")

        assert retrieved_data == original_data

    def test_multiple_secrets_stored_independently(self, tmp_path):
        """Test that multiple secrets are stored independently."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        secret1 = {"api_key": "openai_key"}
        secret2 = {"api_key": "anthropic_key"}
        secret3 = {"username": "admin"}

        vault.store_secret("user/openai", secret1)
        vault.store_secret("user/anthropic", secret2)
        vault.store_secret("user/credentials", secret3)

        assert vault.retrieve_secret("user/openai") == secret1
        assert vault.retrieve_secret("user/anthropic") == secret2
        assert vault.retrieve_secret("user/credentials") == secret3

    def test_secrets_persisted_across_vault_instances(self, tmp_path):
        """Test that secrets persisted on disk can be retrieved by new vault instance."""
        vault1 = FileVault(secrets_dir=str(tmp_path))
        vault1.initialize()
        secret_data = {"api_key": "sk-test123"}
        vault1.store_secret("user/openai", secret_data)

        # Create a new vault instance pointing to the same directory
        vault2 = FileVault(secrets_dir=str(tmp_path))
        vault2.initialize()

        # Should be able to retrieve the secret stored by vault1
        retrieved = vault2.retrieve_secret("user/openai")
        assert retrieved == secret_data

    def test_special_characters_in_paths(self, tmp_path):
        """Test that paths with special characters are handled correctly."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        paths = [
            "user-123/api-keys/open-ai",
            "user_456/db_credentials",
            "prod.config/api.keys",
        ]

        for path in paths:
            data = {"key": path}
            vault.store_secret(path, data)
            assert vault.retrieve_secret(path) == data

    def test_large_secret_values(self, tmp_path):
        """Test that large secret values are handled correctly."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        # Create a large secret value
        large_value = {
            "data": "x" * 100000,  # 100KB of data
            "nested": {"more": "y" * 50000},
        }

        vault.store_secret("user/large_secret", large_value)
        retrieved = vault.retrieve_secret("user/large_secret")

        assert retrieved == large_value

    def test_concurrent_store_operations(self, tmp_path):
        """Test that multiple store operations don't interfere with each other."""
        vault = FileVault(secrets_dir=str(tmp_path))
        vault.initialize()

        # Store multiple secrets in sequence
        for i in range(10):
            vault.store_secret(f"secret_{i}", {"value": i})

        # Verify all were stored correctly
        for i in range(10):
            assert vault.retrieve_secret(f"secret_{i}") == {"value": i}


class TestFileVaultSecretFilePath:
    """Tests for FileVault._get_secret_file_path() method."""

    def test_secret_file_path_adds_json_extension(self):
        """Test that _get_secret_file_path adds .json extension."""
        vault = FileVault(secrets_dir="/app/secrets")
        path = vault._get_secret_file_path("user/api_keys/openai")

        assert str(path).endswith(".json")

    def test_secret_file_path_preserves_directory_structure(self):
        """Test that _get_secret_file_path preserves directory structure."""
        vault = FileVault(secrets_dir="/app/secrets")
        path = vault._get_secret_file_path("user/api_keys/openai")

        assert "user" in str(path)
        assert "api_keys" in str(path)
        assert "openai.json" in str(path)

    def test_secret_file_path_uses_secrets_dir(self):
        """Test that _get_secret_file_path uses the configured secrets_dir."""
        custom_dir = "/custom/vault/path"
        vault = FileVault(secrets_dir=custom_dir)
        path = vault._get_secret_file_path("user/secret")

        assert str(path).startswith(custom_dir)

    def test_secret_file_path_handles_single_level_path(self):
        """Test that _get_secret_file_path handles single-level paths."""
        vault = FileVault(secrets_dir="/app/secrets")
        path = vault._get_secret_file_path("secret")

        assert path == Path("/app/secrets/secret.json")

    def test_secret_file_path_handles_deep_nesting(self):
        """Test that _get_secret_file_path handles deeply nested paths."""
        vault = FileVault(secrets_dir="/app/secrets")
        deep_path = "a/b/c/d/e/f/g/h/secret"
        path = vault._get_secret_file_path(deep_path)

        assert "a/b/c/d/e/f/g/h/secret.json" in str(path)
