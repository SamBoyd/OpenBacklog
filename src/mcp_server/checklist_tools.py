import logging
import uuid
from typing import Any, Dict, List

from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.initiative_management.task_controller import (
    ChecklistItemData,
    TaskController,
    TaskControllerError,
    TaskNotFoundError,
)
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp

logger = logging.getLogger(__name__)


class ChecklistItem(BaseModel):
    title: str
    is_complete: bool


@mcp.tool()
async def update_checklist(
    task_id: str,
    checklist_items: List[ChecklistItem],
) -> Dict[str, Any]:
    """
    Replace the entire checklist for a task with a new implementation plan.

    Used during implementation planning to set the complete checklist of steps
    that need to be completed for the task.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - task_id: The UUID of the task to update checklist for
        - checklist_items: List of checklist item objects with 'title' and 'is_complete'

    Returns:
        - Confirmation of the checklist update with the new items
    """
    logger.info(
        f"Updating checklist for task {task_id} with {len(checklist_items)} items"
    )
    session: Session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        task_uuid = uuid.UUID(task_id)

        # Convert ChecklistItem pydantic models to ChecklistItemData
        items_data = [
            ChecklistItemData(
                title=item.title, is_complete=item.is_complete, order=index
            )
            for index, item in enumerate(checklist_items)
        ]

        # Use TaskController to update checklist
        controller = TaskController(session)
        task = controller.update_checklist(user_id, task_uuid, items_data)

        # Get the updated checklist items from the task
        created_items = [
            {
                "id": str(item.id),
                "title": item.title,
                "is_complete": item.is_complete,
                "order": item.order,
                "task_id": str(item.task_id),
            }
            for item in task.checklist
        ]

        logger.info(
            f"Successfully updated checklist for task {task_id} with {len(created_items)} items"
        )

        return {
            "status": "success",
            "type": "checklist_update",
            "message": f"Successfully updated checklist with {len(created_items)} items",
            "task_id": task_id,
            "created_items": created_items,
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in update_checklist: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_update",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskNotFoundError as e:
        logger.exception(f"Task not found: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_update",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in update_checklist: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_update",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_update",
            "error_message": f"Invalid task ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in update_checklist MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def update_checklist_item(
    task_id: str, item_id: str, is_complete: bool
) -> Dict[str, Any]:
    """
    Mark a specific checklist item as complete or incomplete.

    Used during implementation to track progress by updating individual
    checklist items as work is completed.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - task_id: The UUID of the task (for validation)
        - item_id: The UUID of the checklist item to update
        - is_complete: Whether the item should be marked as complete

    Returns:
        - Confirmation of the item status update
    """
    logger.info(f"Updating checklist item {item_id} to complete={is_complete}")
    session: Session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        task_uuid = uuid.UUID(task_id)
        item_uuid = uuid.UUID(item_id)

        # Use TaskController to update checklist item
        controller = TaskController(session)
        checklist_item = controller.update_checklist_item(
            user_id, task_uuid, item_uuid, is_complete
        )

        updated_item = {
            "id": str(checklist_item.id),
            "title": checklist_item.title,
            "is_complete": checklist_item.is_complete,
            "order": checklist_item.order,
            "task_id": str(checklist_item.task_id),
        }

        logger.info(
            f"Successfully updated checklist item {item_id} to complete={is_complete}"
        )

        return {
            "status": "success",
            "type": "checklist_item_update",
            "message": f"Successfully marked checklist item as {'complete' if is_complete else 'incomplete'}",
            "task_id": task_id,
            "item_id": item_id,
            "is_complete": is_complete,
            "updated_items": [updated_item],
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in update_checklist_item: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_item_update",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskNotFoundError as e:
        logger.exception(f"Task not found: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_item_update",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in update_checklist_item: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_item_update",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_item_update",
            "error_message": f"Invalid ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in update_checklist_item MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_item_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()
