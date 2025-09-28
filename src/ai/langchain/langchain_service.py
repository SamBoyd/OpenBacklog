import logging
import os
from datetime import datetime
from typing import Generic, List, Optional, Type, TypedDict, TypeVar

from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    sentry_operation_tracking,
    track_ai_metrics,
)

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.store.base import BaseStore
from langgraph.store.postgres import PostgresStore
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from src.ai.langchain.internal_tools import get_all_internal_tools
from src.ai.langchain.mcp_client import get_mcp_tools
from src.ai.langchain.memory import (
    ProjectProfile,
    get_memory_tools,
    get_store_manager,
    get_summarization_node,
    initialize_project_profile,
    retrieve_project_profile,
    sanitize_memory_namespace,
)
from src.ai.langchain.response_builder import ResponseBuilder
from src.ai.langchain.tool_callback_handler import ToolCallbackHandler
from src.ai.langchain.utils import convert_openai_message_to_langchain_message
from src.ai.models import (
    EasyDiscussResponseModel,
    EasyInitiativeLLMResponse,
    EasyLLMResponse,
    EasyTaskLLMResponse,
    SimpleLLMResponse,
)
from src.config import settings

logger = logging.getLogger(__name__)

# logger.setLevel(logging.DEBUG)

# Setup LangSmith tracing
os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing)
os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key


T = TypeVar("T", bound=BaseModel)

checkpointer = InMemorySaver()


class State(Generic[T], TypedDict):
    messages: List[BaseMessage]
    project_profile: ProjectProfile


def create_initial_state(
    store: BaseStore, messages: List[BaseMessage], workspace_id: str, llm: BaseChatModel
) -> State:
    project_profile: ProjectProfile = retrieve_project_profile(store, workspace_id, llm)

    logger.info(f"Found project profile: {project_profile}")
    return State(messages=messages, project_profile=project_profile)


