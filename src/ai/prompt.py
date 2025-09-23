# src/ai/prompt.py

import logging
import os
from datetime import datetime
from typing import Any, List, Optional, Type, TypeVar, cast

import jinja2
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from src.ai.langchain.langchain_service import call_llm_api
from src.ai.models import (
    ChatMessageInput,
    DiscussResponseModel,
    EasyDiscussResponseModel,
    EasyInitiativeLLMResponse,
    EasyLLMResponse,
    EasyTaskLLMResponse,
)
from src.config import settings
from src.models import (
    ChatMessage,
    ChatMode,
    Initiative,
    InitiativeLLMResponse,
    PydanticInitiative,
    PydanticTask,
    TaskLLMResponse,
)

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class Prompt:
    """
    Class representing an AI prompt with structured components.

    Attributes:
        base_content (str): The main content of the prompt
        additional_context (str): Any additional context to include
    """

    system_prompt_template: str
    mode: ChatMode = ChatMode.EDIT
    response_model: Any
    easy_response_model: Type[EasyLLMResponse]

    def __init__(
        self,
        base_content: str,
        additional_context: Optional[str] = None,
        messages: Optional[List[ChatMessageInput]] = None,
    ):
        self.base_content = base_content
        self.additional_context = additional_context
        self.messages = messages

    def render_system_content(self) -> str:
        return self.base_content

    def build_messages(self) -> List[ChatMessage]:
        """
        Build the list of messages for LLM processing without calling the LLM.

        Returns:
            List of ChatMessage dictionaries ready for LLM processing
        """
        system_content = self.render_system_content()
        system_message: ChatMessage = {"role": "system", "content": system_content}

        # Prepare the full list of messages
        messages: List[ChatMessage] = [system_message]
        # Assume self.messages comes from InitiativePrompt/TaskPrompt and is List[ChatMessage]
        if self.messages:  # Check if messages exist and is not None/empty
            for msg_input in self.messages:
                combined_content = msg_input.content
                if msg_input.suggested_changes:
                    # Serialize each suggestion in the list to JSON
                    suggestions_json = "\n".join(
                        [
                            suggestion.model_dump_json(indent=2)
                            for suggestion in msg_input.suggested_changes
                        ]
                    )
                    combined_content += (
                        f"\n\n--- Previous Suggestion(s) ---\n{suggestions_json}"
                    )

                messages.append({"role": msg_input.role, "content": combined_content})

        return messages

    async def process_prompt(
        self,
        api_key: str,
        user_auth_token: str,
        workspace_id: str,
        thread_id: str,
        user_id: str,
        callbacks: Optional[List] = None,
    ) -> T:
        """
        Call the LLM API using the constructed messages, validate the response using
        the stored Pydantic response_model, and perform optional custom validation.

        Args:
            api_key (str): The API key to use for the LLM call.
            user_auth_token (str): The user's auth token.
            workspace_id (str): The workspace ID.
        """
        # Cast the result to the specific type T expected by the caller
        if not hasattr(self, "response_model") or self.response_model is None:
            raise TypeError("Prompt subclass must define 'response_model'")

        # Use the build_messages method to construct messages
        messages = self.build_messages()

        if settings.log_prompts:
            with open("prompts.log", "a") as f:
                f.write(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    + "\n"
                    + f"System Message: {self.render_system_content()}\n"
                    + f"User/Assistant Messages: {messages[1:]}\n\n"  # Log subsequent messages
                )

        # Prepare context if this is a TaskPrompt
        validation_context = None
        if isinstance(self, TaskPrompt):
            input_identifiers = {
                task.identifier for task in self.tasks if task.identifier
            }
            validation_context = {"valid_task_identifiers": input_identifiers}
        elif isinstance(self, InitiativePrompt):
            input_identifiers = {
                initiative.identifier
                for initiative in self.initiatives
                if initiative.identifier
            }
            validation_context = {"valid_initiative_identifiers": input_identifiers}

        # We expect call_llm_api to return an instance of self.response_model or raise
        response: T = await call_llm_api(
            # Cast the list to the type expected by call_llm_api
            messages=cast(List[ChatCompletionMessageParam], messages),
            api_key=api_key,
            user_auth_token=user_auth_token,
            workspace_id=str(workspace_id),
            response_model=self.response_model,
            easy_response_model=self.easy_response_model,
            validation_context=validation_context,
            thread_id=thread_id,
            user_id=user_id,
            callbacks=callbacks,
        )

        return response


