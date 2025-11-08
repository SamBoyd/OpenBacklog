import logging
import uuid
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp  # type: ignore
from src.models import Initiative, Workspace

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
        user_id_str, workspace_id_str = get_auth_context(
            session, requires_workspace=True
        )
        user_id = uuid.UUID(user_id_str)
        workspace_id = uuid.UUID(workspace_id_str) if workspace_id_str else None

        workspace = (
            session.query(Workspace).filter(Workspace.id == workspace_id).first()
            if workspace_id
            else None
        )
        if workspace is None:
            raise MCPContextError(
                "Workspace not found for authenticated user",
                error_type="workspace_error",
            )

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

    except MCPContextError as e:
        logger.warning(f"Authorization error during health check: {str(e)}")
        return {
            "status": "error",
            "type": "health_check",
            "error_message": str(e),
            "error_type": e.error_type,
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
