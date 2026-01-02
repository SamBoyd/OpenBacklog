"""Unified framework tool for all entity types.

This module provides a single parameterized tool that replaces 8 separate
framework tools, reducing token consumption and simplifying the API surface.
"""

import logging
from typing import Any, Dict, Literal

from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.narrative_conflicts import (
    get_conflict_creation_framework,
)
from src.mcp_server.prompt_driven_tools.narrative_heroes import (
    get_hero_definition_framework,
)
from src.mcp_server.prompt_driven_tools.narrative_villains import (
    get_villain_definition_framework,
)
from src.mcp_server.prompt_driven_tools.product_outcomes import (
    get_outcome_definition_framework,
)
from src.mcp_server.prompt_driven_tools.product_vision import (
    get_vision_definition_framework,
)
from src.mcp_server.prompt_driven_tools.roadmap_themes import (
    get_theme_exploration_framework,
)
from src.mcp_server.prompt_driven_tools.strategic_initiatives import (
    get_strategic_initiative_definition_framework,
)
from src.mcp_server.prompt_driven_tools.strategic_pillars import (
    get_pillar_definition_framework,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EntityType = Literal[
    "hero", "villain", "conflict", "vision", "pillar", "outcome", "theme", "initiative"
]


@mcp.tool()
async def get_framework(entity_type: EntityType) -> Dict[str, Any]:
    """Get creation & update framework for any entity type.

    Returns rich context with purpose, criteria, examples, questions, etc for provided entity type

    Args:
        entity_type: Type of entity to get framework for. One of:
            - hero: User persona definition
            - villain: Problem/obstacle definition
            - conflict: Conflict between hero and villain
            - vision: Product vision statement
            - pillar: Strategic pillar definition
            - outcome: Product outcome definition
            - theme: Roadmap theme exploration
            - initiative: Strategic initiative definition

    Returns:
        Framework dictionary with guidance for defining the entity type
    """
    logger.info(f"Getting framework for entity type: {entity_type}")

    router = {
        "hero": get_hero_definition_framework,
        "villain": get_villain_definition_framework,
        "conflict": get_conflict_creation_framework,
        "vision": get_vision_definition_framework,
        "pillar": get_pillar_definition_framework,
        "outcome": get_outcome_definition_framework,
        "theme": get_theme_exploration_framework,
        "initiative": get_strategic_initiative_definition_framework,
    }

    framework_func = router.get(entity_type)
    if not framework_func:
        # This should not happen with Literal type, but handle for safety
        raise ValueError(f"Unknown entity type: {entity_type}")

    return await framework_func()
