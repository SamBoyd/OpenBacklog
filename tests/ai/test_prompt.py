import os
import uuid
from datetime import datetime
from typing import List
from unittest.mock import MagicMock, call, patch

import jinja2
import pytest
from hamcrest import (
    assert_that,
    contains_string,
    equal_to,
    has_length,
    instance_of,
    is_,
    none,
    not_,
)
from pydantic import ValidationError

from src.ai.models import ChatMessageInput
from src.ai.prompt import (
    InitiativeLLMResponse,
    InitiativePrompt,
    TaskLLMResponse,
    TaskPrompt,
    get_template_path_for_entity,
)
from src.models import (
    ChatMode,
    ChecklistItemModel,
    CreateInitiativeModel,
    CreateTaskModel,
    Initiative,
    InitiativeType,
    ManagedEntityAction,
    PydanticInitiative,
    PydanticTask,
    Task,
    TaskStatus,
    TaskType,
    UpdateInitiativeModel,
    UpdateTaskModel,
)


@pytest.fixture
def sample_sqlalchemy_task() -> Task:
    """Create a sample SQLAlchemy Task for testing (e.g., Initiative context).
    NOTE: Checklist is intentionally omitted here to avoid fixture complexity.
    PydanticTask fixture will define its own checklist.
    """
    task = Task(
        id=uuid.uuid4(),
        identifier="TASK-1",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        title="Sample Task",
        description="This is a sample task for testing",
        status=TaskStatus.TO_DO,
        type=TaskType.CODING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        initiative_id=None,
        initiative=None,
        checklist=[],  # Initialize with empty list
    )
    return task


@pytest.fixture
def sample_pydantic_task(sample_sqlalchemy_task: Task) -> PydanticTask:
    """Create a PydanticTask model instance using model_validate."""
    # Ensure PydanticTask.Config.from_attributes = True is set
    return PydanticTask.model_validate(sample_sqlalchemy_task)


@pytest.fixture
def sample_sqlalchemy_initiative(sample_sqlalchemy_task: Task) -> Initiative:
    """Create a sample SQLAlchemy Initiative, linking the SQLAlchemy task."""
    initiative = Initiative(
        id=uuid.uuid4(),
        identifier="INIT-1",
        user_id=sample_sqlalchemy_task.user_id,
        workspace_id=sample_sqlalchemy_task.workspace_id,
        title="Sample Initiative",
        description="This is a sample initiative for testing",
        status=TaskStatus.IN_PROGRESS,
        type=InitiativeType.FEATURE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        tasks=[sample_sqlalchemy_task],
    )
    sample_sqlalchemy_task.initiative_id = initiative.id
    return initiative


@pytest.fixture
def sample_pydantic_initiative(
    sample_sqlalchemy_initiative: Initiative,
) -> PydanticInitiative:
    """Create a PydanticInitiative model instance using model_validate."""
    # Ensure PydanticInitiative.Config.from_attributes = True is set
    # Note: This will automatically convert nested tasks if configured correctly
    return PydanticInitiative.model_validate(sample_sqlalchemy_initiative)


# Fixture for sample ChatMessageInput list (without suggested changes)
sample_messages: List[ChatMessageInput] = [
    # Use ChatMessageInput constructor
    ChatMessageInput(role="user", content="This is the user message")
]


# Fixture for a sample ManagedTaskModel (UpdateTaskModel variant)
@pytest.fixture
def sample_suggested_task() -> UpdateTaskModel:
    return UpdateTaskModel(
        action=ManagedEntityAction.UPDATE,
        identifier="TASK-SUGGEST",
        title="Suggested Update Title",
        description="This is a suggested update.",
        checklist=None,
    )


# Fixture for a sample ManagedInitiativeModel (UpdateInitiativeModel variant)
@pytest.fixture
def sample_suggested_initiative() -> UpdateInitiativeModel:
    return UpdateInitiativeModel(
        action=ManagedEntityAction.UPDATE,
        identifier="INIT-SUGGEST",
        title="Suggested Initiative Update Title",
        description="This is a suggested initiative update.",
        tasks=[],
    )


# Fixture for sample ChatMessageInput list (using suggested task)
@pytest.fixture
def sample_chat_message_inputs(
    sample_suggested_task: UpdateTaskModel,
) -> List[ChatMessageInput]:
    return [
        ChatMessageInput(role="user", content="First user message."),
        ChatMessageInput(
            role="assistant",
            content="Here is my suggestion.",
            suggested_changes=[sample_suggested_task],  # Wrap in a list
        ),
        ChatMessageInput(role="user", content="Okay, what about this?"),
    ]


# Fixture for sample ChatMessageInput list (using suggested initiative)
@pytest.fixture
def sample_chat_message_inputs_initiative(
    sample_suggested_initiative: UpdateInitiativeModel,
) -> List[ChatMessageInput]:
    return [
        ChatMessageInput(role="user", content="First user message about initiative."),
        ChatMessageInput(
            role="assistant",
            content="Here is my initiative suggestion.",
            suggested_changes=[sample_suggested_initiative],  # Wrap in a list
        ),
        ChatMessageInput(role="user", content="Understood."),
    ]


