"""
Management command to clean up expired MCP OAuth tokens from storage.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_help() -> str:
    """Return help text for this command."""
    return "Clean up expired MCP OAuth tokens from storage"


async def execute(args: Dict[str, Any]) -> int:
    """
    Clean up expired MCP OAuth tokens from storage.

    Args:
        args: Command-line arguments (currently unused)

    Returns:
        0 on success, 1 on error
    """
    try:
        from src.db import async_session_maker
        from src.mcp_server.storage import PostgreSQLMCPStorage

        logger.info("Starting MCP token cleanup...")

        # Initialize storage backend
        storage = PostgreSQLMCPStorage(async_session_maker)

        # Run cleanup
        deleted_count = await storage.cleanup_expired()

        logger.info(
            f"MCP token cleanup complete: {deleted_count} expired tokens deleted"
        )
        return 0

    except Exception as e:
        logger.error(f"Error cleaning up MCP tokens: {e}")
        return 1
