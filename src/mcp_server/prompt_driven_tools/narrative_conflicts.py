"""Prompt-driven MCP tools for conflict management.

This module provides framework-based tools for creating and managing conflicts
between heroes and villains through conversational refinement.

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
    get_workspace_id_from_request,
    serialize_conflict,
)
from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.exceptions import DomainException
from src.narrative.services.conflict_service import ConflictService
from src.narrative.services.hero_service import HeroService
from src.narrative.services.villain_service import VillainService
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Conflict Workflow
# ============================================================================


@mcp.tool()
async def get_conflict_creation_framework() -> Dict[str, Any]:
    """Get comprehensive framework for creating a conflict.

    Returns rich context to help Claude Code guide the user through
    creating a high-quality conflict between a hero and villain.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary with purpose, criteria, examples, questions,
        anti-patterns, current state (available heroes/villains), and coaching tips

    Example:
        >>> framework = await get_conflict_creation_framework()
        >>> # Claude Code uses framework to guide user through refinement
        >>> await create_conflict(hero_identifier, villain_identifier, description)
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
async def create_conflict(
    hero_identifier: str,
    villain_identifier: str,
    description: str,
    story_arc_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Creates a new conflict between a hero and villain.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        hero_identifier: Human-readable hero identifier (e.g., "H-2003")
        villain_identifier: Human-readable villain identifier (e.g., "V-2003")
        description: Rich description including conflict statement, impact, and stakes
        story_arc_id: Optional UUID of story arc addressing this conflict

    Returns:
        Success response with created conflict (including identifier like "C-2003")

    Example:
        >>> result = await create_conflict(
        ...     hero_identifier="H-2003",
        ...     villain_identifier="V-2003",
        ...     description="Sarah cannot access product context from IDE...",
        ...     story_arc_id="..."
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(f"Creating conflict for workspace {workspace_id}")

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        villain_service = VillainService(session, publisher)

        hero = hero_service.get_hero_by_identifier(
            hero_identifier, uuid.UUID(workspace_id)
        )
        villain = villain_service.get_villain_by_identifier(
            villain_identifier, uuid.UUID(workspace_id)
        )

        story_arc_uuid = None
        if story_arc_id:
            try:
                story_arc_uuid = uuid.UUID(story_arc_id)
            except ValueError:
                return build_error_response(
                    "conflict", f"Invalid story_arc_id format: {story_arc_id}"
                )

        conflict = Conflict.create_conflict(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            hero_id=hero.id,
            villain_id=villain.id,
            description=description,
            story_arc_id=story_arc_uuid,
            session=session,
            publisher=publisher,
        )

        session.commit()

        next_steps = [
            f"Conflict created successfully with identifier {conflict.identifier}",
            f"Hero: {hero.name} ({hero_identifier}) vs Villain: {villain.name} ({villain_identifier})",
        ]

        if story_arc_id:
            next_steps.append(f"Conflict linked to story arc {story_arc_id}")
        else:
            next_steps.append(
                "Consider linking this conflict to a story arc for better tracking"
            )

        next_steps.append(
            "When an initiative resolves this conflict, use mark_conflict_resolved()"
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
        logger.exception(f"Error creating conflict: {e}")
        return build_error_response("conflict", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_conflicts(
    status: Optional[str] = None,
    hero_identifier: Optional[str] = None,
    villain_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves conflicts with optional filtering.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        status: Optional filter by status (OPEN, ESCALATING, RESOLVING, RESOLVED)
        hero_identifier: Optional filter by hero identifier (e.g., "H-2003")
        villain_identifier: Optional filter by villain identifier (e.g., "V-2003")

    Returns:
        List of conflicts matching filters
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(f"Getting conflicts for workspace {workspace_uuid}")

        publisher = EventPublisher(session)
        conflict_service = ConflictService(session, publisher)

        conflicts = conflict_service.get_conflicts_for_workspace(workspace_uuid)

        if status:
            try:
                status_enum = ConflictStatus[status.upper()]
                conflicts = [c for c in conflicts if c.status == status_enum.value]
            except KeyError:
                valid_statuses = ", ".join([cs.name for cs in ConflictStatus])
                return build_error_response(
                    "conflict",
                    f"Invalid status '{status}'. Must be one of: {valid_statuses}",
                )

        if hero_identifier:
            hero_service = HeroService(session, publisher)
            hero = hero_service.get_hero_by_identifier(hero_identifier, workspace_uuid)
            conflicts = [c for c in conflicts if c.hero_id == hero.id]

        if villain_identifier:
            villain_service = VillainService(session, publisher)
            villain = villain_service.get_villain_by_identifier(
                villain_identifier, workspace_uuid
            )
            conflicts = [c for c in conflicts if c.villain_id == villain.id]

        return build_success_response(
            entity_type="conflict",
            message=f"Found {len(conflicts)} conflict(s)",
            data=[serialize_conflict(conflict) for conflict in conflicts],
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("conflict", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("conflict", str(e))
    except Exception as e:
        logger.exception(f"Error getting conflicts: {e}")
        return build_error_response("conflict", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def mark_conflict_resolved(
    conflict_identifier: str,
    resolved_by_initiative_id: str,
) -> Dict[str, Any]:
    """Marks a conflict as resolved by an initiative.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        conflict_identifier: Human-readable conflict identifier (e.g., "C-2003")
        resolved_by_initiative_id: UUID of initiative that resolved it

    Returns:
        Success response with updated conflict
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Marking conflict {conflict_identifier} as resolved in workspace {workspace_uuid}"
        )

        publisher = EventPublisher(session)
        conflict_service = ConflictService(session, publisher)
        conflict = conflict_service.get_conflict_by_identifier(
            conflict_identifier, workspace_uuid
        )

        if conflict.status == ConflictStatus.RESOLVED:
            return build_error_response(
                "conflict", f"Conflict {conflict_identifier} is already resolved"
            )

        try:
            initiative_uuid = uuid.UUID(resolved_by_initiative_id)
        except ValueError:
            return build_error_response(
                "conflict",
                f"Invalid resolved_by_initiative_id format: {resolved_by_initiative_id}",
            )

        conflict.mark_resolved(initiative_uuid, publisher)
        session.commit()

        return build_success_response(
            entity_type="conflict",
            message=f"Conflict '{conflict.identifier}' marked as resolved",
            data=serialize_conflict(conflict),
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("conflict", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("conflict", str(e))
    except Exception as e:
        logger.exception(f"Error marking conflict resolved: {e}")
        return build_error_response("conflict", f"Server error: {str(e)}")
    finally:
        session.close()