class TestInitiativePrompt:
    """Test suite for the InitiativePrompt class."""

    def test_init(self, sample_pydantic_initiative: PydanticInitiative):
        """Test initialization of InitiativePrompt with Pydantic model."""
        prompt = InitiativePrompt(
            initiatives=[sample_pydantic_initiative],
            messages=sample_messages,
            additional_context="Some context",
        )

        assert_that(prompt.initiatives, has_length(1))
        assert_that(prompt.initiatives[0], is_(sample_pydantic_initiative))
        # Check identifier added previously
        assert_that(
            prompt.initiatives[0].identifier,
            equal_to(sample_pydantic_initiative.identifier),
        )
        assert_that(prompt.messages, equal_to(sample_messages))
        assert_that(prompt.additional_context, equal_to("Some context"))
        assert_that(prompt.response_model, equal_to(InitiativeLLMResponse))

    @patch("jinja2.Environment.get_template")  # Mock get_template
    def test_render_system_content(
        self, mock_get_template, sample_pydantic_initiative: PydanticInitiative
    ):
        """Test rendering of initiative prompt system content."""
        # Setup mock template instance
        mock_template_instance = MagicMock(
            spec=jinja2.Template
        )  # Spec helps mock object mimic original
        mock_template_instance.render.return_value = "Rendered template content"
        mock_get_template.return_value = (
            mock_template_instance  # get_template returns the mock template
        )

        # Create prompt
        prompt = InitiativePrompt(
            initiatives=[sample_pydantic_initiative],
            messages=sample_messages,
            additional_context="Some context",
        )

        # Call render
        result = prompt.render_system_content()

        # Assertions
        mock_get_template.assert_called_once_with(
            "initiative_edit.jinja"
        )  # Check get_template was called correctly
        mock_template_instance.render.assert_called_once()

        # Check context passed to render
        call_args, call_kwargs = mock_template_instance.render.call_args
        assert_that(call_kwargs["initiatives"], has_length(1))
        rendered_initiative = call_kwargs["initiatives"][0]
        # Verify some fields in the dictionary passed to template
        assert_that(
            rendered_initiative["id"], equal_to(str(sample_pydantic_initiative.id))
        )
        assert_that(
            rendered_initiative["identifier"],
            equal_to(sample_pydantic_initiative.identifier),
        )
        assert_that(
            rendered_initiative["title"], equal_to(sample_pydantic_initiative.title)
        )
        assert_that(
            rendered_initiative["tasks"],
            has_length(len(sample_pydantic_initiative.tasks)),
        )
        assert_that(
            rendered_initiative["status"],
            equal_to(
                sample_pydantic_initiative.status
                if sample_pydantic_initiative.status
                else None
            ),
        )

        assert_that(call_kwargs["additional_context"], equal_to("Some context"))

        # Check final rendered content
        assert_that(result, equal_to("Rendered template content"))

    @patch("src.ai.prompt.call_llm_api")
    async def test_process_prompt_handles_chat_message_inputs(
        self,
        mock_call_llm_api,
        sample_pydantic_initiative: PydanticInitiative,
        sample_chat_message_inputs_initiative: List[ChatMessageInput],
        sample_suggested_initiative: UpdateInitiativeModel,
    ):
        """Test InitiativePrompt process_prompt correctly formats messages including suggested_changes."""
        # Setup mock response
        mock_response = InitiativeLLMResponse(
            message="Processed initiative messages.", managed_initiatives=[]
        )
        mock_call_llm_api.return_value = mock_response

        # Create prompt with ChatMessageInput fixture for initiatives
        prompt = InitiativePrompt(
            initiatives=[sample_pydantic_initiative],
            messages=sample_chat_message_inputs_initiative,  # Use the initiative fixture
            additional_context="Testing initiative message processing",
        )

        # Call method
        await prompt.process_prompt(
            api_key="test_key_init",
            user_auth_token="test_user_auth_token",
            workspace_id="test_workspace_id",
            thread_id="test_thread_id",
            user_id="test_user_id",
        )

        # Assert call_llm_api was called
        mock_call_llm_api.assert_called_once()
        _, kwargs = mock_call_llm_api.call_args
        passed_messages = kwargs.get("messages", [])

        # Expected message structure (System + 3 from fixture)
        assert_that(passed_messages, has_length(4))

        # 1. System Message
        assert_that(passed_messages[0]["role"], equal_to("system"))

        # 2. First user message
        assert_that(passed_messages[1]["role"], equal_to("user"))
        assert_that(
            passed_messages[1]["content"],
            equal_to("First user message about initiative."),
        )

        # 3. Assistant message with suggested_changes
        assert_that(passed_messages[2]["role"], equal_to("assistant"))
        assert_that(
            passed_messages[2]["content"],
            contains_string("Here is my initiative suggestion."),
        )
        # Check suggested_changes JSON (now expects the JSON of the item within the list)
        expected_suggestion_json = sample_suggested_initiative.model_dump_json(indent=2)
        assert_that(
            passed_messages[2]["content"],
            contains_string("--- Previous Suggestion(s) ---"),  # Updated marker
        )
        assert_that(
            passed_messages[2]["content"], contains_string(expected_suggestion_json)
        )

        # 4. Second user message
        assert_that(passed_messages[3]["role"], equal_to("user"))
        assert_that(passed_messages[3]["content"], equal_to("Understood."))


