"""Prompt-driven MCP tools for villain (problem/obstacle) management.

This module provides framework-based tools for defining villains through
conversational refinement rather than rigid forms.

Pattern: Get Framework → Claude + User Collaborate → Submit Result
"""

import logging
import uuid
from typing import Any, Dict, Optional

from src.db import SessionLocal
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.utils import (
    FrameworkBuilder,
    build_error_response,
    build_success_response,
    get_workspace_id_from_request,
    serialize_villain,
    validate_villain_constraints,
)
from src.narrative.aggregates.villain import Villain, VillainType
from src.narrative.exceptions import DomainException
from src.narrative.services.villain_service import VillainService
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Villain Workflow
# ============================================================================


@mcp.tool()
async def get_villain_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a villain (problem/obstacle).

    Returns rich context to help Claude Code guide the user through
    defining a high-quality villain through collaborative refinement.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary with purpose, criteria, examples, questions,
        anti-patterns, current state, and coaching tips

    Example:
        >>> framework = await get_villain_definition_framework()
        >>> # Claude Code uses framework to guide user through refinement
        >>> await submit_villain(name, villain_type, description, severity)
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting villain definition framework for workspace {workspace_uuid}"
        )

        publisher = EventPublisher(session)
        villain_service = VillainService(session, publisher)
        existing_villains = villain_service.get_villains_for_workspace(workspace_uuid)
        active_villains = villain_service.get_active_villains(workspace_uuid)

        builder = FrameworkBuilder("villain")

        builder.set_purpose("Identify the forces opposing your hero's success")

        builder.add_criteria(
            [
                "Specific problem, not generic",
                "Observable impact on hero",
                "Evidence that it exists",
                "Clear severity assessment",
            ]
        )

        builder.add_example(
            text="Context Switching",
            why_good="Specific, observable, has evidence, clear impact",
            villain_type="WORKFLOW",
            description="Jumping between IDE, docs, planning tool breaks flow",
            impact="Reduces focus, slows shipping, increases cognitive load",
            evidence="User feedback: 'I lose track of what I was doing'",
            severity=5,
        )

        builder.add_questions(
            [
                "What specific problem is blocking your hero?",
                "How does this obstacle manifest?",
                "What impact does it have on the hero?",
                "What evidence shows this problem exists?",
                "How severe is this problem? (1-5)",
            ]
        )

        builder.add_anti_pattern(
            example="Bad UX",
            why_bad="Too vague, no specific manifestation",
            better="Context switching between tools breaks flow state",
        )

        builder.add_anti_pattern(
            example="Competitors",
            why_bad="Too broad, not a specific obstacle",
            better="Competitor X's feature Y prevents user adoption",
        )

        builder.add_coaching_tips(
            [
                "Be specific about how the problem manifests",
                "Focus on observable impact, not assumptions",
                "Include evidence if available (user feedback, metrics)",
                "Severity should reflect real impact on hero",
            ]
        )

        villain_types_info = {
            "EXTERNAL": "Competitor products, market forces",
            "INTERNAL": "Cognitive overload, lack of knowledge",
            "TECHNICAL": "Bugs, system limitations, tech debt",
            "WORKFLOW": "Difficult processes, tool switching",
            "OTHER": "Other obstacles",
        }

        builder.add_context("villain_types", villain_types_info)

        builder.set_conversation_guidelines(
            say_this="the problem, what's blocking them, the friction, the obstacle",
            not_this="the Villain, your villain, the enemy",
            example="What's the biggest thing blocking them today?",
        )

        builder.add_natural_question(
            "problem_identification",
            "What's the biggest thing blocking them right now?",
        )
        builder.add_natural_question(
            "manifestation",
            "How does this show up in their day? What does it look like?",
        )
        builder.add_natural_question(
            "impact",
            "What does this cost them? Time? Money? Frustration?",
        )
        builder.add_natural_question(
            "evidence",
            "How do you know this is a real problem? What have you seen or heard?",
        )

        builder.add_extraction_guidance(
            from_input="They keep telling me they lose track of what they were doing when they switch between tools",
            extractions={
                "villain_name": "Context Switching",
                "villain_type": "WORKFLOW",
                "manifestation": "Switching between tools causes loss of mental context",
                "evidence": "Direct user feedback about losing track",
                "implied_impact": "Lost productivity, frustration, slower shipping",
            },
        )

        builder.add_inference_example(
            user_says="Feedback comes from everywhere - Twitter, email, support - and they can't make sense of it all",
            inferences={
                "villain": "Scattered Feedback",
                "type": "WORKFLOW",
                "impact": "Can't synthesize insights, decision paralysis",
                "implied_hero_pain": "Overwhelmed by multiple input channels",
            },
        )

        current_state = {
            "existing_villains": [
                {
                    "id": str(villain.id),
                    "identifier": villain.identifier,
                    "name": villain.name,
                    "villain_type": villain.villain_type,
                    "severity": villain.severity,
                    "is_defeated": villain.is_defeated,
                }
                for villain in existing_villains
            ],
            "villain_count": len(existing_villains),
            "active_villain_count": len(active_villains),
            "defeated_count": len(existing_villains) - len(active_villains),
        }

        builder.set_current_state(current_state)

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("villain", str(e))
    except Exception as e:
        logger.exception(f"Error getting villain framework: {e}")
        return build_error_response("villain", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_villain(
    name: str,
    villain_type: str,
    description: str,
    severity: int,
) -> Dict[str, Any]:
    """Submit a refined villain (problem/obstacle) after collaborative definition.

    Called only when Claude Code and user have crafted a high-quality
    villain through dialogue using the framework guidance.

    IMPORTANT: Reflect the villain back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Villain name (e.g., "Context Switching")
        villain_type: Type (EXTERNAL, INTERNAL, TECHNICAL, WORKFLOW, OTHER)
        description: Rich description including how it manifests, impact, and evidence
        severity: How big a threat (1-5)

    Returns:
        Success response with created villain

    Example:
        >>> result = await submit_villain(
        ...     name="Context Switching",
        ...     villain_type="WORKFLOW",
        ...     description="Jumping between tools breaks flow...",
        ...     severity=5
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(f"Submitting villain for workspace {workspace_id}")

        try:
            villain_type_enum = VillainType[villain_type.upper()]
        except KeyError:
            valid_types = ", ".join([vt.name for vt in VillainType])
            return build_error_response(
                "villain",
                f"Invalid villain_type '{villain_type}'. Must be one of: {valid_types}",
            )

        validate_villain_constraints(
            workspace_id=uuid.UUID(workspace_id),
            name=name,
            villain_type=villain_type,
            description=description,
            severity=severity,
            session=session,
        )

        publisher = EventPublisher(session)
        villain = Villain.define_villain(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            name=name,
            villain_type=villain_type_enum,
            description=description,
            severity=severity,
            session=session,
            publisher=publisher,
        )

        session.commit()

        next_steps = [
            f"Villain '{villain.name}' created successfully with identifier {villain.identifier}",
            "Link this villain to a hero to create a conflict using create_conflict()",
            "Link this villain to a story arc using link_theme_to_villain()",
        ]

        return build_success_response(
            entity_type="villain",
            message="Villain created successfully",
            data=serialize_villain(villain),
            next_steps=next_steps,
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("villain", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("villain", str(e))
    except MCPContextError as e:
        return build_error_response("villain", str(e))
    except Exception as e:
        logger.exception(f"Error submitting villain: {e}")
        return build_error_response("villain", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_villains() -> Dict[str, Any]:
    """Retrieves all villains for a workspace.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        List of villains with full details
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(f"Getting villains for workspace {workspace_uuid}")

        publisher = EventPublisher(session)
        villain_service = VillainService(session, publisher)
        villains = villain_service.get_villains_for_workspace(workspace_uuid)

        return build_success_response(
            entity_type="villain",
            message=f"Found {len(villains)} villain(s)",
            data={
                "villains": [serialize_villain(villain) for villain in villains],
            },
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("villain", str(e))
    except Exception as e:
        logger.exception(f"Error getting villains: {e}")
        return build_error_response("villain", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_villain_details(villain_identifier: str) -> Dict[str, Any]:
    """Retrieves full villain details including battle summary.

    Returns enriched villain data including counts of conflicts,
    linked themes, and initiatives confronting this villain.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        villain_identifier: Human-readable identifier (e.g., "V-2003")

    Returns:
        Villain details + battle summary (conflicts, themes, initiatives)

    Example:
        >>> result = await get_villain_details(villain_identifier="V-2003")
        >>> print(result["data"]["battle_summary"])
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting villain details for {villain_identifier} in workspace {workspace_uuid}"
        )

        publisher = EventPublisher(session)
        villain_service = VillainService(session, publisher)
        villain = villain_service.get_villain_by_identifier(
            villain_identifier, workspace_uuid
        )

        battle_summary = villain_service.get_villain_battle_summary(villain.id)

        villain_data = serialize_villain(villain)
        villain_data["battle_summary"] = battle_summary

        return build_success_response(
            entity_type="villain",
            message=f"Retrieved villain details for {villain.name}",
            data=villain_data,
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("villain", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("villain", str(e))
    except Exception as e:
        logger.exception(f"Error getting villain details: {e}")
        return build_error_response("villain", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def mark_villain_defeated(villain_identifier: str) -> Dict[str, Any]:
    """Marks a villain as defeated.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        villain_identifier: Human-readable identifier (e.g., "V-2003")

    Returns:
        Success response with updated villain
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Marking villain {villain_identifier} as defeated in workspace {workspace_uuid}"
        )

        publisher = EventPublisher(session)
        villain_service = VillainService(session, publisher)
        villain = villain_service.get_villain_by_identifier(
            villain_identifier, workspace_uuid
        )

        if villain.is_defeated:
            return build_error_response(
                "villain", f"Villain {villain_identifier} is already defeated"
            )

        villain.mark_defeated(publisher)
        session.commit()

        return build_success_response(
            entity_type="villain",
            message=f"Villain '{villain.name}' marked as defeated",
            data=serialize_villain(villain),
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("villain", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("villain", str(e))
    except Exception as e:
        logger.exception(f"Error marking villain defeated: {e}")
        return build_error_response("villain", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def update_villain(
    villain_identifier: str,
    name: Optional[str] = None,
    villain_type: Optional[str] = None,
    description: Optional[str] = None,
    severity: Optional[int] = None,
    is_defeated: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update an existing villain's fields.

    IMPORTANT: Reflect the changes back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        villain_identifier: Human-readable identifier (e.g., "V-2003")
        name: New villain name (optional)
        villain_type: New type (EXTERNAL, INTERNAL, TECHNICAL, WORKFLOW, OTHER) (optional)
        description: New villain description (optional)
        severity: New severity 1-5 (optional)
        is_defeated: Whether the villain is defeated (optional)

    Returns:
        Success response with updated villain

    Example:
        >>> result = await update_villain(
        ...     villain_identifier="V-2003",
        ...     name="Context Switching (Updated)",
        ...     severity=4,
        ... )
    """
    session = SessionLocal()
    try:
        _, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(
            f"Updating villain {villain_identifier} for workspace {workspace_id}"
        )

        if (
            name is None
            and villain_type is None
            and description is None
            and severity is None
            and is_defeated is None
        ):
            return build_error_response(
                "villain",
                "At least one field (name, villain_type, description, severity) must be provided",
            )

        publisher = EventPublisher(session)
        villain_service = VillainService(session, publisher)
        villain = villain_service.get_villain_by_identifier(
            villain_identifier, uuid.UUID(workspace_id)
        )

        final_name = name if name is not None else villain.name
        final_description = (
            description if description is not None else villain.description
        )
        final_severity = severity if severity is not None else villain.severity
        final_is_defeated = (
            is_defeated if is_defeated is not None else villain.is_defeated
        )

        if villain_type is not None:
            try:
                final_villain_type = VillainType[villain_type.upper()]
            except KeyError:
                valid_types = ", ".join([vt.name for vt in VillainType])
                return build_error_response(
                    "villain",
                    f"Invalid villain_type '{villain_type}'. Must be one of: {valid_types}",
                )
        else:
            final_villain_type = VillainType[villain.villain_type]

        villain.update_villain(
            name=final_name,
            villain_type=final_villain_type,
            description=final_description,
            severity=final_severity,
            is_defeated=final_is_defeated,
            publisher=publisher,
        )
        session.add(villain)
        session.commit()
        session.refresh(villain)

        return build_success_response(
            entity_type="villain",
            message=f"Updated villain {villain.identifier}",
            data=serialize_villain(villain),
            next_steps=[
                f"Villain '{villain.name}' ({villain.identifier}) updated successfully"
            ],
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("villain", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("villain", str(e))
    except MCPContextError as e:
        return build_error_response("villain", str(e))
    except Exception as e:
        logger.exception(f"Error updating villain: {e}")
        return build_error_response("villain", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def delete_villain(villain_identifier: str) -> Dict[str, Any]:
    """Delete a villain permanently.

    IMPORTANT: Confirm with user BEFORE calling - this action cannot be undone.
    This will also remove the villain from any linked conflicts and story arcs.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        villain_identifier: Human-readable identifier (e.g., "V-2003")

    Returns:
        Success response confirming deletion

    Example:
        >>> result = await delete_villain(villain_identifier="V-2003")
    """
    session = SessionLocal()
    try:
        _, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(
            f"Deleting villain {villain_identifier} for workspace {workspace_id}"
        )

        publisher = EventPublisher(session)
        villain_service = VillainService(session, publisher)
        villain = villain_service.get_villain_by_identifier(
            villain_identifier, uuid.UUID(workspace_id)
        )

        villain_name = villain.name
        villain_id = str(villain.id)

        session.delete(villain)
        session.commit()

        return build_success_response(
            entity_type="villain",
            message=f"Deleted villain {villain_identifier} ({villain_name})",
            data={"deleted_identifier": villain_identifier, "deleted_id": villain_id},
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("villain", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("villain", str(e))
    except MCPContextError as e:
        return build_error_response("villain", str(e))
    except Exception as e:
        logger.exception(f"Error deleting villain: {e}")
        return build_error_response("villain", f"Server error: {str(e)}")
    finally:
        session.close()
