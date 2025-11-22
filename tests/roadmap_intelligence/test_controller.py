import re
import uuid

import pytest
from hamcrest import assert_that, equal_to, has_length
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.roadmap_intelligence import controller
from src.roadmap_intelligence.services.prioritization_service import (
    PrioritizationService,
)
from src.strategic_planning import controller as product_strategy_controller
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
        [],
        session,
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 2",
        "Problem 2",
        [],
        session,
    )
    theme3 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 3",
        "Problem 3",
        [],
        session,
    )

    themes = controller.get_roadmap_themes(workspace.id, session)

    assert_that(themes, has_length(3))
    assert_that(themes[0].id, equal_to(theme1.id))
    assert_that(themes[1].id, equal_to(theme2.id))
    assert_that(themes[2].id, equal_to(theme3.id))


def test_get_roadmap_themes_eager_loads_heroes(
    user: User, workspace: Workspace, session: Session
):
    """Test get_roadmap_themes eager-loads heroes relationship."""
    from src.narrative.aggregates.hero import Hero
    from src.strategic_planning.services.event_publisher import EventPublisher

    publisher = EventPublisher(session)

    # Create heroes
    hero1 = Hero.define_hero(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Hero 1",
        description="Test hero 1",
        is_primary=False,
        session=session,
        publisher=publisher,
    )
    hero2 = Hero.define_hero(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Hero 2",
        description="Test hero 2",
        is_primary=False,
        session=session,
        publisher=publisher,
    )
    session.commit()

    # Create theme and link heroes
    from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
    from src.strategic_planning.services.event_publisher import EventPublisher

    publisher = EventPublisher(session)
    theme = RoadmapTheme.define_theme(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Test Theme",
        description="Test description",
        session=session,
        publisher=publisher,
        hero_ids=[hero1.id, hero2.id],
    )
    session.commit()

    # Get themes (should eager-load heroes)
    themes = controller.get_roadmap_themes(workspace.id, session)

    assert_that(themes, has_length(1))
    theme = themes[0]

    # Access heroes should NOT trigger additional queries (eager-loaded)
    # We verify this by checking the relationship is accessible
    assert_that(theme.heroes, has_length(2))
    hero_ids = {h.id for h in theme.heroes}
    assert hero1.id in hero_ids
    assert hero2.id in hero_ids


def test_get_roadmap_themes_eager_loads_villains(
    user: User, workspace: Workspace, session: Session
):
    """Test get_roadmap_themes eager-loads villains relationship."""
    from src.narrative.aggregates.villain import Villain, VillainType
    from src.strategic_planning.services.event_publisher import EventPublisher

    publisher = EventPublisher(session)

    # Create villains
    villain1 = Villain.define_villain(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Villain 1",
        villain_type=VillainType.EXTERNAL,
        description="Test villain 1",
        severity=3,
        session=session,
        publisher=publisher,
    )
    villain2 = Villain.define_villain(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Villain 2",
        villain_type=VillainType.INTERNAL,
        description="Test villain 2",
        severity=4,
        session=session,
        publisher=publisher,
    )
    session.commit()

    # Create theme and link villains
    from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
    from src.strategic_planning.services.event_publisher import EventPublisher

    publisher = EventPublisher(session)
    theme = RoadmapTheme.define_theme(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Test Theme",
        description="Test description",
        session=session,
        publisher=publisher,
        villain_ids=[villain1.id, villain2.id],
    )
    session.commit()

    # Get themes (should eager-load villains)
    themes = controller.get_roadmap_themes(workspace.id, session)

    assert_that(themes, has_length(1))
    theme = themes[0]

    # Access villains should NOT trigger additional queries (eager-loaded)
    assert_that(theme.villains, has_length(2))
    villain_ids = {v.id for v in theme.villains}
    assert villain1.id in villain_ids
    assert villain2.id in villain_ids


def test_get_roadmap_themes_eager_loads_heroes_and_villains(
    user: User, workspace: Workspace, session: Session
):
    """Test get_roadmap_themes eager-loads both heroes and villains."""
    from src.narrative.aggregates.hero import Hero
    from src.narrative.aggregates.villain import Villain, VillainType
    from src.strategic_planning.services.event_publisher import EventPublisher

    publisher = EventPublisher(session)

    # Create heroes and villains
    hero = Hero.define_hero(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Hero 1",
        description="Test hero",
        is_primary=False,
        session=session,
        publisher=publisher,
    )
    villain = Villain.define_villain(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Villain 1",
        villain_type=VillainType.EXTERNAL,
        description="Test villain",
        severity=3,
        session=session,
        publisher=publisher,
    )
    session.commit()

    # Create theme with both heroes and villains
    from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme
    from src.strategic_planning.services.event_publisher import EventPublisher

    publisher = EventPublisher(session)
    theme = RoadmapTheme.define_theme(
        workspace_id=workspace.id,
        user_id=user.id,
        name="Test Theme",
        description="Test description",
        session=session,
        publisher=publisher,
        hero_ids=[hero.id],
        villain_ids=[villain.id],
    )
    session.commit()

    # Get themes (should eager-load both)
    themes = controller.get_roadmap_themes(workspace.id, session)

    assert_that(themes, has_length(1))
    theme = themes[0]

    # Both relationships should be accessible without additional queries
    assert_that(theme.heroes, has_length(1))
    assert_that(theme.villains, has_length(1))
    assert_that(theme.heroes[0].id, equal_to(hero.id))
    assert_that(theme.villains[0].id, equal_to(villain.id))


