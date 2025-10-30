"""Unit tests for workspace controller functions."""

from sqlalchemy.orm import Session

from src import controller
from src.models import User
from src.roadmap_intelligence.aggregates.prioritized_roadmap import PrioritizedRoadmap
from src.strategic_planning.aggregates.product_vision import ProductVision


def test_create_workspace_controller(session: Session, user: User):
    """Test controller.create_workspace creates workspace with dependencies."""
    workspace = controller.create_workspace(
        user=user,
        name="Controller Test Workspace",
        description="Test description",
        icon="test-icon.png",
        db=session,
    )

    assert workspace is not None
    assert workspace.name == "Controller Test Workspace"
    assert workspace.description == "Test description"
    assert workspace.icon == "test-icon.png"
    assert workspace.user_id == user.id

    # Verify dependencies were created
    prioritized_roadmap = (
        session.query(PrioritizedRoadmap).filter_by(workspace_id=workspace.id).first()
    )
    product_vision = (
        session.query(ProductVision).filter_by(workspace_id=workspace.id).first()
    )

    assert prioritized_roadmap is not None
    assert product_vision is not None
