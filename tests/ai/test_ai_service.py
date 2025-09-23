import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, contains_string, equal_to, instance_of

from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.ai.ai_service import (
    AIImprovementError,
    BalanceCheckResult,
    LLMAPIError,
    VaultError,
    get_user_api_key,
    process_initiative_improvement,
    process_task_improvement,
    revalidate_user_key,
)
from src.ai.models import ChatMessageInput
from src.ai.prompt import InitiativeLLMResponse, TaskLLMResponse, TaskPrompt
from src.config import settings
from src.models import (
    APIProvider,
    BalanceWarning,
    ChatMode,
    ChecklistItemModel,
    ContextDocument,
    Initiative,
    InitiativeType,
    Lens,
    ManagedEntityAction,
    PydanticInitiative,
    PydanticTask,
    Task,
    TaskStatus,
    TaskType,
    UpdateInitiativeModel,
    UpdateTaskModel,
    UserKey,
)


@pytest.fixture
def initiative(session, user, workspace) -> Initiative:
    """Create a real Initiative object in the test database"""
    initiative = Initiative(
        title="Test Initiative",
        description="This is a test initiative for AI improvement",
        status=TaskStatus.TO_DO,
        type=InitiativeType.FEATURE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id=user.id,
        workspace_id=workspace.id,
    )

    session.add(initiative)
    session.commit()
    session.refresh(initiative)
    return initiative


@pytest.fixture
def task(session, initiative, user, workspace) -> Task:
    """Create a real Task object in the test database"""
    task = Task(
        title="Test Task",
        identifier="test-task-123",
        description="This is a test task for AI improvement",
        status=TaskStatus.TO_DO,
        type=TaskType.CODING,
        initiative_id=initiative.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        user_id=user.id,
        workspace_id=workspace.id,
    )

    initiative.tasks.append(task)
    session.add(initiative)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def valid_user_key(session, user) -> UserKey:
    """Create a valid UserKey object in the test database."""
    key = UserKey()
    key.user_id = user.id
    key.provider = APIProvider.LITELLM
    key.is_valid = True
    key.last_validated_at = datetime.now()
    key.redacted_key = "sk-***1234"
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


@pytest.fixture
def invalid_user_key(session, user) -> UserKey:
    """Create an invalid UserKey object in the test database."""
    key = UserKey()
    key.user_id = user.id
    key.provider = APIProvider.LITELLM
    key.is_valid = False
    key.last_validated_at = datetime.now() - timedelta(days=10)
    key.redacted_key = "sk-***1234"
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