def test_get_roadmap_themes_with_empty_heroes_and_villains(
    user: User, workspace: Workspace, session: Session
):
    """Test get_roadmap_themes works with themes that have no heroes or villains."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme without heroes/villains",
        "Test description",
        [],
        session,
    )

    themes = controller.get_roadmap_themes(workspace.id, session)

    assert_that(themes, has_length(1))
    assert_that(themes[0].heroes, has_length(0))
    assert_that(themes[0].villains, has_length(0))


def test_create_roadmap_theme_minimal(
    user: User, workspace: Workspace, session: Session
):
    """Test creating theme with only required fields."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "First Week Magic",
        "Users fail to integrate in first week",
        [],
        session,
    )

    assert_that(theme.name, equal_to("First Week Magic"))
    assert_that(theme.description, equal_to("Users fail to integrate in first week"))
    assert_that(theme.workspace_id, equal_to(workspace.id))


def test_create_roadmap_theme_full_details(
    user: User, workspace: Workspace, session: Session
):
    """Test creating theme with all fields."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "First Week Magic",
        "Users fail to integrate in first week",
        [],
        session,
    )

    assert_that(theme.name, equal_to("First Week Magic"))
    assert_that(theme.description, equal_to("Users fail to integrate in first week"))


def test_create_roadmap_theme_with_outcome_links(
    user: User, workspace: Workspace, session: Session
):
    """Test creating theme linked to outcomes."""
    outcome1 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 1", None, [], session
    )
    outcome2 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 2", None, [], session
    )

    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Test Theme",
        "Test problem",
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
            [],
            session,
        )


def test_create_roadmap_theme_validates_problem_statement_empty(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of empty description."""
    with pytest.raises(DomainException, match="at least 1 character"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Valid Name",
            "",
            [],
            session,
        )


def test_create_roadmap_theme_validates_problem_statement_too_long(
    user: User, workspace: Workspace, session: Session
):
    """Test validation of description exceeding max length."""
    # Note: Skipped until database schema constraints are updated
    with pytest.raises(
        DomainException, match="Description must be 4000 characters or less"
    ):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Valid name",
            "P" * 4001,
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
            [],
            session,
        )

    with pytest.raises(DomainException, match="maximum of 5 active roadmap themes"):
        controller.create_roadmap_theme(
            workspace.id,
            user.id,
            "Theme 6",
            "Problem 6",
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
        [],
        session,
    )

    updated_name = "Updated Name"
    updated_description = "Updated description"

    updated_theme = controller.update_roadmap_theme(
        theme.id,
        workspace.id,
        updated_name,
        updated_description,
        [],
        session,
    )

    assert_that(updated_theme.id, equal_to(theme.id))
    assert_that(updated_theme.name, equal_to(updated_name))
    assert_that(updated_theme.description, equal_to(updated_description))


def test_update_roadmap_theme_name_only(
    user: User, workspace: Workspace, session: Session
):
    """Test updating only theme name."""
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Original Name",
        "Original problem",
        [],
        session,
    )

    updated_name = "Updated Name"

    updated_theme = controller.update_roadmap_theme(
        theme.id,
        workspace.id,
        updated_name,
        theme.description,
        [],
        session,
    )

    assert_that(updated_theme.name, equal_to(updated_name))
    assert_that(updated_theme.description, equal_to(theme.description))


def test_update_roadmap_theme_outcome_links(
    user: User, workspace: Workspace, session: Session
):
    """Test updating theme outcome linkages."""
    outcome1 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 1", None, [], session
    )
    outcome2 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 2", None, [], session
    )
    outcome3 = product_strategy_controller.create_product_outcome(
        workspace.id, user.id, "Outcome 3", None, [], session
    )

    # Create theme with outcome1 and outcome2
    theme = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Test Theme",
        "Test problem",
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
        theme.description,
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
        [],
        session,
    )

    with pytest.raises(DomainException, match="at least 1 character"):
        controller.update_roadmap_theme(
            theme.id, workspace.id, "", "Problem", [], session
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
        [],
        session,
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 2",
        "Problem 2",
        [],
        session,
    )
    theme3 = controller.create_roadmap_theme(
        workspace.id,
        user.id,
        "Theme 3",
        "Problem 3",
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
        workspace.id, user.id, "Theme 1", "Problem 1", [], session
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 2", "Problem 2", [], session
    )
    theme3 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 3", "Problem 3", [], session
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
        workspace.id, user.id, "Theme 1", "Problem 1", [], session
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 2", "Problem 2", [], session
    )
    theme3 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 3", "Problem 3", [], session
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
        workspace.id, user.id, "Theme 1", "Problem 1", [], session
    )
    theme2 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 2", "Problem 2", [], session
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
        workspace.id, user.id, "Theme 1", "Problem 1", [], session
    )

    theme2 = controller.create_roadmap_theme(
        workspace.id, user.id, "Theme 2", "Problem 2", [], session
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
