# OpenBacklog MCP Server - Tools and Resources Documentation

This document provides a comprehensive overview of all tools and resources available through the OpenBacklog MCP server.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Workflow Tools](#core-workflow-tools)
4. [Initiative Management Tools](#initiative-management-tools)
5. [Task Management Tools](#task-management-tools)
6. [Checklist Management Tools](#checklist-management-tools)
7. [Strategic Planning Tools](#strategic-planning-tools)
8. [Roadmap Management Tools](#roadmap-management-tools)
9. [Utility Tools](#utility-tools)
10. [Prompts](#prompts)

---

## Overview

The OpenBacklog MCP server provides a comprehensive set of tools for managing initiatives, tasks, checklists, and strategic planning through Claude Code. All tools follow a consistent pattern of returning structured JSON responses with status indicators.

**Server Configuration:**
- Name: OpenBacklog MCP server
- Transport: HTTP
- Host: 0.0.0.0
- Port: 9000

---

## Authentication

All tools (except `health_check`) require authentication headers:

**Required Headers:**
- `Authorization: Bearer <token>` - User authentication token
- `X-Workspace-Id: <workspace_uuid>` - Target workspace identifier

---

## Core Workflow Tools

### `health_check()`

Verifies MCP server connectivity and authentication status.

**Returns:**
```json
{
  "status": "success" | "error",
  "type": "health_check",
  "message": "MCP server connectivity and authentication verified",
  "workspace_id": "<workspace_uuid>",
  "api_endpoint": "<postgrest_domain>"
}
```

**Use Cases:**
- Initial connection verification
- Debugging authentication issues
- Validating workspace access

---

### `start_openbacklog_workflow()`

Returns structured workflow guidance for the complete OpenBacklog integration process.

**Returns:**
Comprehensive workflow object with 11 steps covering:
1. Health check
2. Initiative selection
3. Task selection
4. Task prioritization
5. Context retrieval
6. Plan mode entry
7. Plan confirmation
8. Task updates
9. Implementation tracking
10. Task completion
11. Continuation workflow

**Key Workflow Rules:**
- Enter plan mode before implementation
- Get explicit user confirmation before updates
- Update OpenBacklog task BEFORE any coding
- TodoWrite is for local tracking only

---

## Initiative Management Tools

### `get_active_initiatives()`

Fetches all initiatives with 'IN_PROGRESS' status.

**Returns:**
```json
{
  "status": "success",
  "type": "initiative",
  "message": "Found N active initiatives",
  "data": [
    {
      "id": "<uuid>",
      "title": "Initiative Title",
      "description": "Initiative description",
      "identifier": "INIT-001",
      "status": "IN_PROGRESS",
      "workspace_id": "<workspace_uuid>",
      ...
    }
  ]
}
```

**Use Cases:**
- Starting workflow to select initiative to work on
- Listing current active work
- Initiative selection prompts

---

### `search_initiatives(query: str)`

Searches initiatives by title, description, and identifier using PostgreSQL full-text search.

**Parameters:**
- `query`: Search string (will be URL-encoded)

**Returns:**
```json
{
  "status": "success",
  "type": "initiative",
  "data": [/* matching initiatives */]
}
```

**Use Cases:**
- Finding specific initiatives
- Fuzzy search by keywords
- Locating initiatives by identifier

---

### `get_initiative_details(initiative_id: str)`

Retrieves complete initiative context including all associated tasks.

**Parameters:**
- `initiative_id`: UUID of the initiative

**Returns:**
```json
{
  "status": "success",
  "type": "initiative_details",
  "message": "Retrieved comprehensive initiative context...",
  "initiative": {/* initiative object */},
  "tasks": [/* array of task objects */]
}
```

**Use Cases:**
- Getting full initiative context
- Planning work across multiple tasks
- Understanding task dependencies

---

## Task Management Tools

### `get_initiative_tasks(initiative_id: str)`

Retrieves all tasks for a specific initiative.

**Parameters:**
- `initiative_id`: UUID of the initiative

**Returns:**
```json
{
  "status": "success",
  "type": "task",
  "message": "Found N tasks for initiative...",
  "initiative_id": "<initiative_uuid>",
  "data": [/* array of tasks */]
}
```

**Use Cases:**
- Task selection after choosing initiative
- Reviewing initiative scope
- Task prioritization decisions

---

### `get_task_details(task_id: str)`

Pulls complete task context including description, checklist items, initiative context, and related tasks.

**Parameters:**
- `task_id`: UUID of the task

**Returns:**
```json
{
  "status": "success",
  "type": "task_details",
  "message": "Retrieved comprehensive task context...",
  "task": {/* task object */},
  "checklist_items": [/* checklist array */],
  "task_context": "/* Natural language context summary */"
}
```

**Special Features:**
- Generates natural language context summary
- Includes initiative context
- Lists related tasks for scope clarity
- Shows task dependencies

**Use Cases:**
- Starting work on a task
- Understanding task scope
- Implementation planning

---

### `search_tasks(query: str)`

Searches tasks by title, description, and identifier using PostgreSQL full-text search.

**Parameters:**
- `query`: Search string (will be URL-encoded)

**Returns:**
```json
{
  "status": "success",
  "type": "task",
  "data": [/* matching tasks */]
}
```

**Use Cases:**
- Finding specific tasks
- Searching by keywords
- Locating tasks by identifier

---

### `update_task_description(task_id: str, description: str)`

Updates a task's description with additional implementation context.

**Parameters:**
- `task_id`: UUID of the task
- `description`: New description content

**Returns:**
```json
{
  "status": "success",
  "type": "task_update",
  "message": "Successfully updated task description",
  "task_id": "<task_uuid>",
  "updated_description": "..."
}
```

**Use Cases:**
- Adding implementation notes
- Documenting decisions
- Recording plan details

---

### `validate_context(task_id: str)`

Verifies current task state matches expected state.

**Parameters:**
- `task_id`: UUID of the task

**Returns:**
```json
{
  "status": "success",
  "type": "context_validation",
  "message": "Task context is valid and up-to-date",
  "task_id": "<task_uuid>",
  "task": {/* core task fields */},
  "checklist_summary": {
    "total_items": 5,
    "completed_items": 2,
    "completion_percentage": 40
  },
  "validation_timestamp": "current"
}
```

**Use Cases:**
- Pre-update validation
- Ensuring no external changes
- Progress tracking
- Debugging context issues

---

### `update_task_status_inprogress(task_id: str)`

Updates a task's status to 'IN_PROGRESS'.

**Parameters:**
- `task_id`: UUID of the task

**Returns:**
```json
{
  "status": "success",
  "type": "task_status_update",
  "message": "Successfully updated task status to IN_PROGRESS",
  "task_id": "<task_uuid>",
  "new_status": "IN_PROGRESS"
}
```

**Use Cases:**
- Prioritizing selected task
- Starting work on a task
- Status tracking

---

### `update_task_status_done(task_id: str)`

Updates a task's status to 'DONE'.

**Parameters:**
- `task_id`: UUID of the task

**Returns:**
```json
{
  "status": "success",
  "type": "task_status_update",
  "message": "Successfully updated task status to DONE",
  "task_id": "<task_uuid>",
  "new_status": "DONE"
}
```

**Use Cases:**
- Completing a task
- Marking work finished
- Workflow progression

---

## Checklist Management Tools

### `update_checklist(task_id: str, checklist_items: List[ChecklistItem])`

Replaces the entire checklist for a task with a new implementation plan.

**Parameters:**
- `task_id`: UUID of the task
- `checklist_items`: Array of checklist items
  ```json
  [
    {"title": "Step description", "is_complete": false},
    {"title": "Another step", "is_complete": false}
  ]
  ```

**Returns:**
```json
{
  "status": "success",
  "type": "checklist_update",
  "message": "Successfully updated checklist with N items",
  "task_id": "<task_uuid>",
  "created_items": [/* array of created items */]
}
```

**Behavior:**
- Deletes all existing checklist items for the task
- Creates new items in order
- Sets all items to incomplete by default

**Use Cases:**
- Storing implementation plan
- Breaking down task into steps
- Creating actionable checklist

---

### `update_checklist_item(task_id: str, item_id: str, is_complete: bool)`

Marks a specific checklist item as complete or incomplete.

**Parameters:**
- `task_id`: UUID of the task (for validation)
- `item_id`: UUID of the checklist item
- `is_complete`: true to mark complete, false for incomplete

**Returns:**
```json
{
  "status": "success",
  "type": "checklist_item_update",
  "message": "Successfully marked checklist item as complete/incomplete",
  "task_id": "<task_uuid>",
  "item_id": "<item_uuid>",
  "is_complete": true,
  "updated_items": [/* updated items */]
}
```

**Use Cases:**
- Tracking implementation progress
- Marking steps complete
- Progress reporting

---

## Strategic Planning Tools

Strategic planning tools follow a **prompt-driven collaboration pattern**:
**Get Framework ’ Claude + User Collaborate ’ Submit Result**

### Vision Management

#### `get_vision_definition_framework(workspace_id: str)`

Returns comprehensive framework for defining a product vision through collaborative refinement.

**Returns:**
```json
{
  "type": "vision",
  "purpose": "Define the change you want to make in the world",
  "criteria": [/* quality criteria */],
  "examples": [/* good examples with explanations */],
  "questions": [/* guiding questions */],
  "anti_patterns": [/* what to avoid */],
  "current_state": {/* existing vision if any */},
  "coaching_tips": [/* refinement guidance */]
}
```

**Criteria:**
- Outcome-focused, not solution-focused
- Describes change in user's world
- Clear and inspiring
- 1-2 sentences (max 1000 characters)

---

#### `submit_product_vision(workspace_id: str, vision_text: str)`

Submits refined product vision to workspace.

**Parameters:**
- `workspace_id`: UUID of workspace
- `vision_text`: Refined vision statement

**Returns:**
Success response with saved vision data and next steps.

---

### Strategic Pillars

#### `get_pillar_definition_framework(workspace_id: str)`

Returns framework for defining strategic pillars (differentiators).

**Returns:**
Framework similar to vision with pillar-specific criteria:
- Defensible differentiator
- Enables product outcomes
- 3-5 pillars recommended
- Each has name and description

---

#### `submit_strategic_pillar(workspace_id: str, name: str, description: str)`

Submits a refined strategic pillar.

**Parameters:**
- `workspace_id`: UUID of workspace
- `name`: Pillar name
- `description`: Pillar description

**Returns:**
Success response with saved pillar data.

---

### Product Outcomes

#### `get_outcome_definition_framework(workspace_id: str)`

Returns framework for defining measurable product outcomes.

**Returns:**
Framework with outcome-specific guidance:
- Measurable impact on users
- Links to strategic pillars
- Has baseline and target
- Time-bound (usually 12 months)

---

#### `submit_product_outcome(workspace_id: str, name: str, description: str, baseline_value: float, target_value: float, unit: str, target_date: str)`

Submits a refined product outcome.

**Parameters:**
- `workspace_id`: UUID of workspace
- `name`: Outcome name
- `description`: Outcome description
- `baseline_value`: Starting metric value
- `target_value`: Target metric value
- `unit`: Metric unit (e.g., "%", "users", "minutes")
- `target_date`: ISO date string

**Returns:**
Success response with saved outcome data.

---

## Roadmap Management Tools

### Theme Exploration

#### `get_theme_exploration_framework(workspace_id: str)`

Returns framework for defining hypothesis-driven roadmap themes.

**Returns:**
Framework with:
- Purpose: Identify strategic bet areas
- Theme pattern template (problem/hypothesis/metrics/horizon)
- Examples of good themes
- Current outcomes and themes
- Alignment scoring guidance

---

#### `submit_roadmap_theme(workspace_id: str, name: str, problem_statement: str, hypothesis: str, success_metrics: str, time_horizon_months: int)`

Submits a refined roadmap theme.

**Parameters:**
- `workspace_id`: UUID of workspace
- `name`: Theme name
- `problem_statement`: What's broken?
- `hypothesis`: What do you believe will work?
- `success_metrics`: How will you measure success?
- `time_horizon_months`: 0-12 months

**Returns:**
Success response with theme data and alignment score.

---

### Prioritization

#### `get_prioritization_context(workspace_id: str)`

Returns context for prioritizing roadmap themes.

**Returns:**
```json
{
  "prioritized_themes": [/* currently prioritized */],
  "unprioritized_themes": [/* backlog */],
  "outcomes": [/* product outcomes for alignment */],
  "guidance": {/* prioritization tips */}
}
```

---

#### `prioritize_workstream(workspace_id: str, theme_id: str)`

Moves a theme to prioritized (active) status.

**Parameters:**
- `workspace_id`: UUID of workspace
- `theme_id`: UUID of theme to prioritize

**Returns:**
Success response confirming prioritization.

---

#### `deprioritize_workstream(workspace_id: str, theme_id: str)`

Moves a theme back to backlog (unprioritized).

**Parameters:**
- `workspace_id`: UUID of workspace
- `theme_id`: UUID of theme to deprioritize

**Returns:**
Success response confirming deprioritization.

---

#### `organize_roadmap(workspace_id: str, prioritized_theme_ids: List[str])`

Reorders prioritized themes in the roadmap.

**Parameters:**
- `workspace_id`: UUID of workspace
- `prioritized_theme_ids`: Ordered list of theme UUIDs

**Returns:**
Success response with new ordering.

---

#### `connect_theme_to_outcomes(workspace_id: str, theme_id: str, outcome_ids: List[str])`

Links a roadmap theme to product outcomes for alignment tracking.

**Parameters:**
- `workspace_id`: UUID of workspace
- `theme_id`: UUID of theme
- `outcome_ids`: List of outcome UUIDs to link

**Returns:**
Success response with alignment score.

---

## Utility Tools

### `review_strategic_foundation(workspace_id: str)`

Analyzes completeness and quality of workspace strategic foundation.

**Returns:**
```json
{
  "type": "strategic_foundation_review",
  "status": "healthy" | "partial" | "missing",
  "vision": {/* vision status and data */},
  "pillars": {/* pillar count and details */},
  "outcomes": {/* outcome count and linkage */},
  "gaps": [/* identified issues */],
  "next_steps": [/* recommended actions */],
  "summary": "Human-readable health summary"
}
```

**Use Cases:**
- Strategic planning health check
- Identifying gaps
- Getting recommendations

---

### `connect_outcome_to_pillars(workspace_id: str, outcome_id: str, pillar_ids: List[str])`

Links a product outcome to strategic pillars for validation.

**Parameters:**
- `workspace_id`: UUID of workspace
- `outcome_id`: UUID of outcome
- `pillar_ids`: List of pillar UUIDs

**Returns:**
Success response with updated outcome data.

**Use Cases:**
- Validating outcome supports strategic differentiation
- Creating outcome-pillar linkages
- Strategic alignment

---

## Prompts

### `start_work_command`

Provides structured markdown workflow guidance for the complete OpenBacklog integration process.

**Returns:** Markdown-formatted workflow with 11 steps, validation tips, and clear instructions.

**Use Cases:**
- Getting started with OpenBacklog
- Workflow reference
- Training/onboarding

---

## Error Handling

All tools return consistent error responses:

```json
{
  "status": "error",
  "type": "<tool_type>",
  "error_message": "Description of what went wrong",
  "error_type": "authentication_error" | "server_error" | "validation_error"
}
```

**Common Error Types:**
- `authentication_error`: Missing or invalid auth headers
- `workspace_error`: Missing workspace ID
- `validation_error`: Invalid input parameters
- `server_error`: Backend API issues

---

## Best Practices

1. **Always start with health_check** to verify connectivity
2. **Follow the workflow sequence** for best results:
   - Health check ’ Initiative selection ’ Task selection ’ Prioritization ’ Details ’ Planning ’ Updates ’ Implementation ’ Completion
3. **Validate context before updates** using `validate_context()`
4. **Get user confirmation** before making changes
5. **Update OpenBacklog first** before local implementation
6. **Use framework tools** for strategic planning (get framework, collaborate, submit)
7. **Link entities** for strategic alignment (outcomes to pillars, themes to outcomes)
8. **Track progress** using checklist item updates

---

## Architecture Notes

- **Transport:** HTTP on port 9000
- **API Backend:** PostgREST for database access
- **Authentication:** Bearer token + workspace ID headers
- **Pattern:** Prompt-driven collaboration for strategic planning
- **Framework:** FastMCP for MCP server implementation
- **Database:** PostgreSQL with full-text search support

---

## Related Documentation

- Main server: `src/mcp_server/main.py`
- Checklist tools: `src/mcp_server/checklist_tools.py`
- Health check: `src/mcp_server/healthcheck_tool.py`
- Initiative tools: `src/mcp_server/initiative_tools.py`
- Task tools: `src/mcp_server/task_tools.py`
- Workflow: `src/mcp_server/start_openbacklog_workflow.py`
- Strategic foundation: `src/mcp_server/prompt_driven_tools/strategic_foundation.py`
- Roadmap themes: `src/mcp_server/prompt_driven_tools/roadmap_themes.py`
- Utilities: `src/mcp_server/prompt_driven_tools/utilities.py`
- Prompts: `src/mcp_server/slash_commands.py`
