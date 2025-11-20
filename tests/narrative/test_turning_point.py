"""Unit tests for TurningPoint aggregate.

Tests verify that TurningPoint aggregate enforces business rules,
validates input, enforces invariants, and handles domain event linking correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models import Workspace
from src.narrative.aggregates.turning_point import Significance, TurningPoint
from src.strategic_planning.models import DomainEvent


class TestTurningPoint:
    """Unit tests for TurningPoint aggregate."""

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
    def domain_event(self, workspace: Workspace, user, session: Session):
        """Create a DomainEvent instance for testing."""
        event = DomainEvent(
            user_id=user.id,
            event_type="TaskCompleted",
            aggregate_id=uuid.uuid4(),
            payload={
                "workspace_id": str(workspace.id),
                "task_id": str(uuid.uuid4()),
            },
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event

    @pytest.fixture
    def turning_point(self, domain_event: DomainEvent, session: Session):
        """Create a TurningPoint instance for testing."""
        turning_point = TurningPoint.create_from_event(
            domain_event=domain_event,
            narrative_description="Sarah completed the MCP command task!",
            significance=Significance.MODERATE,
            conflict_id=None,
            story_arc_ids=None,
            initiative_ids=None,
            task_id=None,
            session=session,
        )
        session.commit()
        session.refresh(turning_point)
        return turning_point

    def test_create_from_event_success(
        self,
        domain_event: DomainEvent,
        session: Session,
    ):
        """Test that create_from_event() creates turning point successfully."""
        narrative_description = "Sarah completed the MCP command task!"
        significance = Significance.MODERATE

        turning_point = TurningPoint.create_from_event(
            domain_event=domain_event,
            narrative_description=narrative_description,
            significance=significance,
            conflict_id=None,
            story_arc_ids=None,
            initiative_ids=None,
            task_id=None,
            session=session,
        )
        session.refresh(turning_point)

        assert turning_point.id is not None
        assert turning_point.identifier is not None
        assert turning_point.identifier.startswith("TP-")
        assert turning_point.narrative_description == narrative_description
        assert turning_point.significance == significance.value
        assert turning_point.domain_event_id == domain_event.id
        assert turning_point.user_id == domain_event.user_id

    def test_create_from_event_extracts_workspace_id(
        self,
        workspace: Workspace,
        user,
        session: Session,
    ):
        """Test that create_from_event() extracts workspace_id from event payload."""
        domain_event = DomainEvent(
            user_id=user.id,
            event_type="TaskCompleted",
            aggregate_id=uuid.uuid4(),
            payload={
                "workspace_id": str(workspace.id),
                "task_id": str(uuid.uuid4()),
            },
        )
        session.add(domain_event)
        session.commit()
        session.refresh(domain_event)

        turning_point = TurningPoint.create_from_event(
            domain_event=domain_event,
            narrative_description="Test description",
            significance=Significance.MINOR,
            conflict_id=None,
            story_arc_ids=None,
            initiative_ids=None,
            task_id=None,
            session=session,
        )

        assert turning_point.workspace_id == workspace.id

    def test_create_from_event_raises_error_if_no_workspace_id(
        self,
        user,
        session: Session,
    ):
        """Test that create_from_event() raises error if workspace_id missing from payload."""
        domain_event = DomainEvent(
            user_id=user.id,
            event_type="TaskCompleted",
            aggregate_id=uuid.uuid4(),
            payload={
                "task_id": str(uuid.uuid4()),
            },
        )
        session.add(domain_event)
        session.commit()
        session.refresh(domain_event)

        with pytest.raises(ValueError) as exc_info:
            TurningPoint.create_from_event(
                domain_event=domain_event,
                narrative_description="Test description",
                significance=Significance.MINOR,
                conflict_id=None,
                story_arc_ids=None,
                initiative_ids=None,
                task_id=None,
                session=session,
            )

        assert "workspace_id" in str(exc_info.value)

    def test_unique_constraint_enforced_for_domain_event_id(
        self,
        domain_event: DomainEvent,
        session: Session,
    ):
        """Test that (domain_event_id) unique constraint is enforced."""
        turning_point1 = TurningPoint.create_from_event(
            domain_event=domain_event,
            narrative_description="First turning point",
            significance=Significance.MINOR,
            conflict_id=None,
            story_arc_ids=None,
            initiative_ids=None,
            task_id=None,
            session=session,
        )
        session.commit()
        session.refresh(turning_point1)

        turning_point2 = TurningPoint(
            workspace_id=turning_point1.workspace_id,
            user_id=turning_point1.user_id,
            identifier="TP-0002",
            domain_event_id=domain_event.id,
            narrative_description="Second turning point",
            significance=Significance.MODERATE.value,
        )
        session.add(turning_point2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_unique_constraint_enforced_for_workspace_identifier(
        self,
        workspace: Workspace,
        user,
        session: Session,
    ):
        """Test that (workspace_id, identifier) unique constraint is enforced."""
        domain_event1 = DomainEvent(
            user_id=user.id,
            event_type="TaskCompleted",
            aggregate_id=uuid.uuid4(),
            payload={"workspace_id": str(workspace.id)},
        )
        session.add(domain_event1)
        session.commit()
        session.refresh(domain_event1)

        domain_event2 = DomainEvent(
            user_id=user.id,
            event_type="TaskCompleted",
            aggregate_id=uuid.uuid4(),
            payload={"workspace_id": str(workspace.id)},
        )
        session.add(domain_event2)
        session.commit()
        session.refresh(domain_event2)

        turning_point1 = TurningPoint.create_from_event(
            domain_event=domain_event1,
            narrative_description="First turning point",
            significance=Significance.MINOR,
            conflict_id=None,
            story_arc_ids=None,
            initiative_ids=None,
            task_id=None,
            session=session,
        )
        session.commit()
        session.refresh(turning_point1)

        turning_point2 = TurningPoint(
            workspace_id=workspace.id,
            user_id=user.id,
            identifier=turning_point1.identifier,
            domain_event_id=domain_event2.id,
            narrative_description="Second turning point",
            significance=Significance.MODERATE.value,
        )
        session.add(turning_point2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_turning_point_stores_correctly_in_database(
        self,
        domain_event: DomainEvent,
        session: Session,
    ):
        """Test that turning point is stored correctly in database."""
        narrative_description = "Sarah completed the MCP command task!"
        significance = Significance.MODERATE

        turning_point = TurningPoint.create_from_event(
            domain_event=domain_event,
            narrative_description=narrative_description,
            significance=significance,
            conflict_id=None,
            story_arc_ids=None,
            initiative_ids=None,
            task_id=None,
            session=session,
        )
        session.commit()
        session.refresh(turning_point)

        saved_turning_point = (
            session.query(TurningPoint)
            .filter(TurningPoint.id == turning_point.id)
            .first()
        )

        assert saved_turning_point is not None
        assert saved_turning_point.narrative_description == narrative_description
        assert saved_turning_point.significance == significance.value
        assert saved_turning_point.domain_event_id == domain_event.id
