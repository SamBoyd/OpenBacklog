import logging
import os
import time
from typing import Any, Generic, List, Optional, Type, TypedDict, TypeVar

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
    SimpleLLMResponse,
)
from src.config import settings
from src.monitoring.sentry_helpers import (
    add_breadcrumb,
    capture_ai_exception,
    set_operation_context,
    track_ai_metrics,
)

logger = logging.getLogger(__name__)

# logger.setLevel(logging.DEBUG)

# Setup LangSmith tracing
os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing)
os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key


T = TypeVar("T", bound=BaseModel)

checkpointer = InMemorySaver()


# MCP tool filtering configuration
# Tools that are safe to expose to the agent for search/lookup operations
ALLOWED_MCP_TOOLS = {
    "search_tasks",
    "search_initiatives",
    "get_task_details",
    "get_initiative_tasks",
    "get_initiative_details",
}


def filter_mcp_tools(mcp_tools: List[Any]) -> List[Any]:
    """
    Filter MCP tools to only expose search/lookup tools.

    This prevents conflicts with internal CRUD tools and ensures
    the agent uses MCP tools only for searching entities not in context.

    Args:
        mcp_tools: List of all MCP tools from the server

    Returns:
        Filtered list containing only allowed search/lookup tools
    """
    filtered = []
    for tool in mcp_tools:
        tool_name = getattr(tool, "name", None)
        if tool_name in ALLOWED_MCP_TOOLS:
            filtered.append(tool)
            logger.debug(f"Including MCP tool: {tool_name}")
        else:
            logger.debug(f"Filtering out MCP tool: {tool_name}")

    logger.info(f"Filtered {len(filtered)} MCP tools from {len(mcp_tools)} total")
    return filtered


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
    # Set up Sentry context for this LLM API call
    operation_details = {
        "workspace_id": workspace_id,
        "thread_id": thread_id,
        "user_id": user_id,
        "response_model": response_model.__name__ if response_model else None,
        "easy_response_model": (
            easy_response_model.__name__ if easy_response_model else None
        ),
        "message_count": len(messages),
        "has_validation_context": bool(validation_context),
        "has_callbacks": bool(callbacks),
    }

    set_operation_context("llm_api_call", details=operation_details)

    add_breadcrumb(
        f"Starting LLM API call for workspace {workspace_id}",
        category="ai.langchain",
        data=operation_details,
    )

    # Track start metrics
    track_ai_metrics(
        "langchain.api_call.started",
        1,
        tags={
            "workspace_id": workspace_id,
            "response_type": (
                easy_response_model.__name__ if easy_response_model else "unknown"
            ),
        },
    )

    # Input validation with enhanced error context
    try:
        if not api_key or api_key == "":
            raise ValueError("API key must be provided to call the LLM API")

        if len(messages) == 0:
            raise ValueError("Messages must be provided to call the LLM API")

        add_breadcrumb(
            "Input validation completed successfully", category="ai.langchain"
        )

    except ValueError as e:
        track_ai_metrics(
            "langchain.api_call.validation_error",
            1,
            tags={"workspace_id": workspace_id, "error_type": "input_validation"},
        )
        capture_ai_exception(
            e,
            operation_type="llm_api_call",
            extra_context={"validation_stage": "input_validation", **operation_details},
        )
        raise

    # Convert OpenAI message format to LangChain message format
    add_breadcrumb("Starting message conversion", category="ai.langchain")

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
    try:
        langchain_messages = []
        for msg in messages:
            langchain_messages.append(convert_openai_message_to_langchain_message(msg))

        add_breadcrumb(
            f"Converted {len(langchain_messages)} messages to LangChain format",
            category="ai.langchain",
            data={"message_count": len(langchain_messages)},
        )
    except Exception as e:
        track_ai_metrics(
            "langchain.api_call.message_conversion_error",
            1,
            tags={"workspace_id": workspace_id},
        )
        capture_ai_exception(
            e,
            operation_type="llm_api_call",
            extra_context={
                "conversion_stage": "message_conversion",
                **operation_details,
            },
        )
        raise

    # Initialize chatbot model
    add_breadcrumb("Initializing chatbot model", category="ai.langchain")
    try:
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
        add_breadcrumb(
            f"Chatbot model initialized: {settings.llm_model}",
            category="ai.langchain",
            data={"model": settings.llm_model, "base_url": settings.litellm_url},
        )
    except Exception as e:
        track_ai_metrics(
            "langchain.api_call.model_init_error",
            1,
            tags={"workspace_id": workspace_id, "model": settings.llm_model},
        )
        capture_ai_exception(
            e,
            operation_type="llm_api_call",
            extra_context={
                "initialization_stage": "chatbot_model",
                **operation_details,
            },
        )
        raise

    # Initialize tools
    add_breadcrumb("Initializing tools", category="ai.langchain")
    try:
        os.environ["TAVILY_API_KEY"] = settings.tavily_api_key
        search_tool = TavilySearch(max_results=2)

        # Get and filter MCP tools for search/lookup operations
        # If MCP tools fail to load, continue without them (graceful degradation)
        mcp_search_tools = []
        try:
            add_breadcrumb("Fetching MCP tools", category="ai.langchain")
            all_mcp_tools = await get_mcp_tools(user_auth_token, workspace_id)
            mcp_search_tools = filter_mcp_tools(all_mcp_tools)
            add_breadcrumb(
                f"Successfully loaded {len(mcp_search_tools)} MCP search tools",
                category="ai.langchain",
            )
        except Exception as mcp_error:
            logger.warning(
                f"Failed to load MCP tools for workspace {workspace_id}, continuing without them: {mcp_error}"
            )
            add_breadcrumb(
                "MCP tools failed to load, continuing without search tools",
                category="ai.langchain",
                level="warning",
                data={"error": str(mcp_error)},
            )
            track_ai_metrics(
                "langchain.api_call.mcp_tools_error",
                1,
                tags={"workspace_id": workspace_id},
            )
            # Don't raise - allow operation to continue without MCP tools

        memory_tools = get_memory_tools(workspace_id)

        add_breadcrumb(
            "Tools initialized successfully",
            category="ai.langchain",
            data={
                "search_tool": "TavilySearch",
                "mcp_tools_count": len(mcp_search_tools),
                "memory_tools_count": len(memory_tools),
            },
        )
    except Exception as e:
        track_ai_metrics(
            "langchain.api_call.tool_init_error",
            1,
            tags={"workspace_id": workspace_id},
        )
        capture_ai_exception(
            e,
            operation_type="llm_api_call",
            extra_context={"initialization_stage": "tools", **operation_details},
        )
        raise

    # Initialize memory store with enhanced error handling
    add_breadcrumb("Initializing PostgresStore", category="ai.langchain")
    with PostgresStore.from_conn_string(settings.memory_database_url) as store:
        store.setup()
        add_breadcrumb("PostgresStore setup completed", category="ai.langchain")

        # Initialize project profile
        add_breadcrumb("Initializing project profile", category="ai.langchain")
        initialize_project_profile(store, workspace_id, chatbot)
        add_breadcrumb("Project profile initialized", category="ai.langchain")

        # Log current contents of the workspace memory namespace before any LLM calls
        add_breadcrumb(
            "Inspecting memory contents before LLM call", category="ai.langchain"
        )
        try:
            ns = ("memories", workspace_id, "semantic")
            stored_items = store.search(ns, limit=50)
            memory_item_count = len(stored_items)

            add_breadcrumb(
                f"Found {memory_item_count} memory items before LLM invoke",
                category="ai.langchain",
                data={
                    "memory_item_count": memory_item_count,
                    "workspace_id": workspace_id,
                },
            )

            logger.debug(
                "[call_llm_api] Workspace %s memory items BEFORE llm invoke: %s",
                workspace_id,
                [(item.key, item.value) for item in stored_items],
            )
        except Exception as e:
            track_ai_metrics(
                "langchain.api_call.memory_inspection_error",
                1,
                tags={"workspace_id": workspace_id, "stage": "before_llm"},
            )
            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={
                    "memory_stage": "pre_llm_inspection",
                    **operation_details,
                },
            )
            logger.warning(
                "[call_llm_api] Failed to log memory items before llm invoke for workspace %s: %s",
                workspace_id,
                e,
            )

        # Get internal CRUD tools (only for Edit mode, not Discuss mode)
        add_breadcrumb("Getting internal CRUD tools", category="ai.langchain")
        # In Discuss mode, exclude CRUD tools - agent should only provide commentary
        internal_tools = (
            []
            if easy_response_model == EasyDiscussResponseModel
            else get_all_internal_tools()
        )

        # Create callback handler for tracking tool operations
        add_breadcrumb("Creating tool callback handler", category="ai.langchain")
        tool_callback_handler = ToolCallbackHandler()

        # Combine all tools for the agent
        # MCP search tools are available in both EDIT and DISCUSS modes
        # Internal CRUD tools are only available in EDIT mode
        all_agent_tools = (
            [search_tool] + memory_tools + mcp_search_tools + internal_tools
        )

        add_breadcrumb(
            "Assembled agent tools",
            category="ai.langchain",
            data={
                "total_tools": len(all_agent_tools),
                "mcp_tools": len(mcp_search_tools),
                "internal_tools": len(internal_tools),
                "memory_tools": len(memory_tools),
            },
        )

        # Initialize the LLM with simple response format and all tools
        add_breadcrumb("Creating react agent", category="ai.langchain")
        try:
            llm = create_react_agent(
                model=chatbot,
                tools=all_agent_tools,
                response_format=SimpleLLMResponse,
                store=store,
                checkpointer=checkpointer,
                pre_model_hook=get_summarization_node(chatbot),
            )
        except Exception as e:
            track_ai_metrics(
                "langchain.api_call.agent_creation_error",
                1,
                tags={"workspace_id": workspace_id},
            )
            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={
                    "creation_stage": "react_agent",
                    **operation_details,
                },
            )
            raise

        # Initial state with messages
        add_breadcrumb("Creating initial state", category="ai.langchain")
        try:
            initial_state = create_initial_state(
                store, langchain_messages, workspace_id, chatbot
            )
        except Exception as e:
            track_ai_metrics(
                "langchain.api_call.state_creation_error",
                1,
                tags={"workspace_id": workspace_id},
            )
            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={
                    "creation_stage": "initial_state",
                    **operation_details,
                },
            )
            raise

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

        # Invoke the graph with timing
        add_breadcrumb("Starting LLM graph invocation", category="ai.langchain")
        llm_invoke_start = time.time()

        try:
            result = llm.invoke(
                initial_state,
                config=config,
            )

            llm_invoke_duration = (time.time() - llm_invoke_start) * 1000
            add_breadcrumb(
                f"LLM graph invocation completed in {llm_invoke_duration:.2f}ms",
                category="ai.langchain",
                data={"duration_ms": llm_invoke_duration},
            )

            track_ai_metrics(
                "langchain.api_call.llm_invoke_duration",
                llm_invoke_duration,
                tags={"workspace_id": workspace_id},
                unit="ms",
            )

        except Exception as e:
            llm_invoke_duration = (time.time() - llm_invoke_start) * 1000
            add_breadcrumb(
                f"LLM graph invocation failed after {llm_invoke_duration:.2f}ms",
                category="ai.langchain",
                level="error",
                data={"duration_ms": llm_invoke_duration, "error": str(e)},
            )

            track_ai_metrics(
                "langchain.api_call.llm_invoke_error",
                1,
                tags={"workspace_id": workspace_id, "error_type": type(e).__name__},
            )

            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={"invoke_stage": "llm_graph", **operation_details},
            )
            raise

        # The result should contain the simple LLM response
        add_breadcrumb("Validating LLM response", category="ai.langchain")
        if result["structured_response"] is None:
            track_ai_metrics(
                "langchain.api_call.response_extraction_error",
                1,
                tags={"workspace_id": workspace_id},
            )
            error = ValueError(
                "Failed to extract structured output from model response"
            )
            capture_ai_exception(
                error,
                operation_type="llm_api_call",
                extra_context={
                    "validation_stage": "response_extraction",
                    **operation_details,
                },
            )
            raise error

        simple_response = result["structured_response"]

        add_breadcrumb("LLM response extracted successfully", category="ai.langchain")
        logger.debug(
            "[call_llm_api] LLM graph invocation finished for workspace %s. Raw result keys: %s",
            workspace_id,
            list(result.keys()),
        )

        # Ensure all memory values are wrapped with 'kind' to avoid KeyError
        add_breadcrumb("Sanitizing memory namespace", category="ai.langchain")
        try:
            sanitize_memory_namespace(store, workspace_id)
        except Exception as e:
            track_ai_metrics(
                "langchain.api_call.memory_sanitization_error",
                1,
                tags={"workspace_id": workspace_id},
            )
            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={"memory_stage": "sanitization", **operation_details},
            )
            raise

        add_breadcrumb("Getting memory store manager", category="ai.langchain")
        try:
            memory_manager = get_store_manager(chatbot, workspace_id, store)
        except Exception as e:
            track_ai_metrics(
                "langchain.api_call.memory_manager_creation_error",
                1,
                tags={"workspace_id": workspace_id},
            )
            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={
                    "memory_stage": "manager_creation",
                    **operation_details,
                },
            )
            raise

        # Log memory items just before running memory_manager.invoke
        add_breadcrumb(
            "Inspecting memory before memory manager invoke",
            category="ai.langchain",
        )
        try:
            pre_mm_items = store.search(
                ("memories", workspace_id, "semantic"), limit=50
            )
            pre_mm_count = len(pre_mm_items)

            add_breadcrumb(
                f"Found {pre_mm_count} memory items before memory manager invoke",
                category="ai.langchain",
                data={"pre_memory_count": pre_mm_count},
            )

            logger.debug(
                "[call_llm_api] Memory items BEFORE memory_manager.invoke for workspace %s: %s",
                workspace_id,
                [(item.key, item.value) for item in pre_mm_items],
            )
        except Exception as e:
            track_ai_metrics(
                "langchain.api_call.memory_inspection_error",
                1,
                tags={
                    "workspace_id": workspace_id,
                    "stage": "before_memory_manager",
                },
            )
            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={
                    "memory_stage": "pre_manager_inspection",
                    **operation_details,
                },
            )

        # Invoke memory manager with timing
        add_breadcrumb("Starting memory manager invoke", category="ai.langchain")
        memory_manager_start = time.time()

        try:
            memory_manager.invoke(
                input={"messages": langchain_messages, "max_steps": 1},
                config=config,
            )

            memory_manager_duration = (time.time() - memory_manager_start) * 1000
            add_breadcrumb(
                f"Memory manager completed in {memory_manager_duration:.2f}ms",
                category="ai.langchain",
                data={"duration_ms": memory_manager_duration},
            )

            track_ai_metrics(
                "langchain.api_call.memory_manager_duration",
                memory_manager_duration,
                tags={"workspace_id": workspace_id},
                unit="ms",
            )

        except Exception as e:
            memory_manager_duration = (time.time() - memory_manager_start) * 1000
            track_ai_metrics(
                "langchain.api_call.memory_manager_error",
                1,
                tags={"workspace_id": workspace_id, "error_type": type(e).__name__},
            )

            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={
                    "memory_stage": "manager_invoke",
                    **operation_details,
                },
            )
            raise

        # Log memory items after memory manager
        add_breadcrumb(
            "Inspecting memory after memory manager invoke", category="ai.langchain"
        )
        try:
            post_mm_items = store.search(
                ("memories", workspace_id, "semantic"), limit=50
            )
            post_mm_count = len(post_mm_items)

            add_breadcrumb(
                f"Found {post_mm_count} memory items after memory manager invoke",
                category="ai.langchain",
                data={"post_memory_count": post_mm_count},
            )

            logger.debug(
                "[call_llm_api] Memory items AFTER memory_manager.invoke for workspace %s: %s",
                workspace_id,
                [(item.key, item.value) for item in post_mm_items],
            )
        except Exception as e:
            track_ai_metrics(
                "langchain.api_call.memory_inspection_error",
                1,
                tags={
                    "workspace_id": workspace_id,
                    "stage": "after_memory_manager",
                },
            )
            capture_ai_exception(
                e,
                operation_type="llm_api_call",
                extra_context={
                    "memory_stage": "post_manager_inspection",
                    **operation_details,
                },
            )
            logger.warning(
                "[call_llm_api] Failed to log memory items after memory_manager.invoke for workspace %s: %s",
                workspace_id,
                e,
            )

    # Build structured response from tool operations
    add_breadcrumb("Building structured response", category="ai.langchain")
    try:
        response_builder = ResponseBuilder()

        task_operations = tool_callback_handler.get_task_operations()

        initiative_operations = tool_callback_handler.get_initiative_operations()

        add_breadcrumb(
            f"Retrieved operations from tool callback handler",
            category="ai.langchain",
            data={
                "task_operations_count": len(task_operations),
                "initiative_operations_count": len(initiative_operations),
            },
        )

        track_ai_metrics(
            "langchain.api_call.tool_operations",
            len(task_operations) + len(initiative_operations),
            tags={
                "workspace_id": workspace_id,
                "response_type": easy_response_model.__name__,
            },
        )

        # Determine response type based on easy_response_model
        response_build_start = time.time()

        if easy_response_model == EasyInitiativeLLMResponse:
            add_breadcrumb("Building initiative response", category="ai.langchain")
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
            add_breadcrumb("Building discuss response", category="ai.langchain")
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
            add_breadcrumb("Building task response", category="ai.langchain")
            structured_response = response_builder.build_task_response(
                message=simple_response.message,
                operations=task_operations,
                balance_warning=(
                    validation_context.get("balance_warning")
                    if validation_context
                    else None
                ),
            )

        response_build_duration = (time.time() - response_build_start) * 1000
        add_breadcrumb(
            f"Response building completed in {response_build_duration:.2f}ms",
            category="ai.langchain",
            data={"duration_ms": response_build_duration},
        )

        track_ai_metrics(
            "langchain.api_call.response_build_duration",
            response_build_duration,
            tags={
                "workspace_id": workspace_id,
                "response_type": easy_response_model.__name__,
            },
            unit="ms",
        )

        # Clear operations from callback handler
        tool_callback_handler.clear_operations()

        logger.debug(
            f"Structured response built from operations: {structured_response}"
        )

        # Track successful completion
        track_ai_metrics(
            "langchain.api_call.completed",
            1,
            tags={
                "workspace_id": workspace_id,
                "response_type": easy_response_model.__name__,
            },
        )

        add_breadcrumb("LLM API call completed successfully", category="ai.langchain")

        return structured_response.to_managed_model()

    except Exception as response_error:
        track_ai_metrics(
            "langchain.api_call.response_build_error",
            1,
            tags={
                "workspace_id": workspace_id,
                "error_type": type(response_error).__name__,
            },
        )
        capture_ai_exception(
            response_error,
            operation_type="llm_api_call",
            extra_context={
                "response_stage": "structured_response_building",
                **operation_details,
            },
        )
        raise
