"""Prompt-driven MCP tools for strategic foundation.

This module provides framework-based tools for defining strategic foundation
elements (vision, pillars, outcomes) through conversational refinement rather
than rigid forms.

Pattern: Get Framework → Claude + User Collaborate → Submit Result
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from src.db import SessionLocal
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.utils import (
    FrameworkBuilder,
    build_draft_outcome_data,
    build_draft_pillar_data,
    build_draft_response,
    build_draft_vision_data,
    build_error_response,
    build_success_response,
    get_workspace_id_from_request,
    serialize_outcome,
    serialize_pillar,
    serialize_vision,
    validate_outcome_constraints,
    validate_pillar_constraints,
    validate_uuid,
    validate_vision_constraints,
)
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Vision Workflow
# ============================================================================


@mcp.tool()
async def get_vision_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a product vision.

    Returns rich context to help Claude Code guide the user through
    defining a high-quality product vision through collaborative refinement.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary with purpose, criteria, examples, questions,
        anti-patterns, current state, and coaching tips

    Example:
        >>> framework = await get_vision_definition_framework()
        >>> # Claude Code uses framework to guide user through refinement
        >>> # User and Claude iterate until vision is outcome-focused
        >>> await submit_product_vision(refined_vision)
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting vision definition framework for workspace {workspace_uuid}"
        )

        # Get current vision if exists
        current_vision = strategic_controller.get_workspace_vision(
            workspace_uuid, session
        )

        # Build framework using builder pattern
        builder = FrameworkBuilder("vision")

        builder.set_purpose("Define the change you want to make in the world")

        builder.add_criteria(
            [
                "Outcome-focused, not solution-focused",
                "Describes change in user's world",
                "Clear and inspiring",
                "1-2 sentences recommended (no character limit)",
            ]
        )

        builder.add_example(
            text="Enable developers to manage tasks without leaving their IDE",
            why_good="Focuses on user outcome (no context-switching), not features",
        )

        builder.add_example(
            text="Help small businesses access enterprise-grade analytics",
            why_good="Clear outcome (SMBs get capabilities they lack), aspirational",
        )

        builder.add_example(
            text="Allow content creators to publish 10x faster",
            why_good="Measurable change (10x), clear beneficiary (creators)",
        )

        builder.add_questions(
            [
                "What problem are you solving?",
                "What changes for users because your product exists?",
                "What do users achieve that they couldn't before?",
                "If your product disappeared tomorrow, what would users lose?",
            ]
        )

        builder.add_anti_pattern(
            example="Build the best AI tool",
            why_bad="Solution-focused, not outcome-focused",
            better="Enable X users to achieve Y without Z overhead",
        )

        builder.add_anti_pattern(
            example="Create a platform for task management",
            why_bad="Describes what you're building, not why",
            better="Help teams ship faster through better coordination",
        )

        builder.add_coaching_tips(
            [
                "Start broad, then narrow to specific user outcome",
                "Avoid technical jargon or feature lists",
                "Think: 'So that...' - what does your solution enable?",
                "Test: Could this vision apply to a different solution? (If yes, too vague)",
            ]
        )

        # Set current state
        if current_vision:
            builder.set_current_state(
                {
                    "has_vision": True,
                    "current_vision": current_vision.vision_text,
                    "created_at": (
                        current_vision.created_at.isoformat()
                        if current_vision.created_at
                        else None
                    ),
                }
            )
        else:
            builder.set_current_state({"has_vision": False, "current_vision": None})

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("vision", str(e))
    except Exception as e:
        logger.exception(f"Error getting vision framework: {e}")
        return build_error_response("vision", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_product_vision(
    vision_text: str, draft_mode: bool = True
) -> Dict[str, Any]:
    """Submit a refined product vision after collaborative definition.

    Called only when Claude Code and user have crafted a high-quality
    vision through dialogue using the framework guidance.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        vision_text: Refined vision statement (non-empty text)
        draft_mode: If True, validate without persisting; if False, persist to database (default: True)

    Returns:
        Draft response with validation results if draft_mode=True,
        or success response with created/updated vision if draft_mode=False

    Example:
        >>> # Validate first (default)
        >>> draft = await submit_product_vision(
        ...     vision_text="Enable developers to manage tasks without leaving their IDE"
        ... )
        >>> # Then persist after user approval
        >>> result = await submit_product_vision(
        ...     vision_text="Enable developers to manage tasks without leaving their IDE",
        ...     draft_mode=False
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(
            f"Submitting product vision for workspace {workspace_id} (draft_mode={draft_mode})"
        )

        # DRAFT MODE: Validate without persisting
        if draft_mode:
            validate_vision_constraints(vision_text)

            # Get existing vision to use its ID if it exists
            existing_vision = strategic_controller.get_workspace_vision(
                uuid.UUID(workspace_id), session
            )
            existing_vision_id = existing_vision.id if existing_vision else None

            draft_data = build_draft_vision_data(
                workspace_id=uuid.UUID(workspace_id),
                vision_text=vision_text,
                existing_vision_id=existing_vision_id,
            )

            return build_draft_response(
                entity_type="product_vision",
                message=f"Draft vision validated successfully",
                data=draft_data,
                next_steps=[
                    "Review vision statement with user",
                    "Confirm it focuses on user outcome, not features",
                    "If approved, call submit_product_vision() with draft_mode=False",
                    "Consider defining strategic pillars next",
                ],
            )

        # NORMAL MODE: Create/update and persist vision
        vision = strategic_controller.upsert_workspace_vision(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            vision_text=vision_text,
            session=session,
        )

        # Build success response with next steps
        next_steps = [
            "Define 2-5 strategic pillars that explain how you'll differentiate",
            "Each pillar should have a clear anti-strategy (what you WON'T do)",
            "Use get_pillar_definition_framework() to start defining pillars",
        ]

        return build_success_response(
            entity_type="vision",
            message="Vision created/updated successfully",
            data=serialize_vision(vision),
            next_steps=next_steps,
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("vision", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("vision", str(e))
    except MCPContextError as e:
        return build_error_response("vision", str(e))
    except Exception as e:
        logger.exception(f"Error submitting vision: {e}")
        return build_error_response("vision", f"Server error: {str(e)}")
    finally:
        session.close()


# ============================================================================
# Pillar Workflow
# ============================================================================


@mcp.tool()
async def get_pillar_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a strategic pillar.

    Returns rich context to help Claude Code guide the user through
    defining a high-quality strategic pillar through collaborative refinement.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary with purpose, criteria, examples, questions,
        anti-patterns, current state, and coaching tips

    Example:
        >>> framework = await get_pillar_definition_framework()
        >>> # Claude Code uses framework to guide user through refinement
        >>> await submit_strategic_pillar(name, description)
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting pillar definition framework for workspace {workspace_uuid}"
        )

        # Get current pillars
        current_pillars = strategic_controller.get_strategic_pillars(
            workspace_uuid, session
        )

        # Build framework
        builder = FrameworkBuilder("pillar")

        builder.set_purpose("Define how you'll differentiate from competitors")

        builder.add_criteria(
            [
                "Clear, unique differentiation strategy",
                "Has explicit anti-strategy (what you WON'T do)",
                "Trade-offs are intentional and clear",
                "Aligns with overall product vision",
            ]
        )

        builder.add_example(
            text="Deep IDE Integration",
            why_good="Clear focus on IDE, explicit trade-offs on other platforms",
            description="**Strategy**: Provide seamless experience within developer's existing workflow. **Anti-Strategy**: No web-first experience, no mobile app, no Slack/Teams bots.",
        )

        builder.add_example(
            text="Developer-First UX",
            why_good="Prioritizes user over buyer, clear scope exclusions",
            description="**Strategy**: Optimize for individual developer productivity, not team admin. **Anti-Strategy**: No enterprise admin features, no complex permissions, no audit logs.",
        )

        builder.add_questions(
            [
                "What makes your approach unique vs competitors?",
                "What will you explicitly NOT do to maintain this focus?",
                "What are you trading off by choosing this pillar?",
                "If you had to pick only 3 things to be world-class at, is this one of them?",
            ]
        )

        builder.add_anti_pattern(
            example="Innovation",
            why_bad="Generic, could apply to anyone",
            better="Fast Experimentation (ship MVPs in days, not months)",
        )

        builder.add_anti_pattern(
            example="Quality - We build high-quality products",
            why_bad="No clear differentiation, everyone claims quality",
            better="Enterprise-Grade Reliability (99.99% uptime SLA)",
        )

        builder.add_coaching_tips(
            [
                "Anti-strategy is just as important as strategy",
                "Good anti-strategy feels uncomfortable (real trade-offs)",
                "Test: Would competitors make the same trade-offs? (If yes, not differentiating)",
            ]
        )

        # Set current state with pillar limit info
        current_count = len(current_pillars)
        max_pillars = 5
        remaining = max_pillars - current_count

        builder.set_current_state(
            {
                "current_pillars": [
                    {
                        "id": str(pillar.id),
                        "name": pillar.name,
                        "description": pillar.description,
                    }
                    for pillar in current_pillars
                ],
                "pillar_count": current_count,
                "max_pillars": max_pillars,
                "remaining": remaining,
            }
        )

        # Add pillar limit context
        if remaining <= 0:
            builder.add_context(
                "limit_warning",
                "You've reached the maximum of 5 pillars. Consider if a new pillar is necessary or if it overlaps with existing ones.",
            )
        elif remaining <= 1:
            builder.add_context(
                "limit_note",
                f"You have {remaining} pillar slot remaining. Ensure this new pillar is distinct and necessary.",
            )

        if current_count > 0:
            builder.add_context(
                "overlap_warning",
                "Check if new pillar overlaps with existing ones. Consider merging if they're very similar.",
            )

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("pillar", str(e))
    except Exception as e:
        logger.exception(f"Error getting pillar framework: {e}")
        return build_error_response("pillar", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_strategic_pillar(
    name: str,
    description: str,
    draft_mode: bool = True,
) -> Dict[str, Any]:
    """Submit a refined strategic pillar after collaborative definition.

    Called only when Claude Code and user have crafted a high-quality
    pillar through dialogue using the framework guidance.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Pillar name (1-100 characters, unique per workspace)
        description: Pillar description including strategy and anti-strategy (required)
                    Should include both what you'll do and what you won't do
        draft_mode: If True, validate without persisting; if False, persist to database (default: True)

    Returns:
        Draft response with validation results if draft_mode=True,
        or success response with created pillar if draft_mode=False

    Example:
        >>> # Validate first (default)
        >>> draft = await submit_strategic_pillar(
        ...     name="Deep IDE Integration",
        ...     description="Strategy: Seamless developer workflow. Anti-Strategy: No web/mobile."
        ... )
        >>> # Then persist after user approval
        >>> result = await submit_strategic_pillar(
        ...     name="Deep IDE Integration",
        ...     description="Strategy: Seamless developer workflow. Anti-Strategy: No web/mobile.",
        ...     draft_mode=False
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(
            f"Submitting strategic pillar for workspace {workspace_id} (draft_mode={draft_mode})"
        )

        # DRAFT MODE: Validate without persisting
        if draft_mode:
            # Calculate display order
            current_pillars = strategic_controller.get_strategic_pillars(
                uuid.UUID(workspace_id), session
            )
            display_order = len(current_pillars)

            # Run all validation (throws DomainException on failure)
            validate_pillar_constraints(
                workspace_id=uuid.UUID(workspace_id),
                name=name,
                description=description,
                session=session,
            )

            # Build draft data dictionary
            draft_data = build_draft_pillar_data(
                workspace_id=uuid.UUID(workspace_id),
                user_id=uuid.UUID(user_id),
                name=name,
                description=description,
                display_order=display_order,
            )

            # Return draft response
            return build_draft_response(
                entity_type="strategic_pillar",
                message=f"Draft pillar '{name}' validated successfully",
                data=draft_data,
                next_steps=[
                    "Review pillar details with user",
                    "Confirm strategy and anti-strategy are clear",
                    "If approved, call submit_strategic_pillar() with draft_mode=False",
                    "Consider defining product outcomes next",
                ],
            )

        # NORMAL MODE: Create and persist pillar
        pillar = strategic_controller.create_strategic_pillar(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            name=name,
            description=description,
            session=session,
        )

        # Build success response with next steps
        all_pillars = strategic_controller.get_strategic_pillars(
            uuid.UUID(workspace_id), session
        )
        current_pillar_count = len(all_pillars)

        next_steps = []

        if current_pillar_count < 2:
            next_steps.append(
                f"Define {2 - current_pillar_count} more pillar(s) to reach minimum of 2 pillars"
            )
            next_steps.append(
                "Use get_pillar_definition_framework() to define additional pillars"
            )
        elif current_pillar_count >= 2:
            next_steps.append(
                "You now have enough pillars for a complete strategic foundation"
            )
            next_steps.append(
                "Define product outcomes that measure success for these pillars"
            )
            next_steps.append(
                "Use get_outcome_definition_framework() to start defining outcomes"
            )

        return build_success_response(
            entity_type="pillar",
            message="Strategic pillar created successfully",
            data=serialize_pillar(pillar),
            next_steps=next_steps,
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("pillar", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("pillar", str(e))
    except MCPContextError as e:
        return build_error_response("pillar", str(e))
    except Exception as e:
        logger.exception(f"Error submitting pillar: {e}")
        return build_error_response("pillar", f"Server error: {str(e)}")
    finally:
        session.close()


# ============================================================================
# Outcome Workflow
# ============================================================================


@mcp.tool()
async def get_outcome_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a product outcome.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary with guidance for defining measurable outcomes
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting outcome definition framework for workspace {workspace_uuid}"
        )

        # Get current outcomes and available pillars
        current_outcomes = strategic_controller.get_product_outcomes(
            workspace_uuid, session
        )
        available_pillars = strategic_controller.get_strategic_pillars(
            workspace_uuid, session
        )

        # Build framework
        builder = FrameworkBuilder("outcome")

        builder.set_purpose("Define measurable 1-3 year success targets")

        builder.add_criteria(
            [
                "Measurable with specific metrics",
                "Has baseline and target values",
                "Time-bound (1-3 years)",
                "Linked to at least one strategic pillar",
                "Outcome-focused, not solution-focused",
            ]
        )

        builder.add_example(
            text="Developer Daily Adoption",
            why_good="Specific metric, clear baseline/target, reasonable timeline, linked to pillar",
            description="Goal: Increase daily active IDE plugin users to measure adoption. Baseline: 30% of users currently daily active. Target: 80% daily active. Timeline: 6 months to reach this target.",
        )

        builder.add_questions(
            [
                "What does success look like for this pillar?",
                "How will you measure it? What's the metric?",
                "What's the current state (baseline)?",
                "What's your target? Is it ambitious but achievable?",
                "What's a realistic timeline? 6 months? 1 year? 3 years?",
                "Which strategic pillars does this outcome validate?",
            ]
        )

        builder.add_anti_pattern(
            example="Improve retention",
            why_bad="Not measurable, no baseline/target, no timeline",
            better="Increase 30-day retention from 40% to 70% within 12 months",
        )

        builder.add_anti_pattern(
            example="Ship mobile app",
            why_bad="Solution-focused, not outcome-focused",
            better="Enable 50% of users to manage tasks on mobile within 18 months",
        )

        builder.add_coaching_tips(
            [
                "Outcomes should ladder up to pillars (validate your strategy)",
                "Good outcomes are stretch goals but not impossible",
                "Each pillar should have at least 1-2 outcomes",
                "Outcomes should be observable and measurable",
            ]
        )

        # Set current state
        builder.set_current_state(
            {
                "current_outcomes": [
                    {
                        "id": str(outcome.id),
                        "name": outcome.name,
                        "description": outcome.description,
                    }
                    for outcome in current_outcomes
                ],
                "available_pillars": [
                    {"id": str(pillar.id), "name": pillar.name}
                    for pillar in available_pillars
                ],
            }
        )

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("outcome", str(e))
    except Exception as e:
        logger.exception(f"Error getting outcome framework: {e}")
        return build_error_response("outcome", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_product_outcome(
    name: str,
    description: str,
    pillar_ids: Optional[List[str]] = None,
    draft_mode: bool = True,
) -> Dict[str, Any]:
    """Submit a refined product outcome after collaborative definition.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Outcome name (1-150 characters)
        description: Outcome description including goal, baseline, target, and timeline (required)
                    Should include specific metrics, baseline values, target values, and timeline
        pillar_ids: List of pillar UUIDs to link (optional)
        draft_mode: If True, validate without persisting; if False, persist to database (default: True)

    Returns:
        Draft response with validation results if draft_mode=True,
        or success response with created outcome if draft_mode=False

    Example:
        >>> # Validate first (default)
        >>> draft = await submit_product_outcome(
        ...     name="Developer Daily Adoption",
        ...     description="Goal: Increase daily active IDE plugin users to measure adoption. Baseline: 30% of users daily active. Target: 80% daily active. Timeline: 6 months. Metric: Daily active users %",
        ...     pillar_ids=["pillar-uuid-1"]
        ... )
    Example:
        >>> result = await submit_product_outcome(
        ...     name="Developer Daily Adoption",
        ...     description="Goal: Increase daily active IDE plugin users to measure adoption. Baseline: 30% of users daily active. Target: 80% daily active. Timeline: 6 months. Metric: Daily active users %",
        ...     pillar_ids=["pillar-uuid-1"]
        ...     draft_mode=False
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(f"Submitting product outcome for workspace {workspace_id}")

        # DRAFT MODE: Validate without persisting
        if draft_mode:
            validate_outcome_constraints(
                workspace_id=uuid.UUID(workspace_id),
                name=name,
                description=description,
                pillar_ids=pillar_ids,
                session=session,
            )

            draft_data = build_draft_outcome_data(
                workspace_id=uuid.UUID(workspace_id),
                user_id=uuid.UUID(user_id),
                name=name,
                description=description,
                display_order=0,
                pillar_ids=pillar_ids,
            )

            return build_draft_response(
                entity_type="product_outcome",
                message=f"Draft ourcome '{name}' validated successfully",
                data=draft_data,
                next_steps=[
                    "Review product outcome details with user",
                    "Confirm the measure of success is clear",
                    "If approved, call submit_product_outcome() with draft_mode=False",
                    "Consider defining roadmap themes next",
                ],
            )

        # Convert pillar_ids to UUIDs
        pillar_uuids = []
        if pillar_ids:
            for pillar_id in pillar_ids:
                pillar_uuids.append(validate_uuid(pillar_id, "pillar_id"))

        # Call controller to create outcome
        outcome = strategic_controller.create_product_outcome(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            name=name,
            description=description,
            pillar_ids=pillar_uuids,
            session=session,
        )

        # Build success response with next steps
        next_steps = [
            "You've defined a measurable outcome for your strategic pillars",
            "Consider defining additional outcomes for other pillars",
            "Once you have outcomes for all pillars, explore roadmap themes",
        ]

        return build_success_response(
            entity_type="outcome",
            message="Product outcome created successfully",
            data=serialize_outcome(outcome),
            next_steps=next_steps,
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("outcome", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("outcome", str(e))
    except MCPContextError as e:
        return build_error_response("outcome", str(e))
    except Exception as e:
        logger.exception(f"Error submitting outcome: {e}")
        return build_error_response("outcome", f"Server error: {str(e)}")
    finally:
        session.close()


# ============================================================================
# Combined Strategic Foundation Workflow (Placeholder for future)
# ============================================================================

# Note: Combined foundation workflow will be implemented in a future iteration
# For now, users can build foundation piece by piece using individual workflows
