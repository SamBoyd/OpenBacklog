"""Tests for product strategy views."""

import uuid

from hamcrest import assert_that, equal_to, has_key


def test_get_vision_unauthorized(test_client_no_user, workspace):
    """Test getting vision without authentication returns 401."""
    response = test_client_no_user.get(f"/api/workspaces/{workspace.id}/vision")
    assert_that(response.status_code, equal_to(401))


def test_get_vision_not_found(test_client, workspace):
    """Test getting vision when none exists returns 404."""
    response = test_client.get(f"/api/workspaces/{workspace.id}/vision")
    assert_that(response.status_code, equal_to(404))


def test_get_vision_success(test_client, workspace, product_vision):
    """Test getting existing vision returns 200."""
    response = test_client.get(f"/api/workspaces/{workspace.id}/vision")

    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["vision_text"], equal_to(product_vision.vision_text))
    assert_that(data, has_key("id"))
    assert_that(data, has_key("workspace_id"))
    assert_that(data, has_key("created_at"))
    assert_that(data, has_key("updated_at"))


def test_upsert_vision_create(test_client, workspace):
    """Test creating new vision returns 200."""
    response = test_client.put(
        f"/api/workspaces/{workspace.id}/vision",
        json={"vision_text": "Build the best product"},
    )

    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["vision_text"], equal_to("Build the best product"))
    assert_that(data["workspace_id"], equal_to(str(workspace.id)))


def test_upsert_vision_update(test_client, workspace, product_vision):
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


def test_upsert_vision_validation_error_empty(test_client, workspace):
    """Test validation error for empty vision returns 422."""
    response = test_client.put(
        f"/api/workspaces/{workspace.id}/vision",
        json={"vision_text": ""},
    )

    assert_that(response.status_code, equal_to(422))


def test_upsert_vision_validation_error_too_long(test_client, workspace):
    """Test validation error for text exceeding max length returns 422."""
    response = test_client.put(
        f"/api/workspaces/{workspace.id}/vision",
        json={"vision_text": "A" * 1001},
    )

    assert_that(response.status_code, equal_to(422))


def test_upsert_vision_workspace_not_found(test_client):
    """Test upserting vision for non-existent workspace returns 500."""
    fake_workspace_id = uuid.uuid4()
    response = test_client.put(
        f"/api/workspaces/{fake_workspace_id}/vision",
        json={"vision_text": "Some vision text"},
    )

    assert_that(response.status_code, equal_to(500))


def test_upsert_vision_unauthorized(test_client_no_user, workspace):
    """Test upserting vision without authentication returns 401."""
    response = test_client_no_user.put(
        f"/api/workspaces/{workspace.id}/vision",
        json={"vision_text": "Some vision text"},
    )

    assert_that(response.status_code, equal_to(401))


# Strategic Pillar View Tests


def test_get_pillars_empty(test_client, workspace):
    """Test getting pillars when none exist returns empty list."""
    response = test_client.get(f"/api/workspaces/{workspace.id}/pillars")

    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data, equal_to([]))


