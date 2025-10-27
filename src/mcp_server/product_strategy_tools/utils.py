"""MCP tools for product strategy operations.

This module provides MCP tools for managing product strategy entities:
- Product Vision (workspace vision statements)
- Strategic Pillars (ways to win)
- Product Outcomes (measurable objectives)
- Roadmap Themes (tactical bets)
- Strategic Initiatives (strategic context for initiatives)

All tools call controller functions directly with database sessions.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request

from src.initiative_management.aggregates.strategic_initiative import (
    StrategicInitiative,
)
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions for Serialization
# ============================================================================


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string."""
    return dt.isoformat() if dt else None


def serialize_uuid(u: Optional[uuid.UUID]) -> Optional[str]:
    """Convert UUID to string."""
    return str(u) if u else None


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


def get_user_id_from_request() -> uuid.UUID:
    """Extract user ID from request headers.

    For now, this returns a dummy UUID. In production, this should
    extract and validate the user ID from the JWT token.
    """
    # TODO: Extract actual user ID from JWT in Authorization header
    # For now, we'll use a placeholder that matches the test user
    request: Request = get_http_request()
    user_id_header = request.headers.get("X-User-Id")
    if user_id_header:
        return uuid.UUID(user_id_header)

    # Fallback for testing
    return uuid.uuid4()
