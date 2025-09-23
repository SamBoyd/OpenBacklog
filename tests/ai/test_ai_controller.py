from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import pytest
from fastapi import HTTPException
from hamcrest import assert_that, equal_to, is_

from src.ai.ai_controller import create_ai_improvement_job
from src.models import (
    AIImprovementJob,
    APIProvider,
    ChatMessage,
    ChatMode,
    Initiative,
    InitiativeType,
    JobStatus,
    Lens,
    Task,
    TaskStatus,
    TaskType,
    UserKey,
    Workspace,
)


@pytest.fixture
def valid_user_key(user, session):
    user_key = UserKey()
    user_key.user_id = user.id
    user_key.provider = APIProvider.LITELLM
    user_key.is_valid = True
    user_key.last_validated_at = datetime.now()
    user_key.redacted_key = "sk-1234567890"
    session.add(user_key)
    session.commit()
    session.refresh(user_key)
    return user_key


def test_create_ai_improvement_job_with_initiative_id(
    user, session, valid_user_key, workspace
):
    # Create a real initiative
    initiative = Initiative(
        user_id=user.id,
        workspace_id=workspace.id,
        title="Test Initiative",
        identifier="INIT-1",
        type=InitiativeType.FEATURE,
        status=TaskStatus.IN_PROGRESS,
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)

    # Create job with the initiative's ID
    test_messages_as_dict = [{"role": "user", "content": "test message"}]
    job = create_ai_improvement_job(
        user=user,
        db=session,
        messages=cast(Optional[List[ChatMessage]], test_messages_as_dict),
        lens=Lens.INITIATIVE,
        thread_id="1",
        mode=ChatMode.EDIT,
    )

    # Verify job was created correctly
    assert_that(job.lens, equal_to(Lens.INITIATIVE))
    assert_that(job.status, equal_to(JobStatus.PENDING))
    assert_that(job.input_data, equal_to([]))
    assert_that(job.messages, equal_to(test_messages_as_dict))
    # Verify job exists in DB
    db_job = session.query(AIImprovementJob).filter_by(id=job.id).first()
    assert_that(db_job, is_(job))


def test_create_ai_improvement_job_with_task_id(
    user, session, valid_user_key, workspace, test_initiative
):
    # Create a real task
    task = Task(
        user_id=user.id,
        workspace_id=workspace.id,
        title="Test Task",
        identifier="TSK-1",
        type=TaskType.CODING,
        status=TaskStatus.TO_DO,
        initiative_id=test_initiative.id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Create job with the task's ID
    job = create_ai_improvement_job(
        user=user, db=session, lens=Lens.TASK, thread_id="1", mode=ChatMode.EDIT
    )

    # Verify job was created correctly
    assert_that(job.lens, equal_to(Lens.TASK))
    assert_that(job.status, equal_to(JobStatus.PENDING))

    # Verify job exists in DB
    db_job = session.query(AIImprovementJob).filter_by(id=job.id).first()
    assert_that(db_job, is_(job))


def test_create_ai_improvement_job_with_input_data(
    user, session, valid_user_key, workspace
):
    # Create a real initiative
    initiative = Initiative(
        user_id=user.id,
        workspace_id=workspace.id,
        title="Test Initiative",
        identifier="INIT-2",
        type=InitiativeType.RESEARCH,
        status=TaskStatus.IN_PROGRESS,
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)

    # Create a job with input data - Note: input_data should be a List[Dict]
    input_data_list = [{"prompt": "Improve task description", "model": "gpt-4"}]
    job = create_ai_improvement_job(
        user=user,
        input_data=input_data_list,
        db=session,
        lens=Lens.INITIATIVE,
        thread_id="1",
        mode=ChatMode.EDIT,
    )

    # Verify input data was saved
    assert_that(job.input_data, equal_to(input_data_list))


def test_create_ai_improvement_job_requires_lens(user, session, valid_user_key):
    # Should raise TypeError when lens is not provided
    with pytest.raises(TypeError) as excinfo:
        # Explicitly pass user and db but omit lens to trigger TypeError
        # Pass None for messages explicitly to avoid ambiguity
        create_ai_improvement_job(user=user, db=session, messages=None, thread_id="1", mode=ChatMode.EDIT)  # type: ignore

    assert "required positional argument: 'lens'" in str(excinfo.value)


def test_create_ai_improvement_job_with_pending_status(
    user, session, valid_user_key, workspace, test_initiative
):
    # Create a real initiative
    initiative = Initiative(
        user_id=user.id,
        workspace_id=workspace.id,
        title="Test Initiative",
        identifier="INIT-3",
        type=InitiativeType.FEATURE,
        status=TaskStatus.IN_PROGRESS,
        has_pending_job=False,  # Explicitly set to False initially
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)

    # Create a task for the initiative
    task = Task(
        user_id=user.id,
        workspace_id=workspace.id,
        title="Test Task",
        identifier="TSK-3",
        type=TaskType.CODING,
        status=TaskStatus.TO_DO,
        initiative_id=test_initiative.id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Create job with the initiative's ID
    job = create_ai_improvement_job(
        user=user, db=session, lens=Lens.INITIATIVE, thread_id="1", mode=ChatMode.EDIT
    )

    # Verify job status is pending
    assert_that(job.status, equal_to(JobStatus.PENDING))


def test_creating_two_jobs_cancels_the_first_job(
    user, session, valid_user_key, workspace
):
    # Create a real initiative
    initiative = Initiative(
        user_id=user.id,
        workspace_id=workspace.id,
        title="Test Initiative",
        identifier="INIT-4",
        type=InitiativeType.FEATURE,
        status=TaskStatus.IN_PROGRESS,
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)

    # Create the first job
    job1 = create_ai_improvement_job(
        user=user,
        db=session,
        lens=Lens.INITIATIVE,
        messages=None,
        thread_id="1",
        mode=ChatMode.EDIT,
    )
    session.refresh(job1)

    # Create the second job
    job2 = create_ai_improvement_job(
        user=user,
        db=session,
        lens=Lens.INITIATIVE,
        messages=None,
        thread_id="1",
        mode=ChatMode.EDIT,
    )
    session.refresh(job1)
    session.refresh(job2)

    # Verify that the first job is cancelled and the second job is pending
    assert_that(job1.status, equal_to(JobStatus.CANCELED))
    assert_that(job2.status, equal_to(JobStatus.PENDING))
