import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_cached_manifest: Optional[Dict[str, str]] = None
_cached_css_path: Optional[str] = None
_css_path_cached: bool = False


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def load_asset_manifest() -> Optional[Dict[str, str]]:
    """
    Load the asset manifest JSON file with caching.

    Returns:
        The parsed manifest dictionary, or None if the file doesn't exist or can't be parsed.
    """
    global _cached_manifest

    if _cached_manifest is not None:
        return _cached_manifest

    try:
        project_root = get_project_root()
        manifest_path = project_root / "static/css/dist/asset-manifest.json"

        if not manifest_path.exists():
            logger.debug(f"Asset manifest not found at {manifest_path}")
            return None

        with open(manifest_path, "r") as f:
            _cached_manifest = json.load(f)
            logger.debug("Asset manifest loaded successfully")
            return _cached_manifest

    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load asset manifest: {e}")
        return None


def get_hashed_css_path() -> Optional[str]:
    """
    Get the hashed CSS file path from the asset manifest.

    Returns:
        The hashed CSS path if available, otherwise None.
    """
    global _cached_css_path, _css_path_cached

    if _css_path_cached:
        return _cached_css_path

    manifest = load_asset_manifest()

    if manifest and "css" in manifest and len(manifest["css"]) > 0:
        compiled_css_path = "static/css/dist/"
        _cached_css_path = "/" + compiled_css_path + manifest["css"][0]
        logger.debug(f"Using hashed CSS path: {_cached_css_path}")
    else:
        _cached_css_path = None
        logger.debug("No hashed CSS path available, returning None")

    _css_path_cached = True
    return _cached_css_path


def clear_cache() -> None:
    """Clear the cached manifest and CSS path. Useful for testing."""
    global _cached_manifest, _cached_css_path, _css_path_cached
    _cached_manifest = None
    _cached_css_path = None
    _css_path_cached = False
