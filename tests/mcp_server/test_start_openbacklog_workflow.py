from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from src.mcp_server.start_openbacklog_workflow import start_openbacklog_workflow


class TestStartOpenbacklogWorkflow:
    """Test suite for start_openbacklog_workflow MCP tool."""

    @pytest.mark.asyncio
    async def test_start_openbacklog_workflow_returns_correct_structure(self):
        """Test that start_openbacklog_workflow returns the expected workflow structure."""
        with patch("src.mcp_server.start_openbacklog_workflow.logger") as mock_logger:
            result = await start_openbacklog_workflow.fn()

            # Verify basic structure
            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert result["type"] == "workflow_guidance"
            assert "workflow" in result

            # Verify workflow structure
            workflow = result["workflow"]
            assert workflow["title"] == "OpenBacklog Integration Workflow"
            assert "description" in workflow
            assert "steps" in workflow
            assert "validation_tips" in workflow

            # Verify logging was called
            mock_logger.info.assert_called_once_with(
                "Starting OpenBacklog workflow guidance"
            )

    @pytest.mark.asyncio
    async def test_workflow_contains_all_expected_steps(self):
        """Test that the workflow contains all 11 expected steps in correct order."""
        result = await start_openbacklog_workflow.fn()
        steps = result["workflow"]["steps"]

        # Verify we have all 11 steps
        assert len(steps) == 11

        # Verify step numbering is sequential
        expected_step_numbers = list(range(1, 12))
        actual_step_numbers = [step["step"] for step in steps]
        assert actual_step_numbers == expected_step_numbers

        # Verify each step has required fields
        for step in steps:
            assert "step" in step
            assert "title" in step
            assert "description" in step
            assert "action" in step
            assert "next_step" in step
            assert isinstance(step["step"], int)
            assert isinstance(step["title"], str)
            assert isinstance(step["description"], str)
            assert isinstance(step["action"], str)
            assert isinstance(step["next_step"], str)

    @pytest.mark.asyncio
    async def test_step_titles_are_correct(self):
        """Test that all step titles match expected values."""
        result = await start_openbacklog_workflow.fn()
        steps = result["workflow"]["steps"]

        expected_titles = [
            "Health Check",
            "Select Active Initiative",
            "Select Task",
            "Prioritize Task",
            "Retrieve Task Context",
            "Enter Plan Mode & Create Implementation Plan",
            "Confirm Implementation Plan",
            "Update Task Description & Checklist",
            "Execute and Track Progress",
            "Complete Task",
            "Continue Working",
        ]

        actual_titles = [step["title"] for step in steps]
        assert actual_titles == expected_titles

    @pytest.mark.asyncio
    async def test_critical_step_validations_present(self):
        """Test that critical workflow validations are present."""
        result = await start_openbacklog_workflow.fn()
        workflow = result["workflow"]

        # Check for critical step content
        steps = workflow["steps"]

        # Step 2 should mention user responsibility for prioritizing initiatives
        step_2 = next(step for step in steps if step["step"] == 2)
        assert "Claude Code does NOT prioritize initiatives" in step_2["description"]
        assert "user's responsibility" in step_2["description"]

        # Step 7 should emphasize getting explicit user confirmation
        step_7 = next(step for step in steps if step["step"] == 7)
        assert "CRITICAL" in step_7["description"]
        assert "explicit user confirmation" in step_7["description"]
        assert "DO NOT proceed without clear confirmation" in step_7["action"]

        # Step 8 should emphasize updating OpenBacklog first
        step_8 = next(step for step in steps if step["step"] == 8)
        assert "STOP" in step_8["description"]
        assert "Before writing any code" in step_8["description"]
        assert "FIRST action after user approval" in step_8["action"]

    @pytest.mark.asyncio
    async def test_validation_tips_contain_critical_requirements(self):
        """Test that validation tips contain all critical workflow requirements."""
        result = await start_openbacklog_workflow.fn()
        validation_tips = result["workflow"]["validation_tips"]

        # Verify we have validation tips
        assert isinstance(validation_tips, list)
        assert len(validation_tips) > 0

        # Convert to single string for easier searching
        all_tips = " ".join(validation_tips)

        # Check for critical requirements
        assert "validate_context()" in all_tips
        assert "plan mode" in all_tips
        assert "CRITICAL" in all_tips
        assert "MANDATORY" in all_tips
        assert "BLOCKING RULE" in all_tips
        assert "OpenBacklog updates must happen BEFORE any implementation" in all_tips
        assert "NEVER start coding" in all_tips
        assert "TodoWrite is for local session tracking" in all_tips

    @pytest.mark.asyncio
    async def test_workflow_mentions_required_tool_calls(self):
        """Test that workflow steps mention the correct MCP tool calls."""
        result = await start_openbacklog_workflow.fn()
        steps = result["workflow"]["steps"]

        # Convert all actions to single string for easier searching
        all_actions = " ".join(step["action"] for step in steps)

        # Check for expected tool calls
        expected_tools = [
            "health_check()",
            "get_active_initiatives()",
            "get_initiative_tasks(",
            "update_task_status_inprogress(",
            "get_task_details(",
            "update_task_description()",
            "update_checklist()",
            "update_checklist_item()",
            "update_task_status_done(",
        ]

        for tool in expected_tools:
            assert tool in all_actions, f"Tool {tool} not mentioned in workflow actions"

    @pytest.mark.asyncio
    async def test_workflow_emphasizes_plan_mode_entry(self):
        """Test that workflow properly emphasizes plan mode entry."""
        result = await start_openbacklog_workflow.fn()
        steps = result["workflow"]["steps"]

        # Find step 6 (Plan Mode)
        step_6 = next(step for step in steps if step["step"] == 6)

        # Check for specific plan mode entry instruction
        expected_phrase = (
            "Let me research the codebase and create a plan before implementing"
        )
        assert expected_phrase in step_6["action"]

        # Check validation tips also mention this
        validation_tips = result["workflow"]["validation_tips"]
        plan_mode_tips = [tip for tip in validation_tips if "plan mode" in tip.lower()]
        assert len(plan_mode_tips) > 0
        assert any(expected_phrase in tip for tip in plan_mode_tips)

    @pytest.mark.asyncio
    async def test_workflow_structure_immutable_across_calls(self):
        """Test that multiple calls return the same workflow structure."""
        result1 = await start_openbacklog_workflow.fn()
        result2 = await start_openbacklog_workflow.fn()

        # Both results should be identical
        assert result1 == result2

        # Specifically check that step count and structure is consistent
        assert len(result1["workflow"]["steps"]) == len(result2["workflow"]["steps"])
        assert len(result1["workflow"]["validation_tips"]) == len(
            result2["workflow"]["validation_tips"]
        )

    @pytest.mark.asyncio
    async def test_no_external_dependencies_called(self):
        """Test that the function doesn't call any external dependencies."""
        # This test ensures the function is pure and only returns static data
        with (
            patch("requests.get") as mock_requests_get,
            patch("requests.patch") as mock_requests_patch,
        ):

            result = await start_openbacklog_workflow.fn()

            # Verify no external calls were made
            mock_requests_get.assert_not_called()
            mock_requests_patch.assert_not_called()

            # But result should still be valid
            assert result["status"] == "success"
            assert result["type"] == "workflow_guidance"

    @pytest.mark.asyncio
    async def test_logging_behavior(self):
        """Test that logging works correctly."""
        with patch("src.mcp_server.start_openbacklog_workflow.logger") as mock_logger:
            result = await start_openbacklog_workflow.fn()

            # Verify logging was called with correct message
            mock_logger.info.assert_called_once_with(
                "Starting OpenBacklog workflow guidance"
            )

            # Verify result is still correct
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_workflow_step_dependencies_logical(self):
        """Test that workflow steps reference logical next steps."""
        result = await start_openbacklog_workflow.fn()
        steps = result["workflow"]["steps"]

        # Step 1 should reference step 2 on success
        step_1 = next(step for step in steps if step["step"] == 1)
        assert "proceed to step 2" in step_1["next_step"]

        # Step 3 should reference selecting a task and proceeding
        step_3 = next(step for step in steps if step["step"] == 3)
        assert "choose one task" in step_3["next_step"]

        # Step 11 should reference returning to step 3 for continuation
        step_11 = next(step for step in steps if step["step"] == 11)
        assert "return to step 3" in step_11["action"]

    @pytest.mark.asyncio
    async def test_return_type_annotations_respected(self):
        """Test that the function returns the correct type as annotated."""
        result = await start_openbacklog_workflow.fn()

        # Should return Dict[str, Any] as annotated
        assert isinstance(result, dict)

        # All top-level values should be of expected types
        assert isinstance(result["status"], str)
        assert isinstance(result["type"], str)
        assert isinstance(result["workflow"], dict)
