"""
Unit tests for AI models.py to_managed_X_model functions.

Tests the conversion functions that transform Easy* models to Managed* models,
ensuring proper data mapping and validation.

These tests are standalone and don't require database connections.
"""

import pytest
from hamcrest import assert_that, equal_to, has_length, instance_of

from src.ai.models import (
    DiscussResponseModel,
    EasyCreateInitiativeModel,
    EasyCreateTaskModel,
    EasyDeleteInitiativeModel,
    EasyDeleteTaskModel,
    EasyDiscussResponseModel,
    EasyInitiativeLLMResponse,
    EasyTaskLLMResponse,
    EasyUpdateInitiativeModel,
    EasyUpdateTaskModel,
)
from src.models import (
    BalanceWarning,
    ChecklistItemModel,
    CreateInitiativeModel,
    CreateTaskModel,
    DeleteInitiativeModel,
    DeleteTaskModel,
    InitiativeLLMResponse,
    TaskLLMResponse,
    UpdateInitiativeModel,
    UpdateTaskModel,
)


# Override conftest fixtures to prevent database connections
@pytest.fixture(scope="session", autouse=True)
def override_db_fixtures():
    """Override database fixtures to prevent connection attempts."""
    pass


class TestEasyDiscussResponseModel:
    """Test EasyDiscussResponseModel.to_managed_model() function."""

    def test_to_managed_model_basic(self):
        """Test basic conversion without balance warning."""
        easy_model = EasyDiscussResponseModel(message="Test message")

        result = easy_model.to_managed_model()

        assert_that(result, instance_of(DiscussResponseModel))
        assert_that(result.message, equal_to("Test message"))
        assert_that(result.balance_warning, equal_to(None))

    def test_to_managed_model_with_balance_warning(self):
        """Test conversion with balance warning included."""
        balance_warning = BalanceWarning(
            threshold_reached=True, current_balance=10.50, threshold_amount=15.00
        )
        easy_model = EasyDiscussResponseModel(
            message="Test message", balance_warning=balance_warning
        )

        result = easy_model.to_managed_model()

        assert_that(result, instance_of(DiscussResponseModel))
        assert_that(result.message, equal_to("Test message"))
        assert_that(result.balance_warning, equal_to(balance_warning))


class TestEasyCreateTaskModel:
    """Test EasyCreateTaskModel.to_managed_task_model() function."""

    def test_to_managed_task_model_basic(self):
        """Test basic task creation without checklist."""
        easy_model = EasyCreateTaskModel(
            title="Test Task", description="Test Description", checklist=None
        )

        result = easy_model.to_managed_task_model()

        assert_that(result, instance_of(CreateTaskModel))
        assert_that(result.title, equal_to("Test Task"))
        assert_that(result.description, equal_to("Test Description"))
        assert_that(result.checklist, has_length(0))

    def test_to_managed_task_model_with_checklist(self):
        """Test task creation with checklist items."""
        checklist_items = ["Item 1", "Item 2", "Item 3"]
        easy_model = EasyCreateTaskModel(
            title="Test Task", description="Test Description", checklist=checklist_items
        )

        result = easy_model.to_managed_task_model()

        assert_that(result, instance_of(CreateTaskModel))
        assert_that(result.title, equal_to("Test Task"))
        assert_that(result.description, equal_to("Test Description"))
        assert_that(result.checklist, has_length(3))

        for i, item in enumerate(result.checklist):
            assert_that(item, instance_of(ChecklistItemModel))
            assert_that(item.title, equal_to(checklist_items[i]))

    def test_to_managed_task_model_empty_checklist(self):
        """Test task creation with empty checklist."""
        easy_model = EasyCreateTaskModel(
            title="Test Task", description="Test Description", checklist=[]
        )

        result = easy_model.to_managed_task_model()

        assert_that(result, instance_of(CreateTaskModel))
        assert_that(result.checklist, has_length(0))


class TestEasyDeleteTaskModel:
    """Test EasyDeleteTaskModel.to_managed_task_model() function."""

    def test_to_managed_task_model(self):
        """Test task deletion conversion."""
        easy_model = EasyDeleteTaskModel(identifier="task-123")

        result = easy_model.to_managed_task_model()

        assert_that(result, instance_of(DeleteTaskModel))
        assert_that(result.identifier, equal_to("task-123"))


class TestEasyUpdateTaskModel:
    """Test EasyUpdateTaskModel.to_managed_task_model() function."""

    def test_to_managed_task_model_full_update(self):
        """Test task update with all fields."""
        checklist_items = ["Updated Item 1", "Updated Item 2"]
        easy_model = EasyUpdateTaskModel(
            identifier="task-123",
            title="Updated Task",
            description="Updated Description",
            checklist=checklist_items,
        )

        result = easy_model.to_managed_task_model()

        assert_that(result, instance_of(UpdateTaskModel))
        assert_that(result.identifier, equal_to("task-123"))
        assert_that(result.title, equal_to("Updated Task"))
        assert_that(result.description, equal_to("Updated Description"))
        assert_that(result.checklist, has_length(2))

        for i, item in enumerate(result.checklist):
            assert_that(item, instance_of(ChecklistItemModel))
            assert_that(item.title, equal_to(checklist_items[i]))

    def test_to_managed_task_model_partial_update(self):
        """Test task update with only some fields."""
        easy_model = EasyUpdateTaskModel(
            identifier="task-123",
            title="Updated Task",
            description=None,
            checklist=None,
        )

        result = easy_model.to_managed_task_model()

        assert_that(result, instance_of(UpdateTaskModel))
        assert_that(result.identifier, equal_to("task-123"))
        assert_that(result.title, equal_to("Updated Task"))
        assert_that(result.description, equal_to(None))
        assert_that(result.checklist, has_length(0))


