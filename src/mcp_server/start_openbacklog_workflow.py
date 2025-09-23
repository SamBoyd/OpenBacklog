# src/ai/mcp_server.py
import logging
from typing import Any, Dict

from mcp.server.fastmcp import Context

from src.mcp_server.main import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp.tool()
async def start_openbacklog_workflow() -> Dict[str, Any]:
    """
    Returns structured workflow guidance to help Claude Code navigate the OpenBacklog integration process.

    This tool provides step-by-step instructions for:
    1. Selecting an active initiative
    2. Choosing a task within that initiative
    3. Prioritizing the task by moving it to IN_PROGRESS status
    4. Retrieving task context
    5. Entering plan mode and creating implementation plan
    6. Confirming plan with user before proceeding
    7. Updating task descriptions and checklists
    8. Tracking progress through checklist completion
    9. Completing the task and moving to next one

    Returns:
        - Structured workflow guidance with clear next steps
    """
    logger.info("Starting OpenBacklog workflow guidance")

    workflow_guidance = {
        "status": "success",
        "type": "workflow_guidance",
        "workflow": {
            "title": "OpenBacklog Integration Workflow",
            "description": "Follow these steps to work with OpenBacklog tasks through Claude Code",
            "steps": [
                {
                    "step": 1,
                    "title": "Health Check",
                    "description": "Verify MCP server connectivity and authentication",
                    "action": "Call health_check() tool to ensure proper connection",
                    "next_step": "If successful, proceed to step 2. If failed, check authentication.",
                },
                {
                    "step": 2,
                    "title": "Select Active Initiative",
                    "description": "Find which initiative the user wants to work on. NOTE: Claude Code does NOT prioritize initiatives - this is the user's responsibility.",
                    "action": "Call get_active_initiatives() to see all initiatives marked as 'IN_PROGRESS'. If no initiatives are returned, inform the user they need to go to OpenBacklog and move an initiative to IN_PROGRESS status before proceeding.",
                    "next_step": "If initiatives exist, present the list to the user and ask them to choose one. If no active initiatives, stop here and ask user to prioritize an initiative in OpenBacklog first.",
                },
                {
                    "step": 3,
                    "title": "Select Task",
                    "description": "Choose which task within the initiative to work on",
                    "action": "Call get_initiative_tasks(initiative_id) with the chosen initiative ID",
                    "next_step": "Present the task list to the user and ask them to choose one task",
                },
                {
                    "step": 4,
                    "title": "Prioritize Task",
                    "description": "Move selected task to IN_PROGRESS status if not already prioritized",
                    "action": "Check task status - if not IN_PROGRESS, call update_task_status_inprogress(task_id)",
                    "next_step": "Confirm task is now actively prioritized, then proceed to get full context",
                },
                {
                    "step": 5,
                    "title": "Retrieve Task Context",
                    "description": "Pull complete task details including current checklist",
                    "action": "Call get_task_details(task_id) to get full context",
                    "next_step": "Review task description, current checklist, and dependencies, then proceed to planning",
                },
                {
                    "step": 6,
                    "title": "Enter Plan Mode & Create Implementation Plan",
                    "description": "Use Claude Code's plan mode to collaboratively design the implementation approach",
                    "action": "Say 'Let me research the codebase and create a plan before implementing' to enter plan mode. Research existing patterns, propose implementation approach, and iterate with user. The first todo item in EVERY plan you create should be \"Update the OpenBacklog task with the new implementation plan\".",
                    "next_step": "Continue refining the plan through back-and-forth discussion until approach is clear",
                },
                {
                    "step": 7,
                    "title": "Confirm Implementation Plan",
                    "description": "CRITICAL: Get explicit user confirmation before proceeding with any updates",
                    "action": "Present the finalized plan to user and ask for explicit approval. DO NOT proceed without clear confirmation. Suggest that if the user wants to make any changes, they should say 'You should enter plan mode (shift+tab) if you want to make any changes'",
                    "next_step": "IMMEDIATELY after receiving user approval, your FIRST action must be to update the OpenBacklog task description and checklist. Do not start any implementation or use any other tools until this is complete.",
                },
                {
                    "step": 8,
                    "title": "Update Task Description & Checklist",
                    "description": "STOP: Before writing any code or creating local todo lists, you must first update the task description and checklist in OpenBacklog. This is mandatory for project tracking. The sequence is: Get user confirmation → Update OpenBacklog → Then implement",
                    "action": "Use update_task_description() and update_checklist() tools to save the approved plan. This must be your FIRST action after user approval - no exceptions",
                    "next_step": "Verify updates were saved successfully, then begin implementation. TodoWrite is for local session tracking only - OpenBacklog updates are for persistent project management and must happen first",
                },
                {
                    "step": 9,
                    "title": "Execute and Track Progress",
                    "description": "Work through implementation while updating checklist items",
                    "action": "Use update_checklist_item() to mark items complete as work progresses",
                    "next_step": "Continue until all checklist items are complete",
                },
                {
                    "step": 10,
                    "title": "Complete Task",
                    "description": "Mark task as done when all work is finished",
                    "action": "Call update_task_status_done(task_id) to move task to DONE status",
                    "next_step": "Confirm task completion, then proceed to continue working",
                },
                {
                    "step": 11,
                    "title": "Continue Working",
                    "description": "Ask user if they want to work on another task in the same initiative",
                    "action": "If yes, return to step 3 to get updated task list and select next task",
                    "next_step": "Repeat the workflow cycle or end session based on user preference",
                },
            ],
            "validation_tips": [
                "Use validate_context() before making updates to ensure task state is current",
                "Always confirm user selections before proceeding to next step",
                "CRITICAL: Enter plan mode by saying 'Let me research the codebase and create a plan before implementing'",
                "MANDATORY: Get explicit user confirmation before updating task description or checklist",
                "BLOCKING RULE: After user approval, OpenBacklog updates must happen BEFORE any implementation",
                "TodoWrite is for local session tracking - OpenBacklog updates are for persistent project management",
                "NEVER start coding or use other tools until task description and checklist are updated in OpenBacklog",
                "Use update_task_status_inprogress() when starting work on a task if not already in IN_PROGRESS status",
                "Use update_task_status_done() when all checklist items are finished",
                "Provide clear feedback on what was updated in OpenBacklog including status changes",
                "Never skip the plan confirmation step - it prevents implementation misalignment",
            ],
        },
    }

    return workflow_guidance
