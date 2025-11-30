"""Unit tests for draft mode functionality in create_conflict tool."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.narrative_conflicts import create_conflict
from src.models import Workspace


class TestCreateConflictDraftMode:
    """Test suite for create_conflict draft mode functionality."""

    @pytest.mark.asyncio
    async def test_draft_mode_returns_draft_response(self, workspace: Workspace):
        """Test that draft_mode=True returns draft response without persisting."""
        hero_identifier = "H-2003"
        villain_identifier = "V-2003"
        description = "Sarah cannot access product context from IDE, forcing constant tool switching that breaks her flow state."

        with patch(
            "src.mcp_server.prompt_driven_tools.narrative_conflicts.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock get_auth_context
            with patch(
                "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
            ) as mock_get_auth:
                mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                # Call tool with draft_mode=True
                result = await create_conflict.fn(
                    hero_identifier, villain_identifier, description, draft_mode=True
                )

        # Assert draft response structure
        assert_that(result, has_entries({"status": "success", "type": "conflict"}))
        assert_that(result, has_key("is_draft"))
        assert_that(result["is_draft"], equal_to(True))
        assert_that(result, has_key("validation_message"))
        assert "draft" in result["validation_message"].lower()

        # Verify draft data
        assert_that(result, has_key("data"))
        data = result["data"]
        assert_that(data["id"], equal_to("00000000-0000-0000-0000-000000000000"))
        assert_that(data["hero_identifier"], equal_to(hero_identifier))
        assert_that(data["villain_identifier"], equal_to(villain_identifier))
        assert_that(data["description"], equal_to(description))
        assert_that(data["created_at"], equal_to("0001-01-01T00:00:00"))
        assert_that(data["updated_at"], equal_to("0001-01-01T00:00:00"))
