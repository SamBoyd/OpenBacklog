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
    build_draft_response,
    build_draft_theme_data,
    build_error_response,
    build_success_response,
    calculate_alignment_score,
    get_alignment_recommendation,
    get_workspace_id_from_request,
    identify_alignment_issues,
    serialize_theme,
    validate_theme_constraints,
    validate_uuid,
)
from src.roadmap_intelligence import controller as roadmap_controller
from src.strategic_planning import EventPublisher
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

    Roadmap themes are strategic bet areas that organize your roadmap around
    problems to solve, not features to build. Each theme represents a cluster
    of initiatives that together advance one or more product outcomes.

    Good themes express intent and learning focus, not solution decisions.
    They communicate what you're exploring and why, not what you're building
    and when. Themes sit in a 6-12 month horizon.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dict with purpose, criteria, examples, questions, anti-patterns,
        current state (outcomes + themes), coaching tips, and natural language
        mapping guidance.

    Example:
        >>> framework = await get_theme_exploration_framework()
        >>> # Use to guide user through defining a hypothesis-driven bet area
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

        builder.set_purpose(
            "Define a strategic bet area - a problem space to explore over "
            "the next 6-12 months that will advance your product outcomes"
        )

        builder.add_criteria(
            [
                "Outcome-aligned: Clearly ladders up to at least one product outcome",
                "Problem-oriented: Describes a user or business problem, not features",
                "Exploratory: Includes a testable hypothesis you can prove or disprove",
                "Flexible in execution: Allows initiatives to evolve as you learn",
                "Communicable: Clear, memorable name that works as shorthand",
                "Time-bound: Designed for 6-12 month focus, re-evaluated each cycle",
            ]
        )

        builder.add_example(
            text="Stay in Flow",
            why_good="Problem-focused, memorable name, clear hypothesis, measurable",
            description=(
                "**Problem Statement**: Solo devs lose focus when context switching "
                "between IDE and planning tools. "
                "**Hypothesis**: If we embed backlog management directly in the IDE, "
                "developers will complete more tasks per session. "
                "**Indicative Metrics**: IDE engagement rate, task completion velocity. "
                "**Timeline**: 6-9 months to test and validate."
            ),
            outcomes_supported="70% of users manage backlog from IDE",
        )

        builder.add_example(
            text="First-Run Delight",
            why_good="Specific problem with data, clear hypothesis, actionable timeline",
            description=(
                "**Problem Statement**: New users abandon setup (40% drop-off) "
                "because they don't understand why each setting matters. "
                "**Hypothesis**: Smart defaults and contextual examples will "
                "increase setup completion from 40% to 70%. "
                "**Indicative Metrics**: Setup completion rate, time-to-first-value. "
                "**Timeline**: 6 months."
            ),
            outcomes_supported="60% trial-to-active conversion",
        )

        builder.add_example(
            text="AI as Co-Pilot",
            why_good="Clear user benefit, exploratory scope, hypothesis-driven",
            description=(
                "**Problem Statement**: Developers want AI assistance but hesitate "
                "because they don't trust recommendations they don't understand. "
                "**Hypothesis**: Making AI reasoning transparent and educational will "
                "increase AI feature adoption by 50%. "
                "**Indicative Metrics**: AI feature usage rate, trust survey scores. "
                "**Timeline**: 9 months."
            ),
            outcomes_supported="80% of tasks created via AI",
        )

        builder.add_questions(
            [
                "What specific problem are you seeing? Who's experiencing it?",
                "What's your bet? What do you believe will solve this?",
                "How will you know if it worked? What metric will change?",
                "What's a reasonable timeline to test this hypothesis?",
                "Which of your success metrics does this support?",
                "What might this theme include? (initiatives, not features)",
            ]
        )

        builder.add_anti_pattern(
            example="Improve onboarding",
            why_bad="Too vague - doesn't specify the problem or a testable hypothesis",
            better="First-Run Delight: Reduce setup abandonment via smart defaults (40% → 70%)",
        )

        builder.add_anti_pattern(
            example="Build mobile app",
            why_bad="Solution-focused (a feature list), not a problem space to explore",
            better="On-the-Go Access: Test if mobile task management increases daily engagement",
        )

        builder.add_anti_pattern(
            example="Infrastructure improvements",
            why_bad="Departmental bucket - reflects internal structure, not user problems",
            better="Lightning Fast: Reduce response times to maintain user flow state",
        )

        builder.add_anti_pattern(
            example="Add dark mode",
            why_bad="Too narrow/tactical - could be completed in a single sprint",
            better="Developer Comfort: Explore customization options that reduce eye strain and improve focus",
        )

        builder.add_anti_pattern(
            example="Delight users",
            why_bad="Too grand - sounds inspiring but doesn't guide prioritization",
            better="Celebration Moments: Create emotional wins at key milestones to drive retention",
        )

        builder.add_coaching_tips(
            [
                "Name it well: Memorable phrases like 'Stay in Flow' stick better than jargon",
                "Make it a bet: Each theme should embody a hypothesis you can test and learn from",
                "Limit to 3-5 themes per cycle: Enough to diversify bets, few enough to focus",
                "Use it to say no: If an initiative doesn't fit a theme, it's off-strategy",
                "A theme is not a feature: It's a problem space that may spawn multiple initiatives",
                "Good themes are chapters in your product story, not line items on a release calendar",
            ]
        )

        builder.set_conversation_guidelines(
            say_this="your next big bet, the problem space you want to explore, your focus area",
            not_this="Roadmap Theme, the theme entity, your workstream",
            example="What's the next big bet you want to make? What problem space do you want to explore?",
        )

        builder.add_natural_question(
            "problem_space",
            "What problem keeps coming up? What's frustrating your users right now?",
        )
        builder.add_natural_question(
            "hypothesis",
            "What's your bet? If you could fix one thing, what would change for them?",
        )
        builder.add_natural_question(
            "success_signal",
            "How will you know you're on the right track? What number would move?",
        )
        builder.add_natural_question(
            "scope",
            "What kind of work might this include? What would you explore first?",
        )
        builder.add_natural_question(
            "timeline",
            "How long do you need to test this bet? 3 months? 6 months?",
        )

        builder.add_extraction_guidance(
            from_input=(
                "Solo devs keep telling me they lose their train of thought when "
                "they have to leave VS Code to update their backlog. I think if "
                "we put everything in the IDE, they'd get more done."
            ),
            extractions={
                "theme_name": "'Stay in Flow' (memorable, problem-focused)",
                "problem": "Context switching between IDE and planning tool breaks focus",
                "who_affected": "Solo developers",
                "hypothesis": "IDE-native backlog management increases task completion",
                "implied_metric": "Task completion rate, time in flow state",
                "suggested_timeline": "6-9 months (significant integration work)",
            },
        )

        builder.add_extraction_guidance(
            from_input=(
                "New users keep abandoning during setup. Like 40% never finish. "
                "I bet if we showed them examples of what good looks like, more "
                "would complete it."
            ),
            extractions={
                "theme_name": "'First-Run Delight' (focuses on the experience)",
                "problem": "40% of users abandon setup - high drop-off",
                "who_affected": "New users in their first session",
                "hypothesis": "Examples and smart defaults will increase completion",
                "target_metric": "Setup completion rate: 40% → 70%",
                "suggested_timeline": "3-6 months (onboarding iteration)",
            },
        )

        builder.add_inference_example(
            user_says=(
                "Everyone's asking for keyboard shortcuts. Power users hate "
                "reaching for the mouse - kills their flow."
            ),
            inferences={
                "theme": "Keyboard-First Workflows",
                "problem": "Mouse usage interrupts power user flow",
                "who_benefits": "Power users (specific, valuable segment)",
                "hypothesis": "Comprehensive shortcuts will increase engagement",
                "implied_metric": "Power user daily active rate or session length",
                "note": "Narrow scope - may be an initiative under a broader theme like 'Developer Comfort'",
            },
        )

        builder.add_inference_example(
            user_says=(
                "I want to make the AI actually useful. Right now people don't "
                "trust it because they don't know why it's suggesting things."
            ),
            inferences={
                "theme": "AI Transparency (or 'AI as Co-Pilot')",
                "problem": "Users don't trust AI recommendations they don't understand",
                "hypothesis": "Explaining AI reasoning will increase adoption",
                "implied_metric": "AI feature usage rate, trust scores",
                "outcomes_connection": "Supports AI adoption metrics",
            },
        )

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
                        "description": theme.description,
                        "outcome_ids": [str(o.id) for o in theme.outcomes],
                    }
                    for theme in prioritized_themes
                ],
                "unprioritized": [
                    {
                        "id": str(theme.id),
                        "name": theme.name,
                        "description": theme.description,
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
    description: str,
    outcome_ids: Optional[List[str]] = None,
    hero_identifier: Optional[str] = None,
    primary_villain_identifier: Optional[str] = None,
    draft_mode: bool = True,
) -> Dict[str, Any]:
    """Submit a refined roadmap theme after collaborative definition.

    Called only when Claude Code and user have crafted a high-quality
    hypothesis-driven theme through dialogue.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Theme name (1-100 characters, unique per workspace)
        description: Theme description including problem statement, hypothesis, metrics, and timeline (required)
                    Should include specific problem, testable hypothesis, indicative metrics, and timeline
        outcome_ids: List of outcome IDs to link (optional but recommended)
        hero_identifier: Optional human-readable hero identifier (e.g., "H-2003")
        primary_villain_identifier: Optional human-readable villain identifier (e.g., "V-2003")
        draft_mode: If True, validate without persisting; if False, persist to database (default: True)

    Returns:
        Draft response with validation results if draft_mode=True,
        or success response with created theme if draft_mode=False

    Example:
        >>> # Validate first (default)
        >>> draft = await submit_roadmap_theme(
        ...     name="First-Week Configuration Success",
        ...     description="Problem Statement: New users abandon initial configuration (40% drop-off) because they don't understand why each setting matters. Hypothesis: Providing example values and smart defaults will increase setup completion from 40% to 70%. Indicative Metrics: Setup completion rate increases from 40% to 70%. Timeline: 6 months.",
        ...     outcome_ids=["outcome-uuid-1"]
        ...     draft_mode=True
        ... )
        >>> result = await submit_roadmap_theme(
        ...     name="First-Week Configuration Success",
        ...     description="Problem Statement: New users abandon initial configuration (40% drop-off) because they don't understand why each setting matters. Hypothesis: Providing example values and smart defaults will increase setup completion from 40% to 70%. Indicative Metrics: Setup completion rate increases from 40% to 70%. Timeline: 6 months.",
        ...     outcome_ids=["outcome-uuid-1"]
        ...     draft_mode=False
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

        # Resolve hero and villain identifiers if provided
        hero_uuid = None
        villain_uuid = None
        if hero_identifier:
            from src.narrative.services.hero_service import HeroService

            publisher = EventPublisher(session)
            hero_service = HeroService(session, publisher)
            hero = hero_service.get_hero_by_identifier(
                hero_identifier, uuid.UUID(workspace_id)
            )
            hero_uuid = hero.id

        if primary_villain_identifier:
            from src.narrative.services.villain_service import VillainService

            publisher = EventPublisher(session)
            villain_service = VillainService(session, publisher)
            villain = villain_service.get_villain_by_identifier(
                primary_villain_identifier, uuid.UUID(workspace_id)
            )
            villain_uuid = villain.id

        # DRAFT MODE: Validate without persisting
        if draft_mode:
            validate_theme_constraints(
                workspace_id=uuid.UUID(workspace_id),
                name=name,
                description=description,
                outcome_ids=outcome_ids,  # Pass original string list
                session=session,
                hero_identifier=hero_identifier,
                primary_villain_identifier=primary_villain_identifier,
            )

            draft_data = build_draft_theme_data(
                workspace_id=uuid.UUID(workspace_id),
                user_id=uuid.UUID(user_id),
                name=name,
                description=description,
                outcome_ids=outcome_ids,  # Pass original string list
                display_order=0,
                hero_identifier=hero_identifier,
                primary_villain_identifier=primary_villain_identifier,
            )

            return build_draft_response(
                entity_type="theme",
                message=f"Draft theme '{name}' validated successfully",
                data=draft_data,
                next_steps=[
                    "Review theme details with user",
                    "Confirm the theme is clear and correctly defined",
                    "If approved, call submit_roadmap_theme() with draft_mode=False",
                    "Consider linking to product outcomes for better strategic alignment",
                    "Consider linking to heroes and villains for better context",
                ],
            )

        # Create theme via controller
        theme = roadmap_controller.create_roadmap_theme(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            name=name,
            description=description,
            outcome_ids=outcome_uuids,
            session=session,
        )

        # Link hero and villain if provided
        if hero_uuid or villain_uuid:
            theme.hero_id = hero_uuid
            theme.primary_villain_id = villain_uuid
            session.commit()
            session.refresh(theme)

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

        if hero_identifier:
            next_steps.append(f"Theme linked to hero {hero_identifier}")
        if primary_villain_identifier:
            next_steps.append(f"Theme linked to villain {primary_villain_identifier}")

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
            description=theme.description,
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


@mcp.tool()
async def link_theme_to_hero(theme_id: str, hero_identifier: str) -> Dict[str, Any]:
    """Links a roadmap theme to a hero.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        theme_id: UUID of roadmap theme
        hero_identifier: Human-readable hero identifier (e.g., "H-2003")

    Returns:
        Success response with updated theme
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        theme_uuid = validate_uuid(theme_id, "theme_id")

        from src.narrative.services.hero_service import HeroService

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        hero = hero_service.get_hero_by_identifier(hero_identifier, workspace_uuid)

        theme = (
            session.query(roadmap_controller.RoadmapTheme)
            .filter_by(id=theme_uuid, workspace_id=workspace_uuid)
            .first()
        )

        if not theme:
            return build_error_response("theme", "Theme not found")

        theme.hero_id = hero.id
        session.commit()
        session.refresh(theme)

        return build_success_response(
            entity_type="theme",
            message=f"Theme '{theme.name}' linked to hero '{hero.name}' ({hero_identifier})",
            data=serialize_theme(theme),
        )

    except DomainException as e:
        return build_error_response("theme", str(e))
    except ValueError as e:
        return build_error_response("theme", str(e))
    finally:
        session.close()


@mcp.tool()
async def link_theme_to_villain(
    theme_id: str, villain_identifier: str
) -> Dict[str, Any]:
    """Links a roadmap theme to a villain.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        theme_id: UUID of roadmap theme
        villain_identifier: Human-readable villain identifier (e.g., "V-2003")

    Returns:
        Success response with updated theme
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        theme_uuid = validate_uuid(theme_id, "theme_id")

        from src.narrative.services.villain_service import VillainService

        publisher = EventPublisher(session)
        villain_service = VillainService(session, publisher)
        villain = villain_service.get_villain_by_identifier(
            villain_identifier, workspace_uuid
        )

        theme = (
            session.query(roadmap_controller.RoadmapTheme)
            .filter_by(id=theme_uuid, workspace_id=workspace_uuid)
            .first()
        )

        if not theme:
            return build_error_response("theme", "Theme not found")

        theme.primary_villain_id = villain.id
        session.commit()
        session.refresh(theme)

        return build_success_response(
            entity_type="theme",
            message=f"Theme '{theme.name}' linked to villain '{villain.name}' ({villain_identifier})",
            data=serialize_theme(theme),
        )

    except DomainException as e:
        return build_error_response("theme", str(e))
    except ValueError as e:
        return build_error_response("theme", str(e))
    finally:
        session.close()
