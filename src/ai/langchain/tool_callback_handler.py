"""
Custom callback handler for tracking internal tool invocations.
This replaces the thread-local storage approach with a callback-based solution.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

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
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    track_ai_metrics,
)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class ToolCallbackHandler(BaseCallbackHandler):
    """Callback handler that tracks internal tool invocations"""

    def __init__(self):
        self.task_operations: List[TaskOperation] = []
        self.initiative_operations: List[InitiativeOperation] = []

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts running"""

        tool_name = serialized.get("name", "")

        # Only track our internal tools
        if not tool_name.startswith("internal_"):
            return

        logger.debug(f"Tool callback captured: {tool_name} with inputs: {inputs}")

        try:
            if tool_name == "internal_create_task":
                task_data = TaskCreateData(
                    initiative_identifier=inputs.get("initiative_identifier"),
                    title=inputs.get("title"),
                    description=inputs.get("description"),
                )
                operation = TaskOperation(operation_type="create", task_data=task_data)
                self.task_operations.append(operation)

            elif tool_name == "internal_update_task":
                task_data = TaskUpdateData(
                    initiative_identifier=inputs.get("initiative_identifier"),
                    identifier=inputs.get("identifier"),
                    title=inputs.get("title", ""),
                    description=inputs.get("description", ""),
                )
                operation = TaskOperation(operation_type="update", task_data=task_data)
                self.task_operations.append(operation)

            elif tool_name == "internal_delete_task":
                task_data = TaskDeleteData(
                    initiative_identifier=inputs.get("initiative_identifier"),
                    identifier=inputs.get("identifier"),
                )
                operation = TaskOperation(operation_type="delete", task_data=task_data)
                self.task_operations.append(operation)

            elif tool_name == "internal_create_initiative":
                # Extract initiative data (including tasks)
                initiative_data = InitiativeCreateData(
                    title=inputs.get("title"),
                    description=inputs.get("description"),
                    temporary_identifier=inputs.get("temporary_identifier"),
                    tasks=inputs.get("tasks", []),
                )

                # Create initiative operation
                initiative_operation = InitiativeOperation(
                    operation_type="create", initiative_data=initiative_data
                )
                self.initiative_operations.append(initiative_operation)

                # Create task operations for each task in the list
                temporary_identifier = inputs.get("temporary_identifier")
                tasks_list = inputs.get("tasks") or []

                try:
                    for task_dict in tasks_list:
                        # Skip tasks without required title field
                        if not task_dict.get("title"):
                            logger.warning(
                                f"Skipping task without title in initiative {temporary_identifier}"
                            )
                            continue

                        task_data = TaskCreateData(
                            initiative_identifier=temporary_identifier,
                            title=task_dict.get("title", ""),
                            description=task_dict.get("description", ""),
                        )
                        task_operation = TaskOperation(
                            operation_type="create", task_data=task_data
                        )
                        self.task_operations.append(task_operation)

                    # Log for debugging
                    add_breadcrumb(
                        f"Captured initiative creation with {len(tasks_list)} tasks",
                        category="ai.tool_callback",
                        data={
                            "initiative_title": inputs.get("title"),
                            "temporary_identifier": temporary_identifier,
                            "task_count": len(tasks_list),
                        },
                    )
                except Exception as task_error:
                    # Log error but continue with initiative creation
                    logger.error(
                        f"Error creating task operations for initiative {temporary_identifier}: {task_error}"
                    )
                    track_ai_metrics(
                        "langchain.tool_callback.task_creation_error",
                        1,
                        tags={
                            "initiative_identifier": temporary_identifier,
                            "error_type": type(task_error).__name__,
                        },
                    )
                    capture_ai_exception(
                        task_error,
                        operation_type="tool_callback_task_creation",
                        extra_context={
                            "tool_name": tool_name,
                            "initiative_identifier": temporary_identifier,
                            "tasks_list": tasks_list,
                        },
                    )

            elif tool_name == "internal_update_initiative":
                initiative_data = InitiativeUpdateData(
                    identifier=inputs.get("identifier"),
                    title=inputs.get("title", ""),
                    description=inputs.get("description", ""),
                )
                operation = InitiativeOperation(
                    operation_type="update", initiative_data=initiative_data
                )
                self.initiative_operations.append(operation)

            elif tool_name == "internal_delete_initiative":
                initiative_data = InitiativeDeleteData(
                    identifier=inputs.get("identifier")
                )
                operation = InitiativeOperation(
                    operation_type="delete", initiative_data=initiative_data
                )
                self.initiative_operations.append(operation)

        except Exception as e:
            add_breadcrumb(
                f"Failed to track tool {tool_name}",
                category="ai.tool_callback",
                level="error",
                data={"tool_name": tool_name, "error": str(e)},
            )
            track_ai_metrics(
                "langchain.tool_callback.tracking_error",
                1,
                tags={"tool_name": tool_name, "error_type": type(e).__name__},
            )
            capture_ai_exception(
                e,
                operation_type="tool_callback_tracking",
                extra_context={
                    "tool_name": tool_name,
                    "inputs": inputs,
                    "callback_stage": "tool_end_tracking",
                },
            )
            logger.exception(f"Error tracking tool {tool_name}: {e}")

    def get_task_operations(self) -> List[TaskOperation]:
        """Get all tracked task operations"""
        return self.task_operations

    def get_initiative_operations(self) -> List[InitiativeOperation]:
        """Get all tracked initiative operations"""
        return self.initiative_operations

    def clear_operations(self) -> None:
        """Clear all tracked operations"""
        self.task_operations = []
        self.initiative_operations = []
