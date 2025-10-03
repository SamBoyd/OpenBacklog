"""
Unit tests for response_builder.py

Tests the ResponseBuilder class that converts internal tool operations
into structured API responses for the LangGraph architecture.

These tests are standalone and don't require database connections.
"""

from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_length, instance_of

from src.ai.langchain.internal_tools import (
    InitiativeCreateData,
    InitiativeDeleteData,
    InitiativeOperation,
    InitiativeUpdateData,
    TaskCreateData,
    TaskDeleteData,
    TaskOperation,
    TaskUpdateData,
)
from src.ai.langchain.response_builder import ResponseBuilder
from src.ai.models import (
    EasyCreateInitiativeModel,
    EasyCreateTaskModel,
    EasyDeleteInitiativeModel,
    EasyDeleteTaskModel,
    EasyInitiativeLLMResponse,
    EasyTaskLLMResponse,
    EasyUpdateInitiativeModel,
    EasyUpdateTaskModel,
)
from src.models import BalanceWarning


# Override conftest fixtures to prevent database connections
@pytest.fixture(scope="session", autouse=True)
def override_db_fixtures():
    """Override database fixtures to prevent connection attempts."""
    pass


@pytest.fixture(scope="function")
def session():
    """Override session fixture from conftest to prevent database connections."""
    pass


@pytest.fixture
def user():
    """Override user fixture from conftest to prevent database connections."""
    pass


@pytest.fixture
def workspace():
    """Override workspace fixture from conftest to prevent database connections."""
    pass


@pytest.fixture(scope="function")
def test_initiative():
    """Override test_initiative fixture from conftest to prevent database connections."""
    pass


@pytest.fixture(scope="function")
def test_task():
    """Override test_task fixture from conftest to prevent database connections."""
    pass


@pytest.fixture(scope="function")
def test_user_key():
    """Override test_user_key fixture from conftest to prevent database connections."""
    pass


@pytest.fixture
def test_client():
    """Override test_client fixture from conftest to prevent database connections."""
    pass


@pytest.fixture
def test_client_no_user():
    """Override test_client_no_user fixture from conftest to prevent database connections."""
    pass


@pytest.fixture(autouse=True)
def clean_tables():
    """Override clean_tables fixture from conftest to prevent database connections."""
    pass


@pytest.fixture
def cli_args():
    """Override cli_args fixture from conftest to prevent database connections."""
    pass


@pytest.fixture
def run_cli_command():
    """Override run_cli_command fixture from conftest to prevent database connections."""
    pass


@pytest.fixture(autouse=True)
def mock_litellm_model_cost():
    """Override mock_litellm_model_cost fixture from conftest to prevent database connections."""
    pass


class TestResponseBuilder:
    """Test ResponseBuilder initialization and basic functionality."""

    def test_init(self):
        """Test ResponseBuilder can be initialized."""
        builder = ResponseBuilder()
        assert_that(builder, instance_of(ResponseBuilder))