def test_get_pillars_returns_list(test_client, workspace, user):
    """Test getting pillars returns list of pillars."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar1 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 1", None, None, session
        )
        pillar2 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 2", "Description 2", None, session
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


def test_get_pillars_unauthorized(test_client_no_user, workspace):
    """Test getting pillars without authentication returns 401."""
    response = test_client_no_user.get(f"/api/workspaces/{workspace.id}/pillars")
    assert_that(response.status_code, equal_to(401))


def test_create_pillar_success_all_fields(test_client, workspace):
    """Test creating pillar with all fields returns 201."""
    response = test_client.post(
        f"/api/workspaces/{workspace.id}/pillars",
        json={
            "name": "Developer Experience",
            "description": "Make developers love our product",
            "anti_strategy": "Not enterprise features",
        },
    )

    assert_that(response.status_code, equal_to(201))
    data = response.json()
    assert_that(data["name"], equal_to("Developer Experience"))
    assert_that(data["description"], equal_to("Make developers love our product"))
    assert_that(data["anti_strategy"], equal_to("Not enterprise features"))
    assert_that(data["workspace_id"], equal_to(str(workspace.id)))
    assert_that(data["display_order"], equal_to(0))


def test_create_pillar_success_name_only(test_client, workspace):
    """Test creating pillar with only name returns 201."""
    response = test_client.post(
        f"/api/workspaces/{workspace.id}/pillars",
        json={"name": "Developer Experience"},
    )

    assert_that(response.status_code, equal_to(201))
    data = response.json()
    assert_that(data["name"], equal_to("Developer Experience"))
    assert_that(data["description"], equal_to(None))
    assert_that(data["anti_strategy"], equal_to(None))


def test_create_pillar_validation_error_empty_name(test_client, workspace):
    """Test validation error for empty name returns 422."""
    response = test_client.post(
        f"/api/workspaces/{workspace.id}/pillars",
        json={"name": ""},
    )

    assert_that(response.status_code, equal_to(422))


def test_create_pillar_validation_error_name_too_long(test_client, workspace):
    """Test validation error for name exceeding max length returns 422."""
    response = test_client.post(
        f"/api/workspaces/{workspace.id}/pillars",
        json={"name": "A" * 101},
    )

    assert_that(response.status_code, equal_to(422))


def test_create_pillar_validation_error_description_too_long(test_client, workspace):
    """Test validation error for description exceeding max length returns 422."""
    response = test_client.post(
        f"/api/workspaces/{workspace.id}/pillars",
        json={"name": "Valid Name", "description": "A" * 1001},
    )

    assert_that(response.status_code, equal_to(422))


def test_create_pillar_validation_error_anti_strategy_too_long(test_client, workspace):
    """Test validation error for anti_strategy exceeding max length returns 422."""
    response = test_client.post(
        f"/api/workspaces/{workspace.id}/pillars",
        json={"name": "Valid Name", "anti_strategy": "A" * 1001},
    )

    assert_that(response.status_code, equal_to(422))


def test_create_pillar_enforces_5_pillar_limit(test_client, workspace, user):
    """Test creating 6th pillar returns 400 error."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        # Create 5 pillars
        for i in range(5):
            product_strategy_controller.create_strategic_pillar(
                workspace.id, user.id, f"Pillar {i}", None, None, session
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


def test_create_pillar_enforces_unique_name(test_client, workspace):
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


def test_create_pillar_workspace_not_found(test_client):
    """Test creating pillar for non-existent workspace returns 500."""
    fake_workspace_id = uuid.uuid4()
    response = test_client.post(
        f"/api/workspaces/{fake_workspace_id}/pillars",
        json={"name": "Some pillar"},
    )

    assert_that(response.status_code, equal_to(500))


def test_create_pillar_unauthorized(test_client_no_user, workspace):
    """Test creating pillar without authentication returns 401."""
    response = test_client_no_user.post(
        f"/api/workspaces/{workspace.id}/pillars",
        json={"name": "Some pillar"},
    )

    assert_that(response.status_code, equal_to(401))


# Update Pillar View Tests


def test_update_pillar_success_all_fields(test_client, workspace, user):
    """Test updating pillar with all fields returns 200."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar = product_strategy_controller.create_strategic_pillar(
            workspace.id,
            user.id,
            "Original Name",
            "Original desc",
            "Original anti",
            session,
        )
    finally:
        session.close()

    response = test_client.put(
        f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
        json={
            "name": "Updated Name",
            "description": "Updated description",
            "anti_strategy": "Updated anti-strategy",
        },
    )

    assert_that(response.status_code, equal_to(200))
    data = response.json()
    assert_that(data["id"], equal_to(str(pillar.id)))
    assert_that(data["name"], equal_to("Updated Name"))
    assert_that(data["description"], equal_to("Updated description"))
    assert_that(data["anti_strategy"], equal_to("Updated anti-strategy"))


def test_update_pillar_success_name_only(test_client, workspace, user):
    """Test updating pillar name only returns 200."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Original Name", None, None, session
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


def test_update_pillar_validation_error_empty_name(test_client, workspace, user):
    """Test validation error for empty name returns 422."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Original Name", None, None, session
        )
    finally:
        session.close()

    response = test_client.put(
        f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
        json={"name": ""},
    )

    assert_that(response.status_code, equal_to(422))


def test_update_pillar_validation_error_name_too_long(test_client, workspace, user):
    """Test validation error for name exceeding max length returns 422."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Original Name", None, None, session
        )
    finally:
        session.close()

    response = test_client.put(
        f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
        json={"name": "A" * 101},
    )

    assert_that(response.status_code, equal_to(422))


