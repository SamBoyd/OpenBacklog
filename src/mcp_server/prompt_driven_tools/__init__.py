"""Prompt-driven collaboration tools for strategic planning.

This package provides framework-based MCP tools that enable Claude Code
to guide users through strategic planning via natural conversation, rather
than rigid wizards or CRUD operations.

Pattern: Get Framework → Claude + User Collaborate → Submit Result
"""

from src.mcp_server.prompt_driven_tools.strategic_foundation import *

__all__ = [
    "get_vision_definition_framework",
    "submit_product_vision",
    "get_pillar_definition_framework",
    "submit_strategic_pillar",
    "get_outcome_definition_framework",
    "submit_product_outcome",
]
