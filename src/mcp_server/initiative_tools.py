import logging
import urllib.parse
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
async def get_active_initiatives() -> Dict[str, Any]:
    """
    Fetch all initiatives marked as 'IN_PROGRESS' (corresponding to 'Doing' status).

    Returns initiatives that are currently active and available for work.
    Used in the workflow to let users select which initiative to work on.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - List of active initiatives with full context (title, description, identifier)
    """
    logger.info("Fetching active initiatives")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        logger.info(f"Authorization header: {authorization_header}")
        if not authorization_header:
            return {
                "status": "error",
                "type": "initiative",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")
        logger.info(f"Workspace ID: {workspace_id}")

        # Query for initiatives with IN_PROGRESS status
        url = f"{settings.postgrest_domain}/initiative?status=eq.IN_PROGRESS&workspace_id=eq.{workspace_id}&select=*"

        response = requests.get(
            url,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.exception(
                f"Error in get_active_initiatives MCP tool: {response.status_code} - {response.json()}"
            )
            return {
                "status": "error",
                "type": "initiative",
                "error_message": f"Server error: {response.status_code}",
            }

        initiatives_data = response.json()

        logger.info(f"Found {len(initiatives_data)} active initiatives")

        return {
            "status": "success",
            "type": "initiative",
            "message": f"Found {len(initiatives_data)} active initiatives",
            "data": initiatives_data,
        }

    except Exception as e:
        logger.exception(f"Error in get_active_initiatives MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }


@mcp.tool()
async def search_initiatives(
    query: str,
) -> Dict[str, Any]:
    """
    Search for initiatives by title. Uses Postgrest LIKE operator.

    Args:
        - query: The query string to search the titles, descriptions, and identifiers of the user's initiatives

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - a list of initiatives that match the query
    """
    logger.info(f"Searching for initiatives with query {query}")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        logger.info(f"Authorization header: {authorization_header}")
        if not authorization_header:
            return {
                "status": "error",
                "type": "initiative",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")
        logger.info(f"Workspace ID: {workspace_id}")

        # postgrest query url
        url_encoded_query = urllib.parse.quote(query)
        url = f"{settings.postgrest_domain}/initiative?or(title.plfts({url_encoded_query}),description.plfts({url_encoded_query}),identifier.plfts({url_encoded_query}))&workspace_id=eq.{workspace_id}"

        response = requests.get(
            url,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.exception(
                f"Error in search_initiatives MCP tool: {response.status_code} - {response.json()}"
            )
            return {
                "status": "error",
                "type": "initiative",
                "error_message": f"Server error: {response.status_code}",
            }

        initiatives_data = response.json()

        logger.info(f"Found {len(initiatives_data)} initiatives")

        return {
            "status": "success",
            "type": "initiative",
            "data": initiatives_data,
        }

    except Exception as e:
        logger.exception(f"Error in search_initiatives MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
