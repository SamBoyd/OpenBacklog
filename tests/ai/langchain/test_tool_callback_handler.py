"""
Unit tests for tool_callback_handler.py

Tests the callback handler that tracks internal tool invocations.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.ai.langchain.internal_tools import (
    InitiativeCreateData,
    InitiativeDeleteData,
    InitiativeUpdateData,
    TaskCreateData,
    TaskDeleteData,
    TaskUpdateData,
)
from src.ai.langchain.tool_callback_handler import ToolCallbackHandler


class TestToolCallbackHandler:
    """Test ToolCallbackHandler functionality."""

    def setup_method(self):
        """Setup fresh callback handler for each test."""
        self.handler = ToolCallbackHandler()

    def test_init(self):
        """Test that handler initializes with empty operation lists."""
        assert len(self.handler.get_task_operations()) == 0
        assert len(self.handler.get_initiative_operations()) == 0

    def test_track_create_task(self):
        """Test tracking internal_create_task tool invocation."""
        serialized = {"name": "internal_create_task"}
        inputs = {
            "title": "Test Task",
            "description": "Test Description",
            "initiative_identifier": "I-123",
        }

        self.handler.on_tool_start(
            serialized=serialized,
            input_str="",
            run_id=uuid4(),
            parent_run_id=None,
            inputs=inputs,
        )

        operations = self.handler.get_task_operations()
        assert len(operations) == 1

        operation = operations[0]
        assert operation.operation_type == "create"
        assert isinstance(operation.task_data, TaskCreateData)
        assert operation.task_data.title == "Test Task"
        assert operation.task_data.description == "Test Description"
        assert operation.task_data.initiative_identifier == "I-123"

    def test_track_update_task(self):
        """Test tracking internal_update_task tool invocation."""
        serialized = {"name": "internal_update_task"}
        inputs = {
            "initiative_identifier": "I-123",
            "identifier": "task-123",
            "title": "Updated Task",
            "description": "Updated Description",
        }

        self.handler.on_tool_start(
            serialized=serialized, input_str="", run_id=uuid4(), inputs=inputs
        )

        operations = self.handler.get_task_operations()
        assert len(operations) == 1

        operation = operations[0]
        assert operation.operation_type == "update"
        assert isinstance(operation.task_data, TaskUpdateData)
        assert operation.task_data.initiative_identifier == "I-123"
        assert operation.task_data.identifier == "task-123"
        assert operation.task_data.title == "Updated Task"
        assert operation.task_data.description == "Updated Description"

    def test_track_delete_task(self):
        """Test tracking internal_delete_task tool invocation."""
        serialized = {"name": "internal_delete_task"}
        inputs = {"initiative_identifier": "I-123", "identifier": "task-456"}

        self.handler.on_tool_start(
            serialized=serialized, input_str="", run_id=uuid4(), inputs=inputs
        )

        operations = self.handler.get_task_operations()
        assert len(operations) == 1

        operation = operations[0]
        assert operation.operation_type == "delete"
        assert isinstance(operation.task_data, TaskDeleteData)
        assert operation.task_data.initiative_identifier == "I-123"
        assert operation.task_data.identifier == "task-456"

    def test_track_create_initiative(self):
        """Test tracking internal_create_initiative tool invocation."""
        serialized = {"name": "internal_create_initiative"}
        inputs = {
            "temporary_identifier": "TEMP-INIT-123",
            "title": "Test Initiative",
            "description": "Test Description",
        }

        self.handler.on_tool_start(
            serialized=serialized, input_str="", run_id=uuid4(), inputs=inputs
        )

        operations = self.handler.get_initiative_operations()
        assert len(operations) == 1

        operation = operations[0]
        assert operation.operation_type == "create"
        assert isinstance(operation.initiative_data, InitiativeCreateData)
        assert operation.initiative_data.temporary_identifier == "TEMP-INIT-123"
        assert operation.initiative_data.title == "Test Initiative"
        assert operation.initiative_data.description == "Test Description"

    def test_track_update_initiative(self):
        """Test tracking internal_update_initiative tool invocation."""
        serialized = {"name": "internal_update_initiative"}
        inputs = {
            "identifier": "initiative-123",
            "title": "Updated Initiative",
            "description": "Updated Description",
        }

        self.handler.on_tool_start(
            serialized=serialized, input_str="", run_id=uuid4(), inputs=inputs
        )

        operations = self.handler.get_initiative_operations()
        assert len(operations) == 1

        operation = operations[0]
        assert operation.operation_type == "update"
        assert isinstance(operation.initiative_data, InitiativeUpdateData)
        assert operation.initiative_data.identifier == "initiative-123"
        assert operation.initiative_data.title == "Updated Initiative"
        assert operation.initiative_data.description == "Updated Description"

    def test_track_delete_initiative(self):
        """Test tracking internal_delete_initiative tool invocation."""
        serialized = {"name": "internal_delete_initiative"}
        inputs = {"identifier": "initiative-456"}

        self.handler.on_tool_start(
            serialized=serialized, input_str="", run_id=uuid4(), inputs=inputs
        )

        operations = self.handler.get_initiative_operations()
        assert len(operations) == 1

        operation = operations[0]
        assert operation.operation_type == "delete"
        assert isinstance(operation.initiative_data, InitiativeDeleteData)
        assert operation.initiative_data.identifier == "initiative-456"

    def test_ignore_non_internal_tools(self):
        """Test that non-internal tools are ignored."""
        serialized = {"name": "some_other_tool"}
        inputs = {"param": "value"}

        self.handler.on_tool_start(
            serialized=serialized, input_str="", run_id=uuid4(), inputs=inputs
        )

        # Should not track anything
        assert len(self.handler.get_task_operations()) == 0
        assert len(self.handler.get_initiative_operations()) == 0

    def test_multiple_operations(self):
        """Test tracking multiple operations."""
        # Add a task operation
        self.handler.on_tool_start(
            serialized={"name": "internal_create_task"},
            input_str="",
            run_id=uuid4(),
            inputs={
                "initiative_identifier": "I-123",
                "title": "Task 1",
                "description": "Description 1",
            },
        )

        # Add an initiative operation
        self.handler.on_tool_start(
            serialized={"name": "internal_create_initiative"},
            input_str="",
            run_id=uuid4(),
            inputs={
                "temporary_identifier": "TEMP-INIT-123",
                "title": "Initiative 1",
                "description": "Description 1",
            },
        )

        # Add another task operation
        self.handler.on_tool_start(
            serialized={"name": "internal_update_task"},
            input_str="",
            run_id=uuid4(),
            inputs={
                "initiative_identifier": "I-123",
                "identifier": "task-2",
                "title": "Task 2",
                "description": "Description 2",
            },
        )

        task_ops = self.handler.get_task_operations()
        initiative_ops = self.handler.get_initiative_operations()

        assert len(task_ops) == 2
        assert len(initiative_ops) == 1

        assert task_ops[0].operation_type == "create"
        assert task_ops[1].operation_type == "update"
        assert initiative_ops[0].operation_type == "create"

    def test_clear_operations(self):
        """Test clearing operations."""
        # Add some operations
        self.handler.on_tool_start(
            serialized={"name": "internal_create_task"},
            input_str="",
            run_id=uuid4(),
            inputs={
                "initiative_identifier": "I-123",
                "title": "Task",
                "description": "Description",
            },
        )

        self.handler.on_tool_start(
            serialized={"name": "internal_create_initiative"},
            input_str="",
            run_id=uuid4(),
            inputs={
                "temporary_identifier": "TEMP-INIT-123",
                "title": "Initiative",
                "description": "Description",
            },
        )

        # Verify operations exist
        assert len(self.handler.get_task_operations()) == 1
        assert len(self.handler.get_initiative_operations()) == 1

        # Clear operations
        self.handler.clear_operations()

        # Verify operations are cleared
        assert len(self.handler.get_task_operations()) == 0
        assert len(self.handler.get_initiative_operations()) == 0

    def test_exception_handling(self):
        """Test that exceptions during operation tracking don't crash the handler."""
        # This simulates what might happen if inputs are malformed
        serialized = {"name": "internal_create_task"}
        inputs = {}  # Missing required fields

        # Should not raise an exception
        self.handler.on_tool_start(
            serialized=serialized, input_str="", run_id=uuid4(), inputs=inputs
        )

        # Should not have tracked anything due to missing fields
        assert len(self.handler.get_task_operations()) == 0
