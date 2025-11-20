"""Tests for product strategy views."""

import uuid

from hamcrest import assert_that, equal_to, has_key

# Strategic Pillar View Tests


class TestStrategicPillarViews:
    def test_get_pillars_empty(self, test_client, workspace):
        """Test getting pillars when none exist returns empty list."""
        response = test_client.get(f"/api/workspaces/{workspace.id}/pillars")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data, equal_to([]))

    def test_get_pillars_returns_list(self, test_client, workspace, user):
        """Test getting pillars returns list of pillars."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar1 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 1", None, session
            )
            pillar2 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 2", "Description 2", session
            )
        finally:
            session.close()

        response = test_client.get(f"/api/workspaces/{workspace.id}/pillars")

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(len(data), equal_to(2))
        assert_that(data[0]["name"], equal_to("Pillar 1"))
        assert_that(data[1]["name"], equal_to("Pillar 2"))
        assert_that(data[0], has_key("id"))
        assert_that(data[0], has_key("workspace_id"))
        assert_that(data[0], has_key("display_order"))
        assert_that(data[0], has_key("outcome_ids"))
        assert_that(data[0]["outcome_ids"], equal_to([]))

    def test_get_pillars_unauthorized(self, test_client_no_user, workspace):
        """Test getting pillars without authentication returns 401."""
        response = test_client_no_user.get(f"/api/workspaces/{workspace.id}/pillars")
        assert_that(response.status_code, equal_to(401))

    def test_create_pillar_success_all_fields(self, test_client, workspace):
        """Test creating pillar with all fields returns 201."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={
                "name": "Developer Experience",
                "description": "Make developers love our product",
            },
        )

        assert_that(response.status_code, equal_to(201))
        data = response.json()
        assert_that(data["name"], equal_to("Developer Experience"))
        assert_that(data["description"], equal_to("Make developers love our product"))
        assert_that(data["workspace_id"], equal_to(str(workspace.id)))
        assert_that(data["display_order"], equal_to(0))
        assert_that(data, has_key("outcome_ids"))
        assert_that(data["outcome_ids"], equal_to([]))

    def test_create_pillar_success_name_only(self, test_client, workspace):
        """Test creating pillar with only name returns 201."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={"name": "Developer Experience"},
        )

        assert_that(response.status_code, equal_to(201))
        data = response.json()
        assert_that(data["name"], equal_to("Developer Experience"))
        assert_that(data["description"], equal_to(None))
        assert_that(data, has_key("outcome_ids"))
        assert_that(data["outcome_ids"], equal_to([]))

    def test_create_pillar_validation_error_empty_name(self, test_client, workspace):
        """Test validation error for empty name returns 422."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={"name": ""},
        )

        assert_that(response.status_code, equal_to(422))

    def test_create_pillar_validation_error_name_too_long(self, test_client, workspace):
        """Test validation error for name exceeding max length returns 422."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={"name": "A" * 101},
        )

        assert_that(response.status_code, equal_to(422))

    def test_create_pillar_validation_error_description_too_long(
        self, test_client, workspace
    ):
        """Test validation error for description exceeding max length returns 500 (database constraint)."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={"name": "Valid Name", "description": "A" * 1001},
        )

        assert_that(response.status_code, equal_to(500))

    def test_create_pillar_enforces_5_pillar_limit(self, test_client, workspace, user):
        """Test creating 6th pillar returns 400 error."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            # Create 5 pillars
            for i in range(5):
                product_strategy_controller.create_strategic_pillar(
                    workspace.id, user.id, f"Pillar {i}", None, session
                )
        finally:
            session.close()

        # Attempt to create 6th pillar
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={"name": "Pillar 6"},
        )

        assert_that(response.status_code, equal_to(400))
        assert_that(
            response.json()["detail"],
            equal_to("Workspace has reached maximum of 5 strategic pillars"),
        )

    def test_create_pillar_enforces_unique_name(self, test_client, workspace):
        """Test creating duplicate pillar name returns 500."""
        test_client.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={"name": "Developer Experience"},
        )

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={"name": "Developer Experience"},
        )

        assert_that(response.status_code, equal_to(500))

    def test_create_pillar_workspace_not_found(self, test_client):
        """Test creating pillar for non-existent workspace returns 500."""
        fake_workspace_id = uuid.uuid4()
        response = test_client.post(
            f"/api/workspaces/{fake_workspace_id}/pillars",
            json={"name": "Some pillar"},
        )

        assert_that(response.status_code, equal_to(500))

    def test_create_pillar_unauthorized(self, test_client_no_user, workspace):
        """Test creating pillar without authentication returns 401."""
        response = test_client_no_user.post(
            f"/api/workspaces/{workspace.id}/pillars",
            json={"name": "Some pillar"},
        )

        assert_that(response.status_code, equal_to(401))

    # Update Pillar View Tests

    def test_update_pillar_success_all_fields(self, test_client, workspace, user):
        """Test updating pillar with all fields returns 200."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar = product_strategy_controller.create_strategic_pillar(
                workspace.id,
                user.id,
                "Original Name",
                "Original desc",
                session,
            )
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
            json={
                "name": "Updated Name",
                "description": "Updated description",
            },
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["id"], equal_to(str(pillar.id)))
        assert_that(data["name"], equal_to("Updated Name"))
        assert_that(data["description"], equal_to("Updated description"))

    def test_update_pillar_success_name_only(self, test_client, workspace, user):
        """Test updating pillar name only returns 200."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Original Name", None, session
            )
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
            json={"name": "Updated Name"},
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["name"], equal_to("Updated Name"))

    def test_update_pillar_validation_error_empty_name(
        self, test_client, workspace, user
    ):
        """Test validation error for empty name returns 422."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Original Name", None, session
            )
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
            json={"name": ""},
        )

        assert_that(response.status_code, equal_to(422))

    def test_update_pillar_validation_error_name_too_long(
        self, test_client, workspace, user
    ):
        """Test validation error for name exceeding max length returns 422."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Original Name", None, session
            )
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
            json={"name": "A" * 101},
        )

        assert_that(response.status_code, equal_to(422))

    def test_update_pillar_validation_error_description_too_long(
        self, test_client, workspace, user
    ):
        """Test validation error for description exceeding max length returns 500 (database constraint)."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Original Name", None, session
            )
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
            json={"name": "Valid Name", "description": "A" * 1001},
        )

        assert_that(response.status_code, equal_to(500))

    def test_update_pillar_enforces_unique_name(self, test_client, workspace, user):
        """Test updating to duplicate name returns 500."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar1 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 1", None, session
            )
            pillar2 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 2", None, session
            )
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/{pillar2.id}",
            json={"name": "Pillar 1"},
        )

        assert_that(response.status_code, equal_to(500))

    def test_update_pillar_not_found(self, test_client, workspace):
        """Test updating non-existent pillar returns 404."""
        fake_pillar_id = uuid.uuid4()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/{fake_pillar_id}",
            json={"name": "Some name"},
        )

        assert_that(response.status_code, equal_to(404))

    def test_update_pillar_unauthorized(self, test_client_no_user, workspace):
        """Test updating pillar without authentication returns 401."""
        fake_pillar_id = uuid.uuid4()

        response = test_client_no_user.put(
            f"/api/workspaces/{workspace.id}/pillars/{fake_pillar_id}",
            json={"name": "Some name"},
        )

        assert_that(response.status_code, equal_to(401))

    # Delete Pillar View Tests

    def test_delete_pillar_success(self, test_client, workspace, user):
        """Test deleting pillar returns 204."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar to Delete", None, session
            )
        finally:
            session.close()

        response = test_client.delete(
            f"/api/workspaces/{workspace.id}/pillars/{pillar.id}"
        )

        assert_that(response.status_code, equal_to(204))

        # Verify pillar is deleted
        response = test_client.get(f"/api/workspaces/{workspace.id}/pillars")
        data = response.json()
        assert_that(data, equal_to([]))

    def test_delete_pillar_not_found(self, test_client, workspace):
        """Test deleting non-existent pillar returns 404."""
        fake_pillar_id = uuid.uuid4()

        response = test_client.delete(
            f"/api/workspaces/{workspace.id}/pillars/{fake_pillar_id}"
        )

        assert_that(response.status_code, equal_to(404))

    def test_delete_pillar_unauthorized(self, test_client_no_user, workspace):
        """Test deleting pillar without authentication returns 401."""
        fake_pillar_id = uuid.uuid4()

        response = test_client_no_user.delete(
            f"/api/workspaces/{workspace.id}/pillars/{fake_pillar_id}"
        )

        assert_that(response.status_code, equal_to(401))

    # Reorder Pillars View Tests

    def test_reorder_pillars_success(self, test_client, workspace, user):
        """Test reordering pillars returns 200."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar1 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 1", None, session
            )
            pillar2 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 2", None, session
            )
            pillar3 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 3", None, session
            )
            # Store IDs before closing session
            pillar1_id = str(pillar1.id)
            pillar2_id = str(pillar2.id)
            pillar3_id = str(pillar3.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/reorder",
            json={
                "pillars": [
                    {"id": pillar3_id, "display_order": 0},
                    {"id": pillar2_id, "display_order": 1},
                    {"id": pillar1_id, "display_order": 2},
                ]
            },
        )

        assert_that(response.status_code, equal_to(200), response.content)
        data = response.json()
        assert_that(len(data), equal_to(3))
        # Verify order
        assert_that(data[0]["id"], equal_to(pillar3_id))
        assert_that(data[0]["display_order"], equal_to(0))
        assert_that(data[1]["id"], equal_to(pillar2_id))
        assert_that(data[1]["display_order"], equal_to(1))
        assert_that(data[2]["id"], equal_to(pillar1_id))
        assert_that(data[2]["display_order"], equal_to(2))

    def test_reorder_pillars_validation_error_duplicate_display_order(
        self, test_client, workspace, user
    ):
        """Test validation error for duplicate display_order returns 400."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar1 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 1", None, session
            )
            pillar2 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 2", None, session
            )
            # Store IDs before closing session
            pillar1_id = str(pillar1.id)
            pillar2_id = str(pillar2.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/reorder",
            json={
                "pillars": [
                    {"id": pillar1_id, "display_order": 1},
                    {"id": pillar2_id, "display_order": 1},  # Duplicate
                ]
            },
        )
        assert_that(response.status_code, equal_to(400), response.content)

    def test_reorder_pillars_validation_error_display_order_too_high(
        self, test_client, workspace, user
    ):
        """Test validation error for display_order > 4 returns 422."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar1 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 1", None, session
            )
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/reorder",
            json={
                "pillars": [
                    {"id": str(pillar1.id), "display_order": 5},  # Out of range
                ]
            },
        )

        assert_that(response.status_code, equal_to(422))

    def test_reorder_pillars_validation_error_display_order_negative(
        self, test_client, workspace, user
    ):
        """Test validation error for negative display_order returns 422."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar1 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 1", None, session
            )
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/reorder",
            json={
                "pillars": [
                    {"id": str(pillar1.id), "display_order": -1},  # Out of range
                ]
            },
        )

        assert_that(response.status_code, equal_to(422))

    def test_reorder_pillars_pillar_not_found(self, test_client, workspace, user):
        """Test reordering with invalid pillar ID returns 404."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            pillar1 = product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, "Pillar 1", None, session
            )
            # Store ID before closing session
            pillar1_id = str(pillar1.id)
        finally:
            session.close()

        fake_pillar_id = uuid.uuid4()
        response = test_client.put(
            f"/api/workspaces/{workspace.id}/pillars/reorder",
            json={
                "pillars": [
                    {"id": pillar1_id, "display_order": 0},
                    {"id": str(fake_pillar_id), "display_order": 1},  # Does not exist
                ]
            },
        )

        assert_that(response.status_code, equal_to(404), response.content)

    def test_reorder_pillars_unauthorized(self, test_client_no_user, workspace):
        """Test reordering pillars without authentication returns 401."""
        response = test_client_no_user.put(
            f"/api/workspaces/{workspace.id}/pillars/reorder",
            json={
                "pillars": [
                    {"id": str(uuid.uuid4()), "display_order": 0},
                ]
            },
        )

        assert_that(response.status_code, equal_to(401))
