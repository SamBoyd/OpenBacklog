# src/mcp_server/main.py
import logging

from fastmcp.server import FastMCP
from mcp.server.fastmcp import Icon

from src.config import settings
from src.mcp_server.auth_factory import get_mcp_auth_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize authentication using the auth factory
auth_factory = get_mcp_auth_factory()
auth_provider, well_known_routes, mcp_auth_context_provider = auth_factory.initialize()

# Initialize FastMCP with OAuth authentication
mcp = FastMCP(
    name="OpenBacklog MCP server",
    auth=auth_provider,
    website_url="https://openbacklog.ai",
    icons=[
        Icon(
            src="https://www.openbacklog.ai/assets/ob_v2_64x64.png",
            mimeType="image/png",
        ),
    ],
)

from src.mcp_server.healthcheck_tool import *
from src.mcp_server.onboarding_prompts import *
from src.mcp_server.prompt_driven_tools import *
from src.mcp_server.slash_commands import *

# Import all tool modules to register them with the MCP server
from src.mcp_server.start_openbacklog_workflow import *
from src.mcp_server.strategic_context_resource import *
from src.mcp_server.task_tools import *
from src.mcp_server.workspace_tools import *

if __name__ == "__main__":
    # Run with HTTP transport for hosted MCP server
    mcp.run(
        transport="http",
        host="0.0.0.0",  # nosec
        port=9000,
    )