@pytest.fixture
def context_document(session, user, workspace) -> ContextDocument:
    """Create a ContextDocument for testing."""
    doc = ContextDocument(
        title="Test Context Doc",
        content="This is the shared context for the workspace.",
        user_id=user.id,
        workspace_id=workspace.id,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


class TestGetUserApiKey:
    """Test suite for get_user_api_key function."""

    @patch("src.ai.ai_service.retrieve_api_key_from_vault")
    def test_successful_retrieval(
        self, mock_retrieve_vault, session, user, valid_user_key
    ):
        """Test successful API key retrieval."""
        # Setup
        mock_retrieve_vault.return_value = "test_api_key_123"

        # Execute
        api_key = get_user_api_key(user.id, session)

        # Verify
        assert_that(api_key, equal_to("test_api_key_123"))
        mock_retrieve_vault.assert_called_once_with(valid_user_key.vault_path)

    def test_litellm_master_key_returned_for_all_NEW_users(self, session, user):
        """Test when the UserKey for the user and provider is not found."""
        # Setup - No UserKey created for this user/provider combo
        account_details: UserAccountDetails = (
            session.query(UserAccountDetails)
            .filter(UserAccountDetails.user_id == user.id)
            .first()
        )
        account_details.status = UserAccountStatus.NEW
        session.add(account_details)
        session.commit()

        # Execute & Verify
        assert_that(
            get_user_api_key(user.id, session), equal_to(settings.litellm_master_key)
        )

    def test_user_key_not_found(self, session, user):
        """Test when the UserKey for the user and provider is not found."""
        # Setup - No UserKey created for this user/provider combo
        account_details: UserAccountDetails = (
            session.query(UserAccountDetails)
            .filter(UserAccountDetails.user_id == user.id)
            .first()
        )
        account_details.status = UserAccountStatus.ACTIVE_SUBSCRIPTION
        session.add(account_details)
        session.commit()

        # Execute & Verify
        with pytest.raises(VaultError) as excinfo:
            get_user_api_key(user.id, session)
        assert_that(
            str(excinfo.value),
            contains_string(f"API key not found for user {user.id}"),
        )

    def test_user_key_not_valid(self, session, user, invalid_user_key):
        """Test when the UserKey is found but is_valid is False."""
        # Setup - invalid_user_key fixture creates a key with is_valid=False

        # Execute & Verify
        with pytest.raises(VaultError) as excinfo:
            get_user_api_key(user.id, session)
        assert_that(
            str(excinfo.value),
            contains_string(f"API key for user {user.id} is marked as not valid"),
        )

    @patch("src.ai.ai_service.retrieve_api_key_from_vault")
    def test_vault_retrieval_fails(
        self, mock_retrieve_vault, session, user, valid_user_key
    ):
        """Test when retrieving the key from Vault fails."""
        # Setup
        mock_retrieve_vault.side_effect = Exception("Vault connection error")

        # Execute & Verify
        with pytest.raises(VaultError) as excinfo:
            get_user_api_key(user.id, session)
        assert_that(
            str(excinfo.value),
            contains_string(
                "Could not retrieve your API key. Please check your API key in the settings."
            ),
        )


class TestProcessInitiativeImprovement:
    """Test suite for process_initiative_improvement function."""

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.InitiativePrompt")
    async def test_successful_improvement(
        self,
        mock_initiative_prompt_class,
        mock_get_key,
        mock_check_balance,
        initiative,
        task,
        valid_user_key,
        user,
        workspace,
    ):
        """Test successful initiative improvement with default parameters."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_check_balance.return_value = BalanceCheckResult(
            can_proceed=True,
            balance_warning=None,
        )
        mock_prompt_instance = Mock()
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=(
                lambda *args, **kwargs: InitiativeLLMResponse(
                    message="The title and description were improved for clarity.",
                    managed_initiatives=[
                        UpdateInitiativeModel(
                            action=ManagedEntityAction.UPDATE,
                            identifier=initiative.identifier,
                            title="Improved Initiative Title",
                            description="Improved Initiative Description",
                            tasks=[managed_task],
                        )
                    ],
                )
            )
        )
        mock_initiative_prompt_class.return_value = mock_prompt_instance

        # Prepare input data as dictionary
        initiative_dict = initiative.to_dict()
        task_dict = task.to_dict()
        # Prepare mock response data (remains the same)
        managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Improved Task Title",
            description="Improved Task Description",
            checklist=None,
        )
        managed_initiative = UpdateInitiativeModel(
            action=ManagedEntityAction.UPDATE,
            identifier=initiative.identifier,
            title="Improved Initiative Title",
            description="Improved Initiative Description",
            tasks=[
                managed_task
            ],  # Use the same UpdateTaskModel for consistency in the mock
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: InitiativeLLMResponse(
                message="The title and description were improved for clarity.",
                managed_initiatives=[managed_initiative],
            )
        )

        # Execute
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="This is the user message",
                suggested_changes=[],
            )
        ]
        # Pass the initiative as a dictionary within a list
        result = await process_initiative_improvement(
            "thread-1",
            user,
            [initiative_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        # Verify the response is the LLM response object
        assert_that(result, instance_of(InitiativeLLMResponse))
        assert isinstance(result, InitiativeLLMResponse)
        assert_that(
            result.message,
            equal_to("The title and description were improved for clarity."),
        )
        assert_that(len(result.managed_initiatives), equal_to(1))

        # Verify the managed initiative details
        managed_initiative_result = result.managed_initiatives[0]
        assert isinstance(managed_initiative_result, UpdateInitiativeModel)
        assert_that(
            managed_initiative_result.action, equal_to(ManagedEntityAction.UPDATE)
        )
        assert_that(
            managed_initiative_result.title, equal_to("Improved Initiative Title")
        )
        assert_that(
            managed_initiative_result.description,
            equal_to("Improved Initiative Description"),
        )

        assert_that(managed_initiative_result.tasks, equal_to([managed_task]))

        # Verify the InitiativePrompt was created with the correct parameters
        mock_initiative_prompt_class.assert_called_once()
        call_args, call_kwargs = mock_initiative_prompt_class.call_args

        # Check the positional arguments
        assert (
            len(call_args) == 1
        ), "InitiativePrompt should receive one positional argument (initiatives list)"
        initiatives_arg = call_args[0]
        assert isinstance(initiatives_arg, list), "First argument should be a list"
        assert len(initiatives_arg) == 1, "Initiatives list should contain one element"
        # Check if the element is a PydanticInitiative instance
        assert isinstance(
            initiatives_arg[0], PydanticInitiative
        ), "Element should be a PydanticInitiative instance"
        # Optionally, verify some attributes of the parsed PydanticInitiative object match the input dict
        assert initiatives_arg[0].id == initiative.id
        assert initiatives_arg[0].title == initiative.title
        assert isinstance(initiatives_arg[0].tasks, list)
        assert len(initiatives_arg[0].tasks) == 1
        assert isinstance(initiatives_arg[0].tasks[0], PydanticTask)
        assert initiatives_arg[0].tasks[0].id == task.id

        # Check keyword arguments
        assert call_kwargs.get("messages") == sample_messages
        assert call_kwargs.get("additional_context") == ""

        # Verify process_prompt was called with the dummy key
        mock_prompt_instance.process_prompt.assert_called_once_with(
            api_key="dummy_api_key",
            user_auth_token="access_token",
            workspace_id=str(workspace.id),
            thread_id="thread-1",
            user_id=str(user.id),
        )
        mock_get_key.assert_called_once_with(user.id, ANY)

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.InitiativePrompt")
    async def test_successful_improvement_with_context(
        self,
        mock_initiative_prompt_class,
        mock_get_key,
        mock_check_balance,
        initiative,
        task,
        valid_user_key,
        user,
        context_document,
        workspace,
    ):
        """Test successful initiative improvement when a ContextDocument exists."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_check_balance.return_value = BalanceCheckResult(
            can_proceed=True,
            balance_warning=None,
        )
        mock_prompt_instance = mock_initiative_prompt_class.return_value

        # Prepare input data as dictionary
        initiative_dict = initiative.to_dict()
        task_dict = task.to_dict()
        # Prepare mock response data (remains the same)
        managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Improved Task Title",
            description="Improved Task Description",
            checklist=None,
        )
        managed_initiative = UpdateInitiativeModel(
            action=ManagedEntityAction.UPDATE,
            identifier=initiative.identifier,
            title="Improved Initiative Title",
            description="Improved Initiative Description",
            tasks=[
                managed_task
            ],  # Use the same UpdateTaskModel for consistency in the mock
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: InitiativeLLMResponse(
                message="The title and description were improved for clarity.",
                managed_initiatives=[managed_initiative],
            )
        )

        # Execute
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="This is the user message",
                suggested_changes=[],
            )
        ]
        # Pass the initiative as a dictionary within a list
        result = await process_initiative_improvement(
            "thread-1",
            user,
            [initiative_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        # Verify the response is the LLM response object
        assert_that(result, instance_of(InitiativeLLMResponse))
        assert isinstance(result, InitiativeLLMResponse)
        assert_that(
            result.message,
            equal_to("The title and description were improved for clarity."),
        )
        assert_that(len(result.managed_initiatives), equal_to(1))

        # Verify the managed initiative details
        managed_initiative_result = result.managed_initiatives[0]
        assert isinstance(managed_initiative_result, UpdateInitiativeModel)
        assert_that(
            managed_initiative_result.action, equal_to(ManagedEntityAction.UPDATE)
        )
        assert_that(
            managed_initiative_result.title, equal_to("Improved Initiative Title")
        )
        assert_that(
            managed_initiative_result.description,
            equal_to("Improved Initiative Description"),
        )

        assert_that(managed_initiative_result.tasks, equal_to([managed_task]))

        # Verify the InitiativePrompt was created with the correct parameters
        mock_initiative_prompt_class.assert_called_once()
        call_args, call_kwargs = mock_initiative_prompt_class.call_args

        # Check the positional arguments
        assert (
            len(call_args) == 1
        ), "InitiativePrompt should receive one positional argument (initiatives list)"
        initiatives_arg = call_args[0]
        assert isinstance(initiatives_arg, list), "First argument should be a list"
        assert len(initiatives_arg) == 1, "Initiatives list should contain one element"
        # Check if the element is a PydanticInitiative instance
        assert isinstance(
            initiatives_arg[0], PydanticInitiative
        ), "Element should be a PydanticInitiative instance"
        # Optionally, verify some attributes of the parsed PydanticInitiative object match the input dict
        assert initiatives_arg[0].id == initiative.id
        assert initiatives_arg[0].title == initiative.title
        assert isinstance(initiatives_arg[0].tasks, list)
        assert len(initiatives_arg[0].tasks) == 1
        assert isinstance(initiatives_arg[0].tasks[0], PydanticTask)
        assert initiatives_arg[0].tasks[0].id == task.id

        # Check keyword arguments
        assert call_kwargs.get("messages") == sample_messages
        assert call_kwargs.get("additional_context") == context_document.content

        # Verify process_prompt was called with the dummy key
        mock_prompt_instance.process_prompt.assert_called_once_with(
            api_key="dummy_api_key",
            user_auth_token="access_token",
            workspace_id=str(workspace.id),
            thread_id="thread-1",
            user_id=str(user.id),
        )
        mock_get_key.assert_called_once_with(user.id, ANY)

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.InitiativePrompt")
    async def test_successful_improvement_no_context(
        self,
        mock_initiative_prompt_class,
        mock_get_key,
        mock_check_balance,
        initiative,
        task,
        valid_user_key,
        user,
    ):
        """Test successful initiative improvement when no ContextDocument exists."""
        # Setup - No context_document fixture used
        mock_get_key.return_value = "dummy_api_key"
        mock_check_balance.return_value = BalanceCheckResult(
            can_proceed=True,
            balance_warning=None,
        )
        mock_prompt_instance = mock_initiative_prompt_class.return_value

        initiative_dict = initiative.to_dict()
        managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Improved Task Title",
            description="Improved Task Description (No Context)",
            checklist=None,
        )
        managed_initiative = UpdateInitiativeModel(
            action=ManagedEntityAction.UPDATE,
            identifier=initiative.identifier,
            title="Improved Initiative Title",
            description="Improved Initiative Description",
            tasks=[managed_task],
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: InitiativeLLMResponse(
                message="Improvement without context.",
                managed_initiatives=[managed_initiative],
            )
        )

        # Execute
        result = await process_initiative_improvement(
            "thread-1",
            user,
            [initiative_dict],
            mode=ChatMode.EDIT,
        )

        # Verify
        assert_that(result, instance_of(InitiativeLLMResponse))
        mock_initiative_prompt_class.assert_called_once()
        _, call_kwargs = mock_initiative_prompt_class.call_args
        # Verify additional_context is empty
        assert call_kwargs.get("additional_context") == ""

    async def test_initiative_parse_error(self, user):
        """Test error handling when initiative data in input_data is invalid."""
        # Setup invalid data (e.g., missing required field like 'title')
        invalid_initiative_dict = {
            "id": uuid.uuid4(),
            # "title": "Missing Title", # Intentionally missing
            "description": "This dict is invalid",
            "user_id": user.id,
            "workspace_id": uuid.uuid4(),  # Assume workspace_id is needed
        }

        result = await process_initiative_improvement(
            "thread-1",
            user,
            [invalid_initiative_dict],
            mode=ChatMode.EDIT,
        )

        # The function should return an error object due to parsing failure
        assert isinstance(result, AIImprovementError)
        assert_that(result.type, equal_to("initiative"))
        assert_that(result.status, equal_to("error"))
        assert_that(
            result.error_message, contains_string("Invalid initiative data provided")
        )
        assert_that(result.error_message, contains_string("Field required"))
        assert_that(result.error_message, contains_string("title"))
        assert_that(result.error_type, equal_to("value_error"))

    @patch("src.ai.ai_service.get_user_api_key")
    async def test_api_key_retrieval_error(
        self, mock_get_key, initiative, valid_user_key, user
    ):
        """Test error handling when API key retrieval fails."""
        # Setup
        mock_get_key.side_effect = VaultError("Invalid key for user")
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="Test message",
                suggested_changes=[],
            )
        ]
        initiative_dict = initiative.to_dict()

        # Execute - Pass initiative as dict
        result = await process_initiative_improvement(
            "thread-1",
            user,
            [initiative_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        # Verify
        assert type(result) == AIImprovementError
        assert_that(result.type, equal_to("initiative"))
        assert_that(result.status, equal_to("error"))
        assert_that(result.error_message, contains_string("Invalid key for user"))
        assert_that(result.error_type, equal_to("api_key_error"))
        mock_get_key.assert_called_once_with(user.id, ANY)

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.InitiativePrompt")
    async def test_user_doesnt_have_enough_balance_for_request(
        self,
        mock_initiative_prompt_class,
        mock_get_key,
        mock_check_balance,
        initiative,
        task,
        valid_user_key,
        user,
        workspace,
    ):
        """Test successful initiative improvement with default parameters."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_check_balance.return_value = BalanceCheckResult(
            can_proceed=False,
            balance_warning=BalanceWarning(
                warning_type="insufficient_balance",
                message="User does not have enough balance",
            ),
        )
        mock_prompt_instance = Mock()
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=(
                lambda *args, **kwargs: InitiativeLLMResponse(
                    message="The title and description were improved for clarity.",
                    managed_initiatives=[
                        UpdateInitiativeModel(
                            action=ManagedEntityAction.UPDATE,
                            identifier=initiative.identifier,
                            title="Improved Initiative Title",
                            description="Improved Initiative Description",
                            tasks=[managed_task],
                        )
                    ],
                )
            )
        )
        mock_initiative_prompt_class.return_value = mock_prompt_instance

        # Prepare input data as dictionary
        initiative_dict = initiative.to_dict()
        task_dict = task.to_dict()
        # Prepare mock response data (remains the same)
        managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Improved Task Title",
            description="Improved Task Description",
            checklist=None,
        )
        managed_initiative = UpdateInitiativeModel(
            action=ManagedEntityAction.UPDATE,
            identifier=initiative.identifier,
            title="Improved Initiative Title",
            description="Improved Initiative Description",
            tasks=[
                managed_task
            ],  # Use the same UpdateTaskModel for consistency in the mock
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: InitiativeLLMResponse(
                message="The title and description were improved for clarity.",
                managed_initiatives=[managed_initiative],
            )
        )

        # Execute
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="This is the user message",
                suggested_changes=[],
            )
        ]
        # Pass the initiative as a dictionary within a list
        result = await process_initiative_improvement(
            "thread-1",
            user,
            [initiative_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        expected_result = AIImprovementError(
            type="initiative",
            status="error",
            error_message="User does not have enough balance",
            error_type="insufficient_balance",
        )
        assert_that(result, equal_to(expected_result))


class TestProcessTaskImprovement:
    """Test suite for process_task_improvement function."""

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.TaskPrompt")
    async def test_successful_improvement(
        self,
        mockTaskPromptClass,
        mock_get_key,
        mock_check_balance,
        task,
        initiative,
        valid_user_key,
        user,
        session,
        workspace,
    ):
        """Test successful task improvement with default parameters."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_check_balance.return_value = BalanceCheckResult(
            can_proceed=True,
            balance_warning=None,
        )
        # Use the real session provided by the fixture

        # Mock the TaskPrompt class and its process_prompt method
        mock_prompt_instance = mockTaskPromptClass.return_value
        mock_summary = (
            "The task has been improved with a clearer title and description."
        )
        mock_managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Improved Task Title",
            description="This is an improved description for the task.",
            checklist=[
                ChecklistItemModel(title="Step 1"),
                ChecklistItemModel(title="Step 2"),
            ],
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: TaskLLMResponse(
                message=mock_summary,
                managed_tasks=[mock_managed_task],
            )
        )

        # Prepare input data as dictionary (using the updated to_dict)
        task_dict = task.to_dict()

        # Execute
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="This is the user task message",
                suggested_changes=[],
            )
        ]
        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [task_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        # Verify TaskPrompt was created with the correct parameters
        mockTaskPromptClass.assert_called_once()
        call_args, call_kwargs = mockTaskPromptClass.call_args

        # Check positional args: list of Task objects
        assert (
            len(call_args) == 1
        ), "TaskPrompt should receive one positional argument (tasks list)"
        tasks_arg = call_args[0]
        assert isinstance(tasks_arg, list), "First argument should be a list"
        assert len(tasks_arg) == 1, "Tasks list should contain one element"
        assert isinstance(
            tasks_arg[0], PydanticTask
        ), "Element should be a Task instance"
        assert tasks_arg[0].id == task.id
        assert tasks_arg[0].identifier == task.identifier
        assert tasks_arg[0].title == task.title

        # Check keyword args: initiative, messages, context
        # Initiative should be fetched from the real session within the function
        assert call_kwargs.get("initiative") is not None
        assert call_kwargs["initiative"].id == initiative.id
        assert call_kwargs.get("messages") == sample_messages
        assert call_kwargs.get("additional_context") == ""

        # Verify the TaskLLMResponse content
        assert_that(result, instance_of(TaskLLMResponse))
        assert isinstance(result, TaskLLMResponse)
        assert_that(result.message, equal_to(mock_summary))
        assert_that(len(result.managed_tasks), equal_to(1))

        # Verify the managed task details
        managed_task_result = result.managed_tasks[0]
        assert isinstance(managed_task_result, UpdateTaskModel)
        assert_that(managed_task_result.action, equal_to(ManagedEntityAction.UPDATE))
        assert_that(managed_task_result.identifier, equal_to(task.identifier))
        assert_that(managed_task_result.title, equal_to("Improved Task Title"))
        assert_that(
            managed_task_result.description,
            equal_to("This is an improved description for the task."),
        )
        assert_that(
            managed_task_result.checklist,
            equal_to(
                [ChecklistItemModel(title="Step 1"), ChecklistItemModel(title="Step 2")]
            ),
        )

        # Verify the key retrieval and prompt processing were called
        # Ensure the real session was used by get_key (via get_db internally)
        mock_get_key.assert_called_once_with(user.id, ANY)
        mock_prompt_instance.process_prompt.assert_called_once_with(
            api_key="dummy_api_key",
            user_auth_token="access_token",
            workspace_id=str(workspace.id),
            thread_id="thread-1",
            user_id=str(user.id),
        )

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.TaskPrompt")
    async def test_successful_improvement_with_context(
        self,
        mockTaskPromptClass,
        mock_get_key,
        mock_check_balance,
        task,
        initiative,
        valid_user_key,
        user,
        session,
        context_document,
        workspace,
    ):
        """Test successful task improvement when a ContextDocument exists."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_check_balance.return_value = BalanceCheckResult(
            can_proceed=True,
            balance_warning=None,
        )
        # Use the real session provided by the fixture

        # Mock the TaskPrompt class and its process_prompt method
        mock_prompt_instance = mockTaskPromptClass.return_value
        mock_managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Improved Task Title",
            description="This is an improved description for the task.",
            checklist=[
                ChecklistItemModel(title="Step 1"),
                ChecklistItemModel(title="Step 2"),
            ],
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: TaskLLMResponse(
                message="The task has been improved with a clearer title and description.",
                managed_tasks=[mock_managed_task],
            )
        )

        # Prepare input data as dictionary (using the updated to_dict)
        task_dict = task.to_dict()

        # Execute
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="This is the user task message",
                suggested_changes=[],
            )
        ]
        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [task_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )
        # Verify TaskPrompt was created with the correct parameters
        mockTaskPromptClass.assert_called_once()
        call_args, call_kwargs = mockTaskPromptClass.call_args

        # Check positional args: list of Task objects
        assert (
            len(call_args) == 1
        ), "TaskPrompt should receive one positional argument (tasks list)"
        tasks_arg = call_args[0]
        assert isinstance(tasks_arg, list), "First argument should be a list"
        assert len(tasks_arg) == 1, "Tasks list should contain one element"
        assert isinstance(
            tasks_arg[0], PydanticTask
        ), "Element should be a Task instance"
        assert tasks_arg[0].id == task.id
        assert tasks_arg[0].identifier == task.identifier
        assert tasks_arg[0].title == task.title

        # Check keyword args: initiative, messages, context
        # Initiative should be fetched from the real session within the function
        assert call_kwargs.get("initiative") is not None
        assert call_kwargs["initiative"].id == initiative.id
        assert call_kwargs.get("messages") == sample_messages
        # Verify context document content is used
        assert call_kwargs.get("additional_context") == context_document.content

        # Verify the TaskLLMResponse content
        assert_that(result, instance_of(TaskLLMResponse))
        assert isinstance(result, TaskLLMResponse)
        assert_that(
            result.message,
            equal_to(
                "The task has been improved with a clearer title and description."
            ),
        )
        assert_that(len(result.managed_tasks), equal_to(1))

        # Verify the managed task details
        managed_task_result = result.managed_tasks[0]
        assert isinstance(managed_task_result, UpdateTaskModel)
        assert_that(managed_task_result.action, equal_to(ManagedEntityAction.UPDATE))
        assert_that(managed_task_result.identifier, equal_to(task.identifier))
        assert_that(managed_task_result.title, equal_to("Improved Task Title"))
        assert_that(
            managed_task_result.description,
            equal_to("This is an improved description for the task."),
        )
        assert_that(
            managed_task_result.checklist,
            equal_to(
                [ChecklistItemModel(title="Step 1"), ChecklistItemModel(title="Step 2")]
            ),
        )

        # Verify the key retrieval and prompt processing were called
        # Ensure the real session was used by get_key (via get_db internally)
        mock_get_key.assert_called_once_with(user.id, ANY)
        mock_prompt_instance.process_prompt.assert_called_once_with(
            api_key="dummy_api_key",
            user_auth_token="access_token",
            workspace_id=str(workspace.id),
            thread_id="thread-1",
            user_id=str(user.id),
        )

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.TaskPrompt")
    async def test_successful_improvement_no_context(
        self,
        mockTaskPromptClass,
        mock_get_key,
        mock_check_balance,
        task,
        initiative,
        valid_user_key,
        user,
        session,
    ):
        """Test successful task improvement when no ContextDocument exists."""
        # Setup - No context_document fixture used
        mock_get_key.return_value = "dummy_api_key"
        mock_check_balance.return_value = BalanceCheckResult(
            can_proceed=True,
            balance_warning=None,
        )
        mock_prompt_instance = mockTaskPromptClass.return_value

        mock_summary = "Task improved without extra context."
        mock_managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Improved Task Title (No Context)",
            description="Improved Task Description (No Context)",
            checklist=None,
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: TaskLLMResponse(
                message=mock_summary,
                managed_tasks=[mock_managed_task],
            )
        )

        task_dict = task.to_dict()

        # Execute
        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [task_dict],
            mode=ChatMode.EDIT,
        )

        # Verify
        assert_that(result, instance_of(TaskLLMResponse))
        mockTaskPromptClass.assert_called_once()
        _, call_kwargs = mockTaskPromptClass.call_args
        # Verify additional_context is empty
        assert call_kwargs.get("additional_context") == ""

    async def test_task_parse_error(self, user, initiative):
        """Test error handling when task data in input_data is invalid."""
        # Setup invalid data (e.g., missing required field like 'title')
        invalid_task_dict = {
            "id": uuid.uuid4(),
            # "title": "Missing Title", # Intentionally missing
            "description": "This dict is invalid",
            "user_id": user.id,
            "initiative_id": initiative.id,
            "workspace_id": uuid.uuid4(),  # Assume workspace_id is needed
        }

        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [invalid_task_dict],
            mode=ChatMode.EDIT,
        )

        # The function should return an error object due to parsing failure
        assert isinstance(result, AIImprovementError)
        assert_that(result.type, equal_to("task"))
        assert_that(result.status, equal_to("error"))
        assert_that(result.error_message, contains_string("Invalid task data provided"))
        assert_that(result.error_message, contains_string("Field required"))
        assert_that(result.error_message, contains_string("title"))
        assert_that(result.error_type, equal_to("value_error"))

    @patch("src.ai.ai_service.get_user_api_key")
    async def test_api_key_retrieval_error(
        self, mock_get_key, task, valid_user_key, user, session
    ):
        """Test error handling when API key retrieval fails."""
        # Setup
        mock_get_key.side_effect = VaultError("Vault access denied")
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="Test message",
                suggested_changes=[],
            )
        ]
        task_dict = task.to_dict()

        # Execute - Pass task as dict
        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [task_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        # Verify
        assert type(result) == AIImprovementError
        assert_that(result.type, equal_to("task"))
        assert_that(result.status, equal_to("error"))
        assert_that(result.error_message, contains_string("Vault access denied"))
        assert_that(result.error_type, equal_to("api_key_error"))
        mock_get_key.assert_called_once_with(user.id, ANY)  # Check session is used

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch.object(TaskPrompt, "process_prompt")
    async def test_llm_api_error(
        self,
        mock_prompt_process,
        mock_get_key,
        mock_check_user_can_afford_request,
        task,
        valid_user_key,
        user,
        initiative,
        session,
        workspace,
    ):
        """Test error handling when LLM API call fails."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_prompt_process.side_effect = LLMAPIError("API connection failed")
        mock_check_user_can_afford_request.return_value = BalanceCheckResult(
            can_proceed=True
        )
        # Use the real session provided by the fixture

        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="Test message",
                suggested_changes=[],
            )
        ]
        task_dict = task.to_dict()

        # Execute - Pass task as dict
        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [task_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        # Verify
        assert_that(result, instance_of(AIImprovementError))
        if isinstance(result, AIImprovementError):
            assert_that(
                result.error_type, equal_to("llm_api_error")
            )  # Error type from the AuthenticationError

        mock_get_key.assert_called_once_with(user.id, ANY)  # Check session is used
        # We patch process_prompt directly, so check its call
        mock_prompt_process.assert_called_once_with(
            api_key="dummy_api_key",
            user_auth_token="access_token",
            workspace_id=str(workspace.id),
            thread_id="thread-1",
            user_id=str(user.id),
        )
        # No need to verify internal session calls

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.TaskPrompt")
    async def test_checklist_processing(
        self,
        mock_task_prompt_class,
        mock_get_key,
        mock_check_user_can_afford_request,
        task,
        valid_user_key,
        user,
        initiative,
        session,
        workspace,
    ):
        """Test that checklist items are properly processed within the new structure."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_check_user_can_afford_request.return_value = BalanceCheckResult(
            can_proceed=True
        )

        # Mock the TaskPrompt class and its process_prompt method
        mock_prompt_instance = mock_task_prompt_class.return_value
        mock_summary = "Added a comprehensive checklist for better tracking."
        mock_checklist_data = [
            ChecklistItemModel(title="Update model.py"),
            ChecklistItemModel(title="Write unit tests"),
            ChecklistItemModel(title="Update documentation"),
        ]
        mock_managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Task with Checklist",
            description="This task has a detailed checklist.",
            checklist=mock_checklist_data,
        )
        mock_response = TaskLLMResponse(
            message=mock_summary,
            managed_tasks=[mock_managed_task],
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: mock_response
        )

        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="This is the user task message",
                suggested_changes=[],
            )
        ]
        task_dict = task.to_dict()
        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [task_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )
        # Verify the result is a TaskLLMResponse
        assert_that(result, instance_of(TaskLLMResponse))
        assert isinstance(result, TaskLLMResponse)

        # Verify the TaskLLMResponse content
        assert_that(result.message, equal_to(mock_summary))
        assert_that(len(result.managed_tasks), equal_to(1))

        # Verify the managed task details
        managed_task_result = result.managed_tasks[0]
        assert isinstance(managed_task_result, UpdateTaskModel)
        assert_that(managed_task_result.action, equal_to(ManagedEntityAction.UPDATE))
        assert_that(managed_task_result.identifier, equal_to(task.identifier))
        assert_that(managed_task_result.title, equal_to("Task with Checklist"))
        assert_that(
            managed_task_result.description,
            equal_to("This task has a detailed checklist."),
        )

        # Verify the checklist within the managed task
        assert_that(managed_task_result.checklist, instance_of(list))
        assert managed_task_result.checklist is not None

        # Check first item
        assert_that(managed_task_result.checklist[0].title, equal_to("Update model.py"))

        # Check second item
        assert_that(
            managed_task_result.checklist[1].title, equal_to("Write unit tests")
        )

        # Check third item
        assert_that(
            managed_task_result.checklist[2].title, equal_to("Update documentation")
        )

        # Verify mocks
        mock_get_key.assert_called_once_with(user.id, ANY)  # Check session is used
        mock_prompt_instance.process_prompt.assert_called_once_with(
            api_key="dummy_api_key",
            user_auth_token="access_token",
            workspace_id=str(workspace.id),
            thread_id="thread-1",
            user_id=str(user.id),
        )
        # No need to verify internal session calls

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.TaskPrompt")
    async def test_empty_checklist(
        self,
        mock_task_prompt_class,
        mock_get_key,
        mock_check_user_can_afford_request,
        task,
        valid_user_key,
        user,
        initiative,
        session,
        workspace,
    ):
        """Test handling of empty checklist within the new structure."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_check_user_can_afford_request.return_value = BalanceCheckResult(
            can_proceed=True
        )

        # Mock the TaskPrompt class and its process_prompt method
        mock_prompt_instance = mock_task_prompt_class.return_value
        mock_summary = "Updated the task but no checklist items needed."
        mock_managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Task with Empty Checklist",
            description="This task has no checklist items.",
            checklist=[],
        )
        mock_response = TaskLLMResponse(
            message=mock_summary,
            managed_tasks=[mock_managed_task],
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: mock_response
        )

        # Execute - Pass task as dict
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="This is the user task message",
                suggested_changes=[],
            )
        ]
        task_dict = task.to_dict()
        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [task_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )
        # Verify the result is a TaskLLMResponse
        assert_that(result, instance_of(TaskLLMResponse))
        assert isinstance(result, TaskLLMResponse)

        # Verify the TaskLLMResponse content
        assert_that(result.message, equal_to(mock_summary))
        assert_that(len(result.managed_tasks), equal_to(1))

        # Verify the managed task details
        managed_task_result = result.managed_tasks[0]
        assert isinstance(managed_task_result, UpdateTaskModel)
        assert_that(managed_task_result.action, equal_to(ManagedEntityAction.UPDATE))
        assert_that(managed_task_result.identifier, equal_to(task.identifier))
        assert_that(managed_task_result.title, equal_to("Task with Empty Checklist"))
        assert_that(
            managed_task_result.description,
            equal_to("This task has no checklist items."),
        )
        assert_that(managed_task_result.checklist, equal_to([]))

        # Verify mocks
        mock_get_key.assert_called_once_with(user.id, ANY)  # Check session is used
        mock_prompt_instance.process_prompt.assert_called_once_with(
            api_key="dummy_api_key",
            user_auth_token="access_token",
            workspace_id=str(workspace.id),
            thread_id="thread-1",
            user_id=str(user.id),
        )
        # No need to verify internal session calls

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch.object(TaskPrompt, "process_prompt")
    async def test_general_exception_during_prompt(
        self,
        mock_prompt_process,
        mock_get_key,
        mock_check_user_can_afford_request,
        task,
        valid_user_key,
        user,
        initiative,
        session,
        workspace,
    ):
        """Test error handling for general exceptions during prompt processing."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_prompt_process.side_effect = Exception("Unexpected error")
        mock_check_user_can_afford_request.return_value = BalanceCheckResult(
            can_proceed=True
        )
        # Use the real session provided by the fixture

        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="Test message",
                suggested_changes=[],
            )
        ]
        task_dict: List[Dict[str, Any]] = task.to_dict()
        # Execute - Pass task as dict
        result = await process_task_improvement(
            thread_id="thread-1",
            user=user,
            lens=Lens.TASK,
            input_data=[task_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        # Verify
        assert type(result) == AIImprovementError
        assert_that(result.error_message, contains_string("Unexpected error"))
        assert_that(result.error_type, equal_to("processing_error"))
        mock_get_key.assert_called_once_with(user.id, ANY)  # Check session is used
        mock_prompt_process.assert_called_once_with(
            api_key="dummy_api_key",
            user_auth_token="access_token",
            workspace_id=str(workspace.id),
            thread_id="thread-1",
            user_id=str(user.id),
        )
        # No need to verify internal session calls

    @patch("src.ai.ai_service.check_user_can_afford_request")
    @patch("src.ai.ai_service.get_user_api_key")
    @patch("src.ai.ai_service.TaskPrompt")
    async def test_user_doesnt_have_enough_balance_for_request(
        self,
        mockTaskPromptClass,
        mock_get_key,
        mock_check_balance,
        task,
        initiative,
        valid_user_key,
        user,
        session,
        workspace,
    ):
        """Test successful task improvement with default parameters."""
        # Setup
        mock_get_key.return_value = "dummy_api_key"
        mock_check_balance.return_value = BalanceCheckResult(
            can_proceed=False,
            balance_warning=BalanceWarning(
                warning_type="insufficient_balance",
                message="User does not have enough balance",
            ),
        )
        # Use the real session provided by the fixture

        # Mock the TaskPrompt class and its process_prompt method
        mock_prompt_instance = mockTaskPromptClass.return_value
        mock_summary = (
            "The task has been improved with a clearer title and description."
        )
        mock_managed_task = UpdateTaskModel(
            action=ManagedEntityAction.UPDATE,
            identifier=task.identifier,
            title="Improved Task Title",
            description="This is an improved description for the task.",
            checklist=[
                ChecklistItemModel(title="Step 1"),
                ChecklistItemModel(title="Step 2"),
            ],
        )
        mock_prompt_instance.process_prompt = AsyncMock(
            side_effect=lambda *args, **kwargs: TaskLLMResponse(
                message=mock_summary,
                managed_tasks=[mock_managed_task],
            )
        )

        # Prepare input data as dictionary (using the updated to_dict)
        task_dict = task.to_dict()

        # Execute
        sample_messages: List[ChatMessageInput] = [
            ChatMessageInput(
                role="user",
                content="This is the user task message",
                suggested_changes=[],
            )
        ]
        result = await process_task_improvement(
            "thread-1",
            user,
            Lens.TASK,
            [task_dict],
            mode=ChatMode.EDIT,
            messages=sample_messages,
        )

        expected_result = AIImprovementError(
            type="task",
            status="error",
            error_message="User does not have enough balance",
            error_type="insufficient_balance",
        )
        assert_that(result, equal_to(expected_result))


class TestRevalidateUserKey:
    """Test suite for revalidate_user_key function."""

    @patch("src.ai.ai_service._validate_openai_key")
    def test_revalidates_key(self, mock_validate_key, valid_user_key, user, session):
        """Test revalidation of user key."""
        # Setup
        unredacted_key = "sk-1234567890"
        mock_validate_key.return_value = False

        # Execute
        now = datetime.now()
        with freeze_time(now):
            revalidate_user_key(valid_user_key, unredacted_key, session)

        # Verify
        mock_validate_key.assert_called_once_with(unredacted_key)

        # Verify the user key was updated
        session.refresh(valid_user_key)
        assert_that(valid_user_key.is_valid, equal_to(False))
        assert_that(valid_user_key.last_validated_at, equal_to(now))

    @patch("src.ai.ai_service._validate_openai_key")
    def test_revalidates_key_success(
        self, mock_validate_key, valid_user_key, user, session
    ):
        """Test revalidation of user key when validation succeeds."""
        # Setup
        unredacted_key = "sk-1234567890"
        mock_validate_key.return_value = True

        # Execute
        now = datetime.now()
        with freeze_time(now):
            revalidate_user_key(valid_user_key, unredacted_key, session)

        # Verify
        mock_validate_key.assert_called_once_with(unredacted_key)

        session.refresh(valid_user_key)
        assert_that(valid_user_key.is_valid, equal_to(True))
        assert_that(valid_user_key.last_validated_at, equal_to(now))
