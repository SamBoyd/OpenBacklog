import logging
from typing import Optional

from src.mcp_server.main import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp.prompt
def start_work_command() -> str:
    """
    Guided initiative and task selection with validation prompts.

    Fetches active initiatives via MCP, presents structured selection interface,
    validates context before proceeding, and confirms task selection with user.

    This command provides structured workflow guidance for:
    1. Health check and authentication verification
    2. Initiative selection from active (IN_PROGRESS) initiatives
    3. Task selection within chosen initiative
    4. Task prioritization and context retrieval
    5. Implementation planning workflow

    Returns structured guidance for the complete OpenBacklog workflow.
    """
    logger.info("Generating start_work_command prompt")

    return """# OpenBacklog Integration Workflow

Follow these steps to work with OpenBacklog tasks through Claude Code:

## Step 1: Health Check
**Action:** Call `health_check()` tool to verify MCP server connectivity and authentication
**Next:** If successful, proceed to Step 2. If failed, check authentication.

## Step 2: Select Active Initiative
**Action:** Call `get_active_initiatives()` to see all initiatives marked as 'IN_PROGRESS'
**Important:** Claude Code does NOT prioritize initiatives - this is the user's responsibility.
**Next:** If initiatives exist, present the list to the user and ask them to choose one. If no active initiatives, stop here and ask user to prioritize an initiative in OpenBacklog first.

## Step 3: Select Task
**Action:** Call `get_initiative_tasks(initiative_id)` with the chosen initiative ID
**Next:** Present the task list to the user and ask them to choose one task

## Step 4: Prioritize Task
**Action:** Check task status - if not IN_PROGRESS, call `update_task_status_inprogress(task_id)`
**Next:** Confirm task is now actively prioritized, then proceed to get full context

## Step 5: Retrieve Task Context
**Action:** Call `get_task_details(task_id)` to get full context including checklist
**Next:** Review task description, current checklist, and dependencies, then proceed to planning

## Step 6: Enter Plan Mode & Create Implementation Plan
**Action:** Say 'Let me research the codebase and create a plan before implementing' to enter plan mode. Research existing patterns, propose implementation approach, and iterate with user. The first todo item in EVERY plan you create should be "Update the OpenBacklog task with the new implementation plan".
**Next:** Continue refining the plan through back-and-forth discussion until approach is clear

## Step 7: Confirm Implementation Plan
**CRITICAL:** Get explicit user confirmation before proceeding with any updates
**Action:** Present the finalized plan to user and ask for explicit approval. DO NOT proceed without clear confirmation. Suggest that if the user wants to make any changes, they should say 'You should enter plan mode (shift+tab) if you want to make any changes'
**Next:** IMMEDIATELY after receiving user approval, your FIRST action must be to update the OpenBacklog task description and checklist. Do not start any implementation or use any other tools until this is complete.

## Step 8: Update Task Description & Checklist
**STOP:** Before writing any code or creating local todo lists, you must first update the task description and checklist in OpenBacklog. This is mandatory for project tracking. The sequence is: Get user confirmation → Update OpenBacklog → Then implement
**Action:** Use `update_task_description()` and `update_checklist()` tools to save the approved plan. This must be your FIRST action after user approval - no exceptions
**Next:** Verify updates were saved successfully, then begin implementation. TodoWrite is for local session tracking only - OpenBacklog updates are for persistent project management and must happen first

## Step 9: Execute and Track Progress
**Action:** Use `update_checklist_item()` to mark items complete as work progresses
**Next:** Continue until all checklist items are complete

## Step 10: Complete Task
**Action:** Call `update_task_status_done(task_id)` to move task to DONE status
**Next:** Confirm task completion, then proceed to continue working

## Step 11: Continue Working
**Action:** Ask user if they want to work on another task in the same initiative. If yes, return to step 3 to get updated task list and select next task
**Next:** Repeat the workflow cycle or end session based on user preference

## Validation Tips
- Use `validate_context()` before making updates to ensure task state is current
- Always confirm user selections before proceeding to next step
- **CRITICAL:** Enter plan mode by saying 'Let me research the codebase and create a plan before implementing'
- **MANDATORY:** Get explicit user confirmation before updating task description or checklist
- **BLOCKING RULE:** After user approval, OpenBacklog updates must happen BEFORE any implementation
- TodoWrite is for local session tracking - OpenBacklog updates are for persistent project management
- **NEVER** start coding or use other tools until task description and checklist are updated in OpenBacklog
- Use `update_task_status_inprogress()` when starting work on a task if not already in IN_PROGRESS status
- Use `update_task_status_done()` when all checklist items are finished
- Provide clear feedback on what was updated in OpenBacklog including status changes
- Never skip the plan confirmation step - it prevents implementation misalignment
"""