class InitiativePrompt(Prompt):
    """
    Class representing an AI prompt specifically for initiatives.

    Attributes:
        initiatives (List[Initiative]): The initiative objects
        messages (Optional[List[ChatMessage]]): The conversation messages.
        additional_context (str): Any additional context to include
    """

    system_prompt_template = "initiative/initiative_edit.jinja"
    mode: ChatMode = ChatMode.EDIT
    response_model = InitiativeLLMResponse
    easy_response_model = EasyInitiativeLLMResponse

    def __init__(
        self,
        initiatives: List[PydanticInitiative],  # Updated type hint
        messages: Optional[List[ChatMessageInput]] = None,
        additional_context: Optional[str] = None,
    ):
        self.initiatives = initiatives
        self.messages = messages
        self.additional_context = additional_context
        # No call to super().__init__() needed as Prompt doesn't define it
        # and we are setting attributes directly.

    def render_system_content(self) -> str:
        """
        Renders the system prompt content using the initiative template.

        Returns:
            str: The content for the system message.

        Raises:
            FileNotFoundError: If the template file doesn't exist
            jinja2.exceptions.TemplateError: If there's an error rendering the template
        """
        template_path = get_template_full_path(self.system_prompt_template)

        try:
            template_dir = os.path.dirname(template_path)
            template_file = os.path.basename(template_path)

            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir),
                autoescape=jinja2.select_autoescape(["txt"], default_for_string=True),
            )
            template = env.get_template(template_file)

            # Convert initiative to a dictionary for template rendering
            initiatives_data = [
                {
                    "id": str(initiative.id),
                    "identifier": initiative.identifier,  # Added identifier
                    "title": initiative.title,
                    "description": initiative.description,
                    "status": (
                        initiative.status if initiative.status else None
                    ),  # Ensure enum value is passed
                    "type": (
                        initiative.type if initiative.type else None
                    ),  # Ensure enum value is passed
                    "created_at": (
                        initiative.created_at.isoformat()
                        if initiative.created_at
                        else None
                    ),  # Format date
                    "updated_at": (
                        initiative.updated_at.isoformat()
                        if initiative.updated_at
                        else None
                    ),  # Format date
                    "tasks": [
                        {
                            "id": str(task.id),
                            "identifier": task.identifier,
                            "title": task.title,
                            "description": task.description,
                            "status": task.status if task.status else None,
                            "type": task.type if task.type else None,
                        }
                        for task in initiative.tasks  # Assuming tasks are loaded
                    ],
                }
                for initiative in self.initiatives
            ]

            return template.render(
                initiatives=initiatives_data,
                additional_context=self.additional_context,
            )

        except (FileNotFoundError, jinja2.exceptions.TemplateError) as e:
            # Log the error (You may want to use a proper logging system)
            print(f"Error rendering initiative template: {str(e)}")
            raise


class DiscussInitiativePrompt(InitiativePrompt):
    system_prompt_template = "initiative/initiative_discuss.jinja"
    mode: ChatMode = ChatMode.DISCUSS
    response_model = DiscussResponseModel
    easy_response_model = EasyDiscussResponseModel


