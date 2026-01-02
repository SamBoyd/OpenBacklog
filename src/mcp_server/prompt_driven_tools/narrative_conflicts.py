"""Prompt-driven MCP tools for conflict management.

This module provides framework-based tools for creating and managing conflicts
between heroes and villains through conversational refinement.

Pattern: Get Framework → Claude + User Collaborate → Submit Result
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import selectinload

from src.db import SessionLocal
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.utils import (
    FrameworkBuilder,
    build_error_response,
    build_success_response,
    get_workspace_id_from_request,
    serialize_conflict,
)
from src.mcp_server.prompt_driven_tools.utils.identifier_resolvers import (
    resolve_initiative_identifier,
    resolve_theme_identifier,
)
from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.exceptions import DomainException
from src.narrative.services.conflict_service import ConflictService
from src.narrative.services.hero_service import HeroService
from src.narrative.services.villain_service import VillainService
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_conflict_eager_load_options() -> List[Any]:
    """Return common selectinload options for Conflict queries."""
    return [
        selectinload(Conflict.hero),
        selectinload(Conflict.villain),
        selectinload(Conflict.story_arc),
        selectinload(Conflict.resolved_by_initiative),
    ]


# ============================================================================
# Conflict Workflow
# ============================================================================


@mcp.tool()
async def get_conflict_creation_framework() -> Dict[str, Any]:
    """Get framework for creating a conflict between hero and villain.

    Returns context with purpose, criteria, examples, questions, anti-patterns, and coaching tips.
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting conflict creation framework for workspace {workspace_uuid}"
        )

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        villain_service = VillainService(session, publisher)
        conflict_service = ConflictService(session, publisher)

        heroes = hero_service.get_heroes_for_workspace(workspace_uuid)
        villains = villain_service.get_active_villains(workspace_uuid)
        existing_conflicts = conflict_service.get_conflicts_for_workspace(
            workspace_uuid
        )

        builder = FrameworkBuilder("conflict")

        builder.set_purpose("Track narrative tension between hero and villain")

        builder.add_criteria(
            [
                "Clear hero experiencing the conflict",
                "Clear villain creating the conflict",
                "Observable impact",
                "Defined stakes (what's at risk)",
            ]
        )

        builder.add_example(
            text="Sarah cannot access product context from IDE",
            why_good="Specific conflict, clear hero/villain, observable impact, defined stakes",
            description="Sarah cannot access her product context (roadmap, initiatives, tasks) from within her IDE. This forces her to switch between VS Code and a web browser constantly, which breaks her flow state. The impact is severe: she loses focus, forgets what she was working on, and shipping slows down. The stakes are high: if this conflict isn't resolved, Sarah will abandon OpenBacklog and go back to fragmented tools. If it is resolved, she'll achieve uninterrupted flow state and ship 2x faster.",
            impact="Breaks flow state, slows development, increases frustration",
            stakes="If unresolved: abandons OpenBacklog. If resolved: achieves flow state and ships 2x faster",
        )

        builder.add_questions(
            [
                "What specific tension exists between the hero and villain?",
                "What happens because of this conflict? (impact)",
                "What's at risk if it stays unresolved? (stakes)",
                "What would success look like if resolved?",
            ]
        )

        builder.add_anti_pattern(
            example="Hero vs Villain",
            why_bad="Too vague, no specific conflict statement",
            better="Sarah cannot access product context from IDE, forcing constant tool switching",
        )

        builder.add_anti_pattern(
            example="Bad user experience",
            why_bad="No clear hero/villain, no stakes",
            better="Sarah (hero) battles Context Switching (villain) - if unresolved, she abandons the product",
        )

        builder.add_coaching_tips(
            [
                "Conflict should be specific and observable",
                "Include both impact (what happens) and stakes (what's at risk)",
                "Think about what success looks like if resolved",
                "Link conflicts to story arcs for better narrative tracking",
            ]
        )

        builder.set_conversation_guidelines(
            say_this="how this problem affects them, the tension, what's at stake",
            not_this="the Conflict, hero vs villain conflict",
            example="How does this problem actually affect Sarah's day?",
        )

        builder.add_natural_question(
            "tension",
            "How does this problem show up in their daily work?",
        )
        builder.add_natural_question(
            "impact",
            "What does this cost them? What happens because of it?",
        )
        builder.add_natural_question(
            "stakes",
            "What's at risk if this doesn't get solved?",
        )
        builder.add_natural_question(
            "resolution",
            "When this is fixed, what does their day look like instead?",
        )

        builder.add_extraction_guidance(
            from_input="Sarah loses an hour every day just switching between her IDE and the planning tool - she told me she forgets what she was doing",
            extractions={
                "hero_reference": "Sarah",
                "villain_reference": "context switching / tool switching",
                "impact": "loses an hour daily, forgets context",
                "evidence": "direct user feedback",
                "stakes": "productivity loss, frustration, potential churn",
            },
        )

        builder.add_inference_example(
            user_says="If we don't solve the feedback problem, Alex will just keep using spreadsheets and never adopt our tool",
            inferences={
                "hero": "Alex",
                "villain": "feedback fragmentation (or similar)",
                "stakes": "User won't adopt the product",
                "resolution_success": "Alex stops using spreadsheets, fully adopts tool",
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
                    "severity": villain.severity,
                }
                for villain in villains
            ],
            "existing_conflicts": [
                {
                    "id": str(conflict.id),
                    "identifier": conflict.identifier,
                    "hero_id": str(conflict.hero_id),
                    "villain_id": str(conflict.villain_id),
                    "status": conflict.status,
                }
                for conflict in existing_conflicts[:10]
            ],
            "conflict_count": len(existing_conflicts),
        }

        builder.set_current_state(current_state)

        if len(heroes) == 0:
            builder.add_context(
                "missing_hero",
                "No heroes defined yet. Create a hero first using get_hero_definition_framework()",
            )

        if len(villains) == 0:
            builder.add_context(
                "missing_villain",
                "No active villains defined yet. Create a villain first using get_villain_definition_framework()",
            )

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("conflict", str(e))
    except Exception as e:
        logger.exception(f"Error getting conflict framework: {e}")
        return build_error_response("conflict", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_conflict(
    hero_identifier: Optional[str] = None,
    villain_identifier: Optional[str] = None,
    description: Optional[str] = None,
    roadmap_theme_identifier: Optional[str] = None,
    resolved_by_initiative_identifier: Optional[str] = None,
    conflict_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update conflict (upsert: omit conflict_identifier to create, provide to update).

    IMPORTANT: Reflect conflict back to user and confirm before calling.

    Args:
        hero_identifier: Hero identifier (e.g., "H-2003")
        villain_identifier: Villain identifier (e.g., "V-2003")
        description: Conflict statement, impact, and stakes
        roadmap_theme_identifier: Theme identifier to link (e.g., "T-001")
        resolved_by_initiative_identifier: Initiative that resolved this (e.g., "I-1001")
        conflict_identifier: Conflict identifier to update (e.g., "C-001")
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        workspace_uuid = uuid.UUID(workspace_id)
        publisher = EventPublisher(session)

        # UPDATE PATH
        if conflict_identifier:
            logger.info(f"Updating conflict {conflict_identifier}")

            # Validate that at least one field is provided for update
            if (
                description is None
                and roadmap_theme_identifier is None
                and resolved_by_initiative_identifier is None
            ):
                return build_error_response(
                    "conflict",
                    "At least one field (description, roadmap_theme_identifier, resolved_by_initiative_identifier) must be provided",
                )

            conflict = (
                session.query(Conflict)
                .options(*_get_conflict_eager_load_options())
                .filter_by(identifier=conflict_identifier, workspace_id=workspace_uuid)
                .first()
            )

            if not conflict:
                return build_error_response(
                    "conflict",
                    f"Conflict with identifier '{conflict_identifier}' not found",
                )

            # Update description if provided
            final_description = (
                description if description is not None else conflict.description
            )

            # Handle roadmap theme linking
            final_roadmap_theme_id = conflict.story_arc_id
            if roadmap_theme_identifier is not None:
                if (
                    roadmap_theme_identifier.lower() == "null"
                    or roadmap_theme_identifier == ""
                ):
                    final_roadmap_theme_id = None
                else:
                    theme_uuid = resolve_theme_identifier(
                        roadmap_theme_identifier, workspace_uuid, session
                    )
                    final_roadmap_theme_id = theme_uuid

            # Update conflict
            conflict.update_conflict(
                description=final_description,
                roadmap_theme_id=final_roadmap_theme_id,
                publisher=publisher,
            )

            # Mark as resolved if initiative provided
            if resolved_by_initiative_identifier:
                initiative_uuid = resolve_initiative_identifier(
                    resolved_by_initiative_identifier, workspace_uuid, session
                )
                conflict.mark_resolved(initiative_uuid, publisher)

            session.commit()
            session.refresh(conflict)

            next_steps = [f"Conflict '{conflict.identifier}' updated successfully"]
            if roadmap_theme_identifier is not None:
                if final_roadmap_theme_id:
                    next_steps.append(f"Linked to theme {roadmap_theme_identifier}")
                else:
                    next_steps.append("Unlinked from roadmap theme")
            if resolved_by_initiative_identifier:
                next_steps.append(
                    f"Marked as resolved by initiative {resolved_by_initiative_identifier}"
                )

            return build_success_response(
                entity_type="conflict",
                message=f"Updated conflict {conflict.identifier}",
                data=serialize_conflict(conflict),
                next_steps=next_steps,
            )

        # CREATE PATH
        else:
            logger.info("Creating new conflict")

            # Validate required fields for creation
            if not hero_identifier:
                return build_error_response(
                    "conflict",
                    "hero_identifier is required for creating a new conflict",
                )
            if not villain_identifier:
                return build_error_response(
                    "conflict",
                    "villain_identifier is required for creating a new conflict",
                )
            if not description:
                return build_error_response(
                    "conflict",
                    "description is required for creating a new conflict",
                )

            hero_service = HeroService(session, publisher)
            villain_service = VillainService(session, publisher)

            hero = hero_service.get_hero_by_identifier(hero_identifier, workspace_uuid)
            villain = villain_service.get_villain_by_identifier(
                villain_identifier, workspace_uuid
            )

            # Resolve roadmap theme if provided
            roadmap_theme_uuid = None
            if roadmap_theme_identifier:
                roadmap_theme_uuid = resolve_theme_identifier(
                    roadmap_theme_identifier, workspace_uuid, session
                )

            # Create the conflict
            conflict = Conflict.create_conflict(
                workspace_id=workspace_uuid,
                user_id=uuid.UUID(user_id),
                hero_id=hero.id,
                villain_id=villain.id,
                description=description,
                roadmap_theme_id=roadmap_theme_uuid,
                session=session,
                publisher=publisher,
            )

            session.commit()

            next_steps = [
                f"Conflict created successfully with identifier {conflict.identifier}",
                f"Hero: {hero.name} ({hero_identifier}) vs Villain: {villain.name} ({villain_identifier})",
            ]

            if roadmap_theme_uuid:
                next_steps.append(
                    f"Conflict linked to roadmap theme {roadmap_theme_identifier}"
                )
            else:
                next_steps.append(
                    "Consider linking this conflict to a roadmap theme for better tracking"
                )

            next_steps.append(
                "When an initiative resolves this conflict, use submit_conflict() with resolved_by_initiative_identifier"
            )

            return build_success_response(
                entity_type="conflict",
                message="Conflict created successfully",
                data=serialize_conflict(conflict),
                next_steps=next_steps,
            )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("conflict", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("conflict", str(e))
    except MCPContextError as e:
        return build_error_response("conflict", str(e))
    except Exception as e:
        logger.exception(f"Error submitting conflict: {e}")
        return build_error_response("conflict", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def query_conflicts(
    identifier: Optional[str] = None,
    status: Optional[str] = None,
    hero_identifier: Optional[str] = None,
    villain_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Query conflicts with flexible filtering and single-entity lookup.

    Query modes:
    - No params: Returns all conflicts
    - identifier: Returns single conflict with hero/villain context
    - Filters (status, hero_identifier, villain_identifier): Can be combined

    Args:
        identifier: Conflict identifier (e.g., "C-001") for single lookup
        status: Filter by status (OPEN, ESCALATING, RESOLVING, RESOLVED)
        hero_identifier: Filter by hero identifier (e.g., "H-001")
        villain_identifier: Filter by villain identifier (e.g., "V-001")
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        publisher = EventPublisher(session)

        # SINGLE CONFLICT MODE: identifier provided
        if identifier:
            logger.info(
                f"Getting conflict '{identifier}' in workspace {workspace_uuid}"
            )

            conflict = (
                session.query(Conflict)
                .options(*_get_conflict_eager_load_options())
                .filter_by(identifier=identifier, workspace_id=workspace_uuid)
                .first()
            )

            if not conflict:
                return build_error_response(
                    "conflict",
                    f"Conflict not found: {identifier}",
                )

            return build_success_response(
                entity_type="conflict",
                message=f"Found conflict: {conflict.identifier}",
                data=serialize_conflict(conflict),
            )

        # LIST MODE: filter and return conflicts
        logger.info(
            f"Querying conflicts for workspace {workspace_uuid} "
            f"(status={status}, hero={hero_identifier}, villain={villain_identifier})"
        )

        query = (
            session.query(Conflict)
            .options(*_get_conflict_eager_load_options())
            .filter_by(workspace_id=workspace_uuid)
            .order_by(Conflict.created_at.desc())
        )

        if status:
            try:
                status_enum = ConflictStatus[status.upper()]
                query = query.filter(Conflict.status == status_enum.value)
            except KeyError:
                valid_statuses = ", ".join([cs.name for cs in ConflictStatus])
                return build_error_response(
                    "conflict",
                    f"Invalid status '{status}'. Must be one of: {valid_statuses}",
                )

        if hero_identifier:
            hero_service = HeroService(session, publisher)
            hero = hero_service.get_hero_by_identifier(hero_identifier, workspace_uuid)
            query = query.filter(Conflict.hero_id == hero.id)

        if villain_identifier:
            villain_service = VillainService(session, publisher)
            villain = villain_service.get_villain_by_identifier(
                villain_identifier, workspace_uuid
            )
            query = query.filter(Conflict.villain_id == villain.id)

        conflicts = query.all()

        # Build message based on filters applied
        filter_parts = []
        if status:
            filter_parts.append(f"status={status}")
        if hero_identifier:
            filter_parts.append(f"hero={hero_identifier}")
        if villain_identifier:
            filter_parts.append(f"villain={villain_identifier}")

        if filter_parts:
            message = f"Found {len(conflicts)} conflict(s) ({', '.join(filter_parts)})"
        else:
            message = f"Found {len(conflicts)} conflict(s)"

        return build_success_response(
            entity_type="conflict",
            message=message,
            data={
                "conflicts": [serialize_conflict(conflict) for conflict in conflicts],
            },
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("conflict", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("conflict", str(e))
    except Exception as e:
        logger.exception(f"Error querying conflicts: {e}")
        return build_error_response("conflict", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def delete_conflict(conflict_identifier: str) -> Dict[str, Any]:
    """Delete conflict permanently.

    IMPORTANT: Confirm with user BEFORE calling - cannot be undone.

    Args:
        conflict_identifier: Conflict identifier (e.g., "C-2003")
    """
    session = SessionLocal()
    try:
        _, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(
            f"Deleting conflict {conflict_identifier} for workspace {workspace_id}"
        )

        publisher = EventPublisher(session)
        conflict_service = ConflictService(session, publisher)
        conflict = conflict_service.get_conflict_by_identifier(
            conflict_identifier, uuid.UUID(workspace_id)
        )

        conflict_id = conflict.id
        session.delete(conflict)
        session.commit()

        return build_success_response(
            entity_type="conflict",
            message=f"Deleted conflict {conflict_identifier}",
            data={
                "deleted_identifier": conflict_identifier,
                "deleted_id": str(conflict_id),
            },
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("conflict", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("conflict", str(e))
    except MCPContextError as e:
        return build_error_response("conflict", str(e))
    except Exception as e:
        logger.exception(f"Error deleting conflict: {e}")
        return build_error_response("conflict", f"Server error: {str(e)}")
    finally:
        session.close()
