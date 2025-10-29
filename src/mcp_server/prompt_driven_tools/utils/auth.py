"""Authentication utilities for prompt-driven tools.

Provides user identification and authentication helpers for MCP tools.
"""

import uuid

from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request

__all__ = ["get_user_id_from_request"]


def get_user_id_from_request() -> uuid.UUID:
    """Extract user ID from request headers.

    For now, this returns a dummy UUID. In production, this should
    extract and validate the user ID from the JWT token.
    """
    # TODO: Extract actual user ID from JWT in Authorization header
    # For now, we'll use a placeholder that matches the test user
    request: Request = get_http_request()
    user_id_header = request.headers.get("X-User-Id")
    if user_id_header:
        return uuid.UUID(user_id_header)

    # Fallback for testing
    return uuid.uuid4()
