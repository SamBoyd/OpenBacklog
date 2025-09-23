from typing import Any, List, Optional

from langchain_core.output_parsers import PydanticToolsParser
from pydantic import BaseModel


class ContextAwarePydanticToolsParser(PydanticToolsParser):

    def __init__(
        self,
        tools: List[Any],
        first_tool_only: bool,
        validation_context: Optional[dict] = None,
    ):
        super().__init__()  # type: ignore
        self.validation_context = validation_context
        self.tools = tools
        self.first_tool_only = first_tool_only

    def parse(self, text: str) -> Any:
        # Parse the output to JSON using the parent class method
        parsed_json = super().parse(text)

        # If this is a list with a single item and first_tool_only is True
        if (
            self.first_tool_only
            and isinstance(parsed_json, list)
            and len(parsed_json) > 0
        ):
            # Get the correct object type from tools
            for tool in self.tools:
                if tool.__name__ == parsed_json[0]["type"]:
                    # Use model_validate with context
                    return tool.model_validate(
                        parsed_json[0]["args"], context=self.validation_context
                    )
            return parsed_json[0]["args"]  # Fallback if tool not found

        # Handle the case where first_tool_only is False (returns a list)
        result = []
        for item in parsed_json:
            for tool in self.tools:
                if tool.__name__ == item["type"]:
                    # Use model_validate with context
                    validated_item = tool.model_validate(
                        item["args"], context=self.validation_context
                    )
                    result.append(validated_item)
                    break
            else:
                # If no matching tool is found, just append the args
                result.append(item["args"])

        return result
