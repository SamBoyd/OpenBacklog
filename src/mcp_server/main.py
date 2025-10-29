# src/ai/mcp_server.py
import logging

from fastmcp.server import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp: FastMCP = FastMCP(name="OpenBacklog MCP server")  # type: ignore

from src.mcp_server.checklist_tools import *
from src.mcp_server.healthcheck_tool import *
from src.mcp_server.initiative_tools import *
from src.mcp_server.prompt_driven_tools import *
from src.mcp_server.slash_commands import *

# Import all tool modules to register them with the MCP server
from src.mcp_server.start_openbacklog_workflow import *
from src.mcp_server.task_tools import *

# http_app = mcp.http_app(path="/mcp")

if __name__ == "__main__":
    # Run with HTTP transport for hosted MCP server
    mcp.run(
        transport="http",
        host="0.0.0.0",  # nosec
        port=9000,
    )