class TaskPrompt(Prompt):
    """
    Class representing an AI prompt specifically for tasks.

    Attributes:
        tasks (List[Task]): The task objects (or context for MANAGE)
        initiative (Optional[Initiative]): The related initiative.
        messages (Optional[List[ChatMessage]]): The conversation messages.
        additional_context (str): Any additional context to include
    """

    system_prompt_template = "task/task_edit.jinja"
    mode: ChatMode = ChatMode.EDIT
    response_model = TaskLLMResponse
    easy_response_model = EasyTaskLLMResponse

    def __init__(
        self,
        tasks: List[PydanticTask],  # Updated type hint
        initiative: Optional[Initiative],  # Keep SQLAlchemy Initiative for context
        messages: Optional[List[ChatMessageInput]] = None,
        additional_context: Optional[str] = None,
    ):
        self.tasks = tasks
        self.initiative = initiative  # Store the SQLAlchemy Initiative context
        self.messages = messages
        self.additional_context = additional_context
        # No call to super().__init__() needed

    def render_system_content(self) -> str:
        """
        Renders the system prompt content using the task template.

        Returns:
            str: The content for the system message.

        Raises:
            FileNotFoundError: If the template file doesn't exist
            jinja2.exceptions.TemplateError: If there's an error rendering the template
        """
        template_path = get_template_full_path(self.system_prompt_template)

        try:
            template_dir = os.path.dirname(template_path)
            template_file = os.path.basename(template_path)

            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir),
                autoescape=jinja2.select_autoescape(["txt"], default_for_string=True),
            )
            template = env.get_template(template_file)

            # Prepare context data for the template
            task_data = [
                {
                    "id": str(task.id),
                    "identifier": task.identifier,
                    "title": task.title,
                    "description": task.description,
                    "status": (
                        task.status if task.status else None
                    ),  # Ensure enum value
                    "type": task.type if task.type else None,  # Ensure enum value
                    "checklist": [
                        {"title": item.title, "is_complete": item.is_complete}
                        for item in task.checklist  # Assuming checklist is loaded
                    ],
                    "created_at": (
                        task.created_at.isoformat() if task.created_at else None
                    ),  # Format date
                    "updated_at": (
                        task.updated_at.isoformat() if task.updated_at else None
                    ),  # Format date
                }
                for task in self.tasks
            ]

            initiative_data = None
            if self.initiative:
                initiative_data = {
                    "identifier": self.initiative.identifier,
                    "title": self.initiative.title,
                    "description": self.initiative.description,
                }

            return template.render(
                tasks=task_data,
                initiative=initiative_data,
                additional_context=self.additional_context,
            )

        except (FileNotFoundError, jinja2.exceptions.TemplateError) as e:
            print(f"Error rendering task template '{template_path}': {str(e)}")
            raise


class DiscussTaskPrompt(TaskPrompt):
    system_prompt_template = "task/task_discuss.jinja"

    mode: ChatMode = ChatMode.DISCUSS
    response_model = DiscussResponseModel
    easy_response_model = DiscussResponseModel


def get_template_full_path(path: str) -> str:
    """
    Get the template path for a specific entity type.

    Args:
        entity_type (str): The type of entity ("initiative" or "task")

    Returns:
        str: The path to the template file

    Raises:
        ValueError: If the entity_type is not "initiative" or "task"
    """

    # Base directory for templates
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "templates", "prompts", path
    )

    # Ensure this template file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template file not found: {path}")

    return path


def get_template_path_for_entity(entity_type: str, mode: ChatMode) -> str:
    """
    Get the template path for a specific entity type.

    Args:
        entity_type (str): The type of entity ("initiative" or "task")

    Returns:
        str: The path to the template file

    Raises:
        ValueError: If the entity_type is not "initiative" or "task"
    """
    if entity_type not in ["initiative", "task"]:
        raise ValueError(
            f"Entity type must be 'initiative' or 'task', got '{entity_type}'"
        )

    # Base directory for templates
    base_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "templates", "prompts", entity_type
    )

    # Always use the base template
    template_file = f"{entity_type}_{mode.value.lower()}.jinja"
    template_full_path = os.path.join(base_dir, template_file)

    # Ensure this template file exists
    if not os.path.exists(template_full_path):
        raise FileNotFoundError(f"Template file not found: {template_full_path}")

    return template_full_path
