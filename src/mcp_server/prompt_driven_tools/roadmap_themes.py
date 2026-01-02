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
    validate_theme_constraints,
)
from src.mcp_server.prompt_driven_tools.utils.identifier_resolvers import (
    resolve_outcome_identifiers,
)
from src.roadmap_intelligence import controller as roadmap_controller
from src.strategic_planning import EventPublisher, RoadmapTheme
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Theme Exploration Workflow
# ============================================================================


async def get_theme_exploration_framework() -> Dict[str, Any]:
    """Get framework for defining roadmap theme (6-12 month strategic bet area).

    Returns context with purpose, criteria, examples, questions, anti-patterns, coaching tips, and conversational mappings.
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
            "New themes start unprioritized. Use set_theme_priority() to commit to working on it.",
        )

        return builder.build()

    except ValueError as e:
        return build_error_response("theme", str(e))
    finally:
        session.close()


@mcp.tool()
async def submit_roadmap_theme(
    name: Optional[str] = None,
    description: Optional[str] = None,
    outcome_identifiers: Optional[List[str]] = None,
    hero_identifier: Optional[str] = None,
    primary_villain_identifier: Optional[str] = None,
    theme_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a refined roadmap theme after collaborative definition.

    Creates a new roadmap theme or updates an existing one.

    Called only when Claude Code and user have crafted a high-quality
    hypothesis-driven theme through dialogue.

    IMPORTANT: Reflect the theme back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    **Upsert Behavior:**
    - If `theme_identifier` is **omitted**: Creates new theme
    - If `theme_identifier` is **provided**: Updates existing theme

    Args:
        name: Theme name (1-100 characters, unique per workspace, required for create, optional for update)
        description: Theme description (required for create, optional for update)
        outcome_identifiers: List of outcome identifiers to link (optional but recommended)
        hero_identifier: Optional human-readable hero identifier (e.g., "H-001")
        primary_villain_identifier: Optional human-readable villain identifier (e.g., "V-001")
        theme_identifier: If provided, updates existing theme (optional)

    Returns:
        Success response with created or updated theme
        ...     name="First-Week Configuration Success",
        ...     description="Problem Statement: New users abandon initial configuration...",
        ...     outcome_identifiers=["O-001"]
        ... )
        >>> # Update
        >>> result = await submit_roadmap_theme(
        ...     theme_identifier="T-001",
        ...     name="Updated Theme Name",
        ...     hero_identifier="H-001"
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        workspace_uuid = uuid.UUID(workspace_id)

        # UPDATE PATH
        if theme_identifier:
            logger.info(f"Updating roadmap theme {theme_identifier}")

            theme = (
                session.query(RoadmapTheme)
                .filter_by(identifier=theme_identifier, workspace_id=workspace_uuid)
                .first()
            )

            if not theme:
                return build_error_response(
                    "theme", f"Roadmap theme {theme_identifier} not found"
                )

            # Merge fields: use provided values or preserve existing
            final_name = name if name is not None else theme.name
            final_description = (
                description if description is not None else theme.description
            )

            # Resolve outcome identifiers to UUIDs if provided
            outcome_uuids = None
            if outcome_identifiers is not None:
                outcome_uuids = resolve_outcome_identifiers(
                    outcome_identifiers, workspace_uuid, session
                )

            # Use controller to update name, description, and outcomes
            updated_theme = roadmap_controller.update_roadmap_theme(
                theme_id=theme.id,
                workspace_id=workspace_uuid,
                name=final_name,
                description=final_description,
                outcome_ids=(
                    outcome_uuids
                    if outcome_uuids is not None
                    else [o.id for o in theme.outcomes]
                ),
                session=session,
            )

            # Update hero link if provided
            if hero_identifier is not None:
                from src.narrative.services.hero_service import HeroService

                publisher = EventPublisher(session)
                hero_service = HeroService(session, publisher)
                hero = hero_service.get_hero_by_identifier(
                    hero_identifier, workspace_uuid
                )
                updated_theme.link_heroes([hero.id], session)
                session.commit()
                session.refresh(updated_theme)

            # Update villain link if provided
            if primary_villain_identifier is not None:
                from src.narrative.services.villain_service import VillainService

                publisher = EventPublisher(session)
                villain_service = VillainService(session, publisher)
                villain = villain_service.get_villain_by_identifier(
                    primary_villain_identifier, workspace_uuid
                )
                updated_theme.primary_villain_id = villain.id
                session.commit()
                session.refresh(updated_theme)

            # Calculate alignment score for response
            all_outcomes = strategic_controller.get_product_outcomes(
                workspace_uuid, session
            )
            alignment_score = calculate_alignment_score(
                updated_theme, len(all_outcomes)
            )

            next_steps = [f"Roadmap theme '{updated_theme.name}' updated successfully"]
            if outcome_identifiers is not None:
                next_steps.append(
                    f"Theme now linked to {len(outcome_identifiers)} outcome(s)"
                )
            if hero_identifier is not None:
                next_steps.append(f"Theme linked to hero {hero_identifier}")
            if primary_villain_identifier is not None:
                next_steps.append(
                    f"Theme linked to villain {primary_villain_identifier}"
                )
            next_steps.append(f"Strategic alignment score: {alignment_score:.2f}")

            return build_success_response(
                entity_type="theme",
                message=f"Updated roadmap theme '{updated_theme.name}'",
                data=serialize_theme(updated_theme),
                next_steps=next_steps,
            )

        # CREATE PATH
        else:
            logger.info("Creating new roadmap theme")

            # Validate required fields for creation
            if not name:
                return build_error_response(
                    "theme", "name is required for creating a new theme"
                )
            if not description:
                return build_error_response(
                    "theme", "description is required for creating a new theme"
                )

            warnings = []
            if not outcome_identifiers:
                warnings.append(
                    "ALIGNMENT GAP: No outcomes linked. Themes should connect to the product "
                    "outcomes they drive. Consider which outcome(s) this theme advances."
                )

            # Resolve outcome identifiers to UUIDs
            outcome_uuids = []
            if outcome_identifiers:
                outcome_uuids = resolve_outcome_identifiers(
                    outcome_identifiers, workspace_uuid, session
                )

            # Resolve hero and villain identifiers if provided
            hero_uuid = None
            villain_uuid = None
            if hero_identifier:
                from src.narrative.services.hero_service import HeroService

                publisher = EventPublisher(session)
                hero_service = HeroService(session, publisher)
                hero = hero_service.get_hero_by_identifier(
                    hero_identifier, workspace_uuid
                )
                hero_uuid = hero.id

            if primary_villain_identifier:
                from src.narrative.services.villain_service import VillainService

                publisher = EventPublisher(session)
                villain_service = VillainService(session, publisher)
                villain = villain_service.get_villain_by_identifier(
                    primary_villain_identifier, workspace_uuid
                )
                villain_uuid = villain.id

            validate_theme_constraints(
                workspace_id=workspace_uuid,
                name=name,
                description=description,
                outcome_ids=[str(outcome_uuid) for outcome_uuid in outcome_uuids],
                session=session,
                hero_identifier=hero_identifier,
                primary_villain_identifier=primary_villain_identifier,
            )

            # Create theme via controller
            theme = roadmap_controller.create_roadmap_theme(
                workspace_id=workspace_uuid,
                user_id=uuid.UUID(user_id),
                name=name,
                description=description,
                outcome_ids=outcome_uuids,
                session=session,
            )

            if hero_uuid:
                theme.link_heroes([hero_uuid], session)
                session.commit()
                session.refresh(theme)

            if villain_uuid:
                theme.link_villains([villain_uuid], session)
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
                next_steps.append(
                    f"Theme linked to villain {primary_villain_identifier}"
                )

            next_steps.append(
                "When ready to commit to this theme, use set_theme_priority() to move to active roadmap"
            )

            return build_success_response(
                entity_type="theme",
                message="Roadmap theme created successfully",
                data=serialize_theme(theme),
                next_steps=next_steps,
                warnings=warnings if warnings else None,
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
# Priority Management Workflow
# ============================================================================


@mcp.tool()
async def set_theme_priority(
    theme_identifier: str,
    priority_position: Optional[int] = None,
) -> Dict[str, Any]:
    """Set theme priority position or deprioritize theme.

    Sets a theme's priority position on the active roadmap, or removes it
    from prioritization when priority_position is None.

    Args:
        theme_identifier: Human-readable identifier of the theme (e.g., "T-001")
        priority_position: Priority position (0-indexed, 0 = highest priority).
                          If None, removes theme from prioritized roadmap.

    Returns:
        Success response with theme data and next steps, or error response.
        ...     theme_identifier="T-001",
        ...     priority_position=0
        ... )
        ...     theme_identifier="T-001",
        ...     priority_position=None
        ... )
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # Fetch theme
        theme = (
            session.query(roadmap_controller.RoadmapTheme)
            .filter_by(identifier=theme_identifier, workspace_id=workspace_uuid)
            .first()
        )

        if not theme:
            return build_error_response("theme", f"Theme {theme_identifier} not found")

        # Branch: Prioritize vs Deprioritize
        if priority_position is not None:
            # PRIORITIZE PATH
            # Get current prioritized count for capacity warning
            prioritized_themes = roadmap_controller.get_prioritized_themes(
                workspace_uuid, session
            )
            current_count = len(prioritized_themes)

            # Prioritize the theme
            theme = roadmap_controller.prioritize_roadmap_theme(
                theme_id=theme.id,
                new_order=priority_position,
                workspace_id=workspace_uuid,
                session=session,
            )

            # Build next steps with capacity warning
            next_steps = [
                f"Theme prioritized successfully at position {priority_position}",
                "Theme is now part of your active roadmap",
            ]

            if current_count + 1 > 3:
                next_steps.append(
                    f"⚠️  You now have {current_count + 1} prioritized themes. "
                    f"Consider focusing on fewer themes for better execution."
                )

            next_steps.append(
                "Next: Create strategic initiatives to execute this theme"
            )

            return build_success_response(
                entity_type="theme",
                message="Theme prioritized successfully",
                data=serialize_theme(theme),
                next_steps=next_steps,
            )
        else:
            # DEPRIORITIZE PATH
            theme = roadmap_controller.deprioritize_roadmap_theme(
                theme_id=theme.id,
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
async def connect_theme_to_outcomes(
    theme_identifier: str, outcome_identifiers: List[str]
) -> Dict[str, Any]:
    """Update outcome linkages for a theme.

    Args:
        theme_identifier: Human-readable identifier of the theme (e.g., "T-001")
        outcome_identifiers: List of outcome identifiers to link to this theme

    Returns:
        Success response with updated theme and new alignment score, or error response.
        ...     theme_identifier="T-001",
        ...     outcome_identifiers=["O-001", "O-002"]
        ... )
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # Resolve outcome identifiers to UUIDs
        outcome_uuids = resolve_outcome_identifiers(
            outcome_identifiers, workspace_uuid, session
        )

        # Get the theme first
        theme = (
            session.query(roadmap_controller.RoadmapTheme)
            .filter_by(identifier=theme_identifier, workspace_id=workspace_uuid)
            .first()
        )

        if not theme:
            return build_error_response("theme", "Theme not found")

        # Update the theme with new outcome links
        theme = roadmap_controller.update_roadmap_theme(
            theme_id=theme.id,
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


# ============================================================================
# Roadmap Theme CRUD Tools
# ============================================================================


@mcp.tool()
async def query_roadmap_themes(
    identifier: Optional[str] = None,
    prioritized_only: bool = False,
) -> Dict[str, Any]:
    """Query roadmap themes with optional filtering and single-entity lookup.

    A unified query tool that replaces get_roadmap_themes and get_roadmap_theme_details.

    **Query modes:**
    - No params: Returns all themes (prioritized and unprioritized)
    - identifier: Returns single theme with full linked entities and alignment score
    - prioritized_only: Returns only prioritized themes

    Args:
        identifier: Theme identifier (e.g., "T-001") for single lookup
        prioritized_only: If True, filters to prioritized themes only

    Returns:
        For single: theme details with outcomes, hero/villain, alignment score
        For list: array of themes
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # SINGLE THEME MODE: identifier provided
        if identifier:
            logger.info(
                f"Getting roadmap theme '{identifier}' in workspace {workspace_uuid}"
            )

            theme = (
                session.query(roadmap_controller.RoadmapTheme)
                .filter_by(identifier=identifier, workspace_id=workspace_uuid)
                .first()
            )

            if not theme:
                return build_error_response(
                    "theme", f"Roadmap theme not found: {identifier}"
                )

            theme_data = serialize_theme(theme)

            # Add enrichments
            theme_data["outcome_names"] = [outcome.name for outcome in theme.outcomes]
            theme_data["hero_names"] = [hero.name for hero in theme.heroes]
            theme_data["villain_names"] = [villain.name for villain in theme.villains]

            if hasattr(theme, "primary_villain_id") and theme.primary_villain_id:
                primary_villain = next(
                    (v for v in theme.villains if v.id == theme.primary_villain_id),
                    None,
                )
                theme_data["primary_villain_name"] = (
                    primary_villain.name if primary_villain else None
                )
            else:
                theme_data["primary_villain_name"] = None

            prioritized_themes = roadmap_controller.get_prioritized_themes(
                workspace_uuid, session
            )
            is_prioritized = any(t.id == theme.id for t in prioritized_themes)
            theme_data["is_prioritized"] = is_prioritized

            all_outcomes = strategic_controller.get_product_outcomes(
                workspace_uuid, session
            )
            alignment_score = calculate_alignment_score(theme, len(all_outcomes))
            theme_data["alignment_score"] = round(alignment_score, 2)

            return build_success_response(
                entity_type="theme",
                message=f"Found roadmap theme: {theme.name}",
                data=theme_data,
            )

        # LIST MODE: return themes based on filter
        logger.info(
            f"Getting roadmap themes for workspace {workspace_uuid} "
            f"(prioritized_only={prioritized_only})"
        )

        if prioritized_only:
            themes = roadmap_controller.get_prioritized_themes(workspace_uuid, session)
            message = f"Found {len(themes)} prioritized roadmap theme(s)"
        else:
            themes = roadmap_controller.get_roadmap_themes(workspace_uuid, session)
            message = f"Found {len(themes)} roadmap theme(s)"

        return build_success_response(
            entity_type="theme",
            message=message,
            data={
                "themes": [serialize_theme(theme) for theme in themes],
            },
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("theme", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("theme", str(e))
    except Exception as e:
        logger.exception(f"Error querying roadmap themes: {e}")
        return build_error_response("theme", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def delete_roadmap_theme(theme_identifier: str) -> Dict[str, Any]:
    """Delete a roadmap theme permanently.

    IMPORTANT: Confirm with user BEFORE calling - this action cannot be undone.
    This will also unlink the theme from any associated outcomes, heroes, and villains.

    Args:
        theme_identifier: Human-readable identifier of the roadmap theme to delete (e.g., "T-001")

    Returns:
        Success response confirming deletion
    """
    session = SessionLocal()
    try:
        _, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(
            f"Deleting roadmap theme {theme_identifier} for workspace {workspace_id}"
        )

        workspace_uuid = uuid.UUID(workspace_id)

        theme = (
            session.query(roadmap_controller.RoadmapTheme)
            .filter_by(identifier=theme_identifier, workspace_id=workspace_uuid)
            .first()
        )

        if not theme:
            return build_error_response(
                "theme", f"Roadmap theme {theme_identifier} not found"
            )

        theme_name = theme.name

        session.delete(theme)
        session.commit()

        return build_success_response(
            entity_type="theme",
            message=f"Deleted roadmap theme '{theme_name}'",
            data={"deleted_identifier": theme_identifier},
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("theme", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("theme", str(e))
    except MCPContextError as e:
        return build_error_response("theme", str(e))
    except Exception as e:
        logger.exception(f"Error deleting roadmap theme: {e}")
        return build_error_response("theme", f"Server error: {str(e)}")
    finally:
        session.close()
