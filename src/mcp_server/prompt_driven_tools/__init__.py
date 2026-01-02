"""Prompt-driven collaboration tools for strategic planning.

This package provides framework-based MCP tools that enable Claude Code
to guide users through strategic planning via natural conversation, rather
than rigid wizards or CRUD operations.

Pattern: Get Framework → Claude + User Collaborate → Submit Result
"""

from src.mcp_server.prompt_driven_tools.narrative_conflicts import *
from src.mcp_server.prompt_driven_tools.narrative_heroes import *
from src.mcp_server.prompt_driven_tools.narrative_villains import *
from src.mcp_server.prompt_driven_tools.product_outcomes import *
from src.mcp_server.prompt_driven_tools.product_vision import *
from src.mcp_server.prompt_driven_tools.roadmap_themes import *
from src.mcp_server.prompt_driven_tools.strategic_initiatives import *
from src.mcp_server.prompt_driven_tools.strategic_pillars import *
from src.mcp_server.prompt_driven_tools.unified_framework import *
from src.mcp_server.prompt_driven_tools.utilities import *

__all__ = [
    # Unified Framework Tool (replaces 8 individual framework tools)
    "get_framework",
    # Strategic Foundation - Vision
    "submit_product_vision",
    "get_vision_details",
    # Strategic Foundation - Pillars
    "submit_strategic_pillar",
    "query_strategic_pillars",
    "delete_strategic_pillar",
    # Strategic Foundation - Outcomes
    "submit_product_outcome",
    "query_product_outcomes",
    "delete_product_outcome",
    # Roadmap Themes
    "submit_roadmap_theme",
    "query_roadmap_themes",
    "delete_roadmap_theme",
    "set_theme_priority",
    "connect_theme_to_outcomes",
    # Narrative Layer - Heroes
    "submit_hero",
    "query_heroes",
    "delete_hero",
    # Narrative Layer - Villains
    "submit_villain",
    "query_villains",
    "delete_villain",
    # Narrative Layer - Conflicts
    "submit_conflict",
    "query_conflicts",
    "delete_conflict",
    # Strategic Initiatives
    "submit_strategic_initiative",
    "query_strategic_initiatives",
    "delete_strategic_initiative",
    # Utility Tools
    "connect_outcome_to_pillars",
]
