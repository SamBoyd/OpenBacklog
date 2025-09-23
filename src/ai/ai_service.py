import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import sentry_sdk
from openai import AuthenticationError
from pydantic import BaseModel, ValidationError
from sqlalchemy import and_, select

from src.accounting.billing_service import BillingService
from src.accounting.billing_state_machine import AccountStatusResponse
from src.accounting.llm_cost_estimator import (
    LLMCostEstimatorError,
    create_cost_estimator,
)
from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.ai.models import (
    AIImprovementError,
    ChatMessageInput,
    DiscussResponseModel,
    VaultError,
)
from src.ai.openai_service import LLMAPIError, _validate_openai_key
from src.ai.prompt import (
    DiscussInitiativePrompt,
    DiscussTaskPrompt,
    InitiativeLLMResponse,
    InitiativePrompt,
    TaskLLMResponse,
    TaskPrompt,
)
from src.config import settings
from src.db import Session, get_db
from src.key_vault import retrieve_api_key_from_vault
from src.models import (
    APIProvider,
    BalanceWarning,
    ChatMode,
    ContextDocument,
    Initiative,
    Lens,
    PydanticInitiative,
    PydanticTask,
    User,
    UserKey,
)

logger = logging.getLogger(__name__)


# Model configuration for cost estimation
LLM_MODEL_NAME = "gpt-4.1-nano"

# Simplified Types for the results
InitiativeImprovementResult = Union[
    DiscussResponseModel, InitiativeLLMResponse, AIImprovementError
]
TaskImprovementResult = Union[DiscussResponseModel, TaskLLMResponse, AIImprovementError]


class BalanceCheckResult(BaseModel):
    """Result of checking user balance for an LLM request."""

    can_proceed: bool
    balance_warning: Optional[BalanceWarning] = None


def check_user_can_afford_request(
    user: User, messages: List[Any], db: Session
) -> BalanceCheckResult:
    """
    Check if user has active subscription with monthly credits left to use
    or if their account balance can afford the LLM request
    and return balance warning if needed.

    Args:
        user_id: The user's UUID
        messages: The messages to be sent to the LLM
        db: Database session

    Returns:
        BalanceCheckResult with can_proceed flag and optional balance_warning
    """
    try:
        # Get billing service
        billing_service = BillingService(db)

        # Get user account details
        account_status: AccountStatusResponse = (
            billing_service.get_account_status_detailed(user)
        )
        if account_status.state not in [
            UserAccountStatus.ACTIVE_SUBSCRIPTION,
            UserAccountStatus.METERED_BILLING,
        ]:
            return BalanceCheckResult(can_proceed=False, balance_warning=None)

        # For paid users, continue with existing balance checking logic
        # Create cost estimator
        cost_estimator = create_cost_estimator(LLM_MODEL_NAME)

        # Estimate request cost
        estimated_cost_cents = cost_estimator.estimate_request_cost_cents(messages)

        # Get balance status with preview
        balance_status = billing_service.get_balance_status_with_preview(
            user, estimated_cost_cents
        )

        enforcement_decision = balance_status.enforcement_decision
        current_status = balance_status.current_status

        # Determine if request can proceed
        can_proceed = enforcement_decision.action in [
            "allow",
            "allow_with_warning",
            "allow_with_suspension",
        ]

        # Create balance warning if there's an issue or warning
        balance_warning = None
        if enforcement_decision.action != "allow":
            balance_warning = BalanceWarning(
                has_warning=True,
                warning_type=enforcement_decision.reason,
                message=enforcement_decision.message,
                current_balance_cents=current_status.usage_balance_cents,
                current_balance_dollars=current_status.usage_balance_dollars,
                estimated_cost_cents=estimated_cost_cents,
                estimated_cost_dollars=estimated_cost_cents / 100.0,
                top_up_needed_cents=balance_status.top_up_needed_cents,
                top_up_needed_dollars=balance_status.top_up_needed_dollars,
            )

        logger.info(
            f"Balance check for user {user.id}: action={enforcement_decision.action}, "
            f"cost=${estimated_cost_cents/100:.4f}, balance=${current_status.usage_balance_cents/100:.2f}"
        )

        return BalanceCheckResult(
            can_proceed=can_proceed, balance_warning=balance_warning
        )

    except (LLMCostEstimatorError, Exception) as e:
        logger.exception(f"Balance check failed for user {user.id}: {e}")
        # On error, allow the request but log the issue
        # This ensures the system doesn't break if cost estimation fails
        return BalanceCheckResult(can_proceed=True, balance_warning=None)


def get_litellm_key_for_free_users() -> str:
    return settings.litellm_master_key


