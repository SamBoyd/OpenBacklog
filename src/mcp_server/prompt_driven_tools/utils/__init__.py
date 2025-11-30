"""Shared utilities for prompt-driven MCP tools."""

from src.mcp_server.prompt_driven_tools.utils.alignment_scorer import (
    calculate_alignment_score,
    get_alignment_recommendation,
    identify_alignment_issues,
)
from src.mcp_server.prompt_driven_tools.utils.auth import (
    get_user_id_from_request,
    get_workspace_id_from_request,
    get_workspace_id_from_user_id,
)
from src.mcp_server.prompt_driven_tools.utils.draft_builder import (
    build_draft_hero_data,
    build_draft_outcome_data,
    build_draft_pillar_data,
    build_draft_strategic_initiative_data,
    build_draft_theme_data,
    build_draft_villain_data,
    build_draft_vision_data,
)
from src.mcp_server.prompt_driven_tools.utils.framework_builder import FrameworkBuilder
from src.mcp_server.prompt_driven_tools.utils.response_builder import (
    build_draft_response,
    build_error_response,
    build_success_response,
)
from src.mcp_server.prompt_driven_tools.utils.serializers import (
    serialize_conflict,
    serialize_datetime,
    serialize_hero,
    serialize_outcome,
    serialize_pillar,
    serialize_strategic_foundation,
    serialize_strategic_initiative,
    serialize_theme,
    serialize_turning_point,
    serialize_uuid,
    serialize_villain,
    serialize_vision,
)
from src.mcp_server.prompt_driven_tools.utils.validation_runner import (
    validate_hero_constraints,
    validate_outcome_constraints,
    validate_pillar_constraints,
    validate_strategic_initiative_constraints,
    validate_theme_constraints,
    validate_villain_constraints,
    validate_vision_constraints,
)
from src.mcp_server.prompt_driven_tools.utils.validators import (
    validate_time_horizon,
    validate_uuid,
)

__all__ = [
    "FrameworkBuilder",
    "build_success_response",
    "build_draft_response",
    "build_error_response",
    "build_draft_vision_data",
    "build_draft_pillar_data",
    "build_draft_outcome_data",
    "build_draft_hero_data",
    "build_draft_villain_data",
    "build_draft_theme_data",
    "build_draft_strategic_initiative_data",
    "validate_vision_constraints",
    "validate_pillar_constraints",
    "validate_outcome_constraints",
    "validate_hero_constraints",
    "validate_villain_constraints",
    "validate_theme_constraints",
    "validate_strategic_initiative_constraints",
    "validate_uuid",
    "validate_time_horizon",
    "calculate_alignment_score",
    "identify_alignment_issues",
    "get_alignment_recommendation",
    "get_user_id_from_request",
    "get_workspace_id_from_request",
    "get_workspace_id_from_user_id",
    "serialize_datetime",
    "serialize_uuid",
    "serialize_vision",
    "serialize_pillar",
    "serialize_outcome",
    "serialize_theme",
    "serialize_strategic_initiative",
    "serialize_strategic_foundation",
    "serialize_hero",
    "serialize_villain",
    "serialize_conflict",
    "serialize_turning_point",
]