# @mcp.prompt
def create_plan_command(task_id: str) -> str:
    """
    Collaborative implementation planning with explicit confirmation.

    Guides discussion of implementation approach, structures plan creation with
    validation steps, confirms plan with user before updating OpenBacklog, and
    uses MCP tools to update task checklist and description.

    Args:
        task_id: The UUID of the task to create a plan for

    Returns structured guidance for collaborative planning workflow.
    """
    logger.info(f"Generating create_plan_command prompt for task {task_id}")

    return f"""# Implementation Planning Workflow for Task {task_id}

## Step 1: Retrieve Current Task Context
**Action:** Call `get_task_details("{task_id}")` to get complete task information
**Purpose:** Understand current task description, existing checklist, and dependencies
**Next:** Review the task details and current state before planning

## Step 2: Enter Plan Mode
**Action:** Say 'Let me research the codebase and create a plan before implementing'
**Purpose:** Activate Claude Code's plan mode for collaborative design
**Next:** Research existing patterns and propose implementation approach

## Step 3: Research and Design
**Actions:**
- Research existing codebase patterns and architecture
- Identify similar implementations or related functionality
- Consider technical constraints and dependencies
- Design the implementation approach iteratively with user input
**Next:** Draft a comprehensive implementation plan

## Step 4: Create Structured Implementation Plan
**Requirements:**
- The first todo item in EVERY plan must be "Update the OpenBacklog task with the new implementation plan"
- Break down work into specific, actionable checklist items
- Include testing and validation steps
- Consider error handling and edge cases
- Estimate complexity and identify potential blockers

## Step 5: Present Plan for User Confirmation
**CRITICAL STEP:**
- Present the finalized plan to user clearly
- Ask for explicit approval: "Do you approve this implementation plan?"
- **DO NOT proceed without clear confirmation**
- If user wants changes, suggest: "You should enter plan mode (shift+tab) if you want to make any changes"
**Next:** Only proceed after receiving explicit user approval

## Step 6: Update OpenBacklog Task (MANDATORY FIRST ACTION)
**BLOCKING RULE:** After user approval, this must be your FIRST action before any implementation
**Actions:**
1. Call `update_task_description("{task_id}", description)` with enhanced task description including implementation context
2. Call `update_checklist("{task_id}", checklist_items)` with the approved implementation steps
**Validation:** Verify both updates were successful before proceeding
**Next:** Confirm OpenBacklog updates are complete, then begin implementation

## Step 7: Begin Implementation
**Only after OpenBacklog is updated:**
- Use TodoWrite for local session tracking (optional)
- Start implementing the approved plan step by step
- Use `update_checklist_item()` to mark items complete as work progresses

## Important Notes
- **Never skip the confirmation step** - it prevents implementation misalignment
- **OpenBacklog updates are mandatory** before any code implementation
- TodoWrite is for local tracking only - OpenBacklog updates are for persistent project management
- Use `validate_context("{task_id}")` if you need to verify current task state
- Provide clear feedback on what was updated in OpenBacklog
"""