def get_user_api_key(user_id: uuid.UUID, db: Session) -> str:
    """
    Retrieves the validated API key for a given user from the database and vault.

    Args:
        user_id (uuid.UUID): The ID of the user.
        db (Session): The database session.

    Returns:
        str: The retrieved API key.

    Raises:
        ValueError: If the API key is not found for the user or cannot be retrieved from the vault.
    """
    # Fetch the user's API key
    user_key = db.execute(
        select(UserKey).where(
            and_(
                UserKey.user_id == user_id,
                UserKey.provider == APIProvider.LITELLM,
            )
        )
    ).scalar_one_or_none()

    if not user_key:
        account_details: UserAccountDetails = (
            db.query(UserAccountDetails)
            .filter(UserAccountDetails.user_id == user_id)
            .first()
        )
        if account_details and account_details.status == UserAccountStatus.NEW:
            return get_litellm_key_for_free_users()
        else:
            raise VaultError(f"API key not found for user {user_id}")

    if not user_key.is_valid:
        raise VaultError(f"API key for user {user_id} is marked as not valid")

    try:
        api_key = retrieve_api_key_from_vault(user_key.vault_path)
        if api_key is None:
            raise VaultError(
                "Vault service is currently unavailable. Please try again later or contact support."
            )
        if not api_key:
            raise VaultError(
                f"Empty API key retrieved from vault for user {user_id}. Path: {user_key.vault_path}"
            )
        return api_key
    except VaultError:
        # Re-raise VaultError as-is
        raise
    except Exception as vault_error:
        logger.exception(f"Vault retrieval error for user {user_id}: {vault_error}")
        raise VaultError(
            "Could not retrieve your API key. Please check your API key in the settings."
        ) from vault_error


# --- Updated Service Functions --- (Removed old helper functions implicitly)


async def process_initiative_improvement(
    thread_id: str,
    user: User,
    input_data: List[Dict[str, Any]],
    mode: ChatMode,
    messages: Optional[List[ChatMessageInput]] = None,
) -> InitiativeImprovementResult:
    db = next(get_db())
    initiatives: List[PydanticInitiative] = []
    try:
        try:
            initiatives = [PydanticInitiative(**data) for data in input_data]
        except ValidationError as e:
            logger.exception(f"Pydantic validation error parsing initiative data: {e}")
            raise ValueError(f"Invalid initiative data provided: {e}") from e

        user_id = user.id
        oauth_account = user.oauth_accounts[0]
        user_auth_token = oauth_account.access_token

        if not user_auth_token:
            raise VaultError(f"User auth token not found for user {user_id}")

        unredacted_key = get_user_api_key(user_id, db)

        additional_context = ""
        # Fetch ContextDocument if workspace_id is available
        if not initiatives:
            logger.info(f"No initiatives provided for user {user_id}")

        workspace_id = user.workspaces[0].id
        context_doc: Optional[ContextDocument] = db.execute(
            select(ContextDocument).where(
                ContextDocument.user_id == user_id,
                ContextDocument.workspace_id == workspace_id,
            )
        ).scalar_one_or_none()
        if context_doc:
            additional_context = context_doc.content

        if mode == ChatMode.EDIT:
            prompt = InitiativePrompt(
                initiatives,
                messages=messages,
                additional_context=additional_context,
            )
        else:
            prompt = DiscussInitiativePrompt(
                initiatives,
                messages=messages,
                additional_context=additional_context,
            )

        # Check user balance before making LLM request
        prompt_messages = prompt.build_messages()

        # Check balance
        balance_result = check_user_can_afford_request(user, prompt_messages, db)

        if not balance_result.can_proceed:
            # Return error with balance information
            return AIImprovementError(
                type="initiative",
                error_message=(
                    balance_result.balance_warning.message
                    if balance_result.balance_warning
                    else "Insufficient balance"
                ),
                error_type="insufficient_balance",
            )

        try:
            llm_response = await prompt.process_prompt(
                api_key=unredacted_key,
                user_auth_token=user_auth_token,
                workspace_id=str(workspace_id),
                thread_id=thread_id,
                user_id=str(user_id),
            )

            # Add balance warning to response if needed
            if balance_result.balance_warning and hasattr(
                llm_response, "balance_warning"
            ):
                llm_response.balance_warning = balance_result.balance_warning
        except LLMAPIError as e:
            logger.exception(f"LLM API error during initiative processing: {e}")
            raise

        return llm_response

    except Exception as e:
        logger.exception(f"Error processing initiative improvement: {str(e)}")
        error_type = None
        if isinstance(e, LLMAPIError):
            error_type = "llm_api_error"
        elif isinstance(e, AuthenticationError):
            error_type = "authentication_error"
        elif isinstance(e, ValueError):
            error_type = "value_error"  # Covers parsing/validation
        elif isinstance(e, VaultError):
            error_type = "api_key_error"
        elif isinstance(e, FileNotFoundError):
            error_type = "template_not_found"

        sentry_sdk.capture_exception(e)

        return AIImprovementError(
            type="initiative",
            error_message=str(e),
            error_type=error_type,
        )
    finally:
        db.close()


