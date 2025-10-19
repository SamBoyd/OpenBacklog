"""Unit tests for ProductVision aggregate.

Tests verify that ProductVision aggregate enforces business rules,
validates input, and emits domain events correctly.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from src.models import Workspace
from src.strategic_planning.aggregates.product_vision import ProductVision
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestProductVision:
    """Unit tests for ProductVision aggregate."""

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
    def product_vision(self, workspace: Workspace):
        """Create a ProductVision instance for testing."""
        return ProductVision(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            workspace_id=workspace.id,
            vision_text="Initial vision text",
        )

    def test_draft_vision_validates_minimum_length(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that draft_vision() raises exception for empty vision text."""
        with pytest.raises(DomainException) as exc_info:
            product_vision.draft_vision("", mock_publisher)

        assert "at least 1 character" in str(exc_info.value)

    def test_draft_vision_validates_maximum_length(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that draft_vision() raises exception for vision text > 1000 chars."""
        long_text = "x" * 1001

        with pytest.raises(DomainException) as exc_info:
            product_vision.draft_vision(long_text, mock_publisher)

        assert "1000 characters or less" in str(exc_info.value)
        assert "1001" in str(exc_info.value)

    def test_draft_vision_accepts_valid_text(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that draft_vision() accepts valid vision text."""
        valid_text = "Build the best product management tool for developers"

        product_vision.draft_vision(valid_text, mock_publisher)

        assert product_vision.vision_text == valid_text

    def test_draft_vision_accepts_1000_character_text(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that draft_vision() accepts exactly 1000 characters."""
        max_text = "x" * 1000

        product_vision.draft_vision(max_text, mock_publisher)

        assert product_vision.vision_text == max_text

    def test_draft_vision_emits_vision_draft_created_event(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that draft_vision() emits VisionDraftCreated event."""
        vision_text = "Build the best product"

        product_vision.draft_vision(vision_text, mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "VisionDraftCreated"
        assert event.aggregate_id == product_vision.id
        assert event.payload["vision_text"] == vision_text
        assert event.payload["workspace_id"] == str(product_vision.workspace_id)
        assert workspace_id == str(product_vision.workspace_id)

    def test_draft_vision_stores_correctly_in_database(
        self,
        workspace: Workspace,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that draft_vision() stores vision text correctly in database."""
        vision_text = "Build the best product management tool"
        vision = ProductVision(user_id=uuid.uuid4(), workspace_id=workspace.id)

        session.add(vision)
        vision.draft_vision(vision_text, mock_publisher)
        session.commit()

        saved_vision = (
            session.query(ProductVision)
            .filter(ProductVision.workspace_id == workspace.id)
            .first()
        )

        assert saved_vision is not None
        assert saved_vision.vision_text == vision_text
        assert saved_vision.workspace_id == workspace.id

    def test_refine_vision_validates_minimum_length(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that refine_vision() raises exception for empty vision text."""
        with pytest.raises(DomainException) as exc_info:
            product_vision.refine_vision("", mock_publisher)

        assert "at least 1 character" in str(exc_info.value)

    def test_refine_vision_validates_maximum_length(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that refine_vision() raises exception for vision text > 1000 chars."""
        long_text = "x" * 1001

        with pytest.raises(DomainException) as exc_info:
            product_vision.refine_vision(long_text, mock_publisher)

        assert "1000 characters or less" in str(exc_info.value)

    def test_refine_vision_accepts_valid_text(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that refine_vision() accepts valid vision text."""
        original_text = "Build the best product"
        refined_text = "Build the best product for developers"

        product_vision.vision_text = original_text
        product_vision.refine_vision(refined_text, mock_publisher)

        assert product_vision.vision_text == refined_text

    def test_refine_vision_emits_vision_refined_event(
        self,
        product_vision: ProductVision,
        mock_publisher: MagicMock,
    ):
        """Test that refine_vision() emits VisionRefined event."""
        refined_text = "Build the best product for developers"

        product_vision.refine_vision(refined_text, mock_publisher)

        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        workspace_id = mock_publisher.publish.call_args[1]["workspace_id"]

        assert event.event_type == "VisionRefined"
        assert event.aggregate_id == product_vision.id
        assert event.payload["vision_text"] == refined_text
        assert event.payload["workspace_id"] == str(product_vision.workspace_id)
        assert workspace_id == str(product_vision.workspace_id)

    def test_refine_vision_updates_database_correctly(
        self,
        workspace: Workspace,
        mock_publisher: MagicMock,
        session: Session,
    ):
        """Test that refine_vision() updates vision text in database."""
        original_text = "Original vision"
        refined_text = "Refined vision with more detail"

        vision = ProductVision(
            user_id=uuid.uuid4(), workspace_id=workspace.id, vision_text=original_text
        )
        session.add(vision)
        session.commit()

        vision.refine_vision(refined_text, mock_publisher)
        session.commit()

        saved_vision = (
            session.query(ProductVision)
            .filter(ProductVision.workspace_id == workspace.id)
            .first()
        )

        assert saved_vision is not None
        assert saved_vision.vision_text == refined_text

    def test_unique_constraint_enforced_per_workspace(
        self,
        workspace: Workspace,
        session: Session,
    ):
        """Test that workspace can only have one vision (unique constraint)."""
        vision1 = ProductVision(
            user_id=uuid.uuid4(), workspace_id=workspace.id, vision_text="Vision 1"
        )
        vision2 = ProductVision(
            user_id=uuid.uuid4(), workspace_id=workspace.id, vision_text="Vision 2"
        )

        session.add(vision1)
        session.commit()

        session.add(vision2)
        with pytest.raises(Exception):
            session.commit()
