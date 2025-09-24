import logging
import urllib.parse
from re import L
from typing import Any, Dict, List

import requests
import uvicorn
from fastmcp.server import FastMCP
from fastmcp.server.dependencies import get_http_request
from mcp.server.fastmcp import Context
from pydantic import BaseModel
from starlette.requests import Request

from src.config import settings
from src.mcp_server.main import mcp

logger = logging.getLogger(__name__)


class ChecklistItem(BaseModel):
    title: str
    is_complete: bool


@mcp.tool()
async def update_checklist(
    task_id: str,
    checklist_items: List[ChecklistItem],
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Replace the entire checklist for a task with a new implementation plan.

    Used during implementation planning to set the complete checklist of steps
    that need to be completed for the task.

    Args:
        - task_id: The UUID of the task to update checklist for
        - checklist_items: List of checklist item objects with 'title' and optional 'order'

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - Confirmation of the checklist update with the new items
    """
    logger.info(
        f"Updating checklist for task {task_id} with {len(checklist_items)} items"
    )
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            if ctx:
                await ctx.error("No authorization header found")
            return {
                "status": "error",
                "type": "checklist_update",
                "error_message": "No authorization header found",
            }

        # First, delete existing checklist items for this task
        delete_url = f"{settings.postgrest_domain}/checklist?task_id=eq.{task_id}"

        delete_response = requests.delete(
            delete_url,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if delete_response.status_code not in [200, 204]:
            logger.warning(
                f"Could not delete existing checklist items: {delete_response.status_code}"
            )

        # Create new checklist items
        created_items = []
        for index, item in enumerate(checklist_items):
            item_payload = {
                "task_id": task_id,
                "title": item.title,
                "is_complete": False,
            }

            create_url = f"{settings.postgrest_domain}/checklist"

            create_response = requests.post(
                create_url,
                json=item_payload,
                headers={
                    "Authorization": authorization_header,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                timeout=30,
            )

            if create_response.status_code in [200, 201]:
                created_items.extend(create_response.json())
            else:
                logger.warning(
                    f"Could not create checklist item {item.title}: {create_response.status_code}"
                )

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

    except Exception as e:
        logger.exception(f"Error in update_checklist MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }


@mcp.tool()
async def update_checklist_item(
    task_id: str, item_id: str, is_complete: bool, ctx: Context = None
) -> Dict[str, Any]:
    """
    Mark a specific checklist item as complete or incomplete.

    Used during implementation to track progress by updating individual
    checklist items as work is completed.

    Args:
        - task_id: The UUID of the task (for validation)
        - item_id: The UUID of the checklist item to update
        - is_complete: Whether the item should be marked as complete

    REQUIRES: "Authorization: Bearer <token>" header to be set on the MCP request.

    Returns:
        - Confirmation of the item status update
    """
    logger.info(f"Updating checklist item {item_id} to complete={is_complete}")
    try:
        request: Request = get_http_request()

        # Access request data
        authorization_header = request.headers.get("Authorization")
        if not authorization_header:
            if ctx:
                await ctx.error("No authorization header found")
            return {
                "status": "error",
                "type": "checklist_item_update",
                "error_message": "No authorization header found",
            }

        # Update the checklist item
        update_url = f"{settings.postgrest_domain}/checklist?id=eq.{item_id}&task_id=eq.{task_id}"

        payload = {"is_complete": is_complete}

        response = requests.patch(
            update_url,
            json=payload,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            timeout=30,
        )

        if response.status_code not in [200, 204]:
            logger.exception(
                f"Error updating checklist item: {response.status_code} - {response.text}"
            )
            return {
                "status": "error",
                "type": "checklist_item_update",
                "error_message": f"Server error: {response.status_code}",
            }

        updated_items = response.json() if response.content else []

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
            "updated_items": updated_items,
        }

    except Exception as e:
        logger.exception(f"Error in update_checklist_item MCP tool: {str(e)}")
        return {
            "status": "error",
            "type": "checklist_item_update",
            "error_message": f"Server error: {str(e)}",
            "error_type": "server_error",
        }
