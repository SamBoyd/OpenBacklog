"""
Unit tests for langchain_service MCP tool filtering functionality.
"""

from unittest.mock import Mock

import pytest

from src.ai.langchain.langchain_service import ALLOWED_MCP_TOOLS, filter_mcp_tools


class TestMCPToolFiltering:
    """Test suite for MCP tool filtering."""

    def test_filter_mcp_tools_allows_search_tools(self):
        """Test that search tools are included in filtered results."""
        # Create mock tools
        search_tasks_tool = Mock()
        search_tasks_tool.name = "search_tasks"

        search_initiatives_tool = Mock()
        search_initiatives_tool.name = "search_initiatives"

        all_tools = [search_tasks_tool, search_initiatives_tool]

        # Filter tools
        filtered = filter_mcp_tools(all_tools)

        # Assert both search tools are included
        assert len(filtered) == 2
        assert search_tasks_tool in filtered
        assert search_initiatives_tool in filtered

    def test_filter_mcp_tools_blocks_update_tools(self):
        """Test that update/status tools are filtered out."""
        # Create mock tools
        search_tool = Mock()
        search_tool.name = "search_tasks"

        update_tool = Mock()
        update_tool.name = "update_task_description"

        status_tool = Mock()
        status_tool.name = "update_task_status_inprogress"

        all_tools = [search_tool, update_tool, status_tool]

        # Filter tools
        filtered = filter_mcp_tools(all_tools)

        # Assert only search tool is included
        assert len(filtered) == 1
        assert search_tool in filtered
        assert update_tool not in filtered
        assert status_tool not in filtered

    def test_filter_mcp_tools_allows_get_details_tools(self):
        """Test that get_details and lookup tools are included."""
        # Create mock tools
        get_task_details = Mock()
        get_task_details.name = "get_task_details"

        get_initiative_tasks = Mock()
        get_initiative_tasks.name = "get_initiative_tasks"

        all_tools = [get_task_details, get_initiative_tasks]

        # Filter tools
        filtered = filter_mcp_tools(all_tools)

        # Assert both lookup tools are included
        assert len(filtered) == 2
        assert get_task_details in filtered
        assert get_initiative_tasks in filtered

    def test_filter_mcp_tools_empty_list(self):
        """Test filtering with empty tool list."""
        filtered = filter_mcp_tools([])
        assert len(filtered) == 0
        assert filtered == []

    def test_filter_mcp_tools_no_allowed_tools(self):
        """Test filtering when no tools match allowed list."""
        # Create mock tools that aren't in ALLOWED_MCP_TOOLS
        disallowed_tool1 = Mock()
        disallowed_tool1.name = "update_checklist"

        disallowed_tool2 = Mock()
        disallowed_tool2.name = "validate_context"

        all_tools = [disallowed_tool1, disallowed_tool2]

        # Filter tools
        filtered = filter_mcp_tools(all_tools)

        # Assert no tools are included
        assert len(filtered) == 0

    def test_filter_mcp_tools_with_all_types(self):
        """Test filtering with mix of allowed and disallowed tools."""
        # Create mock tools
        search_tool = Mock()
        search_tool.name = "search_tasks"

        get_details_tool = Mock()
        get_details_tool.name = "get_task_details"

        update_tool = Mock()
        update_tool.name = "update_task_description"

        checklist_tool = Mock()
        checklist_tool.name = "update_checklist"

        health_tool = Mock()
        health_tool.name = "health_check"

        all_tools = [
            search_tool,
            get_details_tool,
            update_tool,
            checklist_tool,
            health_tool,
        ]

        # Filter tools
        filtered = filter_mcp_tools(all_tools)

        # Assert only search and lookup tools are included
        assert len(filtered) == 2
        assert search_tool in filtered
        assert get_details_tool in filtered
        assert update_tool not in filtered
        assert checklist_tool not in filtered
        assert health_tool not in filtered

    def test_allowed_mcp_tools_constant(self):
        """Test that ALLOWED_MCP_TOOLS contains expected tools."""
        # This ensures the constant doesn't change unexpectedly
        expected_tools = {
            "search_tasks",
            "search_initiatives",
            "get_task_details",
            "get_initiative_tasks",
            "get_initiative_details",
        }

        assert ALLOWED_MCP_TOOLS == expected_tools

    def test_filter_mcp_tools_handles_missing_name_attribute(self):
        """Test that filtering handles tools without name attribute gracefully."""
        # Create mock tool without name attribute
        bad_tool = Mock(spec=[])  # spec=[] means no attributes

        search_tool = Mock()
        search_tool.name = "search_tasks"

        all_tools = [bad_tool, search_tool]

        # Filter tools - should not raise error
        filtered = filter_mcp_tools(all_tools)

        # Only the valid search tool should be included
        assert len(filtered) == 1
        assert search_tool in filtered
        assert bad_tool not in filtered
