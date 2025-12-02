"""Prompt-driven MCP tools for strategic foundation.

This module provides framework-based tools for defining strategic foundation
elements (vision, pillars, outcomes) through conversational refinement rather
than rigid forms.

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
    serialize_outcome,
    serialize_pillar,
    serialize_vision,
    validate_outcome_constraints,
    validate_pillar_constraints,
    validate_uuid,
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


# ============================================================================
# Pillar Workflow
# ============================================================================


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
async def submit_strategic_pillar(
    name: str,
    description: str,
) -> Dict[str, Any]:
    """Submit a refined strategic pillar after collaborative definition.

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

    Returns:
        Success response with created pillar

    Example:
        >>> result = await submit_strategic_pillar(
        ...     name="Deep IDE Integration",
        ...     description="Strategy: Seamless developer workflow. Anti-Strategy: No web/mobile."
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(f"Submitting strategic pillar for workspace {workspace_id}")

        validate_pillar_constraints(
            workspace_id=uuid.UUID(workspace_id),
            name=name,
            description=description,
            session=session,
        )

        pillar = strategic_controller.create_strategic_pillar(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            name=name,
            description=description,
            session=session,
        )

        # Build success response with next steps
        all_pillars = strategic_controller.get_strategic_pillars(
            uuid.UUID(workspace_id), session
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


# ============================================================================
# Outcome Workflow
# ============================================================================


@mcp.tool()
async def get_outcome_definition_framework() -> Dict[str, Any]:
    """Get comprehensive framework for defining a product outcome.

    Product outcomes describe observable, measurable changes in user behavior
    or business health that indicate progress toward the vision and strategic
    pillars. They express IMPACT (what changed because of what you shipped),
    not OUTPUT (what you shipped).

    Good outcomes measure behavior, not activity. They show that users are
    succeeding, not that the team is busy.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Returns:
        Framework dictionary containing:
        - purpose: Why outcomes matter in the strategy cascade
        - criteria: What makes a good outcome (behavior-focused, measurable, etc.)
        - examples: Real outcome examples with explanations
        - questions_to_explore: Discovery questions for refinement
        - anti_patterns: Common mistakes and how to fix them
        - coaching_tips: Guidance for crafting strong outcomes
        - conversation_guidelines: How to discuss without framework jargon
        - natural_questions: User-friendly question alternatives
        - extraction_guidance: Patterns for parsing user input
        - inference_examples: How to infer outcomes from context
        - current_state: Existing outcomes and available pillars

    Example:
        >>> framework = await get_outcome_definition_framework()
        >>> # Claude Code uses framework to guide user through refinement
        >>> await submit_product_outcome(name, description, pillar_ids)
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()
        logger.info(
            f"Getting outcome definition framework for workspace {workspace_uuid}"
        )

        # Get current outcomes and available pillars
        current_outcomes = strategic_controller.get_product_outcomes(
            workspace_uuid, session
        )
        available_pillars = strategic_controller.get_strategic_pillars(
            workspace_uuid, session
        )

        # Build framework
        builder = FrameworkBuilder("outcome")

        builder.set_purpose(
            "Define the measurable changes in user behavior or business health "
            "that prove your strategy is working. Outcomes bridge long-term pillars "
            "to near-term execution—they're how you know you're succeeding over 1-3 years."
        )

        builder.add_criteria(
            [
                "User-behavior focused: Describes what users DO or EXPERIENCE, not what you build",
                "Measurable & quantitative: Can be tracked objectively with analytics",
                "Has baseline and target: Where are you now, where do you want to be?",
                "Time-bound: Framed within a 1-3 year horizon",
                "Rooted in pillars: Each outcome is evidence that a pillar is working",
                "Lagging indicator: Captures RESULTS, not activity metrics (not logins or page views)",
                "Actionable: Ambitious enough to stretch, realistic enough to focus execution",
            ]
        )

        builder.add_example(
            text="80% of active users create or refine initiatives using AI weekly",
            why_good="Behavior-focused (users creating with AI), measurable (80%, weekly), "
            "tied to pillar (AI-Augmented PM), lagging indicator of real adoption",
            pillar="AI-Augmented Product Management",
            metric_type="Feature Adoption / Behavior",
            baseline_example="Currently 20% use AI features weekly",
            target="80% weekly active AI usage",
            timeline="18 months",
        )

        builder.add_example(
            text="70% of users manage backlog directly from IDE without switching apps",
            why_good="Describes observable behavior (staying in IDE), quantifiable (70%), "
            "validates the pillar (Developer-First Simplicity), captures real workflow change",
            pillar="Developer-First Simplicity",
            metric_type="Workflow Behavior",
            baseline_example="Currently 30% work primarily in IDE",
            target="70% IDE-native workflow",
            timeline="12 months",
        )

        builder.add_example(
            text="50% of commits reference an active OpenBacklog task or initiative",
            why_good="Integration depth metric showing real usage, measurable via GitHub, "
            "proves Close to the Code pillar is working, behavior-based not activity-based",
            pillar="Ecosystem Integration",
            metric_type="Integration Depth",
            baseline_example="Currently 10% of commits have task references",
            target="50% commit traceability",
            timeline="24 months",
        )

        builder.add_questions(
            [
                "What would users be DOING differently if your pillar was succeeding?",
                "How will you measure that behavior? What specific metric?",
                "What's the current baseline for that metric?",
                "What's an ambitious but achievable target?",
                "Over what timeframe? (typically 12-36 months)",
                "Which strategic pillar does this outcome prove is working?",
            ]
        )

        builder.add_anti_pattern(
            example="Ship AI assistant",
            why_bad="Output-focused: describes what you'll BUILD, not what will CHANGE",
            better="80% of users rely on AI to create or refine tickets weekly",
        )

        builder.add_anti_pattern(
            example="Improve retention",
            why_bad="Too vague: no specific metric, no baseline, no target, no timeline",
            better="Increase 90-day user retention from 40% to 65% within 18 months",
        )

        builder.add_anti_pattern(
            example="Increase number of tickets created",
            why_bad="Vanity metric: measures activity without value—more tickets ≠ more success",
            better="80% of created tickets are completed within their estimated timeframe",
        )

        builder.add_anti_pattern(
            example="Grow ARR by 20% this quarter",
            why_bad="Confused with OKRs: this is a quarterly business metric, not a 1-3 year product outcome",
            better="Trial-to-active conversion rate exceeds 60% (leading to sustainable growth)",
        )

        builder.add_anti_pattern(
            example="Users feel inspired by our product",
            why_bad="Unmeasurable: relies on gut feel, no objective way to track",
            better="NPS for 'ease of use' exceeds 70 (quantifiable sentiment)",
        )

        builder.add_coaching_tips(
            [
                "Start from behavior: Ask 'What would users DO differently if we were succeeding?'",
                "Avoid 'launch' language: If it starts with build, ship, or add—it's not an outcome",
                "Pair qualitative + quantitative: e.g., NPS score + task completion time",
                "Think before → after: Describe the shift you want to see",
                "Each pillar needs 1-3 outcomes: They're evidence your strategy is working",
                "Outcomes are NOT OKRs: Outcomes are 1-3 year success states, OKRs are quarterly execution",
                "Test with 6 questions: Behavioral? Traceable to pillar? Quantifiable? Durable (12-36mo)? Actionable? Inspirational?",
            ]
        )

        # Framework-invisible conversation guidelines
        builder.set_conversation_guidelines(
            say_this="what success looks like, how you'll measure progress, your target behavior",
            not_this="Product Outcome, the outcome, outcome metric",
            example="What would users be doing differently if this pillar was really working?",
        )

        # Natural question mappings
        builder.add_natural_question(
            "behavior_change",
            "If your strategy is working, what would users be DOING differently a year from now?",
        )
        builder.add_natural_question(
            "success_metric",
            "How would you measure that? What number or behavior would you watch?",
        )
        builder.add_natural_question(
            "baseline",
            "Where is that metric today? What's your starting point?",
        )
        builder.add_natural_question(
            "target",
            "Where do you want that number to be? What's ambitious but achievable?",
        )
        builder.add_natural_question(
            "timeline",
            "Over what timeframe? 6 months? A year? Two years?",
        )
        builder.add_natural_question(
            "pillar_connection",
            "Which part of your strategy does this prove is working?",
        )

        # Extraction guidance for parsing user input
        builder.add_extraction_guidance(
            from_input="Right now only 30% of users open the app daily, I want 80% in 6 months",
            extractions={
                "outcome_name": "Daily Active Usage",
                "metric": "Percentage of users active daily",
                "baseline": "30%",
                "target": "80%",
                "timeline": "6 months",
                "type": "Engagement / Habit Formation",
                "follow_up_needed": "Which pillar does this validate? Is 6 months realistic for 50pt jump?",
            },
        )

        builder.add_extraction_guidance(
            from_input="I want most users creating tasks with AI help—that's the whole point",
            extractions={
                "outcome_name": "AI-Assisted Task Creation Adoption",
                "implied_behavior": "Users creating tasks WITH AI assistance",
                "implied_metric": "Percentage of tasks created using AI",
                "implied_target": "'Most' = suggest 70-80%",
                "missing": "Baseline (current AI usage), timeline, specific pillar link",
                "follow_up": "What percentage use AI now? What timeline feels right—6 months? A year?",
            },
        )

        # Inference examples for indirect statements
        builder.add_inference_example(
            user_says="We want developers to never leave the IDE—that's when we've won",
            inferences={
                "outcome": "IDE-Native Workflow Adoption",
                "implied_behavior": "Completing full workflows without leaving IDE",
                "implied_metric": "Percentage of workflows completed in-IDE",
                "implied_target": "Very high (90%+) based on 'never leave'",
                "pillar_link": "Developer-First Simplicity or Ecosystem Integration",
                "follow_up": "What percentage work in the IDE today? What workflows still require leaving?",
            },
        )

        builder.add_inference_example(
            user_says="If our AI is good, users won't need to think about what to do next",
            inferences={
                "outcome": "AI-Guided Decision Making",
                "implied_behavior": "Users following AI recommendations without hesitation",
                "implied_metric": "Percentage of AI suggestions accepted, or time-to-decision",
                "pillar_link": "AI-Augmented Product Management",
                "baseline_question": "How often do users currently follow AI suggestions?",
                "target_question": "What acceptance rate would prove the AI is 'good enough'?",
            },
        )

        builder.add_inference_example(
            user_says="Success is when every commit traces back to a planned task",
            inferences={
                "outcome": "Full Development Traceability",
                "behavior": "Developers linking commits to tasks consistently",
                "metric": "Percentage of commits with task references",
                "target": "100% (based on 'every commit')",
                "realistic_target": "Suggest 80-90% as more achievable",
                "pillar_link": "Ecosystem Integration / Close to the Code",
                "follow_up": "What percentage of commits link to tasks today?",
            },
        )

        # Set current state
        builder.set_current_state(
            {
                "current_outcomes": [
                    {
                        "id": str(outcome.id),
                        "name": outcome.name,
                        "description": outcome.description,
                    }
                    for outcome in current_outcomes
                ],
                "available_pillars": [
                    {"id": str(pillar.id), "name": pillar.name}
                    for pillar in available_pillars
                ],
                "outcome_count": len(current_outcomes),
                "pillar_count": len(available_pillars),
            }
        )

        # Add helpful context notes
        if len(available_pillars) == 0:
            builder.add_context(
                "missing_pillars",
                "No strategic pillars defined yet. Consider defining pillars first—outcomes "
                "should prove that your pillars are working. Use get_pillar_definition_framework().",
            )
        elif len(current_outcomes) == 0:
            builder.add_context(
                "getting_started",
                "No outcomes defined yet. Each pillar should have 1-3 outcomes that prove "
                "it's working. Start with your most important pillar.",
            )

        # Check for pillars without outcomes
        if available_pillars and current_outcomes:
            pillars_with_outcomes: set[str] = set()
            for outcome in current_outcomes:
                if hasattr(outcome, "pillars"):
                    for pillar in outcome.pillars:
                        pillars_with_outcomes.add(str(pillar.id))

            pillars_without = [
                p.name
                for p in available_pillars
                if str(p.id) not in pillars_with_outcomes
            ]
            if pillars_without:
                builder.add_context(
                    "coverage_gap",
                    f"These pillars don't have outcomes yet: {', '.join(pillars_without)}. "
                    "Consider adding outcomes to prove these strategies are working.",
                )

        builder.add_context(
            "outcome_formula",
            "[User segment] [does X or experiences Y] resulting in [measurable signal]. "
            "Example: 'Solo developers complete releases 2x faster without external tools.'",
        )

        return builder.build()

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("outcome", str(e))
    except Exception as e:
        logger.exception(f"Error getting outcome framework: {e}")
        return build_error_response("outcome", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def submit_product_outcome(
    name: str,
    description: str,
    pillar_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Submit a refined product outcome after collaborative definition.

    IMPORTANT: Reflect the outcome back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Outcome name (1-150 characters)
        description: Outcome description including goal, baseline, target, and timeline (required)
                    Should include specific metrics, baseline values, target values, and timeline
        pillar_ids: List of pillar UUIDs to link (optional)

    Returns:
        Success response with created outcome

    Example:
        >>> result = await submit_product_outcome(
        ...     name="Developer Daily Adoption",
        ...     description="Goal: Increase daily active IDE plugin users to measure adoption. Baseline: 30% of users daily active. Target: 80% daily active. Timeline: 6 months. Metric: Daily active users %",
        ...     pillar_ids=["pillar-uuid-1"]
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(f"Submitting product outcome for workspace {workspace_id}")

        warnings = []
        if not pillar_ids:
            warnings.append(
                "ALIGNMENT GAP: No pillars linked. Outcomes should connect to the strategic "
                "pillars they advance. Consider which pillar(s) this outcome measures."
            )

        validate_outcome_constraints(
            workspace_id=uuid.UUID(workspace_id),
            name=name,
            description=description,
            pillar_ids=pillar_ids,
            session=session,
        )

        pillar_uuids = []
        if pillar_ids:
            for pillar_id in pillar_ids:
                pillar_uuids.append(validate_uuid(pillar_id, "pillar_id"))

        # Call controller to create outcome
        outcome = strategic_controller.create_product_outcome(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            name=name,
            description=description,
            pillar_ids=pillar_uuids,
            session=session,
        )

        # Build success response with next steps
        next_steps = [
            "You've defined a measurable outcome for your strategic pillars",
            "Consider defining additional outcomes for other pillars",
            "Once you have outcomes for all pillars, explore roadmap themes",
        ]

        return build_success_response(
            entity_type="outcome",
            message="Product outcome created successfully",
            data=serialize_outcome(outcome),
            next_steps=next_steps,
            warnings=warnings if warnings else None,
        )

    except DomainException as e:
        logger.warning(f"Domain validation error: {e}")
        return build_error_response("outcome", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("outcome", str(e))
    except MCPContextError as e:
        return build_error_response("outcome", str(e))
    except Exception as e:
        logger.exception(f"Error submitting outcome: {e}")
        return build_error_response("outcome", f"Server error: {str(e)}")
    finally:
        session.close()


# ============================================================================
# Combined Strategic Foundation Workflow (Placeholder for future)
# ============================================================================

# Note: Combined foundation workflow will be implemented in a future iteration
# For now, users can build foundation piece by piece using individual workflows
