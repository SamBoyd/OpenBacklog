"""Unit tests for workspace_tools MCP tool."""

import uuid
from unittest.mock import Mock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key, is_, is_not, none
from starlette.requests import Request

from src.mcp_server.workspace_tools import create_workspace
from src.models import User, Workspace
from src.roadmap_intelligence.aggregates.prioritized_roadmap import PrioritizedRoadmap
from src.strategic_planning.aggregates.product_vision import ProductVision


class TestCreateWorkspace:
    """Test suite for create_workspace MCP tool."""

    @pytest.fixture
    def mock_request_with_auth(self):
        """Create a mock request with valid authorization header."""
        request = Mock(spec=Request)
        request.headers = {
            "Authorization": "Bearer valid_token",
        }
        return request

    @pytest.fixture
    def mock_request_no_auth(self):
        """Create a mock request without authorization header."""
        request = Mock(spec=Request)
        request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_create_workspace_missing_authorization(self, mock_request_no_auth):
        """Test create_workspace with missing authorization header."""
        with patch(
            "src.mcp_server.workspace_tools.get_http_request"
        ) as mock_get_request:
            mock_get_request.return_value = mock_request_no_auth

            result = await create_workspace.fn("Test Workspace", "Test description")

            assert_that(
                result,
                has_entries(
                    {
                        "status": "error",
                        "type": "workspace",
                        "error_message": "No authorization header found",
                    }
                ),
            )

    @pytest.mark.asyncio
    async def test_create_workspace_invalid_token(self, mock_request_with_auth):
        """Test create_workspace with invalid token."""
        with patch(
            "src.mcp_server.workspace_tools.get_http_request"
        ) as mock_get_request:
            with patch("src.auth.jwt_utils.extract_user_id_from_jwt") as mock_extract:
                mock_get_request.return_value = mock_request_with_auth
                mock_extract.return_value = None

                result = await create_workspace.fn("Test Workspace", "Test description")

                assert_that(
                    result,
                    has_entries(
                        {
                            "status": "error",
                            "type": "workspace",
                            "error_message": "Invalid token: could not extract user ID",
                        }
                    ),
                )

    @pytest.mark.asyncio
    async def test_create_workspace_user_not_found(self, mock_request_with_auth):
        """Test create_workspace when user is not found."""
        fake_user_id = str(uuid.uuid4())
        with patch(
            "src.mcp_server.workspace_tools.get_http_request"
        ) as mock_get_request:
            with patch("src.auth.jwt_utils.extract_user_id_from_jwt") as mock_extract:
                mock_get_request.return_value = mock_request_with_auth
                mock_extract.return_value = fake_user_id

                result = await create_workspace.fn("Test Workspace", "Test description")

                assert_that(
                    result,
                    has_entries(
                        {
                            "status": "error",
                            "type": "workspace",
                            "error_message": "User not found",
                        }
                    ),
                )

    @pytest.mark.asyncio
    async def test_create_workspace_already_exists(
        self, mock_request_with_auth, user: User, session
    ):
        """Test create_workspace when user already has a workspace."""
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        existing_workspace = Workspace(
            name="Existing Workspace",
            description="Existing description",
            user_id=user.id,
        )
        session.add(existing_workspace)
        session.commit()
        session.refresh(existing_workspace)

        user_id_str = str(user.id)
        with patch(
            "src.mcp_server.workspace_tools.get_http_request"
        ) as mock_get_request:
            with patch("src.auth.jwt_utils.extract_user_id_from_jwt") as mock_extract:
                with patch(
                    "src.mcp_server.workspace_tools.SessionLocal"
                ) as mock_session_local:
                    mock_get_request.return_value = mock_request_with_auth
                    mock_extract.return_value = user_id_str
                    mock_session_local.return_value = session

                    result = await create_workspace.fn(
                        "New Workspace", "New description"
                    )

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
    async def test_create_workspace_success(
        self, mock_request_with_auth, user: User, session
    ):
        """Test successful workspace creation."""
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        user_id_str = str(user.id)
        with patch(
            "src.mcp_server.workspace_tools.get_http_request"
        ) as mock_get_request:
            with patch("src.auth.jwt_utils.extract_user_id_from_jwt") as mock_extract:
                with patch(
                    "src.mcp_server.workspace_tools.SessionLocal"
                ) as mock_session_local:
                    mock_get_request.return_value = mock_request_with_auth
                    mock_extract.return_value = user_id_str
                    mock_session_local.return_value = session

                    result = await create_workspace.fn(
                        "Test Workspace", "Test description"
                    )

                    assert_that(result["status"], equal_to("success"))
                    assert_that(result["type"], equal_to("workspace"))
                    assert_that(
                        result["message"],
                        equal_to("Created workspace 'Test Workspace'"),
                    )
                    assert_that(result, has_key("workspace"))

                    workspace_data = result["workspace"]
                    assert_that(workspace_data["name"], equal_to("Test Workspace"))
                    assert_that(
                        workspace_data["description"], equal_to("Test description")
                    )
                    assert_that(workspace_data, has_key("id"))
                    assert_that(workspace_data, has_key("icon"))

                    workspace_id = uuid.UUID(workspace_data["id"])
                    workspace = (
                        session.query(Workspace)
                        .filter(Workspace.id == workspace_id)
                        .first()
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
    async def test_create_workspace_with_empty_description(
        self, mock_request_with_auth, user: User, session
    ):
        """Test workspace creation with empty description."""
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        user_id_str = str(user.id)
        with patch(
            "src.mcp_server.workspace_tools.get_http_request"
        ) as mock_get_request:
            with patch("src.auth.jwt_utils.extract_user_id_from_jwt") as mock_extract:
                with patch(
                    "src.mcp_server.workspace_tools.SessionLocal"
                ) as mock_session_local:
                    mock_get_request.return_value = mock_request_with_auth
                    mock_extract.return_value = user_id_str
                    mock_session_local.return_value = session

                    result = await create_workspace.fn("Test Workspace", "")

                    assert_that(result["status"], equal_to("success"))
                    workspace_data = result["workspace"]
                    assert_that(workspace_data["name"], equal_to("Test Workspace"))
                    assert_that(workspace_data["description"], is_(None))

    @pytest.mark.asyncio
    async def test_create_workspace_without_description(
        self, mock_request_with_auth, user: User, session
    ):
        """Test workspace creation without description parameter."""
        existing_workspaces = (
            session.query(Workspace).filter(Workspace.user_id == user.id).all()
        )
        for ws in existing_workspaces:
            session.delete(ws)
        session.commit()

        user_id_str = str(user.id)
        with patch(
            "src.mcp_server.workspace_tools.get_http_request"
        ) as mock_get_request:
            with patch("src.auth.jwt_utils.extract_user_id_from_jwt") as mock_extract:
                with patch(
                    "src.mcp_server.workspace_tools.SessionLocal"
                ) as mock_session_local:
                    mock_get_request.return_value = mock_request_with_auth
                    mock_extract.return_value = user_id_str
                    mock_session_local.return_value = session

                    result = await create_workspace.fn("Test Workspace")

                    assert_that(result["status"], equal_to("success"))
                    workspace_data = result["workspace"]
                    assert_that(workspace_data["name"], equal_to("Test Workspace"))
                    assert_that(workspace_data["description"], is_(None))
