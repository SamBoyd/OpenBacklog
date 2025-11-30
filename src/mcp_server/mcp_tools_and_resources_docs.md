# OpenBacklog MCP Server - Tools and Resources Documentation

This document provides a comprehensive overview of all tools and resources available through the OpenBacklog MCP server.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Workflow Tools](#core-workflow-tools)
4. [Workspace Management Tools](#workspace-management-tools)
5. [Initiative Management Tools](#initiative-management-tools)
6. [Task Management Tools](#task-management-tools)
7. [Checklist Management Tools](#checklist-management-tools)
8. [Strategic Planning Tools](#strategic-planning-tools)
9. [Roadmap Management Tools](#roadmap-management-tools)
10. [Utility Tools](#utility-tools)
11. [Prompts](#prompts)

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

All tools require OAuth authentication handled by FastMCP's Auth0Provider.

**Authentication Flow:**
- Users authenticate via OAuth 2.0 / OpenID Connect (Auth0)
- FastMCP middleware automatically extracts and validates access tokens from requests
- The authenticated user's workspace is automatically derived (each user has one workspace)
- No manual header management required in tool implementations

**Client Configuration:**
- MCP clients must send `Authorization: Bearer <token>` header
- The workspace is automatically resolved from the authenticated user
- FastMCP handles token validation and user extraction transparently

---

## Core Workflow Tools

### `health_check()`

Verifies MCP server connectivity and authentication status.

**Returns:**
```json
{
  "status": "success" | "error",
  "type": "health_check",
  "message": "MCP server authentication and database connectivity verified",
  "user_id": "<user_uuid>",
  "workspace_id": "<workspace_uuid>",
  "workspace_name": "..."
}
```

**Use Cases:**
- Initial connection verification
- Debugging authentication issues
- Validating workspace access
- Testing database connectivity

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

## Workspace Management Tools

### `create_workspace(name: str, description: str = "")`

Creates a new workspace for the authenticated user.

A workspace is a container for initiatives, tasks, and strategic planning. Creating a workspace automatically creates required dependencies (ProductVision and PrioritizedRoadmap).

**Parameters:**
- `name` (required): Workspace name (max 255 characters)
- `description` (optional): Workspace description

**Returns:**
```json
{
  "status": "success" | "error",
    "type": "workspace",
    "message": "Created workspace '{name}'",
    "workspace": {
      "id": "<uuid>",
      "name": "...",
      "description": "...",
      "icon": null
    }
  }
  ```

  **Use Cases:**
  - First-time user setup (onboarding)
  - Setting up workspace before creating initiatives

  **Important Notes:**
  - This is typically the first step for new users
  - Each user can only have one workspace
  - The workspace is automatically associated with the authenticated user
  - Creating your first initiative after workspace creation will automatically complete onboarding
  - Workspace ID is automatically resolved from the authenticated user in all subsequent requests

**Example Usage:**
```
User: "Create a workspace called 'My SaaS Product' in OpenBacklog"
Claude Code calls: create_workspace(name="My SaaS Product", description="")
```

---

## Initiative Management Tools

### `create_initiative()`

Create a new initiative for the user.

**Parameters:**
  - title: Title for the initiative
  - description: Description for the initiative
  - status: Optional status string (defaults to BACKLOG) - Options: BACKLOG, TO_DO, IN_PROGRESS

**Returns**
```json
{
  "status": "success",
  "type": "initiative",
  "message": "Created initiative 'Initiative Title'",
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
**Get Framework � Claude + User Collaborate � Submit Result**

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

#### `submit_strategic_pillar(name: str, description: str)`

Submits a refined strategic pillar.

**Parameters:**
- `name`: Pillar name (1-100 characters, unique per workspace)
- `description`: Pillar description including strategy and anti-strategy (required)
  - Should include both what you'll do and what you won't do
  - Example: "Strategy: Provide seamless experience within developer's existing workflow. Anti-Strategy: No web-first experience, no mobile app, no Slack/Teams bots."

**Returns:**
Success response with saved pillar data and next steps.

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

#### `submit_product_outcome(name: str, description: str, pillar_ids: List[str] | None)`

Submits a refined product outcome.

**Parameters:**
- `name`: Outcome name (1-150 characters)
- `description`: Outcome description including goal, baseline, target, and timeline (required)
  - Should include: specific metric, baseline value, target value, and timeline
  - Example: "Goal: Increase daily active IDE plugin users. Baseline: 30% of users daily active. Target: 80% daily active. Timeline: 6 months."
- `pillar_ids`: Optional list of pillar UUIDs to link (recommended for strategic alignment)

**Returns:**
Success response with saved outcome data and next steps.

---

## Roadmap Management Tools

### Theme Exploration

#### `get_theme_exploration_framework(workspace_id: str)`

Returns framework for defining hypothesis-driven roadmap themes.

**Returns:**
Framework with:
- Purpose: Identify strategic bet areas
- Criteria for good themes (problem, hypothesis, metrics, timeline)
- Examples of good themes with structured descriptions
- Guiding questions and anti-patterns
- Current outcomes and themes (prioritized and unprioritized)
- Coaching tips for hypothesis-driven thinking

---

#### `submit_roadmap_theme(name: str, description: str, outcome_ids: List[str] | None, hero_identifier: str | None, primary_villain_identifier: str | None)`

Submits a refined roadmap theme.

**Parameters:**
- `name`: Theme name (1-100 characters, unique per workspace)
- `description`: Theme description including problem statement, hypothesis, metrics, and timeline (required)
  - Should include: specific problem, testable hypothesis, indicative metrics, and timeline
  - Example: "Problem Statement: New users abandon setup (40% drop-off). Hypothesis: Smart defaults will increase completion from 40% to 70%. Indicative Metrics: Setup completion rate. Timeline: 6 months."
- `outcome_ids`: Optional list of outcome UUIDs to link (recommended for strategic alignment)
- `hero_identifier`: Optional human-readable hero identifier (e.g., "H-2003") to link who benefits
- `primary_villain_identifier`: Optional human-readable villain identifier (e.g., "V-2003") to link what problem is solved

**Returns:**
Success response with theme data and next steps.

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
- `auth_error`: Missing or invalid access token, or authentication failure
- `workspace_error`: User has no workspace (create workspace first)
- `validation_error`: Invalid input parameters
- `controller_error`: Business logic errors from controllers
- `server_error`: Backend API or database issues

---

## Best Practices

1. **Always start with health_check** to verify connectivity
2. **Follow the workflow sequence** for best results:
   - Health check � Initiative selection � Task selection � Prioritization � Details � Planning � Updates � Implementation � Completion
3. **Validate context before updates** using `validate_context()`
4. **Get user confirmation** before making changes
5. **Update OpenBacklog first** before local implementation
6. **Use framework tools** for strategic planning (get framework, collaborate, submit)
7. **Link entities** for strategic alignment (outcomes to pillars, themes to outcomes)
8. **Track progress** using checklist item updates

---

## Architecture Notes

- **Transport:** HTTP on port 9000
- **Authentication:** OAuth 2.0 / OpenID Connect via FastMCP's Auth0Provider
- **Token Handling:** FastMCP middleware automatically extracts and validates access tokens
- **Workspace Resolution:** Automatically derived from authenticated user (one workspace per user)
- **Pattern:** Prompt-driven collaboration for strategic planning
- **Framework:** FastMCP for MCP server implementation
- **Database:** PostgreSQL with full-text search support
- **User Extraction:** OAuth account claims (`sub`) mapped to users via `OAuthAccount` table

---

## Narrative Layer Tools

Narrative layer tools follow the **prompt-driven collaboration pattern**:
**Get Framework → Claude + User Collaborate → Submit Result**

### Hero Management

#### `get_hero_definition_framework()`

Returns comprehensive framework for defining a hero (user persona) through collaborative refinement.

**Returns:**
Framework dict with purpose, criteria, examples, questions, anti-patterns, current state (existing heroes), and coaching tips.

**Criteria:**
- Specific person with a name, not a broad segment
- Real motivations that drive behavior
- Observable pains and frustrations
- Clear context where they operate
- Jobs to be done that your product helps with

---

#### `submit_hero(name: str, description: str | None, is_primary: bool)`

Submits refined hero (user persona) to workspace.

**Parameters:**
- `name`: Hero name (e.g., "Sarah, The Solo Builder")
- `description`: Rich description including who they are, motivations, jobs-to-be-done, pains, desired gains, and context
- `is_primary`: Whether this is the primary hero

**Returns:**
Success response with created hero (including identifier like "H-2003") and next steps.

---

#### `get_heroes()`

Retrieves all heroes for a workspace.

**Returns:**
List of heroes with full details including identifier, name, description, is_primary status.

---

#### `get_hero_details(hero_identifier: str)`

Retrieves full hero details including journey summary.

**Parameters:**
- `hero_identifier`: Human-readable identifier (e.g., "H-2003")

**Returns:**
Hero details + journey summary (active arcs, open conflicts).

---

### Villain Management

#### `get_villain_definition_framework()`

Returns comprehensive framework for defining a villain (problem/obstacle).

**Returns:**
Framework dict with purpose, criteria, examples, questions, anti-patterns, current state (existing villains), and coaching tips.

**Villain Types:**
- `EXTERNAL`: Competitor products, market forces
- `INTERNAL`: Cognitive overload, lack of knowledge
- `TECHNICAL`: Bugs, system limitations, tech debt
- `WORKFLOW`: Difficult processes, tool switching
- `OTHER`: Other obstacles

---

#### `submit_villain(name: str, villain_type: str, description: str, severity: int)`

Submits refined villain to workspace.

**Parameters:**
- `name`: Villain name (e.g., "Context Switching")
- `villain_type`: Type (EXTERNAL, INTERNAL, TECHNICAL, WORKFLOW, OTHER)
- `description`: Rich description including how it manifests, impact, and evidence
- `severity`: How big a threat (1-5)

**Returns:**
Success response with created villain (including identifier like "V-2003") and next steps.

---

#### `get_villains()`

Retrieves all villains for a workspace.

**Returns:**
List of villains with full details including identifier, name, villain_type, severity, is_defeated status.

---

#### `mark_villain_defeated(villain_identifier: str)`

Marks a villain as defeated.

**Parameters:**
- `villain_identifier`: Human-readable identifier (e.g., "V-2003")

**Returns:**
Success response with updated villain.

---

### Conflict Management

#### `get_conflict_creation_framework()`

Returns framework for creating conflicts between heroes and villains.

**Returns:**
Framework dict with purpose, criteria, examples, questions, anti-patterns, current state (available heroes/villains), and coaching tips.

---

#### `create_conflict(hero_identifier: str, villain_identifier: str, description: str, story_arc_id: str | None)`

Creates a new conflict between a hero and villain.

**Parameters:**
- `hero_identifier`: Human-readable hero identifier (e.g., "H-2003")
- `villain_identifier`: Human-readable villain identifier (e.g., "V-2003")
- `description`: Rich description including conflict statement, impact, and stakes
- `story_arc_id`: Optional UUID of story arc addressing this conflict

**Returns:**
Success response with created conflict (including identifier like "C-2003").

---

#### `get_conflicts(status: str | None, hero_identifier: str | None, villain_identifier: str | None)`

Retrieves conflicts with optional filtering.

**Parameters:**
- `status`: Optional filter by status (OPEN, ESCALATING, RESOLVING, RESOLVED)
- `hero_identifier`: Optional filter by hero identifier (e.g., "H-2003")
- `villain_identifier`: Optional filter by villain identifier (e.g., "V-2003")

**Returns:**
List of conflicts matching filters.

---

#### `mark_conflict_resolved(conflict_identifier: str, resolved_by_initiative_id: str)`

Marks a conflict as resolved by an initiative.

**Parameters:**
- `conflict_identifier`: Human-readable conflict identifier (e.g., "C-2003")
- `resolved_by_initiative_id`: UUID of initiative that resolved it

**Returns:**
Success response with updated conflict.

---

### Narrative Recap Tools

#### `get_recent_turning_points(limit: int = 10)`

Retrieves recent turning points for narrative recap.

**Parameters:**
- `limit`: Maximum number of turning points to return (default 10)

**Returns:**
List of recent turning points ordered by created_at DESC.

---

#### `generate_previously_on()`

Generates 'Previously on...' narrative recap.

This is the key MCP tool that enables narrative-aware development. It generates a story-style summary of recent progress.

**Returns:**
Narrative recap including:
- `recap_text`: Story-style summary
- `primary_hero`: Primary hero details
- `active_arcs`: Active story arcs with narrative context
- `recent_turning_points`: Recent turning points
- `open_conflicts`: Open conflicts
- `suggested_next_tasks`: Suggested next tasks (placeholder)

---

#### `get_story_bible()`

Retrieves complete story bible for workspace.

**Returns:**
Complete story bible including:
- `heroes`: All heroes
- `villains`: All villains
- `story_arcs`: All roadmap themes with narrative context
- `conflicts`: All conflicts
- `turning_points`: Recent turning points

---

### Enhanced Roadmap Theme Tools

#### `submit_roadmap_theme(..., hero_identifier: str | None, primary_villain_identifier: str | None)`

Updated to accept optional hero and villain identifiers for narrative linking.

**New Parameters:**
- `hero_identifier`: Optional human-readable hero identifier (e.g., "H-2003")
- `primary_villain_identifier`: Optional human-readable villain identifier (e.g., "V-2003")

---

#### `link_theme_to_hero(theme_id: str, hero_identifier: str)`

Links a roadmap theme to a hero.

**Parameters:**
- `theme_id`: UUID of roadmap theme
- `hero_identifier`: Human-readable hero identifier (e.g., "H-2003")

**Returns:**
Success response with updated theme.

---

#### `link_theme_to_villain(theme_id: str, villain_identifier: str)`

Links a roadmap theme to a villain.

**Parameters:**
- `theme_id`: UUID of roadmap theme
- `villain_identifier`: Human-readable villain identifier (e.g., "V-2003")

**Returns:**
Success response with updated theme.

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
- Narrative heroes: `src/mcp_server/prompt_driven_tools/narrative_heroes.py`
- Narrative villains: `src/mcp_server/prompt_driven_tools/narrative_villains.py`
- Narrative conflicts: `src/mcp_server/prompt_driven_tools/narrative_conflicts.py`
- Narrative recap: `src/mcp_server/prompt_driven_tools/narrative_recap.py`
- Utilities: `src/mcp_server/prompt_driven_tools/utilities.py`
- Prompts: `src/mcp_server/slash_commands.py`