async def process_task_improvement(
    thread_id: str,
    user: User,
    lens: Lens,
    input_data: List[Dict[str, Any]],
    mode: ChatMode,
    messages: Optional[List[ChatMessageInput]] = None,
) -> TaskImprovementResult:
    db = next(get_db())
    tasks: List[PydanticTask] = []
    try:
        try:
            tasks = [PydanticTask(**data) for data in input_data]
        except ValidationError as e:
            logger.exception(f"Pydantic validation error parsing task data: {e}")
            raise ValueError(f"Invalid task data provided: {e}") from e

        if not tasks:
            raise ValueError("No valid task data provided in input_data")

        initiative_id = tasks[0].initiative_id
        if not initiative_id:
            raise ValueError(
                f"Initiative ID is missing for the first task: {tasks[0].id}"
            )

        # Fetch the SQLAlchemy Initiative model for context
        initiative: Optional[Initiative] = db.execute(
            select(Initiative).where(Initiative.id == initiative_id)
        ).scalar_one_or_none()

        if not initiative:
            raise ValueError(
                f"Initiative with ID {initiative_id} (from task {tasks[0].id}) not found"
            )

        user_id = user.id
        oauth_account = user.oauth_accounts[0]
        user_auth_token = oauth_account.access_token

        if not user_auth_token:
            raise VaultError(f"User auth token not found for user {user_id}")

        unredacted_key = get_user_api_key(user_id, db)

        additional_context = ""
        # Fetch ContextDocument using the initiative's workspace_id
        workspace_id = user.workspaces[0].id
        context_doc: Optional[ContextDocument] = db.execute(
            select(ContextDocument).where(
                and_(
                    ContextDocument.user_id == user_id,
                    ContextDocument.workspace_id == workspace_id,
                )
            )
        ).scalar_one_or_none()
        logger.info(
            f"Context document found for task improvement for user {user_id}: {context_doc}"
        )
        if context_doc:
            additional_context = context_doc.content
            logger.info(
                f"Using context document {context_doc.id} for task improvement for user {user_id}"
            )

        if mode == ChatMode.EDIT:
            prompt = TaskPrompt(
                tasks,
                initiative=initiative,
                messages=messages,
                additional_context=additional_context,
            )
        else:
            prompt = DiscussTaskPrompt(
                tasks,
                initiative=initiative,
                messages=messages,
                additional_context=additional_context,
            )

        # Check user balance before making LLM request
        prompt_messages = prompt.build_messages()

        # Check balance
        balance_result = check_user_can_afford_request(user, prompt_messages, db)

        if not balance_result.can_proceed:
            # Return error with balance information
            return AIImprovementError(
                type="task",
                error_message=(
                    balance_result.balance_warning.message
                    if balance_result.balance_warning
                    else "Insufficient balance"
                ),
                error_type="insufficient_balance",
            )

        try:
            result = await prompt.process_prompt(
                api_key=unredacted_key,
                user_auth_token=user_auth_token,
                workspace_id=str(workspace_id),
                thread_id=thread_id,
                user_id=str(user_id),
            )

            # Add balance warning to response if needed
            if balance_result.balance_warning and hasattr(result, "balance_warning"):
                result.balance_warning = balance_result.balance_warning
        except LLMAPIError as e:
            task_ids_str = ", ".join([str(t.id) for t in tasks])
            logger.exception(
                f"LLM API error during task processing for tasks [{task_ids_str}]: {e}"
            )
            raise

        return result

    except Exception as e:
        task_ids_repr = [data.get("id", "UNKNOWN") for data in input_data]
        logger.exception(
            f"Error processing task request for IDs {task_ids_repr}: {str(e)}"
        )

        error_type = "processing_error"
        if isinstance(e, LLMAPIError):
            error_type = "llm_api_error"
        elif isinstance(e, AuthenticationError):
            error_type = "authentication_error"
        elif isinstance(e, ValueError):
            if "API key" in str(e) or "vault" in str(e).lower():
                error_type = "api_key_error"
            else:
                error_type = "value_error"
        elif isinstance(e, VaultError):
            error_type = "api_key_error"
        elif isinstance(e, FileNotFoundError):
            error_type = "template_not_found"

        sentry_sdk.capture_exception(e)

        return AIImprovementError(
            type="task",
            error_message=str(e),
            error_type=error_type,
        )
    finally:
        db.close()


def revalidate_user_key(user_key: UserKey, unredacted_key: str, db: Session):
    """
    Revalidates the user's OpenAI API key. Marks as invalid if validation fails.
    """
    logger.info(f"Revalidating OpenAI key for user {user_key.user_id}")
    is_now_valid = False
    try:
        is_now_valid = _validate_openai_key(unredacted_key)
    except Exception as validation_error:
        logger.exception(
            f"Error during key validation call for user {user_key.user_id}: {validation_error}"
        )
        is_now_valid = False  # Treat validation error as invalid

    user_key.last_validated_at = datetime.now()
    user_key.is_valid = is_now_valid
    db.commit()
    logger.info(
        f"Key validation result for user {user_key.user_id}: {'Valid' if is_now_valid else 'Invalid'}"
    )
