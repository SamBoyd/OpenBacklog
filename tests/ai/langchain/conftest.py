"""
Test configuration for Langchain agent evaluation.

This module extends the existing conftest.py with agent-specific fixtures
for comprehensive testing of the Langchain agent system.
"""

import os
import uuid
from typing import Generator, List

import pytest
from sqlalchemy.orm import Session

# Import evaluation classes
from evals.agent_evaluator import (
    AgentEvaluator,
    EvalConfig,
    GoldTestCase,
    TracingCallback,
)

# Import model dependencies
from src.models import Initiative, Task, User, Workspace

# Import existing fixtures and models
from tests.conftest import (  # Import from project's main conftest
    clean_tables,
    openai_api_key,
    session,
    test_initiative,
    test_task,
    test_user_key,
    user,
    workspace,
)


@pytest.fixture
def agent_evaluator() -> AgentEvaluator:
    """
    Provides a configured AgentEvaluator instance for testing.

    Returns:
        AgentEvaluator configured with test-appropriate settings
    """
    config = EvalConfig(
        temperature=0.1,  # Low temperature for deterministic testing
        timeout_seconds=60,  # Shorter timeout for tests
        use_real_api=True,  # Use real API for E2E tests
        include_memory=True,
        include_search=False,  # Disable search to reduce external dependencies
        log_traces=True,
    )
    return AgentEvaluator(config)


@pytest.fixture
def mock_agent_config() -> EvalConfig:
    """
    Provides a mock configuration for deterministic testing.

    Returns:
        EvalConfig configured for fast, reproducible tests
    """
    return EvalConfig(
        temperature=0.0,  # Maximum determinism
        timeout_seconds=30,
        use_real_api=False,  # Use mocked responses
        mock_responses={
            "initiative_creation": {
                "message": "Created test initiative",
                "created_initiatives": [
                    {"title": "Test Initiative", "description": "Test description"}
                ],
            },
            "task_creation": {
                "message": "Created test task",
                "created_tasks": [
                    {"title": "Test Task", "description": "Test description"}
                ],
            },
        },
        include_memory=False,  # Disable for unit tests
        include_search=False,
        log_traces=False,
    )


@pytest.fixture
def gold_dataset() -> List[GoldTestCase]:
    """
    Loads and parses the gold dataset for testing.

    Returns:
        List of GoldTestCase objects from datasets/gold.jsonl
    """
    dataset_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "datasets", "gold.jsonl"
    )

    # Ensure the dataset file exists
    if not os.path.exists(dataset_path):
        pytest.skip(f"Gold dataset not found at {dataset_path}")

    return AgentEvaluator.load_gold_dataset(dataset_path)


@pytest.fixture
def sample_test_cases() -> List[GoldTestCase]:
    """
    Provides a small set of test cases for quick testing.

    Returns:
        List of basic test cases for fast execution
    """
    return [
        GoldTestCase(
            name="simple_initiative_test",
            category="initiative_creation",
            input="Create a test initiative",
            context={"initiatives": [], "tasks": []},
            expected_regex="(?i)(test|initiative|creat)",
            references=[],
            tool_plan=["internal_create_initiative"],
            must_include=["test", "initiative"],
            validation_schema="EasyInitiativeLLMResponse",
            expected_operations={"created_initiatives": 1},
        ),
        GoldTestCase(
            name="simple_task_test",
            category="task_creation",
            input="Add a test task",
            context={
                "initiatives": [
                    {
                        "identifier": "INIT-TEST",
                        "title": "Test Initiative",
                        "description": "Test",
                        "tasks": [],
                    }
                ],
                "tasks": [],
            },
            expected_regex="(?i)(test|task|add)",
            references=[],
            tool_plan=["internal_create_task"],
            must_include=["test", "task"],
            validation_schema="EasyTaskLLMResponse",
            expected_operations={"created_tasks": 1},
        ),
        GoldTestCase(
            name="discussion_test",
            category="discussion",
            input="What is the best approach to task management?",
            context={"initiatives": [], "tasks": []},
            expected_regex="(?i)(approach|task|management)",
            references=[],
            tool_plan=[],
            must_include=["task", "management"],
            validation_schema="DiscussResponseModel",
            expected_operations={},
        ),
    ]


@pytest.fixture
def trace_collector() -> TracingCallback:
    """
    Provides a configured TracingCallback for capturing execution traces.

    Returns:
        TracingCallback instance for test execution tracking
    """
    return TracingCallback()


@pytest.fixture
def agent_test_context(
    session: Session,
    user: User,
    workspace: Workspace,
    test_initiative: Initiative,
    test_task: Task,
) -> dict:
    """
    Provides a complete test context with database objects for agent testing.

    Args:
        session: Database session fixture
        user: Test user fixture
        workspace: Test workspace fixture
        test_initiative: Test initiative fixture
        test_task: Test task fixture

    Returns:
        Dictionary containing all context objects needed for agent testing
    """
    return {
        "session": session,
        "user": user,
        "workspace": workspace,
        "initiative": test_initiative,
        "task": test_task,
        "user_id": str(user.id),
        "workspace_id": str(workspace.id),
        "thread_id": str(uuid.uuid4()),
    }


