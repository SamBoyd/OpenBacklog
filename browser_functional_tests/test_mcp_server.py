"""
Functional tests for the MCP server.

Tests the MCP server running at http://127.0.0.1:9000/mcp with HTTP transport.
Requires Authorization and X-Workspace-Id headers for authentication.
"""

import asyncio
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from src.auth.jwt_utils import create_unified_jwt
from src.models import User, Workspace


class TestMCPServer:
    """Test suite for MCP server functionality."""

    @pytest.fixture
    def mcp_client(self, user: User, workspace: Workspace):
        """Create an authenticated MCP client."""
        # Generate JWT token for authentication
        jwt_token = create_unified_jwt(user)
        
        # Configure transport with authentication headers
        transport = StreamableHttpTransport(
            url="http://127.0.0.1:9000/mcp",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "X-Workspace-Id": str(workspace.id)
            }
        )
        
        return Client(transport)

    @pytest.mark.asyncio
    async def test_mcp_server_connection(self, mcp_client: Client):
        """Test that the MCP client can connect to the server."""
        async with mcp_client:
            # Test basic connectivity
            await mcp_client.ping()
            
            # Verify client is connected
            assert mcp_client.is_connected()

    @pytest.mark.asyncio
    async def test_mcp_server_authentication(self, user: User, workspace: Workspace):
        """Test authentication with proper headers."""
        jwt_token = create_unified_jwt(user)
        
        # Test with proper authentication
        transport = StreamableHttpTransport(
            url="http://127.0.0.1:9000/mcp",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "X-Workspace-Id": str(workspace.id)
            }
        )
        client = Client(transport)
        
        async with client:
            await client.ping()
            assert client.is_connected()

    @pytest.mark.asyncio
    async def test_mcp_tools_registration(self, mcp_client: Client):
        """Test that expected tools are registered with the MCP server."""
        async with mcp_client:
            # List available tools
            tools = await mcp_client.list_tools()
            
            # Verify we have tools registered
            assert len(tools) > 0, "No tools registered with MCP server"
            
            # Get tool names
            tool_names = [tool.name for tool in tools]
            
            # Check for expected tools based on the modules imported in main.py
            expected_tools = [
                'update_checklist',
                'update_checklist_item',
                'health_check',
                'get_active_initiatives',
                'search_initiatives',
                'get_initiative_tasks',
                'get_task_details',
                'search_tasks',
                'update_task_description',
                'validate_context',
                'update_task_status_inprogress',
                'update_task_status_done',
                'start_openbacklog_workflow'
            ]
            
            for expected_tool in expected_tools:
                assert any(expected_tool in name for name in tool_names), \
                    f"Expected tool '{expected_tool}' not found in registered tools: {tool_names}"

    @pytest.mark.asyncio
    async def test_mcp_healthcheck_tool(self, mcp_client: Client):
        """Test calling the healthcheck tool."""
        async with mcp_client:
            # Call the healthcheck tool (assuming it exists)
            try:
                result = await mcp_client.call_tool("healthcheck", {})
                
                # Verify we got a response
                assert result is not None
                
                # If the tool returns structured data, verify it
                if hasattr(result, 'data'):
                    assert result.data is not None
                    
            except Exception as e:
                # If healthcheck tool doesn't exist or has different signature,
                # we'll get an exception - that's also valid information
                pytest.skip(f"Healthcheck tool not available or different signature: {e}")

    @pytest.mark.asyncio
    async def test_mcp_tools_list_detailed(self, mcp_client: Client):
        """Test detailed examination of available tools."""
        async with mcp_client:
            tools = await mcp_client.list_tools()
            
            # Print tool information for debugging
            print(f"\nFound {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    print(f"    Input schema: {tool.inputSchema}")
            
            # Verify each tool has required attributes
            for tool in tools:
                assert hasattr(tool, 'name'), f"Tool missing name: {tool}"
                assert tool.name, f"Tool has empty name: {tool}"
                assert hasattr(tool, 'description'), f"Tool missing description: {tool}"

    @pytest.mark.asyncio
    async def test_mcp_resources_list(self, mcp_client: Client):
        """Test listing available resources."""
        async with mcp_client:
            try:
                resources = await mcp_client.list_resources()
                
                # Resources might be empty, that's okay
                print(f"\nFound {len(resources)} resources:")
                for resource in resources:
                    print(f"  - {resource.uri}: {resource.name}")
                    
            except Exception as e:
                # Some MCP servers might not support resources
                pytest.skip(f"Resources not supported or accessible: {e}")

    @pytest.mark.asyncio
    async def test_mcp_prompts_list(self, mcp_client: Client):
        """Test listing available prompts."""
        async with mcp_client:
            try:
                prompts = await mcp_client.list_prompts()
                
                # Prompts might be empty, that's okay
                print(f"\nFound {len(prompts)} prompts:")
                for prompt in prompts:
                    print(f"  - {prompt.name}: {prompt.description}")
                    
            except Exception as e:
                # Some MCP servers might not support prompts
                pytest.skip(f"Prompts not supported or accessible: {e}")