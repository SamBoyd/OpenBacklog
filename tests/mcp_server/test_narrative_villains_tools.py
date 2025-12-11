"""Unit tests for narrative villain MCP tools.

Tests verify that villain definition, submission, retrieval, update, and deletion
tools work correctly, handle errors appropriately, and emit domain events when expected.

Pattern: Tool calls aggregate methods → verifies success response → validates db state
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entries, has_key

from src.mcp_server.auth_utils import MCPContextError
from src.mcp_server.prompt_driven_tools.narrative_villains import (
    delete_villain,
    get_villain_definition_framework,
    get_villains,
    mark_villain_defeated,
    submit_villain,
    update_villain,
)
from src.models import Workspace
from src.narrative.aggregates.villain import Villain, VillainType
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestGetVillainDefinitionFramework:
    """Test suite for get_villain_definition_framework MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
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
    def existing_villain(self, workspace, user, session, mock_publisher):
        """Create an existing villain for testing framework state."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow state",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.mark.asyncio
    async def test_get_framework_basic_structure(self, session, workspace):
        """Test framework retrieval returns correct structure."""
        workspace_id = str(workspace.id)
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = workspace_id

            result = await get_villain_definition_framework.fn()

        # Verify framework structure
        assert_that(result, has_key("entity_type"))
        assert_that(result, has_key("purpose"))
        assert_that(result, has_key("criteria"))
        assert_that(result, has_key("examples"))
        assert_that(result, has_key("questions_to_explore"))
        assert_that(result, has_key("anti_patterns"))
        assert_that(result, has_key("coaching_tips"))

    @pytest.mark.asyncio
    async def test_get_framework_with_existing_villains(
        self, session, workspace, existing_villain
    ):
        """Test framework retrieval includes current state with existing villains."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_villain_definition_framework.fn()

        # Verify current state reflects existing villains
        assert_that(result["current_state"]["villain_count"], equal_to(1))
        assert_that(result["current_state"]["active_villain_count"], equal_to(1))
        assert_that(result["current_state"]["defeated_count"], equal_to(0))

    @pytest.mark.asyncio
    async def test_get_framework_includes_villain_types(self, session, workspace):
        """Test framework includes villain type definitions."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_villain_definition_framework.fn()

        # Verify villain types are included in context
        assert_that(result, has_key("villain_types"))
        villain_types = result["villain_types"]
        assert_that(villain_types, has_key("EXTERNAL"))
        assert_that(villain_types, has_key("INTERNAL"))
        assert_that(villain_types, has_key("TECHNICAL"))
        assert_that(villain_types, has_key("WORKFLOW"))
        assert_that(villain_types, has_key("OTHER"))

    @pytest.mark.asyncio
    async def test_get_framework_includes_coaching_content(self, session, workspace):
        """Test framework includes all required coaching and guidance content."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_villain_definition_framework.fn()

        # Verify coaching and natural questions
        assert_that(result, has_key("conversation_guidelines"))
        assert_that(result, has_key("natural_questions"))
        assert_that(result, has_key("extraction_guidance"))
        assert_that(result, has_key("inference_examples"))


