"""Prompt-driven collaboration tools for strategic planning.

This package provides framework-based MCP tools that enable Claude Code
to guide users through strategic planning via natural conversation, rather
than rigid wizards or CRUD operations.

Pattern: Get Framework → Claude + User Collaborate → Submit Result
"""

from src.mcp_server.prompt_driven_tools.narrative_conflicts import *
from src.mcp_server.prompt_driven_tools.narrative_heroes import *
from src.mcp_server.prompt_driven_tools.narrative_recap import *
from src.mcp_server.prompt_driven_tools.narrative_villains import *
from src.mcp_server.prompt_driven_tools.product_outcomes import *
from src.mcp_server.prompt_driven_tools.product_vision import *
from src.mcp_server.prompt_driven_tools.roadmap_themes import *
from src.mcp_server.prompt_driven_tools.strategic_initiatives import *
from src.mcp_server.prompt_driven_tools.strategic_pillars import *
from src.mcp_server.prompt_driven_tools.utilities import *

__all__ = [
    # Strategic Foundation - Vision
    "get_vision_definition_framework",
    "submit_product_vision",
    "get_vision_details",
    # Strategic Foundation - Pillars
    "get_pillar_definition_framework",
    "submit_strategic_pillar",
    "query_strategic_pillars",
    "delete_strategic_pillar",
    # Strategic Foundation - Outcomes
    "get_outcome_definition_framework",
    "submit_product_outcome",
    "query_product_outcomes",
    "delete_product_outcome",
    # Roadmap Themes
    "get_theme_exploration_framework",
    "submit_roadmap_theme",
    "query_roadmap_themes",
    "delete_roadmap_theme",
    "get_prioritization_context",
    "set_theme_priority",
    "organize_roadmap",
    "connect_theme_to_outcomes",
    # Narrative Layer - Heroes
    "get_hero_definition_framework",
    "submit_hero",
    "query_heroes",
    "delete_hero",
    # Narrative Layer - Villains
    "get_villain_definition_framework",
    "submit_villain",
    "query_villains",
    "delete_villain",
    # Narrative Layer - Conflicts
    "get_conflict_creation_framework",
    "submit_conflict",
    "query_conflicts",
    "delete_conflict",
    # Narrative Recap
    "get_recent_turning_points",
    "generate_previously_on",
    "get_story_bible",
    # Strategic Initiatives
    "get_strategic_initiative_definition_framework",
    "submit_strategic_initiative",
    "query_strategic_initiatives",
    "delete_strategic_initiative",
    # Utility Tools
    "review_strategic_foundation",
    "connect_outcome_to_pillars",
]
