# src/ai/mcp_server.py
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


def _generate_task_context(task, initiative, related_tasks, checklist_items):
    """
    Generate a natural language summary of task context including initiative
    and related tasks information for better LLM understanding.
    """
    context_parts = []

    # Initiative context section
    if initiative:
        context_parts.append(
            f"""INITIATIVE CONTEXT:
This task belongs to Initiative {initiative.get('identifier', 'Unknown')}: "{initiative.get('title', 'Unknown')}" (Status: {initiative.get('status', 'Unknown')})
Initiative Description: {initiative.get('description', 'No description available')}"""
        )
    else:
        context_parts.append(
            """INITIATIVE CONTEXT:
Unable to load initiative details for this task."""
        )

    # Task scope definition section
    if initiative and related_tasks:
        context_parts.append(
            f"""
TASK SCOPE:
Current task {task.get('identifier', 'Unknown')} focuses on "{task.get('title', 'Unknown')}". This is part of the broader "{initiative.get('title', 'initiative')}" but should NOT include work that belongs to other tasks:"""
        )

        # Add related tasks as scope boundaries
        incomplete_tasks = [
            rt for rt in related_tasks if rt.get("status") not in ["DONE", "ARCHIVED"]
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
    if related_tasks:
        context_parts.append(
            f"""
RELATED WORK IN THIS INITIATIVE:"""
        )

        # Group tasks by status for better organization
        status_groups = {}
        for rt in related_tasks:
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
    if initiative and task:
        context_parts.append(
            f"""
IMPLEMENTATION NOTES:
Focus on the specific scope of task {task.get('identifier', 'Unknown')}. Coordinate with related tasks as needed, especially those marked as IN_PROGRESS or TO_DO."""
        )

    return "\n".join(context_parts)


@mcp.tool()
async def get_initiative_tasks(
    initiative_id: str,
) -> Dict[str, Any]:
    """
    Retrieve all tasks for a specific initiative.

    Used in the workflow after user selects an initiative to show available tasks
    for that initiative that they can work on.

    Args:
        - initiative_id: The UUID of the initiative to get tasks for

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - List of tasks belonging to the initiative with full context
    """
    logger.info(f"Fetching tasks for initiative {initiative_id}")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        logger.info(f"Authorization header: {authorization_header}")
        if not authorization_header:
            return {
                "status": "error",
                "type": "task",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")
        logger.info(f"Workspace ID: {workspace_id}")

        # Query for tasks belonging to the specific initiative
        url = f"{settings.postgrest_domain}/task?initiative_id=eq.{initiative_id}&workspace_id=eq.{workspace_id}&select=*"

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
                f"Error in get_initiative_tasks MCP tool: {response.status_code} - {response.json()}"
            )
            return {
                "status": "error",
                "type": "task",
                "error_message": f"Server error: {response.status_code}",
            }

        tasks_data = response.json()

        logger.info(f"Found {len(tasks_data)} tasks for initiative {initiative_id}")

        return {
            "status": "success",
            "type": "task",
            "message": f"Found {len(tasks_data)} tasks for initiative {initiative_id}",
            "initiative_id": initiative_id,
            "data": tasks_data,
        }

    except Exception as e:
        logger.exception(f"Error in get_initiative_tasks MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }


@mcp.tool()
async def get_task_details(
    task_id: str,
) -> Dict[str, Any]:
    """
    Pull complete task context including description, checklist items, and dependencies.

    Used in the workflow after user selects a task to get full context needed
    for implementation planning.

    Args:
        - task_id: The UUID of the task to get details for

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - Complete task details with checklist items and relationships
    """
    logger.info(f"Fetching details for task {task_id}")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        logger.info(f"Authorization header: {authorization_header}")
        if not authorization_header:
            return {
                "status": "error",
                "type": "task_details",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")
        logger.info(f"Workspace ID: {workspace_id}")

        # Query for task details
        task_url = f"{settings.postgrest_domain}/task?id=eq.{task_id}&workspace_id=eq.{workspace_id}&select=*"

        task_response = requests.get(
            task_url,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if task_response.status_code != 200:
            logger.exception(
                f"Error fetching task details: {task_response.status_code} - {task_response.json()}"
            )
            return {
                "status": "error",
                "type": "task_details",
                "error_message": f"Server error fetching task: {task_response.status_code}",
            }

        task_data = task_response.json()
        if not task_data or len(task_data) == 0:
            return {
                "status": "error",
                "type": "task_details",
                "error_message": f"Task {task_id} not found",
            }

        task = task_data[0]

        # Query for checklist items
        checklist_url = f"{settings.postgrest_domain}/checklist?task_id=eq.{task_id}&select=*&order=order"

        checklist_response = requests.get(
            checklist_url,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        checklist_items = []
        if checklist_response.status_code == 200:
            checklist_items = checklist_response.json()
        else:
            logger.warning(
                f"Could not fetch checklist items: {checklist_response.status_code}"
            )

        # Query for initiative details
        initiative = None
        if task.get("initiative_id"):
            initiative_url = f"{settings.postgrest_domain}/initiative?id=eq.{task['initiative_id']}&workspace_id=eq.{workspace_id}&select=*"

            try:
                initiative_response = requests.get(
                    initiative_url,
                    headers={
                        "Authorization": authorization_header,
                        "Content-Type": "application/json",
                    },
                    timeout=30,
                )

                if initiative_response.status_code == 200:
                    initiative_data = initiative_response.json()
                    if initiative_data and len(initiative_data) > 0:
                        initiative = initiative_data[0]
                        logger.info(
                            f"Found initiative {initiative['identifier']} for task {task_id}"
                        )
                    else:
                        logger.warning(f"No initiative found for task {task_id}")
                else:
                    logger.warning(
                        f"Could not fetch initiative: {initiative_response.status_code}"
                    )
            except Exception as e:
                logger.warning(
                    f"Error fetching initiative for task {task_id}: {str(e)}"
                )

        # Query for related tasks in the same initiative
        related_tasks = []
        if task.get("initiative_id"):
            related_tasks_url = f"{settings.postgrest_domain}/task?initiative_id=eq.{task['initiative_id']}&workspace_id=eq.{workspace_id}&id=neq.{task_id}&select=id,identifier,title,status,type&order=status,identifier"

            try:
                related_tasks_response = requests.get(
                    related_tasks_url,
                    headers={
                        "Authorization": authorization_header,
                        "Content-Type": "application/json",
                    },
                    timeout=30,
                )

                if related_tasks_response.status_code == 200:
                    related_tasks = related_tasks_response.json()
                    logger.info(
                        f"Found {len(related_tasks)} related tasks for initiative"
                    )
                else:
                    logger.warning(
                        f"Could not fetch related tasks: {related_tasks_response.status_code}"
                    )
            except Exception as e:
                logger.warning(
                    f"Error fetching related tasks for task {task_id}: {str(e)}"
                )

        # Generate task context summary
        task_context = _generate_task_context(
            task, initiative, related_tasks, checklist_items
        )

        logger.info(
            f"Found task details for {task_id} with {len(checklist_items)} checklist items, initiative context, and {len(related_tasks)} related tasks"
        )

        return {
            "status": "success",
            "type": "task_details",
            "message": f"Retrieved comprehensive task context for {task['title']}",
            "task": task,
            "checklist_items": checklist_items,
            "task_context": task_context,
        }

    except Exception as e:
        logger.exception(f"Error in get_task_details MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task_details",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }


@mcp.tool()
async def search_tasks(
    query: str,
) -> Dict[str, Any]:
    """
    Search for tasks by title, description, and identifier. Uses Postgrest LIKE operator.

    Args:
        - query: The query string to search the titles, descriptions, and identifiers of the user's tasks

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - a list of tasks that match the query
    """
    logger.info(f"Searching for tasks with query {query}")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        logger.info(f"Authorization header: {authorization_header}")
        if not authorization_header:
            return {
                "status": "error",
                "type": "task",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")
        logger.info(f"Workspace ID: {workspace_id}")

        # postgrest query url
        url_encoded_query = urllib.parse.quote(query)
        url = f"{settings.postgrest_domain}/task?or(title.fts({url_encoded_query}),description.fts({url_encoded_query}),identifier.fts({url_encoded_query}))&workspace_id=eq.{workspace_id}"

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
                f"Error in search_tasks MCP tool: {response.status_code} - {response.json()}"
            )
            return {
                "status": "error",
                "type": "task",
                "error_message": f"Server error: {response.status_code}",
            }

        tasks_data = response.json()

        logger.info(f"Found {len(tasks_data)} tasks")

        return {
            "status": "success",
            "type": "task",
            "data": tasks_data,
        }

    except Exception as e:
        logger.exception(f"Error in search_tasks MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }


@mcp.tool()
async def update_task_description(
    task_id: str,
    description: str,
) -> Dict[str, Any]:
    """
    Update a task's description with additional implementation context.

    Used during implementation planning to add context, notes, and implementation
    details to the task description.

    Args:
        - task_id: The UUID of the task to update
        - description: The new description content

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - Confirmation of the update with the new description
    """
    logger.info(f"Updating description for task {task_id}")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            return {
                "status": "error",
                "type": "task_update",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")

        # Update the task description
        update_url = f"{settings.postgrest_domain}/task?id=eq.{task_id}&workspace_id=eq.{workspace_id}"

        payload = {"description": description}

        response = requests.patch(
            update_url,
            json=payload,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if response.status_code not in [200, 204]:
            logger.exception(
                f"Error updating task description: {response.status_code} - {response.text}"
            )
            return {
                "status": "error",
                "type": "task_update",
                "error_message": f"Server error: {response.status_code}",
            }

        logger.info(f"Successfully updated description for task {task_id}")

        return {
            "status": "success",
            "type": "task_update",
            "message": f"Successfully updated task description",
            "task_id": task_id,
            "updated_description": description,
        }

    except Exception as e:
        logger.exception(f"Error in update_task_description MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }


@mcp.tool()
async def validate_context(
    task_id: str,
) -> Dict[str, Any]:
    """
    Verify that the current task context matches expected state.

    Used to prevent agent reliability issues by confirming that the task
    details haven't changed and that the context is still valid before
    making updates.

    Args:
        - task_id: The UUID of the task to validate

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - Validation status and current task state
    """
    logger.info(f"Validating context for task {task_id}")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            return {
                "status": "error",
                "type": "context_validation",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")

        # Fetch current task state
        task_url = f"{settings.postgrest_domain}/task?id=eq.{task_id}&workspace_id=eq.{workspace_id}&select=*"

        task_response = requests.get(
            task_url,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if task_response.status_code != 200:
            logger.exception(
                f"Error validating task context: {task_response.status_code} - {task_response.json()}"
            )
            return {
                "status": "error",
                "type": "context_validation",
                "error_message": f"Could not fetch task: {task_response.status_code}",
            }

        task_data = task_response.json()
        if not task_data or len(task_data) == 0:
            return {
                "status": "error",
                "type": "context_validation",
                "error_message": f"Task {task_id} not found or access denied",
            }

        task = task_data[0]

        # Fetch current checklist state
        checklist_url = f"{settings.postgrest_domain}/checklist?task_id=eq.{task_id}&select=*&order=order"

        checklist_response = requests.get(
            checklist_url,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        checklist_items = []
        if checklist_response.status_code == 200:
            checklist_items = checklist_response.json()

        # Calculate checklist progress
        completed_items = [
            item for item in checklist_items if item.get("is_complete", False)
        ]
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
                "id": task["id"],
                "title": task["title"],
                "description": task.get("description", ""),
                "status": task.get("status", ""),
                "updated_at": task.get("updated_at", ""),
            },
            "checklist_summary": {
                "total_items": total_items,
                "completed_items": len(completed_items),
                "completion_percentage": completion_percentage,
            },
            "validation_timestamp": "current",
        }

    except Exception as e:
        logger.exception(f"Error in validate_context MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "context_validation",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }


@mcp.tool()
async def update_task_status_inprogress(
    task_id: str,
) -> Dict[str, Any]:
    """
    Update a task's status to 'IN_PROGRESS'.

    Args:
        - task_id: The UUID of the task to update

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - Confirmation of the status update
    """
    logger.info(f"Updating task {task_id} status to IN_PROGRESS")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            return {
                "status": "error",
                "type": "task_status_update",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")

        # Update the task status
        update_url = f"{settings.postgrest_domain}/task?id=eq.{task_id}&workspace_id=eq.{workspace_id}"

        payload = {"status": "IN_PROGRESS"}

        response = requests.patch(
            update_url,
            json=payload,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if response.status_code not in [200, 204]:
            logger.exception(
                f"Error updating task status: {response.status_code} - {response.text}"
            )
            return {
                "status": "error",
                "type": "task_status_update",
                "error_message": f"Server error: {response.status_code}",
            }

        logger.info(f"Successfully updated task {task_id} status to IN_PROGRESS")

        return {
            "status": "success",
            "type": "task_status_update",
            "message": f"Successfully updated task status to IN_PROGRESS",
            "task_id": task_id,
            "new_status": "IN_PROGRESS",
        }

    except Exception as e:
        logger.exception(f"Error in update_task_status_inprogress MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }


@mcp.tool()
async def update_task_status_done(
    task_id: str,
) -> Dict[str, Any]:
    """
    Update a task's status to 'DONE'.

    Args:
        - task_id: The UUID of the task to update

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - Confirmation of the status update
    """
    logger.info(f"Updating task {task_id} status to DONE")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            return {
                "status": "error",
                "type": "task_status_update",
                "error_message": "No authorization header found",
            }

        workspace_id = request.headers.get("X-Workspace-Id")

        # Update the task status
        update_url = f"{settings.postgrest_domain}/task?id=eq.{task_id}&workspace_id=eq.{workspace_id}"

        payload = {"status": "DONE"}

        response = requests.patch(
            update_url,
            json=payload,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if response.status_code not in [200, 204]:
            logger.exception(
                f"Error updating task status: {response.status_code} - {response.text}"
            )
            return {
                "status": "error",
                "type": "task_status_update",
                "error_message": f"Server error: {response.status_code}",
            }

        logger.info(f"Successfully updated task {task_id} status to DONE")

        return {
            "status": "success",
            "type": "task_status_update",
            "message": f"Successfully updated task status to DONE",
            "task_id": task_id,
            "new_status": "DONE",
        }

    except Exception as e:
        logger.exception(f"Error in update_task_status_done MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "task_status_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