class TestEasyCreateInitiativeModel:
    """Test EasyCreateInitiativeModel.to_managed_initiative_model() function."""

    def test_to_managed_initiative_model_without_tasks(self):
        """Test initiative creation without tasks."""
        easy_model = EasyCreateInitiativeModel(
            title="Test Initiative", description="Test Description", tasks=None
        )

        result = easy_model.to_managed_initiative_model()

        assert_that(result, instance_of(CreateInitiativeModel))
        assert_that(result.title, equal_to("Test Initiative"))
        assert_that(result.description, equal_to("Test Description"))
        assert_that(result.tasks, has_length(0))

    def test_to_managed_initiative_model_with_tasks(self):
        """Test initiative creation with nested tasks."""
        task1 = EasyCreateTaskModel(
            title="Task 1", description="Description 1", checklist=["Item 1"]
        )
        task2 = EasyCreateTaskModel(
            title="Task 2", description="Description 2", checklist=None
        )

        easy_model = EasyCreateInitiativeModel(
            title="Test Initiative",
            description="Test Description",
            tasks=[task1, task2],
        )

        result = easy_model.to_managed_initiative_model()

        assert_that(result, instance_of(CreateInitiativeModel))
        assert_that(result.title, equal_to("Test Initiative"))
        assert_that(result.description, equal_to("Test Description"))
        assert_that(result.tasks, has_length(2))

        assert_that(result.tasks[0], instance_of(CreateTaskModel))
        assert_that(result.tasks[0].title, equal_to("Task 1"))
        assert_that(result.tasks[0].checklist, has_length(1))

        assert_that(result.tasks[1], instance_of(CreateTaskModel))
        assert_that(result.tasks[1].title, equal_to("Task 2"))
        assert_that(result.tasks[1].checklist, has_length(0))


class TestEasyDeleteInitiativeModel:
    """Test EasyDeleteInitiativeModel.to_managed_initiative_model() function."""

    def test_to_managed_initiative_model(self):
        """Test initiative deletion conversion."""
        easy_model = EasyDeleteInitiativeModel(identifier="initiative-123")

        result = easy_model.to_managed_initiative_model()

        assert_that(result, instance_of(DeleteInitiativeModel))
        assert_that(result.identifier, equal_to("initiative-123"))


class TestEasyUpdateInitiativeModel:
    """Test EasyUpdateInitiativeModel.to_managed_initiative_model() function."""

    def test_to_managed_initiative_model_basic_update(self):
        """Test initiative update without tasks."""
        easy_model = EasyUpdateInitiativeModel(
            identifier="initiative-123",
            title="Updated Initiative",
            description="Updated Description",
            task=None,
        )

        result = easy_model.to_managed_initiative_model()

        assert_that(result, instance_of(UpdateInitiativeModel))
        assert_that(result.identifier, equal_to("initiative-123"))
        assert_that(result.title, equal_to("Updated Initiative"))
        assert_that(result.description, equal_to("Updated Description"))
        assert_that(result.tasks, has_length(0))

    def test_to_managed_initiative_model_with_no_title_or_description(self):
        """Test initiative update without title or description."""
        easy_model = EasyUpdateInitiativeModel(
            identifier="initiative-123", title=None, description=None, task=None
        )

        result = easy_model.to_managed_initiative_model()
        assert_that(result, instance_of(UpdateInitiativeModel))
        assert_that(result.identifier, equal_to("initiative-123"))
        assert_that(result.title, equal_to(None))
        assert_that(result.description, equal_to(None))
        assert_that(result.tasks, has_length(0))

    def test_to_managed_initiative_model_with_mixed_task_operations(self):
        """Test initiative update with mixed task operations."""
        create_task = EasyCreateTaskModel(
            title="New Task", description="New Description", checklist=["New Item"]
        )
        update_task = EasyUpdateTaskModel(
            identifier="task-456",
            title="Updated Task",
            description="Updated Description",
            checklist=None,
        )
        delete_task = EasyDeleteTaskModel(identifier="task-789")

        easy_model = EasyUpdateInitiativeModel(
            identifier="initiative-123",
            title="Updated Initiative",
            description="Updated Description",
            task=[create_task, update_task, delete_task],
        )

        result = easy_model.to_managed_initiative_model()

        assert_that(result, instance_of(UpdateInitiativeModel))
        assert_that(result.identifier, equal_to("initiative-123"))
        assert_that(result.title, equal_to("Updated Initiative"))
        assert_that(result.description, equal_to("Updated Description"))
        assert_that(result.tasks, has_length(3))

        assert_that(result.tasks[0], instance_of(CreateTaskModel))
        assert_that(result.tasks[0].title, equal_to("New Task"))

        assert_that(result.tasks[1], instance_of(UpdateTaskModel))
        assert_that(result.tasks[1].identifier, equal_to("task-456"))

        assert_that(result.tasks[2], instance_of(DeleteTaskModel))
        assert_that(result.tasks[2].identifier, equal_to("task-789"))


