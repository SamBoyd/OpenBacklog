"""Unit tests for workspace_tools MCP tool."""

import uuid
from unittest.mock import patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key, is_, is_not, none

from src.mcp_server.workspace_tools import create_workspace
from src.models import User, Workspace
from src.roadmap_intelligence.aggregates.prioritized_roadmap import PrioritizedRoadmap
from src.strategic_planning.aggregates.product_vision import ProductVision


class TestCreateWorkspace:
    """Test suite for create_workspace MCP tool."""

    @pytest.mark.asyncio
    async def test_create_workspace_already_exists(self, user: User, session):
        """Test create_workspace when user already has a workspace."""
        # Clear existing workspaces
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        # Create an existing workspace
        existing_workspace = Workspace(
            name="Existing Workspace",
            description="Existing description",
            user_id=user.id,
        )
        session.add(existing_workspace)
        session.commit()
        session.refresh(existing_workspace)

        with patch("src.mcp_server.workspace_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await create_workspace.fn("New Workspace", "New description")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "workspace",
                        "error_message": "You already have a workspace. Each user can only have one workspace.",
                        "error_type": "workspace_exists",
                    }
                ),
            )
            assert_that(result, has_key("existing_workspace"))
            assert_that(
                result["existing_workspace"],
                has_entries(
                    {
                        "id": str(existing_workspace.id),
                        "name": "Existing Workspace",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_create_workspace_success(self, user: User, session):
        """Test successful workspace creation."""
        # Clear existing workspaces
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        user_id_str = str(user.id)
        with patch("src.mcp_server.workspace_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await create_workspace.fn("Test Workspace", "Test description")

            assert_that(result["status"], equal_to("success"))
            assert_that(result["type"], equal_to("workspace"))
            assert_that(
                result["message"],
                equal_to("Created workspace 'Test Workspace'"),
            )
            assert_that(result, has_key("workspace"))

            workspace_data = result["workspace"]
            assert_that(workspace_data["name"], equal_to("Test Workspace"))
            assert_that(workspace_data["description"], equal_to("Test description"))
            assert_that(workspace_data, has_key("id"))
            assert_that(workspace_data, has_key("icon"))

            workspace_id = uuid.UUID(workspace_data["id"])
            workspace = (
                session.query(Workspace).filter(Workspace.id == workspace_id).first()
            )
            assert_that(workspace, is_not(none()))
            assert_that(workspace.name, equal_to("Test Workspace"))
            assert_that(workspace.description, equal_to("Test description"))
            assert_that(str(workspace.user_id), equal_to(user_id_str))

            prioritized_roadmap = (
                session.query(PrioritizedRoadmap)
                .filter_by(workspace_id=workspace.id)
                .first()
            )
            assert_that(prioritized_roadmap, is_not(none()))

            product_vision = (
                session.query(ProductVision)
                .filter_by(workspace_id=workspace.id)
                .first()
            )
            assert_that(product_vision, is_not(none()))

    @pytest.mark.asyncio
    async def test_create_workspace_with_empty_description(self, user: User, session):
        """Test workspace creation with empty description."""
        # Clear existing workspaces
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        with patch("src.mcp_server.workspace_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await create_workspace.fn("Test Workspace", "")

            assert_that(result["status"], equal_to("success"))
            workspace_data = result["workspace"]
            assert_that(workspace_data["name"], equal_to("Test Workspace"))
            assert_that(workspace_data["description"], is_(None))

    @pytest.mark.asyncio
    async def test_create_workspace_without_description(self, user: User, session):
        """Test workspace creation without description parameter."""
        # Clear existing workspaces
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        with patch("src.mcp_server.workspace_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await create_workspace.fn("Test Workspace")

            assert_that(result["status"], equal_to("success"))
            workspace_data = result["workspace"]
            assert_that(workspace_data["name"], equal_to("Test Workspace"))
            assert_that(workspace_data["description"], is_(None))

    async def test_create_workspace_with_placeholder(self, user: User, session):
        """Test workspace creation with placeholder."""
        # Clear existing workspaces
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        with patch("src.mcp_server.workspace_tools.SessionLocal") as mock_session_local:
            mock_session_local.return_value = session

            result = await create_workspace.fn("{your workspace name}")

            assert_that(result["status"], equal_to("error"))
            assert_that(result["type"], equal_to("workspace"))
            assert_that(
                result["error_message"],
                equal_to(
                    "You need to replace the placeholder '{your workspace name}' with your actual workspace name."
                ),
            )
            assert_that(result["error_type"], equal_to("placeholder_error"))
