import logging
import uuid
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.mcp_server.main import mcp  # type: ignore
from src.models import User, Workspace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp.tool()
async def create_workspace(name: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new workspace for the authenticated user.

    A workspace is a container for initiatives, tasks, and strategic planning.
    Creating a workspace automatically creates required dependencies (vision, roadmap).

    If the user doesn't have a workspace yet, this is the first step in their OpenBacklog setup.
    After creating a workspace, the user should create their first initiative.

    Args:
        name: Workspace name (required, max 255 characters)
        description: Optional workspace description

    Returns:
        {
            "status": "success" | "error",
            "type": "workspace",
            "message": "Created workspace '{name}'",
            "workspace": {
                "id": "<uuid>",
                "name": "...",
                "description": "...",
                "icon": "..."
            }
        }

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.
    """
    logger.info(f"Creating workspace with name: {name}")
    session: Session = SessionLocal()
    try:
        from src.mcp_server.auth_utils import extract_user_from_request

        user_id, error_message = extract_user_from_request(session)
        if error_message or user_id is None:
            return {
                "status": "error",
                "type": "workspace",
                "error_message": error_message or "Could not extract user ID",
            }

        user = session.query(User).filter(User.id == user_id).first()

        existing_workspace = (
            session.query(Workspace).filter(Workspace.user_id == user_id).first()
        )
        if existing_workspace:
            return {
                "status": "error",
                "type": "workspace",
                "error_message": "You already have a workspace. Each user can only have one workspace.",
                "error_type": "workspace_exists",
                "existing_workspace": {
                    "id": str(existing_workspace.id),
                    "name": existing_workspace.name,
                },
            }

        from src.controller import create_workspace as controller_create_workspace

        workspace = controller_create_workspace(
            user=user,
            name=name,
            description=description if description else None,
            icon=None,
            db=session,
        )

        workspace_data = {
            "id": str(workspace.id),
            "name": workspace.name,
            "description": workspace.description,
            "icon": workspace.icon,
        }

        logger.info(f"Successfully created workspace: {workspace.id}")

        return {
            "status": "success",
            "type": "workspace",
            "message": f"Created workspace '{name}'",
            "workspace": workspace_data,
        }

    except ValueError as e:
        logger.exception(f"Value error in create_workspace MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "workspace",
            "error_message": f"Validation error: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in create_workspace MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "workspace",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()
