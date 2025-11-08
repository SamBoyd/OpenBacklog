"""Prompt-driven MCP tools for roadmap themes and prioritization.

This module provides framework-based tools for defining roadmap themes,
prioritizing work, and managing the strategic roadmap through conversational
refinement.

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
    build_error_response,
    build_success_response,
    calculate_alignment_score,
    get_alignment_recommendation,
    get_workspace_id_from_request,
    identify_alignment_issues,
    serialize_theme,
    validate_uuid,
)
from src.roadmap_intelligence import controller as roadmap_controller
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Theme Exploration Workflow
# ============================================================================


@mcp.tool()
async def get_theme_exploration_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a roadmap theme.

    Returns rich context to help Claude Code guide the user through
    defining a hypothesis-driven roadmap theme through collaborative refinement.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dict with purpose, criteria, examples, questions, anti-patterns,
        current state (outcomes + themes), and coaching tips.

    Example:
        >>> framework = await get_theme_exploration_framework()
        >>> print(framework["purpose"])
        "Identify a new strategic bet area to explore"
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # Get current outcomes and themes
        outcomes = strategic_controller.get_product_outcomes(workspace_uuid, session)
        all_themes = roadmap_controller.get_roadmap_themes(workspace_uuid, session)
        prioritized_themes = roadmap_controller.get_prioritized_themes(
            workspace_uuid, session
        )
        unprioritized_themes = roadmap_controller.get_unprioritized_themes(
            workspace_uuid, session
        )

        builder = FrameworkBuilder("theme")

        builder.set_purpose("Identify a new strategic bet area to explore")

        builder.add_criteria(
            [
                "Clear problem statement (what's broken?)",
                "Testable hypothesis (what do you believe will work?)",
                "Indicative metrics (how will you know it worked?)",
                "Reasonable time horizon (0-12 months)",
                "Linked to product outcomes (strategic alignment)",
            ]
        )

        # Add theme pattern template
        builder.add_context(
            "theme_pattern",
            {
                "problem": "Users are experiencing [specific problem]",
                "hypothesis": "If we [intervention], then [outcome] because [rationale]",
                "metrics": "[Metric] improves from [baseline] to [target]",
                "horizon": "0-12 months",
            },
        )

        # Add detailed examples
        builder.add_example(
            text="First-Week Configuration Success",
            why_good="Specific problem, testable hypothesis, measurable, reasonable timeline",
            problem_statement="New users abandon initial configuration (40% drop-off) because they don't understand why each setting matters",
            hypothesis="Providing example values and smart defaults for each configuration setting will increase setup completion from 40% to 70%",
            indicative_metrics="Setup completion rate: 40% → 70%",
            time_horizon_months=6,
        )

        builder.add_example(
            text="Keyboard-First Power Users",
            why_good="Clear user segment (power users), specific intervention, measurable outcome",
            problem_statement="Power users lose time switching between keyboard and mouse during complex workflows",
            hypothesis="If we provide comprehensive keyboard shortcuts for all actions, daily active power users will increase by 50%",
            indicative_metrics="Daily active power users: +50%",
            time_horizon_months=9,
        )

        # Add guiding questions
        builder.add_question("What specific problem are you seeing?")
        builder.add_question("Who is experiencing this problem?")
        builder.add_question("What do you believe will solve it? (Your hypothesis)")
        builder.add_question("How will you measure success?")
        builder.add_question("What's your timeline to test this?")
        builder.add_question("Which product outcomes does this support?")

        # Add anti-patterns
        builder.add_anti_pattern(
            example="Improve onboarding",
            why_bad="Vague, no specific problem or hypothesis",
            better="Reduce setup abandonment by providing contextual examples (40% → 70% completion)",
        )

        builder.add_anti_pattern(
            example="Build feature X",
            why_bad="Solution-focused, not hypothesis-driven",
            better="Test whether feature X solves problem Y for user segment Z",
        )

        # Add coaching tips
        builder.add_coaching_tip(
            "Good themes are bets you can test, not features to build"
        )
        builder.add_coaching_tip("Problem statement should be specific and observable")
        builder.add_coaching_tip(
            "Hypothesis should be falsifiable (could be proven wrong)"
        )
        builder.add_coaching_tip("Metrics should be leading indicators, not lagging")

        # Set current state with available outcomes and existing themes
        current_state = {
            "available_outcomes": [
                {
                    "id": str(outcome.id),
                    "name": outcome.name,
                    "description": outcome.description,
                }
                for outcome in outcomes
            ],
            "current_themes": {
                "prioritized": [
                    {
                        "id": str(theme.id),
                        "name": theme.name,
                        "problem_statement": theme.problem_statement,
                        "outcome_ids": [str(o.id) for o in theme.outcomes],
                    }
                    for theme in prioritized_themes
                ],
                "unprioritized": [
                    {
                        "id": str(theme.id),
                        "name": theme.name,
                        "problem_statement": theme.problem_statement,
                        "outcome_ids": [str(o.id) for o in theme.outcomes],
                    }
                    for theme in unprioritized_themes
                ],
            },
            "theme_count": len(all_themes),
            "max_themes": 5,
            "remaining": 5 - len(all_themes),
        }

        builder.set_current_state(current_state)

        builder.add_context(
            "prioritization_note",
            "New themes start unprioritized. Use prioritize_workstream() to commit to working on it.",
        )

        return builder.build()

    except ValueError as e:
        return build_error_response("theme", str(e))
    finally:
        session.close()


@mcp.tool()
async def submit_roadmap_theme(
    name: str,
    problem_statement: str,
    hypothesis: Optional[str] = None,
    indicative_metrics: Optional[str] = None,
    time_horizon_months: Optional[int] = None,
    outcome_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Submit a refined roadmap theme after collaborative definition.

    Called only when Claude Code and user have crafted a high-quality
    hypothesis-driven theme through dialogue.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Theme name (1-100 characters, unique per workspace)
        problem_statement: Problem being solved (1-1500 characters, required)
        hypothesis: Expected outcome (max 1500 characters, optional)
        indicative_metrics: Success metrics (max 1000 characters, optional)
        time_horizon_months: Time horizon in months (0-12, optional)
        outcome_ids: List of outcome IDs to link (optional but recommended)

    Returns:
        Success response with theme data and next steps, or error response.

    Example:
        >>> result = await submit_roadmap_theme(
        ...     name="First-Week Configuration Success",
        ...     problem_statement="Users abandon setup...",
        ...     hypothesis="Smart defaults will increase completion...",
        ...     indicative_metrics="Setup completion: 40% → 70%",
        ...     time_horizon_months=6,
        ...     outcome_ids=["outcome-uuid-1"]
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)

        # Convert outcome_ids from strings to UUIDs
        outcome_uuids = []
        if outcome_ids:
            for outcome_id in outcome_ids:
                try:
                    outcome_uuids.append(uuid.UUID(outcome_id))
                except (ValueError, AttributeError, TypeError) as e:
                    return build_error_response(
                        "theme", f"Invalid outcome_id format: {outcome_id}"
                    )

        # Create theme via controller
        theme = roadmap_controller.create_roadmap_theme(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            name=name,
            problem_statement=problem_statement,
            hypothesis=hypothesis,
            indicative_metrics=indicative_metrics,
            time_horizon_months=time_horizon_months,
            outcome_ids=outcome_uuids,
            session=session,
        )

        # Build next steps
        next_steps = [
            "Theme created successfully and starts in unprioritized state (backlog)",
            "Review strategic alignment: Does this theme support key outcomes?",
        ]

        if len(outcome_uuids) == 0:
            next_steps.append(
                "Consider linking to product outcomes for better strategic alignment"
            )
        else:
            next_steps.append(
                f"Theme linked to {len(outcome_uuids)} outcome(s) - good strategic alignment"
            )

        next_steps.append(
            "When ready to commit to this theme, use prioritize_workstream() to move to active roadmap"
        )

        return build_success_response(
            entity_type="theme",
            message="Roadmap theme created successfully",
            data=serialize_theme(theme),
            next_steps=next_steps,
        )

    except DomainException as e:
        return build_error_response("theme", str(e))
    except ValueError as e:
        return build_error_response("theme", str(e))
    except MCPContextError as e:
        return build_error_response("theme", str(e))
    finally:
        session.close()


# ============================================================================
# Prioritization Workflow
# ============================================================================


@mcp.tool()
async def get_prioritization_context() -> Dict[str, Any]:
    """Get context for prioritizing themes (deciding what to commit to).

    Returns rich context including current roadmap state, prioritized themes,
    unprioritized themes with alignment scores, and prioritization guidance.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dict with purpose, current roadmap state, questions to consider,
        prioritization guidance, and capacity check.

    Example:
        >>> context = await get_prioritization_context()
        >>> print(len(context["current_roadmap"]["prioritized_themes"]))
        2
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # Get outcomes for alignment scoring
        all_outcomes = strategic_controller.get_product_outcomes(
            workspace_uuid, session
        )
        total_outcomes = len(all_outcomes)
        all_pillars = strategic_controller.get_strategic_pillars(
            workspace_uuid, session
        )

        # Get prioritized and unprioritized themes
        prioritized_themes = roadmap_controller.get_prioritized_themes(
            workspace_uuid, session
        )
        unprioritized_themes = roadmap_controller.get_unprioritized_themes(
            workspace_uuid, session
        )

        builder = FrameworkBuilder("prioritization")

        builder.set_purpose("Decide what to commit to working on")

        # Build current roadmap state with alignment scores
        prioritized_data = []
        for idx, theme in enumerate(prioritized_themes):
            alignment_score = calculate_alignment_score(theme, total_outcomes)
            prioritized_data.append(
                {
                    "id": str(theme.id),
                    "name": theme.name,
                    "position": idx,
                    "problem_statement": theme.problem_statement,
                    "outcomes": [o.name for o in theme.outcomes],
                    "strategic_alignment_score": round(alignment_score, 2),
                }
            )

        unprioritized_data = []
        for theme in unprioritized_themes:
            alignment_score = calculate_alignment_score(theme, total_outcomes)
            alignment_issues = identify_alignment_issues(theme, all_pillars)
            unprioritized_data.append(
                {
                    "id": str(theme.id),
                    "name": theme.name,
                    "problem_statement": theme.problem_statement,
                    "outcomes": [o.name for o in theme.outcomes],
                    "strategic_alignment_score": round(alignment_score, 2),
                    "alignment_issues": alignment_issues,
                }
            )

        builder.add_context(
            "current_roadmap",
            {
                "prioritized_themes": prioritized_data,
                "unprioritized_themes": unprioritized_data,
            },
        )

        # Add questions to consider
        builder.add_question("Does this theme support your highest-priority outcomes?")
        builder.add_question("Do you have capacity to work on this now?")
        builder.add_question("Are there dependencies on other themes?")
        builder.add_question("Is this more important than currently prioritized work?")

        # Add prioritization guidance
        builder.add_context(
            "prioritization_guidance",
            {
                "factors": [
                    "Strategic alignment (linked to key outcomes)",
                    "User impact (how many users benefit)",
                    "Confidence (how certain is your hypothesis)",
                    "Cost (effort required to test)",
                    "Dependencies (what must happen first)",
                ],
                "anti_patterns": [
                    "Prioritizing based on 'feels urgent' without strategic tie",
                    "Too many themes prioritized at once (focus)",
                    "Prioritizing solutions before understanding problems",
                ],
            },
        )

        # Add capacity check
        current_count = len(prioritized_themes)
        recommended_max = 3
        warning = None
        if current_count >= recommended_max:
            warning = f"Currently have {current_count} prioritized themes. More than {recommended_max} can dilute focus. Consider deprioritizing something first."

        builder.add_context(
            "capacity_check",
            {
                "current_prioritized_count": current_count,
                "recommended_max": recommended_max,
                "warning": warning,
            },
        )

        return builder.build()

    except ValueError as e:
        return build_error_response("prioritization", str(e))
    finally:
        session.close()


