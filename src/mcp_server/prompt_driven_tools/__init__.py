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
    "get_vision",
    # Strategic Foundation - Pillars
    "get_pillar_definition_framework",
    "submit_strategic_pillar",
    "get_strategic_pillars",
    "get_strategic_pillar",
    "update_strategic_pillar",
    "delete_strategic_pillar",
    # Strategic Foundation - Outcomes
    "get_outcome_definition_framework",
    "submit_product_outcome",
    "get_product_outcomes",
    "update_product_outcome",
    "delete_product_outcome",
    # Roadmap Themes
    "get_theme_exploration_framework",
    "submit_roadmap_theme",
    "get_roadmap_themes",
    "update_roadmap_theme",
    "delete_roadmap_theme",
    "get_prioritization_context",
    "prioritize_workstream",
    "deprioritize_workstream",
    "organize_roadmap",
    "connect_theme_to_outcomes",
    "link_theme_to_hero",
    "link_theme_to_villain",
    # Narrative Layer - Heroes
    "get_hero_definition_framework",
    "submit_hero",
    "get_heroes",
    "get_hero_details",
    "update_hero",
    "delete_hero",
    # Narrative Layer - Villains
    "get_villain_definition_framework",
    "submit_villain",
    "get_villains",
    "get_villain_details",
    "update_villain",
    "delete_villain",
    "mark_villain_defeated",
    # Narrative Layer - Conflicts
    "get_conflict_creation_framework",
    "create_conflict",
    "get_conflicts",
    "update_conflict",
    "delete_conflict",
    "mark_conflict_resolved",
    # Narrative Recap
    "get_recent_turning_points",
    "generate_previously_on",
    "get_story_bible",
    # Strategic Initiatives
    "get_strategic_initiative_definition_framework",
    "submit_strategic_initiative",
    "get_strategic_initiatives",
    "get_active_strategic_initiatives",
    "search_strategic_initiatives",
    "get_strategic_initiative",
    "update_strategic_initiative",
    "delete_strategic_initiative",
    # Utility Tools
    "review_strategic_foundation",
    "connect_outcome_to_pillars",
]
