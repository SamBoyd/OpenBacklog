"""Unit tests for EventPublisher service.

Tests verify that domain events are persisted to the database and that
structured logs are emitted with the correct searchable fields.
"""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from src.strategic_planning.models import DomainEvent
from src.strategic_planning.services.event_publisher import EventPublisher


class TestEventPublisher:
    """Unit tests for EventPublisher service."""

    @pytest.fixture
    def event_publisher(self, session: Session):
        """EventPublisher instance with real database session."""
        return EventPublisher(session)

    @pytest.fixture
    def sample_event(self):
        """Sample DomainEvent for testing."""
        return DomainEvent(
            user_id=uuid.uuid4(),
            event_type="VisionDraftCreated",
            aggregate_id=uuid.uuid4(),
            payload={"vision_text": "Build the best product management tool"},
        )

    def test_publish_persists_event_to_database(
        self,
        event_publisher: EventPublisher,
        sample_event: DomainEvent,
        session: Session,
    ):
        """Test that publish() persists event to domain_events table."""
        event_publisher.publish(sample_event)
        session.commit()

        saved_event = (
            session.query(DomainEvent).filter(DomainEvent.id == sample_event.id).first()
        )

        assert saved_event is not None
        assert saved_event.event_type == "VisionDraftCreated"
        assert saved_event.aggregate_id == sample_event.aggregate_id
        assert saved_event.payload == {
            "vision_text": "Build the best product management tool"
        }

    def test_publish_stores_payload_as_jsonb(
        self, event_publisher: EventPublisher, session: Session
    ):
        """Test that event payload is stored as JSONB with proper structure."""
        complex_payload = {
            "vision_text": "Build amazing software",
            "metadata": {"version": 1, "created_by": "user-123"},
            "tags": ["strategy", "vision"],
        }

        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="VisionRefined",
            aggregate_id=uuid.uuid4(),
            payload=complex_payload,
        )

        event_publisher.publish(event)
        session.commit()

        saved_event = (
            session.query(DomainEvent).filter(DomainEvent.id == event.id).first()
        )

        assert saved_event.payload == complex_payload
        assert saved_event.payload["metadata"]["version"] == 1
        assert "strategy" in saved_event.payload["tags"]

    @patch("src.strategic_planning.services.event_publisher.logger")
    def test_publish_emits_structured_log(
        self,
        mock_logger,
        event_publisher: EventPublisher,
        sample_event: DomainEvent,
    ):
        """Test that publish() emits structured log with correct fields."""
        workspace_id = "workspace-123"

        event_publisher.publish(sample_event, workspace_id=workspace_id)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        log_message = call_args[0][0]
        assert "VisionDraftCreated" in log_message

        extra_fields = call_args[1]["extra"]
        assert extra_fields["event_type"] == "VisionDraftCreated"
        assert extra_fields["aggregate_id"] == str(sample_event.aggregate_id)
        assert extra_fields["workspace_id"] == workspace_id
        assert "occurred_at" in extra_fields
        assert extra_fields["event_data"] == sample_event.payload

    @patch("src.strategic_planning.services.event_publisher.logger")
    def test_publish_structured_log_contains_event_type(
        self, mock_logger, event_publisher: EventPublisher, session: Session
    ):
        """Test that structured log contains event_type field for searchability."""
        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="StrategicPillarDefined",
            aggregate_id=uuid.uuid4(),
            payload={"name": "Customer Success"},
        )

        event_publisher.publish(event)

        call_args = mock_logger.info.call_args
        extra_fields = call_args[1]["extra"]

        assert extra_fields["event_type"] == "StrategicPillarDefined"

    @patch("src.strategic_planning.services.event_publisher.logger")
    def test_publish_structured_log_contains_aggregate_id(
        self, mock_logger, event_publisher: EventPublisher, session: Session
    ):
        """Test that structured log contains aggregate_id field for searchability."""
        aggregate_id = uuid.uuid4()
        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="InitiativeStrategicallyEnriched",
            aggregate_id=aggregate_id,
            payload={"pillar_id": str(uuid.uuid4())},
        )

        event_publisher.publish(event)

        call_args = mock_logger.info.call_args
        extra_fields = call_args[1]["extra"]

        assert extra_fields["aggregate_id"] == str(aggregate_id)

    @patch("src.strategic_planning.services.event_publisher.logger")
    def test_publish_structured_log_contains_workspace_id(
        self, mock_logger, event_publisher: EventPublisher, sample_event: DomainEvent
    ):
        """Test that structured log contains workspace_id field for searchability."""
        workspace_id = "workspace-456"

        event_publisher.publish(sample_event, workspace_id=workspace_id)

        call_args = mock_logger.info.call_args
        extra_fields = call_args[1]["extra"]

        assert extra_fields["workspace_id"] == workspace_id

    @patch("src.strategic_planning.services.event_publisher.logger")
    def test_publish_without_workspace_id(
        self, mock_logger, event_publisher: EventPublisher, sample_event: DomainEvent
    ):
        """Test that publish() works without workspace_id (optional parameter)."""
        event_publisher.publish(sample_event)

        call_args = mock_logger.info.call_args
        extra_fields = call_args[1]["extra"]

        assert extra_fields["workspace_id"] is None

    def test_publish_sets_occurred_at_timestamp(
        self, event_publisher: EventPublisher, session: Session
    ):
        """Test that event has occurred_at timestamp set automatically."""
        event = DomainEvent(
            user_id=uuid.uuid4(),
            event_type="VisionDraftCreated",
            aggregate_id=uuid.uuid4(),
            payload={"vision_text": "Build great software"},
        )

        event_publisher.publish(event)
        session.commit()

        saved_event = (
            session.query(DomainEvent).filter(DomainEvent.id == event.id).first()
        )

        assert saved_event.occurred_at is not None
        assert isinstance(saved_event.occurred_at, datetime)
