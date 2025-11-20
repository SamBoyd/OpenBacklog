"""Tests for product strategy views."""

import uuid

from fastapi.testclient import TestClient
from hamcrest import assert_that, equal_to, has_key

from src.models import Workspace
from src.strategic_planning import ProductVision


class TestVisionViews:
    def test_get_vision_unauthorized(
        self, test_client_no_user: TestClient, workspace: Workspace
    ):
        """Test getting vision without authentication returns 401."""
        response = test_client_no_user.get(f"/api/workspaces/{workspace.id}/vision")
        assert_that(response.status_code, equal_to(401))

    def test_get_vision_success(
        self,
        test_client: TestClient,
        workspace: Workspace,
        product_vision: ProductVision,
    ):
        """Test getting existing vision returns 200."""
        response = test_client.get(f"/api/workspaces/{workspace.id}/vision")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["vision_text"], equal_to(product_vision.vision_text))
        assert_that(data, has_key("id"))
        assert_that(data, has_key("workspace_id"))
        assert_that(data, has_key("created_at"))
        assert_that(data, has_key("updated_at"))

    def test_upsert_vision_create(self, test_client: TestClient, workspace: Workspace):
        """Test creating new vision returns 200."""
        response = test_client.put(
            f"/api/workspaces/{workspace.id}/vision",
            json={"vision_text": "Build the best product"},
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["vision_text"], equal_to("Build the best product"))
        assert_that(data["workspace_id"], equal_to(str(workspace.id)))

    def test_upsert_vision_update(
        self,
        test_client: TestClient,
        workspace: Workspace,
        product_vision: ProductVision,
    ):
        """Test updating existing vision returns 200."""
        new_text = "Updated vision text"
        response = test_client.put(
            f"/api/workspaces/{workspace.id}/vision",
            json={"vision_text": new_text},
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["vision_text"], equal_to(new_text))
        assert_that(data["id"], equal_to(str(product_vision.id)))

    def test_upsert_vision_validation_error_empty(
        self, test_client: TestClient, workspace: Workspace
    ):
        """Test validation error for empty vision returns 422."""
        response = test_client.put(
            f"/api/workspaces/{workspace.id}/vision",
            json={"vision_text": ""},
        )

        assert_that(response.status_code, equal_to(422))

    def test_upsert_vision_validation_error_too_long(
        self, test_client: TestClient, workspace: Workspace
    ):
        """Test validation error for text exceeding max length returns 422."""
        response = test_client.put(
            f"/api/workspaces/{workspace.id}/vision",
            json={"vision_text": "A" * 1001},
        )

        assert_that(response.status_code, equal_to(422))

    def test_upsert_vision_workspace_not_found(self, test_client: TestClient):
        """Test upserting vision for non-existent workspace returns 500."""
        fake_workspace_id = uuid.uuid4()
        response = test_client.put(
            f"/api/workspaces/{fake_workspace_id}/vision",
            json={"vision_text": "Some vision text"},
        )

        assert_that(response.status_code, equal_to(500))

    def test_upsert_vision_unauthorized(
        self, test_client_no_user: TestClient, workspace: Workspace
    ):
        """Test upserting vision without authentication returns 401."""
        response = test_client_no_user.put(
            f"/api/workspaces/{workspace.id}/vision",
            json={"vision_text": "Some vision text"},
        )

        assert_that(response.status_code, equal_to(401))
