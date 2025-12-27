# src/mcp_server/task_tools.py
import logging
import uuid
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.initiative_management.task_controller import (
    TaskController,
    TaskControllerError,
    TaskNotFoundError,
)
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp  # type: ignore
from src.models import Initiative, Task, TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _generate_task_context(
    task_dict, initiative_dict, related_tasks_dicts, checklist_items_dicts
):
    """
    Generate a natural language summary of task context including initiative
    and related tasks information for better LLM understanding.
    """
    context_parts = []

    # Initiative context section
    if initiative_dict:
        context_parts.append(
            f"""INITIATIVE CONTEXT:
This task belongs to Initiative {initiative_dict.get('identifier', 'Unknown')}: "{initiative_dict.get('title', 'Unknown')}" (Status: {initiative_dict.get('status', 'Unknown')})
Initiative Description: {initiative_dict.get('description', 'No description available')}"""
        )
    else:
        context_parts.append(
            """INITIATIVE CONTEXT:
Unable to load initiative details for this task."""
        )

    # Task scope definition section
    if initiative_dict and related_tasks_dicts:
        context_parts.append(
            f"""
TASK SCOPE:
Current task {task_dict.get('identifier', 'Unknown')} focuses on "{task_dict.get('title', 'Unknown')}". This is part of the broader "{initiative_dict.get('title', 'initiative')}" but should NOT include work that belongs to other tasks:"""
        )

        # Add related tasks as scope boundaries
        incomplete_tasks = [
            rt
            for rt in related_tasks_dicts
            if rt.get("status") not in ["DONE", "ARCHIVED"]
        ]
        if incomplete_tasks:
            for related_task in incomplete_tasks[
                :5
            ]:  # Limit to first 5 to avoid overwhelming
                context_parts.append(
                    f"- {related_task.get('title', 'Unknown')} (handled by {related_task.get('identifier', 'Unknown')} - {related_task.get('status', 'Unknown')})"
                )

            if len(incomplete_tasks) > 5:
                context_parts.append(
                    f"- ... and {len(incomplete_tasks) - 5} other incomplete tasks in this initiative"
                )

    # Related work section
    if related_tasks_dicts:
        context_parts.append(
            f"""
RELATED WORK IN THIS INITIATIVE:"""
        )

        # Group tasks by status for better organization
        status_groups = {}
        for rt in related_tasks_dicts:
            status = rt.get("status", "Unknown")
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(rt)

        # Show in priority order: IN_PROGRESS, TO_DO, BLOCKED, DONE, ARCHIVED
        status_order = ["IN_PROGRESS", "TO_DO", "BLOCKED", "DONE", "ARCHIVED"]

        for status in status_order:
            if status in status_groups:
                for rt in status_groups[status][:3]:  # Limit to 3 per status
                    context_parts.append(
                        f"- {rt.get('identifier', 'Unknown')}: {rt.get('title', 'Unknown')} ({rt.get('status', 'Unknown')})"
                    )

                if len(status_groups[status]) > 3:
                    context_parts.append(
                        f"  ... and {len(status_groups[status]) - 3} more {status} tasks"
                    )

        # Show any remaining statuses not in our predefined order
        for status, tasks in status_groups.items():
            if status not in status_order:
                for rt in tasks[:2]:
                    context_parts.append(
                        f"- {rt.get('identifier', 'Unknown')}: {rt.get('title', 'Unknown')} ({rt.get('status', 'Unknown')})"
                    )
    else:
        context_parts.append(
            """
RELATED WORK:
Unable to load related tasks for this initiative."""
        )

    # Implementation notes
    if initiative_dict and task_dict:
        context_parts.append(
            f"""
IMPLEMENTATION NOTES:
Focus on the specific scope of task {task_dict.get('identifier', 'Unknown')}. Coordinate with related tasks as needed, especially those marked as IN_PROGRESS or TO_DO."""
        )

    return "\n".join(context_parts)


def _task_to_dict(task: Task) -> Dict[str, Any]:
    """Convert Task model to dictionary."""
    return {
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
        "initiative_id": str(task.initiative_id) if task.initiative_id else None,
    }