async def call_llm_api(
    messages: List[ChatCompletionMessageParam],
    api_key: str,
    user_auth_token: str,
    workspace_id: str,
    response_model: Type[T],
    easy_response_model: Type[EasyLLMResponse],
    thread_id: str,
    user_id: str,
    validation_context: Optional[dict] = None,
    callbacks: Optional[List] = None,
) -> T:
    # Start monitoring this LangChain operation
    add_breadcrumb(
        f"Starting LangChain LLM API call for user {user_id}",
        category="ai.langchain",
        data={
            "thread_id": thread_id,
            "workspace_id": workspace_id,
            "message_count": len(messages),
            "response_model": response_model.__name__ if response_model else None,
            "easy_response_model": (
                easy_response_model.__name__ if easy_response_model else None
            ),
        },
    )

    # Track metrics
    track_ai_metrics(
        "ai.langchain.llm_call.started",
        1,
        tags={
            "workspace_id": workspace_id,
            "response_model": response_model.__name__ if response_model else "unknown",
        },
    )

    operation_start_time = datetime.now()

    if not api_key or api_key == "":
        add_breadcrumb(
            "LLM API call failed: missing API key",
            category="ai.langchain",
            level="error",
        )
        track_ai_metrics(
            "ai.langchain.llm_call.validation_error",
            1,
            tags={"error": "missing_api_key"},
        )
        raise ValueError("API key must be provided to call the LLM API")

    if len(messages) == 0:
        add_breadcrumb(
            "LLM API call failed: no messages provided",
            category="ai.langchain",
            level="error",
        )
        track_ai_metrics(
            "ai.langchain.llm_call.validation_error", 1, tags={"error": "no_messages"}
        )
        raise ValueError("Messages must be provided to call the LLM API")

    if not response_model:
        add_breadcrumb(
            "LLM API call failed: no response model",
            category="ai.langchain",
            level="error",
        )
        track_ai_metrics(
            "ai.langchain.llm_call.validation_error",
            1,
            tags={"error": "no_response_model"},
        )
        raise ValueError("Response model must be provided to call the LLM API")

    # Convert OpenAI message format to LangChain message format

    # Get the last message from the user
    def get_last_user_message(
        messages: List[ChatCompletionMessageParam],
    ) -> ChatCompletionMessageParam:
        if len(messages) == 0:
            raise ValueError("Messages must be provided to get the last user message")

        for msg in reversed(messages):
            if msg["role"] == "user":
                return msg

        return get_last_user_message(messages[:-1])

    # Convert the messages to LangChain messages
    langchain_messages = []
    for msg in messages:
        langchain_messages.append(convert_openai_message_to_langchain_message(msg))

    chatbot = init_chat_model(
        settings.llm_model,
        api_key=api_key,
        model_provider="openai",
        temperature=0.4,
        base_url=settings.litellm_url,
        model_kwargs={
            "user": user_id,
        },
    )

    os.environ["TAVILY_API_KEY"] = settings.tavily_api_key

    search_tool = TavilySearch(max_results=2)
    # mcp_tools = await get_mcp_tools(user_auth_token, workspace_id)
    memory_tools = get_memory_tools(workspace_id)

    add_breadcrumb("Connecting to PostgreSQL memory store", category="ai.langchain")

    try:
        with PostgresStore.from_conn_string(settings.memory_database_url) as store:
            add_breadcrumb(
                "PostgreSQL store connection established", category="ai.langchain"
            )

            try:
                store.setup()
                add_breadcrumb(
                    "PostgreSQL store setup completed", category="ai.langchain"
                )
            except Exception as e:
                add_breadcrumb(
                    "PostgreSQL store setup failed",
                    category="ai.langchain",
                    level="error",
                    data={"error": str(e)},
                )
                track_ai_metrics(
                    "ai.langchain.memory_store.setup_error",
                    1,
                    tags={"workspace_id": workspace_id},
                )
                raise

            try:
                initialize_project_profile(store, workspace_id, chatbot)
                add_breadcrumb("Project profile initialized", category="ai.langchain")
            except Exception as e:
                add_breadcrumb(
                    "Project profile initialization failed",
                    category="ai.langchain",
                    level="warning",
                    data={"error": str(e)},
                )
                track_ai_metrics(
                    "ai.langchain.project_profile.init_error",
                    1,
                    tags={"workspace_id": workspace_id},
                )
                # Continue execution as this is not critical

            # Log current contents of the workspace memory namespace before any LLM calls
            try:
                ns = ("memories", workspace_id, "semantic")
                stored_items = store.search(ns, limit=50)
                add_breadcrumb(
                    f"Found {len(stored_items)} memory items in workspace",
                    category="ai.langchain",
                    data={"memory_count": len(stored_items)},
                )
                track_ai_metrics(
                    "ai.langchain.memory_items.count",
                    len(stored_items),
                    tags={"workspace_id": workspace_id},
                )

                logger.debug(
                    "[call_llm_api] Workspace %s memory items BEFORE llm invoke: %s",
                    workspace_id,
                    [(item.key, item.value) for item in stored_items],
                )
            except Exception as e:
                logger.warning(
                    "[call_llm_api] Failed to log memory items before llm invoke for workspace %s: %s",
                    workspace_id,
                    e,
                )
                add_breadcrumb(
                    "Failed to retrieve memory items",
                    category="ai.langchain",
                    level="warning",
                    data={"error": str(e)},
                )
                track_ai_metrics(
                    "ai.langchain.memory_items.retrieval_error",
                    1,
                    tags={"workspace_id": workspace_id},
                )

        # Initial state with messages
        initial_state = create_initial_state(
            store, langchain_messages, workspace_id, chatbot
        )

        # Combine default tool callback handler with any additional callbacks
        all_callbacks = [tool_callback_handler]
        if callbacks:
            all_callbacks.extend(callbacks)

        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
                "workspace_id": workspace_id,
            },
            "callbacks": all_callbacks,
        }

        logger.debug(f"Invoking the graph with config: {config}")

        # Invoke the graph
        result = llm.invoke(
            initial_state,
            config=config,
        )

        # The result should contain the simple LLM response
        if result["structured_response"] is None:
            raise ValueError("Failed to extract structured output from model response")

        simple_response = result["structured_response"]

        logger.debug(
            "[call_llm_api] LLM graph invocation finished for workspace %s. Raw result keys: %s",
            workspace_id,
            list(result.keys()),
        )

        # Ensure all memory values are wrapped with 'kind' to avoid KeyError
        sanitize_memory_namespace(store, workspace_id)

        memory_manager = get_store_manager(chatbot, workspace_id, store)

        # Log memory items just before running memory_manager.invoke
        try:
            pre_mm_items = store.search(
                ("memories", workspace_id, "semantic"), limit=50
            )
            logger.debug(
                "[call_llm_api] Memory items BEFORE memory_manager.invoke for workspace %s: %s",
                workspace_id,
                [(item.key, item.value) for item in pre_mm_items],
            )
        except Exception as e:
            logger.warning(
                "[call_llm_api] Failed to log memory items before memory_manager.invoke for workspace %s: %s",
                workspace_id,
                e,
            )

        memory_manager.invoke(
            input={"messages": langchain_messages, "max_steps": 1},
            config=config,
        )

        # Log memory items after memory manager
        try:
            post_mm_items = store.search(
                ("memories", workspace_id, "semantic"), limit=50
            )
            logger.debug(
                "[call_llm_api] Memory items AFTER memory_manager.invoke for workspace %s: %s",
                workspace_id,
                [(item.key, item.value) for item in post_mm_items],
            )
        except Exception as e:
            logger.warning(
                "[call_llm_api] Failed to log memory items after memory_manager.invoke for workspace %s: %s",
                workspace_id,
                e,
            )

        # Build structured response from tool operations
        response_builder = ResponseBuilder()

        task_operations = tool_callback_handler.get_task_operations()
        logger.debug("Found %s task operations", len(task_operations))

        initiative_operations = tool_callback_handler.get_initiative_operations()
        logger.debug("Found %s initiative operations", len(initiative_operations))

        # Determine response type based on easy_response_model
        if easy_response_model == EasyInitiativeLLMResponse:
            structured_response = response_builder.build_initiative_response(
                message=simple_response.message,
                operations=initiative_operations,
                task_operations=task_operations,
                balance_warning=(
                    validation_context.get("balance_warning")
                    if validation_context
                    else None
                ),
            )
        elif (
            easy_response_model == EasyDiscussResponseModel
        ):  # pyright: ignore[reportUnnecessaryComparison]
            structured_response = response_builder.build_discuss_response(
                message=simple_response.message,
                balance_warning=(
                    validation_context.get("balance_warning")
                    if validation_context
                    else None
                ),
            )
        else:
            # Default to task response
            structured_response = response_builder.build_task_response(
                message=simple_response.message,
                operations=task_operations,
                balance_warning=(
                    validation_context.get("balance_warning")
                    if validation_context
                    else None
                ),
            )

        # Clear operations from callback handler
        tool_callback_handler.clear_operations()

        logger.debug(
            f"Structured response built from operations: {structured_response}"
        )

        return structured_response.to_managed_model()

    except Exception as e:
        add_breadcrumb(
            "PostgreSQL store connection failed",
            category="ai.langchain",
            level="error",
            data={"error": str(e)},
        )
        track_ai_metrics(
            "ai.langchain.memory_store.connection_error",
            1,
            tags={"workspace_id": workspace_id},
        )

        # Capture this as a critical error
        capture_ai_exception(
            e,
            operation_type="langchain_memory_store_connection",
            extra_context={
                "workspace_id": workspace_id,
                "user_id": user_id,
                "database_url": (
                    settings.memory_database_url[:50] + "..."
                    if len(settings.memory_database_url) > 50
                    else settings.memory_database_url
                ),
            },
        )
