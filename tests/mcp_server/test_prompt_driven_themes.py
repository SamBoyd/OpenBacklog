"""Minimal tests for prompt-driven roadmap theme workflow MCP tools."""

import uuid
from typing import Any, Callable, Tuple
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.roadmap_themes import (
    connect_theme_to_outcomes,
    deprioritize_workstream,
    get_prioritization_context,
    get_theme_exploration_framework,
    organize_roadmap,
    prioritize_workstream,
    submit_roadmap_theme,
)
from src.models import Workspace
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.exceptions import DomainException


class TestGetThemeExplorationFramework:
    """Test suite for get_theme_exploration_framework tool."""

    @pytest.mark.asyncio
    async def test_framework_returns_complete_structure(self):
        """Test that framework returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_roadmap_themes"
                ) as mock_get_themes,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_unprioritized_themes"
                ) as mock_get_unprioritized,
            ):
                mock_get_outcomes.return_value = []
                mock_get_themes.return_value = []
                mock_get_prioritized.return_value = []
                mock_get_unprioritized.return_value = []

                result = await get_theme_exploration_framework.fn()

        # Verify framework structure
        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("criteria"))
        assert_that(result, has_key("examples"))
        assert_that(result, has_key("current_state"))
        assert_that(result, has_key("coaching_tips"))

        # Verify theme limit info
        assert_that(result["current_state"]["theme_count"], equal_to(0))
        assert_that(result["current_state"]["max_themes"], equal_to(5))
        assert_that(result["current_state"]["remaining"], equal_to(5))

    @pytest.mark.asyncio
    async def test_framework_includes_existing_themes_and_outcomes(self):
        """Test that framework includes current themes and outcomes."""
        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock existing outcome
            mock_outcome = MagicMock(spec=ProductOutcome)
            mock_outcome.id = uuid.uuid4()
            mock_outcome.name = "Developer Daily Adoption"
            mock_outcome.description = "Increase daily active users"

            # Mock existing theme
            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.id = uuid.uuid4()
            mock_theme.name = "First-Week Configuration Success"
            mock_theme.problem_statement = "Users abandon initial configuration"
            mock_theme.outcomes = [mock_outcome]

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_roadmap_themes"
                ) as mock_get_themes,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_unprioritized_themes"
                ) as mock_get_unprioritized,
            ):
                mock_get_outcomes.return_value = [mock_outcome]
                mock_get_themes.return_value = [mock_theme]
                mock_get_prioritized.return_value = []
                mock_get_unprioritized.return_value = [mock_theme]

                result = await get_theme_exploration_framework.fn()

        # Verify current state shows existing theme and outcome
        assert_that(result["current_state"]["theme_count"], equal_to(1))
        assert_that(result["current_state"]["remaining"], equal_to(4))
        assert_that(len(result["current_state"]["available_outcomes"]), equal_to(1))
        assert_that(
            len(result["current_state"]["current_themes"]["unprioritized"]),
            equal_to(1),
        )


class TestSubmitRoadmapTheme:
    """Test suite for submit_roadmap_theme tool."""

    @pytest.mark.asyncio
    async def test_submit_creates_theme_successfully(self, workspace: Workspace):
        """Test that submit successfully creates theme via controller."""
        name = "First-Week Configuration Success"
        description = "Problem Statement: Users abandon initial configuration. Hypothesis: Smart defaults will increase completion from 40% to 70%. Indicative Metrics: Setup completion rate. Timeline: 6 months."
        outcome_ids = [str(uuid.uuid4())]

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock controller create
            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.id = uuid.uuid4()
            mock_theme.workspace_id = workspace.id
            mock_theme.name = name
            mock_theme.description = description
            mock_theme.outcomes = []
            mock_theme.created_at = None
            mock_theme.updated_at = None
            mock_theme.display_order = 0

            with patch(
                "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.create_roadmap_theme"
            ) as mock_create:
                mock_create.return_value = mock_theme

                result = await submit_roadmap_theme.fn(
                    name,
                    description,
                    outcome_ids,
                    draft_mode=False,
                )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(self):
        """Test that submit handles domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.create_roadmap_theme"
            ) as mock_create:
                mock_create.side_effect = DomainException(
                    "Workspace has reached maximum of 5 active roadmap themes"
                )

                result = await submit_roadmap_theme.fn(
                    "Theme Name", "Problem statement", draft_mode=False
                )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))

    @pytest.mark.asyncio
    async def test_submit_handles_invalid_uuid(self, mock_get_auth_context: MagicMock):
        """Test that submit handles invalid workspace_id."""
        # Override the conftest mock to raise ValueError for this test
        # mock_get_auth_context[6] is the mock for roadmap_themes.get_auth_context
        original_side_effect = mock_get_auth_context[6].side_effect
        mock_get_auth_context[6].side_effect = ValueError("Invalid workspace ID")

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            result = await submit_roadmap_theme.fn(
                "Theme Name", "Problem statement", draft_mode=False
            )

        # Reset the mock for other tests
        mock_get_auth_context[6].side_effect = original_side_effect

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))


