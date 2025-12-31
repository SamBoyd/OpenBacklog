"""Prompt-driven MCP tools for Strategic Pillars.

This module provides framework-based tools for defining strategic pillars
through conversational refinement.
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
    serialize_pillar,
    validate_pillar_constraints,
)
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp.tool()
async def get_pillar_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a strategic pillar.

    Strategic pillars are enduring, guiding choices that define HOW you'll achieve
    your vision. They sit between why you exist (vision) and what you'll do next
    (outcomes and roadmap). Think of them as the scaffolding of your strategy.

    Key insight: Pillars express ADVANTAGE, not activity. They explain how you'll
    differentiate and sustain value—not what you're doing this quarter.

    Time horizon: 2-4 years. Core question: "What enduring ways will we win?"

    A pillar is a durable "way of competing," not a project or metric.
    Example pillars: "Seamless Developer Flow," "AI-Native Intelligence," "Radical Simplicity."

    Returns rich context to help Claude Code guide the user through defining
    high-quality strategic pillars through collaborative refinement.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary containing:
        - purpose: Why pillars exist and what they accomplish
        - criteria: Quality standards for strong pillars (durable, differentiating, actionable)
        - examples: Strong pillar statements with strategy and anti-strategy
        - questions: Discovery and validation questions for refinement
        - anti_patterns: Common mistakes (too tactical, too generic, departmental)
        - coaching_tips: Guidance for writing belief-style, testable pillars
        - conversation_guidelines: How to discuss pillars in natural language
        - natural_questions: Framework terms mapped to conversational questions
        - extraction_guidance: Patterns for parsing user input into pillar components
        - inference_examples: How to infer pillars from indirect user statements
        - current_state: Existing pillars (max 5 allowed)

    Example:
        >>> framework = await get_pillar_definition_framework()
        >>> # Use natural_questions to guide conversation about differentiation
        >>> # Use extraction_guidance to parse user's strategic choices
        >>> # Draft pillar and reflect back as a belief statement
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

        builder.set_purpose(
            "Define your enduring ways of winning—the strategic choices that "
            "shape all decisions and differentiate you from competitors. "
            "Pillars are lenses for prioritization: they say 'this is how we "
            "will win, and what we will never compromise.'"
        )

        # Criteria based on the 6 attributes from detailed docs
        builder.add_criteria(
            [
                "Durable: Lasts for years, not tied to a specific initiative or trend",
                "Differentiating: Captures a way of winning distinct from competitors",
                "Actionable: Guides trade-offs—you can use it to say 'yes' or 'no'",
                "User-oriented: About value created for users, not internal goals",
                "Emotionally resonant: Can be remembered and repeated like a belief",
                "Has explicit anti-strategy: What you WON'T do to maintain focus",
            ]
        )

        # Examples written as belief statements with clear anti-strategies
        builder.add_example(
            text="Seamless Developer Flow",
            why_good="Durable (will matter for years), differentiating (explicit rejection of context-switching), actionable (guides feature decisions)",
            description=(
                "**Belief**: We believe developers do their best work when they stay in flow. "
                "**Strategy**: Remove all friction between code and backlog; keep developers in their IDE. "
                "**Anti-Strategy**: No web-first dashboards, no mobile apps, no Slack/Teams bots that pull attention away."
            ),
        )

        builder.add_example(
            text="Radical Simplicity",
            why_good="Makes competitors' complexity a disadvantage, guides clear 'no' decisions, memorable",
            description=(
                "**Belief**: We believe clarity beats capability—fewer features, done brilliantly. "
                "**Strategy**: Prioritize speed and focus; fewer clicks, fewer decisions, faster outcomes. "
                "**Anti-Strategy**: No enterprise admin panels, no complex permissions, no feature bloat to satisfy edge cases."
            ),
        )

        builder.add_example(
            text="AI-Native Guidance",
            why_good="Positions AI as foundation not feature, differentiates from 'AI-added' competitors",
            description=(
                "**Belief**: We believe AI should guide the entire product journey, not just assist with tasks. "
                "**Strategy**: Infuse intelligence into every workflow—AI owns the PM function solo developers lack. "
                "**Anti-Strategy**: No 'AI features' bolted on; no AI that requires user prompting to be useful."
            ),
        )

        # Discovery and validation questions
        builder.add_questions(
            [
                # Discovery questions
                "What's your unique approach that competitors won't copy?",
                "What will you explicitly NOT do to maintain this focus?",
                "What are you trading off by making this bet?",
                "If you had to pick only 3 things to be world-class at, is this one?",
                # Validation questions (from docs)
                "Is this a durable way of winning, not just an activity?",
                "Would competitors plausibly make a different choice?",
                "Does this help you decide between two competing features?",
                "Will this still be relevant in 2-3 years?",
                "Can you remember and apply this without looking it up?",
            ]
        )

        # Anti-patterns from detailed docs
        builder.add_anti_pattern(
            example="Launch AI features",
            why_bad="Too tactical—this is a project, not a way of competing",
            better="AI-Native Guidance: Infuse AI into core workflows that reduce cognitive load",
        )

        builder.add_anti_pattern(
            example="Innovation",
            why_bad="Too generic—any company could say this, provides no differentiation",
            better="Fast Experimentation: Ship MVPs in days, validate in weeks, kill or scale in months",
        )

        builder.add_anti_pattern(
            example="Quality - We build high-quality products",
            why_bad="Not testable—everyone claims quality, can't use it to make decisions",
            better="Enterprise-Grade Reliability: 99.99% uptime SLA, zero-data-loss guarantee",
        )

        builder.add_anti_pattern(
            example="Engineering Excellence",
            why_bad="Departmental—describes a function, not a strategic lever",
            better="Close to the Code: Project management feels like part of development, not apart from it",
        )

        builder.add_anti_pattern(
            example="Improve developer experience",
            why_bad="Too short-term—will expire within a product cycle, not a lasting advantage",
            better="Developer-First Design: Every decision optimizes for the individual developer, never the buyer or admin",
        )

        # Coaching tips from docs
        builder.add_coaching_tips(
            [
                "Start from contrast: Define what you WON'T do (anti-strategy) before what you will",
                "Write them like beliefs: 'We believe that...' makes pillars more durable and human",
                "Make them testable: Ask 'Would this help us decide between two competing initiatives?'",
                "Limit to 3-5: Enough to guide trade-offs, few enough to remember",
                "Good anti-strategy feels uncomfortable—if it doesn't hurt to say no, it's not a real trade-off",
                "Revisit for clarity, not change: If you're changing pillars often, they weren't strategic",
            ]
        )

        # === Natural Language Mapping Guidance ===
        builder.set_conversation_guidelines(
            say_this=(
                "your approach, what makes you different, your strategic bet, "
                "your way of winning, what you believe about how to succeed"
            ),
            not_this="Strategic Pillar, the pillar, this strategic element",
            example=(
                "Instead of 'Let's define a Strategic Pillar,' say: "
                "'What's your unique approach here—something competitors won't copy? "
                "And what will you explicitly NOT do to maintain that focus?'"
            ),
        )

        # Natural questions mapped from framework concepts
        builder.add_natural_question(
            "pillar_discovery",
            "What makes your approach unique? What would competitors have to change about themselves to copy you?",
        )
        builder.add_natural_question(
            "anti_strategy",
            "What will you explicitly NOT do to stay focused? What opportunities will you walk away from?",
        )
        builder.add_natural_question(
            "trade_offs",
            "What are you giving up by making this bet? Who won't you serve?",
        )
        builder.add_natural_question(
            "belief_framing",
            "How would you complete this sentence: 'We believe that...'?",
        )
        builder.add_natural_question(
            "decision_test",
            "If you had to choose between two features and could only pick one, how would this help you decide?",
        )
        builder.add_natural_question(
            "durability_test",
            "Will this still matter in 3 years, or is it tied to something that might change?",
        )

        # Extraction guidance for parsing user input
        builder.add_extraction_guidance(
            from_input="We're betting everything on the IDE - no web app, no mobile, just pure IDE integration",
            extractions={
                "pillar_name": "Seamless Developer Flow (or: IDE-Native Experience)",
                "belief": "We believe developers do their best work in their IDE",
                "strategy": "Pure IDE integration, zero context-switching",
                "anti_strategy": "No web app, no mobile app, no external dashboards",
                "trade_off": "Users who want web/mobile access won't be served",
                "validation": "Durable (IDEs aren't going away), Differentiating (most tools are web-first)",
            },
        )

        builder.add_extraction_guidance(
            from_input="We want to be stupid simple - no enterprise features, no complex permissions, just get stuff done",
            extractions={
                "pillar_name": "Radical Simplicity",
                "belief": "We believe clarity beats capability",
                "strategy": "Fewer features done brilliantly, minimal decisions required",
                "anti_strategy": "No enterprise admin, no complex permissions, no audit logs",
                "trade_off": "Enterprise buyers and compliance-heavy orgs won't choose us",
                "validation": "Actionable (can say no to feature requests), Emotionally resonant (memorable)",
            },
        )

        # Inference examples for indirect statements
        builder.add_inference_example(
            user_says="We want to be the simplest option - no enterprise features, no complex setup",
            inferences={
                "pillar": "Radical Simplicity",
                "belief": "Clarity and speed beat feature completeness",
                "anti_strategy": "No enterprise features, no complex configuration",
                "implied_outcome": "Faster onboarding, higher individual adoption",
                "follow_up": "What complexity will you refuse to add, even if customers ask for it?",
            },
        )

        builder.add_inference_example(
            user_says="AI should do the PM work that solo developers can't do themselves",
            inferences={
                "pillar": "AI-Native Guidance",
                "belief": "Solo developers deserve PM capabilities once reserved for teams",
                "strategy": "AI owns the PM function—not as assistant, but as active guide",
                "implied_anti_strategy": "No AI that just responds to prompts; AI should proactively guide",
                "follow_up": "What PM decisions should AI make vs. suggest vs. leave to the user?",
            },
        )

        builder.add_inference_example(
            user_says="We integrate with everything—IDEs, GitHub, AI tools—we're the connective tissue",
            inferences={
                "pillar": "Ecosystem Integration",
                "belief": "We win by being the most connected, not the most complete",
                "strategy": "Seamless integration with best-in-class tools in every category",
                "anti_strategy": "No building features that duplicate what integrated tools do well",
                "implied_trade_off": "Dependent on third-party tools; can't control full experience",
                "follow_up": "What happens if a key integration partner becomes a competitor?",
            },
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
async def query_strategic_pillars(
    identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Query strategic pillars with optional single-entity lookup.

    A unified query tool that replaces get_strategic_pillars and get_strategic_pillar_details.

    **Query modes:**
    - No params: Returns all strategic pillars
    - identifier: Returns single pillar with linked outcomes

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        identifier: Pillar identifier (e.g., "P-001") for single lookup

    Returns:
        For single: pillar details with linked_outcomes
        For list: array of pillars

    Examples:
        >>> # Get all pillars
        >>> await query_strategic_pillars()

        >>> # Get single pillar by identifier
        >>> await query_strategic_pillars(identifier="P-001")
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # SINGLE PILLAR MODE: identifier provided
        if identifier:
            logger.info(
                f"Getting strategic pillar '{identifier}' in workspace {workspace_uuid}"
            )

            pillar = (
                session.query(StrategicPillar)
                .filter_by(identifier=identifier, workspace_id=workspace_uuid)
                .first()
            )

            if not pillar:
                return build_error_response(
                    "pillar", f"Strategic pillar not found: {identifier}"
                )

            from src.mcp_server.prompt_driven_tools.utils import serialize_outcome

            pillar_data = serialize_pillar(pillar)
            pillar_data["linked_outcomes"] = [
                serialize_outcome(outcome) for outcome in pillar.outcomes
            ]

            return build_success_response(
                entity_type="pillar",
                message=f"Found strategic pillar: {pillar.name}",
                data=pillar_data,
            )

        # LIST MODE: return all pillars
        logger.info(f"Getting all strategic pillars for workspace {workspace_uuid}")

        pillars = strategic_controller.get_strategic_pillars(workspace_uuid, session)

        return build_success_response(
            entity_type="pillar",
            message=f"Found {len(pillars)} strategic pillar(s)",
            data={
                "pillars": [serialize_pillar(pillar) for pillar in pillars],
            },
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("pillar", str(e))
    except Exception as e:
        logger.exception(f"Error querying strategic pillars: {e}")
        return build_error_response("pillar", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_strategic_pillar(
    name: str,
    description: str,
    pillar_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a refined strategic pillar - creates new or updates existing.

    UPSERT PATTERN:
    - If pillar_identifier is None: Creates a new pillar
    - If pillar_identifier is provided: Updates the existing pillar

    Called only when Claude Code and user have crafted a high-quality
    pillar through dialogue using the framework guidance.

    IMPORTANT: Reflect the pillar back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Pillar name (1-100 characters, unique per workspace)
        description: Pillar description including strategy and anti-strategy (required)
                    Should include both what you'll do and what you won't do
        pillar_identifier: If provided, updates existing pillar instead of creating

    Returns:
        Success response with created or updated pillar

    Example (Create):
        >>> result = await submit_strategic_pillar(
        ...     name="Deep IDE Integration",
        ...     description="Strategy: Seamless developer workflow. Anti-Strategy: No web/mobile."
        ... )

    Example (Update):
        >>> result = await submit_strategic_pillar(
        ...     pillar_identifier="P-001",
        ...     name="Deep IDE Integration (Updated)",
        ...     description="Updated strategy..."
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        workspace_uuid = uuid.UUID(workspace_id)
        logger.info(f"Submitting strategic pillar for workspace {workspace_id}")

        if pillar_identifier:
            # UPDATE PATH
            logger.info(f"Updating pillar {pillar_identifier}")
            pillar = (
                session.query(StrategicPillar)
                .filter_by(identifier=pillar_identifier, workspace_id=workspace_uuid)
                .first()
            )

            if not pillar:
                return build_error_response(
                    "pillar", f"Strategic pillar {pillar_identifier} not found"
                )

            # Merge fields
            final_name = name if name is not None else pillar.name
            final_description = (
                description if description is not None else pillar.description
            )

            # Only validate if name changed (to avoid uniqueness check on same name)
            if final_name != pillar.name:
                validate_pillar_constraints(
                    workspace_id=workspace_uuid,
                    name=final_name,
                    description=final_description,
                    session=session,
                )
            else:
                # Only validate description format when name hasn't changed
                StrategicPillar._validate_description(final_description)  # type: ignore[attr-defined]

            publisher = EventPublisher(session)
            pillar.update_pillar(
                name=final_name,
                description=final_description,
                publisher=publisher,
            )

            session.commit()
            session.refresh(pillar)

            return build_success_response(
                entity_type="pillar",
                message=f"Updated strategic pillar '{pillar.name}'",
                data=serialize_pillar(pillar),
            )

        else:
            # CREATE PATH
            logger.info("Creating new pillar")
            validate_pillar_constraints(
                workspace_id=workspace_uuid,
                name=name,
                description=description,
                session=session,
            )

            pillar = strategic_controller.create_strategic_pillar(
                workspace_id=workspace_uuid,
                user_id=uuid.UUID(user_id),
                name=name,
                description=description,
                session=session,
            )

            # Build success response with next steps
            all_pillars = strategic_controller.get_strategic_pillars(
                workspace_uuid, session
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


@mcp.tool()
async def delete_strategic_pillar(pillar_identifier: str) -> Dict[str, Any]:
    """Delete a strategic pillar permanently.

    IMPORTANT: Confirm with user BEFORE calling - this action cannot be undone.
    This will also unlink the pillar from any associated outcomes and initiatives.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        pillar_identifier: Human-readable identifier of the strategic pillar to delete (e.g., "P-001")

    Returns:
        Success response confirming deletion

    Example:
        >>> result = await delete_strategic_pillar(pillar_identifier="P-001")
    """
    session = SessionLocal()
    try:
        _, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(
            f"Deleting strategic pillar {pillar_identifier} for workspace {workspace_id}"
        )

        workspace_uuid = uuid.UUID(workspace_id)

        pillar = (
            session.query(StrategicPillar)
            .filter_by(identifier=pillar_identifier, workspace_id=workspace_uuid)
            .first()
        )

        if not pillar:
            return build_error_response(
                "pillar", f"Strategic pillar {pillar_identifier} not found"
            )

        pillar_name = pillar.name
        user_id, _ = get_auth_context(session, requires_workspace=True)

        strategic_controller.delete_strategic_pillar(
            pillar_id=pillar.id,
            workspace_id=workspace_uuid,
            user_id=uuid.UUID(user_id),
            session=session,
        )

        return build_success_response(
            entity_type="pillar",
            message=f"Deleted strategic pillar '{pillar_name}'",
            data={"deleted_identifier": pillar_identifier},
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("pillar", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("pillar", str(e))
    except MCPContextError as e:
        return build_error_response("pillar", str(e))
    except Exception as e:
        logger.exception(f"Error deleting strategic pillar: {e}")
        return build_error_response("pillar", f"Server error: {str(e)}")
    finally:
        session.close()
