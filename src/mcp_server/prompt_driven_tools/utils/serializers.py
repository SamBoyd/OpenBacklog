"""Serialization utilities for prompt-driven tools.

Provides serialization functions for strategic planning entities and
specialized serializers for review/analysis tools.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.initiative_management.aggregates.strategic_initiative import (
    StrategicInitiative,
)
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar

# ============================================================================
# Basic Serialization Helpers
# ============================================================================


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string."""
    return dt.isoformat() if dt else None


def serialize_uuid(u: Optional[uuid.UUID]) -> Optional[str]:
    """Convert UUID to string."""
    return str(u) if u else None


# ============================================================================
# Entity Serializers
# ============================================================================


def serialize_vision(vision: ProductVision) -> Dict[str, Any]:
    """Serialize ProductVision to JSON-serializable dict."""
    return {
        "id": serialize_uuid(vision.id),
        "workspace_id": serialize_uuid(vision.workspace_id),
        "vision_text": vision.vision_text,
        "created_at": serialize_datetime(vision.created_at),
        "updated_at": serialize_datetime(vision.updated_at),
    }


def serialize_pillar(pillar: StrategicPillar) -> Dict[str, Any]:
    """Serialize StrategicPillar to JSON-serializable dict."""
    return {
        "id": serialize_uuid(pillar.id),
        "workspace_id": serialize_uuid(pillar.workspace_id),
        "name": pillar.name,
        "description": pillar.description,
        "anti_strategy": pillar.anti_strategy,
        "display_order": pillar.display_order,
        "outcome_ids": [serialize_uuid(outcome.id) for outcome in pillar.outcomes],
        "created_at": serialize_datetime(pillar.created_at),
        "updated_at": serialize_datetime(pillar.updated_at),
    }


def serialize_outcome(outcome: ProductOutcome) -> Dict[str, Any]:
    """Serialize ProductOutcome to JSON-serializable dict."""
    return {
        "id": serialize_uuid(outcome.id),
        "workspace_id": serialize_uuid(outcome.workspace_id),
        "name": outcome.name,
        "description": outcome.description,
        "metrics": outcome.metrics,
        "time_horizon_months": outcome.time_horizon_months,
        "display_order": outcome.display_order,
        "pillar_ids": [serialize_uuid(pillar.id) for pillar in outcome.pillars],
        "created_at": serialize_datetime(outcome.created_at),
        "updated_at": serialize_datetime(outcome.updated_at),
    }


def serialize_theme(theme: RoadmapTheme) -> Dict[str, Any]:
    """Serialize RoadmapTheme to JSON-serializable dict."""
    return {
        "id": serialize_uuid(theme.id),
        "workspace_id": serialize_uuid(theme.workspace_id),
        "name": theme.name,
        "problem_statement": theme.problem_statement,
        "hypothesis": theme.hypothesis,
        "indicative_metrics": theme.indicative_metrics,
        "time_horizon_months": theme.time_horizon_months,
        "display_order": theme.display_order,
        "outcome_ids": [serialize_uuid(outcome.id) for outcome in theme.outcomes],
        "created_at": serialize_datetime(theme.created_at),
        "updated_at": serialize_datetime(theme.updated_at),
    }


def serialize_strategic_initiative(si: StrategicInitiative) -> Dict[str, Any]:
    """Serialize StrategicInitiative to JSON-serializable dict."""
    return {
        "id": serialize_uuid(si.id),
        "initiative_id": serialize_uuid(si.initiative_id),
        "workspace_id": serialize_uuid(si.workspace_id),
        "pillar_id": serialize_uuid(si.pillar_id),
        "theme_id": serialize_uuid(si.theme_id),
        "user_need": si.user_need,
        "connection_to_vision": si.connection_to_vision,
        "success_criteria": si.success_criteria,
        "out_of_scope": si.out_of_scope,
        "created_at": serialize_datetime(si.created_at),
        "updated_at": serialize_datetime(si.updated_at),
    }


__all__ = [
    "serialize_datetime",
    "serialize_uuid",
    "serialize_vision",
    "serialize_pillar",
    "serialize_outcome",
    "serialize_theme",
    "serialize_strategic_initiative",
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
