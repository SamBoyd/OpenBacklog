import json
import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.mcp_server.auth_utils import extract_user_from_request, get_user_workspace
from src.mcp_server.main import mcp  # type: ignore
from src.models import Initiative

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
    session: Session = SessionLocal()
    try:
        # Verify authentication
        user_id, error = extract_user_from_request(session)
        if error:
            logger.warning(f"Health check failed: {error}")
            return {
                "status": "error",
                "type": "health_check",
                "error_message": error,
                "error_type": "auth_error",
            }

        if user_id is None:
            return {
                "status": "error",
                "type": "health_check",
                "error_message": "User ID not found",
                "error_type": "auth_error",
            }

        # Verify workspace access
        workspace, error = get_user_workspace(session, user_id)
        if error:
            logger.warning(f"Health check failed: {error}")
            return {
                "status": "error",
                "type": "health_check",
                "error_message": error,
                "error_type": "workspace_error",
            }

        # Test database connectivity with a simple query
        try:
            _ = (
                session.query(Initiative)
                .filter(Initiative.user_id == user_id)
                .limit(1)
                .count()
            )
        except Exception as e:
            logger.exception(f"Database connectivity test failed: {str(e)}")
            return {
                "status": "error",
                "type": "health_check",
                "error_message": f"Database connectivity test failed: {str(e)}",
                "error_type": "database_error",
            }

        logger.info(
            "Health check successful - Authentication and database connectivity verified"
        )
        return {
            "status": "success",
            "type": "health_check",
            "message": "MCP server authentication and database connectivity verified",
            "user_id": str(user_id),
            "workspace_id": str(workspace.id),
            "workspace_name": workspace.name,
        }

    except Exception as e:
        logger.exception(f"Health check failed with exception: {str(e)}")
        return {
            "status": "error",
            "type": "health_check",
            "error_message": f"Health check failed: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()
