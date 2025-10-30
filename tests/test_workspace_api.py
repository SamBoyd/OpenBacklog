"""Unit tests for workspace creation API endpoint.

Tests verify that the POST /api/workspaces endpoint correctly creates
workspaces with required dependencies via the SQLAlchemy event listener.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import User
from src.roadmap_intelligence.aggregates.prioritized_roadmap import PrioritizedRoadmap
from src.strategic_planning.aggregates.product_vision import ProductVision


def test_create_workspace_returns_200(test_client: TestClient):
    """Test that creating a workspace returns 200 and workspace data."""
    response = test_client.post(
        "/api/workspaces",
        json={
            "name": "Test Workspace",
            "description": "Test description",
            "icon": "test-icon.png",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Workspace"
    assert data["description"] == "Test description"
    assert data["icon"] == "test-icon.png"
    assert "id" in data


def test_create_workspace_creates_prioritized_roadmap(
    test_client: TestClient, session: Session
):
    """Test that creating a workspace auto-creates PrioritizedRoadmap."""
    response = test_client.post(
        "/api/workspaces",
        json={
            "name": "Test Workspace with Roadmap",
            "description": "Test",
        },
    )

    assert response.status_code == 200
    workspace_id = response.json()["id"]

    # Verify PrioritizedRoadmap was created
    prioritized_roadmap = (
        session.query(PrioritizedRoadmap).filter_by(workspace_id=workspace_id).first()
    )

    assert prioritized_roadmap is not None
    assert str(prioritized_roadmap.workspace_id) == workspace_id
    assert prioritized_roadmap.prioritized_theme_ids == []


def test_create_workspace_creates_product_vision(
    test_client: TestClient, session: Session
):
    """Test that creating a workspace auto-creates ProductVision."""
    response = test_client.post(
        "/api/workspaces",
        json={
            "name": "Test Workspace with Vision",
            "description": "Test",
        },
    )

    assert response.status_code == 200
    workspace_id = response.json()["id"]

    # Verify ProductVision was created
    product_vision = (
        session.query(ProductVision).filter_by(workspace_id=workspace_id).first()
    )

    assert product_vision is not None
    assert str(product_vision.workspace_id) == workspace_id
    assert product_vision.vision_text == ""


def test_create_workspace_requires_authentication(test_client_no_user: TestClient):
    """Test that creating a workspace requires authentication."""
    response = test_client_no_user.post(
        "/api/workspaces",
        json={
            "name": "Test Workspace",
            "description": "Test",
        },
    )

    assert response.status_code == 401


def test_create_workspace_requires_name(test_client: TestClient):
    """Test that creating a workspace requires a name."""
    response = test_client.post(
        "/api/workspaces",
        json={
            "description": "Test",
        },
    )

    assert response.status_code == 422  # Validation error


def test_create_workspace_with_minimal_data(test_client: TestClient, session: Session):
    """Test creating a workspace with only required fields."""
    response = test_client.post(
        "/api/workspaces",
        json={
            "name": "Minimal Workspace",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Minimal Workspace"
    assert data["description"] is None
    assert data["icon"] is None

    # Verify dependencies were still created
    workspace_id = data["id"]
    prioritized_roadmap = (
        session.query(PrioritizedRoadmap).filter_by(workspace_id=workspace_id).first()
    )
    product_vision = (
        session.query(ProductVision).filter_by(workspace_id=workspace_id).first()
    )

    assert prioritized_roadmap is not None
    assert product_vision is not None