class TestTaskResponseBuilding:
    """Test task response building functionality."""

    def setup_method(self):
        """Clean setup for each test."""
        self.builder = ResponseBuilder()

    def test_build_task_response_empty(self):
        """Test building task response with no operations."""
        operations = []

        response = self.builder.build_task_response("Test message", operations)

        assert_that(response, instance_of(EasyTaskLLMResponse))
        assert_that(response.message, equal_to("Test message"))
        assert_that(response.created_tasks, equal_to([]))
        assert_that(response.updated_tasks, equal_to([]))
        assert_that(response.deleted_tasks, equal_to([]))
        assert_that(response.balance_warning, equal_to(None))

    def test_build_task_response_create_operation(self):
        """Test building task response with create operation."""
        create_data = TaskCreateData(
            initiative_identifier="I-001",
            title="New Task",
            description="Task description",
        )
        operation = TaskOperation(operation_type="create", task_data=create_data)
        operations = [operation]

        response = self.builder.build_task_response("Task created", operations)

        assert_that(response.message, equal_to("Task created"))
        assert_that(response.created_tasks, has_length(1))
        assert_that(response.updated_tasks, has_length(0))
        assert_that(response.deleted_tasks, has_length(0))

        created_task = response.created_tasks[0]
        assert_that(created_task, instance_of(EasyCreateTaskModel))
        assert_that(created_task.title, equal_to("New Task"))
        assert_that(created_task.description, equal_to("Task description"))
        assert_that(created_task.checklist, equal_to([]))

    def test_build_task_response_update_operation(self):
        """Test building task response with update operation."""
        update_data = TaskUpdateData(
            identifier="task-123",
            initiative_identifier="I-001",
            title="Updated Task",
            description="Updated description",
        )
        operation = TaskOperation(operation_type="update", task_data=update_data)
        operations = [operation]

        response = self.builder.build_task_response("Task updated", operations)

        assert_that(response.message, equal_to("Task updated"))
        assert_that(response.created_tasks, has_length(0))
        assert_that(response.updated_tasks, has_length(1))
        assert_that(response.deleted_tasks, has_length(0))

        updated_task = response.updated_tasks[0]
        assert_that(updated_task, instance_of(EasyUpdateTaskModel))
        assert_that(updated_task.identifier, equal_to("task-123"))
        assert_that(updated_task.title, equal_to("Updated Task"))
        assert_that(updated_task.description, equal_to("Updated description"))
        assert_that(updated_task.checklist, equal_to([]))

    def test_build_task_response_delete_operation(self):
        """Test building task response with delete operation."""
        delete_data = TaskDeleteData(
            identifier="task-to-delete", initiative_identifier="I-001"
        )
        operation = TaskOperation(operation_type="delete", task_data=delete_data)
        operations = [operation]

        response = self.builder.build_task_response("Task deleted", operations)

        assert_that(response.message, equal_to("Task deleted"))
        assert_that(response.created_tasks, has_length(0))
        assert_that(response.updated_tasks, has_length(0))
        assert_that(response.deleted_tasks, has_length(1))

        deleted_task = response.deleted_tasks[0]
        assert_that(deleted_task, instance_of(EasyDeleteTaskModel))
        assert_that(deleted_task.identifier, equal_to("task-to-delete"))

    def test_build_task_response_multiple_operations(self):
        """Test building task response with multiple operations."""
        create_data = TaskCreateData(
            initiative_identifier="I-001", title="Task 1", description="Description 1"
        )
        update_data = TaskUpdateData(
            identifier="task-2",
            initiative_identifier="I-002",
            title="Task 2",
            description="Description 2",
        )
        delete_data = TaskDeleteData(identifier="task-3", initiative_identifier="I-003")

        operations = [
            TaskOperation(operation_type="create", task_data=create_data),
            TaskOperation(operation_type="update", task_data=update_data),
            TaskOperation(operation_type="delete", task_data=delete_data),
        ]

        response = self.builder.build_task_response("Multiple operations", operations)

        assert_that(response.created_tasks, has_length(1))
        assert_that(response.updated_tasks, has_length(1))
        assert_that(response.deleted_tasks, has_length(1))

    def test_build_task_response_with_balance_warning(self):
        """Test building task response with balance warning."""
        operations = []
        balance_warning = BalanceWarning(message="Low balance")

        response = self.builder.build_task_response(
            "Test message", operations, balance_warning
        )

        assert_that(response.balance_warning, equal_to(balance_warning))

    @patch("src.ai.langchain.response_builder.logger")
    def test_build_task_response_exception_handling(self, mock_logger):
        """Test that exceptions during task model creation are handled gracefully."""
        # Create a malformed operation that will cause an exception
        operation = MagicMock()
        operation.operation_type = "create"
        operation.task_data = MagicMock()
        operation.task_data.title = None  # This should cause validation error

        operations = [operation]

        response = self.builder.build_task_response("Test message", operations)

        # Response should still be created but with empty lists
        assert_that(response.created_tasks, has_length(0))
        assert_that(response.updated_tasks, has_length(0))
        assert_that(response.deleted_tasks, has_length(0))

        # Logger should have been called for the exception
        mock_logger.exception.assert_called()


