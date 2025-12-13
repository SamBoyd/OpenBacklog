"""Unit tests for product outcome MCP tools.

Tests verify that get_product_outcome_details works correctly,
handles errors appropriately, and returns complete data.

Pattern: Tool calls aggregate methods → verifies success response → validates db state
"""

import uuid
from unittest.mock import MagicMock

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key
from sqlalchemy.orm import Session

from src.mcp_server.prompt_driven_tools.product_outcomes import (
    get_product_outcome_details,
)
from src.models import User, Workspace
from src.strategic_planning.aggregates.product_outcome import ProductOutcome
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.services.event_publisher import EventPublisher


class TestGetProductOutcomeDetails:
    """Test suite for get_product_outcome_details MCP tool."""

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
    def mock_publisher(self) -> MagicMock:
        """Mock EventPublisher for testing."""
        return MagicMock(spec=EventPublisher)

    @pytest.fixture
    def pillar(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ) -> StrategicPillar:
        """Create a StrategicPillar instance for testing."""
        pillar = StrategicPillar.define_pillar(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Developer-First Simplicity",
            description="Make it easy for developers.",
            display_order=0,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(pillar)
        return pillar

    @pytest.fixture
    def outcome(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
    ) -> ProductOutcome:
        """Create a ProductOutcome instance for testing."""
        outcome = ProductOutcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Daily Active Usage",
            description="80% of users active daily.",
            display_order=0,
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)
        return outcome

    @pytest.fixture
    def outcome_with_pillar(
        self,
        workspace: Workspace,
        user: User,
        pillar: StrategicPillar,
        session: Session,
        mock_publisher: MagicMock,
    ) -> ProductOutcome:
        """Create a ProductOutcome linked to a pillar."""
        outcome = ProductOutcome(
            workspace_id=workspace.id,
            user_id=user.id,
            name="IDE Adoption",
            description="70% of users work from IDE.",
            display_order=0,
        )
        session.add(outcome)
        session.commit()

        outcome.link_to_pillars(
            pillar_ids=[pillar.id],
            user_id=user.id,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(outcome)
        return outcome

    @pytest.mark.asyncio
    async def test_get_product_outcome_details_success(
        self, session: Session, outcome: ProductOutcome
    ):
        """Test successfully retrieving outcome details."""
        result = await get_product_outcome_details.fn(
            outcome_identifier=outcome.identifier,
        )

        assert_that(result, has_entries({"status": "success", "type": "outcome"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["identifier"], equal_to(outcome.identifier))
        assert_that(result["data"]["name"], equal_to("Daily Active Usage"))
        assert_that(result["data"]["pillar_names"], equal_to([]))
        assert_that(result["data"]["linked_themes"], equal_to([]))

    @pytest.mark.asyncio
    async def test_get_product_outcome_details_with_pillar(
        self, session: Session, outcome_with_pillar: ProductOutcome
    ):
        """Test retrieving outcome details with linked pillar."""
        result = await get_product_outcome_details.fn(
            outcome_identifier=outcome_with_pillar.identifier,
        )

        assert_that(result, has_entries({"status": "success", "type": "outcome"}))
        assert_that(result["data"]["name"], equal_to("IDE Adoption"))
        assert_that(
            result["data"]["pillar_names"], equal_to(["Developer-First Simplicity"])
        )

    @pytest.mark.asyncio
    async def test_get_product_outcome_details_not_found(self, session: Session):
        """Test error when outcome not found."""
        result = await get_product_outcome_details.fn(
            outcome_identifier="O-9999",
        )

        assert_that(result, has_entries({"status": "error", "type": "outcome"}))
        assert_that(result, has_key("error_message"))
