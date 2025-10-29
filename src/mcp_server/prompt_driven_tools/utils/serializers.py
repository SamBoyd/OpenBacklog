"""Serialization utilities for prompt-driven tools.

Provides serialization functions for strategic planning entities and
specialized serializers for review/analysis tools.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Re-export common serializers from product_strategy_tools
from src.mcp_server.product_strategy_tools.utils import (
    serialize_datetime,
    serialize_outcome,
    serialize_pillar,
    serialize_theme,
    serialize_uuid,
    serialize_vision,
)

__all__ = [
    "serialize_datetime",
    "serialize_uuid",
    "serialize_vision",
    "serialize_pillar",
    "serialize_outcome",
    "serialize_theme",
    "serialize_strategic_foundation",
]


def serialize_strategic_foundation(
    vision: Optional[Any],
    pillars: List[Any],
    outcomes: List[Any],
) -> Dict[str, Any]:
    """Serialize complete strategic foundation for review/analysis.

    Args:
        vision: ProductVision instance or None
        pillars: List of StrategicPillar instances
        outcomes: List of ProductOutcome instances

    Returns:
        Dict with structured foundation data including health analysis
    """
    # Serialize individual components
    vision_data = serialize_vision(vision) if vision else None
    pillar_data = [serialize_pillar(p) for p in pillars]
    outcome_data = [serialize_outcome(o) for o in outcomes]

    # Calculate health metrics
    has_vision = vision is not None
    pillar_count = len(pillars)
    outcome_count = len(outcomes)

    # Identify gaps
    gaps = []
    if not has_vision:
        gaps.append(
            "No product vision defined - start with get_vision_definition_framework()"
        )
    if pillar_count < 2:
        gaps.append(
            f"Only {pillar_count} strategic pillar(s) - recommend 2-5 pillars for clear differentiation"
        )
    if pillar_count > 5:
        gaps.append(
            f"{pillar_count} strategic pillars may be too many - consider consolidating for focus"
        )
    if outcome_count == 0:
        gaps.append("No product outcomes defined - outcomes measure strategic progress")

    # Check for unlinked outcomes (outcomes not linked to any pillar)
    unlinked_outcomes = [o for o in outcomes if not o.pillars or len(o.pillars) == 0]
    if unlinked_outcomes:
        gaps.append(
            f"{len(unlinked_outcomes)} outcome(s) not linked to pillars - outcomes should validate strategy"
        )

    # Check for pillars without outcomes
    pillars_without_outcomes = [
        p for p in pillars if not p.outcomes or len(p.outcomes) == 0
    ]
    if pillars_without_outcomes:
        pillar_names = ", ".join([p.name for p in pillars_without_outcomes])
        gaps.append(
            f"Pillars without outcomes: {pillar_names} - each pillar should have measurable outcomes"
        )

    # Determine overall health status
    if has_vision and pillar_count >= 2 and outcome_count > 0 and not unlinked_outcomes:
        status = "healthy"
    elif has_vision or pillar_count > 0 or outcome_count > 0:
        status = "partial"
    else:
        status = "missing"

    # Build next steps recommendations
    next_steps = []
    if not has_vision:
        next_steps.append(
            "Define your product vision using get_vision_definition_framework()"
        )
    elif pillar_count < 2:
        next_steps.append(
            "Add strategic pillars (2-5 recommended) using get_pillar_definition_framework()"
        )
    elif outcome_count == 0:
        next_steps.append(
            "Define product outcomes using get_outcome_definition_framework()"
        )
    elif unlinked_outcomes:
        next_steps.append(
            "Link outcomes to pillars using connect_outcome_to_pillars() to validate strategy"
        )
    elif pillars_without_outcomes:
        next_steps.append(
            "Define outcomes for remaining pillars to measure strategic progress"
        )
    else:
        next_steps.append(
            "Foundation looks healthy! Consider defining roadmap themes with get_theme_exploration_framework()"
        )

    return {
        "status": status,
        "vision": (
            {"exists": has_vision, "data": vision_data}
            if has_vision
            else {"exists": False}
        ),
        "pillars": {
            "count": pillar_count,
            "min_recommended": 2,
            "max_recommended": 5,
            "items": pillar_data,
        },
        "outcomes": {
            "count": outcome_count,
            "unlinked_count": len(unlinked_outcomes),
            "items": outcome_data,
        },
        "gaps": gaps,
        "next_steps": next_steps,
        "summary": _generate_foundation_summary(
            has_vision, pillar_count, outcome_count, status
        ),
    }


def _generate_foundation_summary(
    has_vision: bool, pillar_count: int, outcome_count: int, status: str
) -> str:
    """Generate human-readable summary of strategic foundation health.

    Args:
        has_vision: Whether vision exists
        pillar_count: Number of strategic pillars
        outcome_count: Number of product outcomes
        status: Overall health status

    Returns:
        Summary string
    """
    if status == "healthy":
        return (
            f"Strategic foundation is healthy: Vision defined, {pillar_count} pillars, "
            f"{outcome_count} outcomes with clear strategic alignment."
        )
    elif status == "partial":
        parts = []
        if has_vision:
            parts.append("vision defined")
        if pillar_count > 0:
            parts.append(f"{pillar_count} pillar(s)")
        if outcome_count > 0:
            parts.append(f"{outcome_count} outcome(s)")

        present = ", ".join(parts) if parts else "no elements"
        return f"Strategic foundation is partially complete: {present}. Review gaps for next steps."
    else:
        return "Strategic foundation is missing. Start by defining your product vision."
