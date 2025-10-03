"""
Response builder that constructs structured output from internal tool operations.
This allows the LLM to use simple tools while maintaining the expected API contract.
"""

import logging
from typing import Dict, List, Optional, Union

from src.ai.langchain.internal_tools import (
    InitiativeCreateData,
    InitiativeDeleteData,
    InitiativeOperation,
    InitiativeUpdateData,
    TaskCreateData,
    TaskDeleteData,
    TaskOperation,
    TaskUpdateData,
)
from src.ai.models import (
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
from src.models import BalanceWarning
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    track_ai_metrics,
)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class ResponseBuilder:
    """Builds structured responses from internal tool operations"""

    def __init__(self):
        pass

    def build_task_response(
        self,
        message: str,
        operations: List[TaskOperation],
        balance_warning: Optional[BalanceWarning] = None,
    ) -> EasyTaskLLMResponse:
        """Build EasyTaskLLMResponse from provided task operations"""

        created_tasks = []
        updated_tasks = []
        deleted_tasks = []

        logger.debug("Building response from %s task operations", len(operations))

        for operation in operations:
            logger.debug(f"LLM called operation: {operation}")

            op_type = operation.operation_type
            task_data = operation.task_data

            try:
                if op_type == "create":
                    task_data: TaskCreateData = task_data

                    task_model = EasyCreateTaskModel(
                        title=task_data.title,
                        description=task_data.description,
                        checklist=[],
                    )
                    created_tasks.append(task_model)

                elif op_type == "update":
                    task_data: TaskUpdateData = task_data

                    task_model = EasyUpdateTaskModel(
                        identifier=task_data.identifier,
                        title=task_data.title,
                        description=task_data.description,
                        checklist=[],
                    )
                    updated_tasks.append(task_model)

                elif op_type == "delete":
                    task_data: TaskDeleteData = task_data

                    task_model = EasyDeleteTaskModel(identifier=task_data.identifier)
                    deleted_tasks.append(task_model)

            except Exception as e:
                add_breadcrumb(
                    f"Failed to build task model from operation {op_type}",
                    category="ai.response_builder",
                    level="error",
                    data={"operation_type": op_type, "error": str(e)},
                )
                track_ai_metrics(
                    "langchain.response_builder.task_operation_error",
                    1,
                    tags={"operation_type": op_type, "error_type": type(e).__name__},
                )
                capture_ai_exception(
                    e,
                    operation_type="response_building",
                    extra_context={
                        "operation_type": op_type,
                        "task_data": (
                            task_data.__dict__
                            if hasattr(task_data, "__dict__")
                            else str(task_data)
                        ),
                        "builder_stage": "task_model_creation",
                    },
                )
                logger.exception(
                    f"Error building task model from operation {op_type}: {e}"
                )
                logger.exception(f"Task data: {task_data}")
                continue

        return EasyTaskLLMResponse(
            message=message,
            created_tasks=created_tasks,
            updated_tasks=updated_tasks,
            deleted_tasks=deleted_tasks,
            balance_warning=balance_warning,
        )

    def _group_tasks_by_initiative(
        self, task_operations: List[TaskOperation]
    ) -> Dict[
        str, List[Union[EasyCreateTaskModel, EasyUpdateTaskModel, EasyDeleteTaskModel]]
    ]:
        """Group task operations by initiative identifier"""
        tasks_by_initiative = {}

        for operation in task_operations:
            logger.debug(f"Processing task operation: {operation}")

            try:
                op_type = operation.operation_type
                task_data = operation.task_data

                # Get initiative identifier from task data
                initiative_identifier = None
                if op_type == "create":
                    task_data: TaskCreateData = task_data
                    initiative_identifier = task_data.initiative_identifier

                    task_model = EasyCreateTaskModel(
                        title=task_data.title,
                        description=task_data.description,
                        checklist=[],
                    )
                elif op_type == "update":
                    task_data: TaskUpdateData = task_data
                    initiative_identifier = task_data.initiative_identifier

                    task_model = EasyUpdateTaskModel(
                        identifier=task_data.identifier,
                        title=task_data.title,
                        description=task_data.description,
                        checklist=[],
                    )

                elif op_type == "delete":
                    task_data: TaskDeleteData = task_data
                    initiative_identifier = task_data.initiative_identifier

                    task_model = EasyDeleteTaskModel(identifier=task_data.identifier)

                if initiative_identifier:
                    if initiative_identifier not in tasks_by_initiative:
                        tasks_by_initiative[initiative_identifier] = []
                    tasks_by_initiative[initiative_identifier].append(task_model)

            except Exception as e:
                add_breadcrumb(
                    f"Failed to process task operation",
                    category="ai.response_builder",
                    level="error",
                    data={"error": str(e)},
                )
                track_ai_metrics(
                    "langchain.response_builder.task_processing_error",
                    1,
                    tags={"error_type": type(e).__name__},
                )
                capture_ai_exception(
                    e,
                    operation_type="response_building",
                    extra_context={
                        "operation_data": (
                            operation.__dict__
                            if hasattr(operation, "__dict__")
                            else str(operation)
                        ),
                        "builder_stage": "task_operation_processing",
                    },
                )
                logger.exception(f"Error processing task operation: {e}")
                logger.exception(f"Operation data: {operation}")
                continue

        return tasks_by_initiative

    def build_initiative_response(
        self,
        message: str,
        operations: List[InitiativeOperation],
        task_operations: List[TaskOperation],
        balance_warning: Optional[BalanceWarning] = None,
    ) -> EasyInitiativeLLMResponse:
        """Build EasyInitiativeLLMResponse from provided initiative operations and associated task operations"""

        created_initiatives = []
        updated_initiatives = []
        deleted_initiatives = []

        # Group task operations by initiative identifier
        tasks_by_initiative = self._group_tasks_by_initiative(task_operations)

        logger.debug(
            "Building response from %s initiative operations and %s task operations",
            len(operations),
            len(task_operations),
        )

        # Track which initiative identifiers have been processed
        processed_initiative_ids = set()

        # Create mapping from temporary identifiers to created initiatives
        temp_id_to_create_op = {}

        # Track create operations by temporary identifier for deduplication
        temp_id_to_create_index = {}

        for operation in operations:
            logger.debug(f"LLM called operation: {operation}")

            op_type = operation.operation_type
            initiative_data = operation.initiative_data

            try:
                if op_type == "create":
                    initiative_data: InitiativeCreateData = initiative_data
                    temp_id = initiative_data.temporary_identifier

                    # Get tasks associated with this temporary identifier
                    temp_tasks = tasks_by_initiative.get(temp_id, [])

                    initiative_model = EasyCreateInitiativeModel(
                        title=initiative_data.title,
                        description=initiative_data.description,
                        tasks=temp_tasks,
                    )

                    # Deduplication: If we've seen this temp_id before, REPLACE the previous one
                    if temp_id in temp_id_to_create_index:
                        # Replace existing initiative at the tracked index
                        idx = temp_id_to_create_index[temp_id]
                        previous_task_count = len(created_initiatives[idx].tasks)
                        created_initiatives[idx] = initiative_model

                        add_breadcrumb(
                            f"Replacing duplicate initiative create operation for {temp_id}",
                            category="ai.response_builder",
                            data={
                                "temporary_identifier": temp_id,
                                "previous_task_count": previous_task_count,
                                "new_task_count": len(temp_tasks),
                            },
                        )
                    else:
                        # First time seeing this temp_id, append normally
                        created_initiatives.append(initiative_model)
                        temp_id_to_create_index[temp_id] = len(created_initiatives) - 1

                    # Track this temporary ID as processed
                    temp_id_to_create_op[temp_id] = operation
                    processed_initiative_ids.add(temp_id)

                elif op_type == "update":
                    initiative_data: InitiativeUpdateData = initiative_data

                    # Get associated tasks for this initiative
                    initiative_tasks = tasks_by_initiative.get(
                        initiative_data.identifier, []
                    )

                    initiative_model = EasyUpdateInitiativeModel(
                        identifier=initiative_data.identifier,
                        title=initiative_data.title,
                        description=initiative_data.description,
                        task=initiative_tasks,
                    )
                    updated_initiatives.append(initiative_model)
                    processed_initiative_ids.add(initiative_data.identifier)

                elif op_type == "delete":
                    initiative_data: InitiativeDeleteData = initiative_data

                    initiative_model = EasyDeleteInitiativeModel(
                        identifier=initiative_data.identifier
                    )
                    deleted_initiatives.append(initiative_model)
                    processed_initiative_ids.add(initiative_data.identifier)

            except Exception as e:
                add_breadcrumb(
                    f"Failed to build initiative model from operation {op_type}",
                    category="ai.response_builder",
                    level="error",
                    data={"operation_type": op_type, "error": str(e)},
                )
                track_ai_metrics(
                    "langchain.response_builder.initiative_operation_error",
                    1,
                    tags={"operation_type": op_type, "error_type": type(e).__name__},
                )
                capture_ai_exception(
                    e,
                    operation_type="response_building",
                    extra_context={
                        "operation_type": op_type,
                        "initiative_data": (
                            initiative_data.__dict__
                            if hasattr(initiative_data, "__dict__")
                            else str(initiative_data)
                        ),
                        "builder_stage": "initiative_model_creation",
                    },
                )
                logger.exception(
                    f"Error building initiative model from operation {op_type}: {e}"
                )
                logger.exception(f"Initiative data: {initiative_data}")
                continue

        # Handle orphaned task operations (tasks with initiative identifiers that have no corresponding initiative operations)
        for initiative_id, orphaned_tasks in tasks_by_initiative.items():
            if initiative_id not in processed_initiative_ids:
                # Check if this is a temporary identifier that we might have missed
                if initiative_id.startswith("TEMP-INIT-"):
                    logger.warning(
                        f"Found tasks referencing unprocessed temporary initiative ID: {initiative_id}"
                    )
                    # Skip these - they should have been handled by create operations
                    continue

                logger.debug(
                    f"Creating update model for orphaned tasks in initiative {initiative_id}"
                )

                try:
                    # Create an EasyUpdateInitiativeModel with None title/description for orphaned tasks
                    orphaned_initiative_model = EasyUpdateInitiativeModel(
                        identifier=initiative_id,
                        title=None,
                        description=None,
                        task=orphaned_tasks,
                    )
                    updated_initiatives.append(orphaned_initiative_model)
                except Exception as e:
                    add_breadcrumb(
                        f"Failed to create orphaned initiative model for {initiative_id}",
                        category="ai.response_builder",
                        level="error",
                        data={"initiative_id": initiative_id, "error": str(e)},
                    )
                    track_ai_metrics(
                        "langchain.response_builder.orphaned_initiative_error",
                        1,
                        tags={"error_type": type(e).__name__},
                    )
                    capture_ai_exception(
                        e,
                        operation_type="response_building",
                        extra_context={
                            "initiative_id": initiative_id,
                            "builder_stage": "orphaned_initiative_creation",
                        },
                    )
                    logger.exception(
                        f"Error creating orphaned initiative model for {initiative_id}: {e}"
                    )
                    continue

        return EasyInitiativeLLMResponse(
            message=message,
            created_initiatives=created_initiatives,
            updated_initiatives=updated_initiatives,
            deleted_initiatives=deleted_initiatives,
            balance_warning=balance_warning,
        )

    def build_discuss_response(
        self,
        message: str,
        balance_warning: Optional[BalanceWarning] = None,
    ) -> EasyDiscussResponseModel:
        return EasyDiscussResponseModel(
            message=message,
            balance_warning=balance_warning,
        )
