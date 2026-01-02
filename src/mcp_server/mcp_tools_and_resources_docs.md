# OpenBacklog MCP Server - Tools and Resources Documentation

This document provides a comprehensive overview of all tools and resources available through the OpenBacklog MCP server.

## Table of Contents

1. [Overview](#overview)
2. [Markdown Support](#markdown-support)
3. [Authentication](#authentication)
4. [Core Workflow Tools](#core-workflow-tools)
5. [Workspace Management Tools](#workspace-management-tools)
6. [Strategic Initiative Tools](#strategic-initiative-tools)
7. [Task Management Tools](#task-management-tools)
8. [Strategic Planning Tools](#strategic-planning-tools)
9. [Roadmap Management Tools](#roadmap-management-tools)
10. [Utility Tools](#utility-tools)
11. [Prompts](#prompts)
12. [Narrative Layer Tools](#narrative-layer-tools)
13. [Error Handling](#error-handling)
14. [Best Practices](#best-practices)
15. [Architecture Notes](#architecture-notes)

---

## Overview

The OpenBacklog MCP server provides a comprehensive set of tools for managing initiatives, tasks, and strategic planning through Claude Code. All tools follow a consistent pattern of returning structured JSON responses with status indicators.

**Server Configuration:**
- Name: OpenBacklog MCP server
- Transport: HTTP
- Host: 0.0.0.0
- Port: 9000

---

## Markdown Support

Description fields in OpenBacklog support **full GitHub-flavored markdown**. The UI renders these as rich text, so MCP clients should format descriptions using markdown for optimal display.

**Supported markdown features:**
- Headings (`## Heading`)
- Bold (`**bold**`) and italic (`*italic*`)
- Inline code (`` `code` ``) and code blocks (triple backticks)
- Bullet lists (`- item`) and numbered lists (`1. item`)
- Links (`[text](url)`)
- Blockquotes (`> quote`)

**Fields with markdown support:**

| Tool | Field | Notes |
|------|-------|-------|
| `submit_task` | `description` | Full markdown rendering |
| `submit_strategic_initiative` | `implementation_description` | Full markdown rendering |
| `submit_strategic_initiative` | `strategic_description` | Full markdown rendering |
| `submit_strategic_initiative` | `narrative_intent` | Full markdown, rendered with italic styling |

**Best Practice:** When creating or updating descriptions via MCP tools, use markdown formatting to structure content with headings, bullet points, and emphasis. This creates a better reading experience in the OpenBacklog UI.

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

## Strategic Initiative Tools

Strategic initiative tools follow the **prompt-driven collaboration pattern**:
**Get Framework → Claude + User Collaborate → Submit Result**

These tools create initiatives with full narrative connections (heroes, villains, conflicts, pillars, themes), bridging strategic planning with the narrative layer.

### `get_strategic_initiative_definition_framework()`

**Deprecated:** Use `get_framework(entity_type="initiative")` instead. This function still exists internally but is no longer registered as an MCP tool.

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
    "available_heroes": [{"identifier": "H-001", "name": "...", "is_primary": true}],
    "available_villains": [{"identifier": "V-001", "name": "...", "villain_type": "WORKFLOW"}],
    "available_pillars": [{"identifier": "P-001", "name": "...", "description": "..."}],
    "available_themes": [{"identifier": "T-001", "name": "...", "description": "..."}],
    "active_conflicts": [{"identifier": "C-001", "description": "..."}]
  },
  "coaching_tips": [/* refinement guidance */]
}
```

**Use Cases:**
- Starting initiative creation with full context
- Understanding available narrative connections (use identifiers like "H-001", "V-001" when linking)
- Guiding user through strategic initiative refinement

---

### `submit_strategic_initiative(title, implementation_description, hero_identifiers, villain_identifiers, conflict_identifiers, pillar_identifier, theme_identifier, narrative_intent, status, strategic_description, strategic_initiative_identifier?)` **(UPSERT)**

Creates a new strategic initiative or updates an existing one with optional narrative connections.

**UPSERT BEHAVIOR:**
- `strategic_initiative_identifier=None` → Creates new initiative
- `strategic_initiative_identifier="I-1001"` → Updates existing initiative

Creates both an Initiative and its StrategicInitiative context in one operation. Uses graceful degradation: invalid identifiers are skipped with warnings rather than failing.

**Important:** Reflect the initiative back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `title` (required): Initiative title (e.g., "Smart Context Switching")
- `implementation_description` (required): What this initiative delivers and how it will be built. This is the practical description of the work involved - the "what".
- `hero_identifiers` (optional): List of hero identifiers (e.g., ["H-001", "H-002"]) this initiative helps
- `villain_identifiers` (optional): List of villain identifiers (e.g., ["V-001"]) this initiative confronts
- `conflict_identifiers` (optional): List of conflict identifiers (e.g., ["C-001"]) this initiative addresses
- `pillar_identifier` (optional): Strategic pillar identifier (e.g., "P-001") for alignment
- `theme_identifier` (optional): Roadmap theme identifier (e.g., "T-001") for placement
- `narrative_intent` (optional): Why this initiative matters narratively
- `status` (optional): Initiative status (BACKLOG, TO_DO, IN_PROGRESS) - defaults to BACKLOG
- `strategic_description` (optional): How this initiative connects to the larger product strategy. Explains the "why" - user needs addressed, strategic alignment, and how it fits into the bigger picture. Defaults to `implementation_description` if not provided.
- `strategic_initiative_identifier` (optional): Initiative identifier (e.g., "I-1001") for updates - if provided, updates existing initiative instead of creating new

**Returns:**
```json
{
  "status": "success",
  "type": "strategic_initiative",
  "message": "Strategic initiative created with narrative connections",
  "data": {
    "initiative": {
      "identifier": "I-1001",
      "title": "...",
      "status": "BACKLOG"
    },
    "strategic_context": {/* full strategic initiative details */}
  },
  "next_steps": [/* what to do next */]
}
```

**Create New Example:**
```python
submit_strategic_initiative(
    title="Smart Context Switching",
    implementation_description="Auto-save and restore IDE context...",
    strategic_description="Addresses user need for seamless workflow...",
    hero_identifiers=["H-001"],
    villain_identifiers=["V-001"],
    pillar_identifier="P-001",
    status="TO_DO"
)
```

**Update Existing Example:**
```python
submit_strategic_initiative(
    strategic_initiative_identifier="I-1001",
    title="Updated Title",
    status="IN_PROGRESS",
    implementation_description="Updated implementation details..."
)
```

**Use Cases:**
- Creating initiatives with full strategic context
- Linking initiatives to heroes, villains, and conflicts
- Updating initiative titles, descriptions, or status
- Changing narrative connections

**Note:** Previously separate `update_strategic_initiative()` has been consolidated into this function. Use the `strategic_initiative_identifier` parameter to update existing initiatives.

---

### `query_strategic_initiatives(identifier?: str, search?: str, status?: str, include_tasks?: bool)`

Query strategic initiatives with flexible filtering and single-entity lookup.

**Query modes:**
- No params: Returns all strategic initiatives
- identifier: Returns single initiative with full details + narrative summary
- search: Returns initiatives matching search term (title/description)
- status: Filters by status (e.g., "IN_PROGRESS" for active only)
- include_tasks: Include tasks array (only when identifier provided)

Initiatives without a StrategicInitiative record will have one auto-created with minimal context to ensure all initiatives are visible.

**Parameters:**
- `identifier` (optional): Initiative identifier (e.g., "I-1001") for single lookup
- `search` (optional): Search string for title/description matching
- `status` (optional): Filter by status (BACKLOG, TO_DO, IN_PROGRESS)
- `include_tasks` (optional): Include tasks array (only for single initiative, default: false)

**Returns (list mode):**
```json
{
  "status": "success",
  "type": "strategic_initiative",
  "message": "Found N strategic initiative(s)",
  "data": {
    "strategic_initiatives": [
      {
        "initiative": {
          "identifier": "I-1001",
          "title": "...",
          "description": "...",
          "status": "IN_PROGRESS"
        },
        "strategic_context": {
          "heroes": [/* linked heroes with identifiers */],
          "villains": [/* linked villains with identifiers */],
          "conflicts": [/* linked conflicts with identifiers */],
          "pillar": {/* linked pillar with identifier */},
          "theme": {/* linked theme with identifier */},
          "narrative_intent": "..."
        },
        "narrative_summary": "Helps: Sarah | Defeats: Context Switching | Pillar: Deep IDE Integration"
      }
    ]
  }
}
```

**Returns (single mode):**
```json
{
  "status": "success",
  "type": "strategic_initiative",
  "message": "Found strategic initiative: Title",
  "data": {
    "initiative": {
      "id": "<uuid>",
      "identifier": "I-1001",
      "title": "...",
      "description": "...",
      "status": "IN_PROGRESS"
    },
    "strategic_context": {/* full strategic initiative details */},
    "narrative_summary": "Helps: Sarah | Defeats: Context Switching | Why: ...",
    "tasks": [/* optional, only if include_tasks=True */]
  }
}
```

**Examples:**
```python
# Get all initiatives
await query_strategic_initiatives()

# Get single initiative by identifier
await query_strategic_initiatives(identifier="I-1001")

# Get active initiatives only
await query_strategic_initiatives(status="IN_PROGRESS")

# Search initiatives
await query_strategic_initiatives(search="context switching")

# Get initiative with tasks
await query_strategic_initiatives(identifier="I-1001", include_tasks=True)

# Combine search and status filter
await query_strategic_initiatives(search="auth", status="IN_PROGRESS")
```

**Use Cases:**
- Viewing all initiatives with strategic context
- Getting full context for a specific initiative
- Starting workflow to select an initiative to work on
- Listing current active work with full strategic context
- Finding specific initiatives by keyword
- Searching by initiative identifier (e.g., "I-1001")
- Understanding narrative connections before work

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
    "deleted_identifier": "I-1001"
  }
}
```

**Use Cases:**
- Removing obsolete initiatives
- Strategic planning cleanup
- Removing duplicate initiatives

---

## Task Management Tools

### `get_initiative_tasks(initiative_identifier: str)`

Retrieves all tasks for a specific initiative.

**Parameters:**
- `initiative_identifier`: Initiative identifier (e.g., "I-1001")

**Returns:**
```json
{
  "status": "success",
  "type": "task",
  "message": "Found N tasks for initiative...",
  "initiative_identifier": "I-1001",
  "data": [/* array of tasks */]
}
```

**Use Cases:**
- Task selection after choosing initiative
- Reviewing initiative scope
- Task prioritization decisions

---

### `submit_task(initiative_identifier, title, description?, status?, task_type?, checklist?, task_identifier?)` **(UPSERT)**

Creates a new task or updates an existing task within an initiative.

**UPSERT BEHAVIOR:**
- `task_identifier=None` → Creates new task
- `task_identifier="T-001"` → Updates existing task

**Parameters:**
- `initiative_identifier` (required): Human-readable initiative identifier (e.g., "I-012")
- `title` (required): Task title (1-200 characters)
- `description` (optional): Task description (supports markdown formatting)
- `status` (optional): Task status (TO_DO, IN_PROGRESS, BLOCKED, DONE). Defaults to TO_DO for new tasks
- `task_type` (optional): Task type (e.g., CODING, TESTING, DOCUMENTATION, DESIGN)
- `checklist` (optional): Array of checklist items with `title` (string) and `is_complete` (boolean) fields. Replaces entire checklist if provided.
- `task_identifier` (optional): Task identifier (e.g., "T-001") - if provided, updates existing task instead of creating new

**Returns:**
```json
{
  "status": "success",
  "type": "task",
  "message": "Created task 'Task Title' (TM-001) in initiative I-012",
  "data": {
    "id": "<uuid>",
    "identifier": "TM-001",
    "title": "...",
    "description": "...",
    "status": "TO_DO",
    "type": null,
    "initiative_id": "<uuid>",
    "initiative_identifier": "I-012",
    "checklist_items": [{"id": "<uuid>", "title": "...", "is_complete": false}]
  },
  "next_steps": [
    "Task TM-001 created successfully"
  ]
}
```

**Create New Task Example:**
```python
submit_task(
    initiative_identifier="I-012",
    title="Implement authentication",
    description="Add OAuth login flow",
    status="TO_DO",
    checklist=[
        {"title": "Design login flow", "is_complete": false},
        {"title": "Implement OAuth provider", "is_complete": false}
    ]
)
```

**Update Existing Task Example:**
```python
submit_task(
    task_identifier="T-001",
    title="Updated task title",
    status="IN_PROGRESS",
    description="Updated description"
)
```

**Checklist Management:**
To update a task's checklist, use the `checklist` parameter with a full array of checklist items:
```python
submit_task(
    task_identifier="T-001",
    checklist=[
        {"title": "Step 1", "is_complete": true},
        {"title": "Step 2", "is_complete": false},
        {"title": "New step", "is_complete": false}
    ]
)
```
This replaces the entire checklist. To preserve existing items, retrieve the current checklist via `get_task_details()` first, then include all items in the new array.

**Use Cases:**
- Creating new tasks from MCP client (Claude Code, etc.)
- Breaking down initiatives into actionable tasks
- Creating tasks with initial checklist items
- Updating task titles, descriptions, or status
- Replacing task checklists
- Moving tasks between statuses

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

## Strategic Planning Tools

Strategic planning tools follow a **prompt-driven collaboration pattern**:
**Get Framework → Claude + User Collaborate → Submit Result**

### Framework Response Structure

All framework tools return a rich framework dictionary with the following fields:

**Note:** The `get_framework(entity_type)` unified tool consolidates 8 separate framework tools into a single parameterized tool, reducing token consumption. Individual `get_*_framework()` functions still exist internally but are no longer registered as MCP tools.

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

### Unified Framework Tool

#### `get_framework(entity_type: str)`

**Unified tool that replaces 8 separate framework tools.** Returns comprehensive framework for defining any entity type through collaborative refinement.

**Parameters:**
- `entity_type`: Type of entity to get framework for. Must be one of:
  - `"hero"` - User persona definition
  - `"villain"` - Problem/obstacle definition
  - `"conflict"` - Conflict between hero and villain
  - `"vision"` - Product vision statement
  - `"pillar"` - Strategic pillar definition
  - `"outcome"` - Product outcome definition
  - `"theme"` - Roadmap theme exploration
  - `"initiative"` - Strategic initiative definition

**Returns:**
Framework dict with all standard fields (see Framework Response Structure above) plus entity-specific criteria, examples, and current state.

**Example:**
```python
# Get framework for hero
await get_framework(entity_type="hero")

# Get framework for vision
await get_framework(entity_type="vision")
```

**Use Cases:**
- Starting entity creation/update workflows with full context
- Getting entity-specific guidance and examples
- Understanding current workspace state for an entity type
- All use cases that previously required individual `get_*_framework()` tools

**Benefits:**
- Reduces MCP tool count from 40 to 33 (17.5% reduction)
- Reduces token consumption by 25-30% (consolidates 8 tool definitions into 1)
- Simpler API surface while maintaining full functionality

---

### Vision Management

#### `get_vision_definition_framework()`

**Deprecated:** Use `get_framework(entity_type="vision")` instead. This function still exists internally but is no longer registered as an MCP tool.

Returns comprehensive framework for defining a product vision through collaborative refinement.

**Returns:**
Framework dict with all standard fields plus vision-specific criteria.

**Criteria:**
- Outcome-focused, not solution-focused
- Describes change in user's world
- Clear and inspiring
- 1-2 sentences (max 1000 characters)

---

#### `submit_product_vision(vision_text: str)`

Submits refined product vision to workspace.

**Parameters:**
- `vision_text`: Refined vision statement

**Returns:**
Success response with saved vision data and next steps.

---

#### `get_vision_details()`

Retrieves the current product vision for the workspace.

**Returns:**
```json
{
  "status": "success",
  "type": "vision",
  "message": "Retrieved product vision",
  "data": {
    "id": "<uuid>",
    "workspace_id": "<uuid>",
    "vision_text": "...",
    "created_at": "...",
    "updated_at": "..."
  }
}
```

**Error Response:**
Returns error if no vision is defined yet.

**Use Cases:**
- Quick retrieval of current vision without framework overhead
- Checking if vision exists before other operations
- Displaying current vision to users

---

### Strategic Pillars

#### `get_pillar_definition_framework()`

**Deprecated:** Use `get_framework(entity_type="pillar")` instead. This function still exists internally but is no longer registered as an MCP tool.

Returns framework for defining strategic pillars (differentiators).

**Returns:**
Framework similar to vision with pillar-specific criteria:
- Defensible differentiator
- Enables product outcomes
- 3-5 pillars recommended
- Each has name and description

---

#### `query_strategic_pillars(identifier?: str)`

Query strategic pillars with optional single-entity lookup.

**Query modes:**
- No params: Returns all strategic pillars
- identifier: Returns single pillar with linked outcomes

**Parameters:**
- `identifier` (optional): Pillar identifier (e.g., "P-001") for single lookup

**Returns (list mode):**
```json
{
  "status": "success",
  "type": "pillar",
  "message": "Found N strategic pillar(s)",
  "data": {
    "pillars": [
      {
        "identifier": "P-001",
        "name": "...",
        "description": "..."
      }
    ]
  }
}
```

**Returns (single mode):**
```json
{
  "status": "success",
  "type": "pillar",
  "message": "Found strategic pillar: Pillar Name",
  "data": {
    "identifier": "P-001",
    "name": "...",
    "description": "...",
    "linked_outcomes": [
      {
        "identifier": "O-001",
        "name": "...",
        "description": "..."
      }
    ]
  }
}
```

**Examples:**
```python
# Get all pillars
await query_strategic_pillars()

# Get single pillar by identifier
await query_strategic_pillars(identifier="P-001")
```

**Use Cases:**
- Viewing current strategic pillars
- Checking available pillars before linking outcomes
- Getting full pillar details with linked outcomes
- Understanding pillar-outcome relationships
- Strategic foundation review

---

#### `submit_strategic_pillar(name: str, description: str, pillar_identifier?: str)` **(UPSERT)**

Creates a new strategic pillar or updates an existing one.

**UPSERT BEHAVIOR:**
- `pillar_identifier=None` → Creates new pillar
- `pillar_identifier="P-001"` → Updates existing pillar

**Parameters:**
- `name`: Pillar name (1-100 characters, unique per workspace)
- `description`: Pillar description including strategy and anti-strategy (required)
  - Should include both what you'll do and what you won't do
  - Example: "Strategy: Provide seamless experience within developer's existing workflow. Anti-Strategy: No web-first experience, no mobile app, no Slack/Teams bots."
- `pillar_identifier` (optional): Pillar identifier (e.g., "P-001") - if provided, updates existing pillar instead of creating new

**Returns:**
Success response with saved pillar data and next steps.

**Create New Example:**
```python
submit_strategic_pillar(
    name="Deep IDE Integration",
    description="Strategy: Seamless workflow. Anti-Strategy: No web/mobile"
)
```

**Update Existing Example:**
```python
submit_strategic_pillar(
    pillar_identifier="P-001",
    name="Updated Pillar Name",
    description="Updated strategy..."
)
```

**Note:** Previously separate `update_strategic_pillar()` has been consolidated into this function. Use the `pillar_identifier` parameter to update existing pillars.

---

#### `delete_strategic_pillar(pillar_identifier: str)`

Deletes a strategic pillar permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also unlink the pillar from any associated outcomes and initiatives.

**Parameters:**
- `pillar_identifier`: Human-readable identifier (e.g., "P-001")

**Returns:**
```json
{
  "status": "success",
  "type": "pillar",
  "message": "Deleted strategic pillar 'Pillar Name' (P-001)",
  "data": {
    "deleted_identifier": "P-001"
  }
}
```

**Use Cases:**
- Removing obsolete pillars
- Strategic foundation cleanup
- Consolidating overlapping pillars

---

### Product Outcomes

#### `get_outcome_definition_framework()`

**Deprecated:** Use `get_framework(entity_type="outcome")` instead. This function still exists internally but is no longer registered as an MCP tool.

Returns framework for defining measurable product outcomes.

**Returns:**
Framework with outcome-specific guidance:
- Measurable impact on users
- Links to strategic pillars
- Has baseline and target
- Time-bound (usually 12 months)

---

#### `submit_product_outcome(name: str, description: str, pillar_identifiers?: List[str], outcome_identifier?: str)` **(UPSERT)**

Creates a new product outcome or updates an existing one.

**UPSERT BEHAVIOR:**
- `outcome_identifier=None` → Creates new outcome
- `outcome_identifier="O-002"` → Updates existing outcome

**Parameters:**
- `name`: Outcome name (1-150 characters)
- `description`: Outcome description including goal, baseline, target, and timeline (required)
  - Should include: specific metric, baseline value, target value, and timeline
  - Example: "Goal: Increase daily active IDE plugin users. Baseline: 30% of users daily active. Target: 80% daily active. Timeline: 6 months."
- `pillar_identifiers` (optional): List of pillar identifiers (e.g., ["P-001", "P-002"]) to link (recommended for strategic alignment)
- `outcome_identifier` (optional): Outcome identifier (e.g., "O-002") - if provided, updates existing outcome instead of creating new

**Returns:**
Success response with saved outcome data and next steps.

**Create New Example:**
```python
submit_product_outcome(
    name="Developer Daily Adoption",
    description="Goal: Increase daily active IDE plugin users. Baseline: 30% of users daily active. Target: 80% daily active. Timeline: 6 months.",
    pillar_identifiers=["P-001"]
)
```

**Update Existing Example:**
```python
submit_product_outcome(
    outcome_identifier="O-002",
    description="Updated description...",
    pillar_identifiers=["P-001", "P-002"]
)
```

**Note:** Previously separate `update_product_outcome()` has been consolidated into this function. The `pillar_identifiers` parameter handles linking to pillars. Use the `outcome_identifier` parameter to update existing outcomes.

---

#### `query_product_outcomes(identifier?: str)`

Query product outcomes with optional single-entity lookup.

**Query modes:**
- No params: Returns all product outcomes
- identifier: Returns single outcome with linked pillars and themes

**Parameters:**
- `identifier` (optional): Outcome identifier (e.g., "O-001") for single lookup

**Returns (list mode):**
```json
{
  "status": "success",
  "type": "outcome",
  "message": "Found N product outcome(s)",
  "data": {
    "outcomes": [
      {
        "identifier": "O-001",
        "name": "...",
        "description": "...",
        "pillars": [/* linked pillars with identifiers */]
      }
    ]
  }
}
```

**Returns (single mode):**
```json
{
  "status": "success",
  "type": "outcome",
  "message": "Found product outcome: Outcome Name",
  "data": {
    "identifier": "O-001",
    "name": "...",
    "description": "...",
    "pillars": [/* linked pillars with identifiers */],
    "pillar_names": ["Pillar 1", "Pillar 2"],
    "linked_themes": [
      {
        "identifier": "T-001",
        "name": "...",
        "is_prioritized": true
      }
    ]
  }
}
```

**Examples:**
```python
# Get all outcomes
await query_product_outcomes()

# Get single outcome by identifier
await query_product_outcomes(identifier="O-001")
```

**Use Cases:**
- Viewing all defined product outcomes
- Getting outcome IDs for linking to themes
- Getting full outcome details with linked entities
- Strategic planning review

---

#### `delete_product_outcome(outcome_identifier: str)`

Deletes a product outcome permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also unlink the outcome from any associated pillars and themes.

**Parameters:**
- `outcome_identifier`: Human-readable identifier (e.g., "O-001")

**Returns:**
```json
{
  "status": "success",
  "type": "outcome",
  "message": "Deleted product outcome 'Outcome Name' (O-001)",
  "data": {
    "deleted_identifier": "O-001"
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

#### `get_theme_exploration_framework()`

**Deprecated:** Use `get_framework(entity_type="theme")` instead. This function still exists internally but is no longer registered as an MCP tool.

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

#### `submit_roadmap_theme(name: str, description: str, outcome_identifiers?: List[str], hero_identifier?: str, primary_villain_identifier?: str, theme_identifier?: str)` **(UPSERT)**

Creates a new roadmap theme or updates an existing one.

**UPSERT BEHAVIOR:**
- `theme_identifier=None` → Creates new theme
- `theme_identifier="T-001"` → Updates existing theme

**Parameters:**
- `name`: Theme name (1-100 characters, unique per workspace)
- `description`: Theme description including problem statement, hypothesis, metrics, and timeline (required)
  - Should include: specific problem, testable hypothesis, indicative metrics, and timeline
  - Example: "Problem Statement: New users abandon setup (40% drop-off). Hypothesis: Smart defaults will increase completion from 40% to 70%. Indicative Metrics: Setup completion rate. Timeline: 6 months."
- `outcome_identifiers` (optional): List of outcome identifiers (e.g., ["O-001", "O-002"]) to link (recommended for strategic alignment)
- `hero_identifier` (optional): Human-readable hero identifier (e.g., "H-001") to link who benefits
- `primary_villain_identifier` (optional): Human-readable villain identifier (e.g., "V-001") to link what problem is solved
- `theme_identifier` (optional): Theme identifier (e.g., "T-001") - if provided, updates existing theme instead of creating new

**Returns:**
Success response with theme data and next steps.

**Create New Example:**
```python
submit_roadmap_theme(
    name="First-Week Configuration Success",
    description="Problem Statement: New users abandon setup (40% drop-off)...",
    outcome_identifiers=["O-001"],
    hero_identifier="H-001",
    primary_villain_identifier="V-001"
)
```

**Update Existing Example:**
```python
submit_roadmap_theme(
    theme_identifier="T-001",
    description="Updated problem statement...",
    outcome_identifiers=["O-001", "O-002"]
)
```

**Note:** Previously separate `update_roadmap_theme()` has been consolidated into this function. Hero and villain linking is now handled via identifier parameters. Use the `theme_identifier` parameter to update existing themes.

---

### Prioritization

#### `set_theme_priority(theme_identifier: str, priority_position?: int)`

Sets theme priority position or deprioritizes a theme.

**BEHAVIOR:**
- `priority_position=0,1,2,...` → Prioritizes theme at specified position (0 = highest priority)
- `priority_position=None` → Deprioritizes theme (moves to backlog)

**Parameters:**
- `theme_identifier`: Human-readable identifier (e.g., "T-001")
- `priority_position` (optional): Priority position (0-indexed, None to deprioritize)

**Returns:**
Success response confirming priority change.

**Prioritize Example:**
```python
set_theme_priority(
    theme_identifier="T-001",
    priority_position=0  # Highest priority
)
```

**Deprioritize Example:**
```python
set_theme_priority(
    theme_identifier="T-001",
    priority_position=None  # Move to backlog
)
```

**Use Cases:**
- Adding theme to active roadmap
- Changing theme priority order
- Moving theme back to backlog

**Note:** Previously separate `prioritize_workstream()` and `deprioritize_workstream()` functions have been consolidated into this single function.

---

#### `connect_theme_to_outcomes(theme_identifier: str, outcome_identifiers: List[str])`

Links a roadmap theme to product outcomes for alignment tracking.

**Parameters:**
- `theme_identifier`: Human-readable identifier (e.g., "T-001")
- `outcome_identifiers`: List of outcome identifiers (e.g., ["O-001", "O-002"])

**Returns:**
Success response with alignment score.

---

#### `query_roadmap_themes(identifier?: str, prioritized_only?: bool)`

Query roadmap themes with optional filtering and single-entity lookup.

**Query modes:**
- No params: Returns all themes (prioritized and unprioritized)
- identifier: Returns single theme with full linked entities and alignment score
- prioritized_only: Returns only prioritized themes

**Parameters:**
- `identifier` (optional): Theme identifier (e.g., "T-001") for single lookup
- `prioritized_only` (optional): If True, filters to prioritized themes only (default: false)

**Returns (list mode):**
```json
{
  "status": "success",
  "type": "theme",
  "message": "Found N roadmap theme(s)",
  "data": {
    "themes": [
      {
        "identifier": "T-001",
        "name": "...",
        "description": "...",
        "is_prioritized": true,
        "priority_order": 0,
        "outcomes": [/* linked outcomes with identifiers */],
        "hero_identifier": "H-001",
        "primary_villain_identifier": "V-001"
      }
    ]
  }
}
```

**Returns (single mode):**
```json
{
  "status": "success",
  "type": "theme",
  "message": "Found roadmap theme: Theme Name",
  "data": {
    "identifier": "T-001",
    "name": "...",
    "description": "...",
    "outcome_names": ["Outcome 1", "Outcome 2"],
    "hero_names": ["Sarah"],
    "villain_names": ["Context Switching"],
    "primary_villain_name": "Context Switching",
    "is_prioritized": true,
    "alignment_score": 0.85
  }
}
```

**Examples:**
```python
# Get all themes
await query_roadmap_themes()

# Get single theme by identifier
await query_roadmap_themes(identifier="T-001")

# Get only prioritized themes
await query_roadmap_themes(prioritized_only=True)
```

**Use Cases:**
- Viewing all themes (prioritized and unprioritized)
- Getting theme IDs for linking to initiatives
- Getting full theme details with alignment score
- Roadmap planning review

---

#### `delete_roadmap_theme(theme_identifier: str)`

Deletes a roadmap theme permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also unlink the theme from any associated outcomes, heroes, and villains.

**Parameters:**
- `theme_identifier`: Human-readable identifier (e.g., "T-001")

**Returns:**
```json
{
  "status": "success",
  "type": "theme",
  "message": "Deleted roadmap theme 'Theme Name' (T-001)",
  "data": {
    "deleted_identifier": "T-001"
  }
}
```

**Use Cases:**
- Removing obsolete themes
- Roadmap cleanup
- Consolidating overlapping themes

---

## Utility Tools


### `connect_outcome_to_pillars(outcome_identifier: str, pillar_identifiers: List[str])`

Links a product outcome to strategic pillars for validation.

**Parameters:**
- `outcome_identifier`: Human-readable identifier (e.g., "O-001")
- `pillar_identifiers`: List of pillar identifiers (e.g., "P-001")

**Returns:**
Success response with updated outcome data.

**Use Cases:**
- Validating outcome supports strategic differentiation
- Creating outcome-pillar linkages
- Strategic alignment

---

### `get_strategic_context_summary()`

Returns a comprehensive, human-readable strategic foundation summary.

This tool generates a denormalized markdown summary of the complete strategic foundation including vision, pillars, outcomes, themes, heroes, and villains. It's designed to be called once to get complete strategic context in a single response.

**Returns:** Rendered markdown string containing:

1. **How to Use This Context** - Instructions for evaluating ideas against strategy
2. **Vision** - The product vision statement (with warning if missing)
3. **Strategic Pillars** - All pillars with descriptions and anti-strategies
4. **Product Outcomes** - Success metrics with pillar linkages
5. **Roadmap Themes** - Prioritized (⭐) and backlog themes with outcome linkages
6. **Heroes** - User personas with primary indicator (👑)
7. **Villains** - Problems with severity indicators and defeat status
8. **Strategic Foundation Health** - Summary table showing completeness

**Example Output:**

```markdown
# Strategic Context Summary

> This summary provides the complete strategic foundation for your product...

## Vision
> Enable developers to manage tasks without leaving their IDE

## Strategic Pillars (How We Win)
### P-001: Deep IDE Integration
Strategy: Seamless developer workflow. Anti-Strategy: No web/mobile...

## Roadmap Themes (Current Bets)
### Prioritized Themes (Active Focus)
#### T-001: MCP-Native Product Management ⭐ Priority #1
...

## Heroes (Who We're Building For)
### H-001: Alex, The Solo Builder 👑 PRIMARY
...

## Strategic Foundation Health
✅ **Healthy Foundation** — All strategic elements are in place.
```

**When to Use:**
- At the start of a session to understand the complete strategic context
- When evaluating whether a new idea aligns with the roadmap
- When you need to understand priorities and strategic direction
- To check for gaps in the strategic foundation

**Related Tools:**
- `review_strategic_foundation()` - For structured JSON health check with actionable recommendations
- `get_story_bible()` - For narrative entities (conflicts, turning points)

---

## Prompts

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
6. **Use framework tools** for strategic planning (use `get_framework(entity_type)` unified tool, collaborate, submit)
7. **Link entities** for strategic alignment (outcomes to pillars, themes to outcomes)
8. **Track progress** using checklist updates via the `checklist` parameter in `submit_task()`
9. **Framework-invisible conversations**: Use `framework_invisible_conversation` prompt for strategic planning sessions to ensure natural product conversations. Never expose framework terminology (Hero, Villain, Pillar) to users - use their own product language instead.
10. **Natural language extraction**: Use `conversation_guidelines` and `natural_questions` from framework responses to ask questions in the user's domain language, then extract structured data using `extraction_guidance` patterns.
11. **Use upsert pattern**: All `submit_*` functions support both create and update via optional identifier parameters. Pass identifier to update (e.g., `hero_identifier="H-001"`), omit to create.
12. **Partial updates**: When updating entities, only provide fields you want to change. Omitted fields preserve existing values. For example, `submit_hero(hero_identifier="H-001", name="New Name")` updates only the name.
13. **Use unified query tools**: Each entity type has a single `query_*` function (e.g., `query_heroes`, `query_strategic_initiatives`) that handles both listing and single-entity lookup. Pass `identifier` parameter for details, omit for list view. Some also support filtering (e.g., `status`, `active_only`, `prioritized_only`).

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

**Deprecated:** Use `get_framework(entity_type="hero")` instead. This function still exists internally but is no longer registered as an MCP tool.

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

#### `submit_hero(name: str, description: str | None, is_primary: bool, hero_identifier?: str)` **(UPSERT)**

Creates a new hero or updates an existing hero (user persona).

**UPSERT BEHAVIOR:**
- `hero_identifier=None` → Creates new hero
- `hero_identifier="H-001"` → Updates existing hero

**Parameters:**
- `name`: Hero name (e.g., "Sarah, The Solo Builder")
- `description`: Rich description including who they are, motivations, jobs-to-be-done, pains, desired gains, and context
- `is_primary`: Whether this is the primary hero (default: false)
- `hero_identifier` (optional): Hero identifier (e.g., "H-001") - if provided, updates existing hero instead of creating new

**Returns:**
Success response with created/updated hero (including identifier like "H-001") and next steps.

**Create New Example:**
```python
submit_hero(
    name="Sarah, The Solo Builder",
    description="Sarah is a solo developer building her own SaaS...",
    is_primary=True
)
```

**Update Existing Example:**
```python
submit_hero(
    hero_identifier="H-001",
    name="Sarah Updated",
    is_primary=False
)
```

**Note:** Previously separate `update_hero()` has been consolidated into this function. Use the `hero_identifier` parameter to update existing heroes.

---

#### `query_heroes(identifier?: str)`

Query heroes with optional single-entity lookup.

**Query modes:**
- No params: Returns all heroes (list view)
- identifier: Returns single hero with full details + journey_summary

**Parameters:**
- `identifier` (optional): Hero identifier (e.g., "H-001") for single lookup

**Returns (list mode):**
```json
{
  "status": "success",
  "type": "hero",
  "message": "Found N hero(es)",
  "data": {
    "heroes": [
      {
        "identifier": "H-001",
        "name": "...",
        "description": "...",
        "is_primary": true
      }
    ]
  }
}
```

**Returns (single mode):**
```json
{
  "status": "success",
  "type": "hero",
  "message": "Found hero: Sarah",
  "data": {
    "identifier": "H-001",
    "name": "...",
    "description": "...",
    "is_primary": true,
    "journey_summary": {
      "active_arcs": [...],
      "open_conflicts": [...]
    }
  }
}
```

**Examples:**
```python
# Get all heroes
await query_heroes()

# Get single hero by identifier
await query_heroes(identifier="H-001")
```

**Use Cases:**
- Viewing all heroes for a workspace
- Getting full hero details with journey summary
- Understanding active arcs and open conflicts for a hero

---

#### `delete_hero(hero_identifier: str)`

Deletes a hero permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also remove the hero from any linked story arcs and conflicts.

**Parameters:**
- `hero_identifier`: Human-readable identifier (e.g., "H-001")

**Returns:**
```json
{
  "status": "success",
  "type": "hero",
  "message": "Deleted hero H-001 (Sarah)",
  "data": {
    "deleted_identifier": "H-001"
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

**Deprecated:** Use `get_framework(entity_type="villain")` instead. This function still exists internally but is no longer registered as an MCP tool.

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

#### `submit_villain(name: str, villain_type: str, description: str, severity: int, is_defeated?: bool, villain_identifier?: str)` **(UPSERT)**

Creates a new villain or updates an existing villain (problem/obstacle).

**UPSERT BEHAVIOR:**
- `villain_identifier=None` → Creates new villain
- `villain_identifier="V-001"` → Updates existing villain

**Parameters:**
- `name`: Villain name (e.g., "Context Switching")
- `villain_type`: Type (EXTERNAL, INTERNAL, TECHNICAL, WORKFLOW, OTHER)
- `description`: Rich description including how it manifests, impact, and evidence
- `severity`: How big a threat (1-5)
- `is_defeated` (optional): Whether the villain is defeated (default: false)
- `villain_identifier` (optional): Villain identifier (e.g., "V-001") - if provided, updates existing villain instead of creating new

**Returns:**
Success response with created/updated villain (including identifier like "V-001") and next steps.

**Create New Example:**
```python
submit_villain(
    name="Context Switching",
    villain_type="WORKFLOW",
    description="Jumping between tools breaks developer flow...",
    severity=4
)
```

**Update Existing Example:**
```python
submit_villain(
    villain_identifier="V-001",
    severity=5,
    is_defeated=True
)
```

**Note:** Previously separate `update_villain()` and `mark_villain_defeated()` have been consolidated into this function. Use the `is_defeated` parameter to mark villains as defeated.

---

#### `query_villains(identifier?: str, active_only?: bool)`

Query villains with optional filtering and single-entity lookup.

**Query modes:**
- No params: Returns all villains
- identifier: Returns single villain with full details + battle_summary
- active_only: Filters to non-defeated villains only

**Parameters:**
- `identifier` (optional): Villain identifier (e.g., "V-001") for single lookup
- `active_only` (optional): If True, filters to non-defeated villains only (default: false)

**Returns (list mode):**
```json
{
  "status": "success",
  "type": "villain",
  "message": "Found N villain(s)",
  "data": {
    "villains": [
      {
        "identifier": "V-001",
        "name": "Context Switching",
        "villain_type": "WORKFLOW",
        "severity": 4,
        "is_defeated": false
      }
    ]
  }
}
```

**Returns (single mode):**
```json
{
  "status": "success",
  "type": "villain",
  "message": "Found villain: Context Switching",
  "data": {
    "identifier": "V-001",
    "name": "Context Switching",
    "villain_type": "WORKFLOW",
    "description": "...",
    "severity": 4,
    "is_defeated": false,
    "battle_summary": {
      "conflict_count": 2,
      "theme_count": 1,
      "initiative_count": 3,
      "active_conflicts": [/* conflict details with identifiers */],
      "linked_themes": [/* theme details with identifiers */],
      "confronting_initiatives": [/* initiative details with identifiers */]
    }
  }
}
```

**Examples:**
```python
# Get all villains
await query_villains()

# Get single villain by identifier
await query_villains(identifier="V-001")

# Get only active (non-defeated) villains
await query_villains(active_only=True)
```

**Use Cases:**
- Viewing all villains for a workspace
- Getting comprehensive villain context with battle summary
- Understanding what initiatives are fighting this villain
- Reviewing conflicts and themes related to a villain
- Filtering to only active threats
- Strategic planning around specific problems

---

#### `delete_villain(villain_identifier: str)`

Deletes a villain permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone. This will also remove the villain from any linked conflicts and story arcs.

**Parameters:**
- `villain_identifier`: Human-readable identifier (e.g., "V-001")

**Returns:**
```json
{
  "status": "success",
  "type": "villain",
  "message": "Deleted villain V-001 (Context Switching)",
  "data": {
    "deleted_identifier": "V-001"
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

**Deprecated:** Use `get_framework(entity_type="conflict")` instead. This function still exists internally but is no longer registered as an MCP tool.

Returns framework for creating conflicts between heroes and villains.

**Returns:**
Framework dict with purpose, criteria, examples, questions, anti-patterns, current state (available heroes/villains), and coaching tips.

---

#### `submit_conflict(hero_identifier: str | None, villain_identifier: str | None, description: str | None, roadmap_theme_identifier: str | None, resolved_by_initiative_identifier: str | None, conflict_identifier: str | None)` **(UPSERT)**

Creates a new conflict or updates an existing conflict.

**Upsert Behavior:**
- If `conflict_identifier` is **omitted**: Creates new conflict
- If `conflict_identifier` is **provided**: Updates existing conflict

**Important:** Reflect the conflict back to the user and get explicit confirmation BEFORE calling this function. This persists immediately.

**Parameters:**
- `hero_identifier`: Human-readable hero identifier (required for create, e.g., "H-001")
- `villain_identifier`: Human-readable villain identifier (required for create, e.g., "V-001")
- `description`: Rich description including conflict statement, impact, and stakes (required for create, optional for update)
- `roadmap_theme_identifier`: Optional roadmap theme identifier to link (e.g., "T-001"), use "null" or "" to unlink
- `resolved_by_initiative_identifier`: Initiative identifier that resolved this conflict (e.g., "I-1001")
- `conflict_identifier`: If provided, updates existing conflict (e.g., "C-001")

**Create Example:**
```python
submit_conflict(
    hero_identifier="H-001",
    villain_identifier="V-001",
    description="Sarah cannot access product context from IDE...",
    roadmap_theme_identifier="T-001"
)
```

**Update Example:**
```python
submit_conflict(
    conflict_identifier="C-001",
    description="Updated description...",
    resolved_by_initiative_identifier="I-1001"
)
```

**Returns:**
Success response with created or updated conflict.

**Note:** Previously separate `create_conflict()`, `update_conflict()`, and `mark_conflict_resolved()` functions have been consolidated into this single upsert function.

---

#### `query_conflicts(identifier?: str, status?: str, hero_identifier?: str, villain_identifier?: str)`

Query conflicts with flexible filtering and single-entity lookup.

**Query modes:**
- No params: Returns all conflicts
- identifier: Returns single conflict with full hero/villain context
- Filters (status, hero_identifier, villain_identifier): Can be combined

**Parameters:**
- `identifier` (optional): Conflict identifier (e.g., "C-001") for single lookup
- `status` (optional): Filter by status (OPEN, ESCALATING, RESOLVING, RESOLVED)
- `hero_identifier` (optional): Filter by hero identifier (e.g., "H-001")
- `villain_identifier` (optional): Filter by villain identifier (e.g., "V-001")

**Returns (list mode):**
```json
{
  "status": "success",
  "type": "conflict",
  "message": "Found N conflict(s)",
  "data": {
    "conflicts": [
      {
        "identifier": "C-001",
        "description": "...",
        "status": "OPEN",
        "hero": {/* hero details */},
        "villain": {/* villain details */}
      }
    ]
  }
}
```

**Returns (single mode):**
```json
{
  "status": "success",
  "type": "conflict",
  "message": "Found conflict: C-001",
  "data": {
    "identifier": "C-001",
    "description": "...",
    "status": "OPEN",
    "hero": {/* hero details */},
    "villain": {/* villain details */},
    "roadmap_theme": {/* theme details if linked */}
  }
}
```

**Examples:**
```python
# Get all conflicts
await query_conflicts()

# Get single conflict by identifier
await query_conflicts(identifier="C-001")

# Get open conflicts only
await query_conflicts(status="OPEN")

# Get conflicts for a specific hero
await query_conflicts(hero_identifier="H-001")

# Combine filters
await query_conflicts(status="OPEN", hero_identifier="H-001")
```

**Use Cases:**
- Viewing all conflicts for a workspace
- Getting full conflict details with hero/villain context
- Filtering by status, hero, or villain
- Understanding conflict resolution status

---

#### `delete_conflict(conflict_identifier: str)`

Deletes a conflict permanently.

**Important:** Confirm with user BEFORE calling - this action cannot be undone.

**Parameters:**
- `conflict_identifier`: Human-readable identifier (e.g., "C-001")

**Returns:**
```json
{
  "status": "success",
  "type": "conflict",
  "message": "Deleted conflict C-001",
  "data": {
    "deleted_identifier": "C-001"
  }
}
```

**Use Cases:**
- Removing obsolete conflicts
- Narrative cleanup
- Removing duplicate conflicts

---

### Enhanced Roadmap Theme Tools

#### `submit_roadmap_theme(..., hero_identifier: str | None, primary_villain_identifier: str | None)`

Updated to accept optional hero and villain identifiers for narrative linking.

**New Parameters:**
- `hero_identifier`: Optional human-readable hero identifier (e.g., "H-001")
- `primary_villain_identifier`: Optional human-readable villain identifier (e.g., "V-001")

---

#### `link_theme_to_hero(theme_identifier: str, hero_identifier: str)`

Links a roadmap theme to a hero.

**Parameters:**
- `theme_identifier`: Human-readable identifier (e.g., "T-001")
- `hero_identifier`: Human-readable hero identifier (e.g., "H-001")

**Returns:**
Success response with updated theme.

---

#### `link_theme_to_villain(theme_identifier: str, villain_identifier: str)`

Links a roadmap theme to a villain.

**Parameters:**
- `theme_identifier`: Human-readable identifier (e.g., "T-001")
- `villain_identifier`: Human-readable villain identifier (e.g., "V-001")

**Returns:**
Success response with updated theme.

---

## Related Documentation

- Main server: `src/mcp_server/main.py`
- Health check: `src/mcp_server/healthcheck_tool.py`
- Initiative tools: `src/mcp_server/initiative_tools.py`
- Task tools: `src/mcp_server/task_tools.py`
- Workflow: `src/mcp_server/start_openbacklog_workflow.py`
- Strategic initiatives: `src/mcp_server/prompt_driven_tools/strategic_initiatives.py`
- Roadmap themes: `src/mcp_server/prompt_driven_tools/roadmap_themes.py`
- Narrative heroes: `src/mcp_server/prompt_driven_tools/narrative_heroes.py`
- Narrative villains: `src/mcp_server/prompt_driven_tools/narrative_villains.py`
- Narrative conflicts: `src/mcp_server/prompt_driven_tools/narrative_conflicts.py`
- Utilities: `src/mcp_server/prompt_driven_tools/utilities.py`
- Prompts: `src/mcp_server/slash_commands.py`