class TestInitiativeResponseBuilding:
    """Test initiative response building functionality."""

    def setup_method(self):
        """Clean setup for each test."""
        self.builder = ResponseBuilder()

    def test_build_initiative_response_empty(self):
        """Test building initiative response with no operations."""
        operations = []

        response = self.builder.build_initiative_response(
            "Test message", operations, []
        )

        assert_that(response, instance_of(EasyInitiativeLLMResponse))
        assert_that(response.message, equal_to("Test message"))
        assert_that(response.created_initiatives, equal_to([]))
        assert_that(response.updated_initiatives, equal_to([]))
        assert_that(response.deleted_initiatives, equal_to([]))
        assert_that(response.balance_warning, equal_to(None))

    def test_build_initiative_response_create_operation(self):
        """Test building initiative response with create operation."""
        create_data = InitiativeCreateData(
            title="New Initiative",
            description="Initiative description",
            temporary_identifier="TEMP-INIT-test123",
        )
        operation = InitiativeOperation(
            operation_type="create", initiative_data=create_data
        )
        operations = [operation]

        response = self.builder.build_initiative_response(
            "Initiative created", operations, []
        )

        assert_that(response.message, equal_to("Initiative created"))
        assert_that(response.created_initiatives, has_length(1))
        assert_that(response.updated_initiatives, has_length(0))
        assert_that(response.deleted_initiatives, has_length(0))

        created_initiative = response.created_initiatives[0]
        assert_that(created_initiative, instance_of(EasyCreateInitiativeModel))
        assert_that(created_initiative.title, equal_to("New Initiative"))
        assert_that(created_initiative.description, equal_to("Initiative description"))
        assert_that(created_initiative.tasks, equal_to([]))

    def test_build_initiative_response_update_operation(self):
        """Test building initiative response with update operation."""
        update_data = InitiativeUpdateData(
            identifier="initiative-123",
            title="Updated Initiative",
            description="Updated description",
        )
        operation = InitiativeOperation(
            operation_type="update", initiative_data=update_data
        )
        operations = [operation]

        response = self.builder.build_initiative_response(
            "Initiative updated", operations, []
        )

        assert_that(response.message, equal_to("Initiative updated"))
        assert_that(response.created_initiatives, has_length(0))
        assert_that(response.updated_initiatives, has_length(1))
        assert_that(response.deleted_initiatives, has_length(0))

        updated_initiative = response.updated_initiatives[0]
        assert_that(updated_initiative, instance_of(EasyUpdateInitiativeModel))
        assert_that(updated_initiative.identifier, equal_to("initiative-123"))
        assert_that(updated_initiative.title, equal_to("Updated Initiative"))
        assert_that(updated_initiative.description, equal_to("Updated description"))
        assert_that(updated_initiative.task, equal_to([]))

    def test_build_initiative_response_delete_operation(self):
        """Test building initiative response with delete operation."""
        delete_data = InitiativeDeleteData(identifier="initiative-to-delete")
        operation = InitiativeOperation(
            operation_type="delete", initiative_data=delete_data
        )
        operations = [operation]

        response = self.builder.build_initiative_response(
            "Initiative deleted", operations, []
        )

        assert_that(response.message, equal_to("Initiative deleted"))
        assert_that(response.created_initiatives, has_length(0))
        assert_that(response.updated_initiatives, has_length(0))
        assert_that(response.deleted_initiatives, has_length(1))

        deleted_initiative = response.deleted_initiatives[0]
        assert_that(deleted_initiative, instance_of(EasyDeleteInitiativeModel))
        assert_that(deleted_initiative.identifier, equal_to("initiative-to-delete"))

    def test_build_initiative_response_multiple_operations(self):
        """Test building initiative response with multiple operations."""
        create_data = InitiativeCreateData(
            title="Initiative 1",
            description="Description 1",
            temporary_identifier="TEMP-INIT-abc123",
        )
        update_data = InitiativeUpdateData(
            identifier="initiative-2", title="Initiative 2", description="Description 2"
        )
        delete_data = InitiativeDeleteData(identifier="initiative-3")

        operations = [
            InitiativeOperation(operation_type="create", initiative_data=create_data),
            InitiativeOperation(operation_type="update", initiative_data=update_data),
            InitiativeOperation(operation_type="delete", initiative_data=delete_data),
        ]

        response = self.builder.build_initiative_response(
            "Multiple operations", operations, []
        )

        assert_that(response.created_initiatives, has_length(1))
        assert_that(response.updated_initiatives, has_length(1))
        assert_that(response.deleted_initiatives, has_length(1))

    def test_build_initiative_response_with_balance_warning(self):
        """Test building initiative response with balance warning."""
        operations = []
        balance_warning = BalanceWarning(message="Low balance")

        response = self.builder.build_initiative_response(
            "Test message", operations, [], balance_warning
        )

        assert_that(response.balance_warning, equal_to(balance_warning))

    @patch("src.ai.langchain.response_builder.logger")
    def test_build_initiative_response_exception_handling(self, mock_logger):
        """Test that exceptions during initiative model creation are handled gracefully."""
        # Create a malformed operation that will cause an exception
        operation = MagicMock()
        operation.operation_type = "create"
        operation.initiative_data = MagicMock()
        operation.initiative_data.title = None  # This should cause validation error

        operations = [operation]

        response = self.builder.build_initiative_response(
            "Test message", operations, []
        )

        # Response should still be created but with empty lists
        assert_that(response.created_initiatives, has_length(0))
        assert_that(response.updated_initiatives, has_length(0))
        assert_that(response.deleted_initiatives, has_length(0))

        # Logger should have been called for the exception
        mock_logger.exception.assert_called()

    def test_build_initiative_response_duplicate_temp_ids(self):
        """Test that duplicate create operations with same temp_id are deduplicated."""
        # Simulate agent making multiple create calls with same temp_id (self-correction)
        # First call: 0 tasks
        create_data_1 = InitiativeCreateData(
            title="Web Calculator",
            description="First attempt",
            temporary_identifier="TEMP-INIT-1",
            tasks=[],
        )
        operation_1 = InitiativeOperation(
            operation_type="create", initiative_data=create_data_1
        )

        # Second call: 1 task (agent self-correcting)
        create_data_2 = InitiativeCreateData(
            title="Web Calculator",
            description="Corrected attempt",
            temporary_identifier="TEMP-INIT-1",
            tasks=[],
        )
        operation_2 = InitiativeOperation(
            operation_type="create", initiative_data=create_data_2
        )

        # Task operation for the second initiative
        task_data = TaskCreateData(
            initiative_identifier="TEMP-INIT-1",
            title="Build UI",
            description="Build the calculator UI",
        )
        task_operation = TaskOperation(operation_type="create", task_data=task_data)

        operations = [operation_1, operation_2]
        task_operations = [task_operation]

        response = self.builder.build_initiative_response(
            "Initiative created", operations, task_operations
        )

        # Should only have 1 initiative (the last one)
        assert_that(response.created_initiatives, has_length(1))
        assert_that(response.updated_initiatives, has_length(0))
        assert_that(response.deleted_initiatives, has_length(0))

        # Verify it's the LAST operation (with tasks)
        created_initiative = response.created_initiatives[0]
        assert_that(created_initiative.title, equal_to("Web Calculator"))
        assert_that(created_initiative.description, equal_to("Corrected attempt"))
        assert_that(created_initiative.tasks, has_length(1))
        assert_that(created_initiative.tasks[0].title, equal_to("Build UI"))


