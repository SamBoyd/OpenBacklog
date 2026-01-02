# src/mcp_server/task_tools.py
import logging
import uuid
from typing import Any, Dict, List, Optional

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
from src.mcp_server.main import mcp  # type: ignore
from src.mcp_server.prompt_driven_tools.utils.identifier_resolvers import (
    resolve_initiative_identifier,
)
from src.models import Initiative, Task, TaskStatus
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskChecklistItem(BaseModel):
    """Pydantic model for checklist items when creating a task."""

    title: str
    is_complete: bool = False


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
        "identifier": task.identifier,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "type": task.type,
        "initiative_identifier": (
            task.initiative.identifier if task.initiative else None
        ),
    }


@mcp.tool()
async def query_tasks(
    identifier: Optional[str] = None,
    initiative_identifier: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Query tasks with flexible filtering and single-entity lookup.


    **Query modes:**
    - identifier: Returns single task with full context (checklist, initiative, related tasks)
    - initiative_identifier: Returns all tasks for that initiative
    - search: Returns tasks matching search term (title/description/identifier)
    - No params: Returns error (must specify at least one filter)

    Args:
        identifier: Task identifier (e.g., "TM-001") for single lookup
        initiative_identifier: Initiative identifier (e.g., "I-1001") to list tasks
        search: Search string for title/description matching

    Returns:
        For single: task details with checklist, initiative context, related tasks
        For list: array of tasks
    """
    logger.info(
        f"Querying tasks: identifier={identifier}, initiative={initiative_identifier}, search={search}"
    )
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

        controller = TaskController(session)

        # SINGLE TASK MODE: identifier provided
        if identifier:
            logger.info(f"Getting task '{identifier}' in workspace {workspace_id}")

            # Look up task by identifier
            task = (
                session.query(Task)
                .filter(
                    Task.identifier == identifier,
                    Task.workspace_id == workspace_id,
                    Task.user_id == user_id,
                )
                .first()
            )

            if not task:
                return {
                    "status": "error",
                    "type": "task",
                    "error_message": f"Task not found: {identifier}",
                    "error_type": "not_found",
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
                    "task_identifier": task.identifier,
                }
                for item in task.checklist
            ]

            # Get initiative details
            initiative_dict = None
            if task.initiative_id:
                initiative = (
                    session.query(Initiative)
                    .filter(
                        Initiative.id == task.initiative_id,
                        Initiative.user_id == user_id,
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
                related_tasks = controller.get_initiative_tasks(
                    user_id, task.initiative_id
                )
                related_tasks_dicts = [
                    {
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
                f"Found task {identifier} with {len(checklist_items)} checklist items"
            )

            return {
                "status": "success",
                "type": "task",
                "message": f"Found task: {task.title}",
                "data": {
                    "task": task_dict,
                    "checklist_items": checklist_items,
                    "task_context": task_context,
                },
            }

        # LIST BY INITIATIVE MODE
        if initiative_identifier:
            logger.info(
                f"Getting tasks for initiative '{initiative_identifier}' in workspace {workspace_id}"
            )

            # Resolve initiative identifier to UUID
            initiative_id = resolve_initiative_identifier(
                initiative_identifier, workspace_id, session
            )

            tasks = controller.get_initiative_tasks(user_id, initiative_id)
            tasks_data = [_task_to_dict(task) for task in tasks]

            logger.info(
                f"Found {len(tasks_data)} tasks for initiative {initiative_identifier}"
            )

            return {
                "status": "success",
                "type": "task",
                "message": f"Found {len(tasks_data)} task(s) for initiative {initiative_identifier}",
                "data": {"tasks": tasks_data},
            }

        # SEARCH MODE
        if search:
            logger.info(f"Searching tasks for '{search}' in workspace {workspace_id}")

            tasks = controller.search_tasks(user_id, workspace_id, search)
            tasks_data = [_task_to_dict(task) for task in tasks]

            logger.info(f"Found {len(tasks_data)} tasks matching '{search}'")

            return {
                "status": "success",
                "type": "task",
                "message": f"Found {len(tasks_data)} task(s) matching '{search}'",
                "data": {"tasks": tasks_data},
            }

        # NO PARAMS - return error
        return {
            "status": "error",
            "type": "task",
            "error_message": "At least one filter required: identifier, initiative_identifier, or search",
            "error_type": "validation_error",
        }

    except MCPContextError as e:
        logger.warning(f"Authorization error in query_tasks: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except DomainException as e:
        logger.warning(f"Domain error in query_tasks: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskNotFoundError as e:
        logger.exception(f"Task not found: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in query_tasks: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except Exception as e:
        logger.exception(f"Error in query_tasks MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task",
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
        checklist_items = task.checklist
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
async def submit_task(
    task_identifier: Optional[str] = None,
    initiative_identifier: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    checklist: Optional[List[TaskChecklistItem]] = None,
) -> Dict[str, Any]:
    """
    Create a new task or update an existing one.

    Uses upsert pattern: creates when task_identifier is omitted, updates when provided.

    Args:
        task_identifier: Task identifier (e.g., "T-001") for updates (optional)
        initiative_identifier: Initiative identifier (required for create)
        title: Task title (required for create, optional for update)
        description: Task description (optional)
        status: Task status (TO_DO, IN_PROGRESS, BLOCKED, DONE, ARCHIVED) (optional)
        task_type: Task type (CODING, TESTING, DOCUMENTATION, DESIGN) (optional)
        checklist: List of checklist items (replaces entire checklist if provided) (optional)

    Returns:
        Success response with created or updated task
    """
    logger.info(
        f"Processing task submission: identifier={task_identifier}, title={title}"
    )
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

        controller = TaskController(session)

        # UPDATE PATH
        if task_identifier:
            logger.info(f"Updating task {task_identifier}")

            # Resolve task identifier to UUID
            task = (
                session.query(Task)
                .filter(
                    Task.identifier == task_identifier,
                    Task.workspace_id == workspace_id,
                    Task.user_id == user_id,
                )
                .first()
            )

            if not task:
                return {
                    "status": "error",
                    "type": "task",
                    "error_message": f"Task {task_identifier} not found",
                    "error_type": "not_found",
                }

            # Update description if provided
            if description is not None:
                controller.update_task_description(user_id, task.id, description)

            # Update status if provided
            if status is not None:
                try:
                    task_status = TaskStatus(status)
                except ValueError:
                    valid_statuses = [s.value for s in TaskStatus]
                    return {
                        "status": "error",
                        "type": "task",
                        "error_message": f"Invalid status '{status}'. Valid: {valid_statuses}",
                        "error_type": "validation_error",
                    }
                controller.move_task_to_status(user_id, task.id, task_status)

            # Update type if provided
            if task_type is not None:
                task.type = task_type
                session.add(task)
                session.commit()

            # Update title if provided
            if title is not None:
                task.title = title
                session.add(task)
                session.commit()

            # Replace checklist if provided
            if checklist is not None:
                items_data = [
                    ChecklistItemData(
                        title=item.title, is_complete=item.is_complete, order=idx
                    )
                    for idx, item in enumerate(checklist)
                ]
                controller.update_checklist(user_id, task.id, items_data)

            session.refresh(task)

            logger.info(f"Successfully updated task {task_identifier}")

            return {
                "status": "success",
                "type": "task",
                "message": f"Updated task {task_identifier}",
                "data": _task_to_dict(task),
            }

        # CREATE PATH
        else:
            logger.info(f"Creating task '{title}'")

            # Validate required fields for creation
            if not initiative_identifier:
                return {
                    "status": "error",
                    "type": "task",
                    "error_message": "initiative_identifier is required for task creation",
                    "error_type": "validation_error",
                }

            if not title:
                return {
                    "status": "error",
                    "type": "task",
                    "error_message": "title is required for task creation",
                    "error_type": "validation_error",
                }

            # Resolve initiative identifier to UUID
            initiative_id = resolve_initiative_identifier(
                initiative_identifier, workspace_id, session
            )

            # Parse status if provided
            task_status = TaskStatus.TO_DO
            if status:
                try:
                    task_status = TaskStatus(status)
                except ValueError:
                    valid_statuses = [s.value for s in TaskStatus]
                    return {
                        "status": "error",
                        "type": "task",
                        "error_message": f"Invalid status '{status}'. Valid: {valid_statuses}",
                        "error_type": "validation_error",
                    }

            # Convert checklist items
            checklist_data = None
            if checklist:
                checklist_data = [
                    ChecklistItemData(
                        title=item.title, is_complete=item.is_complete, order=idx
                    )
                    for idx, item in enumerate(checklist)
                ]

            # Create task
            task: Task = controller.create_task(
                title=title,
                user_id=user_id,
                workspace_id=workspace_id,
                initiative_id=initiative_id,
                status=task_status,
                task_type=task_type,
                description=description,
                checklist=checklist_data,
            )

            logger.info(f"Successfully created task {task.identifier}")

            return {
                "status": "success",
                "type": "task",
                "message": f"Created task {task.identifier}",
                "data": _task_to_dict(task),
            }

    except MCPContextError as e:
        logger.warning(f"Authorization error in submit_task: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": e.error_type,
        }
    except DomainException as e:
        logger.warning(f"Domain error in submit_task: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": "not_found",
        }
    except TaskControllerError as e:
        logger.exception(f"Controller error in submit_task: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": str(e),
            "error_type": "controller_error",
        }
    except ValueError as e:
        logger.exception(f"Invalid value in submit_task: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": f"Invalid value: {str(e)}",
            "error_type": "validation_error",
        }
    except Exception as e:
        logger.exception(f"Error in submit_task MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
    finally:
        session.close()
