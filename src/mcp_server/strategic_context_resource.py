"""MCP tool for strategic context summary.

This module provides a tool that returns a comprehensive, denormalized
summary of the OpenBacklog strategic foundation rendered as markdown.

The tool fetches all strategic entities (vision, pillars, outcomes,
themes, heroes, villains) and renders them using a Jinja2 template,
providing complete strategic context in a single request.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

from src.db import SessionLocal
from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.utils import (
    get_workspace_id_from_request,
    serialize_hero,
    serialize_outcome,
    serialize_pillar,
    serialize_theme,
    serialize_villain,
)
from src.narrative.aggregates.villain import Villain
from src.narrative.services.hero_service import HeroService
from src.narrative.services.villain_service import VillainService
from src.roadmap_intelligence import controller as roadmap_controller
from src.roadmap_intelligence.services.prioritization_service import (
    PrioritizationService,
)
from src.strategic_planning import ProductOutcome, RoadmapTheme
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def _adapt_outcome_for_template(outcome: ProductOutcome) -> Dict[str, Any]:
    """Adapt outcome serialization for Jinja template.

    Uses the shared serializer and adds template-specific fields.
    """
    data = serialize_outcome(outcome, include_connections=False)
    data["pillar_names"] = [p.name for p in outcome.pillars] if outcome.pillars else []
    return data


def _adapt_theme_for_template(
    theme: RoadmapTheme,
    prioritized_theme_ids: List[str],
) -> Dict[str, Any]:
    """Adapt theme serialization for Jinja template.

    Uses the shared serializer and adds template-specific fields
    including prioritization status.

    Args:
        theme: The RoadmapTheme to serialize
        prioritized_theme_ids: List of theme ID strings in priority order
    """
    data = serialize_theme(theme, include_connections=True)
    theme_id_str = str(theme.id)
    if theme_id_str in prioritized_theme_ids:
        data["is_prioritized"] = True
        data["priority_order"] = prioritized_theme_ids.index(theme_id_str)
    else:
        data["is_prioritized"] = False
        data["priority_order"] = None

    return data


def _adapt_villain_for_template(villain: Villain) -> Dict[str, Any]:
    """Adapt villain serialization for Jinja template.

    Uses the shared serializer and ensures villain_type is a string.
    """
    data = serialize_villain(villain, include_connections=False)
    if hasattr(data.get("villain_type"), "value"):
        data["villain_type"] = data["villain_type"].value
    elif data.get("villain_type") is None:
        data["villain_type"] = "OTHER"
    return data


@mcp.tool()
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
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(f"Getting strategic context summary for workspace {workspace_uuid}")

        vision = strategic_controller.get_workspace_vision(workspace_uuid, session)
        pillars = strategic_controller.get_strategic_pillars(workspace_uuid, session)
        outcomes = strategic_controller.get_product_outcomes(workspace_uuid, session)
        themes = roadmap_controller.get_roadmap_themes(workspace_uuid, session)

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        villain_service = VillainService(session, publisher)

        heroes = hero_service.get_heroes_for_workspace(workspace_uuid)
        villains = villain_service.get_villains_for_workspace(workspace_uuid)

        prioritization_service = PrioritizationService(session, publisher)
        prioritized_roadmap = prioritization_service.get_prioritized_roadmap(
            workspace_uuid
        )
        prioritized_theme_ids = (
            [str(tid) for tid in prioritized_roadmap.get_prioritized_themes()]
            if prioritized_roadmap
            else []
        )

        serialized_pillars = [
            serialize_pillar(p, include_connections=False) for p in pillars
        ]
        serialized_outcomes = [_adapt_outcome_for_template(o) for o in outcomes]
        serialized_themes = [
            _adapt_theme_for_template(t, prioritized_theme_ids) for t in themes
        ]
        serialized_heroes = [
            serialize_hero(h, include_connections=False) for h in heroes
        ]
        serialized_villains = [_adapt_villain_for_template(v) for v in villains]

        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=False,
        )
        template = env.get_template("prompts/strategic_context_summary.jinja")

        rendered = template.render(
            vision=vision,
            pillars=serialized_pillars,
            outcomes=serialized_outcomes,
            themes=serialized_themes,
            heroes=serialized_heroes,
            villains=serialized_villains,
        )

        return rendered

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.exception(f"Error getting strategic context: {e}")
        return f"Error: Unable to retrieve strategic context. {str(e)}"
    finally:
        session.close()
