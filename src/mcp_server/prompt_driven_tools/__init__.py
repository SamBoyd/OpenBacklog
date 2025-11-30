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
from src.mcp_server.prompt_driven_tools.roadmap_themes import *
from src.mcp_server.prompt_driven_tools.strategic_foundation import *
from src.mcp_server.prompt_driven_tools.strategic_initiatives import *
from src.mcp_server.prompt_driven_tools.utilities import *

__all__ = [
    # Strategic Foundation (Phase 1)
    "get_vision_definition_framework",
    "submit_product_vision",
    "get_pillar_definition_framework",
    "submit_strategic_pillar",
    "get_outcome_definition_framework",
    "submit_product_outcome",
    # Roadmap Themes (Phase 2)
    "get_theme_exploration_framework",
    "submit_roadmap_theme",
    "get_prioritization_context",
    "prioritize_workstream",
    "deprioritize_workstream",
    "organize_roadmap",
    "connect_theme_to_outcomes",
    "link_theme_to_hero",
    "link_theme_to_villain",
    # Narrative Layer (Phase 1)
    "get_hero_definition_framework",
    "submit_hero",
    "get_heroes",
    "get_hero_details",
    "get_villain_definition_framework",
    "submit_villain",
    "get_villains",
    "mark_villain_defeated",
    "get_conflict_creation_framework",
    "create_conflict",
    "get_conflicts",
    "mark_conflict_resolved",
    "get_recent_turning_points",
    "generate_previously_on",
    "get_story_bible",
    # Strategic Initiatives (narrative-connected initiatives)
    "get_strategic_initiative_definition_framework",
    "submit_strategic_initiative",
    "get_strategic_initiatives",
    "get_strategic_initiative",
    # Utility Tools (Phase 3)
    "review_strategic_foundation",
    "connect_outcome_to_pillars",
]
