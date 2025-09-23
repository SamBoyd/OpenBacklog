import logging
from typing import Any, Dict, List, Optional

from src.db import Session
from src.models import AIImprovementJob, ChatMessage, ChatMode, JobStatus, Lens, User

logger = logging.getLogger(__name__)


# TODO: Move this to a postgres function
def create_ai_improvement_job(
    user: User,
    lens: Lens,
    thread_id: str,
    mode: ChatMode,
    input_data: Optional[List[Dict[str, Any]]] = None,
    messages: Optional[List[ChatMessage]] = None,
    db: Session = None,  # type: ignore
) -> AIImprovementJob:
    """
    Creates a new AIImprovementJob record in the database.

    Args:
        user: The user creating the job
        lens: The lens to use for the improvement (TASK, INITIATIVE, etc.)
        input_data: List of input data objects for the AI improvement job
        messages: List of chat messages for the job
        db: Database session

    Returns:
        The created AIImprovementJob instance

    Raises:
        ValueError: If invalid data is provided
    """

    merged_user = db.merge(user)

    db.query(AIImprovementJob).filter(
        AIImprovementJob.user_id == merged_user.id,
        AIImprovementJob.status == JobStatus.PENDING,
    ).update({"status": JobStatus.CANCELED}, synchronize_session=False)
    db.commit()

    # Create new job with pending status
    job = AIImprovementJob()
    job.user = merged_user
    job.status = JobStatus.PENDING
    job.input_data = input_data or []
    job.messages = messages
    job.lens = lens
    job.mode = mode
    job.thread_id = thread_id

    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info(f"Created AI improvement job {job.id}")
    return job
