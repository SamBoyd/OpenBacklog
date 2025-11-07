import logging
import uuid
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.initiative_management.initiative_controller import (
    InitiativeController,
    InitiativeControllerError,
    InitiativeNotFoundError,
)
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
    session: Session = SessionLocal()
    try:
        from src.mcp_server.auth_utils import (
            extract_user_from_request,
            get_user_workspace,
        )

        user_id, error_message = extract_user_from_request(session)
        if error_message or user_id is None:
            return {
                "status": "error",
                "type": "initiative",
                "error_message": error_message or "Could not extract user ID",
            }

        workspace, workspace_error = get_user_workspace(session, user_id)
        if workspace_error or workspace is None:
            return {
                "status": "error",
                "type": "initiative",
                "error_message": workspace_error or "Workspace not found",
            }

        # Use InitiativeController to get active initiatives
        controller = InitiativeController(session)
        initiatives = controller.get_active_initiatives(user_id, workspace.id)

        # Convert to dict format expected by MCP clients
        initiatives_data = [
            {
                "id": str(initiative.id),
                "title": initiative.title,
                "description": initiative.description,
                "identifier": initiative.identifier,
                "status": initiative.status.value,
                "type": initiative.type,
                "created_at": (
                    initiative.created_at.isoformat() if initiative.created_at else None
                ),
                "updated_at": (
                    initiative.updated_at.isoformat() if initiative.updated_at else None
                ),
                "user_id": str(initiative.user_id),
                "workspace_id": str(initiative.workspace_id),
            }
            for initiative in initiatives
        ]

        logger.info(f"Found {len(initiatives_data)} active initiatives")

        return {
            "status": "success",
            "type": "initiative",
            "message": f"Found {len(initiatives_data)} active initiatives",
            "data": initiatives_data,
        }

    except InitiativeControllerError as e:
        logger.exception(f"Controller error in get_active_initiatives: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except Exception as e:
        logger.exception(f"Error in get_active_initiatives MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def search_initiatives(
    query: str,
) -> Dict[str, Any]:
    """
    Search for initiatives by title. Uses LIKE operator.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - query: The query string to search the titles, descriptions, and identifiers of the user's initiatives

    Returns:
        - a list of initiatives that match the query
    """
    logger.info(f"Searching for initiatives with query {query}")
    session: Session = SessionLocal()
    try:
        from src.mcp_server.auth_utils import (
            extract_user_from_request,
            get_user_workspace,
        )

        user_id, error_message = extract_user_from_request(session)
        if error_message or user_id is None:
            return {
                "status": "error",
                "type": "initiative",
                "error_message": error_message or "Could not extract user ID",
            }

        workspace, workspace_error = get_user_workspace(session, user_id)
        if workspace_error or workspace is None:
            return {
                "status": "error",
                "type": "initiative",
                "error_message": workspace_error or "Workspace not found",
            }

        # Use InitiativeController to search initiatives
        controller = InitiativeController(session)
        initiatives = controller.search_initiatives(user_id, workspace.id, query)

        # Convert to dict format expected by MCP clients
        initiatives_data = [
            {
                "id": str(initiative.id),
                "title": initiative.title,
                "description": initiative.description,
                "identifier": initiative.identifier,
                "status": initiative.status.value,
                "type": initiative.type,
                "created_at": (
                    initiative.created_at.isoformat() if initiative.created_at else None
                ),
                "updated_at": (
                    initiative.updated_at.isoformat() if initiative.updated_at else None
                ),
                "user_id": str(initiative.user_id),
                "workspace_id": str(initiative.workspace_id),
            }
            for initiative in initiatives
        ]

        logger.info(f"Found {len(initiatives_data)} initiatives")

        return {
            "status": "success",
            "type": "initiative",
            "data": initiatives_data,
        }

    except InitiativeControllerError as e:
        logger.exception(f"Controller error in search_initiatives: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except Exception as e:
        logger.exception(f"Error in search_initiatives MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def get_initiative_details(
    initiative_id: str,
) -> Dict[str, Any]:
    """
    Pull complete initiative context including all tasks.

    Used in the workflow after user selects or searches for an initiative to get
    full context needed for planning and operations.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - initiative_id: The UUID of the initiative to get details for

    Returns:
        - Complete initiative details with all associated tasks
    """
    logger.info(f"Fetching details for initiative {initiative_id}")
    session: Session = SessionLocal()
    try:
        from src.mcp_server.auth_utils import extract_user_from_request

        user_id, error_message = extract_user_from_request(session)
        if error_message or user_id is None:
            return {
                "status": "error",
                "type": "initiative_details",
                "error_message": error_message or "Could not extract user ID",
            }

        initiative_uuid = uuid.UUID(initiative_id)

        # Use InitiativeController to get initiative details
        controller = InitiativeController(session)
        initiative = controller.get_initiative_details(user_id, initiative_uuid)

        if not initiative:
            return {
                "status": "error",
                "type": "initiative_details",
                "error_message": f"Initiative {initiative_id} not found",
            }

        # Convert initiative to dict
        initiative_data = {
            "id": str(initiative.id),
            "title": initiative.title,
            "description": initiative.description,
            "identifier": initiative.identifier,
            "status": initiative.status.value,
            "type": initiative.type,
            "created_at": (
                initiative.created_at.isoformat() if initiative.created_at else None
            ),
            "updated_at": (
                initiative.updated_at.isoformat() if initiative.updated_at else None
            ),
            "user_id": str(initiative.user_id),
            "workspace_id": str(initiative.workspace_id),
        }

        # Convert tasks to dict
        tasks_data = [
            {
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "identifier": task.identifier,
                "status": task.status.value,
                "type": task.type,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "user_id": str(task.user_id),
                "workspace_id": str(task.workspace_id),
                "initiative_id": str(task.initiative_id),
            }
            for task in initiative.tasks
        ]

        logger.info(
            f"Found initiative details for {initiative_id} with {len(tasks_data)} tasks"
        )

        return {
            "status": "success",
            "type": "initiative_details",
            "message": f"Retrieved comprehensive initiative context for {initiative.title}",
            "initiative": initiative_data,
            "tasks": tasks_data,
        }

    except InitiativeNotFoundError as e:
        logger.exception(f"Initiative not found: {str(e)}")
        return {
            "status": "error",
            "type": "initiative_details",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except InitiativeControllerError as e:
        logger.exception(f"Controller error in get_initiative_details: {str(e)}")
        return {
            "status": "error",
            "type": "initiative_details",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "initiative_details",
            "error_message": f"Invalid initiative ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in get_initiative_details MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "initiative_details",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()
