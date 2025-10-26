"""Tests for roadmap theme prioritization functionality."""

import uuid

import pytest
from sqlalchemy.orm import Session

from src.models import User, Workspace
from src.roadmap_intelligence import controller as roadmap_intelligence_controller
from src.roadmap_intelligence.services.prioritization_service import (
    PrioritizationService,
)
from src.strategic_planning.exceptions import DomainException
from src.strategic_planning.services.event_publisher import EventPublisher


class TestRoadmapThemePrioritization:
    """Test suite for roadmap theme prioritization using PrioritizedRoadmap aggregate."""

    def test_create_theme_starts_unprioritized(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that newly created themes start unprioritized (not in PrioritizedRoadmap)."""
        theme = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="New Theme",
            problem_statement="Problem to solve",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        # Check theme is not in prioritized roadmap
        publisher = EventPublisher(session)
        service = PrioritizationService(session, publisher)
        roadmap = service.get_prioritized_roadmap(workspace.id)

        # Either no roadmap exists yet, or theme is not in it
        is_prioritized = roadmap.is_theme_prioritized(theme.id) if roadmap else False
        assert not is_prioritized

    def test_prioritize_theme(self, session: Session, user: User, workspace: Workspace):
        """Test prioritizing an unprioritized theme."""
        # Create unprioritized theme
        theme = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme to Prioritize",
            problem_statement="Problem",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        publisher = EventPublisher(session)
        service = PrioritizationService(session, publisher)

        # Verify theme starts unprioritized
        roadmap = service.get_prioritized_roadmap(workspace.id)
        is_prioritized = roadmap.is_theme_prioritized(theme.id) if roadmap else False
        assert not is_prioritized

        # Prioritize the theme
        prioritized_theme = roadmap_intelligence_controller.prioritize_roadmap_theme(
            theme_id=theme.id,
            new_order=0,
            workspace_id=workspace.id,
            session=session,
        )

        # Verify theme is now prioritized
        roadmap = service.get_prioritized_roadmap(workspace.id)
        assert roadmap is not None
        assert roadmap.is_theme_prioritized(theme.id)
        assert roadmap.get_prioritized_themes() == [theme.id]

    def test_deprioritize_theme(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test deprioritizing a prioritized theme."""
        # Create and prioritize a theme
        theme = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme to Deprioritize",
            problem_statement="Problem",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        roadmap_intelligence_controller.prioritize_roadmap_theme(
            theme_id=theme.id,
            new_order=0,
            workspace_id=workspace.id,
            session=session,
        )

        publisher = EventPublisher(session)
        service = PrioritizationService(session, publisher)

        # Verify theme is prioritized
        roadmap = service.get_prioritized_roadmap(workspace.id)
        assert roadmap.is_theme_prioritized(theme.id)

        # Deprioritize the theme
        deprioritized_theme = (
            roadmap_intelligence_controller.deprioritize_roadmap_theme(
                theme_id=theme.id,
                workspace_id=workspace.id,
                session=session,
            )
        )

        # Verify theme is no longer prioritized
        roadmap = service.get_prioritized_roadmap(workspace.id)
        assert not roadmap.is_theme_prioritized(theme.id)
        assert roadmap.get_prioritized_themes() == []

    def test_prioritize_already_prioritized_theme_fails(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that prioritizing an already prioritized theme raises an error."""
        theme = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Already Prioritized",
            problem_statement="Problem",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        # Prioritize once
        roadmap_intelligence_controller.prioritize_roadmap_theme(
            theme_id=theme.id,
            new_order=0,
            workspace_id=workspace.id,
            session=session,
        )

        # Try to prioritize again - should fail
        with pytest.raises(DomainException, match="already prioritized"):
            roadmap_intelligence_controller.prioritize_roadmap_theme(
                theme_id=theme.id,
                new_order=1,
                workspace_id=workspace.id,
                session=session,
            )

    def test_deprioritize_unprioritized_theme_fails(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that deprioritizing an unprioritized theme raises an error."""
        theme = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Unprioritized Theme",
            problem_statement="Problem",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        publisher = EventPublisher(session)
        service = PrioritizationService(session, publisher)

        # Verify theme is unprioritized
        roadmap = service.get_prioritized_roadmap(workspace.id)
        is_prioritized = roadmap.is_theme_prioritized(theme.id) if roadmap else False
        assert not is_prioritized

        # Try to deprioritize - should fail
        with pytest.raises(DomainException, match="already unprioritized"):
            roadmap_intelligence_controller.deprioritize_roadmap_theme(
                theme_id=theme.id,
                workspace_id=workspace.id,
                session=session,
            )

    def test_reorder_only_affects_prioritized_themes(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that reordering only affects prioritized themes."""
        # Create 3 themes: 2 will be prioritized, 1 will remain unprioritized
        theme1 = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme 1",
            problem_statement="Problem 1",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        theme2 = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme 2",
            problem_statement="Problem 2",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        theme3 = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme 3 (Unprioritized)",
            problem_statement="Problem 3",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        # Prioritize theme1 and theme2
        roadmap_intelligence_controller.prioritize_roadmap_theme(
            theme_id=theme1.id,
            new_order=0,
            workspace_id=workspace.id,
            session=session,
        )

        roadmap_intelligence_controller.prioritize_roadmap_theme(
            theme_id=theme2.id,
            new_order=1,
            workspace_id=workspace.id,
            session=session,
        )

        publisher = EventPublisher(session)
        service = PrioritizationService(session, publisher)

        # Verify initial state
        roadmap = service.get_prioritized_roadmap(workspace.id)
        assert roadmap.get_prioritized_themes() == [theme1.id, theme2.id]
        assert not roadmap.is_theme_prioritized(theme3.id)

        # Reorder prioritized themes (swap them)
        reordered_themes = roadmap_intelligence_controller.reorder_roadmap_themes(
            workspace_id=workspace.id,
            theme_orders={theme1.id: 1, theme2.id: 0},
            session=session,
        )

        # Verify prioritized themes were reordered
        roadmap = service.get_prioritized_roadmap(workspace.id)
        assert roadmap.get_prioritized_themes() == [theme2.id, theme1.id]

        # Verify unprioritized theme is still not prioritized
        assert not roadmap.is_theme_prioritized(theme3.id)

    def test_reorder_with_unprioritized_theme_id_fails(
        self, session: Session, user: User, workspace: Workspace
    ):
        """Test that including an unprioritized theme ID in reorder fails."""
        # Create 1 prioritized and 1 unprioritized theme
        theme1 = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Prioritized",
            problem_statement="Problem 1",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        theme2 = roadmap_intelligence_controller.create_roadmap_theme(
            workspace_id=workspace.id,
            user_id=user.id,
            name="Unprioritized",
            problem_statement="Problem 2",
            hypothesis=None,
            indicative_metrics=None,
            time_horizon_months=None,
            outcome_ids=[],
            session=session,
        )

        # Prioritize only theme1
        roadmap_intelligence_controller.prioritize_roadmap_theme(
            theme_id=theme1.id,
            new_order=0,
            workspace_id=workspace.id,
            session=session,
        )

        # Try to reorder with unprioritized theme2 - should fail
        with pytest.raises(DomainException, match="not prioritized"):
            roadmap_intelligence_controller.reorder_roadmap_themes(
                workspace_id=workspace.id,
                theme_orders={theme1.id: 0, theme2.id: 1},
                session=session,
            )
