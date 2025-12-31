"""Prompt-driven MCP tools for Product Outcomes.

This module provides framework-based tools for defining product outcomes
through conversational refinement.

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
    validate_outcome_constraints,
)
from src.mcp_server.prompt_driven_tools.utils.identifier_resolvers import (
    resolve_pillar_identifiers,
)
from src.strategic_planning import controller as strategic_controller
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        >>> await submit_product_outcome(name, description, pillar_identifiers)
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
    name: str = None,
    description: str = None,
    pillar_identifiers: Optional[List[str]] = None,
    outcome_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a refined product outcome after collaborative definition.

    Creates a new product outcome or updates an existing one.

    IMPORTANT: Reflect the outcome back to the user and get explicit confirmation
    BEFORE calling this function. This persists immediately.

    **Upsert Behavior:**
    - If `outcome_identifier` is **omitted**: Creates new outcome
    - If `outcome_identifier` is **provided**: Updates existing outcome

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        name: Outcome name (1-150 characters, required for create, optional for update)
        description: Outcome description including goal, baseline, target, and timeline
                    (required for create, optional for update)
        pillar_identifiers: List of pillar identifiers (e.g., "P-001") to link (optional)
        outcome_identifier: If provided, updates existing outcome (optional)

    Returns:
        Success response with created or updated outcome

    Example:
        >>> # Create
        >>> result = await submit_product_outcome(
        ...     name="Developer Daily Adoption",
        ...     description="Goal: Increase daily active IDE plugin users...",
        ...     pillar_identifiers=["P-001"]
        ... )
        >>> # Update
        >>> result = await submit_product_outcome(
        ...     outcome_identifier="O-002",
        ...     name="Updated Name",
        ...     description="Updated description...",
        ... )
    """
    session = SessionLocal()
    try:
        user_id, workspace_id = get_auth_context(session, requires_workspace=True)
        workspace_uuid = uuid.UUID(workspace_id)
        logger.info(f"Submitting product outcome for workspace {workspace_id}")

        # UPDATE PATH
        if outcome_identifier:
            logger.info(f"Updating product outcome {outcome_identifier}")

            outcome = (
                session.query(ProductOutcome)
                .filter_by(identifier=outcome_identifier, workspace_id=workspace_uuid)
                .first()
            )

            if not outcome:
                return build_error_response(
                    "outcome", f"Product outcome {outcome_identifier} not found"
                )

            publisher = EventPublisher(session)

            # Merge fields: use provided values or preserve existing
            final_name = name if name is not None else outcome.name
            final_description = (
                description if description is not None else outcome.description
            )

            # Update name and description
            outcome.update_outcome(
                name=final_name,
                description=final_description,
                publisher=publisher,
            )

            # Update pillar links if provided
            if pillar_identifiers is not None:
                pillar_uuids = resolve_pillar_identifiers(
                    pillar_identifiers, workspace_uuid, session
                )
                outcome.link_to_pillars(
                    pillar_ids=pillar_uuids,
                    user_id=uuid.UUID(user_id),
                    session=session,
                    publisher=publisher,
                )

            session.commit()
            session.refresh(outcome)

            next_steps = [f"Product outcome '{outcome.name}' updated successfully"]
            if pillar_identifiers is not None:
                next_steps.append(
                    f"Outcome now linked to {len(pillar_identifiers)} pillar(s)"
                )

            return build_success_response(
                entity_type="outcome",
                message=f"Updated product outcome '{outcome.name}'",
                data=serialize_outcome(outcome),
                next_steps=next_steps,
            )

        # CREATE PATH
        else:
            logger.info("Creating new product outcome")

            # Validate required fields for creation
            if not name:
                return build_error_response(
                    "outcome", "name is required for creating a new outcome"
                )
            if not description:
                return build_error_response(
                    "outcome", "description is required for creating a new outcome"
                )

            warnings = []
            if not pillar_identifiers:
                warnings.append(
                    "ALIGNMENT GAP: No pillars linked. Outcomes should connect to the strategic "
                    "pillars they advance. Consider which pillar(s) this outcome measures."
                )

            validate_outcome_constraints(
                workspace_id=workspace_uuid,
                name=name,
                description=description,
                pillar_identifiers=pillar_identifiers,
                session=session,
            )

            pillar_uuids = []
            if pillar_identifiers:
                pillar_uuids = resolve_pillar_identifiers(
                    pillar_identifiers, workspace_uuid, session
                )

            # Call controller to create outcome
            outcome = strategic_controller.create_product_outcome(
                workspace_id=workspace_uuid,
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


@mcp.tool()
async def query_product_outcomes(
    identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """Query product outcomes with optional single-entity lookup.

    A unified query tool that replaces get_product_outcomes and get_product_outcome_details.

    **Query modes:**
    - No params: Returns all product outcomes
    - identifier: Returns single outcome with linked pillars and themes

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        identifier: Outcome identifier (e.g., "O-001") for single lookup

    Returns:
        For single: outcome details with pillar_names and linked_themes
        For list: array of outcomes

    Examples:
        >>> # Get all outcomes
        >>> await query_product_outcomes()

        >>> # Get single outcome by identifier
        >>> await query_product_outcomes(identifier="O-001")
    """
    session = SessionLocal()
    try:
        workspace_uuid = get_workspace_id_from_request()

        # SINGLE OUTCOME MODE: identifier provided
        if identifier:
            logger.info(
                f"Getting product outcome '{identifier}' in workspace {workspace_uuid}"
            )

            outcome = (
                session.query(ProductOutcome)
                .filter_by(identifier=identifier, workspace_id=workspace_uuid)
                .first()
            )

            if not outcome:
                return build_error_response(
                    "outcome", f"Product outcome not found: {identifier}"
                )

            outcome_data = serialize_outcome(outcome)

            # Add enrichments
            outcome_data["pillar_names"] = [pillar.name for pillar in outcome.pillars]

            linked_themes = []
            for theme in outcome.themes:
                linked_themes.append(
                    {
                        "identifier": theme.identifier,
                        "name": theme.name,
                        "is_prioritized": theme.display_order is not None,
                    }
                )
            outcome_data["linked_themes"] = linked_themes

            return build_success_response(
                entity_type="outcome",
                message=f"Found product outcome: {outcome.name}",
                data=outcome_data,
            )

        # LIST MODE: return all outcomes
        logger.info(f"Getting all product outcomes for workspace {workspace_uuid}")

        outcomes = strategic_controller.get_product_outcomes(workspace_uuid, session)

        return build_success_response(
            entity_type="outcome",
            message=f"Found {len(outcomes)} product outcome(s)",
            data={
                "outcomes": [serialize_outcome(outcome) for outcome in outcomes],
            },
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("outcome", str(e))
    except Exception as e:
        logger.exception(f"Error querying product outcomes: {e}")
        return build_error_response("outcome", f"Server error: {str(e)}")
    finally:
        session.close()


@mcp.tool()
async def delete_product_outcome(outcome_identifier: str) -> Dict[str, Any]:
    """Delete a product outcome permanently.

    IMPORTANT: Confirm with user BEFORE calling - this action cannot be undone.
    This will also unlink the outcome from any associated pillars and themes.

    Authentication is handled by FastMCP's RemoteAuthProvider.
    Workspace is automatically loaded from the authenticated user.

    Args:
        outcome_identifier: Human-readable identifier of the product outcome to delete (e.g., "O-002")

    Returns:
        Success response confirming deletion

    Example:
        >>> result = await delete_product_outcome(outcome_identifier="O-002")
    """
    session = SessionLocal()
    try:
        _, workspace_id = get_auth_context(session, requires_workspace=True)
        logger.info(
            f"Deleting product outcome {outcome_identifier} for workspace {workspace_id}"
        )

        workspace_uuid = uuid.UUID(workspace_id)

        outcome = (
            session.query(ProductOutcome)
            .filter_by(identifier=outcome_identifier, workspace_id=workspace_uuid)
            .first()
        )

        if not outcome:
            return build_error_response(
                "outcome", f"Product outcome {outcome_identifier} not found"
            )

        outcome_name = outcome.name

        session.delete(outcome)
        session.commit()

        return build_success_response(
            entity_type="outcome",
            message=f"Deleted product outcome '{outcome_name}'",
            data={"deleted_identifier": outcome_identifier},
        )

    except DomainException as e:
        logger.warning(f"Domain error: {e}")
        return build_error_response("outcome", str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response("outcome", str(e))
    except MCPContextError as e:
        return build_error_response("outcome", str(e))
    except Exception as e:
        logger.exception(f"Error deleting product outcome: {e}")
        return build_error_response("outcome", f"Server error: {str(e)}")
    finally:
        session.close()
