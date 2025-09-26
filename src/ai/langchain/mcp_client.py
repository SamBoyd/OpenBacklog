from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.config import settings


async def get_mcp_tools(user_auth_token: str, workspace_id: str):
    if not user_auth_token:
        raise ValueError("User auth token is required to get MCP tools")

    client = MultiServerMCPClient(
        {
            "initiatives": {
                "url": f"{settings.mcp_server_domain}/mcp/",
                "transport": "streamable_http",
                "headers": {
                    "Authorization": f"Bearer {user_auth_token}",
                    "X-Workspace-Id": str(workspace_id),
                },
            }
        }  # type: ignore
    )

    return await client.get_tools()
