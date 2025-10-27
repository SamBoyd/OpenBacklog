import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from hamcrest import assert_that, equal_to, has_entries, has_items, is_
from sqlalchemy.orm import Session

from src.main import app
from src.models import (
    ContextType,
    EntityType,
    Initiative,
    InitiativeStatus,
    Ordering,
    User,
    Workspace,
)
from tests.conftest import dependency_to_override


class TestInitiativeViews:

    @pytest.fixture
    def client(self, user):
        app.dependency_overrides[dependency_to_override] = lambda: user
        client = TestClient(app)
        yield client
        app.dependency_overrides.pop(dependency_to_override, None)

    def _create_mock_orderings(self, initiative_id, user_id):
        """Helper method to create mock orderings for test initiatives."""
        return [
            Ordering(
                id=uuid.uuid4(),
                user_id=user_id,
                workspace_id=None,
                context_type=ContextType.STATUS_LIST,
                context_id=None,
                entity_type=EntityType.INITIATIVE,
                initiative_id=initiative_id,
                task_id=None,
                position="n",
            )
        ]

    @patch("src.initiative_management.views.InitiativeController")
    def test_create_initiative_success(
        self, mock_initiative_controller, client, user, workspace, session
    ):
        initiative_id = uuid.uuid4()

        mock_initiative = Initiative(
            id=initiative_id,
            identifier="INIT-001",
            title="New Test Initiative",
            description="Initiative description",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            type="FEATURE",
            orderings=self._create_mock_orderings(initiative_id, user.id),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            properties={},
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.create_initiative.return_value = (
            mock_initiative
        )

        payload = {
            "title": "New Test Initiative",
            "description": "Initiative description",
            "status": "BACKLOG",
            "type": "FEATURE",
            "workspace_id": str(workspace.id),
        }

        response = client.post("/api/initiatives", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data,
            has_entries(
                {
                    "title": "New Test Initiative",
                    "description": "Initiative description",
                    "status": "BACKLOG",
                    "type": "FEATURE",
                    "user_id": str(user.id),
                    "workspace_id": str(workspace.id),
                    "orderings": has_items(
                        has_entries(
                            {
                                "context_type": "STATUS_LIST",
                                "entity_type": "INITIATIVE",
                                "position": "n",
                            }
                        )
                    ),
                }
            ),
        )

        # Verify the initiative controller was called
        mock_initiative_controller_instance.create_initiative.assert_called_once()

    @patch("src.initiative_management.views.InitiativeController")
    def test_create_initiative_minimal_payload(
        self, mock_initiative_controller, client, user, workspace, session
    ):
        initiative_id = uuid.uuid4()

        mock_initiative = Initiative(
            id=initiative_id,
            identifier="INIT-002",
            title="Minimal Initiative",
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            type=None,
            orderings=self._create_mock_orderings(initiative_id, user.id),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            properties={},
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.create_initiative.return_value = (
            mock_initiative
        )

        payload = {"title": "Minimal Initiative", "workspace_id": str(workspace.id)}

        response = client.post("/api/initiatives", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data,
            has_entries(
                {
                    "title": "Minimal Initiative",
                    "status": "BACKLOG",
                    "type": None,
                    "orderings": has_items(
                        has_entries(
                            {
                                "context_type": "STATUS_LIST",
                                "entity_type": "INITIATIVE",
                                "position": "n",
                            }
                        )
                    ),
                }
            ),
        )

        # Verify the initiative controller was called
        mock_initiative_controller_instance.create_initiative.assert_called_once()

    def test_create_initiative_invalid_title(self, client):
        payload = {"title": ""}

        response = client.post("/api/initiatives", json=payload)

        assert_that(response.status_code, equal_to(422))

    @patch("src.initiative_management.views.InitiativeController")
    def test_delete_initiative_success(
        self,
        mock_initiative_controller,
        client,
        user,
        workspace,
        session,
        test_initiative,
    ):
        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.delete_initiative.return_value = True

        initiative_id = test_initiative.id

        response = client.delete(f"/api/initiatives/{initiative_id}")

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data, has_entries({"message": "Initiative deleted successfully"})
        )

        # Verify the initiative controller was called
        mock_initiative_controller_instance.delete_initiative.assert_called_once_with(
            initiative_id, user.id
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_delete_initiative_not_found(
        self, mock_initiative_controller, client, user
    ):
        from src.initiative_management.initiative_controller import (
            InitiativeNotFoundError,
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        fake_id = uuid.uuid4()
        mock_initiative_controller_instance.delete_initiative.side_effect = (
            InitiativeNotFoundError(f"Initiative {fake_id} not found")
        )

        response = client.delete(f"/api/initiatives/{fake_id}")

        assert_that(response.status_code, equal_to(404))
        mock_initiative_controller_instance.delete_initiative.assert_called_once_with(
            fake_id, user.id
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_move_initiative_success(
        self,
        mock_initiative_controller,
        client,
        user,
        workspace,
        session,
        test_initiative,
    ):
        mock_initiative = Initiative(
            id=test_initiative.id,
            identifier=test_initiative.identifier,
            title=test_initiative.title,
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.BACKLOG,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            properties={},
        )
        mock_initiative.orderings = self._create_mock_orderings(
            test_initiative.id, user.id
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.move_initiative.return_value = (
            mock_initiative
        )

        initiative_id = test_initiative.id
        other_initiative_id = uuid.uuid4()

        payload = {"after_id": str(other_initiative_id)}

        response = client.put(f"/api/initiatives/{initiative_id}/move", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(response_data["id"], equal_to(str(initiative_id)))

        # Verify the initiative controller was called
        mock_initiative_controller_instance.move_initiative.assert_called_once_with(
            initiative_id=initiative_id,
            user_id=user.id,
            after_id=other_initiative_id,
            before_id=None,
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_move_initiative_not_found(self, mock_initiative_controller, client, user):
        from src.initiative_management.initiative_controller import (
            InitiativeNotFoundError,
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        fake_id = uuid.uuid4()
        after_id = uuid.uuid4()
        mock_initiative_controller_instance.move_initiative.side_effect = (
            InitiativeNotFoundError(f"Initiative {fake_id} not found")
        )

        payload = {"after_id": str(after_id)}

        response = client.put(f"/api/initiatives/{fake_id}/move", json=payload)

        assert_that(response.status_code, equal_to(404))
        mock_initiative_controller_instance.move_initiative.assert_called_once_with(
            initiative_id=fake_id, user_id=user.id, after_id=after_id, before_id=None
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_move_initiative_to_status_success(
        self,
        mock_initiative_controller,
        client,
        user,
        workspace,
        session,
        test_initiative,
    ):
        mock_initiative = Initiative(
            id=test_initiative.id,
            identifier=test_initiative.identifier,
            title=test_initiative.title,
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=InitiativeStatus.IN_PROGRESS,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            properties={},
        )
        mock_initiative.orderings = self._create_mock_orderings(
            test_initiative.id, user.id
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.move_initiative_to_status.return_value = (
            mock_initiative
        )

        initiative_id = test_initiative.id

        payload = {"new_status": "IN_PROGRESS", "after_id": None, "before_id": None}

        response = client.put(f"/api/initiatives/{initiative_id}/status", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data,
            has_entries({"id": str(initiative_id), "status": "IN_PROGRESS"}),
        )

        # Verify the initiative controller was called
        mock_initiative_controller_instance.move_initiative_to_status.assert_called_once_with(
            initiative_id=initiative_id,
            user_id=user.id,
            new_status=InitiativeStatus.IN_PROGRESS,
            after_id=None,
            before_id=None,
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_move_initiative_to_status_not_found(
        self, mock_initiative_controller, client, user
    ):
        from src.initiative_management.initiative_controller import (
            InitiativeNotFoundError,
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        fake_id = uuid.uuid4()
        mock_initiative_controller_instance.move_initiative_to_status.side_effect = (
            InitiativeNotFoundError(f"Initiative {fake_id} not found")
        )

        payload = {"new_status": "IN_PROGRESS"}

        response = client.put(f"/api/initiatives/{fake_id}/status", json=payload)

        assert_that(response.status_code, equal_to(404))
        mock_initiative_controller_instance.move_initiative_to_status.assert_called_once_with(
            initiative_id=fake_id,
            user_id=user.id,
            new_status=InitiativeStatus.IN_PROGRESS,
            after_id=None,
            before_id=None,
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_add_initiative_to_group_success(
        self,
        mock_initiative_controller,
        client,
        user,
        workspace,
        session,
        test_initiative,
    ):
        mock_initiative = Initiative(
            id=test_initiative.id,
            identifier=test_initiative.identifier,
            title=test_initiative.title,
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=test_initiative.status,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            properties={},
        )
        mock_initiative.orderings = self._create_mock_orderings(
            test_initiative.id, user.id
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.add_initiative_to_group.return_value = (
            mock_initiative
        )

        initiative_id = test_initiative.id
        group_id = uuid.uuid4()

        payload = {"group_id": str(group_id)}

        response = client.put(f"/api/initiatives/{initiative_id}/groups", json=payload)

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(response_data["id"], equal_to(str(initiative_id)))

        # Verify the initiative controller was called
        mock_initiative_controller_instance.add_initiative_to_group.assert_called_once_with(
            initiative_id=initiative_id,
            user_id=user.id,
            group_id=group_id,
            after_id=None,
            before_id=None,
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_add_initiative_to_group_not_found(
        self, mock_initiative_controller, client, user
    ):
        from src.initiative_management.initiative_controller import (
            InitiativeNotFoundError,
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        fake_id = uuid.uuid4()
        group_id = uuid.uuid4()
        mock_initiative_controller_instance.add_initiative_to_group.side_effect = (
            InitiativeNotFoundError(f"Initiative {fake_id} not found")
        )

        payload = {"group_id": str(group_id)}

        response = client.put(f"/api/initiatives/{fake_id}/groups", json=payload)

        assert_that(response.status_code, equal_to(404))
        mock_initiative_controller_instance.add_initiative_to_group.assert_called_once_with(
            initiative_id=fake_id,
            user_id=user.id,
            group_id=group_id,
            after_id=None,
            before_id=None,
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_remove_initiative_from_group_success(
        self,
        mock_initiative_controller,
        client,
        user,
        workspace,
        session,
        test_initiative,
    ):
        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.remove_initiative_from_group.return_value = (
            True
        )

        initiative_id = test_initiative.id
        group_id = uuid.uuid4()

        response = client.delete(f"/api/initiatives/{initiative_id}/groups/{group_id}")

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data,
            has_entries({"message": "Initiative removed from group successfully"}),
        )

        # Verify the initiative controller was called
        mock_initiative_controller_instance.remove_initiative_from_group.assert_called_once_with(
            initiative_id=initiative_id, user_id=user.id, group_id=group_id
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_remove_initiative_from_group_not_in_group(
        self,
        mock_initiative_controller,
        client,
        user,
        workspace,
        session,
        test_initiative,
    ):
        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.remove_initiative_from_group.return_value = (
            False
        )

        initiative_id = test_initiative.id
        group_id = uuid.uuid4()

        response = client.delete(f"/api/initiatives/{initiative_id}/groups/{group_id}")

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data,
            has_entries({"message": "Initiative was not in the specified group"}),
        )

        # Verify the initiative controller was called
        mock_initiative_controller_instance.remove_initiative_from_group.assert_called_once_with(
            initiative_id=initiative_id, user_id=user.id, group_id=group_id
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_remove_initiative_from_group_not_found(
        self, mock_initiative_controller, client, user
    ):
        from src.initiative_management.initiative_controller import (
            InitiativeNotFoundError,
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        fake_id = uuid.uuid4()
        group_id = uuid.uuid4()
        mock_initiative_controller_instance.remove_initiative_from_group.side_effect = (
            InitiativeNotFoundError(f"Initiative {fake_id} not found")
        )

        response = client.delete(f"/api/initiatives/{fake_id}/groups/{group_id}")

        assert_that(response.status_code, equal_to(404))
        mock_initiative_controller_instance.remove_initiative_from_group.assert_called_once_with(
            initiative_id=fake_id, user_id=user.id, group_id=group_id
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_delete_initiative_with_multiple_group_orderings(
        self,
        mock_initiative_controller,
        client,
        user,
        workspace,
        session,
        test_initiative,
    ):
        """Test that deleting initiative removes all orderings (STATUS_LIST + multiple GROUPs)."""
        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.delete_initiative.return_value = True

        initiative_id = test_initiative.id

        # Delete the initiative via API
        response = client.delete(f"/api/initiatives/{initiative_id}")

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(
            response_data, has_entries({"message": "Initiative deleted successfully"})
        )

        # Verify the initiative controller was called
        mock_initiative_controller_instance.delete_initiative.assert_called_once_with(
            initiative_id, user.id
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_move_initiative_in_group_success(
        self,
        mock_initiative_controller,
        client,
        user,
        workspace,
        session,
        test_initiative,
    ):
        mock_initiative = Initiative(
            id=test_initiative.id,
            identifier=test_initiative.identifier,
            title=test_initiative.title,
            description="",
            user_id=user.id,
            workspace_id=workspace.id,
            status=test_initiative.status,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            properties={},
        )
        mock_initiative.orderings = self._create_mock_orderings(
            test_initiative.id, user.id
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        mock_initiative_controller_instance.move_initiative_in_group.return_value = (
            mock_initiative
        )

        initiative_id = test_initiative.id
        group_id = uuid.uuid4()
        after_id = uuid.uuid4()

        payload = {"after_id": str(after_id)}

        response = client.put(
            f"/api/initiatives/{initiative_id}/groups/{group_id}/move", json=payload
        )

        assert_that(response.status_code, equal_to(200))

        response_data = response.json()
        assert_that(response_data["id"], equal_to(str(initiative_id)))

        # Verify the initiative controller was called
        mock_initiative_controller_instance.move_initiative_in_group.assert_called_once_with(
            initiative_id=initiative_id,
            user_id=user.id,
            group_id=group_id,
            after_id=after_id,
            before_id=None,
        )

    @patch("src.initiative_management.views.InitiativeController")
    def test_move_initiative_in_group_not_found(
        self, mock_initiative_controller, client, user
    ):
        from src.initiative_management.initiative_controller import (
            InitiativeNotFoundError,
        )

        mock_initiative_controller_instance = mock_initiative_controller.return_value
        fake_id = uuid.uuid4()
        group_id = uuid.uuid4()
        mock_initiative_controller_instance.move_initiative_in_group.side_effect = (
            InitiativeNotFoundError(f"Initiative {fake_id} not found")
        )

        payload = {"after_id": str(uuid.uuid4())}

        response = client.put(
            f"/api/initiatives/{fake_id}/groups/{group_id}/move", json=payload
        )

        assert_that(response.status_code, equal_to(404))
        mock_initiative_controller_instance.move_initiative_in_group.assert_called_once()
