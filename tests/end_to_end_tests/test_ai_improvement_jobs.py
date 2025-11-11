import os
import uuid
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

# Add hamcrest imports
from hamcrest import (
    assert_that,
    equal_to,
    greater_than,
    has_entries,
    has_item,
    has_length,
    instance_of,
    is_,
    not_,
)
from sqlalchemy.orm import Session

from src.ai.prompt import TaskLLMResponse

# Assuming your project structure allows these imports
from src.background_service import process_job

# Use session fixture from conftest
# from src.db import SessionLocal # No longer needed here
from src.models import Lens  # Model needed for type hint
from src.models import User  # Model needed for type hint
from src.models import UserKey  # Model needed for type hint
from src.models import Workspace  # Model needed for type hint
from src.models import (
    AIImprovementJob,
    APIProvider,
    CreateTaskModel,
    DeleteTaskModel,
    Initiative,
    InitiativeLLMResponse,
    JobStatus,
    Task,
    UpdateTaskModel,
)

# --- Test Class ---


@pytest.mark.end2end  # Mark as end-to-end test
class TestInitiativeImprovementsE2E:
    @patch("src.secrets.vault_factory.get_vault")  # Patch where it's used
    def test_process_initiative_improvement_job_e2e(
        self,
        mock_get_vault,
        # Use fixtures from conftest.py
        session: Session,
        user: User,
        test_initiative: Initiative,  # Use the new fixture from conftest
        test_task: Task,
        openai_api_key: str,  # Use the fixture from conftest
        test_user_key: UserKey,  # Use the fixture from conftest
    ):
        """
        Tests processing an initiative improvement job end-to-end using a real OpenAI API key.
        Relies on fixtures defined in conftest.py.
        """
        # Arrange
        # Configure the mock to return the real API key when called for this user/provider
        expected_vault_path = (
            f"secret/data/{user.id}/api_keys/{APIProvider.OPENAI.value}"
        )
        mock_vault = MagicMock()
        mock_vault.retrieve_api_key_from_vault.side_effect = lambda vault_path: (
            openai_api_key if vault_path == expected_vault_path else None
        )
        mock_get_vault.return_value = mock_vault

        test_tasks: List[Task] = [
            Task(
                title="Test Task 1",
                description="This is the initial description for E2E testing.",
                user_id=user.id,
                initiative_id=test_initiative.id,
                workspace_id=test_initiative.workspace_id,
            ),
            Task(
                title="Test Task 2",
                description="This is the initial description for E2E testing.",
                user_id=user.id,
                initiative_id=test_initiative.id,
                workspace_id=test_initiative.workspace_id,
            ),
        ]
        session.add_all(test_tasks)
        session.commit()

        # Create the AI Improvement Job
        job = AIImprovementJob(
            user_id=user.id,  # Use the user fixture
            lens=Lens.INITIATIVES,
            status=JobStatus.PENDING,
            messages=[
                dict(
                    role="user",
                    content="Update the initiative title and description to be more descriptive and helpful",
                )
            ],
            input_data=[
                {
                    "id": str(test_initiative.id),
                    "identifier": test_initiative.identifier,
                    "user_id": str(user.id),
                    "title": test_initiative.title,
                    "description": test_initiative.description,
                    "workspace": str(test_initiative.workspace_id),
                    "created_at": test_initiative.created_at.isoformat(),
                    "updated_at": test_initiative.updated_at.isoformat(),
                    "tasks": [
                        {
                            "id": str(test_initiative.tasks[0].id),
                            "identifier": test_initiative.tasks[0].identifier,
                            "title": test_initiative.tasks[0].title,
                            "description": test_initiative.tasks[0].description,
                            "workspace": str(test_initiative.tasks[0].workspace_id),
                            "created_at": test_initiative.tasks[
                                0
                            ].created_at.isoformat(),
                            "updated_at": test_initiative.tasks[
                                0
                            ].updated_at.isoformat(),
                        }
                    ],
                }
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        # Act
        # Process the job using the background service logic
        updated_job = process_job(job, session)  # Pass the session fixture
        session.refresh(updated_job)  # Refresh state from DB after processing

        # Assert
        # Check mock was called correctly
        mock_retrieve_key.assert_called_once_with(expected_vault_path)

        # Check result_data structure and content using hamcrest
        result_data = updated_job.result_data
        assert_that(result_data, is_(instance_of(dict)))
        assert_that(result_data.keys(), has_length(2))

        # Check the result data can be parsed into a TaskLLMResponse
        initiative_llm_response = InitiativeLLMResponse(**result_data)
        assert_that(initiative_llm_response, is_(instance_of(InitiativeLLMResponse)))

        managed_initiatives = result_data.get("managed_initiatives", [])
        assert_that(managed_initiatives, has_length(1))
        assert_that(
            managed_initiatives[0],
            has_entries(
                {
                    "identifier": equal_to(test_initiative.identifier),
                }
            ),
        )

        managed_tasks = managed_initiatives[0].get("tasks", [])
        assert_that(managed_tasks, has_length(1))
        assert_that(
            managed_tasks[0],
            has_entries(
                {
                    "identifier": equal_to(test_initiative.tasks[0].identifier),
                }
            ),
        )

        # Verify the title/description are different from the original
        assert_that(
            managed_initiatives[0].get("title"),
            is_(not_(equal_to(test_initiative.title))),
        )
        assert_that(
            managed_initiatives[0].get("description"),
            is_(not_(equal_to(test_initiative.description))),
        )

        # Check that the summary of changes was populated in the message field
        assert_that(updated_job.message, is_("This is a test message"))


@pytest.mark.end2end  # Mark as end-to-end test
class TestTaskImprovementsE2E:
    @patch("src.secrets.vault_factory.get_vault")
    def test_create_new_task(
        self,
        mock_get_vault,
        session: Session,
        user: User,
        test_task: Task,
        openai_api_key: str,
        test_user_key: UserKey,
    ):
        """Tests processing a task management job that splits a task into two tasks."""
        expected_vault_path = (
            f"secret/data/{user.id}/api_keys/{APIProvider.OPENAI.value}"
        )
        mock_vault = MagicMock()
        mock_vault.retrieve_api_key_from_vault.side_effect = lambda vault_path: (
            openai_api_key if vault_path == expected_vault_path else None
        )
        mock_get_vault.return_value = mock_vault

        from src.ai.prompt import ManagedEntityAction, ManagedTaskModel, TaskLLMResponse

        fake_response = TaskLLMResponse(
            message="Split the task into two smaller tasks",
            managed_tasks=[
                UpdateTaskModel(
                    action=ManagedEntityAction.UPDATE,
                    identifier=test_task.identifier,
                    title="Original task updated",
                    description="First part of task",
                    checklist=[{"title": "Step 1", "is_complete": False}],
                ),
                CreateTaskModel(
                    action=ManagedEntityAction.CREATE,
                    title="New split task",
                    description="Second part from task split",
                    checklist=[{"title": "Step 2", "is_complete": False}],
                ),
            ],
        )
        # mock_call_llm_api.return_value = fake_response

        job = AIImprovementJob(
            user_id=user.id,
            lens=Lens.TASK,
            status=JobStatus.PENDING,
            messages=[dict(role="user", content="This is a test message")],
            input_data={"context": "Split this task into two smaller tasks."},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        updated_job = process_job(job, session)
        session.refresh(updated_job)

        mock_retrieve_key.assert_called_once_with(expected_vault_path)
        # mock_call_llm_api.assert_called_once()

        result_data = updated_job.result_data
        task_llm_response = TaskLLMResponse(**result_data)
        assert_that(task_llm_response, is_(instance_of(TaskLLMResponse)))

        managed_tasks = task_llm_response.managed_tasks
        assert_that(managed_tasks, has_length(2))
        assert_that(
            managed_tasks[0],
            has_entries(
                {
                    "action": equal_to("UPDATE"),
                    "identifier": equal_to(test_task.identifier),
                }
            ),
        )
        assert_that(
            managed_tasks[1],
            has_entries(
                {"action": equal_to("CREATE"), "title": equal_to("New split task")}
            ),
        )
        assert_that(updated_job.status, equal_to(JobStatus.COMPLETED))
        assert_that(updated_job.message, equal_to("This is a test message"))

    @patch("src.ai.prompt.call_llm_api")
    @patch("src.secrets.vault_factory.get_vault")
    def test_delete_task(
        self,
        mock_get_vault,
        mock_call_llm,
        session: Session,
        user: User,
        test_task: Task,
        openai_api_key: str,
        test_user_key: UserKey,
    ):
        """Tests processing a task management job that deletes a task."""
        expected_vault_path = (
            f"secret/data/{user.id}/api_keys/{APIProvider.OPENAI.value}"
        )
        mock_vault = MagicMock()
        mock_vault.retrieve_api_key_from_vault.side_effect = lambda vault_path: (
            openai_api_key if vault_path == expected_vault_path else None
        )
        mock_get_vault.return_value = mock_vault

        from src.ai.prompt import ManagedEntityAction, ManagedTaskModel, TaskLLMResponse

        fake_response = TaskLLMResponse(
            message="Deleted the specified task as it is redundant.",
            managed_tasks=[
                DeleteTaskModel(
                    action=ManagedEntityAction.DELETE,
                    identifier=test_task.identifier,
                )
            ],
        )

        # Create the job requesting deletion (using input_data for intent)
        job = AIImprovementJob(
            user_id=user.id,
            lens=Lens.TASK,
            status=JobStatus.PENDING,
            # Using a generic operation, intent is in input_data or derived by LLM
            message="This is a test message",
            input_data={
                #  TODO: Add the task entity
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        # Act
        updated_job = process_job(job, session)
        session.refresh(updated_job)

        # Assert
        mock_retrieve_key.assert_called_once_with(expected_vault_path)

        # Check job status and message
        assert_that(updated_job.status, equal_to(JobStatus.COMPLETED))
        assert_that(updated_job.message, equal_to("This is a test message"))

        # Check result data reflects the delete action
        result_data = updated_job.result_data
        assert_that(result_data, is_(instance_of(dict)))
        assert_that(
            result_data,
            has_entries(
                {
                    "message": equal_to(
                        "Deleted the specified task as it is redundant."
                    ),
                    "managed_tasks": is_(instance_of(list)),
                }
            ),
        )
        managed_tasks = result_data.get("managed_tasks", [])
        assert_that(managed_tasks, has_length(1))
        assert_that(
            managed_tasks[0],
            has_entries(
                {
                    "action": equal_to("DELETE"),
                    "identifier": equal_to(test_task.identifier),
                }
            ),
        )