class TestEasyInitiativeLLMResponse:
    """Test EasyInitiativeLLMResponse.to_managed_model() function."""

    def test_to_managed_model_empty_operations(self):
        """Test conversion with no operations."""
        easy_model = EasyInitiativeLLMResponse(
            message="No changes needed",
            created_initiatives=[],
            deleted_initiatives=[],
            updated_initiatives=[],
            balance_warning=None,
        )

        result = easy_model.to_managed_model()

        assert_that(result, instance_of(InitiativeLLMResponse))
        assert_that(result.message, equal_to("No changes needed"))
        assert_that(result.managed_initiatives, has_length(0))
        assert_that(result.balance_warning, equal_to(None))

    def test_to_managed_model_with_all_operations(self):
        """Test conversion with all types of operations."""
        create_initiative = EasyCreateInitiativeModel(
            title="New Initiative", description="New Description", tasks=None
        )
        update_initiative = EasyUpdateInitiativeModel(
            identifier="initiative-123",
            title="Updated Initiative",
            description="Updated Description",
            task=None,
        )
        delete_initiative = EasyDeleteInitiativeModel(identifier="initiative-456")

        balance_warning = BalanceWarning(
            threshold_reached=True, current_balance=5.00, threshold_amount=10.00
        )

        easy_model = EasyInitiativeLLMResponse(
            message="Multiple operations performed",
            created_initiatives=[create_initiative],
            deleted_initiatives=[delete_initiative],
            updated_initiatives=[update_initiative],
            balance_warning=balance_warning,
        )

        result = easy_model.to_managed_model()

        assert_that(result, instance_of(InitiativeLLMResponse))
        assert_that(result.message, equal_to("Multiple operations performed"))
        assert_that(result.managed_initiatives, has_length(3))
        assert_that(result.balance_warning, equal_to(balance_warning))

        assert_that(result.managed_initiatives[0], instance_of(CreateInitiativeModel))
        assert_that(result.managed_initiatives[1], instance_of(DeleteInitiativeModel))
        assert_that(result.managed_initiatives[2], instance_of(UpdateInitiativeModel))


class TestEasyTaskLLMResponse:
    """Test EasyTaskLLMResponse.to_managed_model() function."""

    def test_to_managed_model_empty_operations(self):
        """Test conversion with no operations."""
        easy_model = EasyTaskLLMResponse(
            message="No changes needed",
            created_tasks=[],
            deleted_tasks=[],
            updated_tasks=[],
            balance_warning=None,
        )

        result = easy_model.to_managed_model()

        assert_that(result, instance_of(TaskLLMResponse))
        assert_that(result.message, equal_to("No changes needed"))
        assert_that(result.managed_tasks, has_length(0))
        assert_that(result.balance_warning, equal_to(None))

    def test_to_managed_model_with_all_operations(self):
        """Test conversion with all types of operations."""
        create_task = EasyCreateTaskModel(
            title="New Task",
            description="New Description",
            checklist=["Item 1", "Item 2"],
        )
        update_task = EasyUpdateTaskModel(
            identifier="task-123",
            title="Updated Task",
            description="Updated Description",
            checklist=None,
        )
        delete_task = EasyDeleteTaskModel(identifier="task-456")

        balance_warning = BalanceWarning(
            threshold_reached=False, current_balance=25.00, threshold_amount=10.00
        )

        easy_model = EasyTaskLLMResponse(
            message="Multiple task operations performed",
            created_tasks=[create_task],
            deleted_tasks=[delete_task],
            updated_tasks=[update_task],
            balance_warning=balance_warning,
        )

        result = easy_model.to_managed_model()

        assert_that(result, instance_of(TaskLLMResponse))
        assert_that(result.message, equal_to("Multiple task operations performed"))
        assert_that(result.managed_tasks, has_length(3))
        assert_that(result.balance_warning, equal_to(balance_warning))

        assert_that(result.managed_tasks[0], instance_of(CreateTaskModel))
        assert_that(result.managed_tasks[0].title, equal_to("New Task"))
        assert_that(result.managed_tasks[0].checklist, has_length(2))

        assert_that(result.managed_tasks[1], instance_of(DeleteTaskModel))
        assert_that(result.managed_tasks[1].identifier, equal_to("task-456"))

        assert_that(result.managed_tasks[2], instance_of(UpdateTaskModel))
        assert_that(result.managed_tasks[2].identifier, equal_to("task-123"))
