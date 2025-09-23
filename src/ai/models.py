from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator
from pyparsing import Any

from src.models import (
    BalanceWarning,
    ChatMode,
    ChecklistItemModel,
    CreateInitiativeModel,
    CreateTaskModel,
    DeleteInitiativeModel,
    DeleteTaskModel,
    InitiativeLLMResponse,
    InitiativeType,
    Lens,
    ManagedInitiativeModel,
    ManagedTaskModel,
    TaskLLMResponse,
    TaskStatus,
    TaskType,
    UpdateInitiativeModel,
    UpdateTaskModel,
)


class TaskInputData(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    type: Optional[TaskType] = None


class InitiativeInputData(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    type: Optional[InitiativeType] = None


class ChatMessageInput(BaseModel):
    role: Literal["assistant", "system", "user"]
    content: str
    suggested_changes: Optional[
        List[Union[ManagedTaskModel, ManagedInitiativeModel]]
    ] = None


class AIImprovementRequest(BaseModel):
    input_data: Optional[List[Dict[str, Any]]] = None
    thread_id: str
    messages: Optional[List[ChatMessageInput]] = None
    lens: Lens
    mode: ChatMode

    @model_validator(mode="after")
    def validate_input_data(self):
        # Skip validation if input_data is None
        if self.input_data is None:
            return self

        return self

    # TODO: Add a validator for the lens + a non empty list for LENS.TASK & LENS.INITIATIVE


class VaultError(Exception):
    """Exception for vault errors."""

    pass


# Define model for error result (Keep this)
class AIImprovementError(BaseModel):
    type: Literal["initiative", "task"]
    status: Literal["error"] = "error"
    error_message: str
    error_type: Optional[str] = None


class DiscussResponseModel(BaseModel):
    message: str
    balance_warning: Optional[BalanceWarning] = Field(
        default=None, description="Account balance warning information"
    )


class EasyDiscussResponseModel(BaseModel):
    message: str
    balance_warning: Optional[BalanceWarning] = Field(
        default=None, description="Account balance warning information"
    )

    def to_managed_model(self) -> DiscussResponseModel:
        return DiscussResponseModel(
            message=self.message, balance_warning=self.balance_warning
        )


class EasyCreateTaskModel(BaseModel):
    title: str = Field(..., description="The title of the task to create.")
    description: str = Field(..., description="The description of the task to create.")
    checklist: Optional[List[str]] = Field(
        ..., description="The checklist items of the task to create."
    )

    def to_managed_task_model(self) -> CreateTaskModel:
        return CreateTaskModel(
            title=self.title,
            description=self.description,
            checklist=[ChecklistItemModel(title=item) for item in self.checklist or []],
        )


class EasyDeleteTaskModel(BaseModel):
    identifier: str = Field(..., description="The identifier of the task to delete.")

    def to_managed_task_model(self) -> DeleteTaskModel:
        return DeleteTaskModel(
            identifier=self.identifier,
        )


class EasyUpdateTaskModel(BaseModel):
    identifier: str = Field(..., description="The identifier of the task to update.")
    title: Optional[str] = Field(..., description="The title of the task to update.")
    description: Optional[str] = Field(
        ..., description="The description of the task to update."
    )
    checklist: Optional[List[str]] = Field(
        ..., description="The checklist items of the task to update."
    )

    def to_managed_task_model(self) -> UpdateTaskModel:
        return UpdateTaskModel(
            identifier=self.identifier,
            title=self.title,
            description=self.description,
            checklist=[ChecklistItemModel(title=item) for item in self.checklist or []],
        )


class EasyCreateInitiativeModel(BaseModel):
    title: str = Field(..., description="The title of the initiative to create.")
    description: str = Field(
        ..., description="The description of the initiative to create."
    )
    tasks: Optional[List[EasyCreateTaskModel]] = Field(
        ..., description="The tasks to create with the initiative."
    )

    def to_managed_initiative_model(self) -> CreateInitiativeModel:
        return CreateInitiativeModel(
            title=self.title,
            description=self.description,
            tasks=[task.to_managed_task_model() for task in self.tasks or []],
        )


class EasyDeleteInitiativeModel(BaseModel):
    identifier: str = Field(
        ..., description="The identifier of the initiative to delete."
    )

    def to_managed_initiative_model(self) -> DeleteInitiativeModel:
        return DeleteInitiativeModel(
            identifier=self.identifier,
        )


class EasyUpdateInitiativeModel(BaseModel):
    identifier: str = Field(
        ..., description="The identifier of the initiative to update."
    )
    title: Optional[str] = Field(
        ..., description="The title of the initiative to update."
    )
    description: Optional[str] = Field(
        ..., description="The description of the initiative to update."
    )
    task: Optional[
        List[EasyCreateTaskModel | EasyDeleteTaskModel | EasyUpdateTaskModel]
    ] = Field(..., description="The tasks to update with the initiative.")

    def to_managed_initiative_model(self) -> UpdateInitiativeModel:
        return UpdateInitiativeModel(
            identifier=self.identifier,
            title=self.title,
            description=self.description,
            tasks=[task.to_managed_task_model() for task in self.task or []],
        )


class EasyLLMResponse(BaseModel):
    """
    Pydantic model defining the standardized structure of the LLM response
    for any entity batch operations.
    """

    message: str = Field()

    def to_managed_model(self) -> Union[InitiativeLLMResponse, TaskLLMResponse]:
        raise NotImplementedError("Subclasses must implement this method")


class EasyInitiativeLLMResponse(EasyLLMResponse):
    """
    Pydantic model defining the standardized structure of the LLM response
    for initiative batch operations.
    """

    message: str = Field(
        ...,
        description="Your reply to the user. If no changes are needed, or you're asked a question then this is where you should put your reply.",
    )
    created_initiatives: List[EasyCreateInitiativeModel] = Field(
        ...,
        description="List of initiatives to create. If no changes are needed, then this should be an empty list.",
    )
    deleted_initiatives: List[EasyDeleteInitiativeModel] = Field(
        ...,
        description="List of initiatives to delete. If no changes are needed, then this should be an empty list.",
    )
    updated_initiatives: List[EasyUpdateInitiativeModel] = Field(
        ...,
        description="List of initiatives to update. If no changes are needed, then this should be an empty list.",
    )
    balance_warning: Optional[BalanceWarning] = Field(
        default=None, description="Account balance warning information"
    )

    def to_managed_model(self) -> InitiativeLLMResponse:
        return InitiativeLLMResponse(
            message=self.message,
            managed_initiatives=[
                *[
                    initiative.to_managed_initiative_model()
                    for initiative in self.created_initiatives
                ],
                *[
                    initiative.to_managed_initiative_model()
                    for initiative in self.deleted_initiatives
                ],
                *[
                    initiative.to_managed_initiative_model()
                    for initiative in self.updated_initiatives
                ],
            ],
            balance_warning=self.balance_warning,
        )


class SimpleLLMResponse(BaseModel):
    """Simple LLM response model - only generates message, tools handle operations"""

    message: str = Field(
        ...,
        description="Your reply to the user explaining what changes you are making or responding to their question.",
    )

    def to_managed_model(self) -> Union[InitiativeLLMResponse, TaskLLMResponse]:
        raise NotImplementedError("Subclasses must implement this method")


class EasyTaskLLMResponse(EasyLLMResponse):
    message: str = Field(
        ...,
        description="Your reply to the user. If no changes are needed, or you're asked a question then this is where you should put your reply.",
    )
    created_tasks: List[EasyCreateTaskModel] = Field(
        ...,
        description="List of tasks to create. If no changes are needed, then this should be an empty list.",
    )
    deleted_tasks: List[EasyDeleteTaskModel] = Field(
        ...,
        description="List of tasks to delete. If no changes are needed, then this should be an empty list.",
    )
    updated_tasks: List[EasyUpdateTaskModel] = Field(
        ...,
        description="List of tasks to update. If no changes are needed, then this should be an empty list.",
    )
    balance_warning: Optional[BalanceWarning] = Field(
        default=None, description="Account balance warning information"
    )

    def to_managed_model(
        self,
    ) -> TaskLLMResponse:
        return TaskLLMResponse(
            message=self.message,
            managed_tasks=[
                *[task.to_managed_task_model() for task in self.created_tasks],
                *[task.to_managed_task_model() for task in self.deleted_tasks],
                *[task.to_managed_task_model() for task in self.updated_tasks],
            ],
            balance_warning=self.balance_warning,
        )
