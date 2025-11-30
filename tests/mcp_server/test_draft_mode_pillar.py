"""Unit tests for draft mode functionality in submit_strategic_pillar tool."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_entries, has_key

from src.mcp_server.prompt_driven_tools.strategic_foundation import (
    submit_strategic_pillar,
)
from src.strategic_planning.aggregates.strategic_pillar import StrategicPillar
from src.strategic_planning.exceptions import DomainException


class TestSubmitStrategicPillarDraftMode:
    """Test suite for submit_strategic_pillar draft mode functionality."""

    @pytest.mark.asyncio
    async def test_draft_mode_returns_draft_response(self, workspace):
        """Test that draft_mode=True returns draft response without persisting."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock query chain for pillar limit check (count returns 0)
            mock_session.query.return_value.filter.return_value.count.return_value = 0
            # Mock query chain for uniqueness check (returns None = no duplicate)
            mock_session.query.return_value.filter_by.return_value.first.return_value = (
                None
            )

            # Mock get_auth_context
            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.get_auth_context"
            ) as mock_get_auth:
                mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                # Mock get_strategic_pillars to return empty list
                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
                ) as mock_get_pillars:
                    mock_get_pillars.return_value = []

                    result = await submit_strategic_pillar.fn(
                        name="Developer Experience",
                        description="Strategy: Make developers love our product. Anti-Strategy: No web-first UI.",
                        draft_mode=True,
                    )

        # Verify draft response structure
        assert_that(
            result, has_entries({"status": "success", "type": "strategic_pillar"})
        )
        assert_that(result, has_key("is_draft"))
        assert_that(result["is_draft"], equal_to(True))
        assert_that(result, has_key("validation_message"))
        assert "draft" in result["validation_message"].lower()

        # Verify draft data
        assert_that(result, has_key("data"))
        data = result["data"]
        assert_that(data["id"], equal_to("00000000-0000-0000-0000-000000000000"))
        assert_that(data["name"], equal_to("Developer Experience"))
        assert_that(data["created_at"], equal_to("0001-01-01T00:00:00"))
        assert_that(data["updated_at"], equal_to("0001-01-01T00:00:00"))

    @pytest.mark.asyncio
    async def test_draft_mode_validates_duplicate_name(self, workspace):
        """Test that draft mode catches duplicate pillar name."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock validation to raise DomainException for duplicate
            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.validate_pillar_constraints"
            ) as mock_validate:
                mock_validate.side_effect = DomainException(
                    "Pillar with name 'Developer Experience' already exists"
                )

                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                    with patch(
                        "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
                    ) as mock_get_pillars:
                        mock_get_pillars.return_value = []

                        result = await submit_strategic_pillar.fn(
                            name="Developer Experience",
                            description="Strategy: Duplicate. Anti-Strategy: No web.",
                            draft_mode=True,
                        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "pillar"}))
        assert_that(result, has_key("error_message"))
        assert "already exists" in result["error_message"].lower()

    @pytest.mark.asyncio
    async def test_draft_mode_validates_limit_exceeded(self, workspace):
        """Test that draft mode catches pillar limit violation."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock validation to raise DomainException for limit exceeded
            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.validate_pillar_constraints"
            ) as mock_validate:
                mock_validate.side_effect = DomainException(
                    "Workspace has reached maximum of 5 strategic pillars"
                )

                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                    # Mock 5 existing pillars
                    existing_pillars = [
                        MagicMock(spec=StrategicPillar) for _ in range(5)
                    ]
                    with patch(
                        "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
                    ) as mock_get_pillars:
                        mock_get_pillars.return_value = existing_pillars

                        result = await submit_strategic_pillar.fn(
                            name="Pillar 6",
                            description="Strategy: Too many. Anti-Strategy: No web.",
                            draft_mode=True,
                        )

        # Verify error response
        assert_that(result, has_entries({"status": "error", "type": "pillar"}))
        assert_that(result, has_key("error_message"))
        assert "maximum" in result["error_message"].lower()

    @pytest.mark.asyncio
    async def test_draft_mode_false_persists_normally(self, workspace):
        """Test that draft_mode=False persists to database (normal behavior)."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            mock_pillar = MagicMock(spec=StrategicPillar)
            mock_pillar.id = uuid.uuid4()
            mock_pillar.name = "Developer Experience"
            mock_pillar.description = "Strategy: Make devs love our product."
            mock_pillar.created_at = None
            mock_pillar.updated_at = None

            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.get_auth_context"
            ) as mock_get_auth:
                mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.create_strategic_pillar"
                ) as mock_create:
                    mock_create.return_value = mock_pillar

                    with patch(
                        "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
                    ) as mock_get_pillars:
                        mock_get_pillars.return_value = [mock_pillar]

                        result = await submit_strategic_pillar.fn(
                            name="Developer Experience",
                            description="Strategy: Make devs love our product. Anti-Strategy: No web.",
                            draft_mode=False,
                        )

        # Verify normal success response (not draft)
        assert_that(result, has_entries({"status": "success", "type": "pillar"}))
        # is_draft should not be present or should be False
        if "is_draft" in result:
            assert_that(result["is_draft"], equal_to(False))

        # Verify create_strategic_pillar was called
        mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_backward_compatibility_no_draft_mode_parameter(self, workspace):
        """Test that omitting draft_mode parameter defaults to True (draft mode)."""
        with patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.SessionLocal"
        ) as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session

            # Mock validation to prevent DB queries
            with patch(
                "src.mcp_server.prompt_driven_tools.strategic_foundation.validate_pillar_constraints"
            ) as mock_validate:
                mock_validate.return_value = None  # Validation passes

                with patch(
                    "src.mcp_server.prompt_driven_tools.strategic_foundation.get_auth_context"
                ) as mock_get_auth:
                    mock_get_auth.return_value = (str(uuid.uuid4()), str(workspace.id))

                    with patch(
                        "src.mcp_server.prompt_driven_tools.strategic_foundation.strategic_controller.get_strategic_pillars"
                    ) as mock_get_pillars:
                        mock_get_pillars.return_value = []

                        # Call without draft_mode parameter - should default to True
                        result = await submit_strategic_pillar.fn(
                            name="Developer Experience",
                            description="Strategy: Make devs love our product. Anti-Strategy: No web.",
                        )

        # Verify draft response (default is now draft_mode=True)
        assert_that(result, has_entries({"status": "success"}))
        assert_that(result, has_key("is_draft"))
        assert_that(result["is_draft"], equal_to(True))
