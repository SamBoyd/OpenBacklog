"""Tests for product strategy views."""

import uuid

from hamcrest import assert_that, equal_to, has_key, has_length


class TestProductOutcomeViews:
    def test_create_outcome_minimal(self, test_client, workspace):
        """Test creating outcome with minimal data returns 201."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/outcomes",
            json={"name": "80% weekly AI usage"},
        )

        assert_that(response.status_code, equal_to(201))
        data = response.json()
        assert_that(data["name"], equal_to("80% weekly AI usage"))
        assert_that(data["workspace_id"], equal_to(str(workspace.id)))
        assert_that(data["description"], equal_to(None))
        assert_that(data["display_order"], equal_to(0))
        assert_that(data, has_key("id"))
        assert_that(data, has_key("created_at"))
        assert_that(data, has_key("updated_at"))

    def test_create_outcome_full_details(self, test_client, workspace):
        """Test creating outcome with all fields returns 201."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/outcomes",
            json={
                "name": "80% weekly AI usage",
                "description": "Measure AI adoption as a leading indicator",
                "pillar_ids": [],
            },
        )

        assert_that(response.status_code, equal_to(201))
        data = response.json()
        assert_that(data["name"], equal_to("80% weekly AI usage"))
        assert_that(
            data["description"], equal_to("Measure AI adoption as a leading indicator")
        )

    def test_create_outcome_with_pillar_links(self, test_client, workspace, user):
        """Test creating outcome linked to pillars returns 201."""
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
            pillar1_id = str(pillar1.id)
            pillar2_id = str(pillar2.id)
        finally:
            session.close()

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/outcomes",
            json={
                "name": "Test Outcome",
                "pillar_ids": [pillar1_id, pillar2_id],
            },
        )

        assert_that(response.status_code, equal_to(201))
        data = response.json()
        assert_that(data["name"], equal_to("Test Outcome"))
        # Verify the links are returned
        assert_that(set(data["pillar_ids"]), equal_to(set([pillar1_id, pillar2_id])))

    def test_create_outcome_validation_error_empty_name(self, test_client, workspace):
        """Test validation error for empty name returns 422."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/outcomes",
            json={"name": ""},
        )

        assert_that(response.status_code, equal_to(422))

    def test_create_outcome_validation_error_name_too_long(
        self, test_client, workspace
    ):
        """Test validation error for name exceeding max length returns 422."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/outcomes",
            json={"name": "A" * 151},
        )

        assert_that(response.status_code, equal_to(422))

    def test_create_outcome_validation_error_description_too_long(
        self, test_client, workspace
    ):
        """Test validation error for description exceeding max length returns 422."""
        response = test_client.post(
            f"/api/workspaces/{workspace.id}/outcomes",
            json={
                "name": "Valid name",
                "description": "D" * 1501,
            },
        )

        assert_that(response.status_code, equal_to(422))

    def test_create_outcome_max_limit_exceeded(self, test_client, workspace, user):
        """Test creating outcome when limit reached returns 400."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            for i in range(10):
                product_strategy_controller.create_product_outcome(
                    workspace.id,
                    user.id,
                    f"Outcome {i}",
                    None,
                    [],
                    session,
                )
        finally:
            session.close()

        response = test_client.post(
            f"/api/workspaces/{workspace.id}/outcomes",
            json={"name": "Outcome 11"},
        )

        assert_that(response.status_code, equal_to(400))
        data = response.json()
        assert_that(
            data["detail"],
            equal_to("Workspace has reached maximum of 10 product outcomes"),
        )

    def test_create_outcome_unauthorized(self, test_client_no_user, workspace):
        """Test creating outcome without authentication returns 401."""
        response = test_client_no_user.post(
            f"/api/workspaces/{workspace.id}/outcomes",
            json={"name": "Test Outcome"},
        )

        assert_that(response.status_code, equal_to(401))

    # Update Outcome View Tests

    def test_update_outcome_success_all_fields(self, test_client, workspace, user):
        """Test updating outcome with all fields returns 200."""
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
            outcome = product_strategy_controller.create_product_outcome(
                workspace.id,
                user.id,
                "Original Name",
                "Original desc",
                [],
                session,
            )
            outcome_id = str(outcome.id)
            pillar1_id = str(pillar1.id)
            pillar2_id = str(pillar2.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/{outcome_id}",
            json={
                "name": "Updated Name",
                "description": "Updated description",
                "pillar_ids": [pillar1_id, pillar2_id],
            },
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["id"], equal_to(outcome_id))
        assert_that(data["name"], equal_to("Updated Name"))
        assert_that(data["description"], equal_to("Updated description"))
        # Verify pillar links echoed back
        assert_that(set(data["pillar_ids"]), equal_to(set([pillar1_id, pillar2_id])))

    def test_update_outcome_success_name_only(self, test_client, workspace, user):
        """Test updating outcome name only returns 200."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Original Name", None, [], session
            )
            outcome_id = str(outcome.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/{outcome_id}",
            json={"name": "Updated Name"},
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["name"], equal_to("Updated Name"))

    def test_update_outcome_validation_error_empty_name(
        self, test_client, workspace, user
    ):
        """Test validation error for empty name returns 422."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Original Name", None, [], session
            )
            outcome_id = str(outcome.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/{outcome_id}",
            json={"name": ""},
        )

        assert_that(response.status_code, equal_to(422))

    def test_update_outcome_validation_error_name_too_long(
        self, test_client, workspace, user
    ):
        """Test validation error for name exceeding max length returns 422."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Original Name", None, [], session
            )
            outcome_id = str(outcome.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/{outcome_id}",
            json={"name": "A" * 151},
        )

        assert_that(response.status_code, equal_to(422))

    def test_update_outcome_validation_error_description_too_long(
        self, test_client, workspace, user
    ):
        """Test validation error for description exceeding max length returns 422."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Original Name", None, [], session
            )
            outcome_id = str(outcome.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/{outcome_id}",
            json={"name": "Valid Name", "description": "D" * 1501},
        )

        assert_that(response.status_code, equal_to(422))

    def test_update_outcome_pillar_links(self, test_client, workspace, user):
        """Test updating outcome pillar links returns 200."""
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
            outcome = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Test Outcome", None, [], session
            )
            outcome_id = str(outcome.id)
            pillar1_id = str(pillar1.id)
            pillar2_id = str(pillar2.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/{outcome_id}",
            json={
                "name": "Test Outcome",
                "pillar_ids": [pillar1_id, pillar2_id],
            },
        )

        assert_that(response.status_code, equal_to(200))
        data = response.json()
        assert_that(data["id"], equal_to(outcome_id))
        assert_that(set(data["pillar_ids"]), equal_to(set([pillar1_id, pillar2_id])))

    def test_update_outcome_not_found(self, test_client, workspace):
        """Test updating non-existent outcome returns 404."""
        fake_outcome_id = uuid.uuid4()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/{fake_outcome_id}",
            json={"name": "Some name"},
        )

        assert_that(response.status_code, equal_to(404))

    def test_update_outcome_unauthorized(self, test_client_no_user, workspace):
        """Test updating outcome without authentication returns 401."""
        fake_outcome_id = uuid.uuid4()

        response = test_client_no_user.put(
            f"/api/workspaces/{workspace.id}/outcomes/{fake_outcome_id}",
            json={"name": "Some name"},
        )

        assert_that(response.status_code, equal_to(401))

    # Delete Outcome View Tests

    def test_delete_outcome_success(self, test_client, workspace, user, session):
        """Test deleting outcome returns 204."""
        from src.strategic_planning import controller as product_strategy_controller

        outcome = product_strategy_controller.create_product_outcome(
            workspace.id,
            user.id,
            "Outcome to Delete",
            None,
            [],
            session,
        )
        outcome_id = str(outcome.id)

        response = test_client.delete(
            f"/api/workspaces/{workspace.id}/outcomes/{outcome_id}"
        )

        assert_that(response.status_code, equal_to(204))

        # Verify outcome is deleted using controller
        outcomes = product_strategy_controller.get_product_outcomes(
            workspace.id, session
        )
        assert_that(outcomes, has_length(0))

    def test_delete_outcome_not_found(self, test_client, workspace):
        """Test deleting non-existent outcome returns 404."""
        fake_outcome_id = uuid.uuid4()

        response = test_client.delete(
            f"/api/workspaces/{workspace.id}/outcomes/{fake_outcome_id}"
        )

        assert_that(response.status_code, equal_to(404))

    def test_delete_outcome_unauthorized(self, test_client_no_user, workspace):
        """Test deleting outcome without authentication returns 401."""
        fake_outcome_id = uuid.uuid4()

        response = test_client_no_user.delete(
            f"/api/workspaces/{workspace.id}/outcomes/{fake_outcome_id}"
        )

        assert_that(response.status_code, equal_to(401))

    # Reorder Outcomes View Tests

    def test_reorder_outcomes_success(self, test_client, workspace, user):
        """Test reordering outcomes returns 200."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome1 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 1", None, [], session
            )
            outcome2 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 2", None, [], session
            )
            outcome3 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 3", None, [], session
            )
            # Store IDs before closing session
            outcome1_id = str(outcome1.id)
            outcome2_id = str(outcome2.id)
            outcome3_id = str(outcome3.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/reorder",
            json={
                "outcomes": [
                    {"id": outcome3_id, "display_order": 0},
                    {"id": outcome2_id, "display_order": 1},
                    {"id": outcome1_id, "display_order": 2},
                ]
            },
        )

        assert_that(response.status_code, equal_to(200), response.content)
        data = response.json()
        assert_that(len(data), equal_to(3))
        # Verify order
        assert_that(data[0]["id"], equal_to(outcome3_id))
        assert_that(data[0]["display_order"], equal_to(0))
        assert_that(data[1]["id"], equal_to(outcome2_id))
        assert_that(data[1]["display_order"], equal_to(1))
        assert_that(data[2]["id"], equal_to(outcome1_id))
        assert_that(data[2]["display_order"], equal_to(2))

    def test_reorder_outcomes_validation_error_duplicate_display_order(
        self, test_client, workspace, user
    ):
        """Test validation error for duplicate display_order returns 400."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome1 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 1", None, [], session
            )
            outcome2 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 2", None, [], session
            )
            # Store IDs before closing session
            outcome1_id = str(outcome1.id)
            outcome2_id = str(outcome2.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/reorder",
            json={
                "outcomes": [
                    {"id": outcome1_id, "display_order": 1},
                    {"id": outcome2_id, "display_order": 1},  # Duplicate
                ]
            },
        )
        assert_that(response.status_code, equal_to(400), response.content)

    def test_reorder_outcomes_validation_error_missing_outcome(
        self, test_client, workspace, user
    ):
        """Test validation error when not all outcomes are included returns 400."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome1 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 1", None, [], session
            )
            outcome2 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 2", None, [], session
            )
            # Store IDs before closing session
            outcome1_id = str(outcome1.id)
            # Don't include outcome2 in the request
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/reorder",
            json={
                "outcomes": [
                    {"id": outcome1_id, "display_order": 0},
                    # Missing outcome2
                ]
            },
        )

        assert_that(response.status_code, equal_to(400), response.content)

    def test_reorder_outcomes_validation_error_incomplete_sequence(
        self, test_client, workspace, user
    ):
        """Test validation error for incomplete sequence returns 400."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome1 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 1", None, [], session
            )
            outcome2 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 2", None, [], session
            )
            # Store IDs before closing session
            outcome1_id = str(outcome1.id)
            outcome2_id = str(outcome2.id)
        finally:
            session.close()

        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/reorder",
            json={
                "outcomes": [
                    {"id": outcome1_id, "display_order": 0},
                    {"id": outcome2_id, "display_order": 5},  # Gap in sequence
                ]
            },
        )

        assert_that(response.status_code, equal_to(400), response.content)

    def test_reorder_outcomes_outcome_not_found(self, test_client, workspace, user):
        """Test reordering with invalid outcome ID returns 404."""
        from src.db import SessionLocal
        from src.strategic_planning import controller as product_strategy_controller

        session = SessionLocal()
        try:
            outcome1 = product_strategy_controller.create_product_outcome(
                workspace.id, user.id, "Outcome 1", None, [], session
            )
            # Store ID before closing session
            outcome1_id = str(outcome1.id)
        finally:
            session.close()

        fake_outcome_id = uuid.uuid4()
        response = test_client.put(
            f"/api/workspaces/{workspace.id}/outcomes/reorder",
            json={
                "outcomes": [
                    {"id": outcome1_id, "display_order": 0},
                    {"id": str(fake_outcome_id), "display_order": 1},  # Does not exist
                ]
            },
        )

        assert_that(response.status_code, equal_to(404), response.content)

    def test_reorder_outcomes_unauthorized(self, test_client_no_user, workspace):
        """Test reordering outcomes without authentication returns 401."""
        response = test_client_no_user.put(
            f"/api/workspaces/{workspace.id}/outcomes/reorder",
            json={
                "outcomes": [
                    {"id": str(uuid.uuid4()), "display_order": 0},
                ]
            },
        )

        assert_that(response.status_code, equal_to(401))
