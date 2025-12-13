"""Unit tests for narrative conflict MCP tools.

Tests verify that get_conflict_details, update_conflict and delete_conflict tools work correctly,
handle errors appropriately, and emit domain events when expected.

Pattern: Tool calls aggregate methods → verifies success response → validates db state
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    has_entries,
    has_key,
    not_none,
)
from sqlalchemy.orm import Session

from src.mcp_server.auth_utils import MCPContextError
from src.mcp_server.prompt_driven_tools.narrative_conflicts import (
    delete_conflict,
    get_conflict_details,
    update_conflict,
)
from src.models import User, Workspace
from src.narrative.aggregates.conflict import Conflict
from src.narrative.aggregates.hero import Hero
from src.narrative.aggregates.villain import Villain, VillainType
from src.narrative.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestGetConflictDetails:
    """Test suite for get_conflict_details MCP tool."""

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
    def hero(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Hero:
        """Create a Hero instance for testing."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.fixture
    def villain(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Villain:
        """Create a Villain instance for testing."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow.",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.fixture
    def conflict(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Conflict:
        """Create a Conflict instance for testing."""
        conflict = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Sarah cannot access product context from IDE.",
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(conflict)
        return conflict

    @pytest.mark.asyncio
    async def test_get_conflict_details_success(
        self, session: Session, conflict: Conflict, hero: Hero, villain: Villain
    ):
        """Test successfully retrieving conflict details."""
        result = await get_conflict_details.fn(
            conflict_identifier=conflict.identifier,
        )

        assert_that(result, has_entries({"status": "success", "type": "conflict"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["identifier"], equal_to(conflict.identifier))
        assert_that(result["data"]["hero_name"], equal_to("Sarah, The Solo Builder"))
        assert_that(result["data"]["villain_name"], equal_to("Context Switching"))
        assert_that(result["data"]["theme_name"], equal_to(None))

    @pytest.mark.asyncio
    async def test_get_conflict_details_not_found(self, session: Session):
        """Test error when conflict not found."""
        result = await get_conflict_details.fn(
            conflict_identifier="C-9999",
        )

        assert_that(result, has_entries({"status": "error", "type": "conflict"}))
        assert_that(result, has_key("error_message"))


class TestUpdateConflict:
    """Test suite for update_conflict MCP tool."""

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
    def hero(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Hero:
        """Create a Hero instance for testing."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.fixture
    def villain(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Villain:
        """Create a Villain instance for testing."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow.",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.fixture
    def conflict(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Conflict:
        """Create a Conflict instance for testing."""
        conflict = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Sarah cannot access product context from IDE.",
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(conflict)
        return conflict

    @pytest.mark.asyncio
    async def test_update_conflict_description_success(
        self, session: Session, conflict: Conflict
    ):
        """Test successfully updating a conflict's description."""
        new_description = (
            "Sarah cannot access product context from IDE, causing lost time."
        )

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            result = await update_conflict.fn(
                conflict_identifier=conflict.identifier,
                description=new_description,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "conflict"}))
        assert_that(result, has_key("data"))
        assert_that(result["data"]["identifier"], equal_to(conflict.identifier))
        assert_that(result["data"]["description"], equal_to(new_description))

        # Verify database was updated
        updated_conflict = session.query(Conflict).filter_by(id=conflict.id).first()
        assert_that(updated_conflict, not_none())
        assert_that(
            updated_conflict.description, equal_to(new_description)
        )  # pyright: ignore[reportOptionalMemberAccess]

    @pytest.mark.asyncio
    async def test_update_conflict_roadmap_theme_identifier_linking_fails_without_roadmap_theme(
        self, session: Session, conflict: Conflict
    ):
        """Test that linking to non-existent roadmap theme fails with FK constraint."""
        invalid_theme_identifier = "T-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            result = await update_conflict.fn(
                conflict_identifier=conflict.identifier,
                roadmap_theme_identifier=invalid_theme_identifier,
            )

        # Verify error response due to theme not found
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_update_conflict_both_fields_success(
        self, session: Session, conflict: Conflict
    ):
        """Test successfully updating both description and unlinking roadmap theme."""
        new_description = "Updated description"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            result = await update_conflict.fn(
                conflict_identifier=conflict.identifier,
                description=new_description,
                roadmap_theme_identifier="null",
            )

        # Verify both fields updated
        assert_that(result, has_entries({"status": "success", "type": "conflict"}))
        assert_that(result["data"]["description"], equal_to(new_description))

    @pytest.mark.asyncio
    async def test_update_conflict_unlink_roadmap_theme_with_null(
        self, session: Session, conflict: Conflict
    ):
        """Test unlinking conflict from roadmap theme using 'null' string."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            result = await update_conflict.fn(
                conflict_identifier=conflict.identifier,
                roadmap_theme_identifier="null",
            )

        # Verify roadmap theme unlinked
        assert_that(result, has_entries({"status": "success", "type": "conflict"}))
        assert_that(result["data"]["roadmap_theme_identifier"], equal_to(None))

    @pytest.mark.asyncio
    async def test_update_conflict_unlink_roadmap_theme_with_empty_string(
        self, session: Session, conflict: Conflict
    ):
        """Test unlinking conflict from roadmap theme using empty string."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            result = await update_conflict.fn(
                conflict_identifier=conflict.identifier,
                roadmap_theme_identifier="",
            )

        # Verify roadmap theme unlinked
        assert_that(result, has_entries({"status": "success", "type": "conflict"}))
        assert_that(result["data"]["roadmap_theme_identifier"], equal_to(None))

    @pytest.mark.asyncio
    async def test_update_conflict_no_fields_provided_error(
        self, session: Session, conflict: Conflict
    ):
        """Test error when no fields provided for update."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            result = await update_conflict.fn(
                conflict_identifier=conflict.identifier,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))
        assert_that(result, has_key("error_message"))
        assert_that(
            result.get("error_message", ""), contains_string("At least one field")
        )

    @pytest.mark.asyncio
    async def test_update_conflict_invalid_roadmap_theme_identifier_format(
        self, session: Session, conflict: Conflict
    ):
        """Test error when roadmap_theme_identifier is invalid."""
        invalid_identifier = "INVALID-ID"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            result = await update_conflict.fn(
                conflict_identifier=conflict.identifier,
                roadmap_theme_identifier=invalid_identifier,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_update_conflict_not_found_error(
        self, session: Session, conflict: Conflict
    ):
        """Test error when conflict not found."""
        fake_identifier = "C-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.ConflictService"
            ) as mock_service_class,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_conflict_by_identifier.side_effect = DomainException(
                f"Conflict {fake_identifier} not found"
            )

            result = await update_conflict.fn(
                conflict_identifier=fake_identifier,
                description="New description",
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_update_conflict_mcp_context_error(
        self, session: Session, conflict: Conflict
    ):
        """Test handling of MCPContextError."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await update_conflict.fn(
                conflict_identifier=conflict.identifier,
                description="New description",
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))

    @pytest.mark.asyncio
    async def test_update_conflict_preserves_other_fields(
        self, session: Session, conflict: Conflict
    ):
        """Test that updating one field doesn't modify other fields."""
        original_hero_id = conflict.hero_id
        original_villain_id = conflict.villain_id
        original_status = conflict.status
        new_description = "Updated description"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            await update_conflict.fn(
                conflict_identifier=conflict.identifier,
                description=new_description,
            )

        # Verify immutable fields unchanged
        updated_conflict = session.query(Conflict).filter_by(id=conflict.id).first()
        assert_that(update_conflict, not_none())
        assert_that(
            updated_conflict.hero_id, equal_to(original_hero_id)
        )  # pyright: ignore[reportOptionalMemberAccess]
        assert_that(
            updated_conflict.villain_id, equal_to(original_villain_id)
        )  # pyright: ignore[reportOptionalMemberAccess]
        assert_that(
            updated_conflict.status, equal_to(original_status)
        )  # pyright: ignore[reportOptionalMemberAccess]


