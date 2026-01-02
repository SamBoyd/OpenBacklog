"""Unit tests for narrative villain MCP tools.

Tests verify that villain definition, submission, retrieval, update, and deletion
tools work correctly, handle errors appropriately, and emit domain events when expected.

Pattern: Tool calls aggregate methods → verifies success response → validates db state
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entries, has_key
from sqlalchemy.orm import Session

from src.mcp_server.auth_utils import MCPContextError
from src.mcp_server.prompt_driven_tools.narrative_villains import (
    delete_villain,
    get_villain_definition_framework,
    query_villains,
    submit_villain,
)
from src.models import User, Workspace
from src.narrative.aggregates.villain import Villain, VillainType
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


@pytest.fixture
def mock_get_workspace_id_from_request(workspace: Workspace):
    """Fixture that patches get_workspace_id_from_request and returns workspace ID."""
    with patch(
        "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
    ) as mock:
        mock.return_value = str(workspace.id)
        yield mock


@pytest.fixture
def mock_get_auth_context(user: User, workspace: Workspace):
    """Fixture that patches get_auth_context and returns (user_id, workspace_id) tuple."""
    with patch(
        "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
    ) as mock:
        mock.return_value = (str(user.id), str(workspace.id))
        yield mock


class TestQueryVillainsSingle:
    """Test suite for query_villains MCP tool in single mode."""

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
            description="Jumping between tools breaks flow state",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.mark.asyncio
    async def test_query_villain_single_success(
        self, session, workspace, villain, mock_get_workspace_id_from_request
    ):
        """Test successfully retrieving villain details."""
        result = await query_villains.fn(identifier=villain.identifier)

        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["name"], equal_to(villain.name))
        assert_that(result["data"]["identifier"], equal_to(villain.identifier))

    @pytest.mark.asyncio
    async def test_query_villain_single_includes_battle_summary(
        self, session, workspace, villain, mock_get_workspace_id_from_request
    ):
        """Test that villain details include battle summary."""
        result = await query_villains.fn(identifier=villain.identifier)

        assert_that(result["data"], has_key("battle_summary"))
        battle_summary = result["data"]["battle_summary"]
        assert_that(battle_summary, has_key("open_conflicts_count"))
        assert_that(battle_summary, has_key("resolved_conflicts_count"))
        assert_that(battle_summary, has_key("total_conflicts_count"))
        assert_that(battle_summary, has_key("linked_themes_count"))
        assert_that(battle_summary, has_key("initiatives_confronting_count"))

    @pytest.mark.asyncio
    async def test_query_villain_single_not_found(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test error when villain not found."""
        fake_identifier = "V-9999"

        result = await query_villains.fn(identifier=fake_identifier)

        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_query_villain_single_handles_workspace_error(
        self, session, villain, mock_get_workspace_id_from_request
    ):
        """Test handling of workspace error."""
        mock_get_workspace_id_from_request.side_effect = ValueError(
            "Invalid workspace ID"
        )

        result = await query_villains.fn(identifier=villain.identifier)

        assert_that(result, has_entries({"status": "error", "type": "villain"}))


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
    async def test_get_framework_basic_structure(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test framework retrieval returns correct structure."""
        result = await get_villain_definition_framework()

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
        self, session, workspace, existing_villain, mock_get_workspace_id_from_request
    ):
        """Test framework retrieval includes current state with existing villains."""
        result = await get_villain_definition_framework()

        # Verify current state reflects existing villains
        assert_that(result["current_state"]["villain_count"], equal_to(1))
        assert_that(result["current_state"]["active_villain_count"], equal_to(1))
        assert_that(result["current_state"]["defeated_count"], equal_to(0))

    @pytest.mark.asyncio
    async def test_get_framework_includes_villain_types(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test framework includes villain type definitions."""
        result = await get_villain_definition_framework()

        # Verify villain types are included in context
        assert_that(result, has_key("villain_types"))
        villain_types = result["villain_types"]
        assert_that(villain_types, has_key("EXTERNAL"))
        assert_that(villain_types, has_key("INTERNAL"))
        assert_that(villain_types, has_key("TECHNICAL"))
        assert_that(villain_types, has_key("WORKFLOW"))
        assert_that(villain_types, has_key("OTHER"))

    @pytest.mark.asyncio
    async def test_get_framework_includes_coaching_content(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test framework includes all required coaching and guidance content."""
        result = await get_villain_definition_framework()

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
    async def test_submit_villain_success(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test successfully submitting a new villain."""
        villain_name = "Context Switching"
        villain_type = "WORKFLOW"
        villain_description = "Jumping between tools breaks flow state"
        severity = 5

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
    async def test_submit_villain_external_type(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test submitting a villain with EXTERNAL type."""
        villain_name = "Competitor Product"
        villain_type = "EXTERNAL"
        villain_description = "Competitor X has better feature Y"
        severity = 4

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
    async def test_submit_villain_invalid_type(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test error when submitting villain with invalid type."""
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
    async def test_submit_villain_severity_edge_cases(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test villain severity validation with edge cases."""
        # Test minimum severity
        result = await submit_villain.fn(
            name="Low Severity Villain",
            villain_type="INTERNAL",
            description="Minor issue",
            severity=1,
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["severity"], equal_to(1))

        # Test maximum severity - use different name to avoid constraint
        result = await submit_villain.fn(
            name="High Severity Issue",
            villain_type="TECHNICAL",
            description="Critical problem",
            severity=5,
        )

        assert_that(result, has_entries({"status": "success"}))
        assert_that(result["data"]["severity"], equal_to(5))

    @pytest.mark.asyncio
    async def test_submit_villain_mcp_context_error(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test handling of MCPContextError during submission."""
        mock_get_auth_context.side_effect = MCPContextError("No workspace in context")

        result = await submit_villain.fn(
            name="Context Switching",
            villain_type="WORKFLOW",
            description="Description",
            severity=5,
        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_submit_villain_domain_exception(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test handling of domain validation errors."""
        with patch(
            "src.mcp_server.prompt_driven_tools.narrative_villains.validate_villain_constraints"
        ) as mock_validate:
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
    async def test_submit_villain_includes_next_steps(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test that submit_villain includes helpful next steps."""
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


class TestQueryVillainsList:
    """Test suite for query_villains MCP tool in list mode."""

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
    async def test_query_villains_list_empty_workspace(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test retrieving villains from workspace with no villains."""
        result = await query_villains.fn()

        # Verify success response with empty list
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["villains"], equal_to([]))

    @pytest.mark.asyncio
    async def test_query_villains_list_multiple_villains(
        self,
        session,
        workspace,
        user,
        mock_publisher,
        mock_get_workspace_id_from_request,
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

        result = await query_villains.fn()

        # Verify response contains both villains
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(len(result["data"]["villains"]), equal_to(2))

    @pytest.mark.asyncio
    async def test_query_villains_list_success_response_structure(
        self, session, workspace, mock_get_workspace_id_from_request
    ):
        """Test query_villains returns correctly structured response."""
        result = await query_villains.fn()

        # Verify response structure
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result, has_key("message"))
        assert_that(result, has_key("data"))
        assert_that(result["data"], has_key("villains"))

    @pytest.mark.asyncio
    async def test_query_villains_list_includes_defeated_status(
        self,
        session,
        workspace,
        user,
        mock_publisher,
        mock_get_workspace_id_from_request,
    ):
        """Test that query_villains includes defeated status for each villain."""
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

        result = await query_villains.fn()

        # Verify each villain includes is_defeated status
        assert_that(len(result["data"]["villains"]), equal_to(1))
        assert_that(result["data"]["villains"][0], has_key("is_defeated"))


class TestQueryVillainsActiveFilter:
    """Test suite for query_villains MCP tool with active_only filter."""

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
    async def test_query_villains_active_only_returns_non_defeated(
        self,
        session,
        workspace,
        user,
        mock_publisher,
        mock_get_workspace_id_from_request,
    ):
        """Test that active_only filter returns only non-defeated villains."""
        # Create active villain
        active_villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Active Problem",
            villain_type=VillainType.WORKFLOW,
            description="Still a problem",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()

        # Create defeated villain
        defeated_villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Solved Problem",
            villain_type=VillainType.TECHNICAL,
            description="No longer a problem",
            severity=3,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        defeated_villain.update_villain(
            name=defeated_villain.name,
            villain_type=VillainType[defeated_villain.villain_type],
            description=defeated_villain.description,
            severity=defeated_villain.severity,
            is_defeated=True,
            publisher=mock_publisher,
        )
        session.add(defeated_villain)
        session.commit()

        result = await query_villains.fn(active_only=True)

        # Verify only active villain returned
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(len(result["data"]["villains"]), equal_to(1))
        assert_that(result["data"]["villains"][0]["name"], equal_to("Active Problem"))
        assert_that(result["data"]["villains"][0]["is_defeated"], equal_to(False))

    @pytest.mark.asyncio
    async def test_query_villains_active_only_empty_when_all_defeated(
        self,
        session,
        workspace,
        user,
        mock_publisher,
        mock_get_workspace_id_from_request,
    ):
        """Test that active_only returns empty list when all villains are defeated."""
        # Create defeated villain
        defeated_villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Solved Problem",
            villain_type=VillainType.TECHNICAL,
            description="No longer a problem",
            severity=3,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        defeated_villain.update_villain(
            name=defeated_villain.name,
            villain_type=VillainType[defeated_villain.villain_type],
            description=defeated_villain.description,
            severity=defeated_villain.severity,
            is_defeated=True,
            publisher=mock_publisher,
        )
        session.add(defeated_villain)
        session.commit()

        result = await query_villains.fn(active_only=True)

        # Verify empty list
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["villains"], equal_to([]))

    @pytest.mark.asyncio
    async def test_query_villains_active_only_counts_correctly(
        self,
        session,
        workspace,
        user,
        mock_publisher,
        mock_get_workspace_id_from_request,
    ):
        """Test that active_only correctly counts active villains."""
        # Create 3 active villains
        for i in range(3):
            villain = Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name=f"Active Problem {i}",
                villain_type=VillainType.WORKFLOW,
                description=f"Problem {i}",
                severity=i + 1,
                session=session,
                publisher=mock_publisher,
            )
            session.commit()

        # Create 2 defeated villains
        for i in range(2):
            villain = Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name=f"Solved Problem {i}",
                villain_type=VillainType.TECHNICAL,
                description=f"Solved {i}",
                severity=i + 1,
                session=session,
                publisher=mock_publisher,
            )
            session.commit()
            villain.update_villain(
                name=villain.name,
                villain_type=VillainType[villain.villain_type],
                description=villain.description,
                severity=villain.severity,
                is_defeated=True,
                publisher=mock_publisher,
            )
            session.add(villain)
            session.commit()

        result = await query_villains.fn(active_only=True)

        # Verify only 3 active villains returned
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(len(result["data"]["villains"]), equal_to(3))
        for villain in result["data"]["villains"]:
            assert_that(villain["is_defeated"], equal_to(False))

    @pytest.mark.asyncio
    async def test_query_villains_without_active_only_returns_all(
        self,
        session,
        workspace,
        user,
        mock_publisher,
        mock_get_workspace_id_from_request,
    ):
        """Test that without active_only filter, all villains are returned."""
        # Create 2 active villains
        for i in range(2):
            villain = Villain.define_villain(
                workspace_id=workspace.id,
                user_id=user.id,
                name=f"Active Problem {i}",
                villain_type=VillainType.WORKFLOW,
                description=f"Problem {i}",
                severity=i + 1,
                session=session,
                publisher=mock_publisher,
            )
            session.commit()

        # Create 1 defeated villain
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Solved Problem",
            villain_type=VillainType.TECHNICAL,
            description="Solved",
            severity=1,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        villain.update_villain(
            name=villain.name,
            villain_type=VillainType[villain.villain_type],
            description=villain.description,
            severity=villain.severity,
            is_defeated=True,
            publisher=mock_publisher,
        )
        session.add(villain)
        session.commit()

        result = await query_villains.fn(active_only=False)

        # Verify all 3 villains returned
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(len(result["data"]["villains"]), equal_to(3))


class TestSubmitVillainUpsert:
    """Test suite for submit_villain upsert MCP tool (create and update paths)."""

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
        """Create a villain for testing updates."""
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
    async def test_submit_villain_update_name_success(
        self, session, user, workspace, villain, mock_get_auth_context
    ):
        """Test successfully updating villain's name via upsert."""
        new_name = "Context Switching (Critical)"

        result = await submit_villain.fn(
            name=new_name,
            villain_type=villain.villain_type,
            description=villain.description,
            severity=villain.severity,
            villain_identifier=villain.identifier,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["name"], equal_to(new_name))

    @pytest.mark.asyncio
    async def test_submit_villain_update_severity_success(
        self, session, user, workspace, villain, mock_get_auth_context
    ):
        """Test successfully updating villain's severity via upsert."""
        new_severity = 3

        result = await submit_villain.fn(
            name=villain.name,
            villain_type=villain.villain_type,
            description=villain.description,
            severity=new_severity,
            villain_identifier=villain.identifier,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["severity"], equal_to(new_severity))

    @pytest.mark.asyncio
    async def test_submit_villain_update_type_success(
        self, session, user, workspace, villain, mock_get_auth_context
    ):
        """Test successfully updating villain's type via upsert."""
        new_type = "TECHNICAL"

        result = await submit_villain.fn(
            name=villain.name,
            villain_type=new_type,
            description=villain.description,
            severity=villain.severity,
            villain_identifier=villain.identifier,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["villain_type"], equal_to(new_type))

    @pytest.mark.asyncio
    async def test_submit_villain_update_description_success(
        self, session, user, workspace, villain, mock_get_auth_context
    ):
        """Test successfully updating villain's description via upsert."""
        new_description = "New description of the problem"

        result = await submit_villain.fn(
            name=villain.name,
            villain_type=villain.villain_type,
            description=new_description,
            severity=villain.severity,
            villain_identifier=villain.identifier,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_submit_villain_update_defeated_status(
        self, session, user, workspace, villain, mock_get_auth_context
    ):
        """Test updating villain's defeated status via upsert."""
        result = await submit_villain.fn(
            name=villain.name,
            villain_type=villain.villain_type,
            description=villain.description,
            severity=villain.severity,
            villain_identifier=villain.identifier,
            is_defeated=True,
        )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["is_defeated"], equal_to(True))

    @pytest.mark.asyncio
    async def test_submit_villain_update_all_fields_success(
        self, session, user, workspace, villain, mock_get_auth_context
    ):
        """Test updating all fields at once via upsert."""
        new_name = "Technical Debt"
        new_type = "TECHNICAL"
        new_description = "Legacy code slows development"
        new_severity = 4

        result = await submit_villain.fn(
            name=new_name,
            villain_type=new_type,
            description=new_description,
            severity=new_severity,
            villain_identifier=villain.identifier,
        )

        # Verify all fields updated
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result["data"]["name"], equal_to(new_name))
        assert_that(result["data"]["villain_type"], equal_to(new_type))
        assert_that(result["data"]["description"], equal_to(new_description))
        assert_that(result["data"]["severity"], equal_to(new_severity))

    @pytest.mark.asyncio
    async def test_submit_villain_update_invalid_type(
        self, session, user, workspace, villain, mock_get_auth_context
    ):
        """Test error when updating with invalid villain type."""
        result = await submit_villain.fn(
            name=villain.name,
            villain_type="INVALID_TYPE",
            description=villain.description,
            severity=villain.severity,
            villain_identifier=villain.identifier,
        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))
        assert_that(result["error_message"], contains_string("Invalid villain_type"))

    @pytest.mark.asyncio
    async def test_submit_villain_update_not_found(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test error when villain not found during update."""
        fake_identifier = "V-9999"

        result = await submit_villain.fn(
            name="New Name",
            villain_type="WORKFLOW",
            description="Description",
            severity=5,
            villain_identifier=fake_identifier,
        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_submit_villain_update_mcp_context_error(
        self, session, villain, mock_get_auth_context
    ):
        """Test handling of MCPContextError during update."""
        mock_get_auth_context.side_effect = MCPContextError("No workspace in context")

        result = await submit_villain.fn(
            name="New Name",
            villain_type="WORKFLOW",
            description="Description",
            severity=5,
            villain_identifier=villain.identifier,
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
    async def test_delete_villain_success(
        self,
        session: Session,
        user: User,
        workspace: Workspace,
        villain: Villain,
        mock_get_auth_context,
    ):
        """Test successfully deleting a villain."""
        villain_id = villain.id
        villain_identifier = villain.identifier

        result = await delete_villain.fn(villain_identifier=villain_identifier)

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(
            result["message"], contains_string(f"Deleted villain {villain_identifier}")
        )
        assert_that(result["data"]["deleted_identifier"], equal_to(villain_identifier))
        assert_that(result["data"]["deleted_id"], equal_to(str(villain_id)))

    @pytest.mark.asyncio
    async def test_delete_villain_not_found(
        self, session, user, workspace, mock_get_auth_context
    ):
        """Test error when villain not found."""
        fake_identifier = "V-9999"

        result = await delete_villain.fn(villain_identifier=fake_identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_delete_villain_mcp_context_error(
        self, session, villain, mock_get_auth_context
    ):
        """Test handling of MCPContextError."""
        mock_get_auth_context.side_effect = MCPContextError("No workspace in context")

        result = await delete_villain.fn(villain_identifier=villain.identifier)

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "villain"}))

    @pytest.mark.asyncio
    async def test_delete_villain_generic_exception(
        self, session, user, workspace, villain, mock_get_auth_context
    ):
        """Test handling of generic exceptions during deletion."""
        with patch(
            "src.mcp_server.prompt_driven_tools.narrative_villains.VillainService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_villain_by_identifier.side_effect = RuntimeError(
                "Unexpected database error"
            )

            result = await delete_villain.fn(villain_identifier=villain.identifier)

        # Verify error response includes server error message
        assert_that(result, has_entries({"status": "error", "type": "villain"}))
        assert_that(result["error_message"], contains_string("Server error"))