class TestTaskPrompt:
    """Test suite for the TaskPrompt class."""

    # Add test for message processing
    @patch("src.ai.prompt.call_llm_api")
    async def test_process_prompt_handles_chat_message_inputs(
        self,
        mock_call_llm_api,
        sample_pydantic_task: PydanticTask,
        sample_chat_message_inputs: List[ChatMessageInput],
        sample_suggested_task: UpdateTaskModel,
    ):
        """Test that process_prompt correctly formats messages including suggested_changes."""
        # Setup mock response
        mock_response = TaskLLMResponse(message="Processed messages.", managed_tasks=[])
        mock_call_llm_api.return_value = mock_response

        # Create prompt with the ChatMessageInput fixture
        prompt = TaskPrompt(
            tasks=[sample_pydantic_task],
            initiative=None,
            messages=sample_chat_message_inputs,  # Use the fixture here
            additional_context="Testing message processing",
        )

        # Call method
        await prompt.process_prompt(
            api_key="test_key",
            user_auth_token="test_user_auth_token",
            workspace_id="test_workspace_id",
            thread_id="test_thread_id",
            user_id="test_user_id",
        )

        # Assert call_llm_api was called
        mock_call_llm_api.assert_called_once()
        _, kwargs = mock_call_llm_api.call_args
        passed_messages = kwargs.get("messages", [])

        # Expected message structure (after processing ChatMessageInput)
        # System message + 3 from sample_chat_message_inputs
        assert_that(passed_messages, has_length(4))

        # 1. System Message (check role)
        assert_that(passed_messages[0]["role"], equal_to("system"))

        # 2. First user message (index 1 corresponds to first item in sample_chat_message_inputs)
        assert_that(passed_messages[1]["role"], equal_to("user"))
        assert_that(passed_messages[1]["content"], equal_to("First user message."))

        # 3. Assistant message with suggested_changes
        assert_that(passed_messages[2]["role"], equal_to("assistant"))
        # Check that original content is present
        assert_that(
            passed_messages[2]["content"], contains_string("Here is my suggestion.")
        )
        # Check that suggested_changes JSON is appended (expects JSON of item in list)
        expected_suggestion_json = sample_suggested_task.model_dump_json(indent=2)
        assert_that(
            passed_messages[2]["content"],
            contains_string("--- Previous Suggestion(s) ---"),
        )  # Updated marker
        assert_that(
            passed_messages[2]["content"], contains_string(expected_suggestion_json)
        )

        # 4. Second user message
        assert_that(passed_messages[3]["role"], equal_to("user"))
        assert_that(passed_messages[3]["content"], equal_to("Okay, what about this?"))

    # Use pydantic task and sqlalchemy initiative fixtures
    def test_init(
        self,
        sample_pydantic_task: PydanticTask,
        sample_sqlalchemy_initiative: Initiative,
    ):
        """Test initialization of TaskPrompt."""
        prompt = TaskPrompt(
            tasks=[sample_pydantic_task],
            initiative=sample_sqlalchemy_initiative,
            messages=sample_messages,
            additional_context="Some task context",
        )

        assert_that(prompt.tasks, has_length(1))
        assert_that(prompt.tasks[0], is_(sample_pydantic_task))
        # Check identifier added previously
        assert_that(
            prompt.tasks[0].identifier, equal_to(sample_pydantic_task.identifier)
        )
        assert_that(prompt.initiative, is_(sample_sqlalchemy_initiative))
        assert_that(prompt.messages, equal_to(sample_messages))
        assert_that(prompt.additional_context, equal_to("Some task context"))
        assert_that(prompt.response_model, equal_to(TaskLLMResponse))

    @patch("jinja2.Environment.get_template")  # Mock get_template
    def test_render_system_content(
        self, mock_get_template, sample_pydantic_task: PydanticTask
    ):
        """Test rendering of task prompt system content without initiative."""
        # Setup mock template instance
        mock_template_instance = MagicMock(spec=jinja2.Template)
        mock_template_instance.render.return_value = "Rendered task template content"
        mock_get_template.return_value = mock_template_instance

        # Create prompt without initiative
        prompt = TaskPrompt(
            tasks=[sample_pydantic_task],
            initiative=None,
            messages=sample_messages,
            additional_context="Some context",
        )

        # Call render
        result = prompt.render_system_content()

        # Assertions
        mock_get_template.assert_called_once_with("task_edit.jinja")
        mock_template_instance.render.assert_called_once()

        # Check context passed to render
        call_args, call_kwargs = mock_template_instance.render.call_args
        assert_that(call_kwargs["tasks"], has_length(1))
        rendered_task = call_kwargs["tasks"][0]
        # Verify some fields
        assert_that(rendered_task["id"], equal_to(str(sample_pydantic_task.id)))
        assert_that(
            rendered_task["identifier"], equal_to(sample_pydantic_task.identifier)
        )
        assert_that(rendered_task["title"], equal_to(sample_pydantic_task.title))
        assert_that(
            rendered_task["checklist"], has_length(len(sample_pydantic_task.checklist))
        )
        assert_that(
            rendered_task["status"],
            equal_to(
                sample_pydantic_task.status if sample_pydantic_task.status else None
            ),
        )

        assert_that(call_kwargs["initiative"], is_(none()))  # No initiative context
        assert_that(call_kwargs["additional_context"], equal_to("Some context"))

        # Check final rendered content
        assert_that(result, equal_to("Rendered task template content"))

    @patch("jinja2.Environment.get_template")  # Mock get_template
    def test_render_with_initiative(
        self,
        mock_get_template,
        sample_pydantic_task: PydanticTask,
        sample_sqlalchemy_initiative: Initiative,
    ):
        """Test rendering of task prompt when initiative context is present."""
        # Setup mock template instance
        mock_template_instance = MagicMock(spec=jinja2.Template)
        mock_template_instance.render.return_value = (
            "Rendered task template with initiative"
        )
        mock_get_template.return_value = mock_template_instance

        # Create prompt
        prompt = TaskPrompt(
            tasks=[sample_pydantic_task],
            initiative=sample_sqlalchemy_initiative,
            messages=sample_messages,
            additional_context="Some context",
        )

        # Call render
        result = prompt.render_system_content()

        # Assertions
        mock_get_template.assert_called_once_with("task_edit.jinja")
        mock_template_instance.render.assert_called_once()

        # Check context passed to render
        call_args, call_kwargs = mock_template_instance.render.call_args
        assert_that(call_kwargs["tasks"], has_length(1))
        rendered_task = call_kwargs["tasks"][0]
        assert_that(rendered_task["id"], equal_to(str(sample_pydantic_task.id)))
        assert_that(rendered_task["title"], equal_to(sample_pydantic_task.title))

        # Check initiative context
        assert_that(call_kwargs["initiative"], is_(not_(none())))
        rendered_initiative = call_kwargs["initiative"]
        assert_that(
            rendered_initiative["identifier"],
            equal_to(sample_sqlalchemy_initiative.identifier),
        )
        assert_that(
            rendered_initiative["title"], equal_to(sample_sqlalchemy_initiative.title)
        )

        assert_that(call_kwargs["additional_context"], equal_to("Some context"))

        # Check final rendered content
        assert_that(result, equal_to("Rendered task template with initiative"))

    @patch("src.ai.prompt.call_llm_api")
    async def test_process_prompt_passes_validation_context(
        self, mock_call_llm_api, sample_pydantic_task: PydanticTask
    ):
        """Test that process_prompt passes the expected task IDs for validation context."""
        # Setup
        mock_response = TaskLLMResponse(message="No changes needed", managed_tasks=[])
        mock_call_llm_api.return_value = mock_response

        # Create prompt
        prompt = TaskPrompt(
            tasks=[sample_pydantic_task],
            initiative=None,
            messages=sample_messages,
        )

        # Call method
        result = await prompt.process_prompt(
            api_key="test_api_key",
            user_auth_token="test_user_auth_token",
            workspace_id="test_workspace_id",
            thread_id="test_thread_id",
            user_id="test_user_id",
        )

        # Check the context was passed correctly
        expected_context = {
            "valid_task_identifiers": {sample_pydantic_task.identifier}
        }  # Use identifier
        mock_call_llm_api.assert_called_once()
        _, kwargs = mock_call_llm_api.call_args
        assert_that(kwargs["validation_context"], is_(not_(none())))
        # Use direct set comparison instead of hamcrest.equal_to for clarity/robustness
        assert (
            kwargs["validation_context"].get("valid_task_identifiers")
            == expected_context["valid_task_identifiers"]
        )
        assert_that(result, is_(mock_response))

    @patch("src.ai.prompt.call_llm_api")
    async def test_validation_multiple_tasks(self, mock_call_llm_api):
        """Test validation context with multiple pydantic tasks."""
        # Create Pydantic tasks
        task1 = PydanticTask(id=uuid.uuid4(), identifier="TASK-100", title="First Task")
        task2 = PydanticTask(
            id=uuid.uuid4(), identifier="TASK-200", title="Second Task"
        )

        # Setup mock response
        mock_response = TaskLLMResponse(message="Updated both tasks", managed_tasks=[])
        mock_call_llm_api.return_value = mock_response

        # Create prompt with multiple tasks
        prompt = TaskPrompt(
            tasks=[task1, task2],
            initiative=None,
            messages=sample_messages,
        )

        # Call method
        await prompt.process_prompt(
            api_key="test_api_key",
            user_auth_token="test_user_auth_token",
            workspace_id="test_workspace_id",
            thread_id="test_thread_id",
            user_id="test_user_id",
        )

        # Check that both task identifiers were included in context
        _, kwargs = mock_call_llm_api.call_args
        expected_ids = {task1.identifier, task2.identifier}  # Use identifiers
        assert_that(kwargs["validation_context"], is_(not_(none())))
        actual_identifiers = kwargs["validation_context"].get("valid_task_identifiers")
        assert_that(actual_identifiers, equal_to(expected_ids))

    @patch("src.ai.prompt.call_llm_api")
    async def test_validation_fails_for_invalid_task_identifier(
        self, mock_call_llm_api, sample_pydantic_task: PydanticTask
    ):
        """
        Test that validation raises an error for UPDATE on task identifiers that don't exist.
        Simulates call_llm_api raising validation error.
        """
        # Set up the mock to raise a ValueError (as if Pydantic validation failed within call_llm_api)
        # Note: The check is now against identifier
        invalid_id_str = "TASK-999"  # Use an identifier not present
        mock_call_llm_api.side_effect = ValidationError.from_exception_data(
            title=TaskLLMResponse.__name__,
            line_errors=[
                {
                    "type": "value_error",  # Standard Pydantic error type
                    "loc": ("managed_tasks", 0, "identifier"),  # Location of the error
                    "input": invalid_id_str,  # The input value that caused the error
                    # 'msg' is automatically generated by Pydantic based on type/ctx
                    # Add 'ctx' if needed for custom error messages, but value_error is often sufficient
                    "ctx": {
                        "error": f"Proposed update for task identifier '{invalid_id_str}' not found in provided tasks."
                    },  # Optional context
                }
            ],
        )

        # Create prompt
        prompt = TaskPrompt(
            tasks=[sample_pydantic_task],  # Only has sample_pydantic_task.identifier
            initiative=None,
            messages=sample_messages,
        )

        # Verify validation error is raised by process_prompt
        # The call_llm_api function itself raises the ValidationError
        with pytest.raises(ValidationError) as excinfo:
            await prompt.process_prompt(
                api_key="test_api_key",
                user_auth_token="test_user_auth_token",
                workspace_id="test_workspace_id",
                thread_id="test_thread_id",
                user_id="test_user_id",
            )

        # Check the error message reflects the original validation error
        # Access the Pydantic errors directly
        assert len(excinfo.value.errors()) == 1
        pydantic_error = excinfo.value.errors()[0]
        assert_that(pydantic_error["loc"], equal_to(("managed_tasks", 0, "identifier")))
        assert_that(pydantic_error["input"], equal_to(invalid_id_str))
        # Check the generated message or the context if needed
        assert_that(
            pydantic_error["msg"], contains_string("Value error")
        )  # Default msg for value_error
        # Or check context if provided
        ctx = pydantic_error.get("ctx", {})  # Safely get ctx
        assert_that(
            ctx.get("error", ""),
            contains_string(f"identifier '{invalid_id_str}' not found"),
        )  # Safely get error within ctx

        # Verify call_llm_api was called with the right context
        expected_context = {
            "valid_task_identifiers": {sample_pydantic_task.identifier}
        }  # Use identifier
        _, kwargs = mock_call_llm_api.call_args
        assert_that(
            kwargs["validation_context"].get("valid_task_identifiers"),
            equal_to(expected_context["valid_task_identifiers"]),
        )

        # Check the validation error details more precisely
        errors = excinfo.value.errors()
        assert len(errors) == 1
        error_details = errors[0]
        assert error_details["type"] == "value_error"
        assert error_details["loc"] == (
            "managed_tasks",
            0,
            "identifier",
        )  # Check location matches the invalid field
        assert (
            error_details["input"] == invalid_id_str
        )  # Check input value matches the invalid one
        assert (
            "not found in provided tasks." in error_details["msg"]
        )  # Check specific error message segment

    def test_task_create_validation(self):
        """Test validation of task creation with empty fields."""
        # Valid task creation
        valid_task = CreateTaskModel(
            title="Valid Title",
            description="Valid Description",
            checklist=None,  # This field expects List[Dict], None is valid
        )
        # CreateTaskModel does not use 'action' in its definition, but it's implicitly set
        # Test data should reflect the model definition
        empty_title_task_data = {
            "action": "CREATE",
            "title": "",
            "description": "Valid Description",
            "checklist": None,
        }
        empty_desc_task_data = {
            "action": "CREATE",
            "title": "Valid Title",
            "description": "",
            "checklist": None,
        }
        null_title_task_data = {
            "action": "CREATE",
            "title": None,
            "description": "Valid Description",
            "checklist": None,
        }
        null_desc_task_data = {
            "action": "CREATE",
            "title": "Valid Title",
            "description": None,
            "checklist": None,
        }

        # Validate directly using model_validate
        valid_response_data = {
            "message": "Valid creation",
            "managed_tasks": [valid_task.model_dump()],
        }
        TaskLLMResponse.model_validate(valid_response_data)  # Should pass

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_tasks": [empty_title_task_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {"message": "Invalid creation", "managed_tasks": [empty_desc_task_data]}
            )
        assert_that(str(excinfo.value), contains_string("description"))

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {"message": "Invalid creation", "managed_tasks": [null_title_task_data]}
            )
        assert_that(str(excinfo.value), contains_string("title"))

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {"message": "Invalid creation", "managed_tasks": [null_desc_task_data]}
            )
        assert_that(str(excinfo.value), contains_string("description"))

    def test_task_update_validation(self):
        """Test validation of task updates with empty fields."""
        valid_update = UpdateTaskModel(
            identifier="TASK-123",
            title="New Valid Title",
            description="New Valid Description",
            checklist=[ChecklistItemModel(title="item")],  # Correct checklist
        )
        # UpdateTaskModel uses action field
        empty_title_update_data = {
            "action": "UPDATE",
            "identifier": "TASK-123",
            "title": "",
            "description": "Valid Description",
            "checklist": [],
        }
        empty_desc_update_data = {
            "action": "UPDATE",
            "identifier": "TASK-123",
            "title": "Valid Title",
            "description": "",
            "checklist": [],
        }

        # Validate directly using model_validate (context is needed for UPDATE identifier check)
        context = {"valid_task_ids": {"TASK-123"}}
        valid_response_data = {
            "message": "Valid update",
            "managed_tasks": [valid_update.model_dump()],
        }
        TaskLLMResponse.model_validate(
            valid_response_data, context=context
        )  # Should pass

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_tasks": [empty_title_update_data],
                },
                context=context,
            )
        assert_that(str(excinfo.value), contains_string("title"))

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_tasks": [empty_desc_update_data],
                },
                context=context,
            )
        assert_that(str(excinfo.value), contains_string("description"))

    def test_initiative_create_validation(self):
        """Test validation of initiative creation with empty fields."""
        valid_initiative = CreateInitiativeModel(
            title="Valid Title",
            description="Valid Description",
            tasks=[],
        )
        # Test data should reflect the model definition
        empty_title_initiative_data = {
            "action": "CREATE",
            "title": "",
            "description": "Valid Description",
            "tasks": [],
        }
        empty_desc_initiative_data = {
            "action": "CREATE",
            "title": "Valid Title",
            "description": "",
            "tasks": [],
        }
        empty_task_initiative_data = {
            "action": "CREATE",
            "title": "",
            "description": "Valid Description",
            # Task data within initiative create should be raw dicts for validation
            "tasks": [
                {
                    "action": "CREATE",
                    "title": "",
                    "description": "Valid Task Desc",
                    "checklist": None,
                }
            ],  # Invalid task
        }

        # Validate directly using model_validate
        valid_response_data = {
            "message": "Valid creation",
            "managed_initiatives": [valid_initiative.model_dump()],
        }
        InitiativeLLMResponse.model_validate(valid_response_data)  # Should pass

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_initiatives": [empty_title_initiative_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Initiative title

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_initiatives": [empty_desc_initiative_data],
                }
            )
        assert_that(
            str(excinfo.value), contains_string("description")
        )  # Initiative description

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_initiatives": [empty_task_initiative_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Checks task title

    def test_initiative_update_validation_allows_none_values(self):
        """Test validation of initiative updates with empty fields."""
        valid_update = UpdateInitiativeModel(
            identifier="INIT-1",
            title="New Valid Title",
            description="New Valid Description",
            tasks=[
                UpdateTaskModel(
                    identifier="TASK-1",
                    title="T",
                    description="D",
                    checklist=[ChecklistItemModel(title="i")],
                )
            ],
        )
        # Test data reflects model structure
        null_desc_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": "Valid Title",
            "description": None,
            "tasks": [
                {
                    "action": "UPDATE",
                    "identifier": "TASK-1",
                    "title": "Some title",
                    "description": "Valid Desc",
                    "checklist": [],
                }
            ],  # Invalid task title
        }
        null_title_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": None,
            "description": "Valid Description",
            "tasks": None,
        }

        # Validate directly using model_validate
        # Context might be needed if task updates require identifier validation within InitiativeLLMResponse
        # For now, assuming initiative update focuses on its own fields + nested task validation
        valid_response_data = {
            "message": "Valid update",
            "managed_initiatives": [valid_update.model_dump()],
        }
        InitiativeLLMResponse.model_validate(valid_response_data)  # Should pass

        InitiativeLLMResponse.model_validate(
            {
                "message": "Invalid update",
                "managed_initiatives": [null_desc_update_data],
            }
        )
        InitiativeLLMResponse.model_validate(
            {
                "message": "Invalid update",
                "managed_initiatives": [null_title_update_data],
            }
        )

    def test_initiative_update_validation(self):
        """Test validation of initiative updates with empty fields."""
        valid_update = UpdateInitiativeModel(
            identifier="INIT-1",
            title="New Valid Title",
            description="New Valid Description",
            tasks=[
                UpdateTaskModel(
                    identifier="TASK-1",
                    title="T",
                    description="D",
                    checklist=[ChecklistItemModel(title="i")],
                )
            ],
        )
        # Test data reflects model structure
        empty_title_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": "",
            "description": "Valid Description",
            "tasks": [],
        }
        empty_desc_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": "Valid Title",
            "description": "",
            "tasks": [],
        }
        empty_task_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": "",
            "description": "Valid Description",
            # Task data within initiative update should be raw dicts for validation
            "tasks": [
                {
                    "action": "UPDATE",
                    "identifier": "TASK-1",
                    "title": "",
                    "description": "Valid Desc",
                    "checklist": [],
                }
            ],  # Invalid task title
        }

        # Validate directly using model_validate
        # Context might be needed if task updates require identifier validation within InitiativeLLMResponse
        # For now, assuming initiative update focuses on its own fields + nested task validation
        valid_response_data = {
            "message": "Valid update",
            "managed_initiatives": [valid_update.model_dump()],
        }
        InitiativeLLMResponse.model_validate(valid_response_data)  # Should pass

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_initiatives": [empty_title_update_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Initiative title

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_initiatives": [empty_desc_update_data],
                }
            )
        assert_that(
            str(excinfo.value), contains_string("description")
        )  # Initiative description

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_initiatives": [empty_task_update_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Checks task title