@pytest.fixture
def agent_test_data() -> dict:
    """
    Provides test data structures for agent context.

    Returns:
        Dictionary with sample context data for testing
    """
    return {
        "empty_context": {"initiatives": [], "tasks": []},
        "single_initiative_context": {
            "initiatives": [
                {
                    "identifier": "INIT-001",
                    "title": "Test Initiative",
                    "description": "A test initiative for evaluation",
                    "tasks": [],
                }
            ],
            "tasks": [],
        },
        "complex_context": {
            "initiatives": [
                {
                    "identifier": "INIT-001",
                    "title": "Frontend Development",
                    "description": "User interface development",
                    "tasks": [],
                },
                {
                    "identifier": "INIT-002",
                    "title": "Backend API",
                    "description": "Server-side API development",
                    "tasks": [],
                },
            ],
            "tasks": [
                {
                    "identifier": "TASK-001",
                    "title": "Setup Authentication",
                    "description": "Implement user authentication",
                    "initiative_identifier": "INIT-002",
                    "checklist": [
                        {"title": "Setup OAuth", "is_complete": False},
                        {"title": "Configure sessions", "is_complete": True},
                    ],
                }
            ],
        },
    }


@pytest.fixture(autouse=True)
def setup_agent_environment(
    session: Session,
    user: User,
    workspace: Workspace,
    test_initiative: Initiative,
    test_task: Task,
):
    """
    Automatically sets up the test environment for agent testing.

    This fixture ensures that the database is properly configured with
    test data and that all relationships are correctly established.

    Args:
        session: Database session
        user: Test user
        workspace: Test workspace
        test_initiative: Test initiative
        test_task: Test task
    """
    # Ensure all objects are properly committed and refreshed
    session.commit()
    session.refresh(user)
    session.refresh(workspace)
    session.refresh(test_initiative)
    session.refresh(test_task)

    # Verify relationships
    assert test_initiative.user_id == user.id
    assert test_initiative.workspace_id == workspace.id
    assert test_task.user_id == user.id
    assert test_task.workspace_id == workspace.id
    assert test_task.initiative_id == test_initiative.id

    yield

    # Cleanup is handled by the clean_tables fixture


# Helper functions for test setup patterns


def create_test_case_with_context(
    name: str,
    category: str,
    input_text: str,
    context: dict,
    validation_schema: str = "EasyInitiativeLLMResponse",
    must_include: List[str] = None,
) -> GoldTestCase:
    """
    Helper function to create test cases with context.

    Args:
        name: Test case name
        category: Test category
        input_text: User input text
        context: Test context with initiatives/tasks
        validation_schema: Expected response schema
        must_include: Required keywords in response

    Returns:
        GoldTestCase object
    """
    if must_include is None:
        must_include = []

    return GoldTestCase(
        name=name,
        category=category,
        input=input_text,
        context=context,
        expected_regex=".*",  # Match any response
        references=[],
        tool_plan=[],
        must_include=must_include,
        validation_schema=validation_schema,
        expected_operations={},
    )


def assert_agent_response_structure(response, expected_schema: str):
    """
    Helper function to assert agent response structure.

    Args:
        response: Agent response object
        expected_schema: Expected schema name
    """
    if expected_schema == "EasyInitiativeLLMResponse":
        assert hasattr(response, "message")
        assert hasattr(response, "created_initiatives")
        assert hasattr(response, "updated_initiatives")
        assert hasattr(response, "deleted_initiatives")
    elif expected_schema == "EasyTaskLLMResponse":
        assert hasattr(response, "message")
        assert hasattr(response, "created_tasks")
        assert hasattr(response, "updated_tasks")
        assert hasattr(response, "deleted_tasks")
    elif expected_schema == "DiscussResponseModel":
        assert hasattr(response, "message")
    else:
        raise ValueError(f"Unknown schema: {expected_schema}")


# Configuration for different test environments


@pytest.fixture
def unit_test_config() -> EvalConfig:
    """Configuration for unit tests - fast, mocked, isolated."""
    return EvalConfig(
        temperature=0.0,
        timeout_seconds=10,
        use_real_api=False,
        include_memory=False,
        include_search=False,
        log_traces=False,
    )


@pytest.fixture
def integration_test_config(openai_api_key: str) -> EvalConfig:
    """Configuration for integration tests - real API, shorter timeouts."""
    return EvalConfig(
        temperature=0.1,
        timeout_seconds=30,
        use_real_api=True,
        include_memory=True,
        include_search=False,
        log_traces=True,
    )


@pytest.fixture
def e2e_test_config(openai_api_key: str) -> EvalConfig:
    """Configuration for end-to-end tests - full system, longer timeouts."""
    return EvalConfig(
        temperature=0.2,
        timeout_seconds=120,
        use_real_api=True,
        include_memory=True,
        include_search=True,
        log_traces=True,
    )