class TestSubmitVillain:
    """Test suite for submit_villain MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
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

    @pytest.mark.asyncio
    async def test_submit_villain_success(self, session, user, workspace):
        """Test successfully submitting a new villain."""
        villain_name = "Context Switching"
        villain_type = "WORKFLOW"
        villain_description = "Jumping between tools breaks flow state"
        severity = 5

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await submit_villain.fn(
                name=villain_name,
                villain_type=villain_type,
                description=villain_description,
                severity=severity,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["name"], equal_to(villain_name))
        assert_that(result["data"]["description"], equal_to(villain_description))
        assert_that(result["data"]["severity"], equal_to(severity))

    @pytest.mark.asyncio
    async def test_submit_villain_external_type(self, session, user, workspace):
        """Test submitting a villain with EXTERNAL type."""
        villain_name = "Competitor Product"
        villain_type = "EXTERNAL"
        villain_description = "Competitor X has better feature Y"
        severity = 4

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await submit_villain.fn(
                name=villain_name,
                villain_type=villain_type,
                description=villain_description,
                severity=severity,
            )

        # Verify success response with correct type
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["villain_type"], equal_to("EXTERNAL"))

    @pytest.mark.asyncio
    async def test_submit_villain_invalid_type(self, session, user, workspace):
        """Test error when submitting villain with invalid type."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await submit_villain.fn(
                name="Test Villain",
                villain_type="INVALID_TYPE",
                description="Description",
                severity=3,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))
        assert_that(result["error_message"], contains_string("Invalid villain_type"))

    @pytest.mark.asyncio
    async def test_submit_villain_severity_edge_cases(self, session, user, workspace):
        """Test villain severity validation with edge cases."""
        # Save IDs before detachment
        user_id = str(user.id)
        workspace_id = str(workspace.id)

        # Test minimum severity
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (user_id, workspace_id)

            result = await submit_villain.fn(
                name="Low Severity Villain",
                villain_type="INTERNAL",
                description="Minor issue",
                severity=1,
            )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["severity"], equal_to(1))

        # Test maximum severity - use different name to avoid constraint
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (user_id, workspace_id)

            result = await submit_villain.fn(
                name="High Severity Issue",
                villain_type="TECHNICAL",
                description="Critical problem",
                severity=5,
            )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["severity"], equal_to(5))

    @pytest.mark.asyncio
    async def test_submit_villain_mcp_context_error(self, session, user, workspace):
        """Test handling of MCPContextError during submission."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await submit_villain.fn(
                name="Context Switching",
                villain_type="WORKFLOW",
                description="Description",
                severity=5,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_submit_villain_domain_exception(self, session, user, workspace):
        """Test handling of domain validation errors."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.validate_villain_constraints"
            ) as mock_validate,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))
            mock_validate.side_effect = DomainException("Villain name must be unique")

            result = await submit_villain.fn(
                name="Context Switching",
                villain_type="WORKFLOW",
                description="Description",
                severity=5,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))
        assert_that(
            result["error_message"], contains_string("Villain name must be unique")
        )

    @pytest.mark.asyncio
    async def test_submit_villain_includes_next_steps(self, session, user, workspace):
        """Test that submit_villain includes helpful next steps."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await submit_villain.fn(
                name="Context Switching",
                villain_type="WORKFLOW",
                description="Description",
                severity=5,
            )

        # Verify next_steps are included
        assert_that(result, has_key("next_steps"))
        # Check that next_steps is a list with strings mentioning the conflict tool
        assert_that(len(result["next_steps"]), equal_to(3))  # Should have 3 next steps


class TestGetVillains:
    """Test suite for get_villains MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
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

    @pytest.mark.asyncio
    async def test_get_villains_empty_workspace(self, session, workspace):
        """Test retrieving villains from workspace with no villains."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_villains.fn()

        # Verify success response with empty list
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["villains"], equal_to([]))

    @pytest.mark.asyncio
    async def test_get_villains_multiple_villains(
        self, session, workspace, user, mock_publisher
    ):
        """Test retrieving multiple villains from workspace."""
        # Create multiple villains
        villain1 = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        villain2 = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Technical Debt",
            villain_type=VillainType.TECHNICAL,
            description="Legacy code slows development",
            severity=4,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_villains.fn()

        # Verify response contains both villains
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(len(result["data"]["villains"]), equal_to(2))

    @pytest.mark.asyncio
    async def test_get_villains_success_response_structure(self, session, workspace):
        """Test get_villains returns correctly structured response."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_villains.fn()

        # Verify response structure
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result, has_key("message"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("villains"))

    @pytest.mark.asyncio
    async def test_get_villains_includes_defeated_status(
        self, session, workspace, user, mock_publisher
    ):
        """Test that get_villains includes defeated status for each villain."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await get_villains.fn()

        # Verify each villain includes is_defeated status
        assert_that(len(result["data"]["villains"]), equal_to(1))
        assert_that(result["data"]["villains"][0], has_key("is_defeated"))


class TestMarkVillainDefeated:
    """Test suite for mark_villain_defeated MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
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
    def villain(self, workspace, user, session, mock_publisher):
        """Create a villain for testing."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.mark.asyncio
    async def test_mark_villain_defeated_success(self, session, workspace, villain):
        """Test successfully marking a villain as defeated."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await mark_villain_defeated.fn(
                villain_identifier=villain.identifier
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["message"], contains_string("marked as defeated"))
        assert_that(result["data"]["is_defeated"], equal_to(True))

    @pytest.mark.asyncio
    async def test_mark_villain_defeated_already_defeated(
        self, session, workspace, villain, mock_publisher
    ):
        """Test error when marking already defeated villain."""
        # Mark villain as defeated first
        villain.mark_defeated(mock_publisher)
        session.commit()
        session.refresh(villain)

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await mark_villain_defeated.fn(
                villain_identifier=villain.identifier
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))
        assert_that(result["error_message"], contains_string("already defeated"))

    @pytest.mark.asyncio
    async def test_mark_villain_defeated_not_found(self, session, workspace):
        """Test error when villain not found."""
        fake_identifier = "V-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
            ) as mock_get_ws,
        ):
            mock_session_local.return_value = session
            mock_get_ws.return_value = str(workspace.id)

            result = await mark_villain_defeated.fn(villain_identifier=fake_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))