class TestDeleteConflict:
    """Test suite for delete_conflict MCP tool."""

    @pytest.fixture
    def workspace(self, user: User, session: Session) -> Workspace:
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
    def hero(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Hero:
        """Create a Hero instance for testing."""
        hero = Hero.define_hero(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Sarah, The Solo Builder",
            description="Sarah is a solo developer.",
            is_primary=True,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(hero)
        return hero

    @pytest.fixture
    def villain(
        self,
        workspace: Workspace,
        user: User,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Villain:
        """Create a Villain instance for testing."""
        villain = Villain.define_villain(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Context Switching",
            villain_type=VillainType.WORKFLOW,
            description="Jumping between tools breaks flow.",
            severity=5,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(villain)
        return villain

    @pytest.fixture
    def conflict(
        self,
        workspace: Workspace,
        user: User,
        hero: Hero,
        villain: Villain,
        session: Session,
        mock_publisher: MagicMock,
    ) -> Conflict:
        """Create a Conflict instance for testing."""
        conflict = Conflict.create_conflict(
            workspace_id=workspace.id,
            user_id=user.id,
            hero_id=hero.id,
            villain_id=villain.id,
            description="Sarah cannot access product context from IDE.",
            roadmap_theme_id=None,
            session=session,
            publisher=mock_publisher,
        )
        session.commit()
        session.refresh(conflict)
        return conflict

    @pytest.mark.asyncio
    async def test_delete_conflict_success(self, session: Session, conflict: Conflict):
        """Test successfully deleting a conflict."""
        conflict_id = conflict.id
        conflict_identifier = conflict.identifier

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            result = await delete_conflict.fn(
                conflict_identifier=conflict_identifier,
            )

        # Verify success response
        assert_that(result, has_entries({"status": "success", "type": "conflict"}))
        assert_that(
            result["message"],
            contains_string(f"Deleted conflict {conflict_identifier}"),
        )
        assert_that(result["data"]["deleted_identifier"], equal_to(conflict_identifier))
        assert_that(result["data"]["deleted_id"], equal_to(str(conflict_id)))

        # Verify deleted from database
        deleted_conflict = session.query(Conflict).filter_by(id=conflict_id).first()
        assert_that(deleted_conflict, equal_to(None))

    @pytest.mark.asyncio
    async def test_delete_conflict_not_found_error(
        self, session: Session, conflict: Conflict
    ):
        """Test error when conflict not found."""
        fake_identifier = "C-9999"

        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.ConflictService"
            ) as mock_service_class,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_conflict_by_identifier.side_effect = DomainException(
                f"Conflict {fake_identifier} not found"
            )

            result = await delete_conflict.fn(
                conflict_identifier=fake_identifier,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))
        assert_that(result, has_key("error_message"))

    @pytest.mark.asyncio
    async def test_delete_conflict_mcp_context_error(
        self, session: Session, conflict: Conflict
    ):
        """Test handling of MCPContextError."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
        ):
            mock_session_local.return_value = session
            mock_auth.side_effect = MCPContextError("No workspace in context")

            result = await delete_conflict.fn(
                conflict_identifier=conflict.identifier,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))

    @pytest.mark.asyncio
    async def test_delete_conflict_domain_exception_handling(
        self, session: Session, conflict: Conflict
    ):
        """Test handling of domain exceptions during deletion."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.ConflictService"
            ) as mock_service_class,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_conflict_by_identifier.side_effect = DomainException(
                "Conflict validation failed"
            )

            result = await delete_conflict.fn(
                conflict_identifier=conflict.identifier,
            )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))

    @pytest.mark.asyncio
    async def test_delete_conflict_generic_exception_handling(
        self, session: Session, conflict: Conflict
    ):
        """Test handling of generic exceptions during deletion."""
        with (
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
            ) as mock_session_local,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_auth,
            patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.ConflictService"
            ) as mock_service_class,
        ):
            mock_session_local.return_value = session
            mock_auth.return_value = (str(conflict.user_id), str(conflict.workspace_id))

            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_conflict_by_identifier.side_effect = RuntimeError(
                "Unexpected database error"
            )

            result = await delete_conflict.fn(
                conflict_identifier=conflict.identifier,
            )

        # Verify error response includes server error message
        assert_that(result, has_entries({"status": "error", "type": "conflict"}))
        assert_that(result, has_key("error_message"))