class TestGetTemplatePath:
    """Test suite for the get_template_path function."""

    @patch("os.path.join")
    @patch("os.path.dirname")
    def test_get_template_path(self, mock_dirname, mock_join):
        """Test get_template_path returns correct path."""
        # Setup mocks
        mock_dirname.return_value = "/path/to/ai"
        mock_join.side_effect = lambda *args: "/".join(args)

        # Call function
        with pytest.raises(FileNotFoundError):
            result = get_template_path_for_entity("initiative", ChatMode.EDIT)

        # Assertions
        mock_dirname.assert_called_once()

        # Check all the expected path components were used
        expected_calls = [
            call("/path/to/ai", "..", "..", "templates", "prompts", "initiative"),
            call(
                "/path/to/ai/../../templates/prompts/initiative",
                f"initiative_edit.jinja",
            ),
        ]
        assert_that(mock_join.call_args_list, equal_to(expected_calls))

    def test_get_template_path_invalid_entity(self):
        """Test get_template_path raises ValueError for invalid entity type."""
        with pytest.raises(ValueError) as excinfo:
            get_template_path_for_entity("invalid_entity", ChatMode.EDIT)

        assert_that(
            str(excinfo.value),
            equal_to(
                "Entity type must be 'initiative' or 'task', got 'invalid_entity'"
            ),
        )