# @mcp.prompt
def mark_complete_command(item_number: int) -> str:
    """
    Validated checklist item completion with user confirmation.

    Shows current checklist state, confirms which item is being marked complete,
    validates item number against current checklist, and uses MCP tools to
    update OpenBacklog after confirmation.

    Args:
        item_number: The 1-based index of the checklist item to mark complete

    Returns structured guidance for checklist item validation and completion.
    """
    logger.info(f"Generating mark_complete_command prompt for item {item_number}")

    return f"""# Mark Checklist Item #{item_number} Complete

## Step 1: Validate Current Context
**Action:** Call `validate_context(task_id)` to get current task and checklist state
**Purpose:** Ensure you have the most up-to-date checklist information
**Next:** Review the current checklist to confirm item #{item_number} exists

## Step 2: Display Current Checklist
**Action:** Show the user the current checklist with item numbers
**Format:**
```
Current Checklist:
1. [✓] Item title (if complete)
2. [ ] Item title (if incomplete)  
3. [ ] Item title (if incomplete)
```
**Next:** Confirm the specific item to be marked complete

## Step 3: Validate Item Selection
**Check:** Verify that item #{item_number} exists in the checklist
**Confirm with user:** "You want to mark item #{item_number}: '[Item Title]' as complete. Is this correct?"
**Next:** Only proceed with explicit user confirmation

## Step 4: Mark Item Complete
**Action:** Call `update_checklist_item(task_id, item_id, true)` where:
- `task_id`: The current task UUID
- `item_id`: The UUID of checklist item #{item_number} from the checklist
- `true`: Mark as complete
**Next:** Verify the update was successful

## Step 5: Show Updated Progress
**Action:** Display updated checklist showing the newly completed item
**Calculate:** Show completion percentage (completed_items / total_items * 100)
**Next:** Ask user if they want to mark additional items complete or continue with implementation

## Validation Requirements
- **Always validate item number** against actual checklist length
- **Always confirm with user** before marking complete
- **Handle errors gracefully** if item doesn't exist or update fails
- **Show clear feedback** about what was updated
- **Calculate progress** to show user how much work remains

## Error Handling
- If item #{item_number} doesn't exist: "Item #{item_number} not found. Current checklist has X items."
- If update fails: "Failed to update item. Please try again or check connectivity."
- If no current task context: "No task context found. Please use /start-work to select a task first."

## Next Steps Guidance
- If all items complete: Suggest using `update_task_status_done(task_id)` to complete the task
- If items remain: Show remaining incomplete items and ask what to work on next
- If user wants to continue: Return to implementation workflow
"""


# @mcp.prompt
def validate_context_command(task_id: Optional[str] = None) -> str:
    """
    Verify current task state matches expectations.

    Checks task details haven't changed, validates checklist state, alerts to
    any discrepancies, and refreshes context if needed.

    Args:
        task_id: Optional UUID of specific task to validate. If not provided,
                validates the current working task context.

    Returns structured guidance for context verification workflow.
    """
    logger.info(
        f"Generating validate_context_command prompt for task {task_id or 'current'}"
    )

    task_context = f'"{task_id}"' if task_id else "current task"

    return f"""# Validate Task Context - {task_context.title()}

## Step 1: Determine Task to Validate
{"**Using provided task:** " + task_id if task_id else "**Action:** Identify the current working task ID from context"}
**Next:** Proceed with validation for the specified task

## Step 2: Fetch Current Task State  
**Action:** Call `validate_context({task_id or "task_id"})` to get comprehensive task information
**Returns:** Current task details, checklist state, and completion statistics
**Next:** Analyze the returned data for any discrepancies

## Step 3: Verify Task Details
**Check these fields:**
- **Task Title:** Confirm it matches your understanding
- **Task Description:** Look for any changes since last interaction  
- **Task Status:** Verify current status (TODO, IN_PROGRESS, DONE)
- **Last Updated:** Check timestamp for recent changes
**Next:** Alert user to any unexpected changes

## Step 4: Validate Checklist State
**Analyze checklist data:**
- **Total Items:** Count of checklist items
- **Completed Items:** Number marked as complete
- **Completion Percentage:** Progress calculation
- **Item Details:** Review individual item titles and completion status
**Next:** Compare against your expected state

## Step 5: Report Validation Results
**If context is valid:**
- "✅ Task context is valid and up-to-date"
- Show current progress summary
- Display any recent changes (if timestamp indicates updates)

**If discrepancies found:**
- "⚠️ Context discrepancies detected:"
- List specific differences found
- Recommend actions to refresh or resynchronize

## Step 6: Handle Discrepancies
**Common issues and solutions:**
- **Task status changed:** Update your workflow accordingly
- **Checklist modified:** Refresh your understanding of remaining work
- **Description updated:** Review new information that may affect implementation
- **Items completed externally:** Acknowledge progress and adjust plan

## Step 7: Refresh Context if Needed
**Action:** If significant changes detected, call `get_task_details({task_id or "task_id"})` for complete refresh
**Purpose:** Ensure you have the most current task information
**Next:** Update your implementation approach based on current state

## Validation Checklist
- [ ] Task details match expectations
- [ ] Checklist state is current
- [ ] No unexpected status changes
- [ ] Implementation plan still valid
- [ ] Dependencies haven't changed

## When to Use This Command
- Before making significant updates to task or checklist
- After periods of inactivity to ensure context is current  
- When you suspect changes may have been made externally
- Before completing a task to verify all work is accounted for
- When encountering unexpected errors during updates

## Next Steps
- **If valid:** Continue with planned workflow
- **If changes detected:** Adjust approach and inform user of changes
- **If errors:** Investigate connectivity or permission issues
"""
