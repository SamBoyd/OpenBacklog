"""
Tests for the background service.
"""

import datetime
import uuid
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_property, is_, is_not, none

from src.ai.ai_service import (
    InitiativeLLMResponse,  # Import the list-based response for initiatives
)
from src.ai.ai_service import (
    TaskLLMResponse,  # Import the list-based response for tasks
)
from src.ai.ai_service import AIImprovementError
from src.ai.models import ChatMessageInput
from src.background_service import (
    _call_ai_service,
    _update_entity_processing_status,
    _update_job_on_failure,
    _update_job_on_success,
    cancel_users_previous_jobs_and_get_last,
    get_next_pending_job,
    process_job,
)
from src.management.commands.process_jobs import execute
from src.models import (
    AIImprovementJob,
    ChatMessage,
    ChatMode,
    CreateTaskModel,
    Initiative,
    JobStatus,
    Lens,
    ManagedEntityAction,
    Task,
    UpdateInitiativeModel,
    UpdateTaskModel,
    User,
)


@pytest.fixture
def test_initiative(session, user, workspace):
    """Create a sample initiative for testing."""
    initiative = Initiative(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Test Initiative",
        description="Test initiative description",
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        workspace_id=workspace.id,
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)
    return initiative


@pytest.fixture
def test_task(session, test_initiative, user, workspace):
    """Create a sample task for testing."""
    task = Task(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Test Task",
        description="Test task description",
        initiative_id=test_initiative.id,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        workspace_id=workspace.id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def pending_initiative_job(session, test_initiative, test_task, user):
    """Create a sample pending job and store it in the database."""
    sample_messages: List[ChatMessage] = [
        {"role": "user", "content": "This is the user message"}
    ]
    job = AIImprovementJob(
        user_id=user.id,
        lens=Lens.INITIATIVE,
        status=JobStatus.PENDING,
        input_data=[{"id": str(test_initiative.id), "key": "value"}],
        messages=sample_messages,
        result_data=None,
        error_message=None,
        thread_id="thread-123",
        mode=ChatMode.EDIT,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def test_get_next_pending_job(session, pending_initiative_job):
    """Test retrieving the next pending job."""
    # Call the function with a real session
    job_result = get_next_pending_job(session)

    # Verify the job_result using PyHamcrest
    assert_that(job_result, is_not(none()))
    assert job_result is not None
    assert_that(job_result.id, equal_to(pending_initiative_job.id))
    assert_that(job_result.status, equal_to(JobStatus.PENDING))


def test_get_next_pending_job_none(session):
    """Test retrieving the next pending job when none exists."""
    # Make sure there are no pending jobs
    session.query(AIImprovementJob).delete()
    session.commit()

    # Call the function
    job_result = get_next_pending_job(session)

    # Verify the job_result using PyHamcrest
    assert_that(job_result, is_(none()))


@patch("src.background_service.process_initiative_improvement")
async def test_process_job_success(
    mock_process_ai, session, pending_initiative_job, user
):
    """Test processing a job successfully."""
    # Setup mock to return an InitiativeLLMResponse directly
    mock_result = InitiativeLLMResponse(
        message="Title and description were improved for clarity and effectiveness.",
        managed_initiatives=[
            UpdateInitiativeModel(
                identifier="INIT-1",
                title="Improved title",
                description="Improved description",
                tasks=[],
            )
        ],
    )
    mock_process_ai.return_value = mock_result
    # Call the function
    job_result = await process_job(pending_initiative_job, session)

    # Refresh the job from database to get updated state
    session.refresh(pending_initiative_job)

    # Verify the job_result using PyHamcrest
    assert_that(job_result, has_property("status", equal_to(JobStatus.COMPLETED)))
    # Verify the messages field was preserved
    assert_that(
        job_result.messages,
        equal_to([{"role": "user", "content": "This is the user message"}]),
    )
    assert_that(job_result, has_property("error_message", equal_to("")))
    assert_that(
        pending_initiative_job, has_property("status", equal_to(JobStatus.COMPLETED))
    )

    # Verify the mock was called correctly
    mock_process_ai.assert_called_once_with(
        thread_id="thread-123",
        user=user,
        input_data=pending_initiative_job.input_data,
        messages=[
            ChatMessageInput(
                role="user", content="This is the user message", suggested_changes=None
            )
        ],
        mode=ChatMode.EDIT,
    )


@patch("src.background_service.process_initiative_improvement")
async def test_process_job_with_valid_message(
    mock_process_ai, session, pending_initiative_job, user
):
    """Test processing a job with a valid message in the message field."""
    # Set a valid message
    pending_initiative_job.message = "This is the user message"
    session.commit()

    # Setup mock to return InitiativeLLMResponse directly
    mock_process_ai.return_value = InitiativeLLMResponse(
        message="Content improved",
        managed_initiatives=[
            UpdateInitiativeModel(
                action=ManagedEntityAction.UPDATE,
                identifier="INIT-1",
                title="Improved title",
                description="Improved description",
                tasks=[],
            )
        ],
    )

    # Call the function
    await process_job(pending_initiative_job, session)

    # Verify the message was passed correctly
    mock_process_ai.assert_called_once_with(
        thread_id="thread-123",
        user=user,
        input_data=pending_initiative_job.input_data,
        messages=[
            ChatMessageInput(
                role="user", content="This is the user message", suggested_changes=None
            )
        ],
        mode=ChatMode.EDIT,
    )


@pytest.fixture
def pending_task_job(session, test_task, user):
    """Create a sample pending job for a task and store it in the database."""
    sample_messages: List[ChatMessage] = [
        {"role": "user", "content": "This is the user task message"}
    ]
    job = AIImprovementJob(
        user_id=user.id,
        lens=Lens.TASK,
        thread_id="test_thread_id",
        status=JobStatus.PENDING,
        input_data=[{"id": str(test_task.id), "key": "value"}],
        messages=sample_messages,
        result_data=None,  # Explicitly None
        error_message=None,  # Explicitly None
        mode=ChatMode.EDIT,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@patch("src.background_service.process_initiative_improvement")
async def test_process_job_failure(
    mock_process_ai, session, pending_initiative_job, user
):
    """Test processing a job that fails."""
    pending_initiative_job.message = None

    # Setup mock to return an AIImprovementError directly
    mock_process_ai.return_value = AIImprovementError(
        type="initiative",
        error_message="Test error",
    )

    # Call the function
    job_result = await process_job(pending_initiative_job, session)

    # Refresh the job from database to get updated state
    session.refresh(pending_initiative_job)

    # Verify the job_result using PyHamcrest
    assert_that(job_result, has_property("status", equal_to(JobStatus.FAILED)))
    # Expect the error message from the mocked AIImprovementError
    assert_that(job_result, has_property("error_message", equal_to("Test error")))
    assert_that(
        pending_initiative_job, has_property("status", equal_to(JobStatus.FAILED))
    )
    # Verify the AI process function *was* called
    mock_process_ai.assert_called_once_with(
        thread_id="thread-123",
        user=user,
        input_data=pending_initiative_job.input_data,
        messages=[
            ChatMessageInput(
                role="user", content="This is the user message", suggested_changes=None
            )
        ],
        mode=ChatMode.EDIT,
    )


# --- Tests for Helper Functions ---


class TestUpdateEntityProcessingStatus:
    """Tests for the _update_entity_processing_status helper function."""

    @patch("src.background_service.update")
    @patch("src.background_service.Initiative")
    @patch("src.background_service.Task")
    def test_update_initiative_status(
        self, mock_task, mock_initiative, mock_update, session
    ):
        """Test updating status for an initiative."""
        mock_db_execute = MagicMock()
        session.execute = mock_db_execute
        entity_ids = [uuid.uuid4()]

        _update_entity_processing_status(session, Lens.INITIATIVE, entity_ids, True)

        mock_update.assert_called_once_with(mock_initiative)
        update_instance = mock_update.return_value
        update_instance.where.assert_called_once_with(
            mock_initiative.id == entity_ids[0]
        )
        where_instance = update_instance.where.return_value
        where_instance.values.assert_called_once_with(has_pending_job=True)
        session.execute.assert_called_once_with(where_instance.values.return_value)

    @patch("src.background_service.update")
    @patch("src.background_service.Initiative")
    @patch("src.background_service.Task")
    def test_update_task_status(self, mock_task, mock_initiative, mock_update, session):
        """Test updating status for a task."""
        mock_db_execute = MagicMock()
        session.execute = mock_db_execute
        entity_ids = [uuid.uuid4()]

        _update_entity_processing_status(session, Lens.TASK, entity_ids, False)

        mock_update.assert_called_once_with(mock_task)
        update_instance = mock_update.return_value
        update_instance.where.assert_called_once_with(mock_task.id == entity_ids[0])
        where_instance = update_instance.where.return_value
        where_instance.values.assert_called_once_with(has_pending_job=False)
        session.execute.assert_called_once_with(where_instance.values.return_value)


class TestCallAiService:
    """Tests for the _call_ai_service helper function."""

    @patch("src.background_service.process_initiative_improvement")
    @patch("src.background_service.process_task_improvement")
    async def test_call_initiative_service(
        self, mock_process_task, mock_process_initiative
    ):
        """Test calling the initiative improvement service."""
        mock_user = MagicMock(spec=User)
        mock_user.id = uuid.uuid4()
        input_data = [{"id": str(uuid.uuid4()), "context": "test"}]
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": "This is the user message"}
        ]
        mock_result = InitiativeLLMResponse(
            message="Test initiative summary",
            managed_initiatives=[
                UpdateInitiativeModel(
                    identifier="INIT-1",
                    title="New Title",
                    description="New Desc",
                    tasks=[],
                )
            ],
        )
        mock_process_initiative.return_value = mock_result

        result = await _call_ai_service(
            thread_id="thread-1",
            user=mock_user,
            lens=Lens.INITIATIVE,
            input_data=input_data,
            messages=messages,
            mode=ChatMode.EDIT,
        )

        mock_process_initiative.assert_called_once_with(
            thread_id="thread-1",
            user=mock_user,
            input_data=input_data,
            messages=[
                ChatMessageInput(
                    role="user",
                    content="This is the user message",
                    suggested_changes=None,
                )
            ],
            mode=ChatMode.EDIT,
        )
        mock_process_task.assert_not_called()
        assert_that(result, equal_to(mock_result))

    @patch("src.background_service.process_initiative_improvement")
    @patch("src.background_service.process_task_improvement")
    async def test_call_task_service(self, mock_process_task, mock_process_initiative):
        """Test calling the task improvement service."""
        mock_user = MagicMock(spec=User)
        mock_user.id = uuid.uuid4()
        input_data = [{"id": str(uuid.uuid4())}]
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": "Break down the task into smaller tasks."}
        ]
        mock_result = TaskLLMResponse(
            message="Test task summary",
            managed_tasks=[
                UpdateTaskModel(
                    identifier="TASK-1",
                    title="New Task Title",
                    description="New task description",
                    checklist=[],
                )
            ],
        )
        mock_process_task.return_value = mock_result

        result = await _call_ai_service(
            thread_id="thread-1",
            user=mock_user,
            lens=Lens.TASK,
            input_data=input_data,
            messages=messages,
            mode=ChatMode.EDIT,
        )  # type: ignore

        mock_process_task.assert_called_once_with(
            thread_id="thread-1",
            user=mock_user,
            lens=Lens.TASK,
            input_data=input_data,
            messages=[
                ChatMessageInput(
                    role="user",
                    content="Break down the task into smaller tasks.",
                    suggested_changes=None,
                )
            ],
            mode=ChatMode.EDIT,
        )
        mock_process_initiative.assert_not_called()
        assert_that(result, equal_to(mock_result))


class TestUpdateJobOnSuccess:
    """Tests for the _update_job_on_success helper function."""

    def test_update_initiative_success(self, pending_initiative_job):
        """Test updating job state on successful initiative improvement."""
        job = pending_initiative_job
        job.status = JobStatus.PROCESSING  # Start state
        result_obj = InitiativeLLMResponse(
            message="Changes were made.",
            managed_initiatives=[
                UpdateInitiativeModel(
                    action=ManagedEntityAction.UPDATE,
                    identifier="INIT-1",
                    title="New Title",
                    description="New Desc",
                    tasks=[],
                )
            ],
        )

        _update_job_on_success(job, result_obj)

        assert_that(job.status, equal_to(JobStatus.COMPLETED))
        assert_that(
            job.result_data, equal_to(result_obj.model_dump())
        )  # Use model_dump()
        assert_that(
            job.messages,
            equal_to([{"role": "user", "content": "This is the user message"}]),
        )  # Check messages
        assert_that(job.error_message, is_(""))
        assert_that(job.updated_at, is_not(none()))  # Should be set

    def test_update_task_success(self, pending_task_job):
        """Test updating job state on successful task improvement."""
        job = pending_task_job
        job.status = JobStatus.PROCESSING  # Start state
        result_obj = TaskLLMResponse(
            message="Task broken down.",
            managed_tasks=[
                CreateTaskModel(
                    title="Subtask 1", description="Subtask 1 description", checklist=[]
                )
            ],
        )

        _update_job_on_success(job, result_obj)

        assert_that(job.status, equal_to(JobStatus.COMPLETED))
        assert_that(
            job.result_data, equal_to(result_obj.model_dump())
        )  # Use model_dump()
        assert_that(
            job.messages,
            equal_to([{"role": "user", "content": "This is the user task message"}]),
        )  # Check messages
        assert_that(job.error_message, is_(""))
        assert_that(job.updated_at, is_not(none()))


class TestUpdateJobOnFailure:
    """Tests for the _update_job_on_failure helper function."""

    def test_update_failure_with_error_object(self, pending_initiative_job):
        """Test updating job state with an AIImprovementError object."""
        job = pending_initiative_job
        job.status = JobStatus.PROCESSING  # Start state

        error_result = AIImprovementError(
            type="initiative",
            error_message="Something went wrong.",
            error_type="test_error",
        )

        _update_job_on_failure(job, error_result)

        assert_that(job.status, equal_to(JobStatus.FAILED))
        assert_that(job.error_message, equal_to("Something went wrong."))
        assert_that(job.updated_at, is_not(none()))

    def test_update_failure_with_api_error(self, pending_task_job):
        """Test updating job state with an API error."""
        job = pending_task_job
        job.status = JobStatus.PROCESSING  # Start state

        error_result = AIImprovementError(
            type="task", error_message="AI API Error", error_type="llm_api_error"
        )

        _update_job_on_failure(job, error_result)

        assert_that(job.status, equal_to(JobStatus.FAILED))
        assert_that(job.error_message, equal_to("AI API Error"))
        assert_that(job.updated_at, is_not(none()))


# --- End Tests for Helper Functions ---


@patch("src.management.commands.process_jobs.get_next_pending_job")
@patch("src.management.commands.process_jobs.process_job")
@patch("src.management.commands.process_jobs.get_db")
async def test_process_jobs_command_with_job(
    mock_get_db, mock_process_job, mock_get_next_job, session, pending_initiative_job
):
    """Test running the job processor command when a job exists."""
    # Setup mocks
    mock_get_db.return_value.__next__.return_value = session
    mock_get_next_job.return_value = pending_initiative_job

    # Mock time.sleep to avoid actual waiting
    with patch("time.sleep"):
        # Call the command with single_run=True to avoid infinite loop
        job_result = await execute(interval=1, single_run=True)

    # Verify the job_result using appropriate assertions
    assert_that(job_result, equal_to(0))  # Successful exit code
    mock_get_next_job.assert_called_once_with(session)
    mock_process_job.assert_called_once_with(pending_initiative_job, session)


@patch("src.management.commands.process_jobs.get_next_pending_job")
@patch("src.management.commands.process_jobs.process_job")
@patch("src.management.commands.process_jobs.get_db")
async def test_process_jobs_command_no_job(
    mock_get_db, mock_process_job, mock_get_next_job, session
):
    """Test running the job processor command when no job exists."""
    # Setup mocks
    mock_get_db.return_value.__next__.return_value = session
    mock_get_next_job.return_value = None

    # Mock time.sleep to avoid actual waiting
    with patch("time.sleep"):
        # Call the command with single_run=True to avoid infinite loop
        job_result = await execute(interval=1, single_run=True)

    # Verify the job_result using appropriate assertions
    assert_that(job_result, equal_to(0))  # Successful exit code
    mock_get_next_job.assert_called_once_with(session)
    # The process_job should not be called when there's no job
    mock_process_job.assert_not_called()


@patch("src.management.commands.process_jobs.get_next_pending_job")
@patch("src.management.commands.process_jobs.get_db")
async def test_process_jobs_command_exception(mock_get_db, mock_get_next_job, session):
    """Test running the job processor command when an exception occurs."""
    # Setup mocks
    mock_get_db.return_value.__next__.return_value = session
    mock_get_next_job.side_effect = Exception("Test error")

    # Mock time.sleep to avoid actual waiting
    with patch("time.sleep"):
        # Call the command with single_run=True to avoid infinite loop
        job_result = await execute(interval=1, single_run=True)

    # Verify the job_result using appropriate assertions
    assert_that(job_result, equal_to(0))  # Should still exit with success
    mock_get_next_job.assert_called_once_with(session)


def test_get_help():
    """Test that the command's help text is available."""
    from src.management.commands.process_jobs import get_help

    help_text = get_help()
    assert_that(help_text, is_not(none()))
    assert_that(isinstance(help_text, str), is_(True))


@pytest.mark.skip
def test_rollsback_transaction_if_the_job_fails():
    assert_that(False, is_(True))


@pytest.mark.skip
def test_records_the_number_of_times_the_job_has_been_attempted():
    assert_that(False, is_(True))


def test_deletes_previous_jobs_if_they_are_pending(session, user):
    """Test that previous jobs are canceled if they are pending."""
    # Setup mocks
    user_id = user.id

    previous_completed_jobs = [
        AIImprovementJob(
            user_id=user_id,
            thread_id="thread-1",
            id=uuid.uuid4(),
            status=JobStatus.COMPLETED,
            lens=Lens.INITIATIVE,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        for _ in range(3)
    ]
    session.add_all(previous_completed_jobs)

    previous_failed_jobs = [
        AIImprovementJob(
            user_id=user_id,
            thread_id="thread-1",
            id=uuid.uuid4(),
            status=JobStatus.FAILED,
            lens=Lens.INITIATIVE,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        for _ in range(3)
    ]
    session.add_all(previous_failed_jobs)

    previous_jobs = [
        AIImprovementJob(
            user_id=user_id,
            id=uuid.uuid4(),
            thread_id="thread-1",
            status=JobStatus.PENDING,
            lens=Lens.INITIATIVE,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        for _ in range(3)
    ]

    # Create a job with PENDING status
    last_job = AIImprovementJob(
        user_id=user_id,
        id=uuid.uuid4(),
        thread_id="thread-1",
        status=JobStatus.PENDING,
        lens=Lens.INITIATIVE,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    session.add_all(previous_jobs)
    session.add(last_job)
    session.commit()

    # Call the command with single_run=True to avoid infinite loop
    result = cancel_users_previous_jobs_and_get_last(session, user_id)

    # Verify that the previous jobs were deleted
    all_jobs = session.query(AIImprovementJob).filter_by(user_id=user_id).all()
    assert_that(len(all_jobs), equal_to(1))  # 3 completed + 3 failed + 1 pending
    assert_that(result, equal_to(last_job))
    assert_that(all_jobs[0], equal_to(last_job))
