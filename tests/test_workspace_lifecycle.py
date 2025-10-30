"""Unit tests for Workspace lifecycle event listeners.

Tests verify that creating a Workspace automatically creates required
1:1 relationship entities (PrioritizedRoadmap and ProductVision).
"""

import pytest
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.roadmap_intelligence.aggregates.prioritized_roadmap import PrioritizedRoadmap
from src.strategic_planning.aggregates.product_vision import ProductVision


def test_workspace_creation_auto_creates_prioritized_roadmap(
    session: Session, user: User
):
    """Test that creating a workspace automatically creates a PrioritizedRoadmap."""
    # Create workspace
    workspace = Workspace(
        name="Test Workspace Auto Create",
        description="Test description",
        user_id=user.id,
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Verify PrioritizedRoadmap was created
    prioritized_roadmap = (
        session.query(PrioritizedRoadmap).filter_by(workspace_id=workspace.id).first()
    )

    assert prioritized_roadmap is not None, "PrioritizedRoadmap should be auto-created"
    assert prioritized_roadmap.workspace_id == workspace.id
    assert prioritized_roadmap.user_id == user.id
    assert (
        prioritized_roadmap.prioritized_theme_ids == []
    ), "Should start with empty theme list"


def test_workspace_creation_auto_creates_product_vision(session: Session, user: User):
    """Test that creating a workspace automatically creates a ProductVision."""
    # Create workspace
    workspace = Workspace(
        name="Test Workspace Vision",
        description="Test description",
        user_id=user.id,
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Verify ProductVision was created
    product_vision = (
        session.query(ProductVision).filter_by(workspace_id=workspace.id).first()
    )

    assert product_vision is not None, "ProductVision should be auto-created"
    assert product_vision.workspace_id == workspace.id
    assert product_vision.user_id == user.id
    assert product_vision.vision_text == "", "Should start with empty vision text"


def test_workspace_creation_creates_both_dependencies(session: Session, user: User):
    """Test that creating a workspace creates both PrioritizedRoadmap and ProductVision."""
    # Create workspace
    workspace = Workspace(
        name="Test Workspace Both",
        description="Test description",
        user_id=user.id,
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Verify both were created
    prioritized_roadmap = (
        session.query(PrioritizedRoadmap).filter_by(workspace_id=workspace.id).first()
    )
    product_vision = (
        session.query(ProductVision).filter_by(workspace_id=workspace.id).first()
    )

    assert prioritized_roadmap is not None, "PrioritizedRoadmap should exist"
    assert product_vision is not None, "ProductVision should exist"


def test_workspace_relationships_accessible(session: Session, user: User):
    """Test that workspace relationships to created entities are accessible."""
    # Create workspace
    workspace = Workspace(
        name="Test Workspace Relationships",
        description="Test description",
        user_id=user.id,
    )
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Access relationships (should work without additional queries due to eager loading)
    assert (
        workspace.prioritized_roadmap is not None
    ), "Relationship to prioritized_roadmap should be accessible"
    assert workspace.vision is not None, "Relationship to vision should be accessible"
    assert workspace.prioritized_roadmap.workspace_id == workspace.id
    assert workspace.vision.workspace_id == workspace.id


def test_existing_workspace_fixture_has_dependencies(session: Session, workspace):
    """Test that the existing workspace fixture now has auto-created dependencies.

    This verifies that the conftest.py workspace fixture benefits from
    the event listener without any changes to the fixture code.
    """
    # The workspace fixture from conftest.py should now have dependencies
    prioritized_roadmap = (
        session.query(PrioritizedRoadmap).filter_by(workspace_id=workspace.id).first()
    )
    product_vision = (
        session.query(ProductVision).filter_by(workspace_id=workspace.id).first()
    )

    assert (
        prioritized_roadmap is not None
    ), "Fixture workspace should have PrioritizedRoadmap"
    assert product_vision is not None, "Fixture workspace should have ProductVision"
