"""Shared utilities for prompt-driven MCP tools."""

from src.mcp_server.prompt_driven_tools.utils.alignment_scorer import (
    calculate_alignment_score,
    get_alignment_recommendation,
    identify_alignment_issues,
)
from src.mcp_server.prompt_driven_tools.utils.auth import get_user_id_from_request
from src.mcp_server.prompt_driven_tools.utils.framework_builder import FrameworkBuilder
from src.mcp_server.prompt_driven_tools.utils.response_builder import (
    build_error_response,
    build_success_response,
)
from src.mcp_server.prompt_driven_tools.utils.serializers import (
    serialize_datetime,
    serialize_outcome,
    serialize_pillar,
    serialize_strategic_foundation,
    serialize_strategic_initiative,
    serialize_theme,
    serialize_uuid,
    serialize_vision,
)
from src.mcp_server.prompt_driven_tools.utils.validators import (
    validate_time_horizon,
    validate_uuid,
)

__all__ = [
    "FrameworkBuilder",
    "build_success_response",
    "build_error_response",
    "validate_uuid",
    "validate_time_horizon",
    "calculate_alignment_score",
    "identify_alignment_issues",
    "get_alignment_recommendation",
    "get_user_id_from_request",
    "serialize_datetime",
    "serialize_uuid",
    "serialize_vision",
    "serialize_pillar",
    "serialize_outcome",
    "serialize_theme",
    "serialize_strategic_initiative",
    "serialize_strategic_foundation",
]