class TestGetPrioritizationContext:
    """Test suite for get_prioritization_context tool."""

    @pytest.mark.asyncio
    async def test_context_returns_complete_structure(self):
        """Test that context returns all required fields."""
        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_unprioritized_themes"
                ) as mock_get_unprioritized,
            ):
                mock_get_outcomes.return_value = []
                mock_get_pillars.return_value = []
                mock_get_prioritized.return_value = []
                mock_get_unprioritized.return_value = []

                result = await get_prioritization_context.fn()

        # Verify context structure
        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("current_roadmap"))
        assert_that(result, has_key("prioritization_guidance"))
        assert_that(result, has_key("capacity_check"))

    @pytest.mark.asyncio
    async def test_context_includes_alignment_scores(self):
        """Test that context includes alignment scores for themes."""
        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock outcome
            mock_outcome = MagicMock(spec=ProductOutcome)
            mock_outcome.id = uuid.uuid4()
            mock_outcome.name = "Developer Daily Adoption"

            # Mock theme with outcome link
            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.id = uuid.uuid4()
            mock_theme.name = "Test Theme"
            mock_theme.problem_statement = "Test problem"
            mock_theme.outcomes = [mock_outcome]
            mock_theme.hypothesis = "Test hypothesis"
            mock_theme.indicative_metrics = "Test metrics"
            mock_theme.time_horizon_months = 6

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_unprioritized_themes"
                ) as mock_get_unprioritized,
            ):
                mock_get_outcomes.return_value = [mock_outcome]
                mock_get_pillars.return_value = []
                mock_get_prioritized.return_value = []
                mock_get_unprioritized.return_value = [mock_theme]

                result = await get_prioritization_context.fn()

        # Verify unprioritized theme has alignment score
        unprioritized = result["current_roadmap"]["unprioritized_themes"]
        assert_that(len(unprioritized), equal_to(1))
        assert_that(unprioritized[0], has_key("strategic_alignment_score"))


class TestPrioritizeWorkstream:
    """Test suite for prioritize_workstream tool."""

    @pytest.mark.asyncio
    async def test_prioritize_succeeds_with_valid_input(self, workspace):
        """Test that prioritize successfully prioritizes theme."""
        theme_id = str(uuid.uuid4())
        priority_position = 0

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock theme
            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.id = uuid.UUID(theme_id)
            mock_theme.workspace_id = workspace.id
            mock_theme.name = "Test Theme"
            mock_theme.problem_statement = "Test problem"
            mock_theme.outcomes = []
            mock_theme.created_at = None
            mock_theme.updated_at = None
            mock_theme.display_order = 0
            mock_theme.hypothesis = None
            mock_theme.indicative_metrics = None
            mock_theme.time_horizon_months = None

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.prioritize_roadmap_theme"
                ) as mock_prioritize,
            ):
                mock_get_prioritized.return_value = []
                mock_prioritize.return_value = mock_theme

                result = await prioritize_workstream.fn(theme_id, priority_position)

        # Verify success response
        assert_that(
            result, has_entries({"status": "success", "type": "prioritization"})
        )
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_prioritize_warns_on_capacity_exceeded(self, workspace):
        """Test that prioritize warns when capacity exceeded."""
        theme_id = str(uuid.uuid4())
        priority_position = 0

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock 3 existing prioritized themes
            existing_themes = [MagicMock(spec=RoadmapTheme) for _ in range(3)]

            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.id = uuid.UUID(theme_id)
            mock_theme.workspace_id = workspace.id
            mock_theme.name = "Test Theme"
            mock_theme.problem_statement = "Test problem"
            mock_theme.outcomes = []
            mock_theme.created_at = None
            mock_theme.updated_at = None
            mock_theme.display_order = 0
            mock_theme.hypothesis = None
            mock_theme.indicative_metrics = None
            mock_theme.time_horizon_months = None

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.prioritize_roadmap_theme"
                ) as mock_prioritize,
            ):
                mock_get_prioritized.return_value = existing_themes
                mock_prioritize.return_value = mock_theme

                result = await prioritize_workstream.fn(theme_id, priority_position)

        # Verify warning in next_steps
        assert_that(result, has_key("next_steps"))
        warning_found = any("⚠️" in step for step in result["next_steps"])
        assert_that(warning_found, equal_to(True))

    @pytest.mark.asyncio
    async def test_prioritize_handles_domain_exception(self):
        """Test that prioritize handles domain validation errors."""
        theme_id = str(uuid.uuid4())

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.prioritize_roadmap_theme"
                ) as mock_prioritize,
            ):
                mock_get_prioritized.return_value = []
                mock_prioritize.side_effect = DomainException(
                    "Theme already prioritized"
                )

                result = await prioritize_workstream.fn(theme_id, 0)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "prioritization"}))


