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
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp  # type: ignore
from src.models import Initiative, InitiativeStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _initiative_to_dict(initiative: Initiative) -> Dict[str, Any]:
    return {
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


@mcp.tool()
async def create_initiative(
    title: str,
    description: str,
    status: str | None = None,
) -> Dict[str, Any]:
    """
    Create a new initiative for the user.

    Args:
        - title: Title for the initiative
        - description: Description for the initiative
        - status: Optional status string (defaults to BACKLOG) - Options: BACKLOG, TO_DO, IN_PROGRESS
    """
    logger.info("Creating a new initiative via MCP tool")
    session: Session = SessionLocal()
    try:
        user_id_str, workspace_id_str = get_auth_context(
            session, requires_workspace=True
        )
        if workspace_id_str is None:
            raise MCPContextError(
                "Workspace not found.",
                error_type="workspace_error",
            )

        user_id = uuid.UUID(user_id_str)
        workspace_id = uuid.UUID(workspace_id_str)

        initiative_status = InitiativeStatus.BACKLOG
        if status:
            try:
                initiative_status = InitiativeStatus(status.upper())
            except ValueError:
                valid_statuses = ", ".join(s.value for s in InitiativeStatus)
                logger.warning(f"Invalid initiative status provided: {status}")
                return {
                    "status": "error",
                    "type": "initiative",
                    "error_message": (
                        f"Invalid status '{status}'. Valid statuses are: {valid_statuses}"
                    ),
                    "error_type": "validation_error",
                }

        controller = InitiativeController(session)
        initiative = controller.create_initiative(
            title=title,
            description=description,
            user_id=user_id,
            workspace_id=workspace_id,
            status=initiative_status,
        )

        controller.complete_onboarding_if_first_initiative(user_id)

        initiative_data = _initiative_to_dict(initiative)

        logger.info(f"Created initiative {initiative.id} for user {user_id}")
        return {
            "status": "success",
            "type": "initiative",
            "message": f"Created initiative '{initiative.title}'",
            "initiative": initiative_data,
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in create_initiative: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except InitiativeControllerError as e:
        logger.exception(f"Controller error in create_initiative: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except Exception as e:
        logger.exception(f"Error in create_initiative MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


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
        user_id_str, workspace_id_str = get_auth_context(
            session, requires_workspace=True
        )
        if workspace_id_str is None:
            raise MCPContextError(
                "Workspace not found.",
                error_type="workspace_error",
            )
        user_id = uuid.UUID(user_id_str)
        workspace_id = uuid.UUID(workspace_id_str)

        controller = InitiativeController(session)
        initiatives = controller.get_active_initiatives(user_id, workspace_id)

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

    except MCPContextError as e:
        logger.warning(f"Authorization error in get_active_initiatives: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": str(e),
            "error_type": e.error_type,
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
        user_id_str, workspace_id_str = get_auth_context(
            session, requires_workspace=True
        )
        if workspace_id_str is None:
            raise MCPContextError(
                "Workspace not found.",
                error_type="workspace_error",
            )
        user_id = uuid.UUID(user_id_str)
        workspace_id = uuid.UUID(workspace_id_str)

        controller = InitiativeController(session)
        initiatives = controller.search_initiatives(user_id, workspace_id, query)

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

    except MCPContextError as e:
        logger.warning(f"Authorization error in search_initiatives: {str(e)}")
        return {
            "status": "error",
            "type": "initiative",
            "error_message": str(e),
            "error_type": e.error_type,
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
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        initiative_uuid = uuid.UUID(initiative_id)

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

    except MCPContextError as e:
        logger.warning(f"Authorization error in get_initiative_details: {str(e)}")
        return {
            "status": "error",
            "type": "initiative_details",
            "error_message": str(e),
            "error_type": e.error_type,
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
