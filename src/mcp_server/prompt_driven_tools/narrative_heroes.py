"""Prompt-driven MCP tools for hero (user persona) management.

This module provides framework-based tools for defining heroes through
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
    serialize_hero,
    validate_hero_constraints,
)
from src.narrative.aggregates.hero import Hero
from src.narrative.exceptions import DomainException
from src.narrative.services.hero_service import HeroService
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Hero Workflow
# ============================================================================


@mcp.tool()
async def get_hero_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a hero (user persona).

    Returns rich context to help Claude Code guide the user through
    defining a high-quality hero through collaborative refinement.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary with purpose, criteria, examples, questions,
        anti-patterns, current state, and coaching tips

    Example:
        >>> framework = await get_hero_definition_framework()
        >>> # Claude Code uses framework to guide user through refinement
        >>> await submit_hero(name, description, is_primary)
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(f"Getting hero definition framework for workspace {workspace_uuid}")

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        existing_heroes = hero_service.get_heroes_for_workspace(workspace_uuid)
        primary_hero = hero_service.get_primary_hero(workspace_uuid)

        builder = FrameworkBuilder("hero")

        builder.set_purpose(
            "Define who you're building for - the protagonist of your product story"
        )

        builder.add_criteria(
            [
                "Specific person with a name, not a broad segment",
                "Real motivations that drive behavior",
                "Observable pains and frustrations",
                "Clear context where they operate",
                "Jobs to be done that your product helps with",
            ]
        )

        builder.add_example(
            text="Sarah, The Solo Builder",
            why_good="Specific person with name, clear archetype, observable context",
            description="Sarah is a solo developer building a SaaS product. She's driven by wanting to ship quality products without needing a team. Her main job is to ship features quickly while maintaining context about her product. What frustrates her most is context switching between tools that kills her flow state. Success would be staying in flow all day, with AI handling boilerplate. She works solo using Claude Code and FastAPI.",
            motivations="Ship quality products without needing a team",
            jobs_to_be_done="Ship features quickly while maintaining context",
            pains="Context switching kills flow state",
            gains_desired="Stay in flow all day, AI handles boilerplate",
            context="Building SaaS solo using Claude Code + FastAPI",
        )

        builder.add_questions(
            [
                "Who specifically are you building this for?",
                "What drives them? What do they care about?",
                "What frustrates them today?",
                "What would success look like for them?",
                "Where/how do they work?",
            ]
        )

        builder.add_anti_pattern(
            example="Developers",
            why_bad="Too broad - not a specific person",
            better="Sarah, The Solo Builder - a specific developer archetype",
        )

        builder.add_anti_pattern(
            example="People who want productivity",
            why_bad="Generic motivation, no observable context",
            better="Sarah who loses flow state when switching between IDE and planning tools",
        )

        builder.add_coaching_tips(
            [
                "Be specific - give them a name and archetype",
                "Focus on observable behaviors and real pain points",
                "Describe their context - where do they operate?",
                "Think about what success looks like from their perspective",
            ]
        )

        builder.set_conversation_guidelines(
            say_this="use their actual name (Sarah, Alex), 'your user', 'the person you're building for'",
            not_this="the Hero, your hero persona, the primary hero",
            example="Who's the one person you're building this for? Give me a specific example.",
        )

        builder.add_natural_question(
            "hero_identity",
            "Who's the one person you're building this for? Give me a real example.",
        )
        builder.add_natural_question(
            "motivations",
            "What drives them? What do they really care about?",
        )
        builder.add_natural_question(
            "pains",
            "What frustrates them most right now?",
        )
        builder.add_natural_question(
            "context",
            "Where and how do they work? What's their day like?",
        )
        builder.add_natural_question(
            "success",
            "When this works perfectly, what does their day look like?",
        )

        builder.add_extraction_guidance(
            from_input="Solo founders drowning in feedback from everywhere - Twitter, email, support tickets",
            extractions={
                "name_pattern": "[Role], The [Descriptor] → 'Alex, The Solo Founder'",
                "core_pain": "drowning in feedback = overwhelmed by scattered input",
                "context": "solo founder = works alone, limited resources",
                "sources_of_pain": "Twitter, email, support tickets = multiple channels",
            },
        )

        builder.add_inference_example(
            user_says="I keep talking to developers who lose hours every day switching between their IDE and planning tools",
            inferences={
                "hero_name": "A developer (give them a specific name like 'Sarah')",
                "pain": "loses hours to context switching",
                "context": "works in IDE, uses separate planning tools",
                "implied_villain": "Context switching between tools",
            },
        )

        current_state = {
            "existing_heroes": [
                {
                    "id": str(hero.id),
                    "identifier": hero.identifier,
                    "name": hero.name,
                    "is_primary": hero.is_primary,
                }
                for hero in existing_heroes
            ],
            "hero_count": len(existing_heroes),
            "has_primary_hero": primary_hero is not None,
            "primary_hero": (
                {
                    "id": str(primary_hero.id),
                    "identifier": primary_hero.identifier,
                    "name": primary_hero.name,
                }
                if primary_hero
                else None
            ),
        }

        builder.set_current_state(current_state)

        if primary_hero:
            builder.add_context(
                "primary_hero_note",
                f"Current primary hero: {primary_hero.name} ({primary_hero.identifier}). Setting a new hero as primary will unset this one.",
            )

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("hero", str(e))
    except Exception as e:
        logger.exception(f"Error getting hero framework: {e}")
        return build_error_response("hero", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_hero(
    name: str,
    description: Optional[str] = None,
    is_primary: bool = False,
) -> Dict[str, Any]:
    """Submit a refined hero (user persona) after collaborative definition.

    Called only when Claude Code and user have crafted a high-quality
    hero through dialogue using the framework guidance.

    IMPORTANT: Reflect the hero back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Hero name (e.g., "Sarah, The Solo Builder")
        description: Rich description including who they are, motivations,
                     jobs-to-be-done, pains, desired gains, and context
        is_primary: Whether this is the primary hero

    Returns:
        Success response with created hero

    Example:
        >>> result = await submit_hero(
        ...     name="Sarah, The Solo Builder",
        ...     description="Sarah is a solo developer...",
        ...     is_primary=True
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(f"Submitting hero for workspace {workspace_id}")

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)

        validate_hero_constraints(
            workspace_id=uuid.UUID(workspace_id),
            name=name,
            description=description,
            is_primary=is_primary,
            session=session,
        )

        if is_primary:
            existing_primary = hero_service.get_primary_hero(uuid.UUID(workspace_id))
            if existing_primary:
                existing_primary.update_hero(
                    name=existing_primary.name,
                    description=existing_primary.description,
                    is_primary=False,
                    publisher=publisher,
                )

        hero = Hero.define_hero(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            name=name,
            description=description,
            is_primary=is_primary,
            session=session,
            publisher=publisher,
        )

        session.commit()

        next_steps = [
            f"Hero '{hero.name}' created successfully with identifier {hero.identifier}",
        ]

        if is_primary:
            next_steps.append("This hero is now set as your primary hero")
        else:
            next_steps.append(
                "Consider setting a primary hero if this is your main user persona"
            )

        next_steps.extend(
            [
                "Now define a villain (problem/obstacle) using get_villain_definition_framework()",
                "Link this hero to a story arc using link_theme_to_hero()",
            ]
        )

        return build_success_response(
            entity_type="hero",
            message="Hero created successfully",
            data=serialize_hero(hero),
            next_steps=next_steps,
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("hero", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("hero", str(e))
    except MCPContextError as e:
        return build_error_response("hero", str(e))
    except Exception as e:
        logger.exception(f"Error submitting hero: {e}")
        return build_error_response("hero", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_heroes() -> Dict[str, Any]:
    """Retrieves all heroes for a workspace.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        List of heroes with full details
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(f"Getting heroes for workspace {workspace_uuid}")

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        heroes = hero_service.get_heroes_for_workspace(workspace_uuid)

        return build_success_response(
            entity_type="hero",
            message=f"Found {len(heroes)} hero(es)",
            data={
                "heroes": [serialize_hero(hero) for hero in heroes],
            },
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("hero", str(e))
    except Exception as e:
        logger.exception(f"Error getting heroes: {e}")
        return build_error_response("hero", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_hero_details(hero_identifier: str) -> Dict[str, Any]:
    """Retrieves full hero details including journey summary.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        hero_identifier: Human-readable identifier (e.g., "H-2003")

    Returns:
        Hero details + linked arcs + conflicts + journey summary
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting hero details for {hero_identifier} in workspace {workspace_uuid}"
        )

        publisher = EventPublisher(session)
        hero_service = HeroService(session, publisher)
        hero = hero_service.get_hero_by_identifier(hero_identifier, workspace_uuid)

        journey_summary = hero_service.get_hero_journey_summary(hero.id)

        hero_data = serialize_hero(hero)
        hero_data["journey_summary"] = journey_summary

        return build_success_response(
            entity_type="hero",
            message=f"Retrieved hero details for {hero.name}",
            data=hero_data,
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("hero", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("hero", str(e))
    except Exception as e:
        logger.exception(f"Error getting hero details: {e}")
        return build_error_response("hero", f"Server error: {str(e)}")
    finally:
        session.close()