@mcp.tool()
async def get_initiative_tasks(
    initiative_id: str,
) -> Dict[str, Any]:
    """
    Retrieve all tasks for a specific initiative.

    Used in the workflow after user selects an initiative to show available tasks
    for that initiative that they can work on.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - initiative_id: The UUID of the initiative to get tasks for

    Returns:
        - List of tasks belonging to the initiative with full context
    """
    logger.info(f"Fetching tasks for initiative {initiative_id}")
    session: Session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        initiative_uuid = uuid.UUID(initiative_id)

        # Use TaskController to get initiative tasks
        controller = TaskController(session)
        tasks = controller.get_initiative_tasks(user_id, initiative_uuid)

        # Convert to dict format
        tasks_data = [_task_to_dict(task) for task in tasks]

        logger.info(f"Found {len(tasks_data)} tasks for initiative {initiative_id}")

        return {
            "status": "success",
            "type": "task",
            "message": f"Found {len(tasks_data)} tasks for initiative {initiative_id}",
            "initiative_id": initiative_id,
            "data": tasks_data,
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in get_initiative_tasks: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in get_initiative_tasks: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": f"Invalid initiative ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in get_initiative_tasks MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def get_task_details(
    task_id: str,
) -> Dict[str, Any]:
    """
    Pull complete task context including description, checklist items, and dependencies.

    Used in the workflow after user selects a task to get full context needed
    for implementation planning.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - task_id: The UUID of the task to get details for

    Returns:
        - Complete task details with checklist items and relationships
    """
    logger.info(f"Fetching details for task {task_id}")
    session: Session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        task_uuid = uuid.UUID(task_id)

        # Use TaskController to get task details
        controller = TaskController(session)
        task = controller.get_task_details(user_id, task_uuid)

        if not task:
            return {
                "status": "error",
                "type": "task_details",
                "error_message": f"Task {task_id} not found",
            }

        # Convert task to dict
        task_dict = _task_to_dict(task)

        # Convert checklist items to dict
        checklist_items = [
            {
                "id": str(item.id),
                "title": item.title,
                "is_complete": item.is_complete,
                "order": item.order,
                "task_id": str(item.task_id),
            }
            for item in task.checklist_items
        ]

        # Get initiative details
        initiative_dict = None
        if task.initiative_id:
            initiative = (
                session.query(Initiative)
                .filter(
                    Initiative.id == task.initiative_id, Initiative.user_id == user_id
                )
                .first()
            )
            if initiative:
                initiative_dict = {
                    "id": str(initiative.id),
                    "title": initiative.title,
                    "description": initiative.description,
                    "identifier": initiative.identifier,
                    "status": initiative.status.value,
                }

        # Get related tasks in the same initiative
        related_tasks_dicts = []
        if task.initiative_id:
            related_tasks = controller.get_initiative_tasks(user_id, task.initiative_id)
            related_tasks_dicts = [
                {
                    "id": str(rt.id),
                    "identifier": rt.identifier,
                    "title": rt.title,
                    "status": rt.status.value,
                    "type": rt.type,
                }
                for rt in related_tasks
                if rt.id != task.id
            ]

        # Generate task context summary
        task_context = _generate_task_context(
            task_dict, initiative_dict, related_tasks_dicts, checklist_items
        )

        logger.info(
            f"Found task details for {task_id} with {len(checklist_items)} checklist items, initiative context, and {len(related_tasks_dicts)} related tasks"
        )

        return {
            "status": "success",
            "type": "task_details",
            "message": f"Retrieved comprehensive task context for {task.title}",
            "task": task_dict,
            "checklist_items": checklist_items,
            "task_context": task_context,
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in get_task_details: {str(e)}")
        return {
            "status": "error",
            "type": "task_details",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskNotFoundError as e:
        logger.exception(f"Task not found: {str(e)}")
        return {
            "status": "error",
            "type": "task_details",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in get_task_details: {str(e)}")
        return {
            "status": "error",
            "type": "task_details",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "task_details",
            "error_message": f"Invalid task ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in get_task_details MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task_details",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def search_tasks(
    query: str,
) -> Dict[str, Any]:
    """
    Search for tasks by title, description, and identifier. Uses LIKE operator.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - query: The query string to search the titles, descriptions, and identifiers of the user's tasks

    Returns:
        - a list of tasks that match the query
    """
    logger.info(f"Searching for tasks with query {query}")
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

        # Use TaskController to search tasks
        controller = TaskController(session)
        tasks = controller.search_tasks(user_id, workspace_id, query)

        # Convert to dict format
        tasks_data = [_task_to_dict(task) for task in tasks]

        logger.info(f"Found {len(tasks_data)} tasks")

        return {
            "status": "success",
            "type": "task",
            "data": tasks_data,
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in search_tasks: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in search_tasks: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except Exception as e:
        logger.exception(f"Error in search_tasks MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def update_task_description(
    task_id: str,
    description: str,
) -> Dict[str, Any]:
    """
    Update a task's description with additional implementation context.

    Used during implementation planning to add context, notes, and implementation
    details to the task description.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - task_id: The UUID of the task to update
        - description: The new description content. Supports full markdown formatting
          including headings, bold, italic, code blocks, lists, links, and blockquotes.
          The UI renders this as rich text.

    Returns:
        - Confirmation of the update with the new description
    """
    logger.info(f"Updating description for task {task_id}")
    session: Session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        task_uuid = uuid.UUID(task_id)

        # Use TaskController to update task description
        controller = TaskController(session)
        task = controller.update_task_description(user_id, task_uuid, description)

        logger.info(f"Successfully updated description for task {task_id}")

        return {
            "status": "success",
            "type": "task_update",
            "message": f"Successfully updated task description",
            "task_id": task_id,
            "updated_description": description,
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in update_task_description: {str(e)}")
        return {
            "status": "error",
            "type": "task_update",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskNotFoundError as e:
        logger.exception(f"Task not found: {str(e)}")
        return {
            "status": "error",
            "type": "task_update",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in update_task_description: {str(e)}")
        return {
            "status": "error",
            "type": "task_update",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "task_update",
            "error_message": f"Invalid task ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in update_task_description MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def validate_context(
    task_id: str,
) -> Dict[str, Any]:
    """
    Verify that the current task context matches expected state.

    Used to prevent agent reliability issues by confirming that the task
    details haven't changed and that the context is still valid before
    making updates.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - task_id: The UUID of the task to validate

    Returns:
        - Validation status and current task state
    """
    logger.info(f"Validating context for task {task_id}")
    session: Session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        task_uuid = uuid.UUID(task_id)

        # Use TaskController to get task details
        controller = TaskController(session)
        task = controller.get_task_details(user_id, task_uuid)

        if not task:
            return {
                "status": "error",
                "type": "context_validation",
                "error_message": f"Task {task_id} not found or access denied",
            }

        # Calculate checklist progress
        checklist_items = task.checklist_items
        completed_items = [item for item in checklist_items if item.is_complete]
        total_items = len(checklist_items)
        completion_percentage = (
            (len(completed_items) / total_items * 100) if total_items > 0 else 0
        )

        logger.info(f"Context validation successful for task {task_id}")

        return {
            "status": "success",
            "type": "context_validation",
            "message": f"Task context is valid and up-to-date",
            "task_id": task_id,
            "task": {
                "id": str(task.id),
                "title": task.title,
                "description": task.description or "",
                "status": task.status.value,
                "updated_at": task.updated_at.isoformat() if task.updated_at else "",
            },
            "checklist_summary": {
                "total_items": total_items,
                "completed_items": len(completed_items),
                "completion_percentage": completion_percentage,
            },
            "validation_timestamp": "current",
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in validate_context: {str(e)}")
        return {
            "status": "error",
            "type": "context_validation",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskNotFoundError as e:
        logger.exception(f"Task not found: {str(e)}")
        return {
            "status": "error",
            "type": "context_validation",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in validate_context: {str(e)}")
        return {
            "status": "error",
            "type": "context_validation",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "context_validation",
            "error_message": f"Invalid task ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in validate_context MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "context_validation",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def update_task_status_inprogress(
    task_id: str,
) -> Dict[str, Any]:
    """
    Update a task's status to 'IN_PROGRESS'.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - task_id: The UUID of the task to update

    Returns:
        - Confirmation of the status update
    """
    logger.info(f"Updating task {task_id} status to IN_PROGRESS")
    session: Session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        task_uuid = uuid.UUID(task_id)

        # Use TaskController to update task status
        controller = TaskController(session)
        task = controller.move_task_to_status(
            user_id, task_uuid, TaskStatus.IN_PROGRESS
        )

        logger.info(f"Successfully updated task {task_id} status to IN_PROGRESS")

        return {
            "status": "success",
            "type": "task_status_update",
            "message": f"Successfully updated task status to IN_PROGRESS",
            "task_id": task_id,
            "new_status": "IN_PROGRESS",
        }

    except MCPContextError as e:
        logger.warning(
            f"Authorization error in update_task_status_inprogress: {str(e)}"
        )
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskNotFoundError as e:
        logger.exception(f"Task not found: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in update_task_status_inprogress: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": f"Invalid task ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in update_task_status_inprogress MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()


@mcp.tool()
async def update_task_status_done(
    task_id: str,
) -> Dict[str, Any]:
    """
    Update a task's status to 'DONE'.

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Args:
        - task_id: The UUID of the task to update

    Returns:
        - Confirmation of the status update
    """
    logger.info(f"Updating task {task_id} status to DONE")
    session: Session = SessionLocal()
    try:
        user_id_str, _ = get_auth_context(session, requires_workspace=True)
        user_id = uuid.UUID(user_id_str)

        task_uuid = uuid.UUID(task_id)

        # Use TaskController to update task status
        controller = TaskController(session)
        task = controller.move_task_to_status(user_id, task_uuid, TaskStatus.DONE)

        logger.info(f"Successfully updated task {task_id} status to DONE")

        return {
            "status": "success",
            "type": "task_status_update",
            "message": f"Successfully updated task status to DONE",
            "task_id": task_id,
            "new_status": "DONE",
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in update_task_status_done: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except TaskNotFoundError as e:
        logger.exception(f"Task not found: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in update_task_status_done: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid UUID format: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": f"Invalid task ID format: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in update_task_status_done MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()