@mcp.tool()
async def prioritize_workstream(
    theme_id: str, priority_position: int
) -> Dict[str, Any]:
    """Add theme to prioritized roadmap at specified position.

    Commits to working on a theme by moving it from backlog to active roadmap.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        theme_id: UUID of the theme to prioritize
        priority_position: Position in priority list (0-indexed, 0 = highest priority)

    Returns:
        Success response with theme data and next steps, or error response.

    Example:
        >>> result = await prioritize_workstream(
        ...     theme_id="...",
        ...     priority_position=0
        ... )
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        theme_uuid = validate_uuid(theme_id, "theme_id")

        # Get current prioritized count for capacity warning
        prioritized_themes = roadmap_controller.get_prioritized_themes(
            workspace_uuid, session
        )
        current_count = len(prioritized_themes)

        # Prioritize the theme
        theme = roadmap_controller.prioritize_roadmap_theme(
            theme_id=theme_uuid,
            new_order=priority_position,
            workspace_id=workspace_uuid,
            session=session,
        )

        # Build next steps
        next_steps = [
            f"Theme prioritized successfully at position {priority_position}",
            "Theme is now part of your active roadmap",
        ]

        # Warn if capacity exceeded
        if current_count + 1 > 3:
            next_steps.append(
                f"⚠️  You now have {current_count + 1} prioritized themes. Consider focusing on fewer themes for better execution."
            )

        next_steps.append("Next: Create strategic initiatives to execute this theme")

        return build_success_response(
            entity_type="prioritization",
            message="Theme prioritized successfully",
            data=serialize_theme(theme),
            next_steps=next_steps,
        )

    except DomainException as e:
        return build_error_response("prioritization", str(e))
    except ValueError as e:
        return build_error_response("prioritization", str(e))
    finally:
        session.close()


# ============================================================================
# Single-Turn Utility Tools
# ============================================================================


@mcp.tool()
async def deprioritize_workstream(theme_id: str) -> Dict[str, Any]:
    """Remove theme from prioritized roadmap (move back to backlog).

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        theme_id: UUID of the theme to deprioritize

    Returns:
        Success response with theme data, or error response.

    Example:
        >>> result = await deprioritize_workstream(theme_id="...")
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        theme_uuid = validate_uuid(theme_id, "theme_id")

        # Deprioritize the theme
        theme = roadmap_controller.deprioritize_roadmap_theme(
            theme_id=theme_uuid,
            workspace_id=workspace_uuid,
            session=session,
        )

        return build_success_response(
            entity_type="theme",
            message="Theme deprioritized successfully (moved to backlog)",
            data=serialize_theme(theme),
        )

    except DomainException as e:
        return build_error_response("theme", str(e))
    except ValueError as e:
        return build_error_response("theme", str(e))
    finally:
        session.close()


