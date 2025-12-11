# OpenBacklog MCP Server - Tools and Resources Documentation

This document provides a comprehensive overview of all tools and resources available through the OpenBacklog MCP server.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Workflow Tools](#core-workflow-tools)
4. [Workspace Management Tools](#workspace-management-tools)
5. [Initiative Management Tools](#initiative-management-tools)
6. [Strategic Initiative Tools](#strategic-initiative-tools)
7. [Task Management Tools](#task-management-tools)
8. [Checklist Management Tools](#checklist-management-tools)
9. [Strategic Planning Tools](#strategic-planning-tools)
10. [Roadmap Management Tools](#roadmap-management-tools)
11. [Utility Tools](#utility-tools)
12. [Prompts](#prompts)
13. [Narrative Layer Tools](#narrative-layer-tools)
14. [Error Handling](#error-handling)
15. [Best Practices](#best-practices)
16. [Architecture Notes](#architecture-notes)

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
  },
  "first_session_guidance": {
    "instruction": "This is a NEW USER. Begin their first strategic planning session NOW. Do NOT offer choices. Follow the guidance below precisely.",
    "full_guide": "# First Session Onboarding Guide\n\n[~350 lines of comprehensive guidance including:\n- Strategic framework overview\n- Framework-invisible conversation philosophy\n- Validation workflow (reflect before submit pattern)\n- Entity sequence (Vision → Hero → Villain → ... → Strategic Initiative)\n- Natural questions quick reference\n- Session completion checklist]"
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
- **The response includes embedded `first_session_guidance`** with conversation philosophy, validation workflow, and entity sequence - MCP clients should follow this guidance immediately
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

## Strategic Initiative Tools

Strategic initiative tools follow the **prompt-driven collaboration pattern**:
**Get Framework → Claude + User Collaborate → Submit Result**

These tools create initiatives with full narrative connections (heroes, villains, conflicts, pillars, themes), bridging strategic planning with the narrative layer.

### `get_strategic_initiative_definition_framework()`

Returns comprehensive framework for defining a strategic initiative with narrative connections.

**Returns:**
```json
{
  "type": "strategic_initiative",
  "purpose": "Define an initiative with strategic context - who it helps, what it defeats, and why it matters",
  "criteria": [/* quality criteria */],
  "examples": [/* good examples with explanations */],
  "questions": [/* guiding questions */],
  "anti_patterns": [/* what to avoid */],
  "current_state": {
    "available_heroes": [/* heroes to link */],
    "available_villains": [/* villains to confront */],
    "available_pillars": [/* pillars for alignment */],
    "available_themes": [/* themes for placement */],
    "active_conflicts": [/* conflicts to address */]
  },
  "coaching_tips": [/* refinement guidance */]
}
```

**Use Cases:**
- Starting initiative creation with full context
- Understanding available narrative connections
- Guiding user through strategic initiative refinement

---

### `submit_strategic_initiative(title, implementation_description, hero_ids, villain_ids, conflict_ids, pillar_id, theme_id, narrative_intent, status, strategic_description)`

Submits a strategic initiative with optional narrative connections.

Creates both an Initiative and its StrategicInitiative context in one operation. Uses graceful degradation: invalid narrative IDs are skipped with warnings rather than failing.

**Important:** Reflect the initiative back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `title` (required): Initiative title (e.g., "Smart Context Switching")
- `implementation_description` (required): What this initiative delivers and how it will be built. This is the practical description of the work involved - the "what".
- `hero_ids` (optional): List of hero UUIDs this initiative helps
- `villain_ids` (optional): List of villain UUIDs this initiative confronts
- `conflict_ids` (optional): List of conflict UUIDs this initiative addresses
- `pillar_id` (optional): Strategic pillar UUID for alignment
- `theme_id` (optional): Roadmap theme UUID for placement
- `narrative_intent` (optional): Why this initiative matters narratively
- `status` (optional): Initiative status (BACKLOG, TO_DO, IN_PROGRESS) - defaults to BACKLOG
- `strategic_description` (optional): How this initiative connects to the larger product strategy. Explains the "why" - user needs addressed, strategic alignment, and how it fits into the bigger picture. Defaults to `implementation_description` if not provided.

**Returns:**
```json
{
  "status": "success",
  "type": "strategic_initiative",
  "message": "Strategic initiative created with narrative connections",
  "data": {
    "initiative": {
      "id": "<uuid>",
      "title": "...",
      "identifier": "I-1001",
      "status": "BACKLOG"
    },
    "strategic_context": {/* full strategic initiative details */}
  },
  "next_steps": [/* what to do next */]
}
```

**Use Cases:**
- Creating initiatives with full strategic context
- Linking initiatives to heroes, villains, and conflicts

---

### `get_strategic_initiatives()`

Retrieves all strategic initiatives with their narrative connections.

**Returns:**
```json
{
  "status": "success",
  "type": "strategic_initiative",
  "message": "Found N strategic initiative(s)",
  "data": {
    "strategic_initiatives": [
      {
        "id": "<uuid>",
        "initiative": {
          "id": "<uuid>",
          "title": "...",
          "description": "...",
          "identifier": "I-1001",
          "status": "IN_PROGRESS"
        },
        "strategic_context": {
          "heroes": [/* linked heroes */],
          "villains": [/* linked villains */],
          "conflicts": [/* linked conflicts */],
          "pillar": {/* linked pillar */},
          "theme": {/* linked theme */},
          "narrative_intent": "..."
        },
        "narrative_summary": "Helps: Sarah | Defeats: Context Switching | Pillar: Deep IDE Integration"
      }
    ]
  }
}
```

**Use Cases:**
- Viewing all initiatives with strategic context
- Understanding the full narrative landscape
- Planning based on hero/villain connections

---

### `get_strategic_initiative(query: str)`

Retrieves a single strategic initiative by ID or identifier.

Accepts a flexible query that tries multiple lookup strategies:
1. First tries as StrategicInitiative UUID
2. Then tries as Initiative UUID
3. Finally tries as Initiative identifier (e.g., "I-1001")

**Parameters:**
- `query`: Strategic initiative ID, initiative ID, or initiative identifier

**Returns:**
```json
{
  "status": "success",
  "type": "strategic_initiative",
  "message": "Found strategic initiative: Title",
  "data": {
    "id": "<uuid>",
    "initiative": {
      "id": "<uuid>",
      "title": "...",
      "description": "...",
      "identifier": "I-1001",
      "status": "IN_PROGRESS"
    },
    "strategic_context": {/* full strategic initiative details */},
    "narrative_summary": "Helps: Sarah | Defeats: Context Switching | Why: ..."
  }
}
```

**Use Cases:**
- Getting full context for a specific initiative
- Looking up initiative by human-readable identifier
- Understanding narrative connections before work

---

### `update_strategic_initiative(query, title, implementation_description, status, hero_ids, villain_ids, conflict_ids, pillar_id, theme_id, narrative_intent, strategic_description)`

Updates an existing strategic initiative's fields.

**Important:** Reflect the changes back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

Accepts a flexible query that tries multiple lookup strategies:
1. First tries as StrategicInitiative UUID
2. Then tries as Initiative UUID
3. Finally tries as Initiative identifier (e.g., "I-1001")

**Parameters:**
- `query` (required): Strategic initiative ID, initiative ID, or initiative identifier
- `title` (optional): New initiative title
- `implementation_description` (optional): New description of what this initiative delivers and how it will be built - the practical "what"
- `status` (optional): New status (BACKLOG, TO_DO, IN_PROGRESS)
- `hero_ids` (optional): New list of hero UUIDs (replaces existing)
- `villain_ids` (optional): New list of villain UUIDs (replaces existing)
- `conflict_ids` (optional): New list of conflict UUIDs (replaces existing)
- `pillar_id` (optional): New strategic pillar UUID (use "null" to unlink)
- `theme_id` (optional): New roadmap theme UUID (use "null" to unlink)
- `narrative_intent` (optional): New narrative intent
- `strategic_description` (optional): New description of how this initiative connects to the larger product strategy - the "why"

**Returns:**
```json
{
  "status": "success",
  "type": "strategic_initiative",
  "message": "Updated strategic initiative I-1001",
  "data": {
    "id": "<uuid>",
    "initiative": {
      "id": "<uuid>",
      "title": "...",
      "description": "...",
      "identifier": "I-1001",
      "status": "IN_PROGRESS"
    },
    "strategic_context": {/* full strategic initiative details */},
    "narrative_summary": "Helps: Sarah | Defeats: Context Switching | Why: ..."
  },
  "next_steps": [
    "Strategic initiative 'Title' updated successfully"
  ]
}
```

**Use Cases:**
- Updating initiative titles, implementation descriptions, or status
- Updating strategic descriptions separately from implementation details
- Changing narrative connections (heroes, villains, conflicts)
- Re-linking to different pillars or themes
- Updating narrative intent

---

### `delete_strategic_initiative(query: str)`

Deletes a strategic initiative permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This deletes both the Initiative and its StrategicInitiative context.

Accepts a flexible query that tries multiple lookup strategies:
1. First tries as StrategicInitiative UUID
2. Then tries as Initiative UUID
3. Finally tries as Initiative identifier (e.g., "I-1001")

**Parameters:**
- `query`: Strategic initiative ID, initiative ID, or initiative identifier

**Returns:**
```json
{
  "status": "success",
  "type": "strategic_initiative",
  "message": "Deleted strategic initiative I-1001 (Initiative Title)",
  "data": {
    "deleted_identifier": "I-1001",
    "deleted_id": "<uuid>"
  }
}
```

**Use Cases:**
- Removing obsolete initiatives
- Strategic planning cleanup
- Removing duplicate initiatives

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
**Get Framework → Claude + User Collaborate → Submit Result**

### Framework Response Structure

All `get_*_framework()` tools return a rich framework dictionary with the following fields:

**Core Fields:**
- `entity_type`: Type of entity (vision, pillar, outcome, hero, villain, etc.)
- `purpose`: Why this entity matters
- `criteria`: Quality criteria for good entities
- `examples`: Good examples with explanations
- `questions_to_explore`: Guiding questions for refinement
- `anti_patterns`: What NOT to do with explanations
- `coaching_tips`: Tips for refinement
- `current_state`: Current workspace state for this entity type

**Natural Language Mapping Fields (Framework-Invisible UX):**

These fields help Claude Code conduct natural product conversations without exposing framework terminology:

- `conversation_guidelines`: Entity-specific phrasing guidance
  - `say_this`: Natural language to use
  - `not_this`: Framework term to avoid
  - `example_question`: Example natural question
- `natural_questions`: Maps framework concepts to natural conversational questions
- `extraction_guidance`: Patterns for parsing user input into structured entity fields
- `inference_examples`: How to infer entities when users don't explicitly state them

**Example Framework Response:**
```json
{
  "entity_type": "hero",
  "purpose": "Define who you're building for",
  "criteria": ["Specific person with a name", "Real motivations", "Observable pains"],
  "examples": [{"text": "Sarah, The Solo Builder", "why_good": "Specific, observable"}],
  "questions_to_explore": ["Who specifically are you building this for?"],
  "anti_patterns": [{"example": "Developers", "why_bad": "Too broad", "better": "Sarah"}],
  "coaching_tips": ["Be specific - give them a name and archetype"],
  "current_state": {"existing_heroes": [], "hero_count": 0},
  "conversation_guidelines": {
    "say_this": "use their actual name (Sarah, Alex)",
    "not_this": "the Hero, your hero persona",
    "example_question": "Who's the one person you're building this for?"
  },
  "natural_questions": [
    {"framework_term": "hero_identity", "natural_question": "Who's the one person you're building this for?"},
    {"framework_term": "pains", "natural_question": "What frustrates them most right now?"}
  ],
  "extraction_guidance": [
    {
      "from_input": "Solo founders drowning in feedback from everywhere",
      "extractions": {"name_pattern": "[Role], The [Descriptor]", "core_pain": "overwhelmed by input"}
    }
  ],
  "inference_examples": [
    {
      "user_says": "I keep talking to developers who lose hours switching tools",
      "inferences": {"hero_name": "A developer (give them a name)", "pain": "context switching"}
    }
  ]
}
```

---

### Vision Management

#### `get_vision_definition_framework(workspace_id: str)`

Returns comprehensive framework for defining a product vision through collaborative refinement.

**Returns:**
Framework dict with all standard fields plus vision-specific criteria.

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

#### `get_strategic_pillars()`

Lists all strategic pillars for the workspace.

**Returns:**
```json
{
  "status": "success",
  "type": "pillar",
  "message": "Found N strategic pillar(s)",
  "data": {
    "pillars": [
      {
        "id": "<uuid>",
        "name": "...",
        "description": "..."
      }
    ]
  }
}
```

**Use Cases:**
- Viewing current strategic pillars
- Checking available pillars before linking outcomes
- Strategic foundation review

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

#### `get_strategic_pillars()`

Lists all strategic pillars for the workspace.

**Returns:**
```json
{
  "status": "success",
  "type": "pillar",
  "message": "Found N strategic pillar(s)",
  "data": {
    "pillars": [
      {
        "id": "<uuid>",
        "name": "...",
        "description": "..."
      }
    ]
  }
}
```

**Use Cases:**
- Viewing all defined strategic pillars
- Getting pillar IDs for linking to outcomes
- Strategic planning review

---

#### `update_strategic_pillar(pillar_id: str, name: str | None, description: str | None)`

Updates an existing strategic pillar.

**Important:** Reflect the changes back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `pillar_id`: UUID of the strategic pillar to update
- `name`: New pillar name (optional, 1-100 characters)
- `description`: New pillar description (optional, 1-3000 characters)

**Returns:**
```json
{
  "status": "success",
  "type": "pillar",
  "message": "Updated strategic pillar 'Pillar Name'",
  "data": {
    "id": "<uuid>",
    "name": "...",
    "description": "..."
  }
}
```

**Use Cases:**
- Refining pillar descriptions
- Updating strategy and anti-strategy
- Renaming pillars

---

#### `delete_strategic_pillar(pillar_id: str)`

Deletes a strategic pillar permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also unlink the pillar from any associated outcomes and initiatives.

**Parameters:**
- `pillar_id`: UUID of the strategic pillar to delete

**Returns:**
```json
{
  "status": "success",
  "type": "pillar",
  "message": "Deleted strategic pillar 'Pillar Name'",
  "data": {
    "deleted_id": "<uuid>"
  }
}
```

**Use Cases:**
- Removing obsolete pillars
- Strategic foundation cleanup
- Consolidating overlapping pillars

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

#### `get_product_outcomes()`

Lists all product outcomes for the workspace.

**Returns:**
```json
{
  "status": "success",
  "type": "outcome",
  "message": "Found N product outcome(s)",
  "data": {
    "outcomes": [
      {
        "id": "<uuid>",
        "name": "...",
        "description": "...",
        "pillars": [/* linked pillars */]
      }
    ]
  }
}
```

**Use Cases:**
- Viewing all defined product outcomes
- Getting outcome IDs for linking to themes
- Strategic planning review

---

#### `update_product_outcome(outcome_id: str, name: str | None, description: str | None, pillar_ids: List[str] | None)`

Updates an existing product outcome.

**Important:** Reflect the changes back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `outcome_id`: UUID of the product outcome to update
- `name`: New outcome name (optional, 1-150 characters)
- `description`: New outcome description (optional, 1-3000 characters)
- `pillar_ids`: List of pillar UUIDs to link (optional, replaces existing links)

**Returns:**
```json
{
  "status": "success",
  "type": "outcome",
  "message": "Updated product outcome 'Outcome Name'",
  "data": {
    "id": "<uuid>",
    "name": "...",
    "description": "...",
    "pillars": [/* linked pillars */]
  },
  "next_steps": [
    "Product outcome 'Outcome Name' updated successfully",
    "Outcome now linked to N pillar(s)"
  ]
}
```

**Use Cases:**
- Updating metrics, baselines, or targets
- Changing pillar linkages
- Refining outcome descriptions

---

#### `delete_product_outcome(outcome_id: str)`

Deletes a product outcome permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also unlink the outcome from any associated pillars and themes.

**Parameters:**
- `outcome_id`: UUID of the product outcome to delete

**Returns:**
```json
{
  "status": "success",
  "type": "outcome",
  "message": "Deleted product outcome 'Outcome Name'",
  "data": {
    "deleted_id": "<uuid>"
  }
}
```

**Use Cases:**
- Removing obsolete outcomes
- Strategic foundation cleanup
- Consolidating overlapping outcomes

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

#### `get_roadmap_themes()`

Lists all roadmap themes for the workspace (both prioritized and unprioritized).

**Returns:**
```json
{
  "status": "success",
  "type": "theme",
  "message": "Found N roadmap theme(s)",
  "data": {
    "themes": [
      {
        "id": "<uuid>",
        "name": "...",
        "description": "...",
        "is_prioritized": true,
        "priority_order": 0,
        "outcomes": [/* linked outcomes */],
        "hero_id": "<uuid>",
        "primary_villain_id": "<uuid>"
      }
    ]
  }
}
```

**Use Cases:**
- Viewing all themes (prioritized and unprioritized)
- Getting theme IDs for linking to initiatives
- Roadmap planning review

---

#### `update_roadmap_theme(theme_id: str, name: str | None, description: str | None, outcome_ids: List[str] | None)`

Updates an existing roadmap theme.

**Important:** Reflect the changes back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `theme_id`: UUID of the roadmap theme to update
- `name`: New theme name (optional, 1-100 characters)
- `description`: New theme description (optional)
- `outcome_ids`: List of outcome UUIDs to link (optional, replaces existing links)

**Returns:**
```json
{
  "status": "success",
  "type": "theme",
  "message": "Updated roadmap theme 'Theme Name'",
  "data": {
    "id": "<uuid>",
    "name": "...",
    "description": "...",
    "is_prioritized": true,
    "priority_order": 0,
    "outcomes": [/* linked outcomes */]
  },
  "next_steps": [
    "Roadmap theme 'Theme Name' updated successfully",
    "Theme now linked to N outcome(s)",
    "Strategic alignment score: 0.75"
  ]
}
```

**Use Cases:**
- Updating problem statement, hypothesis, or metrics
- Changing outcome linkages
- Refining theme descriptions

---

#### `delete_roadmap_theme(theme_id: str)`

Deletes a roadmap theme permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also unlink the theme from any associated outcomes, heroes, and villains.

**Parameters:**
- `theme_id`: UUID of the roadmap theme to delete

**Returns:**
```json
{
  "status": "success",
  "type": "theme",
  "message": "Deleted roadmap theme 'Theme Name'",
  "data": {
    "deleted_id": "<uuid>"
  }
}
```

**Use Cases:**
- Removing obsolete themes
- Roadmap cleanup
- Consolidating overlapping themes

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

### `framework_invisible_conversation`

Establishes the conversation philosophy for strategic planning sessions. The framework should be Claude Code's internal scaffolding, NOT user-facing vocabulary.

**Core Principle:** Users should experience a natural product conversation, never learn framework terminology.

**Key Guidelines:**
- Never say "the Hero" - use their actual name (e.g., "Sarah", "Alex")
- Never say "the Villain" - say "the problem", "what's blocking them"
- Never say "the Vision" - say "what you're building toward"
- Never say "Strategic Pillar" - say "your approach", "what makes you different"
- Never say "Product Outcome" - say "what success looks like"
- Never say "Roadmap Theme" - say "your next focus area", "the hypothesis you want to test"

**Returns:** Markdown-formatted guide with:
- Core philosophy
- Terminology translation table (internal term → natural phrase)
- Conversation patterns (what not to say, what to say instead)
- Guidance for reflecting back to users
- How to work with existing entities by name

**Use Cases:**
- Establishing conversation norms for strategic planning sessions
- Reference for framework-invisible UX
- Training Claude Code to avoid exposing framework terminology

---

### `first_session_onboarding`

Comprehensive onboarding guide for first strategic planning sessions with new users. This prompt should be loaded immediately after `create_workspace()` to ensure proper conversation norms.

**When to Load:** After `create_workspace()` returns successfully. The response includes a `recommended_prompt` field pointing to this prompt.

**Key Sections:**
1. **Framework Overview:** Vision → Pillars → Outcomes → Themes → Initiatives hierarchy with time horizons
2. **Framework-Invisible Conversation Philosophy:** Embedded (no separate prompt load needed)
3. **Validation Workflow:** Reflect content back to user → get confirmation → submit pattern
4. **Entity Sequence:** Recommended order for first session entities
5. **Natural Questions Reference:** Quick-reference for each entity type
6. **Session Completion Checklist:** Ensures strategic initiative created

**Core Requirements:**
- Never expose framework terminology to users
- Always reflect content back to user, get explicit "yes" confirmation, then call submit_*()
- Create entities one at a time with validation (no batch submissions)
- Session MUST end with a strategic initiative that connects to hero, villain, conflict, pillar, and theme

**Returns:** Markdown-formatted comprehensive guide (~400 lines) with:
- Strategic hierarchy explanation
- Terminology translation table
- Validation workflow steps
- Entity sequence with natural questions
- Completion checklist

**Use Cases:**
- First session with a new user after workspace creation
- Ensuring framework-invisible UX from the start
- Establishing validation discipline
- Guaranteeing concrete "what to build first" outcome

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
   - Health check → Initiative selection → Task selection → Prioritization → Details → Planning → Updates → Implementation → Completion
3. **Validate context before updates** using `validate_context()`
4. **Get user confirmation** before making changes
5. **Update OpenBacklog first** before local implementation
6. **Use framework tools** for strategic planning (get framework, collaborate, submit)
7. **Link entities** for strategic alignment (outcomes to pillars, themes to outcomes)
8. **Track progress** using checklist item updates
9. **Framework-invisible conversations**: Use `framework_invisible_conversation` prompt for strategic planning sessions to ensure natural product conversations. Never expose framework terminology (Hero, Villain, Pillar) to users - use their own product language instead.
10. **Natural language extraction**: Use `conversation_guidelines` and `natural_questions` from framework responses to ask questions in the user's domain language, then extract structured data using `extraction_guidance` patterns.

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

All narrative framework tools include the standard framework response fields plus **natural language mapping fields** (`conversation_guidelines`, `natural_questions`, `extraction_guidance`, `inference_examples`) to support framework-invisible UX. See the Framework Response Structure section above for details.

### Hero Management

#### `get_hero_definition_framework()`

Returns comprehensive framework for defining a hero (user persona) through collaborative refinement.

**Returns:**
Framework dict with all standard fields. Key conversation guideline: Use the hero's actual name (e.g., "Sarah") instead of "the hero".

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

#### `update_hero(hero_identifier: str, name: str | None, description: str | None, is_primary: bool | None)`

Updates an existing hero's fields.

**Important:** Reflect the changes back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `hero_identifier`: Human-readable identifier (e.g., "H-2003")
- `name`: New hero name (optional)
- `description`: New hero description (optional)
- `is_primary`: Whether this is the primary hero (optional)

**Returns:**
```json
{
  "status": "success",
  "type": "hero",
  "message": "Updated hero H-2003",
  "data": {
    "id": "<uuid>",
    "identifier": "H-2003",
    "name": "...",
    "description": "...",
    "is_primary": true
  },
  "next_steps": [
    "Hero 'Sarah' (H-2003) updated successfully",
    "This hero is now set as your primary hero"
  ]
}
```

**Use Cases:**
- Refining hero descriptions
- Updating motivations, pains, or context
- Changing primary hero designation

---

#### `delete_hero(hero_identifier: str)`

Deletes a hero permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also remove the hero from any linked story arcs and conflicts.

**Parameters:**
- `hero_identifier`: Human-readable identifier (e.g., "H-2003")

**Returns:**
```json
{
  "status": "success",
  "type": "hero",
  "message": "Deleted hero H-2003 (Sarah)",
  "data": {
    "deleted_identifier": "H-2003",
    "deleted_id": "<uuid>"
  }
}
```

**Use Cases:**
- Removing obsolete personas
- Narrative cleanup
- Consolidating overlapping heroes

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

#### `update_villain(villain_identifier: str, name: str | None, villain_type: str | None, description: str | None, severity: int | None, is_defeated: bool | None)`

Updates an existing villain's fields.

**Important:** Reflect the changes back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `villain_identifier`: Human-readable identifier (e.g., "V-2003")
- `name`: New villain name (optional)
- `villain_type`: New type (EXTERNAL, INTERNAL, TECHNICAL, WORKFLOW, OTHER) (optional)
- `description`: New villain description (optional)
- `severity`: New severity 1-5 (optional)
- `is_defeated`: Whether the villain is defeated (optional)

**Returns:**
```json
{
  "status": "success",
  "type": "villain",
  "message": "Updated villain V-2003",
  "data": {
    "id": "<uuid>",
    "identifier": "V-2003",
    "name": "...",
    "villain_type": "WORKFLOW",
    "description": "...",
    "severity": 4,
    "is_defeated": false
  },
  "next_steps": [
    "Villain 'Context Switching' (V-2003) updated successfully"
  ]
}
```

**Use Cases:**
- Refining villain descriptions
- Updating severity assessments
- Changing villain type
- Marking villains as defeated/undefeated

---

#### `delete_villain(villain_identifier: str)`

Deletes a villain permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also remove the villain from any linked conflicts and story arcs.

**Parameters:**
- `villain_identifier`: Human-readable identifier (e.g., "V-2003")

**Returns:**
```json
{
  "status": "success",
  "type": "villain",
  "message": "Deleted villain V-2003 (Context Switching)",
  "data": {
    "deleted_identifier": "V-2003",
    "deleted_id": "<uuid>"
  }
}
```

**Use Cases:**
- Removing obsolete villains
- Narrative cleanup
- Consolidating overlapping villains

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

#### `update_conflict(conflict_identifier: str, description: str | None, roadmap_theme_id: str | None)`

Updates an existing conflict's fields.

**Important:** Reflect the changes back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `conflict_identifier`: Human-readable identifier (e.g., "C-2003")
- `description`: New conflict description (optional)
- `roadmap_theme_id`: New roadmap theme ID to link (optional, use "null" to unlink)

**Returns:**
```json
{
  "status": "success",
  "type": "conflict",
  "message": "Updated conflict C-2003",
  "data": {
    "id": "<uuid>",
    "identifier": "C-2003",
    "hero_id": "<uuid>",
    "villain_id": "<uuid>",
    "description": "...",
    "status": "OPEN",
    "story_arc_id": "<uuid>"
  },
  "next_steps": [
    "Conflict 'C-2003' updated successfully"
  ]
}
```

**Use Cases:**
- Refining conflict descriptions
- Linking/unlinking conflicts to story arcs
- Updating impact or stakes

---

#### `delete_conflict(conflict_identifier: str)`

Deletes a conflict permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone.

**Parameters:**
- `conflict_identifier`: Human-readable identifier (e.g., "C-2003")

**Returns:**
```json
{
  "status": "success",
  "type": "conflict",
  "message": "Deleted conflict C-2003",
  "data": {
    "deleted_identifier": "C-2003",
    "deleted_id": "<uuid>"
  }
}
```

**Use Cases:**
- Removing obsolete conflicts
- Narrative cleanup
- Removing duplicate conflicts

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
- Strategic initiatives: `src/mcp_server/prompt_driven_tools/strategic_initiatives.py`
- Roadmap themes: `src/mcp_server/prompt_driven_tools/roadmap_themes.py`
- Narrative heroes: `src/mcp_server/prompt_driven_tools/narrative_heroes.py`
- Narrative villains: `src/mcp_server/prompt_driven_tools/narrative_villains.py`
- Narrative conflicts: `src/mcp_server/prompt_driven_tools/narrative_conflicts.py`
- Narrative recap: `src/mcp_server/prompt_driven_tools/narrative_recap.py`
- Utilities: `src/mcp_server/prompt_driven_tools/utilities.py`
- Prompts: `src/mcp_server/slash_commands.py`
