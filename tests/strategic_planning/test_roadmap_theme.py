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
from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
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
            description="Users fail to integrate in first week. Quick wins drive adoption. % users active in week 1",
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
                description=f"Description {i}",
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
                description=f"Description {i}",
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
                description="Valid description",
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
                description="Valid description",
                session=session,
                publisher=mock_publisher,
            )

        assert "100 characters or less" in str(exc_info.value)
        assert "101" in str(exc_info.value)

    def test_define_theme_validates_description_minimum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for empty description."""
        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description="",
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_define_theme_validates_description_maximum_length(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() raises exception for description > 4000 chars."""
        long_description = "x" * 4001

        with pytest.raises(DomainException) as exc_info:
            RoadmapTheme.define_theme(
                workspace_id=workspace.id,
                user_id=user.id,
                name="Valid Name",
                description=long_description,
                session=session,
                publisher=mock_publisher,
            )

        assert "4000 characters or less" in str(exc_info.value)

    def test_define_theme_accepts_valid_input(
        self,
        workspace: Workspace,
        user,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() accepts valid input."""
        name = "First Week Magic"
        description = "Users fail to integrate in first week. Quick wins drive adoption. % users active in week 1"

        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            session=session,
            publisher=mock_publisher,
        )

        assert theme.name == name
        assert theme.description == description

    def test_define_theme_accepts_valid_description(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() accepts valid description."""
        name = "First Week Magic"
        description = "Users fail to integrate in first week"

        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            session=session,
            publisher=mock_publisher,
        )

        assert theme.name == name
        assert theme.description == description

    def test_define_theme_emits_theme_defined_event(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that define_theme() emits ThemeDefined event."""
        name = "First Week Magic"
        description = "Users fail to integrate in first week. Quick wins drive adoption. % users active in week 1"

        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            session=session,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "ThemeDefined"
        assert event.aggregate_id == theme.id
        assert event.payload["name"] == name
        assert event.payload["description"] == description
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
                description="Valid description",
                publisher=mock_publisher,
            )

    def test_update_theme_updates_fields_correctly(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that update_theme() updates fields correctly."""
        new_name = "Updated Name"
        new_description = "Updated description"

        roadmap_theme.update_theme(
            name=new_name,
            description=new_description,
            publisher=mock_publisher,
        )

        assert roadmap_theme.name == new_name
        assert roadmap_theme.description == new_description

    def test_update_theme_emits_theme_updated_event(
        self,
        roadmap_theme: RoadmapTheme,
        mock_publisher: MagicMock,
    ):
        """Test that update_theme() emits ThemeUpdated event."""
        new_name = "Updated Name"
        new_description = "Updated description"

        roadmap_theme.update_theme(
            name=new_name,
            description=new_description,
            publisher=mock_publisher,
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]

        assert event.event_type == "ThemeUpdated"
        assert event.payload["name"] == new_name
        assert event.payload["description"] == new_description

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
            description="Description 1",
        )
        session.add(theme1)
        session.commit()

        theme2 = RoadmapTheme(
            user_id=user.id,
            workspace_id=workspace.id,
            name="First Week Magic",
            description="Description 2",
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
        description = "Users fail to integrate in first week. Quick wins drive adoption. % users active in week 1"

        theme = RoadmapTheme.define_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name=name,
            description=description,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        saved_theme = (
            session.query(RoadmapTheme).filter(RoadmapTheme.id == theme.id).first()
        )

        assert saved_theme is not None
        assert saved_theme.name == name
        assert saved_theme.description == description
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
