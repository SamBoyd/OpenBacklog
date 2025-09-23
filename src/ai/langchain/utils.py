from typing import Type, TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def convert_openai_message_to_langchain_message(
    message: ChatCompletionMessageParam,
) -> BaseMessage:
    content = message.get("content", "")

    # Convert complex content to string if needed
    if not isinstance(content, str):
        content = str(content) if content else ""

    role = message.get("role", "")

    if role == "system":
        return SystemMessage(content=content)
    elif role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    else:
        raise ValueError(f"Invalid role: {role}")


def extract_structured_output(state, response_model: Type[T]):
    """Process the output message to extract the structured output"""
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Get the first tool call and parse it
        tool_call = last_message.tool_calls[0]
        structured_result = response_model.model_validate(tool_call["args"])
        return {"messages": state["messages"], "response": structured_result}

    # If no tool call is found, return the original state
    return state
