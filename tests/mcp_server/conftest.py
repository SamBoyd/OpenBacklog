import uuid
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_mcp_auth_provider(user, workspace):
    """
    Mock MCP auth provider that returns test user and workspace.

    Useful for testing auth_utils and provider logic in isolation.
    """
    from src.mcp_server.providers.base import MCPAuthProvider

    provider = MagicMock(spec=MCPAuthProvider)
    provider.get_user_context.return_value = (user.id, workspace.id)
    provider.get_provider_name.return_value = "Mock"

    return provider


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
        MagicMock(),  # Replacing a removed file
        patch("src.mcp_server.task_tools.get_auth_context"),
        patch("src.mcp_server.checklist_tools.get_auth_context"),
        # Prompt-driven tools also use get_auth_context
        patch("src.mcp_server.prompt_driven_tools.product_outcomes.get_auth_context"),
        patch("src.mcp_server.prompt_driven_tools.product_vision.get_auth_context"),
        patch("src.mcp_server.prompt_driven_tools.strategic_pillars.get_auth_context"),
        patch("src.mcp_server.prompt_driven_tools.roadmap_themes.get_auth_context"),
        patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_auth_context"
        ),
        patch("src.mcp_server.prompt_driven_tools.narrative_heroes.get_auth_context"),
        patch("src.mcp_server.prompt_driven_tools.narrative_villains.get_auth_context"),
        patch(
            "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_auth_context"
        ),
        # Prompt-driven tools use get_workspace_id_from_request
        patch(
            "src.mcp_server.prompt_driven_tools.product_outcomes.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.product_vision.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.strategic_pillars.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.roadmap_themes.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.strategic_initiatives.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.narrative_heroes.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.narrative_villains.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.narrative_conflicts.get_workspace_id_from_request"
        ),
        patch(
            "src.mcp_server.prompt_driven_tools.utilities.get_workspace_id_from_request"
        ),
        # Only utilities.py uses get_user_id_from_request
        patch("src.mcp_server.prompt_driven_tools.utilities.get_user_id_from_request"),
    ]

    mocks = [p.start() for p in patches]
    # First 12 mocks return (user_id, workspace_id) tuple
    for mock in mocks[:12]:
        mock.return_value = (str(user.id), str(workspace.id))

    # Mocks 12-19 return just workspace.id (UUID)
    for mock in mocks[12:22]:
        mock.return_value = workspace.id

    # Last mock returns user.id (UUID)
    mocks[22].return_value = user.id

    yield mocks

    for p in patches:
        p.stop()
