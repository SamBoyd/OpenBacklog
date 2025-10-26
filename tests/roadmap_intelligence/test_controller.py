import re
import uuid

import pytest
from hamcrest import assert_that, equal_to, has_length
from sqlalchemy.orm import Session

from src.controllers import product_strategy_controller
from src.models import User, Workspace
from src.roadmap_intelligence import controller
from src.roadmap_intelligence.services import prioritization_service
from src.roadmap_intelligence.services.prioritization_service import (
    PrioritizationService,
)
from src.roadmap_intelligence.views import prioritize_theme
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


def test_get_roadmap_themes_empty(workspace: Workspace, session: Session):
    """Test getting themes for workspace with no themes."""
    themes = controller.get_roadmap_themes(workspace.id, session)
    assert_that(themes, has_length(0))


def test_get_roadmap_themes_returns_ordered_list(
    user: User, workspace: Workspace, session: Session
):
    """Test getting themes returns list ordered."""
    theme1 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 1",
        "Problem 1",
        None,
        None,
        None,
        [],
        session,
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 2",
        "Problem 2",
        None,
        None,
        None,
        [],
        session,
    )
    theme3 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 3",
        "Problem 3",
        None,
        None,
        None,
        [],
        session,
    )

    themes = controller.get_roadmap_themes(workspace.id, session)

    assert_that(themes, has_length(3))
    assert_that(themes[0].id, equal_to(theme1.id))
    assert_that(themes[1].id, equal_to(theme2.id))
    assert_that(themes[2].id, equal_to(theme3.id))


def test_create_roadmap_theme_minimal(
    user: User, workspace: Workspace, session: Session
):
    """Test creating theme with only required fields."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "First Week Magic",
        "Users fail to integrate in first week",
        None,
        None,
        None,
        [],
        session,
    )

    assert_that(theme.name, equal_to("First Week Magic"))
    assert_that(
        theme.problem_statement, equal_to("Users fail to integrate in first week")
    )
    assert_that(theme.workspace_id, equal_to(workspace.id))
    assert_that(theme.hypothesis, equal_to(None))
    assert_that(theme.indicative_metrics, equal_to(None))
    assert_that(theme.time_horizon_months, equal_to(None))


def test_create_roadmap_theme_full_details(
    user: User, workspace: Workspace, session: Session
):
    """Test creating theme with all fields."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "First Week Magic",
        "Users fail to integrate in first week",
        "Quick wins drive adoption",
        "% users active in week 1",
        6,
        [],
        session,
    )

    assert_that(theme.name, equal_to("First Week Magic"))
    assert_that(
        theme.problem_statement, equal_to("Users fail to integrate in first week")
    )
    assert_that(theme.hypothesis, equal_to("Quick wins drive adoption"))
    assert_that(theme.indicative_metrics, equal_to("% users active in week 1"))
    assert_that(theme.time_horizon_months, equal_to(6))


def test_create_roadmap_theme_with_outcome_links(
    user: User, workspace: Workspace, session: Session
):
    """Test creating theme linked to outcomes."""
    outcome1 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 1", None, None, None, [], session
    )
    outcome2 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 2", None, None, None, [], session
    )

    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Test Theme",
        "Test problem",
        None,
        None,
        None,
        [outcome1.id, outcome2.id],
        session,
    )

    session.refresh(theme)
    assert_that(theme.outcomes, has_length(2))
    outcome_ids = {o.id for o in theme.outcomes}
    assert outcome1.id in outcome_ids
    assert outcome2.id in outcome_ids


