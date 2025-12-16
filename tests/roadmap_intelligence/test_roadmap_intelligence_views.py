"""Unit tests for roadmap intelligence views."""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from hamcrest import assert_that, equal_to, has_entries

from src.strategic_planning.exceptions import DomainException


class TestThemeViews:
    """Test cases for roadmap theme CRUD endpoints."""

    @pytest.fixture
    def mock_theme(self, user, workspace):
        """Create a mock RoadmapTheme for testing."""
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        theme = RoadmapTheme(
            id=uuid.uuid4(),
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Theme",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = []
        theme.villains = []
        return theme

    @patch("src.roadmap_intelligence.views.controller.get_roadmap_themes")
    def test_get_workspace_themes_success(
        self, mock_get_themes, test_client, workspace, mock_theme
    ):
        """Test getting all themes returns list."""
        mock_get_themes.return_value = [mock_theme]

        response = test_client.get(f"/api/workspaces/{workspace.id}/themes")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(1))
        assert_that(
            data[0],
            has_entries(
                {
                    "id": str(mock_theme.id),
                    "identifier": mock_theme.identifier,
                    "workspace_id": str(workspace.id),
                    "name": "Test Theme",
                    "description": "Test description",
                    "outcome_ids": [],
                    "hero_ids": [],
                    "villain_ids": [],
                }
            ),
        )
        mock_get_themes.assert_called_once()

    @patch("src.roadmap_intelligence.views.controller.get_roadmap_themes")
    def test_get_workspace_themes_empty(self, mock_get_themes, test_client, workspace):
        """Test getting themes when none exist returns empty list."""
        mock_get_themes.return_value = []

        response = test_client.get(f"/api/workspaces/{workspace.id}/themes")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data, equal_to([]))

    @patch("src.roadmap_intelligence.views.controller.get_roadmap_themes")
    def test_get_workspace_themes_error(self, mock_get_themes, test_client, workspace):
        """Test getting themes with error returns 500."""
        mock_get_themes.side_effect = Exception("Database error")

        response = test_client.get(f"/api/workspaces/{workspace.id}/themes")

        assert_that(response.status_code, equal_to(500))
        assert_that(response.json()["detail"], equal_to("Failed to get themes"))

    @patch("src.roadmap_intelligence.views.controller.create_roadmap_theme")
    def test_create_roadmap_theme_success_all_fields(
        self, mock_create, test_client, user, workspace, mock_theme
    ):
        """Test creating theme with all fields returns 201."""
        mock_create.return_value = mock_theme

        payload = {
            "name": "Test Theme",
            "identifier": "T-001",
            "description": "Test description",
            "outcome_ids": [],
        }

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes", json=payload
        )

        assert_that(response.status_code, equal_to(201))
        data = response.json()
        assert_that(
            data,
            has_entries(
                {
                    "name": "Test Theme",
                    "identifier": "T-001",
                    "description": "Test description",
                }
            ),
        )
        mock_create.assert_called_once()

    def test_create_roadmap_theme_validation_empty_name(self, test_client, workspace):
        """Test validation error for empty name returns 422."""
        payload = {
            "name": "",
            "identifier": "T-001",
            "description": "Test description",
        }

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes", json=payload
        )

        assert_that(response.status_code, equal_to(422))

    def test_create_roadmap_theme_validation_name_too_long(
        self, test_client, workspace
    ):
        """Test validation error for name exceeding max length returns 422."""
        payload = {
            "name": "A" * 101,
            "description": "Test description",
        }

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes", json=payload
        )

        assert_that(response.status_code, equal_to(422))

    def test_create_roadmap_theme_validation_description_too_long(
        self, test_client, workspace
    ):
        """Test validation error for description exceeding max length returns 400."""
        payload = {
            "name": "Valid Name",
            "description": "A" * 4001,
        }

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes", json=payload
        )

        assert_that(response.status_code, equal_to(400))

    @patch("src.roadmap_intelligence.views.controller.create_roadmap_theme")
    def test_create_roadmap_theme_limit_exceeded(
        self, mock_create, test_client, workspace
    ):
        """Test creating theme when limit exceeded returns 400."""
        mock_create.side_effect = DomainException(
            "Workspace has reached maximum of 5 roadmap themes"
        )

        payload = {
            "name": "Theme 6",
            "description": "Test description",
        }

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes", json=payload
        )

        assert_that(response.status_code, equal_to(400))
        assert_that(
            response.json()["detail"],
            equal_to("Workspace has reached maximum of 5 roadmap themes"),
        )

    @patch("src.roadmap_intelligence.views.controller.update_roadmap_theme")
    def test_update_roadmap_theme_success_all_fields(
        self, mock_update, test_client, user, workspace, mock_theme
    ):
        """Test updating theme with all fields returns 200."""
        updated_theme = mock_theme
        updated_theme.name = "Updated Theme"
        mock_update.return_value = updated_theme

        payload = {
            "name": "Updated Theme",
            "description": "Updated description",
            "outcome_ids": [],
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/{mock_theme.id}", json=payload
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["id"], equal_to(str(mock_theme.id)))
        assert_that(data["name"], equal_to("Updated Theme"))
        mock_update.assert_called_once()

    @patch("src.roadmap_intelligence.views.controller.update_roadmap_theme")
    def test_update_roadmap_theme_success_name_only(
        self, mock_update, test_client, workspace, mock_theme
    ):
        """Test updating theme name only returns 200."""
        updated_theme = mock_theme
        updated_theme.name = "Updated Name"
        mock_update.return_value = updated_theme

        payload = {
            "name": "Updated Name",
            "description": "Test description",
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/{mock_theme.id}", json=payload
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["name"], equal_to("Updated Name"))

    @patch("src.roadmap_intelligence.views.controller.update_roadmap_theme")
    def test_update_roadmap_theme_not_found(self, mock_update, test_client, workspace):
        """Test updating non-existent theme returns 404."""
        fake_id = uuid.uuid4()
        mock_update.side_effect = DomainException("Roadmap theme not found")

        payload = {
            "name": "Updated Name",
            "description": "Test description",
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/{fake_id}", json=payload
        )

        assert_that(response.status_code, equal_to(404))

    def test_update_roadmap_theme_validation_empty_name(self, test_client, workspace):
        """Test validation error for empty name returns 422."""
        fake_id = uuid.uuid4()
        payload = {
            "name": "",
            "description": "Test description",
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/{fake_id}", json=payload
        )

        assert_that(response.status_code, equal_to(422))

    @patch("src.roadmap_intelligence.views.controller.delete_roadmap_theme")
    def test_delete_roadmap_theme_success(
        self, mock_delete, test_client, user, workspace, session
    ):
        """Test deleting theme returns 204."""
        theme_id = uuid.uuid4()
        mock_delete.return_value = None

        response = test_client.delete(
            f"/api/workspaces/{workspace.id}/themes/{theme_id}"
        )

        assert_that(response.status_code, equal_to(204))
        # Verify controller was called (session is auto-injected by FastAPI)
        assert mock_delete.called

    @patch("src.roadmap_intelligence.views.controller.delete_roadmap_theme")
    def test_delete_roadmap_theme_not_found(self, mock_delete, test_client, workspace):
        """Test deleting non-existent theme returns 404."""
        fake_id = uuid.uuid4()
        mock_delete.side_effect = DomainException("Roadmap theme not found")

        response = test_client.delete(
            f"/api/workspaces/{workspace.id}/themes/{fake_id}"
        )

        assert_that(response.status_code, equal_to(404))

    @patch("src.roadmap_intelligence.views.controller.reorder_roadmap_themes")
    def test_reorder_roadmap_themes_success(
        self, mock_reorder, test_client, workspace, mock_theme
    ):
        """Test reordering themes returns 200."""
        theme1 = mock_theme
        theme2_id = uuid.uuid4()

        mock_reorder.return_value = [theme1]

        payload = {
            "themes": [
                {"id": str(theme1.id), "display_order": 0},
                {"id": str(theme2_id), "display_order": 1},
            ]
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/reorder", json=payload
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(1))
        mock_reorder.assert_called_once()

    @patch("src.roadmap_intelligence.views.controller.reorder_roadmap_themes")
    def test_reorder_roadmap_themes_unprioritized(
        self, mock_reorder, test_client, workspace
    ):
        """Test reordering unprioritized themes returns 400."""
        theme_id = uuid.uuid4()
        mock_reorder.side_effect = DomainException("Themes are not prioritized")

        payload = {
            "themes": [
                {"id": str(theme_id), "display_order": 0},
            ]
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/reorder", json=payload
        )

        assert_that(response.status_code, equal_to(400))

    @patch("src.roadmap_intelligence.views.controller.reorder_roadmap_themes")
    def test_reorder_roadmap_themes_not_found(
        self, mock_reorder, test_client, workspace
    ):
        """Test reordering with invalid theme ID returns 404."""
        theme_id = uuid.uuid4()
        mock_reorder.side_effect = DomainException("Theme not found")

        payload = {
            "themes": [
                {"id": str(theme_id), "display_order": 0},
            ]
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/reorder", json=payload
        )

        assert_that(response.status_code, equal_to(404))

    def test_reorder_roadmap_themes_validation_display_order_too_high(
        self, test_client, workspace
    ):
        """Test validation error for display_order > 4 returns 422."""
        theme_id = uuid.uuid4()
        payload = {
            "themes": [
                {"id": str(theme_id), "display_order": 5},
            ]
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/reorder", json=payload
        )

        assert_that(response.status_code, equal_to(422))

    @patch("src.roadmap_intelligence.views.controller.get_roadmap_themes")
    def test_get_workspace_themes_with_heroes_and_villains(
        self, mock_get_themes, test_client, user, workspace
    ):
        """Test getting themes includes hero_ids and villain_ids."""
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        hero_id_1 = uuid.uuid4()
        hero_id_2 = uuid.uuid4()
        villain_id_1 = uuid.uuid4()
        villain_id_2 = uuid.uuid4()

        # Create mock hero and villain objects
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain

        mock_hero_1 = Hero(
            id=hero_id_1,
            name="Hero 1",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_hero_2 = Hero(
            id=hero_id_2,
            name="Hero 2",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain_1 = Villain(
            id=villain_id_1,
            name="Villain 1",
            description="Test",
            villain_type="EXTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain_2 = Villain(
            id=villain_id_2,
            name="Villain 2",
            description="Test",
            villain_type="INTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        theme = RoadmapTheme(
            id=uuid.uuid4(),
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme with Heroes/Villains",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = [mock_hero_1, mock_hero_2]
        theme.villains = [mock_villain_1, mock_villain_2]

        mock_get_themes.return_value = [theme]

        response = test_client.get(f"/api/workspaces/{workspace.id}/themes")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(1))
        assert_that(
            data[0],
            has_entries(
                {
                    "id": str(theme.id),
                    "identifier": theme.identifier,
                    "hero_ids": [str(hero_id_1), str(hero_id_2)],
                    "villain_ids": [str(villain_id_1), str(villain_id_2)],
                }
            ),
        )

    @patch("src.roadmap_intelligence.views.controller.create_roadmap_theme")
    def test_create_roadmap_theme_returns_hero_and_villain_ids(
        self, mock_create, test_client, user, workspace
    ):
        """Test creating theme returns hero_ids and villain_ids in response."""
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        hero_id = uuid.uuid4()
        villain_id = uuid.uuid4()

        mock_hero = Hero(
            id=hero_id,
            name="Hero",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain = Villain(
            id=villain_id,
            name="Villain",
            description="Test",
            villain_type="EXTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        theme = RoadmapTheme(
            id=uuid.uuid4(),
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="New Theme",
            description="New description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = [mock_hero]
        theme.villains = [mock_villain]

        mock_create.return_value = theme

        payload = {
            "name": "New Theme",
            "description": "New description",
            "outcome_ids": [],
        }

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes", json=payload
        )

        assert_that(response.status_code, equal_to(201))
        data = response.json()
        assert_that(data["identifier"], equal_to(theme.identifier))
        assert_that(data["hero_ids"], equal_to([str(hero_id)]))
        assert_that(data["villain_ids"], equal_to([str(villain_id)]))

    @patch("src.roadmap_intelligence.views.controller.update_roadmap_theme")
    def test_update_roadmap_theme_returns_hero_and_villain_ids(
        self, mock_update, test_client, user, workspace
    ):
        """Test updating theme returns hero_ids and villain_ids in response."""
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        theme_id = uuid.uuid4()
        hero_id = uuid.uuid4()
        villain_id = uuid.uuid4()

        mock_hero = Hero(
            id=hero_id,
            name="Hero",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain = Villain(
            id=villain_id,
            name="Villain",
            description="Test",
            villain_type="EXTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        theme = RoadmapTheme(
            id=theme_id,
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Updated Theme",
            description="Updated description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = [mock_hero]
        theme.villains = [mock_villain]

        mock_update.return_value = theme

        payload = {
            "name": "Updated Theme",
            "description": "Updated description",
            "outcome_ids": [],
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/{theme_id}", json=payload
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["hero_ids"], equal_to([str(hero_id)]))
        assert_that(data["villain_ids"], equal_to([str(villain_id)]))

    @patch("src.roadmap_intelligence.views.controller.reorder_roadmap_themes")
    def test_reorder_roadmap_themes_returns_hero_and_villain_ids(
        self, mock_reorder, test_client, user, workspace
    ):
        """Test reordering themes returns hero_ids and villain_ids in response."""
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        theme_id_1 = uuid.uuid4()
        theme_id_2 = uuid.uuid4()
        hero_id = uuid.uuid4()
        villain_id = uuid.uuid4()

        mock_hero = Hero(
            id=hero_id,
            name="Hero",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain = Villain(
            id=villain_id,
            name="Villain",
            description="Test",
            villain_type="EXTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        theme1 = RoadmapTheme(
            id=theme_id_1,
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme 1",
            description="Description 1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme1.outcomes = []
        theme1.heroes = [mock_hero]
        theme1.villains = [mock_villain]

        theme2 = RoadmapTheme(
            id=theme_id_2,
            identifier="T-002",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme 2",
            description="Description 2",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme2.outcomes = []
        theme2.heroes = []
        theme2.villains = []

        mock_reorder.return_value = [theme1, theme2]

        payload = {
            "themes": [
                {"id": str(theme_id_1), "display_order": 0},
                {"id": str(theme_id_2), "display_order": 1},
            ]
        }

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/themes/reorder", json=payload
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(2))
        assert_that(data[0]["hero_ids"], equal_to([str(hero_id)]))
        assert_that(data[0]["villain_ids"], equal_to([str(villain_id)]))
        assert_that(data[1]["hero_ids"], equal_to([]))
        assert_that(data[1]["villain_ids"], equal_to([]))


class TestThemePrioritizationViews:
    """Test cases for theme prioritization endpoints."""

    @pytest.fixture
    def mock_theme(self, user, workspace):
        """Create a mock RoadmapTheme for testing."""
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        theme = RoadmapTheme(
            id=uuid.uuid4(),
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Test Theme",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = []
        theme.villains = []
        return theme

    @patch("src.roadmap_intelligence.views.controller.get_prioritized_themes")
    def test_get_prioritized_themes_success(
        self, mock_get_prioritized, test_client, workspace, mock_theme
    ):
        """Test getting prioritized themes returns list in order."""
        mock_get_prioritized.return_value = [mock_theme]

        response = test_client.get(f"/api/workspaces/{workspace.id}/themes/prioritized")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(1))
        assert_that(data[0]["id"], equal_to(str(mock_theme.id)))
        mock_get_prioritized.assert_called_once()

    @patch("src.roadmap_intelligence.views.controller.get_prioritized_themes")
    def test_get_prioritized_themes_empty(
        self, mock_get_prioritized, test_client, workspace
    ):
        """Test getting prioritized themes when none exist returns empty list."""
        mock_get_prioritized.return_value = []

        response = test_client.get(f"/api/workspaces/{workspace.id}/themes/prioritized")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data, equal_to([]))

    @patch("src.roadmap_intelligence.views.controller.get_prioritized_themes")
    def test_get_prioritized_themes_error(
        self, mock_get_prioritized, test_client, workspace
    ):
        """Test getting prioritized themes with error returns 500."""
        mock_get_prioritized.side_effect = Exception("Database error")

        response = test_client.get(f"/api/workspaces/{workspace.id}/themes/prioritized")

        assert_that(response.status_code, equal_to(500))
        assert_that(
            response.json()["detail"], equal_to("Failed to get prioritized themes")
        )

    @patch("src.roadmap_intelligence.views.controller.get_unprioritized_themes")
    def test_get_unprioritized_themes_success(
        self, mock_get_unprioritized, test_client, workspace, mock_theme
    ):
        """Test getting unprioritized themes returns list."""
        mock_get_unprioritized.return_value = [mock_theme]

        response = test_client.get(
            f"/api/workspaces/{workspace.id}/themes/unprioritized"
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(1))
        assert_that(data[0]["id"], equal_to(str(mock_theme.id)))
        mock_get_unprioritized.assert_called_once()

    @patch("src.roadmap_intelligence.views.controller.get_unprioritized_themes")
    def test_get_unprioritized_themes_empty(
        self, mock_get_unprioritized, test_client, workspace
    ):
        """Test getting unprioritized themes when none exist returns empty list."""
        mock_get_unprioritized.return_value = []

        response = test_client.get(
            f"/api/workspaces/{workspace.id}/themes/unprioritized"
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data, equal_to([]))

    @patch("src.roadmap_intelligence.views.controller.prioritize_roadmap_theme")
    def test_prioritize_theme_success(
        self, mock_prioritize, test_client, workspace, mock_theme
    ):
        """Test prioritizing theme returns 200."""
        mock_prioritize.return_value = mock_theme

        payload = {"position": 0}

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{mock_theme.id}/prioritize",
            json=payload,
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["id"], equal_to(str(mock_theme.id)))
        mock_prioritize.assert_called_once()

    @patch("src.roadmap_intelligence.views.controller.prioritize_roadmap_theme")
    def test_prioritize_theme_not_found(self, mock_prioritize, test_client, workspace):
        """Test prioritizing non-existent theme returns 404."""
        fake_id = uuid.uuid4()
        mock_prioritize.side_effect = DomainException("Roadmap theme not found")

        payload = {"position": 0}

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{fake_id}/prioritize",
            json=payload,
        )

        assert_that(response.status_code, equal_to(404))

    @patch("src.roadmap_intelligence.views.controller.prioritize_roadmap_theme")
    def test_prioritize_theme_already_prioritized(
        self, mock_prioritize, test_client, workspace, mock_theme
    ):
        """Test prioritizing already prioritized theme returns 400."""
        mock_prioritize.side_effect = DomainException("Theme is already prioritized")

        payload = {"position": 0}

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{mock_theme.id}/prioritize",
            json=payload,
        )

        assert_that(response.status_code, equal_to(400))

    def test_prioritize_theme_validation_negative_position(
        self, test_client, workspace
    ):
        """Test validation error for negative position returns 422."""
        theme_id = uuid.uuid4()
        payload = {"position": -1}

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{theme_id}/prioritize",
            json=payload,
        )

        assert_that(response.status_code, equal_to(422))

    @patch("src.roadmap_intelligence.views.controller.deprioritize_roadmap_theme")
    def test_deprioritize_theme_success(
        self, mock_deprioritize, test_client, workspace, mock_theme
    ):
        """Test deprioritizing theme returns 200."""
        mock_deprioritize.return_value = mock_theme

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{mock_theme.id}/deprioritize"
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["id"], equal_to(str(mock_theme.id)))
        mock_deprioritize.assert_called_once()

    @patch("src.roadmap_intelligence.views.controller.deprioritize_roadmap_theme")
    def test_deprioritize_theme_not_found(
        self, mock_deprioritize, test_client, workspace
    ):
        """Test deprioritizing non-existent theme returns 404."""
        fake_id = uuid.uuid4()
        mock_deprioritize.side_effect = DomainException("Roadmap theme not found")

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{fake_id}/deprioritize"
        )

        assert_that(response.status_code, equal_to(404))

    @patch("src.roadmap_intelligence.views.controller.deprioritize_roadmap_theme")
    def test_deprioritize_theme_not_prioritized(
        self, mock_deprioritize, test_client, workspace, mock_theme
    ):
        """Test deprioritizing unprioritized theme returns 400."""
        mock_deprioritize.side_effect = DomainException("Theme is not prioritized")

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{mock_theme.id}/deprioritize"
        )

        assert_that(response.status_code, equal_to(400))

    @patch("src.roadmap_intelligence.views.controller.get_prioritized_themes")
    def test_get_prioritized_themes_includes_hero_and_villain_ids(
        self, mock_get_prioritized, test_client, user, workspace
    ):
        """Test get prioritized themes includes hero_ids and villain_ids."""
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        hero_id = uuid.uuid4()
        villain_id = uuid.uuid4()

        mock_hero = Hero(
            id=hero_id,
            name="Hero",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain = Villain(
            id=villain_id,
            name="Villain",
            description="Test",
            villain_type="EXTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        theme = RoadmapTheme(
            id=uuid.uuid4(),
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Prioritized Theme",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = [mock_hero]
        theme.villains = [mock_villain]

        mock_get_prioritized.return_value = [theme]

        response = test_client.get(f"/api/workspaces/{workspace.id}/themes/prioritized")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(1))
        assert_that(data[0]["hero_ids"], equal_to([str(hero_id)]))
        assert_that(data[0]["villain_ids"], equal_to([str(villain_id)]))

    @patch("src.roadmap_intelligence.views.controller.get_unprioritized_themes")
    def test_get_unprioritized_themes_includes_hero_and_villain_ids(
        self, mock_get_unprioritized, test_client, user, workspace
    ):
        """Test get unprioritized themes includes hero_ids and villain_ids."""
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        hero_id = uuid.uuid4()
        villain_id = uuid.uuid4()

        mock_hero = Hero(
            id=hero_id,
            name="Hero",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain = Villain(
            id=villain_id,
            name="Villain",
            description="Test",
            villain_type="EXTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        theme = RoadmapTheme(
            id=uuid.uuid4(),
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Unprioritized Theme",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = [mock_hero]
        theme.villains = [mock_villain]

        mock_get_unprioritized.return_value = [theme]

        response = test_client.get(
            f"/api/workspaces/{workspace.id}/themes/unprioritized"
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(1))
        assert_that(data[0]["hero_ids"], equal_to([str(hero_id)]))
        assert_that(data[0]["villain_ids"], equal_to([str(villain_id)]))

    @patch("src.roadmap_intelligence.views.controller.prioritize_roadmap_theme")
    def test_prioritize_theme_returns_hero_and_villain_ids(
        self, mock_prioritize, test_client, user, workspace
    ):
        """Test prioritizing theme returns hero_ids and villain_ids."""
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        theme_id = uuid.uuid4()
        hero_id = uuid.uuid4()
        villain_id = uuid.uuid4()

        mock_hero = Hero(
            id=hero_id,
            name="Hero",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain = Villain(
            id=villain_id,
            name="Villain",
            description="Test",
            villain_type="EXTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        theme = RoadmapTheme(
            id=theme_id,
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = [mock_hero]
        theme.villains = [mock_villain]

        mock_prioritize.return_value = theme

        payload = {"position": 0}

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{theme_id}/prioritize",
            json=payload,
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["hero_ids"], equal_to([str(hero_id)]))
        assert_that(data["villain_ids"], equal_to([str(villain_id)]))

    @patch("src.roadmap_intelligence.views.controller.deprioritize_roadmap_theme")
    def test_deprioritize_theme_returns_hero_and_villain_ids(
        self, mock_deprioritize, test_client, user, workspace
    ):
        """Test deprioritizing theme returns hero_ids and villain_ids."""
        from src.narrative.aggregates.hero import Hero
        from src.narrative.aggregates.villain import Villain
        from src.roadmap_intelligence.aggregates.roadmap_theme import RoadmapTheme

        theme_id = uuid.uuid4()
        hero_id = uuid.uuid4()
        villain_id = uuid.uuid4()

        mock_hero = Hero(
            id=hero_id,
            name="Hero",
            description="Test",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_villain = Villain(
            id=villain_id,
            name="Villain",
            description="Test",
            villain_type="EXTERNAL",
            workspace_id=workspace.id,
            user_id=user.id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        theme = RoadmapTheme(
            id=theme_id,
            identifier="T-001",
            workspace_id=workspace.id,
            user_id=user.id,
            name="Theme",
            description="Test description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        theme.outcomes = []
        theme.heroes = [mock_hero]
        theme.villains = [mock_villain]

        mock_deprioritize.return_value = theme

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/themes/{theme_id}/deprioritize"
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["hero_ids"], equal_to([str(hero_id)]))
        assert_that(data["villain_ids"], equal_to([str(villain_id)]))