class TestInitiativeTaskIntegration:
    """Test initiative response building with associated task operations."""

    def setup_method(self):
        """Clean setup for each test."""
        self.builder = ResponseBuilder()

    def test_build_initiative_response_with_create_tasks(self):
        """Test building initiative response with associated task create operations."""
        # Setup initiative update operation
        initiative_data = InitiativeUpdateData(
            identifier="I-001",
            title="Updated Initiative",
            description="Updated description",
        )
        initiative_operation = InitiativeOperation(
            operation_type="update", initiative_data=initiative_data
        )
        initiative_operations = [initiative_operation]

        # Setup task create operations for this initiative
        task_data_1 = TaskCreateData(
            initiative_identifier="I-001",
            title="Task 1",
            description="Task 1 description",
        )
        task_data_2 = TaskCreateData(
            initiative_identifier="I-001",
            title="Task 2",
            description="Task 2 description",
        )
        task_operations = [
            TaskOperation(operation_type="create", task_data=task_data_1),
            TaskOperation(operation_type="create", task_data=task_data_2),
        ]

        # Build response with both initiative and task operations
        response = self.builder.build_initiative_response(
            "Initiative updated with tasks", initiative_operations, task_operations
        )

        # Verify response structure
        assert_that(response.message, equal_to("Initiative updated with tasks"))
        assert_that(response.created_initiatives, has_length(0))
        assert_that(response.updated_initiatives, has_length(1))
        assert_that(response.deleted_initiatives, has_length(0))

        # Verify initiative has associated tasks
        updated_initiative = response.updated_initiatives[0]
        assert_that(updated_initiative.identifier, equal_to("I-001"))
        assert_that(updated_initiative.task, has_length(2))

        # Verify task details
        tasks = updated_initiative.task
        assert_that(tasks[0], instance_of(EasyCreateTaskModel))
        assert_that(tasks[0].title, equal_to("Task 1"))
        assert_that(tasks[0].description, equal_to("Task 1 description"))
        assert_that(tasks[1].title, equal_to("Task 2"))
        assert_that(tasks[1].description, equal_to("Task 2 description"))

    def test_build_initiative_response_tasks_for_different_initiatives(self):
        """Test task operations are correctly matched to their respective initiatives."""
        # Setup multiple initiative operations
        initiative_data_1 = InitiativeUpdateData(
            identifier="I-001", title="Initiative 1", description="Description 1"
        )
        initiative_data_2 = InitiativeUpdateData(
            identifier="I-002", title="Initiative 2", description="Description 2"
        )
        initiative_operations = [
            InitiativeOperation(
                operation_type="update", initiative_data=initiative_data_1
            ),
            InitiativeOperation(
                operation_type="update", initiative_data=initiative_data_2
            ),
        ]

        # Setup task operations for different initiatives
        task_data_1 = TaskCreateData(
            initiative_identifier="I-001",
            title="Task for I-001",
            description="Task description",
        )
        task_data_2 = TaskCreateData(
            initiative_identifier="I-002",
            title="Task for I-002",
            description="Task description",
        )
        task_operations = [
            TaskOperation(operation_type="create", task_data=task_data_1),
            TaskOperation(operation_type="create", task_data=task_data_2),
        ]

        response = self.builder.build_initiative_response(
            "Multiple initiatives updated", initiative_operations, task_operations
        )

        # Verify both initiatives are updated
        assert_that(response.updated_initiatives, has_length(2))

        # Find initiatives by identifier and verify tasks
        initiatives_by_id = {
            init.identifier: init for init in response.updated_initiatives
        }

        assert_that(initiatives_by_id["I-001"].task, has_length(1))
        assert_that(
            initiatives_by_id["I-001"].task[0].title, equal_to("Task for I-001")
        )

        assert_that(initiatives_by_id["I-002"].task, has_length(1))
        assert_that(
            initiatives_by_id["I-002"].task[0].title, equal_to("Task for I-002")
        )

    def test_build_initiative_response_tasks_without_matching_initiatives(self):
        """Test task operations without matching initiative identifiers are ignored."""
        # Setup initiative operation
        initiative_data = InitiativeUpdateData(
            identifier="I-001", title="Initiative", description="Description"
        )
        initiative_operation = InitiativeOperation(
            operation_type="update", initiative_data=initiative_data
        )
        initiative_operations = [initiative_operation]

        # Setup task operation for non-existent initiative
        task_data = TaskCreateData(
            initiative_identifier="I-999",  # This doesn't match any initiative
            title="Orphaned Task",
            description="Task description",
        )
        task_operations = [TaskOperation(operation_type="create", task_data=task_data)]

        response = self.builder.build_initiative_response(
            "Initiative without orphaned tasks", initiative_operations, task_operations
        )

        # With our new implementation, orphaned tasks are captured in separate initiative models
        assert_that(response.updated_initiatives, has_length(2))

        # Find initiatives by identifier
        initiatives_by_id = {
            init.identifier: init for init in response.updated_initiatives
        }

        # Verify original initiative has no tasks
        original_initiative = initiatives_by_id["I-001"]
        assert_that(original_initiative.task, has_length(0))

        # Verify orphaned task was captured
        orphaned_initiative = initiatives_by_id["I-999"]
        assert_that(orphaned_initiative.title, equal_to(None))
        assert_that(orphaned_initiative.description, equal_to(None))
        assert_that(orphaned_initiative.task, has_length(1))

    def test_build_initiative_response_empty_task_operations(self):
        """Test initiative response building with empty task operations list."""
        initiative_data = InitiativeUpdateData(
            identifier="I-001", title="Initiative", description="Description"
        )
        initiative_operation = InitiativeOperation(
            operation_type="update", initiative_data=initiative_data
        )
        initiative_operations = [initiative_operation]

        # Empty task operations
        task_operations = []

        response = self.builder.build_initiative_response(
            "Initiative without tasks", initiative_operations, task_operations
        )

        # Verify initiative has no tasks
        assert_that(response.updated_initiatives, has_length(1))
        updated_initiative = response.updated_initiatives[0]
        assert_that(updated_initiative.task, has_length(0))

    def test_build_initiative_response_create_initiative_with_temp_id_matching(self):
        """Test that create operations can match tasks via temporary identifiers."""
        # Setup initiative create operation
        temp_id = "TEMP-INIT-xyz789"
        initiative_data = InitiativeCreateData(
            title="New Initiative",
            description="New description",
            temporary_identifier=temp_id,
        )
        initiative_operation = InitiativeOperation(
            operation_type="create", initiative_data=initiative_data
        )
        initiative_operations = [initiative_operation]

        # Setup task operation that matches the temp ID
        task_data = TaskCreateData(
            initiative_identifier=temp_id,  # Matches the temp ID
            title="Task",
            description="Task description",
        )
        task_operations = [TaskOperation(operation_type="create", task_data=task_data)]

        response = self.builder.build_initiative_response(
            "New initiative created with tasks", initiative_operations, task_operations
        )

        # Verify created initiative includes the matching tasks
        assert_that(response.created_initiatives, has_length(1))
        created_initiative = response.created_initiatives[0]
        assert_that(created_initiative.title, equal_to("New Initiative"))
        assert_that(created_initiative.description, equal_to("New description"))
        assert_that(created_initiative.tasks, has_length(1))  # Task should be included

        # No orphaned tasks should be created
        assert_that(response.updated_initiatives, has_length(0))

    def test_build_initiative_response_with_update_delete_tasks(self):
        """Test building initiative response with update and delete task operations."""
        # Setup initiative update operation
        initiative_data = InitiativeUpdateData(
            identifier="I-001",
            title="Updated Initiative",
            description="Updated description",
        )
        initiative_operation = InitiativeOperation(
            operation_type="update", initiative_data=initiative_data
        )
        initiative_operations = [initiative_operation]

        # Setup task operations: create, update, delete for this initiative
        task_create_data = TaskCreateData(
            initiative_identifier="I-001",
            title="New Task",
            description="New task description",
        )
        task_update_data = TaskUpdateData(
            identifier="T-123",
            initiative_identifier="I-001",
            title="Updated Task",
            description="Updated task description",
        )
        task_delete_data = TaskDeleteData(
            identifier="T-456", initiative_identifier="I-001"
        )

        task_operations = [
            TaskOperation(operation_type="create", task_data=task_create_data),
            TaskOperation(operation_type="update", task_data=task_update_data),
            TaskOperation(operation_type="delete", task_data=task_delete_data),
        ]

        # Build response with both initiative and task operations
        response = self.builder.build_initiative_response(
            "Initiative updated with mixed task operations",
            initiative_operations,
            task_operations,
        )

        # Verify response structure
        assert_that(
            response.message, equal_to("Initiative updated with mixed task operations")
        )
        assert_that(response.updated_initiatives, has_length(1))

        # Verify initiative has all associated tasks
        updated_initiative = response.updated_initiatives[0]
        assert_that(updated_initiative.identifier, equal_to("I-001"))
        assert_that(updated_initiative.task, has_length(3))

        # Verify task types and details
        tasks = updated_initiative.task
        create_task = next(t for t in tasks if isinstance(t, EasyCreateTaskModel))
        update_task = next(t for t in tasks if isinstance(t, EasyUpdateTaskModel))
        delete_task = next(t for t in tasks if isinstance(t, EasyDeleteTaskModel))

        assert_that(create_task.title, equal_to("New Task"))
        assert_that(create_task.description, equal_to("New task description"))

        assert_that(update_task.identifier, equal_to("T-123"))
        assert_that(update_task.title, equal_to("Updated Task"))
        assert_that(update_task.description, equal_to("Updated task description"))

        assert_that(delete_task.identifier, equal_to("T-456"))