class TestLLMResponseModels:
    """Test suite for LLM response models (output validation)."""

    def test_task_llm_response(self):
        """Test initialization of TaskLLMResponse with correct checklist model."""
        managed_task = UpdateTaskModel(
            identifier="TASK-123",
            title="New Task Title",
            description="New task description",
            checklist=[
                ChecklistItemModel(title="Step 1"),  # Use ChecklistItemModel
                ChecklistItemModel(title="Step 2"),  # Use ChecklistItemModel
            ],
        )

        response = TaskLLMResponse(
            message="Updated task description", managed_tasks=[managed_task]
        )
        assert_that(response.message, equal_to("Updated task description"))
        assert_that(response.managed_tasks, has_length(1))
        managed_task_result = response.managed_tasks[0]
        assert_that(managed_task_result, instance_of(UpdateTaskModel))
        # Use isinstance for type narrowing for MyPy/Pylance
        assert isinstance(managed_task_result, UpdateTaskModel)
        assert_that(managed_task_result.action, equal_to(ManagedEntityAction.UPDATE))
        assert_that(managed_task_result.identifier, equal_to("TASK-123"))
        assert_that(managed_task_result.title, equal_to("New Task Title"))
        # Verify checklist items are correct type
        assert managed_task_result.checklist is not None
        assert_that(managed_task_result.checklist, has_length(2))
        assert_that(managed_task_result.checklist[0], instance_of(ChecklistItemModel))
        assert_that(managed_task_result.checklist[0].title, equal_to("Step 1"))

    def test_initiative_llm_response(self):
        """Test initialization of InitiativeLLMResponse with correct checklist model."""
        managed_task = UpdateTaskModel(
            identifier="TASK-123",
            title="New Task Title",
            description="New task description",
            checklist=[
                ChecklistItemModel(title="Step 1"),  # Use ChecklistItemModel
                ChecklistItemModel(title="Step 2"),  # Use ChecklistItemModel
            ],
        )
        managed_initiative = UpdateInitiativeModel(
            action=ManagedEntityAction.UPDATE,
            identifier="INIT-1",
            title="New Initiative Title",
            description="New initiative description",
            tasks=[managed_task],
        )

        response = InitiativeLLMResponse(
            message="Updated initiative structure",
            managed_initiatives=[managed_initiative],
        )
        assert_that(response.message, equal_to("Updated initiative structure"))
        assert_that(response.managed_initiatives, has_length(1))
        managed_initiative_result = response.managed_initiatives[0]
        # Use isinstance for type narrowing
        assert isinstance(managed_initiative_result, UpdateInitiativeModel)
        assert_that(
            managed_initiative_result.action, equal_to(ManagedEntityAction.UPDATE)
        )
        assert_that(managed_initiative_result.identifier, equal_to("INIT-1"))
        assert_that(managed_initiative_result.title, equal_to("New Initiative Title"))
        assert managed_initiative_result.tasks is not None
        assert_that(managed_initiative_result.tasks, has_length(1))

        managed_task_result = managed_initiative_result.tasks[0]
        assert isinstance(managed_task_result, UpdateTaskModel)
        assert_that(managed_task_result.action, equal_to(ManagedEntityAction.UPDATE))
        assert_that(managed_task_result.identifier, equal_to("TASK-123"))
        # Verify checklist
        assert managed_task_result.checklist is not None
        assert_that(managed_task_result.checklist, has_length(2))
        assert_that(managed_task_result.checklist[0].title, equal_to("Step 1"))

    def test_task_llm_response_validation(self):
        """Test TaskLLMResponse validation rejects updates to unknown task identifiers."""
        # Test the validation logic using the context mechanism
        # This requires calling the validator directly or via model_validate
        # Prepare context like process_prompt would
        context = {
            "valid_task_identifiers": {"TASK-123"}
        }  # Identifiers used for validation

        # Validation should pass for valid identifier
        TaskLLMResponse.model_validate(
            {
                "message": "Valid",
                "managed_tasks": [
                    {
                        "action": "UPDATE",
                        "identifier": "TASK-123",
                        "title": "This should work fine",
                        "description": "Valid task",
                        "checklist": [{"title": "item"}],
                    }
                ],
            },
            context=context,
        )

        # Validation should fail for invalid identifier
        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {
                    "message": "Invalid",
                    "managed_tasks": [
                        {
                            "action": "UPDATE",
                            "identifier": "TASK-999",
                            "title": "Invalid",
                            "description": "Invalid",
                            "checklist": [],
                        }
                    ],
                },
                context=context,
            )
        assert_that(str(excinfo.value), contains_string("TASK-999"))
        assert_that(
            str(excinfo.value),
            contains_string(
                "but no such task identifier was found in the provided tasks."
            ),
        )

    def test_initiative_llm_response_validation(self):
        """Test InitiativeLLMResponse validation rejects updates to unknown initiative identifiers."""
        # Test the validation logic using the context mechanism
        # This requires calling the validator directly or via model_validate
        # Prepare context like process_prompt would
        context = {
            "valid_initiative_identifiers": {"INIT-1"}
        }  # Identifiers used for validation

        # Validation should pass for valid identifier
        InitiativeLLMResponse.model_validate(
            {
                "message": "Validating initiative identifier",
                "managed_initiatives": [
                    {
                        "action": "UPDATE",
                        "identifier": "INIT-1",
                        "title": "This should work fine",
                        "description": "Valid initiative",
                        "tasks": [],
                    }
                ],
            },
            context=context,
        )

        # Validation should fail for invalid identifier
        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid",
                    "managed_initiatives": [
                        {
                            "action": "UPDATE",
                            "identifier": "INIT-999",
                            "title": "Invalid",
                            "description": "Invalid",
                            "tasks": [],
                        }
                    ],
                },
                context=context,
            )
        assert_that(str(excinfo.value), contains_string("INIT-999"))
        assert_that(
            str(excinfo.value),
            contains_string(
                "but no such initiative identifier was found in the provided initiatives."
            ),
        )

    def test_task_create_validation(self):
        """Test validation of task creation with empty fields."""
        # Valid task creation
        valid_task = CreateTaskModel(
            title="Valid Title",
            description="Valid Description",
            checklist=None,  # This field expects List[Dict], None is valid
        )
        # CreateTaskModel does not use 'action' in its definition, but it's implicitly set
        # Test data should reflect the model definition
        empty_title_task_data = {
            "action": "CREATE",
            "title": "",
            "description": "Valid Description",
            "checklist": None,
        }
        empty_desc_task_data = {
            "action": "CREATE",
            "title": "Valid Title",
            "description": "",
            "checklist": None,
        }
        null_title_task_data = {
            "action": "CREATE",
            "title": None,
            "description": "Valid Description",
            "checklist": None,
        }
        null_desc_task_data = {
            "action": "CREATE",
            "title": "Valid Title",
            "description": None,
            "checklist": None,
        }

        # Validate directly using model_validate
        valid_response_data = {
            "message": "Valid creation",
            "managed_tasks": [valid_task.model_dump()],
        }
        TaskLLMResponse.model_validate(valid_response_data)  # Should pass

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_tasks": [empty_title_task_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {"message": "Invalid creation", "managed_tasks": [empty_desc_task_data]}
            )
        assert_that(str(excinfo.value), contains_string("description"))

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {"message": "Invalid creation", "managed_tasks": [null_title_task_data]}
            )
        assert_that(str(excinfo.value), contains_string("title"))

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {"message": "Invalid creation", "managed_tasks": [null_desc_task_data]}
            )
        assert_that(str(excinfo.value), contains_string("description"))

    def test_task_update_validation(self):
        """Test validation of task updates with empty fields."""
        valid_update = UpdateTaskModel(
            identifier="TASK-123",
            title="New Valid Title",
            description="New Valid Description",
            checklist=[ChecklistItemModel(title="item")],  # Correct checklist
        )
        # UpdateTaskModel uses action field
        empty_title_update_data = {
            "action": "UPDATE",
            "identifier": "TASK-123",
            "title": "",
            "description": "Valid Description",
            "checklist": [],
        }
        empty_desc_update_data = {
            "action": "UPDATE",
            "identifier": "TASK-123",
            "title": "Valid Title",
            "description": "",
            "checklist": [],
        }
        null_title_update_data = {
            "action": "UPDATE",
            "identifier": "TASK-123",
            "title": None,
            "description": "Valid Description",
            "checklist": [],
        }
        null_desc_update_data = {
            "action": "UPDATE",
            "identifier": "TASK-123",
            "title": "Valid Title",
            "description": None,
            "checklist": [],
        }

        # Validate directly using model_validate (context is needed for UPDATE identifier check)
        context = {"valid_task_ids": {"TASK-123"}}
        valid_response_data = {
            "message": "Valid update",
            "managed_tasks": [valid_update.model_dump()],
        }
        TaskLLMResponse.model_validate(
            valid_response_data, context=context
        )  # Should pass

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_tasks": [empty_title_update_data],
                },
                context=context,
            )
        assert_that(str(excinfo.value), contains_string("title"))

        with pytest.raises(ValidationError) as excinfo:
            TaskLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_tasks": [empty_desc_update_data],
                },
                context=context,
            )
        assert_that(str(excinfo.value), contains_string("description"))

        # Should not raise validation error
        # for null title and description
        TaskLLMResponse.model_validate(
            {
                "message": "Invalid update",
                "managed_tasks": [null_title_update_data],
            },
            context=context,
        )
        TaskLLMResponse.model_validate(
            {"message": "Invalid update", "managed_tasks": [null_desc_update_data]},
            context=context,
        )

    def test_initiative_create_validation(self):
        """Test validation of initiative creation with empty fields."""
        valid_initiative = CreateInitiativeModel(
            title="Valid Title",
            description="Valid Description",
            tasks=[],  # Should contain CreateTaskModel instances if not empty
        )
        # Test data should reflect the model definition
        empty_title_initiative_data = {
            "action": "CREATE",
            "title": "",
            "description": "Valid Description",
            "tasks": [],
        }
        empty_desc_initiative_data = {
            "action": "CREATE",
            "title": "Valid Title",
            "description": "",
            "tasks": [],
        }
        empty_title_initiative_data = {
            "action": "CREATE",
            "title": "",
            "description": "Valid Description",
            # Task data within initiative create should be raw dicts for validation
            "tasks": [
                {
                    "action": "CREATE",
                    "title": "",
                    "description": "Valid Task Desc",
                    "checklist": None,
                }
            ],  # Invalid task
        }
        null_title_initiative_data = {
            "action": "CREATE",
            "title": None,
            "description": "Valid Description",
            "tasks": [],
        }
        null_desc_initiative_data = {
            "action": "CREATE",
            "title": "Valid Title",
            "description": None,
            "tasks": [],
        }

        # Validate directly using model_validate
        valid_response_data = {
            "message": "Valid creation",
            "managed_initiatives": [valid_initiative.model_dump()],
        }
        InitiativeLLMResponse.model_validate(valid_response_data)  # Should pass

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_initiatives": [empty_title_initiative_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Initiative title

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_initiatives": [empty_desc_initiative_data],
                }
            )
        assert_that(
            str(excinfo.value), contains_string("description")
        )  # Initiative description

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_initiatives": [empty_title_initiative_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Checks task title

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_initiatives": [null_title_initiative_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Checks task title

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid creation",
                    "managed_initiatives": [null_desc_initiative_data],
                }
            )
        assert_that(
            str(excinfo.value), contains_string("description")
        )  # Checks task title

    def test_initiative_update_validation(self):
        """Test validation of initiative updates with empty fields."""
        valid_update = UpdateInitiativeModel(
            identifier="INIT-1",
            title="New Valid Title",
            description="New Valid Description",
            tasks=[
                UpdateTaskModel(
                    identifier="TASK-1",
                    title="T",
                    description="D",
                    checklist=[ChecklistItemModel(title="i")],
                )
            ],
        )
        # Test data reflects model structure
        empty_title_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": "",
            "description": "Valid Description",
            "tasks": [],
        }
        empty_desc_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": "Valid Title",
            "description": "",
            "tasks": [],
        }
        empty_task_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": "",
            "description": "Valid Description",
            # Task data within initiative update should be raw dicts for validation
            "tasks": [
                {
                    "action": "UPDATE",
                    "identifier": "TASK-1",
                    "title": "",
                    "description": "Valid Desc",
                    "checklist": [],
                }
            ],  # Invalid task title
        }
        null_desc_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": "Valid Title",
            "description": None,
            "tasks": [
                {
                    "action": "UPDATE",
                    "identifier": "TASK-1",
                    "title": "Valid task title",
                    "description": "Valid Desc",
                    "checklist": [],
                }
            ],  # Invalid task title
        }
        null_title_update_data = {
            "action": "UPDATE",
            "identifier": "INIT-1",
            "title": None,
            "description": "Valid Description",
            "tasks": [],
        }

        # Validate directly using model_validate
        # Context might be needed if task updates require identifier validation within InitiativeLLMResponse
        # For now, assuming initiative update focuses on its own fields + nested task validation
        valid_response_data = {
            "message": "Valid update",
            "managed_initiatives": [valid_update.model_dump()],
        }
        InitiativeLLMResponse.model_validate(valid_response_data)  # Should pass

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_initiatives": [empty_title_update_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Initiative title

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_initiatives": [empty_desc_update_data],
                }
            )
        assert_that(
            str(excinfo.value), contains_string("description")
        )  # Initiative description

        with pytest.raises(ValidationError) as excinfo:
            InitiativeLLMResponse.model_validate(
                {
                    "message": "Invalid update",
                    "managed_initiatives": [empty_task_update_data],
                }
            )
        assert_that(str(excinfo.value), contains_string("title"))  # Checks task title

        # Should not raise validation error
        # for null title and description
        InitiativeLLMResponse.model_validate(
            {
                "message": "Invalid update",
                "managed_initiatives": [null_desc_update_data],
            }
        )
        InitiativeLLMResponse.model_validate(
            {
                "message": "Invalid update",
                "managed_initiatives": [null_title_update_data],
            }
        )
