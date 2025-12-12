"""Unit tests for Conflict aggregate.

Tests verify that Conflict aggregate enforces business rules,
validates input, enforces invariants, and emits domain events correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from hamcrest import assert_that, equal_to
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.narrative.aggregates.conflict import Conflict, ConflictStatus
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.villain import Villain, VillainType
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestConflict:
    """Unit tests for Conflict aggregate."""

    @pytest.fixture
    def workspace(self, user: User, session: Session):
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
    def hero(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Create a Hero instance for testing."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.fixture
    def villain(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Create a Villain instance for testing."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow.",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.fixture
    def conflict(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Create a Conflict instance for testing."""
        conflict = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Sarah cannot access product context from IDE.",
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(conflict)
        return conflict

    def test_create_conflict_success(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that create_conflict() creates conflict successfully."""
        description = "Sarah cannot access product context from IDE."

        conflict = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description=description,
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.refresh(conflict)

        assert conflict.id is not None
        assert conflict.identifier is not None
        assert conflict.identifier.startswith("C-")
        assert conflict.description == description
        assert conflict.status == ConflictStatus.OPEN.value
        assert conflict.hero_id == hero.id
        assert conflict.villain_id == villain.id
        assert conflict.workspace_id == workspace.id

    def test_create_conflict_description_validation_empty(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that create_conflict() raises exception for empty description."""
        with pytest.raises(DomainException) as exc_info:
            Conflict.create_conflict(
                workspace_id=workspace.id,
                user_id=user.id,
                hero_id=hero.id,
                villain_id=villain.id,
                description="",
                roadmap_theme_id=None,
                session=session,
                publisher=mock_publisher,
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_create_conflict_description_validation_too_long(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that create_conflict() raises exception for description > 2000 chars."""
        long_description = "x" * 2001

        with pytest.raises(DomainException) as exc_info:
            Conflict.create_conflict(
                workspace_id=workspace.id,
                user_id=user.id,
                hero_id=hero.id,
                villain_id=villain.id,
                description=long_description,
                roadmap_theme_id=None,
                session=session,
                publisher=mock_publisher,
            )

        assert "2000 characters or less" in str(exc_info.value)
        assert "2001" in str(exc_info.value)

    def test_create_conflict_validates_hero_exists(
        self,
        workspace: Workspace,
        user: User,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that create_conflict() raises exception if hero doesn't exist."""
        fake_hero_id = uuid.uuid4()

        with pytest.raises(DomainException) as exc_info:
            Conflict.create_conflict(
                workspace_id=workspace.id,
                user_id=user.id,
                hero_id=fake_hero_id,
                villain_id=villain.id,
                description="Valid description",
                roadmap_theme_id=None,
                session=session,
                publisher=mock_publisher,
            )

        assert "does not exist" in str(exc_info.value)
        assert str(fake_hero_id) in str(exc_info.value)

    def test_create_conflict_validates_villain_exists(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that create_conflict() raises exception if villain doesn't exist."""
        fake_villain_id = uuid.uuid4()

        with pytest.raises(DomainException) as exc_info:
            Conflict.create_conflict(
                workspace_id=workspace.id,
                user_id=user.id,
                hero_id=hero.id,
                villain_id=fake_villain_id,
                description="Valid description",
                roadmap_theme_id=None,
                session=session,
                publisher=mock_publisher,
            )

        assert "does not exist" in str(exc_info.value)
        assert str(fake_villain_id) in str(exc_info.value)

    def test_create_conflict_defaults_to_open_status(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that create_conflict() defaults to OPEN status."""
        conflict = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Valid description",
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )

        assert conflict.status == ConflictStatus.OPEN.value

    def test_create_conflict_emits_conflict_created_event(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that create_conflict() emits ConflictCreated event."""
        description = "Sarah cannot access product context from IDE."

        mock_publisher.reset_mock()

        conflict = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description=description,
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.refresh(conflict)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "ConflictCreated"
        assert event.aggregate_id == conflict.id
        assert event.payload["hero_id"] == str(hero.id)
        assert event.payload["villain_id"] == str(villain.id)
        assert event.payload["description"] == description
        assert event.payload["workspace_id"] == str(workspace.id)
        assert workspace_id_arg == str(workspace.id)

    def test_mark_resolving_updates_status(
        self,
        conflict: Conflict,
        mock_publisher: MagicMock,
    ):
        """Test that mark_resolving() updates status to RESOLVING."""
        assert conflict.status == ConflictStatus.OPEN.value

        conflict.mark_resolving(mock_publisher)

        assert conflict.status == ConflictStatus.RESOLVING.value

    def test_mark_resolving_emits_conflict_resolving_event(
        self,
        conflict: Conflict,
        mock_publisher: MagicMock,
    ):
        """Test that mark_resolving() emits ConflictResolving event."""
        mock_publisher.reset_mock()

        conflict.mark_resolving(mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "ConflictResolving"
        assert event.aggregate_id == conflict.id
        assert event.payload["workspace_id"] == str(conflict.workspace_id)
        assert event.payload["conflict_id"] == str(conflict.id)
        assert workspace_id_arg == str(conflict.workspace_id)

    def test_mark_resolved_updates_status_and_timestamp(
        self,
        conflict: Conflict,
        mock_publisher: MagicMock,
    ):
        """Test that mark_resolved() updates status and sets resolved_at timestamp."""
        initiative_id = uuid.uuid4()

        assert conflict.status == ConflictStatus.OPEN.value
        assert conflict.resolved_at is None

        conflict.mark_resolved(
            resolved_by_initiative_id=initiative_id, publisher=mock_publisher
        )

        assert conflict.status == ConflictStatus.RESOLVED.value
        assert conflict.resolved_at is not None
        assert conflict.resolved_by_initiative_id == initiative_id

    def test_mark_resolved_emits_conflict_resolved_event(
        self,
        conflict: Conflict,
        mock_publisher: MagicMock,
    ):
        """Test that mark_resolved() emits ConflictResolved event."""
        initiative_id = uuid.uuid4()

        mock_publisher.reset_mock()

        conflict.mark_resolved(
            resolved_by_initiative_id=initiative_id, publisher=mock_publisher
        )

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id_arg = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "ConflictResolved"
        assert event.aggregate_id == conflict.id
        assert event.payload["workspace_id"] == str(conflict.workspace_id)
        assert event.payload["conflict_id"] == str(conflict.id)
        assert event.payload["resolved_by_initiative_id"] == str(initiative_id)
        assert workspace_id_arg == str(conflict.workspace_id)

    def test_unique_constraint_enforced_for_workspace_identifier(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ):
        """Test that (workspace_id, identifier) unique constraint is enforced."""
        conflict1 = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Conflict 1",
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(conflict1)

        conflict2 = Conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            identifier=conflict1.identifier,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Conflict 2",
            status=ConflictStatus.OPEN.value,
        )
        session.add(conflict2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_conflict_stores_correctly_in_database(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that conflict is stored correctly in database."""
        description = "Sarah cannot access product context from IDE."

        conflict = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description=description,
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(conflict)

        saved_conflict = (
            session.query(Conflict).filter(Conflict.id == conflict.id).first()
        )

        assert saved_conflict is not None
        assert saved_conflict.description == description
        assert saved_conflict.status == ConflictStatus.OPEN.value
        assert saved_conflict.hero_id == hero.id
        assert saved_conflict.villain_id == villain.id
        assert saved_conflict.workspace_id == workspace.id

    def test_identifier_increments_sequentially(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that identifiers increment sequentially for same user."""
        conflict1 = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="First conflict",
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(conflict1)

        conflict2 = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Second conflict",
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(conflict2)

        assert_that(conflict1.identifier, equal_to("C-001"))
        assert_that(conflict2.identifier, equal_to("C-002"))
