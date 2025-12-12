"""Prompt-driven MCP tools for Product Vision.

This module provides framework-based tools for defining product vision
through conversational refinement.

"""

import logging
import uuid
from typing import Any, Dict

from src.db import SessionLocal
from src.mcp_server.auth_utils import MCPContextError, get_auth_context
from src.mcp_server.main import mcp
from src.mcp_server.prompt_driven_tools.utils import (
    FrameworkBuilder,
    build_error_response,
    build_success_response,
    get_workspace_id_from_request,
    serialize_vision,
    validate_vision_constraints,
)
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.exceptions import DomainException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Vision Workflow
# ============================================================================


@mcp.tool()
async def get_vision_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a product vision.

    Returns rich context to help Claude Code guide the user through
    defining a high-quality product vision through collaborative refinement.

    A vision describes the change you want to make in the world—not what you're
    building, but why it matters. The test: "If others achieve this vision and
    we can close shop, it's a good one." This ensures the vision is world-centric
    rather than self-serving.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary containing:
        - purpose: Why this entity exists
        - criteria: Quality standards for a good vision
        - examples: Strong vision statements with explanations
        - questions: Discovery questions for refinement
        - anti_patterns: Common mistakes to avoid
        - coaching_tips: Guidance for iteration
        - conversation_guidelines: How to discuss vision in natural language
        - natural_questions: Framework terms mapped to conversational questions
        - extraction_guidance: Patterns for parsing user input into vision components
        - inference_examples: How to infer vision from indirect user statements
        - current_state: Existing vision if any

    Example:
        >>> framework = await get_vision_definition_framework()
        >>> # Use natural_questions to guide conversation
        >>> # Use extraction_guidance to parse user's response
        >>> # Draft vision and reflect back in user's own words
        >>> await submit_product_vision(refined_vision)
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting vision definition framework for workspace {workspace_uuid}"
        )

        # Get current vision if exists
        current_vision = strategic_controller.get_workspace_vision(
            workspace_uuid, session
        )

        # Build framework using builder pattern
        builder = FrameworkBuilder("vision")

        builder.set_purpose("Define the change you want to make in the world")

        builder.add_criteria(
            [
                "Outcome-focused, not solution-focused",
                "Describes change in user's world",
                "Clear and inspiring",
                "1-2 sentences recommended (no character limit)",
            ]
        )

        builder.add_example(
            text="Enable developers to manage tasks without leaving their IDE",
            why_good="Focuses on user outcome (no context-switching), not features",
        )

        builder.add_example(
            text="Help small businesses access enterprise-grade analytics",
            why_good="Clear outcome (SMBs get capabilities they lack), aspirational",
        )

        builder.add_example(
            text="Allow content creators to publish 10x faster",
            why_good="Measurable change (10x), clear beneficiary (creators)",
        )

        builder.add_questions(
            [
                "What problem are you solving?",
                "What changes for users because your product exists?",
                "What do users achieve that they couldn't before?",
                "If your product disappeared tomorrow, what would users lose?",
            ]
        )

        builder.add_anti_pattern(
            example="Build the best AI tool",
            why_bad="Solution-focused, not outcome-focused",
            better="Enable X users to achieve Y without Z overhead",
        )

        builder.add_anti_pattern(
            example="Create a platform for task management",
            why_bad="Describes what you're building, not why",
            better="Help teams ship faster through better coordination",
        )

        builder.add_coaching_tips(
            [
                "Start broad, then narrow to specific user outcome",
                "Avoid technical jargon or feature lists",
                "Think: 'So that...' - what does your solution enable?",
                "Test: Could this vision apply to a different solution? (If yes, too vague)",
            ]
        )

        # === Natural Language Mapping Guidance ===
        # These fields help Claude Code conduct natural product conversations
        # without exposing internal framework terminology to users.

        builder.set_conversation_guidelines(
            say_this=(
                "the future you're working toward, "
                "the change you want to create, "
                "what becomes possible because of your work"
            ),
            not_this=(
                "the Vision, your product vision, "
                "the vision statement, this strategic element"
            ),
            example=(
                "Instead of 'Let's define your product vision,' say: "
                "'What future are you working toward? If you succeed beyond "
                "your wildest dreams, what changes in the world?'"
            ),
        )

        # Questions to ask users, mapped from framework concepts to natural language
        builder.add_natural_question(
            "vision_statement",
            "What do you want to make possible for people?",
        )
        builder.add_natural_question(
            "outcome_focus",
            "When this works, what will users be able to do that they can't today?",
        )
        builder.add_natural_question(
            "success_scenario",
            "Imagine it's 5 years from now and you've succeeded. What's different about the world?",
        )
        builder.add_natural_question(
            "beneficiary_focus",
            "Who specifically benefits most from what you're building? What changes for them?",
        )
        builder.add_natural_question(
            "competition_test",
            "If a competitor achieved exactly what you're describing, would you be happy the world changed—or frustrated you lost?",
        )

        # Patterns for extracting vision components from natural conversation
        builder.add_extraction_guidance(
            from_input="I'm building a tool for indie hackers to turn scattered feedback into product decisions",
            extractions={
                "beneficiary": "indie hackers (solo developers building products)",
                "current_state": "scattered feedback across channels, hard to synthesize",
                "desired_state": "confident product decisions based on clear signal",
                "transformation": "from overwhelmed by noise → acting on clarity",
                "draft_vision": (
                    "Indie hackers take confident product decisions "
                    + "using clear signals to successfully build their passions"
                ),
            },
        )

        builder.add_extraction_guidance(
            from_input="We want to help small teams ship faster without enterprise complexity",
            extractions={
                "beneficiary": "small teams (likely startups or small companies)",
                "current_state": "slowed down by enterprise-grade tool complexity",
                "desired_state": "shipping faster with right-sized tooling",
                "anti_pattern_signal": "user dislikes enterprise complexity → simplicity pillar",
                "draft_vision": (
                    "Small teams ship at startup speed without enterprise overhead"
                ),
            },
        )

        # Examples of inferring vision from indirect user statements
        builder.add_inference_example(
            user_says="We help developers ship faster by removing context switching",
            inferences={
                "vision": "Enable developers to ship faster by staying in their flow",
                "implied_beneficiary": "Developers who lose time to tool-switching",
                "implied_problem": "Context switching between tools breaks focus",
                "implied_outcome": "Faster shipping through maintained flow state",
                "follow_up": (
                    "What does 'faster' mean to you? 2x? 10x? "
                    "And what breaks their flow most often today?"
                ),
            },
        )

        builder.add_inference_example(
            user_says="I want to democratize access to AI for non-technical people",
            inferences={
                "vision": "Make AI capabilities accessible to everyone, regardless of technical skill",
                "implied_beneficiary": "Non-technical users excluded from AI benefits",
                "implied_problem": "AI tools require technical expertise to use effectively",
                "implied_outcome": "Non-technical people gain AI-powered capabilities",
                "follow_up": (
                    "When non-technical people can use AI, what do they accomplish? "
                    "What specific task becomes possible for them?"
                ),
            },
        )

        builder.add_inference_example(
            user_says="We're building the Stripe of X",
            inferences={
                "pattern": "Analogy-based description—user thinks in comparisons",
                "what_stripe_means": "Simple API, great DX, complex problem made easy",
                "implied_vision": "Make [X] as simple and accessible as Stripe made payments",
                "follow_up": (
                    "What is it about Stripe that you want to emulate? "
                    "The simplicity? The developer experience? Making a hard thing easy?"
                ),
            },
        )

        # Set current state
        if current_vision:
            builder.set_current_state(
                {
                    "has_vision": True,
                    "current_vision": current_vision.vision_text,
                    "created_at": (
                        current_vision.created_at.isoformat()
                        if current_vision.created_at
                        else None
                    ),
                }
            )
        else:
            builder.set_current_state({"has_vision": False, "current_vision": None})

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("vision", str(e))
    except Exception as e:
        logger.exception(f"Error getting vision framework: {e}")
        return build_error_response("vision", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_product_vision(
    vision_text: str,
) -> Dict[str, Any]:
    """Submit a refined product vision after collaborative definition.

    Called only when Claude Code and user have crafted a high-quality
    vision through dialogue using the framework guidance.

    IMPORTANT: Reflect the vision back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        vision_text: Refined vision statement (non-empty text)

    Returns:
        Success response with created/updated vision

    Example:
        >>> result = await submit_product_vision(
        ...     vision_text="Enable developers to manage tasks without leaving their IDE"
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(f"Submitting product vision for workspace {workspace_id}")

        validate_vision_constraints(vision_text)

        vision = strategic_controller.upsert_workspace_vision(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            vision_text=vision_text,
            session=session,
        )

        # Build success response with next steps
        next_steps = [
            "Define 2-5 strategic pillars that explain how you'll differentiate",
            "Each pillar should have a clear anti-strategy (what you WON'T do)",
            "Use get_pillar_definition_framework() to start defining pillars",
        ]

        return build_success_response(
            entity_type="vision",
            message="Vision created/updated successfully",
            data=serialize_vision(vision),
            next_steps=next_steps,
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("vision", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("vision", str(e))
    except MCPContextError as e:
        return build_error_response("vision", str(e))
    except Exception as e:
        logger.exception(f"Error submitting vision: {e}")
        return build_error_response("vision", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def get_vision_details() -> Dict[str, Any]:
    """Retrieves the current product vision for the workspace.

    Returns the vision statement if one has been defined, or an error
    if no vision exists yet.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Success response with vision data, or error if no vision defined

    Example:
        >>> result = await get_vision_details()
        >>> print(result["data"]["vision_text"])
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(f"Getting product vision for workspace {workspace_uuid}")

        vision = strategic_controller.get_workspace_vision(workspace_uuid, session)

        if not vision:
            return build_error_response(
                "vision",
                "No vision defined yet. Use get_vision_definition_framework() to start defining one.",
            )

        return build_success_response(
            entity_type="vision",
            message="Retrieved product vision",
            data=serialize_vision(vision),
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("vision", str(e))
    except Exception as e:
        logger.exception(f"Error getting vision: {e}")
        return build_error_response("vision", f"Server error: {str(e)}")
    finally:
        session.close()