def test_create_roadmap_theme_validates_name_empty(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of empty theme name."""
    with pytest.raises(DomainException, match="at least 1 character"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "",
            "Valid problem",
            None,
            None,
            None,
            [],
            session,
        )


def test_create_roadmap_theme_validates_name_too_long(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of theme name exceeding max length."""
    with pytest.raises(DomainException, match="100 characters or less"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "A" * 101,
            "Valid problem",
            None,
            None,
            None,
            [],
            session,
        )


def test_create_roadmap_theme_validates_problem_statement_empty(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of empty problem statement."""
    with pytest.raises(DomainException, match="at least 1 character"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Valid Name",
            "",
            None,
            None,
            None,
            [],
            session,
        )


def test_create_roadmap_theme_validates_problem_statement_too_long(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of problem statement exceeding max length."""
    with pytest.raises(DomainException, match="1500 characters or less"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Valid name",
            "P" * 1501,
            None,
            None,
            None,
            [],
            session,
        )


def test_create_roadmap_theme_validates_hypothesis_too_long(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of hypothesis exceeding max length."""
    with pytest.raises(DomainException, match="1500 characters or less"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Valid name",
            "Valid problem",
            "H" * 1501,
            None,
            None,
            [],
            session,
        )


def test_create_roadmap_theme_validates_metrics_too_long(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of indicative_metrics exceeding max length."""
    with pytest.raises(DomainException, match="1000 characters or less"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Valid name",
            "Valid problem",
            None,
            "M" * 1001,
            None,
            [],
            session,
        )


def test_create_roadmap_theme_validates_time_horizon_too_low(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of time horizon below minimum."""
    with pytest.raises(DomainException, match="between 0-12 months"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Valid name",
            "Valid problem",
            None,
            None,
            -1,
            [],
            session,
        )


def test_create_roadmap_theme_validates_time_horizon_too_high(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of time horizon above maximum."""
    with pytest.raises(DomainException, match="between 0-12 months"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Valid name",
            "Valid problem",
            None,
            None,
            13,
            [],
            session,
        )


def test_create_roadmap_theme_enforces_max_limit(
    user: User, workspace: Workspace, session: Session
):
    """Test that workspace cannot exceed 5 theme limit."""
    for i in range(5):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            f"Theme {i}",
            f"Problem {i}",
            None,
            None,
            None,
            [],
            session,
        )

    with pytest.raises(DomainException, match="maximum of 5 active roadmap themes"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Theme 6",
            "Problem 6",
            None,
            None,
            None,
            [],
            session,
        )


def test_update_roadmap_theme_with_all_fields(
    user: User, workspace: Workspace, session: Session
):
    """Test updating theme with all fields."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Original Name",
        "Original problem",
        "Original hypothesis",
        "Original metrics",
        6,
        [],
        session,
    )

    updated_name = "Updated Name"
    updated_problem = "Updated problem statement"
    updated_hypothesis = "Updated hypothesis"
    updated_metrics = "Updated metrics"
    updated_time_horizon = 9

    updated_theme = controller.update_roadmap_theme(
        theme.id,
        workspace.id,
        updated_name,
        updated_problem,
        updated_hypothesis,
        updated_metrics,
        updated_time_horizon,
        [],
        session,
    )

    assert_that(updated_theme.id, equal_to(theme.id))
    assert_that(updated_theme.name, equal_to(updated_name))
    assert_that(updated_theme.problem_statement, equal_to(updated_problem))
    assert_that(updated_theme.hypothesis, equal_to(updated_hypothesis))
    assert_that(updated_theme.indicative_metrics, equal_to(updated_metrics))
    assert_that(updated_theme.time_horizon_months, equal_to(updated_time_horizon))


def test_update_roadmap_theme_name_only(
    user: User, workspace: Workspace, session: Session
):
    """Test updating only theme name."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Original Name",
        "Original problem",
        "Original hypothesis",
        "Original metrics",
        6,
        [],
        session,
    )

    updated_name = "Updated Name"

    updated_theme = controller.update_roadmap_theme(
        theme.id,
        workspace.id,
        updated_name,
        theme.problem_statement,
        theme.hypothesis,
        theme.indicative_metrics,
        theme.time_horizon_months,
        [],
        session,
    )

    assert_that(updated_theme.name, equal_to(updated_name))
    assert_that(updated_theme.problem_statement, equal_to(theme.problem_statement))
    assert_that(updated_theme.hypothesis, equal_to(theme.hypothesis))
    assert_that(updated_theme.indicative_metrics, equal_to(theme.indicative_metrics))
    assert_that(updated_theme.time_horizon_months, equal_to(theme.time_horizon_months))


def test_update_roadmap_theme_outcome_links(
    user: User, workspace: Workspace, session: Session
):
    """Test updating theme outcome linkages."""
    outcome1 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 1", None, None, None, [], session
    )
    outcome2 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 2", None, None, None, [], session
    )
    outcome3 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 3", None, None, None, [], session
    )

    # Create theme with outcome1 and outcome2
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Test Theme",
        "Test problem",
        None,
        None,
        None,
        [outcome1.id, outcome2.id],
        session,
    )

    session.refresh(theme)
    assert_that(theme.outcomes, has_length(2))

    # Update to link outcome2 and outcome3 (remove outcome1, add outcome3)
    updated_theme = controller.update_roadmap_theme(
        theme.id,
        workspace.id,
        theme.name,
        theme.problem_statement,
        theme.hypothesis,
        theme.indicative_metrics,
        theme.time_horizon_months,
        [outcome2.id, outcome3.id],
        session,
    )

    session.refresh(updated_theme)
    assert_that(updated_theme.outcomes, has_length(2))
    outcome_ids = {o.id for o in updated_theme.outcomes}
    assert outcome2.id in outcome_ids
    assert outcome3.id in outcome_ids
    assert outcome1.id not in outcome_ids