class TestOrphanedTaskOperations:
    """Test handling of orphaned task operations (tasks without corresponding initiative operations)."""

    def setup_method(self):
        """Clean setup for each test."""
        self.builder = ResponseBuilder()

    def test_build_initiative_response_with_orphaned_tasks_only(self):
        """Test building initiative response with only orphaned task operations (no initiative operations)."""
        # No initiative operations - empty list
        initiative_operations = []

        # Setup task operations for non-existent initiative operations
        task_create_data = TaskCreateData(
            initiative_identifier="I-001",
            title="Orphaned Task 1",
            description="Orphaned task description",
        )
        task_update_data = TaskUpdateData(
            identifier="T-123",
            initiative_identifier="I-001",
            title="Orphaned Task 2",
            description="Orphaned task update description",
        )
        task_delete_data = TaskDeleteData(
            identifier="T-456", initiative_identifier="I-001"
        )

        task_operations = [
            TaskOperation(operation_type="create", task_data=task_create_data),
            TaskOperation(operation_type="update", task_data=task_update_data),
            TaskOperation(operation_type="delete", task_data=task_delete_data),
        ]

        # Build response with no initiative operations but with task operations
        response = self.builder.build_initiative_response(
            "Processing orphaned tasks", initiative_operations, task_operations
        )

        # Verify response structure
        assert_that(response.message, equal_to("Processing orphaned tasks"))
        assert_that(response.created_initiatives, has_length(0))
        assert_that(
            response.updated_initiatives, has_length(1)
        )  # Should create one update for orphaned tasks
        assert_that(response.deleted_initiatives, has_length(0))

        # Verify orphaned initiative has the tasks
        orphaned_initiative = response.updated_initiatives[0]
        assert_that(orphaned_initiative.identifier, equal_to("I-001"))
        assert_that(
            orphaned_initiative.title, equal_to(None)
        )  # Should be None since we're not updating title
        assert_that(
            orphaned_initiative.description, equal_to(None)
        )  # Should be None since we're not updating description
        assert_that(
            orphaned_initiative.task, has_length(3)
        )  # Should have all 3 task operations

        # Verify task types
        tasks = orphaned_initiative.task
        create_task = next(t for t in tasks if isinstance(t, EasyCreateTaskModel))
        update_task = next(t for t in tasks if isinstance(t, EasyUpdateTaskModel))
        delete_task = next(t for t in tasks if isinstance(t, EasyDeleteTaskModel))

        assert_that(create_task.title, equal_to("Orphaned Task 1"))
        assert_that(update_task.identifier, equal_to("T-123"))
        assert_that(delete_task.identifier, equal_to("T-456"))

    def test_build_initiative_response_mixed_orphaned_and_normal(self):
        """Test building initiative response with both normal operations and orphaned tasks."""
        # Setup normal initiative update operation
        initiative_data = InitiativeUpdateData(
            identifier="I-001",
            title="Normal Initiative",
            description="Normal description",
        )
        initiative_operation = InitiativeOperation(
            operation_type="update", initiative_data=initiative_data
        )
        initiative_operations = [initiative_operation]

        # Setup task operations: some for existing initiative, some orphaned
        task_for_existing = TaskCreateData(
            initiative_identifier="I-001",  # Matches existing initiative
            title="Task for existing",
            description="Task description",
        )
        task_orphaned = TaskCreateData(
            initiative_identifier="I-999",  # No corresponding initiative operation
            title="Orphaned task",
            description="Orphaned task description",
        )

        task_operations = [
            TaskOperation(operation_type="create", task_data=task_for_existing),
            TaskOperation(operation_type="create", task_data=task_orphaned),
        ]

        response = self.builder.build_initiative_response(
            "Mixed operations", initiative_operations, task_operations
        )

        # Should have 2 updated initiatives: one normal, one orphaned
        assert_that(response.updated_initiatives, has_length(2))

        # Find initiatives by identifier
        initiatives_by_id = {
            init.identifier: init for init in response.updated_initiatives
        }

        # Verify normal initiative
        normal_initiative = initiatives_by_id["I-001"]
        assert_that(normal_initiative.title, equal_to("Normal Initiative"))
        assert_that(normal_initiative.description, equal_to("Normal description"))
        assert_that(normal_initiative.task, has_length(1))
        assert_that(normal_initiative.task[0].title, equal_to("Task for existing"))

        # Verify orphaned initiative
        orphaned_initiative = initiatives_by_id["I-999"]
        assert_that(orphaned_initiative.title, equal_to(None))
        assert_that(orphaned_initiative.description, equal_to(None))
        assert_that(orphaned_initiative.task, has_length(1))
        assert_that(orphaned_initiative.task[0].title, equal_to("Orphaned task"))

    def test_build_initiative_response_multiple_orphaned_initiatives(self):
        """Test building initiative response with multiple orphaned initiatives."""
        # No initiative operations
        initiative_operations = []

        # Setup task operations for multiple different initiatives
        task_i001 = TaskCreateData(
            initiative_identifier="I-001",
            title="Task for I-001",
            description="Task description",
        )
        task_i002 = TaskCreateData(
            initiative_identifier="I-002",
            title="Task for I-002",
            description="Task description",
        )
        task_i003 = TaskUpdateData(
            identifier="T-789",
            initiative_identifier="I-003",
            title="Task for I-003",
            description="Task description",
        )

        task_operations = [
            TaskOperation(operation_type="create", task_data=task_i001),
            TaskOperation(operation_type="create", task_data=task_i002),
            TaskOperation(operation_type="update", task_data=task_i003),
        ]

        response = self.builder.build_initiative_response(
            "Multiple orphaned initiatives", initiative_operations, task_operations
        )

        # Should have 3 updated initiatives for the 3 orphaned task groups
        assert_that(response.updated_initiatives, has_length(3))

        # Verify all are orphaned (None title/description) and have correct identifiers
        initiative_ids = {init.identifier for init in response.updated_initiatives}
        assert_that(initiative_ids, equal_to({"I-001", "I-002", "I-003"}))

        for initiative in response.updated_initiatives:
            assert_that(initiative.title, equal_to(None))
            assert_that(initiative.description, equal_to(None))
            assert_that(initiative.task, has_length(1))

    def test_build_initiative_response_orphaned_tasks_with_delete_operations(self):
        """Test that delete operations are tracked to prevent orphaned tasks from being created."""
        # Setup initiative delete operation
        initiative_data = InitiativeDeleteData(identifier="I-001")
        initiative_operation = InitiativeOperation(
            operation_type="delete", initiative_data=initiative_data
        )
        initiative_operations = [initiative_operation]

        # Setup task operation for the deleted initiative (should not become orphaned)
        task_data = TaskCreateData(
            initiative_identifier="I-001",
            title="Task for deleted initiative",
            description="Task description",
        )
        task_operations = [TaskOperation(operation_type="create", task_data=task_data)]

        response = self.builder.build_initiative_response(
            "Delete with tasks", initiative_operations, task_operations
        )

        # Should have one deleted initiative and no updated initiatives (task was not orphaned)
        assert_that(response.created_initiatives, has_length(0))
        assert_that(response.updated_initiatives, has_length(0))
        assert_that(response.deleted_initiatives, has_length(1))
        assert_that(response.deleted_initiatives[0].identifier, equal_to("I-001"))


