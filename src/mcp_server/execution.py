# src/mcp_server/execution.py
"""Execution-only MCP server with minimal toolset for coding workflows.

This server exposes only the 5 tools needed for execution:
- query_strategic_initiatives
- submit_strategic_initiative (update existing initiatives only)
- query_tasks
- submit_task (update existing tasks only)
- get_strategic_context_summary

This reduces context window bloat when developers are focused on implementation
rather than strategic planning. Note that submit operations are update-only - use
the strategy-mode MCP server to create new initiatives or tasks.
"""
import logging
from typing import Any, Dict, List, Optional

from fastmcp.server import FastMCP
from mcp.server.fastmcp import Icon

from src.mcp_server.auth_factory import get_mcp_auth_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize authentication using the auth factory
auth_factory = get_mcp_auth_factory()
auth_provider, _, _ = auth_factory.initialize()

# Initialize FastMCP with OAuth authentication
mcp_execution = FastMCP(
    name="OpenBacklog Execution",
    auth=auth_provider,
    website_url="https://openbacklog.ai",
    icons=[
        Icon(
            src="https://www.openbacklog.ai/assets/ob_v2_64x64.png",
            mimeType="image/png",
        ),
    ],
)

# Import implementation functions (not the decorated versions)
from src.mcp_server.prompt_driven_tools.strategic_initiatives import (
    _query_strategic_initiatives_impl,
    _submit_strategic_initiative_impl,
)
from src.mcp_server.strategic_context_resource import (
    _get_strategic_context_summary_impl,
)
from src.mcp_server.task_tools import _query_tasks_impl, _submit_task_impl


# Register execution tools
@mcp_execution.tool()
async def query_strategic_initiatives(
    identifier: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    include_tasks: bool = False,
) -> Dict[str, Any]:
    """Query strategic initiatives with optional single-entity lookup.

    Query modes:
    - No params: Returns all strategic initiatives
    - identifier: Returns single initiative with full details + narrative summary
    - search: Returns initiatives matching search term (title/description)
    - status: Filters by status (e.g., "IN_PROGRESS" for active only)
    - include_tasks: Include tasks array (only when identifier provided)

    Args:
        identifier: Initiative identifier (e.g., "I-1001") for single lookup
        search: Search string for title/description matching
        status: Filter by status (BACKLOG, TO_DO, IN_PROGRESS)
        include_tasks: Include tasks array (only for single initiative)

    Returns:
        For single: initiative details with linked tasks and narrative summary
        For list/search: array of initiatives with narrative summaries
    """
    return await _query_strategic_initiatives_impl(
        identifier, search, status, include_tasks
    )


@mcp_execution.tool()
async def submit_strategic_initiative(
    strategic_initiative_identifier: str,
    title: Optional[str] = None,
    implementation_description: Optional[str] = None,
    strategic_description: Optional[str] = None,
    hero_identifiers: Optional[List[str]] = None,
    villain_identifiers: Optional[List[str]] = None,
    conflict_identifiers: Optional[List[str]] = None,
    pillar_identifier: Optional[str] = None,
    theme_identifier: Optional[str] = None,
    narrative_intent: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing strategic initiative.

    This execution-mode tool only supports updates to existing initiatives.
    To create new initiatives, use the strategy-mode MCP server.

    IMPORTANT: Reflect the initiative back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    Args:
        strategic_initiative_identifier: Initiative identifier (e.g., "I-1001") - required
        title: Initiative title (optional)
        implementation_description: What this initiative delivers and how it will be built (optional). Supports markdown formatting.
        strategic_description: How this initiative connects to the larger product strategy (optional)
        hero_identifiers: List of hero identifiers this initiative helps (optional)
        villain_identifiers: List of villain identifiers this initiative confronts (optional)
        conflict_identifiers: List of conflict identifiers this initiative addresses (optional)
        pillar_identifier: Strategic pillar identifier for alignment (optional, use "null" to unlink)
        theme_identifier: Roadmap theme identifier for placement (optional, use "null" to unlink)
        narrative_intent: Why this initiative matters narratively (optional)
        status: Initiative status (BACKLOG, TO_DO, IN_PROGRESS) (optional)

    Returns:
        Success response with updated initiative data, or error if initiative not found
    """
    return await _submit_strategic_initiative_impl(
        title,  # type: ignore[arg-type]
        implementation_description,  # type: ignore[arg-type]
        strategic_description,
        hero_identifiers,
        villain_identifiers,
        conflict_identifiers,
        pillar_identifier,
        theme_identifier,
        narrative_intent,
        status,
        strategic_initiative_identifier,
    )


@mcp_execution.tool()
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
    return await _query_tasks_impl(identifier, initiative_identifier, search)


@mcp_execution.tool()
async def submit_task(
    task_identifier: Optional[str] = None,
    initiative_identifier: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    checklist: Optional[List[Any]] = None,
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
    return await _submit_task_impl(
        task_identifier,
        initiative_identifier,
        title,
        description,
        status,
        task_type,
        checklist,
    )


@mcp_execution.tool()
async def get_strategic_context_summary() -> str:
    """Comprehensive strategic foundation summary.

    Returns a denormalized, human-readable summary of the complete strategic
    foundation including vision, pillars, outcomes, themes, heroes, and villains.

    This tool is designed to be called once to get complete strategic
    context in a single response—enabling developers to evaluate new ideas
    against the roadmap, understand priorities, and capture problems with
    full strategic context.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Rendered markdown string containing the complete strategic context.
    """
    return await _get_strategic_context_summary_impl()


if __name__ == "__main__":
    # Run with HTTP transport for hosted MCP server
    mcp_execution.run(
        transport="http",
        host="0.0.0.0",  # nosec
        port=9001,
    )
