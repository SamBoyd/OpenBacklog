"""Single-turn utility tools for prompt-driven collaboration (Phase 3).

These tools handle simple operations that don't require iterative refinement:
- Reviewing foundation health
- Linking outcomes to pillars

Note: Phase 2 already implemented roadmap-related utilities (deprioritize_workstream,
organize_roadmap, connect_theme_to_outcomes) in roadmap_themes.py.
"""

from typing import Any, Dict, List

from src.db import SessionLocal
from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.utils import (
    build_error_response,
    build_success_response,
    get_user_id_from_request,
    get_workspace_id_from_request,
    serialize_outcome,
    serialize_strategic_foundation,
    validate_uuid,
)
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.exceptions import DomainException


@mcp.tool()
async def review_strategic_foundation() -> Dict[str, Any]:
    """Get health check and gap analysis of strategic foundation.

    Analyzes the completeness and quality of workspace strategic foundation
    (vision, pillars, outcomes) and provides actionable recommendations.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Dict containing:
        - status: "healthy" | "partial" | "missing"
        - vision: Vision status and data
        - pillars: Pillar count and details
        - outcomes: Outcome count and linkage status
        - gaps: List of identified issues
        - next_steps: Recommended actions
        - summary: Human-readable health summary

    Example:
        >>> result = await review_strategic_foundation()
        >>> print(result["status"])  # "partial"
        >>> print(result["gaps"])    # ["Only 1 strategic pillar..."]
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # Fetch strategic foundation components
        vision = strategic_controller.get_workspace_vision(workspace_uuid, session)
        pillars = strategic_controller.get_strategic_pillars(workspace_uuid, session)
        outcomes = strategic_controller.get_product_outcomes(workspace_uuid, session)

        # Serialize with health analysis
        foundation_data = serialize_strategic_foundation(vision, pillars, outcomes)

        return {
            "type": "strategic_foundation_review",
            **foundation_data,
        }

    except ValueError as e:
        return build_error_response("strategic_foundation_review", str(e))
    finally:
        session.close()


@mcp.tool()
async def connect_outcome_to_pillars(
    outcome_id: str,
    pillar_ids: List[str],
) -> Dict[str, Any]:
    """Link a product outcome to strategic pillars.

    Outcomes should be linked to at least one pillar to validate that they
    support your strategic differentiation.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        outcome_id: UUID of the outcome to link
        pillar_ids: List of pillar UUIDs to link to this outcome

    Returns:
        Success response with updated outcome data

    Example:
        >>> result = await connect_outcome_to_pillars(
        ...     outcome_id="outcome-uuid",
        ...     pillar_ids=["pillar1-uuid", "pillar2-uuid"]
        ... )
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        outcome_uuid = validate_uuid(outcome_id, "outcome_id")
        pillar_uuids = [
            validate_uuid(pid, f"pillar_ids[{i}]") for i, pid in enumerate(pillar_ids)
        ]

        # Fetch the outcome
        outcomes = strategic_controller.get_product_outcomes(workspace_uuid, session)
        outcome = next((o for o in outcomes if o.id == outcome_uuid), None)

        if not outcome:
            return build_error_response(
                "outcome_pillar_link",
                f"Product outcome {outcome_id} not found in workspace {workspace_uuid}",
            )

        # Link to pillars via controller
        from src.strategic_planning.services.event_publisher import EventPublisher

        publisher = EventPublisher(session)
        user_id = get_user_id_from_request()
        outcome.link_to_pillars(pillar_uuids, user_id, session, publisher)

        session.commit()
        session.refresh(outcome)

        return build_success_response(
            entity_type="outcome_pillar_link",
            message=f"Successfully linked outcome '{outcome.name}' to {len(pillar_uuids)} pillar(s)",
            data={"outcome": serialize_outcome(outcome)},
            next_steps=[
                "Outcome now validates strategic pillars through measurable results",
                "Consider defining roadmap themes to achieve this outcome",
            ],
        )

    except DomainException as e:
        return build_error_response("outcome_pillar_link", str(e))
    except ValueError as e:
        return build_error_response("outcome_pillar_link", f"Invalid input: {str(e)}")
    finally:
        session.close()


# Note: The following utility tools were implemented in Phase 2 (roadmap_themes.py):
# - connect_theme_to_outcomes
# - deprioritize_workstream
# - organize_roadmap
#
# Phase 3 adds the new utility tools above: review_strategic_foundation and connect_outcome_to_pillars
