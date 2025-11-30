"""Unit tests for draft mode functionality in submit_villain tool."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.narrative_villains import submit_villain


class TestSubmitVillainDraftMode:
    """Test suite for submit_villain draft mode functionality."""

    @pytest.mark.asyncio
    async def test_draft_mode_returns_draft_response(self, workspace):
        """Test that draft_mode=True returns draft response without persisting."""
        name = "Context Switching"
        villain_type = (
            "WORKFLOW"  # Must be one of: EXTERNAL, INTERNAL, TECHNICAL, WORKFLOW, OTHER
        )
        description = "The constant need to switch between different tools and contexts breaks flow state and slows down development."
        severity = 3

        with patch(
            "src.mcp_server.prompt_driven_tools.narrative_villains.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock validation to prevent DB queries
            with patch(
                "src.mcp_server.prompt_driven_tools.narrative_villains.validate_villain_constraints"
            ) as mock_validate:
                mock_validate.return_value = None  # Validation passes

                # Mock get_auth_context
                with patch(
                    "src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                    # Call tool with draft_mode=True
                    result = await submit_villain.fn(
                        name, villain_type, description, severity, draft_mode=True
                    )

        # Debug: print result if it's an error
        if result.get("status") == "error":
            print(f"Error result: {result}")

        # Assert draft response structure
        assert_that(result, has_entries({"status": "success", "type": "villain"}))
        assert_that(result, has_key("is_draft"))
        assert_that(result["is_draft"], equal_to(True))
        assert_that(result, has_key("validation_message"))
        assert "draft" in result["validation_message"].lower()

        # Verify draft data
        assert_that(result, has_key("data"))
        data = result["data"]
        assert_that(data["id"], equal_to("00000000-0000-0000-0000-000000000000"))
        assert_that(data["identifier"], equal_to("V-DRAFT-001"))  # Temporary identifier
        assert_that(data["name"], equal_to(name))
        assert_that(data["description"], equal_to(description))
        assert_that(data["villain_type"], equal_to(villain_type))
        assert_that(data["severity"], equal_to(severity))
        assert_that(data["created_at"], equal_to("0001-01-01T00:00:00"))
        assert_that(data["updated_at"], equal_to("0001-01-01T00:00:00"))

        # Verify validation was called
        mock_validate.assert_called_once()
