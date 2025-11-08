import uuid
from unittest.mock import MagicMock, patch

import pytest

# Override the clean_tables fixture to prevent database operations for tests that don't need it
# @pytest.fixture(autouse=True)
# def clean_tables():
#     """Mock clean_tables fixture to prevent database operations in unit tests."""
#     pass


@pytest.fixture(autouse=True)
def mock_get_auth_context(request, user, workspace):
    """
    Mock get_auth_context to return test user and workspace IDs across all tool modules.

    This allows MCP tool tests to focus on business logic without dealing with
    Auth0 authentication. The actual get_auth_context logic is tested separately
    in test_auth_utils.py.

    We need to patch get_auth_context in each module where it's imported, since
    tools use `from src.mcp_server.auth_utils import get_auth_context`.
    """
    # Skip mocking for test_auth_utils.py since those tests specifically test auth logic
    if "test_auth_utils" in request.node.nodeid:
        yield
        return

    # Patch in all MCP server tool modules
    patches = [
        patch("src.mcp_server.healthcheck_tool.get_auth_context"),
        patch("src.mcp_server.workspace_tools.get_auth_context"),
        patch("src.mcp_server.initiative_tools.get_auth_context"),
        patch("src.mcp_server.task_tools.get_auth_context"),
        patch("src.mcp_server.checklist_tools.get_auth_context"),
        # Prompt-driven tools also use get_auth_context
        patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.get_auth_context"
        ),
        patch("src.mcp_server.prompt_driven_tools.roadmap_themes.get_auth_context"),
        # Prompt-driven tools use get_workspace_id_from_request
        patch(
            "src.mcp_server.prompt_driven_tools.strategic_foundation.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.utilities.get_workspace_id_from_request"
        ),
        # Only utilities.py uses get_user_id_from_request
        patch("src.mcp_server.prompt_driven_tools.utilities.get_user_id_from_request"),
    ]

    mocks = [p.start() for p in patches]
    # First 7 mocks return (user_id, workspace_id) tuple
    for mock in mocks[:7]:
        mock.return_value = (str(user.id), str(workspace.id))

    # Mocks 7-9 return just workspace.id (UUID)
    for mock in mocks[7:10]:
        mock.return_value = workspace.id

    # Last mock returns user.id (UUID)
    mocks[10].return_value = user.id

    yield mocks

    for p in patches:
        p.stop()