def test_update_roadmap_theme_validates_name_empty(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of empty name when updating."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Original Name",
        "Problem",
        None,
        None,
        None,
        [],
        session,
    )

    with pytest.raises(DomainException, match="at least 1 character"):
        controller.update_roadmap_theme(
            theme.id, workspace.id, "", "Problem", None, None, None, [], session
        )


def test_update_roadmap_theme_not_found(
    user: User, workspace: Workspace, session: Session
):
    """Test updating non-existent theme raises DomainException."""
    fake_theme_id = uuid.uuid4()

    with pytest.raises(DomainException, match="not found"):
        controller.update_roadmap_theme(
            fake_theme_id,
            workspace.id,
            "Some name",
            "Some problem",
            None,
            None,
            None,
            [],
            session,
        )


# Delete Roadmap Theme Tests


def test_delete_roadmap_theme_success(
    user: User, workspace: Workspace, session: Session
):
    """Test successfully deleting a theme."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme to Delete",
        "Problem",
        None,
        None,
        None,
        [],
        session,
    )

    controller.delete_roadmap_theme(theme.id, workspace.id, user.id, session)

    # Verify theme is deleted
    themes = controller.get_roadmap_themes(workspace.id, session)
    assert_that(themes, has_length(0))


def test_delete_roadmap_theme_not_found(
    user: User, workspace: Workspace, session: Session
):
    """Test deleting non-existent theme raises DomainException."""
    fake_theme_id = uuid.uuid4()

    with pytest.raises(DomainException, match="not found"):
        controller.delete_roadmap_theme(fake_theme_id, workspace.id, user.id, session)


# Reorder Roadmap Themes Tests


def test_reorder_roadmap_themes_success(
    user: User, workspace: Workspace, session: Session
):
    """Test successfully reordering themes."""

    # Create 3 theme
    theme1 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 1",
        "Problem 1",
        None,
        None,
        None,
        [],
        session,
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 2",
        "Problem 2",
        None,
        None,
        None,
        [],
        session,
    )
    theme3 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 3",
        "Problem 3",
        None,
        None,
        None,
        [],
        session,
    )

    prioritization_service = PrioritizationService(session, EventPublisher(session))
    prioritization_service.prioritize_theme(workspace.id, user.id, theme1.id, 0)
    prioritization_service.prioritize_theme(workspace.id, user.id, theme2.id, 1)
    prioritization_service.prioritize_theme(workspace.id, user.id, theme3.id, 2)

    # Reorder: swap theme1 and theme3 (0 -> 2, 2 -> 0)
    theme_orders = {
        theme1.id: 2,  # Move theme1 to end
        theme2.id: 1,  # Keep theme2 in middle
        theme3.id: 0,  # Move theme3 to start
    }

    result = controller.reorder_roadmap_themes(workspace.id, theme_orders, session)

    # Verify result is ordered correctly
    assert_that(result, has_length(3))
    assert_that(result[0].id, equal_to(theme3.id))
    assert_that(result[1].id, equal_to(theme2.id))
    assert_that(result[2].id, equal_to(theme1.id))


def test_reorder_roadmap_themes_requires_all_themes(
    user: User, workspace: Workspace, session: Session
):
    """Test that partial reordering (not including all themes) raises error."""
    prioritization_service = PrioritizationService(session, EventPublisher(session))

    # Create 3 themes
    theme1 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 1", "Problem 1", None, None, None, [], session
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 2", "Problem 2", None, None, None, [], session
    )
    theme3 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 3", "Problem 3", None, None, None, [], session
    )

    prioritization_service.prioritize_theme(workspace.id, user.id, theme1.id, 0)
    prioritization_service.prioritize_theme(workspace.id, user.id, theme2.id, 1)
    prioritization_service.prioritize_theme(workspace.id, user.id, theme3.id, 2)

    # Try to reorder only theme1 and theme2 (missing theme3)
    theme_orders = {
        theme1.id: 1,
        theme2.id: 0,
    }

    with pytest.raises(
        DomainException,
        match=re.escape(
            f"Must provide order for all 3 prioritized themes (got 2). Missing: {theme3.id}"
        ),
    ):
        controller.reorder_roadmap_themes(workspace.id, theme_orders, session)


def test_reorder_roadmap_themes_validates_incomplete_sequence(
    user: User, workspace: Workspace, session: Session
):
    """Test that display orders must form complete sequence [0,1,2,...]."""
    prioritization_service = PrioritizationService(session, EventPublisher(session))

    theme1 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 1", "Problem 1", None, None, None, [], session
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 2", "Problem 2", None, None, None, [], session
    )
    theme3 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 3", "Problem 3", None, None, None, [], session
    )

    prioritization_service.prioritize_theme(workspace.id, user.id, theme1.id, 0)
    prioritization_service.prioritize_theme(workspace.id, user.id, theme2.id, 1)
    prioritization_service.prioritize_theme(workspace.id, user.id, theme3.id, 2)

    # Try to set display orders with gaps: [0, 1, 5]
    theme_orders = {
        theme1.id: 0,
        theme2.id: 1,
        theme3.id: 5,
    }

    with pytest.raises(DomainException, match="Display orders must be"):
        controller.reorder_roadmap_themes(workspace.id, theme_orders, session)


def test_reorder_roadmap_themes_missing_theme(
    user: User, workspace: Workspace, session: Session
):
    """Test that missing a theme raises DomainException."""
    prioritization_service = PrioritizationService(session, EventPublisher(session))

    theme1 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 1", "Problem 1", None, None, None, [], session
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 2", "Problem 2", None, None, None, [], session
    )

    prioritization_service.prioritize_theme(workspace.id, user.id, theme1.id, 0)
    prioritization_service.prioritize_theme(workspace.id, user.id, theme2.id, 1)

    # Only include theme1, missing theme2
    theme_orders = {
        theme1.id: 0,
    }

    with pytest.raises(
        DomainException,
        match=re.escape(
            f"Must provide order for all 2 prioritized themes (got 1). Missing: {theme2.id}"
        ),
    ):
        controller.reorder_roadmap_themes(workspace.id, theme_orders, session)


def test_reorder_roadmap_themes_unknown_theme(
    user: User, workspace: Workspace, session: Session
):
    """Test that unknown theme ID raises DomainException."""
    prioritization_service = PrioritizationService(session, EventPublisher(session))

    theme1 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 1", "Problem 1", None, None, None, [], session
    )

    theme2 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 2", "Problem 2", None, None, None, [], session
    )

    prioritization_service.prioritize_theme(workspace.id, user.id, theme1.id, 0)
    prioritization_service.prioritize_theme(workspace.id, user.id, theme2.id, 1)

    fake_theme_id = uuid.uuid4()
    theme_orders = {
        theme1.id: 0,
        fake_theme_id: 1,
    }

    with pytest.raises(
        DomainException, match=re.escape(f"Themes are not prioritized: {fake_theme_id}")
    ):
        controller.reorder_roadmap_themes(workspace.id, theme_orders, session)
