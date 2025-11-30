"""Unit tests for draft mode functionality in submit_hero tool."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.narrative_heroes import submit_hero


class TestSubmitHeroDraftMode:
    """Test suite for submit_hero draft mode functionality."""

    @pytest.mark.asyncio
    async def test_draft_mode_returns_draft_response(self, workspace):
        """Test that draft_mode=True returns draft response without persisting."""
        name = "Sarah, The Solo Builder"
        description = "Sarah is a solo developer building a SaaS product. She's driven by wanting to ship quality products without needing a team."

        with patch(
            "src.mcp_server.prompt_driven_tools.narrative_heroes.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock validation to prevent DB queries
            with patch(
                "src.mcp_server.prompt_driven_tools.narrative_heroes.validate_hero_constraints"
            ) as mock_validate:
                mock_validate.return_value = None  # Validation passes

                # Mock get_auth_context
                with patch(
                    "src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                    # Call tool with draft_mode=True
                    result = await submit_hero.fn(
                        name, description, is_primary=True, draft_mode=True
                    )

        # Assert draft response structure
        assert_that(result, has_entries({"status": "success", "type": "hero"}))
        assert_that(result, has_key("is_draft"))
        assert_that(result["is_draft"], equal_to(True))
        assert_that(result, has_key("validation_message"))
        assert "draft" in result["validation_message"].lower()

        # Verify draft data
        assert_that(result, has_key("data"))
        data = result["data"]
        assert_that(data["id"], equal_to("00000000-0000-0000-0000-000000000000"))
        assert_that(data["identifier"], equal_to("H-DRAFT-001"))  # Temporary identifier
        assert_that(data["name"], equal_to(name))
        assert_that(data["description"], equal_to(description))
        assert_that(data["is_primary"], equal_to(True))
        assert_that(data["created_at"], equal_to("0001-01-01T00:00:00"))
        assert_that(data["updated_at"], equal_to("0001-01-01T00:00:00"))

        # Verify validation was called
        mock_validate.assert_called_once()
