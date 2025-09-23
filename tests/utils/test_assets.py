import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.utils.assets import (
    clear_cache,
    get_hashed_css_path,
    get_project_root,
    load_asset_manifest,
)


class TestAssets:
    def setup_method(self):
        """Clear the cache before each test to ensure clean state."""
        clear_cache()

    def test_get_project_root(self):
        """Test that get_project_root returns the correct path."""
        root = get_project_root()
        assert root.name == "OpenBacklog"
        assert root.is_dir()

    @patch("src.utils.assets.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_asset_manifest_success(self, mock_file, mock_exists):
        """Test successful loading of asset manifest."""
        mock_exists.return_value = True
        manifest_data = {"css": ["styles.abc123.css"], "js": ["app.def456.js"]}
        mock_file.return_value.read.return_value = json.dumps(manifest_data)

        result = load_asset_manifest()

        assert result == manifest_data
        mock_exists.assert_called_once()
        mock_file.assert_called_once()

    @patch("src.utils.assets.Path.exists")
    def test_load_asset_manifest_file_not_exists(self, mock_exists):
        """Test loading when asset manifest file doesn't exist."""
        mock_exists.return_value = False

        result = load_asset_manifest()

        assert result is None
        mock_exists.assert_called_once()

    @patch("src.utils.assets.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_asset_manifest_json_decode_error(self, mock_file, mock_exists):
        """Test loading with invalid JSON content."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "invalid json content"

        result = load_asset_manifest()

        assert result is None

    @patch("src.utils.assets.Path.exists")
    @patch("builtins.open")
    def test_load_asset_manifest_os_error(self, mock_file, mock_exists):
        """Test loading with OS error (permission denied, etc)."""
        mock_exists.return_value = True
        mock_file.side_effect = OSError("Permission denied")

        result = load_asset_manifest()

        assert result is None

    @patch("src.utils.assets.load_asset_manifest")
    def test_get_hashed_css_path_with_manifest(self, mock_load_manifest):
        """Test getting hashed CSS path when manifest is available."""
        mock_load_manifest.return_value = {"css": ["styles.abc123.css"]}

        result = get_hashed_css_path()

        assert result == "/static/css/dist/styles.abc123.css"

    @patch("src.utils.assets.load_asset_manifest")
    def test_get_hashed_css_path_no_manifest(self, mock_load_manifest):
        """Test getting CSS path when manifest is not available."""
        mock_load_manifest.return_value = None

        result = get_hashed_css_path()

        assert result is None

    @patch("src.utils.assets.load_asset_manifest")
    def test_get_hashed_css_path_empty_css_array(self, mock_load_manifest):
        """Test getting CSS path when manifest has empty CSS array."""
        mock_load_manifest.return_value = {"css": []}

        result = get_hashed_css_path()

        assert result is None

    @patch("src.utils.assets.load_asset_manifest")
    def test_get_hashed_css_path_no_css_key(self, mock_load_manifest):
        """Test getting CSS path when manifest has no 'css' key."""
        mock_load_manifest.return_value = {"js": ["app.def456.js"]}

        result = get_hashed_css_path()

        assert result is None

    @patch("src.utils.assets.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_caching_behavior_manifest(self, mock_file, mock_exists):
        """Test that manifest is cached and not loaded multiple times."""
        mock_exists.return_value = True
        manifest_data = {"css": ["styles.abc123.css"]}
        mock_file.return_value.read.return_value = json.dumps(manifest_data)

        # Call multiple times
        result1 = load_asset_manifest()
        result2 = load_asset_manifest()

        assert result1 == manifest_data
        assert result2 == manifest_data
        # File should only be opened once due to caching
        mock_file.assert_called_once()

    @patch("src.utils.assets.load_asset_manifest")
    def test_caching_behavior_css_path(self, mock_load_manifest):
        """Test that CSS path is cached and manifest not loaded multiple times."""
        mock_load_manifest.return_value = {"css": ["styles.abc123.css"]}

        # Call multiple times
        result1 = get_hashed_css_path()
        result2 = get_hashed_css_path()

        assert result1 == "/static/css/dist/styles.abc123.css"
        assert result2 == "/static/css/dist/styles.abc123.css"
        # Should only be called once due to caching
        mock_load_manifest.assert_called_once()

    @patch("src.utils.assets.load_asset_manifest")
    def test_clear_cache_functionality(self, mock_load_manifest):
        """Test that clearing cache allows fresh loading."""
        mock_load_manifest.return_value = {"css": ["styles.abc123.css"]}

        # Load once
        get_hashed_css_path()
        assert mock_load_manifest.call_count == 1

        # Clear cache
        clear_cache()

        # Load again - should call load_asset_manifest again
        get_hashed_css_path()
        assert mock_load_manifest.call_count == 2

    @patch("src.utils.assets.load_asset_manifest")
    def test_caching_none_values(self, mock_load_manifest):
        """Test that None values are properly cached."""
        mock_load_manifest.return_value = None

        # Call multiple times
        result1 = get_hashed_css_path()
        result2 = get_hashed_css_path()

        assert result1 is None
        assert result2 is None
        # Should only be called once due to caching
        mock_load_manifest.assert_called_once()
