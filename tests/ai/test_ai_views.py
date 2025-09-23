import uuid
from unittest.mock import ANY, MagicMock, patch

from hamcrest import assert_that, contains_string, equal_to, has_entries

from src.main import app
from src.models import (
    AIImprovementJob,
    ChatMode,
    InitiativeType,
    JobStatus,
    Lens,
    ManagedEntityAction,
    TaskStatus,
    TaskType,
    UpdateTaskModel,
)


@patch("src.ai.ai_views.ai_controller.create_ai_improvement_job")
def test_ai_improvement_post_with_valid_initiative_id(
    mock_create_job, user, test_client
):
    """Test that POST /api/ai-improvement with initiative_id creates a job"""
    # Set up mock to return a job with specified ID and status
    job_id = uuid.uuid4()
    mock_job = AIImprovementJob()
    mock_job.id = job_id
    mock_job.user = user
    mock_job.status = JobStatus.PENDING
    mock_job.lens = Lens.INITIATIVE
    mock_job.input_data = []
    mock_job.thread_id = "1"
    mock_create_job.return_value = mock_job

    # Make request with lens=INITIATIVE
    response = test_client.post(
        "/api/ai-improvement",
        json={"lens": Lens.INITIATIVE, "thread_id": "1", "mode": ChatMode.EDIT},
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(
        data,
        has_entries(
            {"job_id": equal_to(str(job_id)), "status": equal_to(JobStatus.PENDING)}
        ),
    )

    # Verify ai_controller was called with correct parameters
    mock_create_job.assert_called_once_with(
        user=user,
        lens=Lens.INITIATIVE,
        thread_id="1",
        input_data=None,
        messages=None,
        db=ANY,
        mode=ChatMode.EDIT,
    )


@patch("src.ai.ai_views.ai_controller.create_ai_improvement_job")
def test_ai_improvement_post_with_valid_task_id(mock_create_job, user, test_client):
    """Test that POST /api/ai-improvement with task lens creates a job"""
    # Set up mock
    job_id = uuid.uuid4()
    mock_job = AIImprovementJob()
    mock_job.id = job_id
    mock_job.user = user
    mock_job.status = JobStatus.PENDING
    mock_job.lens = Lens.TASK
    mock_job.input_data = []
    mock_job.thread_id = "1"
    mock_create_job.return_value = mock_job

    # Make request
    response = test_client.post(
        "/api/ai-improvement",
        json={"lens": Lens.TASK, "thread_id": "1", "mode": ChatMode.EDIT},
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(
        data,
        has_entries(
            {"job_id": equal_to(str(job_id)), "status": equal_to(JobStatus.PENDING)}
        ),
    )

    # Verify ai_controller was called with correct parameters
    mock_create_job.assert_called_once_with(
        user=user,
        lens=Lens.TASK,
        thread_id="1",
        input_data=None,
        messages=None,
        db=ANY,
        mode=ChatMode.EDIT,
    )


@patch("src.ai.ai_views.ai_controller.create_ai_improvement_job")
def test_ai_improvement_post_with_valid_task_input_data(
    mock_create_job, test_client, user
):
    """Test that POST /api/ai-improvement with task lens and valid task input data creates a job"""
    # Set up mock
    job_id = uuid.uuid4()
    mock_job = AIImprovementJob()
    mock_job.id = job_id
    mock_job.user = user
    mock_job.status = JobStatus.PENDING
    mock_job.lens = Lens.TASK
    mock_job.input_data = []
    mock_job.thread_id = "1"
    mock_create_job.return_value = mock_job

    # Create valid task input data
    task_input_data = [
        {
            "title": "Test Task",
            "description": "This is a test task",
            "status": TaskStatus.IN_PROGRESS,
            "type": TaskType.CODING,
            "checklist": [{"title": "Test Checklist Item", "is_complete": False}],
        }
    ]

    # Make request
    response = test_client.post(
        "/api/ai-improvement",
        json={
            "lens": Lens.TASK,
            "input_data": task_input_data,
            "thread_id": "1",
            "mode": ChatMode.EDIT,
        },
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(
        data,
        has_entries(
            {"job_id": equal_to(str(job_id)), "status": equal_to(JobStatus.PENDING)}
        ),
    )

    # Verify ai_controller was called with correct parameters
    mock_create_job.assert_called_once_with(
        user=user,
        lens=Lens.TASK,
        input_data=task_input_data,
        thread_id="1",
        messages=None,
        db=ANY,
        mode=ChatMode.EDIT,
    )


@patch("src.ai.ai_views.ai_controller.create_ai_improvement_job")
def test_ai_improvement_post_with_valid_initiative_input_data(
    mock_create_job, test_client, user
):
    """Test that POST /api/ai-improvement with initiative lens and valid initiative input data creates a job"""
    # Set up mock
    job_id = uuid.uuid4()
    mock_job = AIImprovementJob()
    mock_job.id = job_id
    mock_job.user = user
    mock_job.status = JobStatus.PENDING
    mock_job.lens = Lens.INITIATIVE
    mock_job.input_data = []
    mock_job.thread_id = "1"
    mock_create_job.return_value = mock_job

    # Create valid initiative input data
    initiative_input_data = [
        {
            "title": "Test Initiative",
            "description": "This is a test initiative",
            "status": TaskStatus.TO_DO,
            "type": InitiativeType.FEATURE,
        }
    ]

    # Make request
    response = test_client.post(
        "/api/ai-improvement",
        json={
            "lens": Lens.INITIATIVE,
            "input_data": initiative_input_data,
            "thread_id": "1",
            "mode": ChatMode.EDIT,
        },
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(
        data,
        has_entries(
            {"job_id": equal_to(str(job_id)), "status": equal_to(JobStatus.PENDING)}
        ),
    )

    # Verify ai_controller was called with correct parameters
    mock_create_job.assert_called_once_with(
        user=ANY,
        lens=Lens.INITIATIVE,
        input_data=initiative_input_data,
        messages=None,
        db=ANY,
        thread_id="1",
        mode=ChatMode.EDIT,
    )


def test_ai_improvement_post_with_invalid_initiative_input_data(
    test_client, test_user_key
):
    """Test that POST /api/ai-improvement with initiative lens and invalid initiative input data returns 422"""
    # Create invalid initiative input data (invalid type value)
    invalid_initiative_input_data = [
        {
            "title": "Test Initiative",
            "type": "INVALID_TYPE",  # Invalid initiative type
        }
    ]

    # Make request
    response = test_client.post(
        "/api/ai-improvement",
        json={
            "lens": Lens.INITIATIVE,
            "input_data": invalid_initiative_input_data,
            "thread_id": "1",
            "mode": ChatMode.EDIT,
        },
    )

    # Verify response indicates that the error page was rendered
    assert_that(response.status_code, equal_to(400))
    assert_that(
        response.content.decode("utf-8"), contains_string("Something went wrong")
    )


@patch("src.ai.ai_views.ai_controller.create_ai_improvement_job")
def test_ai_improvement_post_with_valid_message(mock_create_job, user, test_client):
    """Test that POST /api/ai-improvement with a valid message creates a job"""
    # Set up mock
    job_id = uuid.uuid4()
    mock_job = AIImprovementJob()
    mock_job.id = job_id
    mock_job.user = user
    mock_job.status = JobStatus.PENDING
    mock_job.lens = Lens.TASK
    mock_job.input_data = []
    mock_job.thread_id = "1"
    mock_create_job.return_value = mock_job

    # Make request with a valid messages list
    test_messages = [
        {
            "role": "user",
            "content": "Rewrite this task",
            "suggested_changes": None,
        }
    ]
    response = test_client.post(
        "/api/ai-improvement",
        json={
            "lens": Lens.TASK,
            "messages": test_messages,
            "thread_id": "1",
            "mode": ChatMode.EDIT,
        },
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(
        data,
        has_entries(
            {"job_id": equal_to(str(job_id)), "status": equal_to(JobStatus.PENDING)}
        ),
    )

    # Verify ai_controller was called with correct parameters including messages
    mock_create_job.assert_called_once_with(
        user=user,
        thread_id="1",
        lens=Lens.TASK,
        input_data=None,
        messages=test_messages,
        db=ANY,
        mode=ChatMode.EDIT,
    )


@patch("src.ai.ai_views.ai_controller.create_ai_improvement_job")
def test_ai_improvement_post_with_message_and_suggested_changes(
    mock_create_job, user, test_client
):
    """Test POST /api/ai-improvement with message including suggested_changes"""
    # Set up mock
    job_id = uuid.uuid4()
    mock_job = AIImprovementJob()
    mock_job.id = job_id
    mock_job.user = user
    mock_job.status = JobStatus.PENDING
    mock_job.lens = Lens.TASK
    mock_job.input_data = []
    mock_job.thread_id = "1"
    mock_create_job.return_value = mock_job

    # Create mock suggested changes (using ManagedTaskModel)
    suggested_task = UpdateTaskModel(
        action=ManagedEntityAction.UPDATE,
        identifier="123",
        title="Updated Task Title",
        description="Updated Task Description",
        checklist=[],
    )

    # Make request with a message containing suggested_changes
    test_messages = [
        {
            "role": "assistant",
            "content": "Here's a suggestion",
            "suggested_changes": [suggested_task.model_dump()],
        }
    ]

    response = test_client.post(
        "/api/ai-improvement",
        json={
            "lens": Lens.TASK,
            "messages": test_messages,
            "thread_id": "1",
            "mode": ChatMode.EDIT,
        },
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(
        data,
        has_entries(
            {"job_id": equal_to(str(job_id)), "status": equal_to(JobStatus.PENDING)}
        ),
    )

    # Verify ai_controller was called with correct parameters including messages with suggested_changes
    mock_create_job.assert_called_once_with(
        user=user,
        thread_id="1",
        lens=Lens.TASK,
        input_data=None,
        messages=[
            {
                "role": "assistant",
                "content": "Here's a suggestion",
                "suggested_changes": [suggested_task.model_dump()],
            }
        ],
        db=ANY,
        mode=ChatMode.EDIT,
    )


def test_ai_improvement_post_missing_lens(test_client):
    """Test that POST /api/ai-improvement without lens field returns 422"""
    # Make request without lens field
    response = test_client.post(
        "/api/ai-improvement",
        json={
            "messages": [{"role": "user", "content": "Test message"}],
            "thread_id": "1",
        },
    )

    # Verify response indicates validation error
    assert_that(response.status_code, equal_to(422))
    data = response.json()
    loc_path = data["detail"][0]["loc"]
    assert_that(str(loc_path), contains_string("lens"))


# Tests for AI endpoints that use LiteLLM


@patch("src.ai.ai_views.get_user_api_key")
@patch("src.ai.ai_views.completion")
def test_rewrite_text_success(mock_completion, mock_get_api_key, test_client, user):
    """Test successful text rewrite using LiteLLM completion"""
    # Setup mocks
    mock_get_api_key.return_value = "test_api_key"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is the rewritten text."
    mock_completion.return_value = mock_response

    # Make request
    response = test_client.post(
        "/api/rewrite",
        json={
            "text": "This is some text to rewrite",
            "existing_description": "Some existing context",
        },
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data, has_entries({"rewritten_text": "This is the rewritten text."}))

    # Verify LiteLLM was called correctly
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args
    assert_that(call_args[1]["model"], equal_to("gpt-4.1-nano"))
    assert_that(call_args[1]["api_key"], equal_to("test_api_key"))
    assert_that(len(call_args[1]["messages"]), equal_to(2))
    assert_that(call_args[1]["messages"][0]["role"], equal_to("system"))
    assert_that(call_args[1]["messages"][1]["role"], equal_to("user"))
    assert_that(
        call_args[1]["messages"][1]["content"], equal_to("This is some text to rewrite")
    )


@patch("src.ai.ai_views.get_user_api_key")
def test_rewrite_text_no_api_key(mock_get_api_key, test_client, user):
    """Test rewrite endpoint when user has no API key"""
    mock_get_api_key.return_value = None

    response = test_client.post(
        "/api/rewrite", json={"text": "Some text", "existing_description": "Context"}
    )

    assert_that(response.status_code, equal_to(400))
    data = response.json()
    assert_that(data["detail"], contains_string("User has no OpenAI API key"))


@patch("src.ai.ai_views.get_user_api_key")
@patch("src.ai.ai_views.completion")
def test_rewrite_text_litellm_error(
    mock_completion, mock_get_api_key, test_client, user
):
    """Test rewrite endpoint when LiteLLM raises an exception"""
    mock_get_api_key.return_value = "test_api_key"
    mock_completion.side_effect = Exception("LiteLLM API error")

    response = test_client.post(
        "/api/rewrite", json={"text": "Some text", "existing_description": "Context"}
    )

    assert_that(response.status_code, equal_to(500))
    data = response.json()
    assert_that(data["detail"], contains_string("Error processing rewrite request"))


@patch("src.ai.ai_views.get_user_api_key")
@patch("src.ai.ai_views.completion")
def test_text_completion_non_streaming_success(
    mock_completion, mock_get_api_key, test_client, user
):
    """Test successful non-streaming text completion using LiteLLM"""
    # Setup mocks
    mock_get_api_key.return_value = "test_api_key"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is the completed text."
    mock_completion.return_value = mock_response

    # Make request
    response = test_client.post(
        "/api/text-completion",
        json={"text": "This is a partial sentence", "stream": False},
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data, has_entries({"response": "This is the completed text."}))

    # Verify LiteLLM was called correctly
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args
    assert_that(call_args[1]["model"], equal_to("gpt-4.1-nano"))
    assert_that(call_args[1]["api_key"], equal_to("test_api_key"))
    assert_that(len(call_args[1]["messages"]), equal_to(2))


@patch("src.ai.ai_views.get_user_api_key")
@patch("src.ai.ai_views.completion")
def test_text_completion_streaming_success(
    mock_completion, mock_get_api_key, test_client, user
):
    """Test successful streaming text completion using LiteLLM"""
    # Setup mocks
    mock_get_api_key.return_value = "test_api_key"

    # Mock streaming response
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock()]
    mock_chunk1.choices[0].delta.content = "Hello"

    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock()]
    mock_chunk2.choices[0].delta.content = " world"

    mock_chunk3 = MagicMock()
    mock_chunk3.choices = [MagicMock()]
    mock_chunk3.choices[0].delta.content = None

    mock_completion.return_value = [mock_chunk1, mock_chunk2, mock_chunk3]

    # Make request
    response = test_client.post(
        "/api/text-completion",
        json={"text": "This is a partial sentence", "stream": True},
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    assert_that(response.headers["content-type"], contains_string("text/event-stream"))

    # Verify LiteLLM was called correctly
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args
    assert_that(call_args[1]["model"], equal_to("gpt-4.1-nano"))
    assert_that(call_args[1]["stream"], equal_to(True))
    assert_that(call_args[1]["api_key"], equal_to("test_api_key"))


@patch("src.ai.ai_views.get_user_api_key")
def test_text_completion_no_api_key(mock_get_api_key, test_client, user):
    """Test text completion endpoint when user has no API key"""
    mock_get_api_key.return_value = None

    response = test_client.post(
        "/api/text-completion", json={"text": "Some text", "stream": False}
    )

    assert_that(response.status_code, equal_to(400))
    data = response.json()
    assert_that(data["detail"], contains_string("User has no OpenAI API key"))


@patch("src.ai.ai_views.get_user_api_key")
@patch("src.ai.ai_views.transcription")
def test_transcribe_audio_success(
    mock_transcription, mock_get_api_key, test_client, user
):
    """Test successful audio transcription using LiteLLM"""
    # Setup mocks
    mock_get_api_key.return_value = "test_api_key"
    mock_transcription.return_value = "This is the transcribed text."

    # Create a mock file
    mock_file_content = b"fake audio content"

    # Make request
    response = test_client.post(
        "/api/transcribe",
        files={"file": ("test.webm", mock_file_content, "audio/webm")},
    )

    # Verify response
    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data, has_entries({"transcript": "This is the transcribed text."}))

    # Verify LiteLLM transcription was called correctly
    mock_transcription.assert_called_once()
    call_args = mock_transcription.call_args
    assert_that(call_args[1]["model"], equal_to("whisper-1"))
    assert_that(call_args[1]["api_key"], equal_to("test_api_key"))
    assert_that(call_args[1]["response_format"], equal_to("text"))
    assert_that(call_args[1]["language"], equal_to("en"))


@patch("src.ai.ai_views.get_user_api_key")
def test_transcribe_audio_no_api_key(mock_get_api_key, test_client, user):
    """Test transcribe endpoint when user has no API key"""
    mock_get_api_key.return_value = None

    mock_file_content = b"fake audio content"

    response = test_client.post(
        "/api/transcribe",
        files={"file": ("test.webm", mock_file_content, "audio/webm")},
    )

    assert_that(response.status_code, equal_to(400))
    data = response.json()
    assert_that(data["detail"], contains_string("User has no OpenAI API key"))
