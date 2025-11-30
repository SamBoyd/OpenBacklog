"""Prompt-driven MCP tools for strategic initiative management.

This module provides framework-based tools for creating initiatives with
full narrative connections (heroes, villains, conflicts, pillars, themes)
through conversational refinement.

Pattern: Get Framework → Claude + User Collaborate → Submit Result
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import selectinload

from src.db import SessionLocal
from src.initiative_management.aggregates.strategic_initiative import (
    StrategicInitiative,
)
from src.initiative_management.initiative_controller import InitiativeController
from src.initiative_management.product_strategy_controller import (
    create_strategic_initiative as create_strategic_context,
)
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.utils import (
    FrameworkBuilder,
    build_draft_response,
    build_error_response,
    build_success_response,
    get_workspace_id_from_request,
    serialize_strategic_initiative,
)
from src.mcp_server.prompt_driven_tools.utils.draft_builder import (
    build_draft_strategic_initiative_data,
)
from src.mcp_server.prompt_driven_tools.utils.validation_runner import (
    validate_strategic_initiative_constraints,
)
from src.models import InitiativeStatus
from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.services.hero_service import HeroService
from src.narrative.services.villain_service import VillainService
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp.tool()
async def get_strategic_initiative_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a strategic initiative.

    Returns rich context to help Claude Code guide the user through
    creating an initiative with full narrative connections - who it helps,
    what problems it defeats, and why it matters strategically.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary with purpose, criteria, examples, questions,
        anti-patterns, current state (available heroes/villains/pillars/themes),
        and coaching tips

    Example:
        >>> framework = await get_strategic_initiative_definition_framework()
        >>> # Claude Code uses framework to guide user through refinement
        >>> await submit_strategic_initiative(title, description, hero_ids, ...)
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting strategic initiative framework for workspace {workspace_uuid}"
        )

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        villain_service = VillainService(session, publisher)

        heroes = hero_service.get_heroes_for_workspace(workspace_uuid)
        villains = villain_service.get_villains_for_workspace(workspace_uuid)
        pillars = strategic_controller.get_strategic_pillars(workspace_uuid, session)
        themes = (
            session.query(RoadmapTheme)
            .filter_by(workspace_id=workspace_uuid)
            .order_by(RoadmapTheme.created_at)
            .all()
        )
        conflicts = (
            session.query(Conflict)
            .filter_by(workspace_id=workspace_uuid)
            .filter(Conflict.status != ConflictStatus.RESOLVED)
            .all()
        )

        builder = FrameworkBuilder("strategic_initiative")

        builder.set_purpose(
            "Define an initiative with strategic context - who it helps, "
            "what it defeats, and why it matters"
        )

        builder.add_criteria(
            [
                "Clear, actionable title describing what will be built",
                "Description explains the value delivered",
                "Linked to at least one hero (who benefits)",
                "Connected to villains/conflicts it addresses",
                "Aligned with a strategic pillar or roadmap theme",
                "Has narrative intent explaining why it matters",
            ]
        )

        builder.add_example(
            text="Smart Context Switching",
            why_good="Clear title, linked to hero/villain, has narrative intent, aligned to pillar",
            description="Auto-save and restore IDE context when switching between tasks, "
            "eliminating the cognitive load of manually tracking state.",
            hero_link="Sarah, The Solo Builder",
            villain_link="Context Switching (WORKFLOW)",
            pillar_link="Deep IDE Integration",
            narrative_intent="Defeats the context switching villain by making task switches instant and painless for Sarah.",
        )

        builder.add_example(
            text="AI-Powered Decision Synthesis",
            why_good="Specific deliverable, addresses multiple villains, clear strategic alignment",
            description="Transform scattered feedback from multiple sources into actionable "
            "product decisions with AI-generated summaries and recommendations.",
            hero_link="Alex, The Product Manager",
            villain_link="Scattered Insights (WORKFLOW)",
            theme_link="Feedback to Decision Pipeline",
            narrative_intent="Helps Alex conquer information overload by synthesizing chaos into clarity.",
        )

        builder.add_questions(
            [
                "What specific thing will you build?",
                "Who will benefit from this? (Which hero?)",
                "What problem or obstacle does this address? (Which villain?)",
                "How does this align with your strategy? (Which pillar or theme?)",
                "Why does this initiative matter narratively?",
            ]
        )

        builder.add_anti_pattern(
            example="Improve UX",
            why_bad="Too vague, no specific deliverable, no narrative connections",
            better="Smart Context Switching - auto-save/restore IDE state for Sarah to defeat context switching",
        )

        builder.add_anti_pattern(
            example="Build feature X (no connections)",
            why_bad="Plain initiative without strategic context loses the 'why'",
            better="Feature X linked to heroes it helps and villains it defeats",
        )

        builder.add_coaching_tips(
            [
                "Start with who benefits (hero) and what problem is solved (villain)",
                "The narrative intent explains the story: 'This helps [hero] defeat [villain] by...'",
                "Link to a pillar for strategic alignment or a theme for roadmap placement",
                "Initiatives without connections are just tasks - add the strategic context",
            ]
        )

        builder.set_conversation_guidelines(
            say_this="what you want to build next, your next project, this feature",
            not_this="Strategic Initiative, the initiative, this initiative entity",
            example="What do you want to build next? Who will it help and what problem will it solve?",
        )

        builder.add_natural_question(
            "deliverable",
            "What specific thing do you want to build?",
        )
        builder.add_natural_question(
            "beneficiary",
            "Who will this help? (Use their name, like Sarah or Alex)",
        )
        builder.add_natural_question(
            "problem_solved",
            "What problem does this solve for them?",
        )
        builder.add_natural_question(
            "why_now",
            "Why is this the right thing to build now?",
        )
        builder.add_natural_question(
            "success",
            "When this ships, what changes for them?",
        )

        builder.add_extraction_guidance(
            from_input="I want to build auto-save for IDE context so Sarah doesn't lose her place when switching tasks",
            extractions={
                "title": "Auto-Save IDE Context",
                "description": "Automatically save and restore IDE context when switching tasks",
                "hero_connection": "Sarah (by name)",
                "problem_solved": "losing place when switching tasks",
                "implied_villain": "Context Switching",
                "narrative_intent": "Help Sarah maintain flow by eliminating context loss during task switches",
            },
        )

        builder.add_inference_example(
            user_says="Alex needs a way to turn all that feedback chaos into actual decisions",
            inferences={
                "initiative_title": "AI-Powered Decision Synthesis (or similar)",
                "hero": "Alex",
                "villain": "Feedback chaos / scattered insights",
                "value_delivered": "Transform chaos into actionable decisions",
                "narrative_intent": "Help Alex conquer information overload",
            },
        )

        current_state = {
            "available_heroes": [
                {
                    "id": str(hero.id),
                    "identifier": hero.identifier,
                    "name": hero.name,
                    "is_primary": hero.is_primary,
                }
                for hero in heroes
            ],
            "available_villains": [
                {
                    "id": str(villain.id),
                    "identifier": villain.identifier,
                    "name": villain.name,
                    "villain_type": villain.villain_type,
                    "is_defeated": villain.is_defeated,
                }
                for villain in villains
                if not villain.is_defeated
            ],
            "available_pillars": [
                {
                    "id": str(pillar.id),
                    "name": pillar.name,
                    "description": pillar.description,
                }
                for pillar in pillars
            ],
            "available_themes": [
                {
                    "id": str(theme.id),
                    "name": theme.name,
                    "is_prioritized": theme.is_prioritized,
                }
                for theme in themes
            ],
            "active_conflicts": [
                {
                    "id": str(conflict.id),
                    "identifier": conflict.identifier,
                    "description": conflict.description,
                }
                for conflict in conflicts
            ],
            "hero_count": len(heroes),
            "villain_count": len([v for v in villains if not v.is_defeated]),
            "pillar_count": len(pillars),
            "theme_count": len(themes),
        }

        builder.set_current_state(current_state)

        if not heroes:
            builder.add_context(
                "missing_heroes",
                "No heroes defined yet. Consider defining who you're building for "
                "using get_hero_definition_framework() first.",
            )

        if not villains or all(v.is_defeated for v in villains):
            builder.add_context(
                "missing_villains",
                "No active villains defined. Consider defining problems to solve "
                "using get_villain_definition_framework() first.",
            )

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except Exception as e:
        logger.exception(f"Error getting strategic initiative framework: {e}")
        return build_error_response("strategic_initiative", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_strategic_initiative(
    title: str,
    description: str,
    hero_ids: Optional[List[str]] = None,
    villain_ids: Optional[List[str]] = None,
    conflict_ids: Optional[List[str]] = None,
    pillar_id: Optional[str] = None,
    theme_id: Optional[str] = None,
    narrative_intent: Optional[str] = None,
    status: Optional[str] = None,
    draft_mode: bool = True,
) -> Dict[str, Any]:
    """Submit a strategic initiative optionally with full narrative connections.

    Creates both an Initiative and its StrategicInitiative context in one
    operation, linking to heroes, villains, conflicts, pillars, and themes.

    Uses graceful degradation: invalid narrative IDs are skipped with warnings
    rather than failing the entire operation.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        title: Initiative title (e.g., "Smart Context Switching")
        description: What this initiative delivers
        hero_ids: List of hero UUIDs this initiative helps (optional)
        villain_ids: List of villain UUIDs this initiative confronts (optional)
        conflict_ids: List of conflict UUIDs this initiative addresses (optional)
        pillar_id: Strategic pillar UUID for alignment (optional)
        theme_id: Roadmap theme UUID for placement (optional)
        narrative_intent: Why this initiative matters narratively (optional)
        status: Initiative status (BACKLOG, TO_DO, IN_PROGRESS) - defaults to BACKLOG
        draft_mode: If True, validate without persisting; if False, persist (default: True)

    Returns:
        Draft response with validation results and warnings if draft_mode=True,
        or success response with created initiative and strategic context if draft_mode=False

    Example:
        >>> # Validate first (default)
        >>> draft = await submit_strategic_initiative(
        ...     title="Smart Context Switching",
        ...     description="Auto-save and restore IDE context...",
        ...     hero_ids=["uuid-of-sarah"],
        ...     villain_ids=["uuid-of-context-switching"],
        ...     pillar_id="uuid-of-ide-integration-pillar",
        ...     narrative_intent="Defeats context switching for Sarah",
        ...     draft_mode=True
        ... )
        >>> # Then persist
        >>> result = await submit_strategic_initiative(..., draft_mode=False)
    """
    session = SessionLocal()
    try:
        user_id_str, workspace_id_str = get_auth_context(
            session, requires_workspace=True
        )
        if workspace_id_str is None:
            raise MCPContextError(
                "Workspace not found.",
                error_type="workspace_error",
            )

        user_id = uuid.UUID(user_id_str)
        workspace_id = uuid.UUID(workspace_id_str)

        logger.info(f"Submitting strategic initiative for workspace {workspace_id}")

        initiative_status = InitiativeStatus.BACKLOG
        if status:
            try:
                initiative_status = InitiativeStatus(status.upper())
            except ValueError:
                valid_statuses = ", ".join(s.value for s in InitiativeStatus)
                return build_error_response(
                    "strategic_initiative",
                    f"Invalid status '{status}'. Valid statuses are: {valid_statuses}",
                )

        hero_ids = hero_ids or []
        villain_ids = villain_ids or []
        conflict_ids = conflict_ids or []

        validation_result = validate_strategic_initiative_constraints(
            workspace_id=workspace_id,
            title=title,
            description=description,
            hero_ids=hero_ids,
            villain_ids=villain_ids,
            conflict_ids=conflict_ids,
            pillar_id=pillar_id,
            theme_id=theme_id,
            narrative_intent=narrative_intent,
            session=session,
        )

        valid_hero_ids = validation_result["valid_hero_ids"]
        valid_villain_ids = validation_result["valid_villain_ids"]
        valid_conflict_ids = validation_result["valid_conflict_ids"]
        valid_pillar_id = validation_result["valid_pillar_id"]
        valid_theme_id = validation_result["valid_theme_id"]
        warnings = validation_result["warnings"]

        if draft_mode:
            draft_data = build_draft_strategic_initiative_data(
                workspace_id=workspace_id,
                user_id=user_id,
                title=title,
                description=description,
                status=initiative_status,
                hero_ids=valid_hero_ids,
                villain_ids=valid_villain_ids,
                conflict_ids=valid_conflict_ids,
                pillar_id=valid_pillar_id,
                theme_id=valid_theme_id,
                narrative_intent=narrative_intent,
            )

            next_steps = [
                "Review initiative details with user",
                "Confirm the narrative connections are correct",
                "If approved, call submit_strategic_initiative() with draft_mode=False",
            ]

            if warnings:
                next_steps.insert(
                    0, f"Note: {len(warnings)} warning(s) - some IDs were invalid"
                )

            return build_draft_response(
                entity_type="strategic_initiative",
                message=f"Draft strategic initiative '{title}' validated successfully",
                data=draft_data,
                next_steps=next_steps,
                warnings=warnings,
            )

        controller = InitiativeController(session)
        initiative = controller.create_initiative(
            title=title,
            description=description,
            user_id=user_id,
            workspace_id=workspace_id,
            status=initiative_status,
        )

        controller.complete_onboarding_if_first_initiative(user_id)

        strategic_initiative = create_strategic_context(
            initiative_id=initiative.id,
            workspace_id=workspace_id,
            user_id=user_id,
            pillar_id=valid_pillar_id,
            theme_id=valid_theme_id,
            description=description,
            narrative_intent=narrative_intent,
            session=session,
            hero_ids=valid_hero_ids,
            villain_ids=valid_villain_ids,
            conflict_ids=valid_conflict_ids,
        )

        session.refresh(strategic_initiative)

        response_data = {
            "initiative": {
                "id": str(initiative.id),
                "title": initiative.title,
                "description": initiative.description,
                "identifier": initiative.identifier,
                "status": initiative.status.value,
            },
            "strategic_context": serialize_strategic_initiative(strategic_initiative),
        }

        next_steps = [
            f"Strategic initiative '{initiative.title}' created with identifier {initiative.identifier}",
        ]

        if valid_hero_ids:
            next_steps.append(
                f"Linked to {len(valid_hero_ids)} hero(es) - they will benefit from this"
            )
        if valid_villain_ids:
            next_steps.append(
                f"Confronts {len(valid_villain_ids)} villain(s) - progress defeats them"
            )
        if valid_pillar_id:
            next_steps.append("Aligned with strategic pillar for strategic coherence")
        if valid_theme_id:
            next_steps.append("Placed in roadmap theme for planning visibility")

        next_steps.append(
            "Use get_initiative_details() to see the full context anytime"
        )

        return build_success_response(
            entity_type="strategic_initiative",
            message="Strategic initiative created with narrative connections",
            data=response_data,
            next_steps=next_steps,
            warnings=warnings if warnings else None,
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except MCPContextError as e:
        logger.warning(f"Context error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except Exception as e:
        logger.exception(f"Error submitting strategic initiative: {e}")
        return build_error_response("strategic_initiative", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_strategic_initiatives() -> Dict[str, Any]:
    """Retrieve all strategic initiatives with their narrative connections.

    Returns initiatives that have strategic context (heroes, villains, pillars,
    themes) attached, providing the full picture of what's being built and why.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        List of strategic initiatives with full narrative context
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(f"Getting strategic initiatives for workspace {workspace_uuid}")

        strategic_initiatives = (
            session.query(StrategicInitiative)
            .options(
                selectinload(StrategicInitiative.initiative),
                selectinload(StrategicInitiative.strategic_pillar),
                selectinload(StrategicInitiative.roadmap_theme),
                selectinload(StrategicInitiative.heroes),
                selectinload(StrategicInitiative.villains),
                selectinload(StrategicInitiative.conflicts),
            )
            .filter_by(workspace_id=workspace_uuid)
            .all()
        )

        initiatives_data = []
        for si in strategic_initiatives:
            initiative_data = {
                "id": str(si.id),
                "initiative": {
                    "id": str(si.initiative.id),
                    "title": si.initiative.title,
                    "description": si.initiative.description,
                    "identifier": si.initiative.identifier,
                    "status": si.initiative.status.value,
                },
                "strategic_context": serialize_strategic_initiative(si),
                "narrative_summary": _build_narrative_summary(si),
            }
            initiatives_data.append(initiative_data)

        return build_success_response(
            entity_type="strategic_initiative",
            message=f"Found {len(initiatives_data)} strategic initiative(s)",
            data={"strategic_initiatives": initiatives_data},
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except Exception as e:
        logger.exception(f"Error getting strategic initiatives: {e}")
        return build_error_response("strategic_initiative", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_strategic_initiative(query: str) -> Dict[str, Any]:
    """Retrieve a single strategic initiative by ID or identifier.

    Accepts a flexible query that tries multiple lookup strategies:
    1. First tries as StrategicInitiative UUID
    2. Then tries as Initiative UUID
    3. Finally tries as Initiative identifier (e.g., "I-1001")

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        query: Strategic initiative ID, initiative ID, or initiative identifier

    Returns:
        Strategic initiative with full narrative context, or error if not found
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting strategic initiative for query '{query}' in workspace {workspace_uuid}"
        )

        strategic_initiative = None

        try:
            query_uuid = uuid.UUID(query)

            strategic_initiative = (
                session.query(StrategicInitiative)
                .options(
                    selectinload(StrategicInitiative.initiative),
                    selectinload(StrategicInitiative.strategic_pillar),
                    selectinload(StrategicInitiative.roadmap_theme),
                    selectinload(StrategicInitiative.heroes),
                    selectinload(StrategicInitiative.villains),
                    selectinload(StrategicInitiative.conflicts),
                )
                .filter_by(id=query_uuid, workspace_id=workspace_uuid)
                .first()
            )

            if not strategic_initiative:
                strategic_initiative = (
                    session.query(StrategicInitiative)
                    .options(
                        selectinload(StrategicInitiative.initiative),
                        selectinload(StrategicInitiative.strategic_pillar),
                        selectinload(StrategicInitiative.roadmap_theme),
                        selectinload(StrategicInitiative.heroes),
                        selectinload(StrategicInitiative.villains),
                        selectinload(StrategicInitiative.conflicts),
                    )
                    .filter_by(initiative_id=query_uuid, workspace_id=workspace_uuid)
                    .first()
                )
        except ValueError:
            pass

        if not strategic_initiative:
            from src.models import Initiative

            initiative = (
                session.query(Initiative)
                .filter_by(identifier=query, workspace_id=workspace_uuid)
                .first()
            )

            if initiative:
                strategic_initiative = (
                    session.query(StrategicInitiative)
                    .options(
                        selectinload(StrategicInitiative.initiative),
                        selectinload(StrategicInitiative.strategic_pillar),
                        selectinload(StrategicInitiative.roadmap_theme),
                        selectinload(StrategicInitiative.heroes),
                        selectinload(StrategicInitiative.villains),
                        selectinload(StrategicInitiative.conflicts),
                    )
                    .filter_by(initiative_id=initiative.id, workspace_id=workspace_uuid)
                    .first()
                )

        if not strategic_initiative:
            return build_error_response(
                "strategic_initiative",
                f"Strategic initiative not found for query: {query}",
            )

        initiative_data = {
            "id": str(strategic_initiative.id),
            "initiative": {
                "id": str(strategic_initiative.initiative.id),
                "title": strategic_initiative.initiative.title,
                "description": strategic_initiative.initiative.description,
                "identifier": strategic_initiative.initiative.identifier,
                "status": strategic_initiative.initiative.status.value,
            },
            "strategic_context": serialize_strategic_initiative(strategic_initiative),
            "narrative_summary": _build_narrative_summary(strategic_initiative),
        }

        return build_success_response(
            entity_type="strategic_initiative",
            message=f"Found strategic initiative: {strategic_initiative.initiative.title}",
            data=initiative_data,
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except Exception as e:
        logger.exception(f"Error getting strategic initiative: {e}")
        return build_error_response("strategic_initiative", f"Server error: {str(e)}")
    finally:
        session.close()


def _build_narrative_summary(si: StrategicInitiative) -> str:
    """Build a human-readable narrative summary of a strategic initiative."""
    parts = []

    if si.heroes:
        hero_names = ", ".join([h.name for h in si.heroes])
        parts.append(f"Helps: {hero_names}")

    if si.villains:
        villain_names = ", ".join([v.name for v in si.villains])
        parts.append(f"Defeats: {villain_names}")

    if si.strategic_pillar:
        parts.append(f"Pillar: {si.strategic_pillar.name}")

    if si.roadmap_theme:
        parts.append(f"Theme: {si.roadmap_theme.name}")

    if si.narrative_intent:
        parts.append(f"Why: {si.narrative_intent}")

    return " | ".join(parts) if parts else "No narrative connections yet"
