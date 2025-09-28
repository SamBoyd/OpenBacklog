"""
Background service for processing AI improvement jobs.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload  # Added selectinload

from src.accounting.billing_service import BillingService
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    set_job_context,
    set_user_context,
    track_ai_metrics,
)
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.ai.ai_service import (
    AIImprovementError,
    InitiativeLLMResponse,
    TaskLLMResponse,
    VaultError,
    process_initiative_improvement,
    process_task_improvement,
)
from src.ai.models import ChatMessageInput, DiscussResponseModel
from src.main import app
from src.models import (
    AIImprovementJob,
    ChatMode,
    Initiative,
    JobStatus,
    Lens,
    Task,
    User,
)

logger = logging.getLogger(__name__)

# logger.setLevel(logging.DEBUG)


# --- Helper Functions for process_job ---
def _update_entity_processing_status(
    db: Session, lens: Lens, entity_ids: List[UUID], status: bool
) -> None:
    """
    Updates the 'has_pending_job' status for the given entity.

    Args:
        db (Session): Database session.
        entity_type (str): 'initiative' or 'task'.
        entity_id (UUID): The ID of the entity.
        status (bool): The new status for has_pending_job (True or False).
    """
    EntityModel = (
        Initiative if (lens == Lens.INITIATIVE or lens == Lens.INITIATIVES) else Task
    )
    for entity_id in entity_ids:
        db.execute(
            update(EntityModel)
            .where(EntityModel.id == entity_id)
            .values(has_pending_job=status)
        )


async def _call_ai_service(
    thread_id: str,
    user: User,
    lens: Lens,
    input_data: List[Dict[str, Any]],
    mode: ChatMode,
    messages: Optional[List[Dict[Any, Any]]] = None,
) -> Union[
    DiscussResponseModel, InitiativeLLMResponse, TaskLLMResponse, AIImprovementError
]:
    """
    Calls the appropriate AI service function based on the entity type.

    Args:
        user (User): The user object.
        lens (Lens): The lens indicating the target entity type.
        input_data (List[Dict[str, Any]]): Input data for the AI service.
        messages (Optional[List[ChatMessage]]): Conversation messages.

    Returns:
        Union[InitiativeLLMResponse, TaskLLMResponse, AIImprovementError]:
            A single object containing the result (success or error).
    """

    # Convert messages to ChatMessageInput if needed
    messages_inputs = (
        [ChatMessageInput(**msg) for msg in messages] if messages else None
    )

    if lens == Lens.INITIATIVE or lens == Lens.INITIATIVES:
        return await process_initiative_improvement(
            thread_id=thread_id,
            user=user,
            input_data=input_data,
            messages=messages_inputs,
            mode=mode,
        )
    else:
        return await process_task_improvement(
            thread_id=thread_id,
            user=user,
            lens=lens,
            input_data=input_data,
            messages=messages_inputs,
            mode=mode,
        )


def _update_job_on_success(
    job: AIImprovementJob,
    result_object: Union[InitiativeLLMResponse, TaskLLMResponse, DiscussResponseModel],
) -> None:
    """
    Updates the job record upon successful AI processing.

    Args:
        job (AIImprovementJob): The job to update.
        result_object (Union[InitiativeLLMResponse, TaskLLMResponse, DiscussResponseModel]): The successful result from the AI service.
    """
    job.status = JobStatus.COMPLETED
    job.result_data = result_object.model_dump()  # Use model_dump()
    # Set empty string instead of None to avoid SQLAlchemy error
    job.error_message = "" if job.error_message is None else job.error_message
    job.updated_at = datetime.now()


def _update_job_on_failure(
    job: AIImprovementJob,
    error_result: AIImprovementError,  # Expect the error model directly
    # error_message: str, # Removed
    # error_type: Optional[str] = None, # Removed
    # result_data: Optional[Dict[str, Any]] = None, # Removed
) -> None:
    """
    Updates the job record upon failed AI processing or other errors.

    Args:
        job (AIImprovementJob): The job to update.
        error_result (AIImprovementError): The error result object from the AI service.
    """
    job.status = JobStatus.FAILED
    job.error_message = (
        error_result.error_message or "An error occurred. Please try again"
    )  # Ensure not None
    # Optionally store error type if a field exists on the job model
    # job.error_type = error_result.error_type
    job.updated_at = datetime.now()


# --- Main Processing Function ---


def get_next_pending_job(db: Session) -> Optional[AIImprovementJob]:
    """
    Retrieves the oldest pending AI improvement job.

    Args:
        db (Session): Database session

    Returns:
        Optional[AIImprovementJob]: The oldest pending job or None if no pending jobs
    """
    query = (
        select(AIImprovementJob)
        .where(AIImprovementJob.status == JobStatus.PENDING)
        .order_by(AIImprovementJob.created_at)
        .limit(1)
        # Optional: Eager load user for logging
        .options(selectinload(AIImprovementJob.user))
    )
    result = db.execute(query).scalars().first()
    return result


def check_free_usage(
    account_details: UserAccountDetails,
) -> Optional[AIImprovementError]:
    # Record free prompt usage
    if (
        account_details.status == UserAccountStatus.NEW
        and account_details.free_prompts_limit == account_details.free_prompts_used
    ):
        return AIImprovementError(
            error_message="You have 0 free prompts remaining", type="initiative"
        )


async def process_job(job: AIImprovementJob, db: Session) -> AIImprovementJob:
    """
    Processes an AI improvement job by calling the AI service and updating the job status.

    Orchestrates the job processing by calling helper functions.

    Args:
        job (AIImprovementJob): The job to process.
        db (Session): Database session.

    Returns:
        AIImprovementJob: The updated job.
    """
    # Set up Sentry context for this job
    set_job_context(job)

    # Track job processing metrics
    track_ai_metrics(
        "ai_job.started",
        1,
        tags={
            "job_lens": job.lens.value if job.lens else "unknown",
            "job_mode": job.mode.value if job.mode else "unknown",
        },
    )

    # 1. Determine input Entity ids
    entity_ids = [entity["id"] for entity in job.input_data]

    add_breadcrumb(
        f"Processing job {job.id} with {len(entity_ids)} entities",
        category="ai.job",
        data={
            "entity_count": len(entity_ids),
            "lens": job.lens.value if job.lens else None,
        },
    )

    try:
        # 2. Mark Entity as Processing
        add_breadcrumb("Marking entities as processing", category="ai.job")
        _update_entity_processing_status(db, job.lens, entity_ids, True)
        db.commit()  # Commit entity status update

        # 3. Mark Job as Processing
        add_breadcrumb("Updating job status to PROCESSING", category="ai.job")
        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.now()
        db.commit()  # Commit job status update
        logger.info(f"Job {job.id} marked as PROCESSING")

        # 4. Get the messages from the job
        messages = job.messages
        logger.info(f"Job {job.id} messages: {messages or 'None'}")
        add_breadcrumb(
            f"Job has {len(messages) if messages else 0} messages",
            category="ai.job",
            data={"message_count": len(messages) if messages else 0},
        )

        # 5. Check the user is loaded
        logger.info(f"Calling AI service for job {job.id}...")
        add_breadcrumb("Validating user context", category="ai.job")

        # Ensure user is loaded (should be loaded by get_next_pending_job)
        if not job.user:
            # Handle case where user is not loaded - this shouldn't happen
            # if get_next_pending_job uses selectinload correctly.
            # You might want to fetch the user explicitly here if needed.
            logger.exception(
                f"User object not loaded for job {job.id}. Fetching user {job.user_id}..."
            )
            add_breadcrumb(
                "User not loaded, fetching explicitly",
                category="ai.job",
                level="warning",
            )

            from src.models import User  # Local import if needed

            user = db.get(User, job.user_id)
            if not user:
                error_msg = f"User with ID {job.user_id} not found for job {job.id}"
                add_breadcrumb(
                    "User not found in database", category="ai.job", level="error"
                )
                raise ValueError(error_msg)
            job.user = user  # Assign the loaded user back if necessary

        # Set user context now that we have the user
        set_user_context(job.user)

        # 6. Check for a free user usage
        add_breadcrumb("Checking user account details", category="ai.job")
        account_details: UserAccountDetails = (
            db.query(UserAccountDetails)
            .filter(UserAccountDetails.user_id == job.user.id)
            .first()
        )
        if not account_details:
            error_msg = f"No account details found for user: {job.user.id}"
            add_breadcrumb(
                "Account details not found", category="ai.job", level="error"
            )
            raise Exception(error_msg)

        # Call returns a single result object now
        add_breadcrumb("Calling AI service", category="ai.job")
        ai_service_start_time = datetime.now()

        result_object = await _call_ai_service(
            thread_id=job.thread_id,
            user=job.user,  # Pass the loaded user object
            lens=job.lens,
            input_data=job.input_data,
            messages=messages,
            mode=job.mode,
        )

        ai_service_duration = (
            datetime.now() - ai_service_start_time
        ).total_seconds() * 1000
        track_ai_metrics(
            "ai_service.duration_ms",
            ai_service_duration,
            tags={
                "job_lens": job.lens.value if job.lens else "unknown",
                "success": "unknown",  # Will be updated below
            },
        )

        logger.info(f"AI service call completed for job {job.id}")
        add_breadcrumb(
            f"AI service completed in {ai_service_duration:.2f}ms",
            category="ai.job",
            data={"duration_ms": ai_service_duration},
        )

        # 7. Handle AI Service Result (Check type of the single result)
        if isinstance(result_object, AIImprovementError):
            logger.warning(
                f"Job {job.id} failed in AI service: {result_object.error_message}"
            )
            add_breadcrumb(
                "AI service returned error",
                category="ai.job",
                level="warning",
                data={
                    "error_type": result_object.error_type,
                    "error_message": result_object.error_message,
                },
            )

            track_ai_metrics(
                "ai_job.failed",
                1,
                tags={
                    "job_lens": job.lens.value if job.lens else "unknown",
                    "error_type": result_object.error_type or "unknown",
                },
            )

            # Pass the error object directly
            _update_job_on_failure(job, result_object)
        elif isinstance(
            result_object,
            (InitiativeLLMResponse, TaskLLMResponse, DiscussResponseModel),
        ):
            logger.info(f"Job {job.id} completed successfully by AI service.")
            add_breadcrumb("AI service completed successfully", category="ai.job")

            track_ai_metrics(
                "ai_job.completed",
                1,
                tags={"job_lens": job.lens.value if job.lens else "unknown"},
            )

            # Record free prompt usage for free tier users
            billing_service = BillingService(db)
            if account_details.status == UserAccountStatus.NEW:
                # Record free prompt usage
                # Note: For paid users, usage tracking is handled by the existing usage_tracker.py service
                add_breadcrumb("Recording free prompt usage", category="ai.job")
                billing_service.record_free_prompt_usage(job.user)
                logger.info(f"Recorded free prompt usage for user {job.user.id}")

            # Pass the success object directly
            _update_job_on_success(job, result_object)
        else:
            # Should not happen if _call_ai_service is correct
            err_msg = f"Internal error: Unexpected result type {type(result_object)} from _call_ai_service"
            logger.exception(f"Job {job.id}: {err_msg}")
            add_breadcrumb(
                "Unexpected result type from AI service",
                category="ai.job",
                level="error",
                data={"result_type": str(type(result_object))},
            )

            track_ai_metrics(
                "ai_job.internal_error",
                1,
                tags={
                    "job_lens": job.lens.value if job.lens else "unknown",
                    "error_type": "unexpected_result_type",
                },
            )

            # Create an ad-hoc error object or handle differently
            error_obj = AIImprovementError(
                type=(
                    "initiative"
                    if job.lens == Lens.INITIATIVE or job.lens == Lens.INITIATIVES
                    else "task"
                ),
                error_message=err_msg,
                error_type="internal_processing_error",
            )
            _update_job_on_failure(job, error_obj)

    except VaultError as ve:
        logger.info(f"Vault error processing job {job.id}: {ve}")
        add_breadcrumb(
            "Vault error during job processing",
            category="ai.job",
            level="error",
            data={"vault_error": str(ve)},
        )

        track_ai_metrics(
            "ai_job.vault_error",
            1,
            tags={"job_lens": job.lens.value if job.lens else "unknown"},
        )

        # Capture with enhanced context
        capture_ai_exception(ve, user=job.user, job=job, operation_type="vault_lookup")

        # Create an ad-hoc error object
        error_obj = AIImprovementError(
            type=(
                "initiative"
                if job.lens == Lens.INITIATIVE or job.lens == Lens.INITIATIVES
                else "task"
            ),
            error_message="Could not retrieve your OpenAI API key. Please update your API key in the settings.",
            error_type="vault_error",
        )
        _update_job_on_failure(job, error_obj)

    except Exception as e:
        logger.exception(f"Critical error processing job {job.id}: {str(e)}")
        add_breadcrumb(
            "Critical error during job processing",
            category="ai.job",
            level="error",
            data={"error": str(e), "error_type": type(e).__name__},
        )

        track_ai_metrics(
            "ai_job.critical_error",
            1,
            tags={
                "job_lens": job.lens.value if job.lens else "unknown",
                "error_type": type(e).__name__,
            },
        )

        # Enhanced exception capture
        capture_ai_exception(
            e,
            user=job.user,
            job=job,
            operation_type="job_processing",
            extra_context={"entity_ids": [str(eid) for eid in entity_ids]},
        )

        # Create an ad-hoc error object
        error_obj = AIImprovementError(
            type=(
                "initiative"
                if job.lens == Lens.INITIATIVE or job.lens == Lens.INITIATIVES
                else "task"
            ),
            error_message="An error occurred. Please try again",
            error_type="unhandled_exception",
        )
        _update_job_on_failure(job, error_obj)
    finally:
        # 8. Clear Entity Processing Status (if entity was identified)
        add_breadcrumb("Clearing entity processing status", category="ai.job")
        _update_entity_processing_status(db, job.lens, entity_ids, False)

        # 9. Commit Final Job Status and Entity Status
        try:
            db.commit()
            logger.info(f"Final status for job {job.id}: {job.status.value}")
            add_breadcrumb(
                f"Job completed with status: {job.status.value}",
                category="ai.job",
                data={"final_status": job.status.value},
            )

            # Track final job metrics
            if job.status == JobStatus.COMPLETED:
                track_ai_metrics(
                    "ai_job.success",
                    1,
                    tags={"job_lens": job.lens.value if job.lens else "unknown"},
                )
            elif job.status == JobStatus.FAILED:
                track_ai_metrics(
                    "ai_job.failure",
                    1,
                    tags={"job_lens": job.lens.value if job.lens else "unknown"},
                )

        except Exception as commit_error:
            logger.exception(
                f"Failed to commit final state for job {job.id}: {commit_error}"
            )
            add_breadcrumb(
                "Failed to commit final job state",
                category="ai.job",
                level="error",
                data={"commit_error": str(commit_error)},
            )

            track_ai_metrics(
                "ai_job.commit_error",
                1,
                tags={"job_lens": job.lens.value if job.lens else "unknown"},
            )

            db.rollback()  # Rollback if final commit fails

            # Enhanced commit error capture
            capture_ai_exception(
                commit_error, user=job.user, job=job, operation_type="database_commit"
            )

    return job


def cancel_users_previous_jobs_and_get_last(
    db: Session, user_id: UUID
) -> Optional[AIImprovementJob]:  # Changed return type hint
    """
    Cancels all previous jobs for the given user and retrieves the last job.

    Args:
        db (Session): Database session
        user_id (str): User ID

    Returns:
        Optional[AIImprovementJob]: The last pending job for the user or None
    """
    # ... (implementation remains the same as previous version)
    last_job = (
        db.query(AIImprovementJob)
        .filter(AIImprovementJob.user_id == user_id)
        .filter(AIImprovementJob.status == JobStatus.PENDING)
        .order_by(AIImprovementJob.created_at.desc())
        .options(selectinload(AIImprovementJob.user))  # Optional: load user if needed
        .first()
    )

    # Cancel previous jobs if any
    if last_job:
        db.query(AIImprovementJob).filter(
            AIImprovementJob.user_id == user_id,
            AIImprovementJob.id != last_job.id,
        ).delete(synchronize_session=False)

    return last_job
