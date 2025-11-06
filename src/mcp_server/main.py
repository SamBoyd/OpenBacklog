# src/ai/mcp_server.py
import logging

from fastmcp.server import FastMCP
from fastmcp.server.auth.providers.auth0 import Auth0Provider

from src.config import ENV_FILE, settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Auth0 OAuth authentication
# Users authenticate via browser redirect to Auth0 login page
# Client credentials are stored server-side only (never distributed to users)
# After initial login, tokens are cached locally on the user's machine
auth_provider = Auth0Provider(
    config_url=f"https://{settings.mcp_server_auth0_domain}/.well-known/openid-configuration",
    client_id=settings.mcp_server_auth0_client_id,
    client_secret=settings.mcp_server_auth0_client_secret,
    audience=settings.mcp_server_auth0_audience,
    base_url=f"{settings.mcp_server_domain}/mcp",
    issuer_url=f"{settings.mcp_server_domain}",
    jwt_signing_key="test-hardcoded-jwt-signing-key-for-debugging-purposes-12345",
)

well_known_routes = auth_provider.get_well_known_routes(mcp_path="/mcp")

# Initialize FastMCP with OAuth authentication
mcp = FastMCP(name="OpenBacklog MCP server", auth=auth_provider)  # type: ignore

from src.mcp_server.checklist_tools import *
from src.mcp_server.healthcheck_tool import *
from src.mcp_server.initiative_tools import *
from src.mcp_server.prompt_driven_tools import *
from src.mcp_server.slash_commands import *

# Import all tool modules to register them with the MCP server
from src.mcp_server.start_openbacklog_workflow import *
from src.mcp_server.task_tools import *
from src.mcp_server.workspace_tools import *

if __name__ == "__main__":
    # Run with HTTP transport for hosted MCP server
    mcp.run(
        transport="http",
        host="0.0.0.0",  # nosec
        port=9000,
    )
