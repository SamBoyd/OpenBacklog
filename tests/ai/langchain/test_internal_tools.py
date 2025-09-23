"""
Unit tests for internal_tools.py

Tests the thread-local storage management, CRUD tools, and helper functions
that are core to the new tool-based LangGraph architecture.

These tests are standalone and don't require database connections.
"""

import threading
import time
from typing import List

import pytest
from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    has_items,
    has_length,
    instance_of,
)

from src.ai.langchain.internal_tools import (
    InitiativeOperation,
    TaskOperation,
    get_all_internal_tools,
    get_internal_initiative_tools,
    get_internal_task_tools,
    internal_create_initiative,
    internal_create_task,
    internal_delete_initiative,
    internal_delete_task,
    internal_update_initiative,
    internal_update_task,
)


# Override conftest fixtures to prevent database connections
@pytest.fixture(scope="session", autouse=True)
def override_db_fixtures():
    """Override database fixtures to prevent connection attempts."""
    pass


class TestToolsReturnMessages:
    """Test that tools return proper messages without storing operations."""

    def test_tools_return_messages(self):
        """Test that all tools return appropriate confirmation messages."""
        # Task tools
        result = internal_create_task.invoke(
            {
                "initiative_identifier": "initiative-123",
                "title": "Test Task",
                "description": "Test Description",
            }
        )
        assert_that(
            result,
            equal_to(
                "Task 'Test Task' will be created on initiative 'initiative-123'."
            ),
        )

        result = internal_update_task.invoke(
            {
                "initiative_identifier": "initiative-123",
                "identifier": "task-123",
                "title": "Updated Task",
                "description": "Updated Description",
            }
        )
        assert_that(
            result,
            equal_to("Task 'task-123' on initiative 'initiative-123' will be updated."),
        )

        result = internal_delete_task.invoke(
            {"initiative_identifier": "initiative-123", "identifier": "task-456"}
        )
        assert_that(
            result,
            equal_to("Task 'task-456' on initiative 'initiative-123' will be deleted."),
        )

        # Initiative tools
        result = internal_create_initiative.invoke(
            {
                "title": "Test Initiative",
                "description": "Test Description",
                "temporary_identifier": "TEMP-INIT-test123",
            }
        )
        assert_that(
            result,
            contains_string(
                "Initiative 'Test Initiative' will be created with temporary identifier 'TEMP-INIT-test123'"
            ),
        )
        assert_that(result, contains_string("Use this identifier when creating tasks"))

        result = internal_update_initiative.invoke(
            {
                "identifier": "initiative-123",
                "title": "Updated Initiative",
                "description": "Updated Description",
            }
        )
        assert_that(result, equal_to("Initiative 'initiative-123' will be updated."))

        result = internal_delete_initiative.invoke({"identifier": "initiative-456"})
        assert_that(result, equal_to("Initiative 'initiative-456' will be deleted."))


class TestHelperFunctions:
    """Test helper functions that return tool lists."""

    def test_get_internal_task_tools(self):
        """Test that get_internal_task_tools returns exactly 3 task tools."""
        tools = get_internal_task_tools()

        assert_that(tools, has_length(3))

        # Verify tool names
        tool_names: List[str] = [tool.name for tool in tools]
        expected_names: List[str] = [
            "internal_create_task",
            "internal_update_task",
            "internal_delete_task",
        ]

        assert_that(tool_names, has_items(*expected_names))

    def test_get_internal_initiative_tools(self):
        """Test that get_internal_initiative_tools returns exactly 3 initiative tools."""
        tools = get_internal_initiative_tools()

        assert_that(tools, has_length(3))

        # Verify tool names
        tool_names = [tool.name for tool in tools]
        expected_names = [
            "internal_create_initiative",
            "internal_update_initiative",
            "internal_delete_initiative",
        ]

        assert_that(tool_names, has_items(*expected_names))

    def test_get_all_internal_tools(self):
        """Test that get_all_internal_tools returns all 6 tools combined."""
        tools = get_all_internal_tools()

        assert_that(tools, has_length(6))

        # Verify all tool names are present
        tool_names = [tool.name for tool in tools]
        expected_names = [
            "internal_create_task",
            "internal_update_task",
            "internal_delete_task",
            "internal_create_initiative",
            "internal_update_initiative",
            "internal_delete_initiative",
        ]

        assert_that(tool_names, has_items(*expected_names))


class TestDataModels:
    """Test Pydantic data models."""

    def test_task_operation_model(self):
        """Test TaskOperation creation and validation."""
        from src.ai.langchain.internal_tools import TaskCreateData

        task_data = TaskCreateData(
            initiative_identifier="test-123",
            title="Test Task",
            description="Test Description",
        )

        operation = TaskOperation(operation_type="create", task_data=task_data)

        assert_that(operation.operation_type, equal_to("create"))
        assert_that(operation.task_data.initiative_identifier, equal_to("test-123"))
        assert_that(operation.task_data.title, equal_to("Test Task"))
        assert_that(operation.task_data.description, equal_to("Test Description"))

    def test_initiative_operation_model(self):
        """Test InitiativeOperation creation and validation."""
        from src.ai.langchain.internal_tools import InitiativeUpdateData

        initiative_data = InitiativeUpdateData(
            identifier="test-123",
            title="Test Initiative",
            description="Test Description",
        )

        operation = InitiativeOperation(
            operation_type="update", initiative_data=initiative_data
        )

        assert_that(operation.operation_type, equal_to("update"))
        assert_that(operation.initiative_data.identifier, equal_to("test-123"))
        assert_that(operation.initiative_data.title, equal_to("Test Initiative"))
        assert_that(operation.initiative_data.description, equal_to("Test Description"))

    def test_model_serialization(self):
        """Test that Pydantic models serialize correctly."""
        from src.ai.langchain.internal_tools import TaskDeleteData

        task_data = TaskDeleteData(initiative_identifier="I-123", identifier="test-123")
        operation = TaskOperation(operation_type="delete", task_data=task_data)

        # Test dict conversion
        operation_dict = operation.model_dump()
        assert_that(operation_dict["operation_type"], equal_to("delete"))
        assert_that(
            operation_dict["task_data"]["initiative_identifier"], equal_to("I-123")
        )
        assert_that(operation_dict["task_data"]["identifier"], equal_to("test-123"))