class TestUpdateVillain:
    """Test suite for update_villain MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
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
    def villain(self, workspace, user, session, mock_publisher):
        """Create a villain for testing."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.mark.asyncio
    async def test_update_villain_name_success(self, session, user, workspace, villain):
        """Test successfully updating villain's name."""
        new_name = "Context Switching (Critical)"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
                name=new_name,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["name"], equal_to(new_name))

    @pytest.mark.asyncio
    async def test_update_villain_severity_success(
        self, session, user, workspace, villain
    ):
        """Test successfully updating villain's severity."""
        new_severity = 3

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
                severity=new_severity,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["severity"], equal_to(new_severity))

    @pytest.mark.asyncio
    async def test_update_villain_type_success(self, session, user, workspace, villain):
        """Test successfully updating villain's type."""
        new_type = "TECHNICAL"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
                villain_type=new_type,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["villain_type"], equal_to(new_type))

    @pytest.mark.asyncio
    async def test_update_villain_description_success(
        self, session, user, workspace, villain
    ):
        """Test successfully updating villain's description."""
        new_description = "New description of the problem"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
                description=new_description,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_update_villain_defeated_status(
        self, session, user, workspace, villain
    ):
        """Test updating villain's defeated status."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
                is_defeated=True,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["is_defeated"], equal_to(True))

    @pytest.mark.asyncio
    async def test_update_villain_all_fields_success(
        self, session, user, workspace, villain
    ):
        """Test updating all fields at once."""
        new_name = "Technical Debt"
        new_type = "TECHNICAL"
        new_description = "Legacy code slows development"
        new_severity = 4

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
                name=new_name,
                villain_type=new_type,
                description=new_description,
                severity=new_severity,
            )

        # Verify all fields updated
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["name"], equal_to(new_name))
        assert_that(result["data"]["villain_type"], equal_to(new_type))
        assert_that(result["data"]["description"], equal_to(new_description))
        assert_that(result["data"]["severity"], equal_to(new_severity))

    @pytest.mark.asyncio
    async def test_update_villain_no_fields_error(
        self, session, user, workspace, villain
    ):
        """Test error when no fields provided for update."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))
        assert_that(result["error_message"], contains_string("At least one field"))

    @pytest.mark.asyncio
    async def test_update_villain_invalid_type(self, session, user, workspace, villain):
        """Test error when updating with invalid villain type."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
                villain_type="INVALID_TYPE",
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))
        assert_that(result["error_message"], contains_string("Invalid villain_type"))

    @pytest.mark.asyncio
    async def test_update_villain_not_found(self, session, user, workspace):
        """Test error when villain not found."""
        fake_identifier = "V-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await update_villain.fn(
                villain_identifier=fake_identifier,
                name="New Name",
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_update_villain_mcp_context_error(self, session, villain):
        """Test handling of MCPContextError."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await update_villain.fn(
                villain_identifier=villain.identifier,
                name="New Name",
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))


class TestDeleteVillain:
    """Test suite for delete_villain MCP tool."""

    @pytest.fixture
    def workspace(self, user, session):
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
    def villain(self, workspace, user, session, mock_publisher):
        """Create a villain for testing."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.mark.asyncio
    async def test_delete_villain_success(self, session, user, workspace, villain):
        """Test successfully deleting a villain."""
        villain_id = villain.id
        villain_identifier = villain.identifier

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await delete_villain.fn(villain_identifier=villain_identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(
            result["message"], contains_string(f"Deleted villain {villain_identifier}")
        )
        assert_that(result["data"]["deleted_identifier"], equal_to(villain_identifier))
        assert_that(result["data"]["deleted_id"], equal_to(str(villain_id)))

    @pytest.mark.asyncio
    async def test_delete_villain_not_found(self, session, user, workspace):
        """Test error when villain not found."""
        fake_identifier = "V-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            result = await delete_villain.fn(villain_identifier=fake_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_delete_villain_mcp_context_error(self, session, villain):
        """Test handling of MCPContextError."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await delete_villain.fn(villain_identifier=villain.identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_delete_villain_generic_exception(
        self, session, user, workspace, villain
    ):
        """Test handling of generic exceptions during deletion."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.VillainService"
            ) as mock_service_class,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(user.id), str(workspace.id))

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_villain_by_identifier.side_effect = RuntimeError(
                "Unexpected database error"
            )

            result = await delete_villain.fn(villain_identifier=villain.identifier)

        # Verify error response includes server error message
        assert_that(result, has_entries({"status": "error", "type": "villain"}))
        assert_that(result["error_message"], contains_string("Server error"))
