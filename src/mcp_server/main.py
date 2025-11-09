# src/ai/mcp_server.py
import logging
import os
from unittest.mock import MagicMock

from fastmcp.server import FastMCP
from mcp.server.fastmcp import Icon

from src.config import ENV_FILE, settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Auth0 OAuth authentication only in non-test environments
# In test environments, we use a mock auth provider
if settings.environment == "test":
    # Mock auth provider for tests
    auth_provider = None  # No auth in test mode
    well_known_routes = {}
else:
    from cryptography.fernet import Fernet
    from fastmcp.server.auth.providers.auth0 import Auth0Provider
    from key_value.aio.wrappers.encryption import FernetEncryptionWrapper

    from src.db import async_session_maker
    from src.mcp_server.storage import PostgreSQLMCPStorage

    # Initialize PostgreSQL storage backend for OAuth tokens
    postgres_storage = PostgreSQLMCPStorage(async_session_maker)

    # Wrap storage with encryption for security
    client_storage = FernetEncryptionWrapper(
        key_value=postgres_storage,
        fernet=Fernet(settings.mcp_oauth_storage_encryption_key.encode()),
    )

    # Configure Auth0 OAuth authentication
    # Users authenticate via browser redirect to Auth0 login page
    # Client credentials are stored server-side only (never distributed to users)
    # After initial login, tokens are cached locally on the user's machine
    # Tokens are persisted in PostgreSQL with encryption for security
    auth_provider = Auth0Provider(
        config_url=f"https://{settings.mcp_server_auth0_domain}/.well-known/openid-configuration",
        client_id=settings.mcp_server_auth0_client_id,
        client_secret=settings.mcp_server_auth0_client_secret,
        audience=settings.mcp_server_auth0_audience,
        base_url=f"{settings.mcp_server_domain}/mcp",
        issuer_url=f"{settings.mcp_server_domain}",
        jwt_signing_key=settings.mcp_oauth_jwt_signing_key,
        client_storage=client_storage,
    )

    well_known_routes = auth_provider.get_well_known_routes(mcp_path="/mcp")

# Initialize FastMCP with OAuth authentication
mcp = FastMCP(
    name="OpenBacklog MCP server",
    auth=auth_provider,
    website_url="https://openbacklog.ai",
    icons=[
        Icon(
            src="https://www.openbacklog.ai/assets/ob_v2_64x64.png",
            mimeType="image/png",
            sizes=["64x64"],
        ),
    ],
)

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
