"""Prompt-driven MCP tools for strategic initiative management.

This module provides framework-based tools for creating initiatives with
full narrative connections (heroes, villains, conflicts, pillars, themes)
through conversational refinement.

Pattern: Get Framework → Claude + User Collaborate → Submit Result
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, selectinload

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
    build_error_response,
    build_success_response,
    get_workspace_id_from_request,
    serialize_strategic_initiative,
)
from src.mcp_server.prompt_driven_tools.utils.identifier_resolvers import (
    resolve_pillar_identifier,
    resolve_theme_identifier,
)
from src.mcp_server.prompt_driven_tools.utils.validation_runner import (
    validate_strategic_initiative_constraints,
)
from src.models import Initiative, InitiativeStatus
from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.services.hero_service import HeroService
from src.narrative.services.villain_service import VillainService
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Markdown templates for initiative description fields
IMPLEMENTATION_DESCRIPTION_TEMPLATE = """[One paragraph describing the deliverable and its core functionality]

## Technical Approach
[Key technical decisions, architecture choices, or implementation strategy]

## Scope
- [In scope item 1]
- [In scope item 2]

### Out of Scope
- [Explicitly excluded item]
"""

STRATEGIC_DESCRIPTION_TEMPLATE = """[Who needs this and what problem they're experiencing]

## Strategic Alignment
[How this connects to pillars, themes, or outcomes]

## Why Now
[What makes this the right time to build this]

## Expected Impact
[What changes for users when this ships]
"""

NARRATIVE_INTENT_TEMPLATE = """This initiative helps **[hero name]** defeat **[villain name]** by [how it addresses their core conflict].

It advances the **[theme name]** story arc by [contribution to the larger narrative].
"""


@mcp.tool()
async def get_strategic_initiative_definition_framework() -> Dict[str, Any]:
    """Get framework for defining a strategic initiative.

    Returns rich context with purpose, criteria, examples, questions etc
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

        current_state: Dict[str, Any] = {
            "available_heroes": [
                {
                    "identifier": hero.identifier,
                    "name": hero.name,
                    "is_primary": hero.is_primary,
                }
                for hero in heroes
            ],
            "available_villains": [
                {
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
                    "identifier": pillar.identifier,
                    "name": pillar.name,
                    "description": (
                        pillar.description[:100] if pillar.description else ""
                    ),
                }
                for pillar in pillars
            ],
            "available_themes": [
                {
                    "identifier": theme.identifier,
                    "name": theme.name,
                    "description": theme.description[:100],
                }
                for theme in themes
            ],
            "active_conflicts": [
                {
                    "identifier": conflict.identifier,
                    "description": conflict.description[:100],
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

        # Add markdown templates for description fields
        builder.add_template(
            "implementation_description", IMPLEMENTATION_DESCRIPTION_TEMPLATE
        )
        builder.add_template("strategic_description", STRATEGIC_DESCRIPTION_TEMPLATE)
        builder.add_template("narrative_intent", NARRATIVE_INTENT_TEMPLATE)

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
    title: str = None,
    implementation_description: str = None,
    strategic_description: Optional[str] = None,
    hero_identifiers: Optional[List[str]] = None,
    villain_identifiers: Optional[List[str]] = None,
    conflict_identifiers: Optional[List[str]] = None,
    pillar_identifier: Optional[str] = None,
    theme_identifier: Optional[str] = None,
    narrative_intent: Optional[str] = None,
    status: Optional[str] = None,
    strategic_initiative_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update a strategic initiative optionally with full narrative connections (upsert: omit strategic_initiative_identifier to create, provide to update).

    IMPORTANT: Reflect the initiative back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    Args:
        title: Initiative title (required for create, optional for update)
        implementation_description: What this initiative delivers and how it will be built (required for create, optional for update). Supports markdown formatting.
        strategic_description: How this initiative connects to the larger product strategy (optional, defaults to implementation_description for create)
        hero_identifiers: List of hero identifiers this initiative helps (optional)
        villain_identifiers: List of villain identifiers this initiative confronts (optional)
        conflict_identifiers: List of conflict identifiers this initiative addresses (optional)
        pillar_identifier: Strategic pillar identifier for alignment (optional, use "null" to unlink)
        theme_identifier: Roadmap theme identifier for placement (optional, use "null" to unlink)
        narrative_intent: Why this initiative matters narratively (optional)
        status: Initiative status (BACKLOG, TO_DO, IN_PROGRESS) - defaults to BACKLOG (optional)
        strategic_initiative_identifier: If provided, updates existing initiative (optional)
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

        # UPDATE PATH
        if strategic_initiative_identifier:
            logger.info(
                f"Updating strategic initiative {strategic_initiative_identifier}"
            )

            # Look up the strategic initiative
            strategic_initiative = _lookup_strategic_initiative(
                session, strategic_initiative_identifier, workspace_id
            )

            if not strategic_initiative:
                return build_error_response(
                    "strategic_initiative",
                    f"Strategic initiative not found for query: {strategic_initiative_identifier}",
                )

            warnings = []
            initiative = strategic_initiative.initiative

            if (
                title is not None
                or implementation_description is not None
                or status is not None
            ):
                controller = InitiativeController(session)

                initiative_status = None
                if status is not None:
                    try:
                        initiative_status = InitiativeStatus(status.upper())
                    except ValueError:
                        valid_statuses = ", ".join(s.value for s in InitiativeStatus)
                        return build_error_response(
                            "strategic_initiative",
                            f"Invalid status '{status}'. Valid statuses are: {valid_statuses}",
                        )

                controller.update_initiative(
                    initiative_id=initiative.id,
                    user_id=user_id,
                    title=title,
                    description=implementation_description,
                    status=initiative_status,
                )

            # Update strategic context via aggregate method
            publisher = EventPublisher(session)

            # Validate and prepare narrative link updates
            if (
                hero_identifiers is not None
                or villain_identifiers is not None
                or conflict_identifiers is not None
                or pillar_identifier is not None
                or theme_identifier is not None
            ):
                validation_result = validate_strategic_initiative_constraints(
                    workspace_id=workspace_id,
                    title=initiative.title,
                    description=initiative.description,
                    hero_identifiers=hero_identifiers or [],
                    villain_identifiers=villain_identifiers or [],
                    conflict_identifiers=conflict_identifiers or [],
                    pillar_identifier=pillar_identifier,
                    theme_identifier=theme_identifier,
                    narrative_intent=narrative_intent,
                    session=session,
                )

                if hero_identifiers is not None:
                    strategic_initiative.link_heroes(
                        validation_result["valid_hero_ids"], session
                    )
                if villain_identifiers is not None:
                    strategic_initiative.link_villains(
                        validation_result["valid_villain_ids"], session
                    )
                if conflict_identifiers is not None:
                    strategic_initiative.link_conflicts(
                        validation_result["valid_conflict_ids"], session
                    )

                warnings.extend(validation_result.get("warnings", []))

            # Update pillar/theme/narrative_intent
            final_pillar_id = strategic_initiative.pillar_id
            if pillar_identifier is not None:
                if pillar_identifier.lower() == "null" or pillar_identifier == "":
                    final_pillar_id = None
                else:
                    final_pillar_id = resolve_pillar_identifier(
                        pillar_identifier, workspace_id, session
                    )

            final_theme_id = strategic_initiative.theme_id
            if theme_identifier is not None:
                if theme_identifier.lower() == "null" or theme_identifier == "":
                    final_theme_id = None
                else:
                    final_theme_id = resolve_theme_identifier(
                        theme_identifier, workspace_id, session
                    )

            final_strategic_description = (
                strategic_description
                if strategic_description is not None
                else strategic_initiative.description
            )
            final_narrative_intent = (
                narrative_intent
                if narrative_intent is not None
                else strategic_initiative.narrative_intent
            )

            if any(
                [
                    pillar_identifier is not None,
                    theme_identifier is not None,
                    strategic_description is not None,
                    narrative_intent is not None,
                ]
            ):
                strategic_initiative.update_strategic_context(
                    publisher=publisher,
                    pillar_id=final_pillar_id,
                    theme_id=final_theme_id,
                    description=final_strategic_description,
                    narrative_intent=final_narrative_intent,
                )

            session.commit()
            session.refresh(strategic_initiative)
            session.refresh(initiative)

            initiative_data = {
                "id": str(strategic_initiative.id),
                "initiative": {
                    "id": str(initiative.id),
                    "title": initiative.title,
                    "description": initiative.description,
                    "identifier": initiative.identifier,
                    "status": initiative.status.value,
                },
                "strategic_context": serialize_strategic_initiative(
                    strategic_initiative
                ),
                "narrative_summary": _build_narrative_summary(strategic_initiative),
            }

            return build_success_response(
                entity_type="strategic_initiative",
                message=f"Updated strategic initiative {initiative.identifier}",
                data=initiative_data,
                next_steps=[
                    f"Strategic initiative '{initiative.title}' updated successfully"
                ],
                warnings=warnings if warnings else None,
            )

        # CREATE PATH
        else:
            logger.info("Creating new strategic initiative")

            # Validate required fields for creation
            if not title:
                return build_error_response(
                    "strategic_initiative",
                    "title is required for creating a new initiative",
                )
            if not implementation_description:
                return build_error_response(
                    "strategic_initiative",
                    "implementation_description is required for creating a new initiative",
                )

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

            hero_identifiers = hero_identifiers or []
            villain_identifiers = villain_identifiers or []
            conflict_identifiers = conflict_identifiers or []

            validation_result = validate_strategic_initiative_constraints(
                workspace_id=workspace_id,
                title=title,
                description=implementation_description,
                hero_identifiers=hero_identifiers,
                villain_identifiers=villain_identifiers,
                conflict_identifiers=conflict_identifiers,
                pillar_identifier=pillar_identifier,
                theme_identifier=theme_identifier,
                narrative_intent=narrative_intent,
                session=session,
            )

            valid_hero_ids = validation_result["valid_hero_ids"]
            valid_villain_ids = validation_result["valid_villain_ids"]
            valid_conflict_ids = validation_result["valid_conflict_ids"]
            valid_pillar_id = validation_result["valid_pillar_id"]
            valid_theme_id = validation_result["valid_theme_id"]
            warnings = validation_result["warnings"]

            if not valid_hero_ids:
                warnings.append(
                    "NARRATIVE GAP: No heroes linked. Strategic initiatives should connect "
                    "to the hero they help. Consider calling submit_hero() first if you "
                    "discussed who this helps but haven't created the entity yet."
                )

            if not valid_villain_ids:
                warnings.append(
                    "NARRATIVE GAP: No villains linked. Consider calling submit_villain() "
                    "to create the villain this initiative confronts."
                )

            if not valid_conflict_ids:
                warnings.append(
                    "NARRATIVE GAP: No conflicts linked. Consider calling create_conflict() "
                    "to establish the hero vs villain tension this initiative resolves."
                )

            controller = InitiativeController(session)
            initiative = controller.create_initiative(
                title=title,
                description=implementation_description,
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
                description=strategic_description,
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
                "strategic_context": serialize_strategic_initiative(
                    strategic_initiative
                ),
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
                next_steps.append(
                    "Aligned with strategic pillar for strategic coherence"
                )
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
async def query_strategic_initiatives(
    identifier: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    include_tasks: bool = False,
) -> Dict[str, Any]:
    """Query strategic initiatives with optional single-entity lookup.

    Query modes:
    - No params: Returns all strategic initiatives
    - identifier: Returns single initiative with full details + narrative summary
    - search: Returns initiatives matching search term (title/description)
    - status: Filters by status (e.g., "IN_PROGRESS" for active only)
    - include_tasks: Include tasks array (only when identifier provided)

    Args:
        identifier: Initiative identifier (e.g., "I-1001") for single lookup
        search: Search string for title/description matching
        status: Filter by status (BACKLOG, TO_DO, IN_PROGRESS)
        include_tasks: Include tasks array (only for single initiative)

    Returns:
        For single: initiative details with linked tasks and narrative summary
        For list/search: array of initiatives with narrative summaries
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
        workspace_uuid = uuid.UUID(workspace_id_str)

        # SINGLE INITIATIVE MODE: identifier provided
        if identifier:
            logger.info(
                f"Getting strategic initiative '{identifier}' in workspace {workspace_uuid}"
            )

            strategic_initiative = _lookup_strategic_initiative(
                session, identifier, workspace_uuid
            )

            if not strategic_initiative:
                return build_error_response(
                    "strategic_initiative",
                    f"Strategic initiative not found: {identifier}",
                )

            initiative = strategic_initiative.initiative
            initiative_data: Dict[str, Any] = {
                "initiative": {
                    "id": str(initiative.id),
                    "identifier": initiative.identifier,
                    "title": initiative.title,
                    "description": initiative.description,
                    "status": initiative.status.value,
                },
                "strategic_context": serialize_strategic_initiative(
                    strategic_initiative
                ),
                "narrative_summary": _build_narrative_summary(strategic_initiative),
            }

            if include_tasks:
                tasks_data = [
                    {
                        "id": str(task.id),
                        "identifier": task.identifier,
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value,
                        "type": task.type,
                        "created_at": (
                            task.created_at.isoformat() if task.created_at else None
                        ),
                        "updated_at": (
                            task.updated_at.isoformat() if task.updated_at else None
                        ),
                    }
                    for task in initiative.tasks
                ]
                initiative_data["tasks"] = tasks_data

            message = f"Found strategic initiative: {initiative.title}"
            if include_tasks:
                message += f" with {len(initiative.tasks)} task(s)"

            return build_success_response(
                entity_type="strategic_initiative",
                message=message,
                data=initiative_data,
            )

        # LIST MODE: search, status filter, or all
        logger.info(
            f"Querying strategic initiatives in workspace {workspace_uuid} "
            f"(search={search}, status={status})"
        )

        # Build base query
        if search:
            # Use search functionality
            controller = InitiativeController(session)
            initiatives = controller.search_initiatives(user_id, workspace_uuid, search)

            # Apply status filter if provided
            if status:
                try:
                    status_enum = InitiativeStatus(status.upper())
                    initiatives = [i for i in initiatives if i.status == status_enum]
                except ValueError:
                    valid_statuses = ", ".join(s.value for s in InitiativeStatus)
                    return build_error_response(
                        "strategic_initiative",
                        f"Invalid status '{status}'. Valid statuses are: {valid_statuses}",
                    )
        elif status:
            # Status filter only
            try:
                status_enum = InitiativeStatus(status.upper())
            except ValueError:
                valid_statuses = ", ".join(s.value for s in InitiativeStatus)
                return build_error_response(
                    "strategic_initiative",
                    f"Invalid status '{status}'. Valid statuses are: {valid_statuses}",
                )

            initiatives = (
                session.query(Initiative)
                .filter_by(workspace_id=workspace_uuid, status=status_enum)
                .order_by(Initiative.updated_at.desc())
                .all()
            )
        else:
            # Get all - query via StrategicInitiative for full context
            strategic_initiatives = (
                session.query(StrategicInitiative)
                .options(*_get_strategic_initiative_eager_load_options())
                .filter_by(workspace_id=workspace_uuid)
                .all()
            )

            initiatives_data = []
            for si in strategic_initiatives:
                initiative_data = {
                    "id": str(si.id),
                    "initiative": {
                        "id": str(si.initiative.id),
                        "identifier": si.initiative.identifier,
                        "title": si.initiative.title,
                        "description": si.initiative.description,
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

        # Process initiatives from search or status filter
        initiatives_data = []
        for initiative in initiatives:
            si = _ensure_strategic_context(session, initiative, user_id)

            initiative_data = {
                "id": str(si.id),
                "initiative": {
                    "id": str(initiative.id),
                    "identifier": initiative.identifier,
                    "title": initiative.title,
                    "description": initiative.description,
                    "status": initiative.status.value,
                },
                "strategic_context": serialize_strategic_initiative(si),
                "narrative_summary": _build_narrative_summary(si),
            }
            initiatives_data.append(initiative_data)

        session.commit()

        # Build message based on query type
        if search and status:
            message = f"Found {len(initiatives_data)} strategic initiative(s) matching '{search}' with status {status}"
        elif search:
            message = f"Found {len(initiatives_data)} strategic initiative(s) matching '{search}'"
        elif status:
            message = f"Found {len(initiatives_data)} strategic initiative(s) with status {status}"
        else:
            message = f"Found {len(initiatives_data)} strategic initiative(s)"

        return build_success_response(
            entity_type="strategic_initiative",
            message=message,
            data={"strategic_initiatives": initiatives_data},
        )

    except MCPContextError as e:
        logger.warning(f"Context error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except Exception as e:
        logger.exception(f"Error querying strategic initiatives: {e}")
        return build_error_response("strategic_initiative", f"Server error: {str(e)}")
    finally:
        session.close()


def _ensure_strategic_context(
    session: Session,
    initiative: Initiative,
    user_id: uuid.UUID,
) -> StrategicInitiative:
    """Get or create StrategicInitiative for an initiative.

    This helper ensures every Initiative has an associated StrategicInitiative,
    auto-creating one with minimal context if it doesn't exist.

    Args:
        session: Database session
        initiative: The Initiative entity to ensure has strategic context
        user_id: User ID for the strategic initiative if created

    Returns:
        The existing or newly created StrategicInitiative
    """
    si = (
        session.query(StrategicInitiative)
        .options(*_get_strategic_initiative_eager_load_options())
        .filter_by(initiative_id=initiative.id)
        .first()
    )
    if not si:
        si = StrategicInitiative(
            initiative_id=initiative.id,
            workspace_id=initiative.workspace_id,
            user_id=user_id,
            description=initiative.description,
        )
        session.add(si)
        session.flush()
        session.refresh(si)
    return si


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


def _get_strategic_initiative_eager_load_options():
    """Return common selectinload options for StrategicInitiative queries."""
    return [
        selectinload(StrategicInitiative.initiative),
        selectinload(StrategicInitiative.strategic_pillar).selectinload(
            StrategicPillar.outcomes
        ),
        selectinload(StrategicInitiative.roadmap_theme),
        selectinload(StrategicInitiative.heroes),
        selectinload(StrategicInitiative.villains),
        selectinload(StrategicInitiative.conflicts).selectinload(Conflict.hero),
        selectinload(StrategicInitiative.conflicts).selectinload(Conflict.villain),
        selectinload(StrategicInitiative.conflicts).selectinload(Conflict.story_arc),
    ]


def _lookup_strategic_initiative(
    session: Session, query: str, workspace_uuid: uuid.UUID
) -> Optional[StrategicInitiative]:
    """Look up a strategic initiative using flexible query (UUID or identifier).

    Tries multiple lookup strategies:
    1. First tries as StrategicInitiative UUID
    2. Then tries as Initiative UUID
    3. Finally tries as Initiative identifier (e.g., "I-1001")

    Returns the StrategicInitiative with eager-loaded relationships, or None if not found.
    """
    strategic_initiative = None
    eager_options = _get_strategic_initiative_eager_load_options()

    try:
        query_uuid = uuid.UUID(query)

        strategic_initiative = (
            session.query(StrategicInitiative)
            .options(*eager_options)
            .filter_by(id=query_uuid, workspace_id=workspace_uuid)
            .first()
        )

        if not strategic_initiative:
            strategic_initiative = (
                session.query(StrategicInitiative)
                .options(*eager_options)
                .filter_by(initiative_id=query_uuid, workspace_id=workspace_uuid)
                .first()
            )
    except ValueError:
        pass

    if not strategic_initiative:
        initiative = (
            session.query(Initiative)
            .filter_by(identifier=query, workspace_id=workspace_uuid)
            .first()
        )

        if initiative:
            strategic_initiative = (
                session.query(StrategicInitiative)
                .options(*eager_options)
                .filter_by(initiative_id=initiative.id, workspace_id=workspace_uuid)
                .first()
            )

    return strategic_initiative


@mcp.tool()
async def delete_strategic_initiative(query: str) -> Dict[str, Any]:
    """Delete a strategic initiative permanently.

    IMPORTANT: Confirm with user BEFORE calling - this action cannot be undone.
    Unlinks initiative from associated heroes, villains, conflicts, pillars, and themes.

    Args:
        query: Initiative identifier (e.g., "I-1001")
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

        logger.info(
            f"Deleting strategic initiative '{query}' for workspace {workspace_id}"
        )

        # Look up the strategic initiative
        strategic_initiative = _lookup_strategic_initiative(
            session, query, workspace_id
        )

        if not strategic_initiative:
            return build_error_response(
                "strategic_initiative",
                f"Strategic initiative not found for query: {query}",
            )

        initiative = strategic_initiative.initiative
        initiative_identifier = initiative.identifier
        initiative_title = initiative.title

        # Delete the initiative using the controller (StrategicInitiative cascades)
        controller = InitiativeController(session)
        controller.delete_initiative(initiative.id, user_id)

        return build_success_response(
            entity_type="strategic_initiative",
            message=f"Deleted strategic initiative {initiative_identifier} ({initiative_title})",
            data={
                "deleted_identifier": initiative_identifier,
            },
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except MCPContextError as e:
        logger.warning(f"Context error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("strategic_initiative", str(e))
    except Exception as e:
        logger.exception(f"Error deleting strategic initiative: {e}")
        return build_error_response("strategic_initiative", f"Server error: {str(e)}")
    finally:
        session.close()