class TestUtilityTools:
    """Test suite for utility tools (deprioritize, organize, connect)."""

    @pytest.mark.asyncio
    async def test_deprioritize_removes_from_priority_list(self, workspace):
        """Test that deprioritize successfully removes theme."""
        theme_id = str(uuid.uuid4())

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.id = uuid.UUID(theme_id)
            mock_theme.workspace_id = workspace.id
            mock_theme.name = "Test Theme"
            mock_theme.problem_statement = "Test problem"
            mock_theme.outcomes = []
            mock_theme.created_at = None
            mock_theme.updated_at = None
            mock_theme.display_order = 0
            mock_theme.hypothesis = None
            mock_theme.indicative_metrics = None
            mock_theme.time_horizon_months = None

            with patch(
                "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.deprioritize_roadmap_theme"
            ) as mock_deprioritize:
                mock_deprioritize.return_value = mock_theme

                result = await deprioritize_workstream.fn(theme_id)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))

    @pytest.mark.asyncio
    async def test_organize_reorders_themes_correctly(self):
        """Test that organize successfully reorders themes."""
        theme_id_1 = str(uuid.uuid4())
        theme_id_2 = str(uuid.uuid4())
        theme_order = {theme_id_1: 0, theme_id_2: 1}

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_themes = [MagicMock(spec=RoadmapTheme) for _ in range(2)]
            for theme in mock_themes:
                theme.outcomes = []
                theme.created_at = None
                theme.updated_at = None
                theme.display_order = 0
                theme.hypothesis = None
                theme.indicative_metrics = None
                theme.time_horizon_months = None

            with patch(
                "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.reorder_roadmap_themes"
            ) as mock_reorder:
                mock_reorder.return_value = mock_themes

                result = await organize_roadmap.fn(theme_order)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "roadmap"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["count"], equal_to(2))

    @pytest.mark.asyncio
    async def test_connect_updates_outcome_links(self, workspace):
        """Test that connect successfully updates outcome links."""
        theme_id = str(uuid.uuid4())
        outcome_ids = [str(uuid.uuid4())]

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock theme with outcome
            mock_outcome = MagicMock(spec=ProductOutcome)
            mock_outcome.id = uuid.UUID(outcome_ids[0])

            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.id = uuid.UUID(theme_id)
            mock_theme.workspace_id = workspace.id
            mock_theme.name = "Test Theme"
            mock_theme.problem_statement = "Test problem"
            mock_theme.outcomes = [mock_outcome]
            mock_theme.created_at = None
            mock_theme.updated_at = None
            mock_theme.display_order = 0
            mock_theme.hypothesis = "Test"
            mock_theme.indicative_metrics = "Test"
            mock_theme.time_horizon_months = 6

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.update_roadmap_theme"
                ) as mock_update,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
            ):
                mock_session.query.return_value.filter_by.return_value.first.return_value = (
                    mock_theme
                )
                mock_update.return_value = mock_theme
                mock_get_outcomes.return_value = [mock_outcome]

                result = await connect_theme_to_outcomes.fn(theme_id, outcome_ids)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))


class TestSubmitRoadmapThemeDraftMode:
    """Test suite for submit_roadmap_theme draft mode functionality."""

    @pytest.mark.asyncio
    async def test_draft_mode_returns_draft_response(self, workspace):
        """Test that draft_mode=True returns draft response without persisting."""
        name = "First-Week Configuration Success"
        description = "Problem Statement: Users abandon initial configuration. Hypothesis: Smart defaults will increase completion from 40% to 70%. Indicative Metrics: Setup completion rate. Timeline: 6 months."
        outcome_ids = [str(uuid.uuid4())]

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock validation to prevent DB queries
            with patch(
                "src.mcp_server.prompt_driven_tools.roadmap_themes.validate_theme_constraints"
            ) as mock_validate:
                mock_validate.return_value = None  # Validation passes

                # Mock get_auth_context
                with patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                    # Mock get_roadmap_themes to return empty list for display_order calculation
                    with patch(
                        "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_roadmap_themes"
                    ) as mock_get_themes:
                        mock_get_themes.return_value = []

                        # Call tool with draft_mode=True
                        result = await submit_roadmap_theme.fn(
                            name, description, outcome_ids, draft_mode=True
                        )

        # Assert draft response structure
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("is_draft"))
        assert_that(result["is_draft"], equal_to(True))
        assert_that(result, has_key("validation_message"))
        assert "draft" in result["validation_message"].lower()

        # Verify draft data
        assert_that(result, has_key("data"))
        data = result["data"]
        assert_that(data["id"], equal_to("00000000-0000-0000-0000-000000000000"))
        assert_that(data["name"], equal_to(name))
        assert_that(data["description"], equal_to(description))
        assert_that(data["created_at"], equal_to("0001-01-01T00:00:00"))
        assert_that(data["updated_at"], equal_to("0001-01-01T00:00:00"))

        # Verify validation was called
        mock_validate.assert_called_once()