def test_update_pillar_validation_error_description_too_long(
    test_client, workspace, user
):
    """Test validation error for description exceeding max length returns 422."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Original Name", None, None, session
        )
    finally:
        session.close()

    response = test_client.put(
        f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
        json={"name": "Valid Name", "description": "A" * 1001},
    )

    assert_that(response.status_code, equal_to(422))


def test_update_pillar_validation_error_anti_strategy_too_long(
    test_client, workspace, user
):
    """Test validation error for anti_strategy exceeding max length returns 422."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Original Name", None, None, session
        )
    finally:
        session.close()

    response = test_client.put(
        f"/api/workspaces/{workspace.id}/pillars/{pillar.id}",
        json={"name": "Valid Name", "anti_strategy": "A" * 1001},
    )

    assert_that(response.status_code, equal_to(422))


def test_update_pillar_enforces_unique_name(test_client, workspace, user):
    """Test updating to duplicate name returns 500."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar1 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 1", None, None, session
        )
        pillar2 = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar 2", None, None, session
        )
    finally:
        session.close()

    response = test_client.put(
        f"/api/workspaces/{workspace.id}/pillars/{pillar2.id}",
        json={"name": "Pillar 1"},
    )

    assert_that(response.status_code, equal_to(500))


def test_update_pillar_not_found(test_client, workspace):
    """Test updating non-existent pillar returns 404."""
    fake_pillar_id = uuid.uuid4()

    response = test_client.put(
        f"/api/workspaces/{workspace.id}/pillars/{fake_pillar_id}",
        json={"name": "Some name"},
    )

    assert_that(response.status_code, equal_to(404))


def test_update_pillar_unauthorized(test_client_no_user, workspace):
    """Test updating pillar without authentication returns 401."""
    fake_pillar_id = uuid.uuid4()

    response = test_client_no_user.put(
        f"/api/workspaces/{workspace.id}/pillars/{fake_pillar_id}",
        json={"name": "Some name"},
    )

    assert_that(response.status_code, equal_to(401))


# Delete Pillar View Tests


def test_delete_pillar_success(test_client, workspace, user):
    """Test deleting pillar returns 204."""
    from src.controllers import product_strategy_controller
    from src.db import SessionLocal

    session = SessionLocal()
    try:
        pillar = product_strategy_controller.create_strategic_pillar(
            workspace.id, user.id, "Pillar to Delete", None, None, session
        )
    finally:
        session.close()

    response = test_client.delete(f"/api/workspaces/{workspace.id}/pillars/{pillar.id}")

    assert_that(response.status_code, equal_to(204))

    # Verify pillar is deleted
    response = test_client.get(f"/api/workspaces/{workspace.id}/pillars")
    data = response.json()
    assert_that(data, equal_to([]))


def test_delete_pillar_not_found(test_client, workspace):
    """Test deleting non-existent pillar returns 404."""
    fake_pillar_id = uuid.uuid4()

    response = test_client.delete(
        f"/api/workspaces/{workspace.id}/pillars/{fake_pillar_id}"
    )

    assert_that(response.status_code, equal_to(404))


def test_delete_pillar_unauthorized(test_client_no_user, workspace):
    """Test deleting pillar without authentication returns 401."""
    fake_pillar_id = uuid.uuid4()

    response = test_client_no_user.delete(
        f"/api/workspaces/{workspace.id}/pillars/{fake_pillar_id}"
    )

    assert_that(response.status_code, equal_to(401))
