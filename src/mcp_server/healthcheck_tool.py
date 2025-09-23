import logging
from typing import Any, Dict

import requests
from fastmcp.server.dependencies import get_http_request
from mcp.server.fastmcp import Context
from starlette.requests import Request

from src.config import settings
from src.mcp_server.main import mcp  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Verify MCP server connectivity and authentication status.

    Tests the connection to the OpenBacklog API and validates that authentication
    headers are present and working correctly.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - Status of connectivity and authentication
        - Basic user/workspace information if successful
    """
    logger.info("Performing health check")
    try:
        request: Request = get_http_request()

        # Check for required headers
        authorization_header = request.headers.get("Authorization")
        workspace_id = request.headers.get("X-Workspace-Id")

        if not authorization_header:
            return {
                "status": "error",
                "type": "health_check",
                "error_message": "No authorization header found",
                "error_type": "authentication_error",
            }

        if not workspace_id:
            return {
                "status": "error",
                "type": "health_check",
                "error_message": "No workspace ID header found",
                "error_type": "workspace_error",
            }

        # Test API connectivity with a simple query
        test_url = f"{settings.postgrest_domain}/initiative?limit=1&workspace_id=eq.{workspace_id}"

        response = requests.get(
            test_url,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 200:
            logger.info("Health check successful")
            return {
                "status": "success",
                "type": "health_check",
                "message": "MCP server connectivity and authentication verified",
                "workspace_id": workspace_id,
                "api_endpoint": settings.postgrest_domain,
            }
        else:
            logger.warning(f"Health check failed with status {response.status_code}")
            return {
                "status": "error",
                "type": "health_check",
                "error_message": f"API returned status {response.status_code}",
                "error_type": "api_error",
            }

    except Exception as e:
        logger.exception(f"Health check failed with exception: {str(e)}")
        return {
            "status": "error",
            "type": "health_check",
            "error_message": f"Health check failed: {str(e)}",
            "error_type": "server_error",
        }
