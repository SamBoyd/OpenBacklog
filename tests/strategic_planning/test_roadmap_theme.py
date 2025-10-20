"""Unit tests for RoadmapTheme aggregate.

Tests verify that RoadmapTheme aggregate enforces business rules,
validates input, enforces invariants, and emits domain events correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestRoadmapTheme:
    """Unit tests for RoadmapTheme aggregate."""

    @pytest.fixture
    def workspace(self, user, session: Session):
        """Create a workspace for testing."""
        workspace = Workspace(
            id=uuid.uuid4(),
            name="Test Workspace",
            description="A test workspace",
            user_id=user.id,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return workspace

    @pytest.fixture
    def mock_publisher(self):
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def roadmap_theme(self, workspace: Workspace, user: User, session: Session):
        """Create a RoadmapTheme instance for testing."""
        theme = RoadmapTheme(
            user_id=user.id,
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            name="First Week Magic",
            problem_statement="Users fail to integrate in first week",
            hypothesis="Quick wins drive adoption",
            indicative_metrics="% users active in week 1",
            time_horizon_months=6,
            display_order=0,
        )
        session.add(theme)
        session.commit()
        session.refresh(theme)
        return theme

    def test_validate_theme_limit_raises_exception_when_5_themes_exist(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
    ):
        """Test that validate_theme_limit() raises exception when 5 themes exist."""
        for i in range(5):
            theme = RoadmapTheme(
                user_id=user.id,
                workspace_id=workspace.id,
                name=f"Theme {i}",
                problem_statement=f"Problem {i}",
                display_order=i,
            )
            session.add(theme)
        session.commit()

        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.validate_theme_limit(workspace.id, session)

        assert "maximum of 5 active roadmap themes" in str(exc_info.value)

    def test_validate_theme_limit_passes_when_less_than_5_themes(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
    ):
        """Test that validate_theme_limit() passes when < 5 themes exist."""
        for i in range(4):
            theme = RoadmapTheme(
                user_id=user.id,
                workspace_id=workspace.id,
                name=f"Theme {i}",
                problem_statement=f"Problem {i}",
                display_order=i,
            )
            session.add(theme)
        session.commit()

        RoadmapTheme.validate_theme_limit(workspace.id, session)

    def test_define_theme_validates_name_minimum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for empty name."""
        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="",
                problem_statement="Valid problem",
                hypothesis=None,
                indicative_metrics=None,
                time_horizon_months=None,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_define_theme_validates_name_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for name > 100 chars."""
        long_name = "x" * 101

        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name=long_name,
                problem_statement="Valid problem",
                hypothesis=None,
                indicative_metrics=None,
                time_horizon_months=None,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "100 characters or less" in str(exc_info.value)
        assert "101" in str(exc_info.value)

    def test_define_theme_validates_problem_statement_minimum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for empty problem statement."""
        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                problem_statement="",
                hypothesis=None,
                indicative_metrics=None,
                time_horizon_months=None,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_define_theme_validates_problem_statement_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for problem_statement > 1500 chars."""
        long_problem = "x" * 1501

        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                problem_statement=long_problem,
                hypothesis=None,
                indicative_metrics=None,
                time_horizon_months=None,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "1500 characters or less" in str(exc_info.value)
        assert "Problem statement" in str(exc_info.value)

    def test_define_theme_validates_hypothesis_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for hypothesis > 1500 chars."""
        long_hypothesis = "x" * 1501

        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                problem_statement="Valid problem",
                hypothesis=long_hypothesis,
                indicative_metrics=None,
                time_horizon_months=None,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "1500 characters or less" in str(exc_info.value)
        assert "Hypothesis" in str(exc_info.value)

    def test_define_theme_validates_indicative_metrics_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for indicative_metrics > 1000 chars."""
        long_metrics = "x" * 1001

        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                problem_statement="Valid problem",
                hypothesis=None,
                indicative_metrics=long_metrics,
                time_horizon_months=None,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "1000 characters or less" in str(exc_info.value)
        assert "Indicative metrics" in str(exc_info.value)

    def test_define_theme_validates_time_horizon_minimum(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for time_horizon < 0."""
        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                problem_statement="Valid problem",
                hypothesis=None,
                indicative_metrics=None,
                time_horizon_months=-1,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "between 0-12 months" in str(exc_info.value)

    def test_define_theme_validates_time_horizon_maximum(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for time_horizon > 12."""
        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                problem_statement="Valid problem",
                hypothesis=None,
                indicative_metrics=None,
                time_horizon_months=13,
                display_order=0,
                session=session,
                publisher=mock_publisher,
            )

        assert "between 0-12 months" in str(exc_info.value)

    def test_define_theme_accepts_valid_input(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() accepts valid input."""
        name = "First Week Magic"
        problem_statement = "Users fail to integrate in first week"
        hypothesis = "Quick wins drive adoption"
        indicative_metrics = "% users active in week 1"
        time_horizon_months = 6
        display_order = 2

        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            problem_statement=problem_statement,
            hypothesis=hypothesis,
            indicative_metrics=indicative_metrics,
            time_horizon_months=time_horizon_months,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )

        assert theme.name == name
        assert theme.problem_statement == problem_statement
        assert theme.hypothesis == hypothesis
        assert theme.indicative_metrics == indicative_metrics
        assert theme.time_horizon_months == time_horizon_months
        assert theme.display_order == display_order

    def test_define_theme_accepts_none_for_optional_fields(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() accepts None for optional fields."""
        name = "First Week Magic"
        problem_statement = "Users fail to integrate in first week"

        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            problem_statement=problem_statement,
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            display_order=0,
            session=session,
            publisher=mock_publisher,
        )

        assert theme.name == name
        assert theme.problem_statement == problem_statement
        assert theme.hypothesis is None
        assert theme.indicative_metrics is None
        assert theme.time_horizon_months is None

    def test_define_theme_emits_theme_defined_event(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() emits ThemeDefined event."""
        name = "First Week Magic"
        problem_statement = "Users fail to integrate in first week"
        hypothesis = "Quick wins drive adoption"
        indicative_metrics = "% users active in week 1"
        time_horizon_months = 6
        display_order = 1

        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            problem_statement=problem_statement,
            hypothesis=hypothesis,
            indicative_metrics=indicative_metrics,
            time_horizon_months=time_horizon_months,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "ThemeDefined"
        assert event.aggregate_id == theme.id
        assert event.payload["name"] == name
        assert event.payload["problem_statement"] == problem_statement
        assert event.payload["hypothesis"] == hypothesis
        assert event.payload["indicative_metrics"] == indicative_metrics
        assert event.payload["time_horizon_months"] == time_horizon_months
        assert event.payload["display_order"] == display_order
        assert event.payload["workspace_id"] == str(workspace.id)
        assert workspace_id_arg == str(workspace.id)

    def test_update_theme_validates_fields(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that update_theme() validates field lengths."""
        with pytest.raises(DomainException):
            roadmap_theme.update_theme(
                name="x" * 101,
                problem_statement="Valid",
                hypothesis=None,
                indicative_metrics=None,
                time_horizon_months=6,
                publisher=mock_publisher,
            )

    def test_update_theme_updates_fields_correctly(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that update_theme() updates fields correctly."""
        new_name = "Updated Name"
        new_problem = "Updated problem statement"
        new_hypothesis = "Updated hypothesis"
        new_metrics = "Updated metrics"
        new_time_horizon = 9

        roadmap_theme.update_theme(
            name=new_name,
            problem_statement=new_problem,
            hypothesis=new_hypothesis,
            indicative_metrics=new_metrics,
            time_horizon_months=new_time_horizon,
            publisher=mock_publisher,
        )

        assert roadmap_theme.name == new_name
        assert roadmap_theme.problem_statement == new_problem
        assert roadmap_theme.hypothesis == new_hypothesis
        assert roadmap_theme.indicative_metrics == new_metrics
        assert roadmap_theme.time_horizon_months == new_time_horizon

    def test_update_theme_emits_theme_updated_event(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that update_theme() emits ThemeUpdated event."""
        new_name = "Updated Name"
        new_problem = "Updated problem"

        roadmap_theme.update_theme(
            name=new_name,
            problem_statement=new_problem,
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "ThemeUpdated"
        assert event.payload["name"] == new_name
        assert event.payload["problem_statement"] == new_problem

    def test_reorder_theme_updates_display_order(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_theme() updates display_order correctly."""
        old_order = roadmap_theme.display_order
        new_order = 3

        roadmap_theme.reorder_theme(new_order, mock_publisher)

        assert roadmap_theme.display_order == new_order
        assert roadmap_theme.display_order != old_order

    def test_reorder_theme_validates_display_order_minimum(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_theme() validates display_order >= 0."""
        with pytest.raises(DomainException) as exc_info:
            roadmap_theme.reorder_theme(-1, mock_publisher)

        assert "between 0-4" in str(exc_info.value)

    def test_reorder_theme_validates_display_order_maximum(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_theme() validates display_order <= 4."""
        with pytest.raises(DomainException) as exc_info:
            roadmap_theme.reorder_theme(5, mock_publisher)

        assert "between 0-4" in str(exc_info.value)

    def test_reorder_theme_emits_themes_reordered_event(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that reorder_theme() emits ThemesReordered event."""
        old_order = roadmap_theme.display_order
        new_order = 2

        roadmap_theme.reorder_theme(new_order, mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "ThemesReordered"
        assert event.payload["old_order"] == old_order
        assert event.payload["new_order"] == new_order
        assert event.payload["theme_id"] == str(roadmap_theme.id)
        assert event.payload["workspace_id"] == str(roadmap_theme.workspace_id)
        assert workspace_id_arg == str(roadmap_theme.workspace_id)

    def test_link_to_outcomes_creates_outcome_links(
        self,
        roadmap_theme: RoadmapTheme,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_to_outcomes() creates outcome linkages."""
        # Create some outcomes
        outcome1 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Outcome 1",
            display_order=0,
        )
        outcome2 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Outcome 2",
            display_order=1,
        )
        session.add(outcome1)
        session.add(outcome2)
        session.commit()

        roadmap_theme.link_to_outcomes(
            [outcome1.id, outcome2.id],
            session,
            mock_publisher,
        )
        session.commit()

        # Refresh to get updated relationships
        session.refresh(roadmap_theme)

        assert len(roadmap_theme.outcomes) == 2
        outcome_ids = {o.id for o in roadmap_theme.outcomes}
        assert outcome1.id in outcome_ids
        assert outcome2.id in outcome_ids

    def test_link_to_outcomes_replaces_existing_links(
        self,
        roadmap_theme: RoadmapTheme,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_to_outcomes() replaces existing outcome linkages."""
        # Create outcomes
        outcome1 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Outcome 1",
            display_order=0,
        )
        outcome2 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Outcome 2",
            display_order=1,
        )
        session.add(outcome1)
        session.add(outcome2)
        session.commit()

        # Link to outcome1
        roadmap_theme.link_to_outcomes([outcome1.id], session, mock_publisher)
        session.commit()
        session.refresh(roadmap_theme)
        assert len(roadmap_theme.outcomes) == 1

        # Replace with outcome2
        roadmap_theme.link_to_outcomes([outcome2.id], session, mock_publisher)
        session.commit()
        session.refresh(roadmap_theme)

        assert len(roadmap_theme.outcomes) == 1
        assert roadmap_theme.outcomes[0].id == outcome2.id

    def test_link_to_outcomes_emits_theme_outcomes_linked_event(
        self,
        roadmap_theme: RoadmapTheme,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that link_to_outcomes() emits ThemeOutcomesLinked event."""
        outcome1 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Outcome 1",
            display_order=0,
        )
        session.add(outcome1)
        session.commit()

        roadmap_theme.link_to_outcomes([outcome1.id], session, mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "ThemeOutcomesLinked"
        assert event.payload["theme_id"] == str(roadmap_theme.id)
        assert str(outcome1.id) in event.payload["outcome_ids"]

    def test_unique_constraint_enforced_for_workspace_name(
        self,
        user: User,
        workspace: Workspace,
        session: Session,
    ):
        """Test that (workspace_id, name) unique constraint is enforced."""
        theme1 = RoadmapTheme(
            user_id=user.id,
            workspace_id=workspace.id,
            name="First Week Magic",
            problem_statement="Problem 1",
            display_order=0,
        )
        session.add(theme1)
        session.commit()

        theme2 = RoadmapTheme(
            user_id=user.id,
            workspace_id=workspace.id,
            name="First Week Magic",
            problem_statement="Problem 2",
            display_order=1,
        )
        session.add(theme2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_theme_stores_correctly_in_database(
        self,
        workspace: Workspace,
        user: User,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that theme is stored correctly in database."""
        name = "First Week Magic"
        problem_statement = "Users fail to integrate in first week"
        hypothesis = "Quick wins drive adoption"
        indicative_metrics = "% users active in week 1"
        time_horizon_months = 6
        display_order = 1

        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            problem_statement=problem_statement,
            hypothesis=hypothesis,
            indicative_metrics=indicative_metrics,
            time_horizon_months=time_horizon_months,
            display_order=display_order,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        saved_theme = (
            session.query(RoadmapTheme).filter(RoadmapTheme.id == theme.id).first()
        )

        assert saved_theme is not None
        assert saved_theme.name == name
        assert saved_theme.problem_statement == problem_statement
        assert saved_theme.hypothesis == hypothesis
        assert saved_theme.indicative_metrics == indicative_metrics
        assert saved_theme.time_horizon_months == time_horizon_months
        assert saved_theme.display_order == display_order
        assert saved_theme.workspace_id == workspace.id

    def test_get_derived_pillars_returns_pillars_from_outcomes(
        self,
        roadmap_theme: RoadmapTheme,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that get_derived_pillars() returns pillars linked via outcomes."""
        from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar

        # Create pillars
        pillar1 = StrategicPillar(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Pillar 1",
            display_order=0,
        )
        pillar2 = StrategicPillar(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Pillar 2",
            display_order=1,
        )
        session.add(pillar1)
        session.add(pillar2)
        session.commit()

        # Create outcome linked to pillar1
        outcome1 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Outcome 1",
            display_order=0,
        )
        session.add(outcome1)
        session.commit()
        outcome1.link_to_pillars(
            [pillar1.id, pillar2.id], user.id, session, mock_publisher
        )
        session.commit()

        # Link theme to outcome
        roadmap_theme.link_to_outcomes([outcome1.id], session, mock_publisher)
        session.commit()
        session.refresh(roadmap_theme)

        # Get derived pillars
        derived_pillars = roadmap_theme.get_derived_pillars()

        assert len(derived_pillars) == 2
        pillar_ids = {p.id for p in derived_pillars}
        assert pillar1.id in pillar_ids
        assert pillar2.id in pillar_ids

    def test_get_derived_pillars_deduplicates_pillars(
        self,
        roadmap_theme: RoadmapTheme,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that get_derived_pillars() deduplicates pillars from multiple outcomes."""
        from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar

        # Create pillar
        pillar1 = StrategicPillar(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Pillar 1",
            display_order=0,
        )
        session.add(pillar1)
        session.commit()

        # Create two outcomes both linked to same pillar
        outcome1 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Outcome 1",
            display_order=0,
        )
        outcome2 = ProductOutcome(
            user_id=user.id,
            workspace_id=workspace.id,
            name="Outcome 2",
            display_order=1,
        )
        session.add(outcome1)
        session.add(outcome2)
        session.commit()

        outcome1.link_to_pillars([pillar1.id], user.id, session, mock_publisher)
        outcome2.link_to_pillars([pillar1.id], user.id, session, mock_publisher)
        session.commit()

        # Link theme to both outcomes
        roadmap_theme.link_to_outcomes(
            [outcome1.id, outcome2.id], session, mock_publisher
        )
        session.commit()
        session.refresh(roadmap_theme)

        # Get derived pillars - should deduplicate
        derived_pillars = roadmap_theme.get_derived_pillars()

        assert len(derived_pillars) == 1
        assert derived_pillars[0].id == pillar1.id