class TestResponseBuilderIntegration:
    """Test integration between ResponseBuilder and internal tools."""

    def setup_method(self):
        """Clean setup for each test."""
        self.builder = ResponseBuilder()

    def test_build_responses_independently(self):
        """Test that task and initiative responses are built independently."""
        # Setup task operations
        task_data = TaskCreateData(
            initiative_identifier="I-001", title="Task", description="Description"
        )
        task_operation = TaskOperation(operation_type="create", task_data=task_data)
        task_operations = [task_operation]

        # Setup initiative operations
        initiative_data = InitiativeCreateData(
            title="Initiative",
            description="Description",
            temporary_identifier="TEMP-INIT-def456",
        )
        initiative_operation = InitiativeOperation(
            operation_type="create", initiative_data=initiative_data
        )
        initiative_operations = [initiative_operation]

        # Build task response - should only include task operations
        task_response = self.builder.build_task_response(
            "Task message", task_operations
        )
        assert_that(task_response.created_tasks, has_length(1))

        # Build initiative response - should only include initiative operations
        initiative_response = self.builder.build_initiative_response(
            "Initiative message", initiative_operations, []
        )
        assert_that(initiative_response.created_initiatives, has_length(1))

        # Verify they don't interfere
        assert_that(task_response.message, equal_to("Task message"))
        assert_that(initiative_response.message, equal_to("Initiative message"))
