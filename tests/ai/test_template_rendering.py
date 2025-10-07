"""
Quick validation test to ensure prompt templates render correctly.
"""

import os

from src.ai.prompt import InitiativePrompt, TaskPrompt
from src.models import Initiative, PydanticInitiative, PydanticTask


def test_initiative_edit_template_renders():
    """Test that initiative_edit.jinja renders without errors."""
    initiative = PydanticInitiative(
        id="00000000-0000-0000-0000-000000000001",
        identifier="TEST-1",
        title="Test Initiative",
        description="Test description",
        tasks=[],
    )

    prompt = InitiativePrompt(
        initiatives=[initiative],
        additional_context="Test context",
    )

    # Should not raise any Jinja2 errors
    rendered = prompt.render_system_content()

    # Verify scenario-based guidance is present
    assert "Scenario 1: User mentions work not in current context" in rendered
    assert "search_tasks" in rendered
    assert "get_initiative_details" in rendered


def test_task_edit_template_renders():
    """Test that task_edit.jinja renders without errors."""
    task = PydanticTask(
        id="00000000-0000-0000-0000-000000000002",
        identifier="TEST-2",
        title="Test Task",
        description="Test description",
        checklist=[],
    )

    # Create a mock initiative for context
    from unittest.mock import Mock

    initiative = Mock(spec=Initiative)
    initiative.identifier = "TEST-INIT"
    initiative.title = "Test Initiative"
    initiative.description = "Test initiative description"

    prompt = TaskPrompt(
        tasks=[task],
        initiative=initiative,
        additional_context="Test context",
    )

    # Should not raise any Jinja2 errors
    rendered = prompt.render_system_content()

    # Verify scenario-based guidance is present
    assert "Scenario 1: User mentions work not in current context" in rendered
    assert "search_tasks" in rendered
    assert "get_initiative_details" in rendered
