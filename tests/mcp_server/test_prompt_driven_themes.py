"""Minimal tests for prompt-driven roadmap theme workflow MCP tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key
from sqlalchemy.orm.session import Session

from src.mcp_server.prompt_driven_tools.roadmap_themes import (
    connect_theme_to_outcomes,
    delete_roadmap_theme,
    deprioritize_workstream,
    get_prioritization_context,
    get_roadmap_theme_details,
    get_roadmap_themes,
    get_theme_exploration_framework,
    link_theme_to_hero,
    link_theme_to_villain,
    organize_roadmap,
    prioritize_workstream,
    submit_roadmap_theme,
    update_roadmap_theme,
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
    async def test_submit_creates_theme_successfully(
        self, session: Session, workspace: Workspace
    ):
        """Test that submit successfully creates theme via controller."""
        name = "First-Week Configuration Success"
        description = "Problem Statement: Users abandon initial configuration. Hypothesis: Smart defaults will increase completion from 40% to 70%. Indicative Metrics: Setup completion rate. Timeline: 6 months."

        outcome = ProductOutcome(
            name="Developer Daily Adoption",
            description="Increase daily active users",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            display_order=0,
        )
        session.add(outcome)
        session.commit()
        outcome_identifiers = [outcome.identifier]

        result = await submit_roadmap_theme.fn(
            name,
            description,
            outcome_identifiers,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_submit_handles_domain_exception(
        self, session: Session, workspace: Workspace
    ):
        """Test that submit handles domain validation errors."""
        # Create 5 themes to hit the limit
        for i in range(5):
            theme = RoadmapTheme(
                name=f"Test Theme {i}",
                description=f"Problem {i}",
                workspace_id=workspace.id,
                user_id=workspace.user_id,
            )
            session.add(theme)
        session.commit()

        # Try to create another theme, should fail with domain exception
        result = await submit_roadmap_theme.fn("Theme Name", "Problem statement")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))

    @pytest.mark.asyncio
    async def test_submit_handles_invalid_uuid(self, mock_get_auth_context: MagicMock):
        """Test that submit handles invalid workspace_id."""
        # Override the conftest mock to raise ValueError for this test
        # mock_get_auth_context[6] is the mock for roadmap_themes.get_auth_context
        original_side_effect = mock_get_auth_context[
            8
        ].side_effect  # pyright: ignore[reportUnknownVariableType]
        mock_get_auth_context[8].side_effect = ValueError("Invalid workspace ID")

        result = await submit_roadmap_theme.fn("Theme Name", "Problem statement")

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
    async def test_prioritize_succeeds_with_valid_input(self, workspace: Workspace):
        """Test that prioritize successfully prioritizes theme."""
        theme_identifier = "T-001"
        priority_position = 0

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock theme
            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.identifier = theme_identifier
            mock_theme.id = uuid.uuid4()
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
            mock_theme.primary_villain_id = None

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.prioritize_roadmap_theme"
                ) as mock_prioritize,
            ):
                mock_session.query.return_value.filter_by.return_value.first.return_value = (
                    mock_theme
                )
                mock_get_prioritized.return_value = []
                mock_prioritize.return_value = mock_theme

                result = await prioritize_workstream.fn(
                    theme_identifier, priority_position
                )

        # Verify success response
        assert_that(
            result, has_entries({"status": "success", "type": "prioritization"})
        )
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))

    @pytest.mark.asyncio
    async def test_prioritize_warns_on_capacity_exceeded(self, workspace: Workspace):
        """Test that prioritize warns when capacity exceeded."""
        theme_identifier = "T-001"
        priority_position = 0

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock 3 existing prioritized themes
            existing_themes = [MagicMock(spec=RoadmapTheme) for _ in range(3)]

            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.identifier = theme_identifier
            mock_theme.id = uuid.uuid4()
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
            mock_theme.primary_villain_id = None

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_prioritized_themes"
                ) as mock_get_prioritized,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.prioritize_roadmap_theme"
                ) as mock_prioritize,
            ):
                mock_session.query.return_value.filter_by.return_value.first.return_value = (
                    mock_theme
                )
                mock_get_prioritized.return_value = existing_themes
                mock_prioritize.return_value = mock_theme

                result = await prioritize_workstream.fn(
                    theme_identifier, priority_position
                )

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
    async def test_deprioritize_removes_from_priority_list(self, workspace: Workspace):
        """Test that deprioritize successfully removes theme."""
        theme_identifier = "T-001"

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.identifier = theme_identifier
            mock_theme.id = uuid.uuid4()
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
            mock_theme.primary_villain_id = None

            with patch(
                "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.deprioritize_roadmap_theme"
            ) as mock_deprioritize:
                mock_session.query.return_value.filter_by.return_value.first.return_value = (
                    mock_theme
                )
                mock_deprioritize.return_value = mock_theme

                result = await deprioritize_workstream.fn(theme_identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))

    @pytest.mark.asyncio
    async def test_organize_reorders_themes_correctly(self):
        """Test that organize successfully reorders themes."""
        theme_identifier_1 = "T-001"
        theme_identifier_2 = "T-002"
        theme_order = {theme_identifier_1: 0, theme_identifier_2: 1}

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_themes = [MagicMock(spec=RoadmapTheme) for _ in range(2)]
            for i, theme in enumerate(mock_themes):
                theme.identifier = f"T-00{i+1}"
                theme.id = uuid.uuid4()
                theme.outcomes = []
                theme.created_at = None
                theme.updated_at = None
                theme.display_order = 0
                theme.hypothesis = None
                theme.indicative_metrics = None
                theme.time_horizon_months = None
                theme.primary_villain_id = None

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.reorder_roadmap_themes"
                ) as mock_reorder,
            ):

                def mock_query_filter(identifier, workspace_id):
                    mock_theme = next(
                        (t for t in mock_themes if t.identifier == identifier), None
                    )
                    mock_result = MagicMock()
                    mock_result.first.return_value = mock_theme
                    return mock_result

                mock_session.query.return_value.filter_by.side_effect = (
                    mock_query_filter
                )
                mock_reorder.return_value = mock_themes

                result = await organize_roadmap.fn(theme_order)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "roadmap"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["count"], equal_to(2))

    @pytest.mark.asyncio
    async def test_connect_updates_outcome_links(self, workspace: Workspace):
        """Test that connect successfully updates outcome links."""
        theme_identifier = "T-001"
        outcome_identifiers = ["O-001"]

        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock theme with outcome
            mock_outcome = MagicMock(spec=ProductOutcome)
            mock_outcome.identifier = outcome_identifiers[0]
            mock_outcome.id = uuid.uuid4()

            mock_theme = MagicMock(spec=RoadmapTheme)
            mock_theme.identifier = theme_identifier
            mock_theme.id = uuid.uuid4()
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
            mock_theme.primary_villain_id = None

            with (
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.resolve_outcome_identifiers"
                ) as mock_resolve_outcomes,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.update_roadmap_theme"
                ) as mock_update,
                patch(
                    "src.mcp_server.prompt_driven_tools.roadmap_themes.strategic_controller.get_product_outcomes"
                ) as mock_get_outcomes,
            ):
                mock_resolve_outcomes.return_value = [mock_outcome.id]
                mock_session.query.return_value.filter_by.return_value.first.return_value = (
                    mock_theme
                )
                mock_update.return_value = mock_theme
                mock_get_outcomes.return_value = [mock_outcome]

                result = await connect_theme_to_outcomes.fn(
                    theme_identifier, outcome_identifiers
                )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))


class TestGetRoadmapThemes:
    """Test suite for get_roadmap_themes tool."""

    @pytest.mark.asyncio
    async def test_get_themes_returns_empty_list(
        self, session: Session, workspace: Workspace
    ):
        """Test that get_roadmap_themes returns empty list when no themes exist."""
        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_roadmap_themes"
            ) as mock_get_themes:
                mock_get_themes.return_value = []

                result = await get_roadmap_themes.fn()

        # Verify success response with empty list
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result["data"]["themes"], equal_to([]))

    @pytest.mark.asyncio
    async def test_get_themes_returns_list_of_themes(
        self, session: Session, workspace: Workspace
    ):
        """Test that get_roadmap_themes returns list of existing themes."""
        # Create test themes
        theme1 = RoadmapTheme(
            name="Test Theme 1",
            description="Problem 1",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        theme2 = RoadmapTheme(
            name="Test Theme 2",
            description="Problem 2",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme1)
        session.add(theme2)
        session.commit()

        result = await get_roadmap_themes.fn()

        # Verify success response with themes
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(len(result["data"]["themes"]), equal_to(2))

    @pytest.mark.asyncio
    async def test_get_themes_handles_error(self):
        """Test that get_roadmap_themes handles errors gracefully."""
        with patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            with patch(
                "src.mcp_server.prompt_driven_tools.roadmap_themes.roadmap_controller.get_roadmap_themes"
            ) as mock_get_themes:
                mock_get_themes.side_effect = Exception("Database error")

                result = await get_roadmap_themes.fn()

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))


class TestUpdateRoadmapTheme:
    """Test suite for update_roadmap_theme tool."""

    @pytest.mark.asyncio
    async def test_update_theme_with_all_fields(
        self, session: Session, workspace: Workspace
    ):
        """Test that update_roadmap_theme updates all fields successfully."""
        # Create test theme
        theme = RoadmapTheme(
            name="Original Theme",
            description="Original problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()

        # Create outcome
        outcome = ProductOutcome(
            name="Test Outcome",
            description="Test outcome",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            display_order=0,
        )
        session.add(outcome)
        session.commit()

        result = await update_roadmap_theme.fn(
            theme.identifier,
            name="Updated Theme",
            description="Updated problem",
            outcome_identifiers=[outcome.identifier],
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))
        assert_that(result, has_key("next_steps"))
        assert_that(result["data"]["name"], equal_to("Updated Theme"))

    @pytest.mark.asyncio
    async def test_update_theme_with_name_only(
        self, session: Session, workspace: Workspace
    ):
        """Test that update_roadmap_theme updates only name when provided."""
        # Create test theme
        theme = RoadmapTheme(
            name="Original Theme",
            description="Original problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()

        result = await update_roadmap_theme.fn(theme.identifier, name="Updated Theme")

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result["data"]["name"], equal_to("Updated Theme"))

    @pytest.mark.asyncio
    async def test_update_theme_with_description_only(
        self, session: Session, workspace: Workspace
    ):
        """Test that update_roadmap_theme updates only description when provided."""
        # Create test theme
        theme = RoadmapTheme(
            name="Test Theme",
            description="Original problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()

        result = await update_roadmap_theme.fn(
            theme.identifier,
            description="Updated problem",
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))

    @pytest.mark.asyncio
    async def test_update_theme_requires_at_least_one_field(self):
        """Test that update_roadmap_theme requires at least one field."""
        theme_identifier = "T-99999"

        result = await update_roadmap_theme.fn(theme_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))

    @pytest.mark.asyncio
    async def test_update_theme_not_found(self):
        """Test that update_roadmap_theme handles theme not found."""
        theme_identifier = "T-99999"

        result = await update_roadmap_theme.fn(theme_identifier, name="Updated Name")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))

    @pytest.mark.asyncio
    async def test_update_theme_with_invalid_outcome_id(
        self, session: Session, workspace: Workspace
    ):
        """Test that update_roadmap_theme handles invalid outcome IDs."""
        # Create test theme
        theme = RoadmapTheme(
            name="Test Theme",
            description="Problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()

        result = await update_roadmap_theme.fn(
            theme.identifier,
            outcome_identifiers=["INVALID"],
        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))


class TestDeleteRoadmapTheme:
    """Test suite for delete_roadmap_theme tool."""

    @pytest.mark.asyncio
    async def test_delete_theme_succeeds(self, session: Session, workspace: Workspace):
        """Test that delete_roadmap_theme removes theme successfully."""
        # Create test theme
        theme = RoadmapTheme(
            name="Test Theme",
            description="Problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()
        theme_identifier = theme.identifier

        result = await delete_roadmap_theme.fn(theme_identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result["data"]["deleted_identifier"], equal_to(theme_identifier))

        # Verify theme is actually deleted
        deleted_theme = (
            session.query(RoadmapTheme).filter_by(identifier=theme_identifier).first()
        )
        assert_that(deleted_theme, equal_to(None))

    @pytest.mark.asyncio
    async def test_delete_theme_not_found(self):
        """Test that delete_roadmap_theme handles theme not found."""
        theme_identifier = "T-99999"

        result = await delete_roadmap_theme.fn(theme_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))

    @pytest.mark.asyncio
    async def test_delete_theme_with_invalid_id(self):
        """Test that delete_roadmap_theme handles invalid theme identifier."""
        result = await delete_roadmap_theme.fn("INVALID")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))


class TestLinkThemeToHero:
    """Test suite for link_theme_to_hero tool."""

    @pytest.mark.asyncio
    async def test_link_theme_to_hero_succeeds(
        self, session: Session, workspace: Workspace
    ):
        """Test that link_theme_to_hero successfully links theme to hero."""
        from src.narrative.aggregates.hero import Hero
        from src.strategic_planning.services.event_publisher import EventPublisher

        # Create test theme
        theme = RoadmapTheme(
            name="Test Theme",
            description="Problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)

        # Create test hero using define_hero class method
        publisher = EventPublisher(session)
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Hero",
            description="Test hero description",
            is_primary=True,
            session=session,
            publisher=publisher,
        )
        session.commit()
        session.refresh(theme)

        result = await link_theme_to_hero.fn(theme.identifier, hero.identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))
        assert_that(
            result["message"],
            equal_to(
                f"Theme 'Test Theme' linked to hero 'Test Hero' ({hero.identifier})"
            ),
        )

    @pytest.mark.asyncio
    async def test_link_theme_to_hero_not_found(
        self, session: Session, workspace: Workspace
    ):
        """Test that link_theme_to_hero handles hero not found."""
        # Create test theme
        theme = RoadmapTheme(
            name="Test Theme",
            description="Problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()

        result = await link_theme_to_hero.fn(theme.identifier, "H-99999")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))

    @pytest.mark.asyncio
    async def test_link_theme_to_hero_theme_not_found(self):
        """Test that link_theme_to_hero handles theme not found."""
        theme_identifier = "T-99999"

        result = await link_theme_to_hero.fn(theme_identifier, "H-1001")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))


class TestLinkThemeToVillain:
    """Test suite for link_theme_to_villain tool."""

    @pytest.mark.asyncio
    async def test_link_theme_to_villain_succeeds(
        self, session: Session, workspace: Workspace
    ):
        """Test that link_theme_to_villain successfully links theme to villain."""
        from src.narrative.aggregates.villain import Villain, VillainType
        from src.strategic_planning.services.event_publisher import EventPublisher

        # Create test theme
        theme = RoadmapTheme(
            name="Test Theme",
            description="Problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)

        # Create test villain using define_villain class method
        publisher = EventPublisher(session)
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=workspace.user_id,
            name="Test Villain",
            description="Test villain description",
            villain_type=VillainType.EXTERNAL,
            severity=3,
            session=session,
            publisher=publisher,
        )
        session.commit()

        result = await link_theme_to_villain.fn(theme.identifier, villain.identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))
        assert_that(
            result["message"],
            equal_to(
                f"Theme 'Test Theme' linked to villain 'Test Villain' ({villain.identifier})"
            ),
        )

    @pytest.mark.asyncio
    async def test_link_theme_to_villain_not_found(
        self, session: Session, workspace: Workspace
    ):
        """Test that link_theme_to_villain handles villain not found."""
        # Create test theme
        theme = RoadmapTheme(
            name="Test Theme",
            description="Problem",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()

        result = await link_theme_to_villain.fn(theme.identifier, "V-99999")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))

    @pytest.mark.asyncio
    async def test_link_theme_to_villain_theme_not_found(self):
        """Test that link_theme_to_villain handles theme not found."""
        theme_identifier = "T-99999"

        result = await link_theme_to_villain.fn(theme_identifier, "V-1001")

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "theme"}))


class TestGetRoadmapThemeDetails:
    """Test suite for get_roadmap_theme_details MCP tool."""

    @pytest.mark.asyncio
    async def test_get_theme_details_success(
        self, session: Session, workspace: Workspace
    ):
        """Test successfully retrieving theme details."""
        theme = RoadmapTheme(
            name="Test Theme",
            description="Problem statement for testing",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()

        result = await get_roadmap_theme_details.fn(
            theme_identifier=theme.identifier,
        )

        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["identifier"], equal_to(theme.identifier))
        assert_that(result["data"]["name"], equal_to("Test Theme"))
        assert_that(result["data"]["outcome_names"], equal_to([]))
        assert_that(result["data"]["hero_names"], equal_to([]))
        assert_that(result["data"]["villain_names"], equal_to([]))
        assert_that(result["data"]["is_prioritized"], equal_to(False))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("alignment_score"))

    @pytest.mark.asyncio
    async def test_get_theme_details_includes_hero_and_villain_names(
        self, session: Session, workspace: Workspace
    ):
        """Test retrieving theme details includes hero and villain name lists."""
        theme = RoadmapTheme(
            name="Theme With Details",
            description="Problem statement",
            workspace_id=workspace.id,
            user_id=workspace.user_id,
        )
        session.add(theme)
        session.commit()

        result = await get_roadmap_theme_details.fn(
            theme_identifier=theme.identifier,
        )

        assert_that(result, has_entries({"status": "success", "type": "theme"}))
        assert_that(result["data"]["name"], equal_to("Theme With Details"))
        assert_that(result["data"], has_key("hero_names"))
        assert_that(result["data"], has_key("villain_names"))
        assert_that(result["data"], has_key("primary_villain_name"))

    @pytest.mark.asyncio
    async def test_get_theme_details_not_found(self):
        """Test error when theme not found."""
        result = await get_roadmap_theme_details.fn(
            theme_identifier="T-9999",
        )

        assert_that(result, has_entries({"status": "error", "type": "theme"}))
        assert_that(result, has_key("error_message"))
