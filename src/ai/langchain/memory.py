# Create profile manager
import logging
from ast import Store
from typing import Any, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.config import get_config
from langgraph.func import entrypoint
from langgraph.store.base import BaseStore, IndexConfig
from langgraph.store.memory import InMemoryStore
from langmem import (
    create_manage_memory_tool,
    create_memory_store_manager,
    create_search_memory_tool,
)
from langmem.knowledge.extraction import MemoryStoreManager
from langmem.short_term import SummarizationNode
from pydantic import BaseModel

# Store ----------------------------------------------------------------------

logger = logging.getLogger(__name__)

store = InMemoryStore()


# Project Profile ------------------------------------------------------------


class ProjectProfile(BaseModel):
    """Represents the full representation of a user."""

    model_version: int = 1

    name: Optional[str] = None
    technologies_used: Optional[List[str]] = None
    elevator_pitch: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[str] = None
    pain_points: Optional[List[str]] = None
    areas_of_interest: Optional[List[str]] = None


def get_store_manager(
    llm: BaseChatModel, workspace_id: str, store: BaseStore
) -> MemoryStoreManager:
    return create_memory_store_manager(
        llm,
        store=store,
        namespace=("memories", workspace_id, "semantic"),
        schemas=[ProjectProfile],
        enable_inserts=False,
        enable_deletes=False,
    )


def initialize_project_profile(store: BaseStore, workspace_id: str, llm: BaseChatModel):
    """Ensure there is a properly-formatted project_profile item in the store.

    The item **must** have the structure {"kind": "ProjectProfile", "content": {...}} so that
    LangMem can process it without raising a KeyError. If no item exists we create one; if an
    existing item is missing the wrapper we rewrite it in-place.
    """

    namespace = ("memories", workspace_id, "semantic")

    existing_item = store.get(namespace=namespace, key="project_profile")

    logger.debug(
        "[initialize_project_profile] Existing project_profile for workspace %s: %s",
        workspace_id,
        None if existing_item is None else existing_item.value,
    )

    # Determine if we need to write or rewrite the item
    needs_init = (
        existing_item is None
        or existing_item.value is None
        or "kind" not in existing_item.value
    )

    if needs_init:
        profile_obj = (
            existing_item.value
            if existing_item and existing_item.value
            else ProjectProfile().model_dump()
        )

        # If we detected an existing raw dict, wrap it; otherwise wrap the freshly created object.
        wrapped_value = {
            "kind": "ProjectProfile",
            "content": profile_obj if isinstance(profile_obj, dict) else profile_obj,
        }

        store.put(namespace=namespace, key="project_profile", value=wrapped_value)

        logger.debug(
            "[initialize_project_profile] Stored new wrapped project_profile for workspace %s: %s",
            workspace_id,
            wrapped_value,
        )


def retrieve_project_profile(
    store: BaseStore, workspace_id: str, llm: BaseChatModel
) -> ProjectProfile:
    """
    Retrieve the most recent project profile using MemoryStoreManager search.
    If no profile exists, return a new empty profile.
    """
    # Create a memory store manager to search for existing profiles
    memory_manager = get_store_manager(llm, workspace_id, store)

    # Search for existing project profiles
    results = memory_manager.store.get(
        namespace=("memories", workspace_id, "semantic"),
        key="project_profile",
    )

    if results and results.value:
        value = results.value
        # Handle both wrapped and legacy formats
        if isinstance(value, dict) and "content" in value:
            value = value["content"]

        logger.debug(
            "[retrieve_project_profile] Returning stored ProjectProfile for workspace %s: %s",
            workspace_id,
            value,
        )

        return ProjectProfile.model_validate(value)

    logger.debug(
        "[retrieve_project_profile] No stored profile found for workspace %s. Returning empty profile.",
        workspace_id,
    )
    return ProjectProfile()


# Tools ----------------------------------------------------------------------


def get_memory_tools(workspace_id: str) -> List[Any]:
    return [
        create_manage_memory_tool(namespace=("memories", workspace_id, "semantic")),
        create_search_memory_tool(namespace=("memories", workspace_id, "semantic")),
    ]


def get_summarization_node(
    llm: BaseChatModel,
    max_tokens: Optional[int] = None,
    max_summary_tokens: Optional[int] = None,
    max_tokens_before_summary: Optional[int] = None,
) -> SummarizationNode:
    """
    Create a summarization node with configurable token limits.

    @param llm: The language model to use for summarization
    @param max_tokens: Total tokens allowed after summarization (default: 1024)
    @param max_summary_tokens: Maximum tokens for summary content (default: 256)
    @param max_tokens_before_summary: Threshold to trigger summarization (default: 768)
    @returns: Configured SummarizationNode
    """
    configs = [
        {
            "max_tokens": 512,
            "max_summary_tokens": 128,
            "max_tokens_before_summary": 768,
        },  # Conservative
        {
            "max_tokens": 1024,
            "max_summary_tokens": 256,
            "max_tokens_before_summary": 1536,
        },  # Balanced
        {
            "max_tokens": 2048,
            "max_summary_tokens": 512,
            "max_tokens_before_summary": 3072,
        },  # Generous
    ]

    _max_tokens = max_tokens or configs[0]["max_tokens"]
    _max_summary_tokens = max_summary_tokens or configs[0]["max_summary_tokens"]
    _max_tokens_before_summary = (
        max_tokens_before_summary or configs[0]["max_tokens_before_summary"]
    )

    return SummarizationNode(
        token_counter=count_tokens_approximately,
        model=llm,
        max_tokens=_max_tokens,
        max_tokens_before_summary=_max_tokens_before_summary,
        max_summary_tokens=_max_summary_tokens,
        output_messages_key="llm_input_messages",
    )


def sanitize_memory_namespace(store: BaseStore, workspace_id: str):
    """Ensure every item in the workspace semantic namespace has a 'kind' wrapper.

    Any value that is missing the 'kind' key will be wrapped as:
        {"kind": "Memory", "content": <old_value>}
    This prevents KeyError when LangMem expects the structured format.
    """
    namespace_prefix = ("memories", workspace_id, "semantic")

    try:
        items = store.search(namespace_prefix, limit=100)
    except Exception as e:
        logger.warning(
            "[sanitize_memory_namespace] Failed to search namespace %s due to %s",
            namespace_prefix,
            e,
        )
        return

    rewritten = 0
    for item in items:
        if item.value is None or not isinstance(item.value, dict):
            continue
        if "kind" not in item.value:
            new_val = {"kind": "Memory", "content": item.value}
            store.put(namespace=item.namespace, key=item.key, value=new_val)
            rewritten += 1

    if rewritten:
        logger.debug(
            "[sanitize_memory_namespace] Wrapped %s malformed memory items for workspace %s",
            rewritten,
            workspace_id,
        )