@mcp.tool()
async def organize_roadmap(theme_order: Dict[str, int]) -> Dict[str, Any]:
    """Reorder prioritized themes.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        theme_order: Dict mapping theme_id (str) to new position (int).
                     Must include ALL prioritized themes.

    Returns:
        Success response with ordered theme list, or error response.

    Example:
        >>> result = await organize_roadmap(
        ...     theme_order={"theme-1": 0, "theme-2": 1, "theme-3": 2}
        ... )
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # Convert theme_order keys from strings to UUIDs
        theme_order_uuids = {}
        for theme_id_str, position in theme_order.items():
            try:
                theme_order_uuids[uuid.UUID(theme_id_str)] = position
            except (ValueError, AttributeError, TypeError):
                return build_error_response(
                    "roadmap", f"Invalid theme_id format: {theme_id_str}"
                )

        # Reorder themes
        ordered_themes = roadmap_controller.reorder_roadmap_themes(
            workspace_id=workspace_uuid,
            theme_orders=theme_order_uuids,
            session=session,
        )

        return build_success_response(
            entity_type="roadmap",
            message="Roadmap reordered successfully",
            data={
                "themes": [serialize_theme(theme) for theme in ordered_themes],
                "count": len(ordered_themes),
            },
        )

    except DomainException as e:
        return build_error_response("roadmap", str(e))
    except ValueError as e:
        return build_error_response("roadmap", str(e))
    finally:
        session.close()


@mcp.tool()
async def connect_theme_to_outcomes(
    theme_id: str, outcome_ids: List[str]
) -> Dict[str, Any]:
    """Update outcome linkages for a theme.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        theme_id: UUID of the theme
        outcome_ids: List of outcome IDs to link to this theme

    Returns:
        Success response with updated theme and new alignment score, or error response.

    Example:
        >>> result = await connect_theme_to_outcomes(
        ...     theme_id="...",
        ...     outcome_ids=["outcome-1", "outcome-2"]
        ... )
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        theme_uuid = validate_uuid(theme_id, "theme_id")

        # Convert outcome_ids from strings to UUIDs
        outcome_uuids = []
        for outcome_id in outcome_ids:
            try:
                outcome_uuids.append(uuid.UUID(outcome_id))
            except (ValueError, AttributeError, TypeError):
                return build_error_response(
                    "theme", f"Invalid outcome_id format: {outcome_id}"
                )

        # Get the theme first
        theme = (
            session.query(roadmap_controller.RoadmapTheme)
            .filter_by(id=theme_uuid, workspace_id=workspace_uuid)
            .first()
        )

        if not theme:
            return build_error_response("theme", "Theme not found")

        # Update the theme with new outcome links
        theme = roadmap_controller.update_roadmap_theme(
            theme_id=theme_uuid,
            workspace_id=workspace_uuid,
            name=theme.name,
            problem_statement=theme.problem_statement,
            hypothesis=theme.hypothesis,
            indicative_metrics=theme.indicative_metrics,
            time_horizon_months=theme.time_horizon_months,
            outcome_ids=outcome_uuids,
            session=session,
        )

        # Calculate new alignment score
        all_outcomes = strategic_controller.get_product_outcomes(
            workspace_uuid, session
        )
        alignment_score = calculate_alignment_score(theme, len(all_outcomes))
        alignment_recommendation = get_alignment_recommendation(alignment_score)

        next_steps = [
            f"Theme now linked to {len(outcome_uuids)} outcome(s)",
            f"Alignment score: {alignment_score:.2f}",
            alignment_recommendation,
        ]

        return build_success_response(
            entity_type="theme",
            message="Theme outcome links updated successfully",
            data=serialize_theme(theme),
            next_steps=next_steps,
        )

    except DomainException as e:
        return build_error_response("theme", str(e))
    except ValueError as e:
        return build_error_response("theme", str(e))
    finally:
        session.close()
