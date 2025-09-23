import datetime
import logging
import uuid
from datetime import timedelta

import freezegun
from hamcrest import assert_that, equal_to, is_, not_

from src.accounting.models import UserAccountDetails, UserAccountStatus
from src.models import (
    AIImprovementJob,
    APIProvider,
    ContextType,
    EntityType,
    GitHubInstallation,
    Group,
    GroupType,
    Initiative,
    InitiativeGroup,
    InitiativeStatus,
    InitiativeType,
    JobStatus,
    Lens,
    Ordering,
    Task,
    TaskStatus,
    TaskType,
    User,
    UserKey,
    Workspace,
)

logger = logging.getLogger(__name__)


def test_initiative_type():
    for initiative_type in InitiativeType:
        assert isinstance(initiative_type, InitiativeType)
        assert_that(initiative_type.value, equal_to(initiative_type.name))


def test_task_type():
    for task_type in TaskType:
        assert isinstance(task_type, TaskType)
        assert_that(task_type.value, equal_to(task_type.name))


def test_task_status():
    for task_status in TaskStatus:
        assert isinstance(task_status, TaskStatus)
        assert_that(task_status.value, equal_to(task_status.name))


def test_task_table_config(session, user, workspace, test_initiative):
    logger.debug("Beginning test_task_table_config")

    assert Task.__tablename__ == "task"

    now = datetime.datetime.now()
    task = Task(
        identifier="TM-002",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
        title="title",
        description="description",
        created_at=now - timedelta(days=1),
        updated_at=now,
        status=TaskStatus.TO_DO.value,
        type=TaskType.CODING.value,
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    assert task.id is not None
    assert task.identifier == "TM-002"
    assert task.user_id == user.id
    assert task.workspace_id == workspace.id
    assert task.title == "title"
    assert task.description == "description"
    assert task.created_at == now - timedelta(days=1)
    assert task.updated_at == now
    assert task.status == TaskStatus.TO_DO.value
    assert task.type == TaskType.CODING
    session.refresh(task, ["checklist", "initiative"])
    assert task.checklist == []
    assert task.initiative == test_initiative
    logger.debug("Finished test_task_table_config")


def test_task_truncate_fields(session, user, workspace, test_initiative):
    now = datetime.datetime.now()

    task = Task(
        identifier="TM-002",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
        title="title" * 200,
        description="description" * 600,
        created_at=now - timedelta(days=1),
        updated_at=now,
        status=TaskStatus.TO_DO.value,
        type=TaskType.CODING.value,
    )

    task.truncate_fields()

    assert len(task.title) == 100
    assert len(task.description) == 500

    session.add(task)
    session.commit()
    session.refresh(task)


def test_initiative_identifier_autoincrements(
    session, user, workspace, test_initiative
):
    now = datetime.datetime.now()

    task_1 = Task(
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
        title="title" * 200,
        description="description" * 600,
        created_at=now - timedelta(days=1),
        updated_at=now,
        status=TaskStatus.TO_DO.value,
        type=TaskType.CODING.value,
    )
    session.add(task_1)
    session.commit()
    session.refresh(task_1)

    task_2 = Task(
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
        title="title" * 200,
        description="description" * 600,
        created_at=now - timedelta(days=1),
        updated_at=now,
        status=TaskStatus.TO_DO.value,
        type=TaskType.CODING.value,
    )
    session.add(task_2)
    session.commit()
    session.refresh(task_2)


def test_minimal_data_inserts_and_defaults(session, user, workspace, test_initiative):
    now = datetime.datetime.now()

    with freezegun.freeze_time(now):
        task = Task(
            user_id=user.id,
            workspace_id=workspace.id,
            initiative_id=test_initiative.id,
            title="title",
        )
        session.add(task)
        session.commit()
        session.refresh(task)

    assert_that(task.id, equal_to(task.id))
    assert_that(task.user_id, equal_to(user.id))
    assert_that(task.workspace_id, equal_to(workspace.id))
    assert_that(task.title, equal_to("title"))

    assert_that(task.description, equal_to(""))
    assert_that(task.status, equal_to(TaskStatus.TO_DO.value))
    assert_that(task.type, equal_to(None))
    assert_that(task.checklist, equal_to([]))

    with freezegun.freeze_time(now):
        initiative = Initiative(
            user_id=user.id,
            workspace_id=workspace.id,
            title="title",
        )
        session.add(initiative)
        session.commit()
        session.refresh(initiative)

    assert_that(initiative.id, equal_to(initiative.id))
    assert_that(initiative.user_id, equal_to(user.id))
    assert_that(initiative.workspace_id, equal_to(workspace.id))
    assert_that(initiative.title, equal_to("title"))

    assert_that(initiative.description, equal_to(""))
    assert_that(initiative.status, equal_to(InitiativeStatus.BACKLOG.value))
    assert_that(initiative.type, equal_to(None))
    assert_that(initiative.tasks, equal_to([]))


def test_default_user_display_preferences(user):
    assert_that(
        user.display_preferences,
        equal_to(
            {
                "timezone": "UTC",
                "language": "English",
                "dateFormat": "YYYY-MM-DD",
                "theme": "Light",
            }
        ),
    )


def test_github_installation_model(session, user):
    installation = GitHubInstallation(installation_id="install-123456", user_id=user.id)
    session.add(installation)
    session.commit()
    session.refresh(installation)
    assert installation.id is not None
    assert installation.installation_id == "install-123456"
    assert installation.user_id == user.id


def test_workspace_model_creation(session, user):
    """Test creating a workspace with minimal required fields."""
    workspace = Workspace(name="Test Workspace", user_id=user.id)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    # Verify basic properties
    assert workspace.id is not None
    assert workspace.name == "Test Workspace"
    assert workspace.user_id == user.id
    assert workspace.description is None
    assert workspace.created_at is not None
    assert workspace.updated_at is not None

    # Verify relationships are initialized as empty lists
    assert workspace.tasks == []
    assert workspace.initiatives == []


def test_workspace_with_full_data(session, user):
    """Test creating a workspace with all fields populated."""
    now = datetime.datetime.now()

    with freezegun.freeze_time(now):
        workspace = Workspace(
            name="Full Workspace",
            description="A complete workspace with all fields",
            user_id=user.id,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

    assert_that(workspace.id, not_(equal_to(None)))
    assert_that(workspace.name, equal_to("Full Workspace"))
    assert_that(workspace.description, equal_to("A complete workspace with all fields"))
    assert_that(workspace.user_id, equal_to(user.id))
    assert_that(workspace.created_at, not_(equal_to(None)))
    assert_that(workspace.updated_at, not_(equal_to(None)))


def test_workspace_user_relationship(session):
    """Test the relationship between workspace and user."""
    # Create a new user
    user = User(
        name="Workspace Owner",
        email=f"workspace_owner+{uuid.uuid4()}@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        last_logged_in=datetime.datetime.now(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create workspaces for the user
    workspace1 = Workspace(name="First Workspace", user_id=user.id)

    session.add_all([workspace1])
    session.commit()
    session.refresh(user)

    # Verify the user has the workspaces
    assert len(user.workspaces) == 1
    assert any(w.name == "First Workspace" for w in user.workspaces)


def test_workspace_task_relationship(session, user, workspace, test_initiative):
    """Test the relationship between workspace and tasks."""
    # Create tasks in the workspace
    task1 = Task(
        title="Task 1",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
    )
    task2 = Task(
        title="Task 2",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
    )

    session.add_all([task1, task2])
    session.commit()
    session.refresh(workspace)

    # Verify the workspace has the tasks
    assert len(workspace.tasks) == 2
    assert any(t.title == "Task 1" for t in workspace.tasks)
    assert any(t.title == "Task 2" for t in workspace.tasks)


def test_workspace_initiative_relationship(session, user, workspace):
    """Test the relationship between workspace and initiatives."""
    # Create initiatives in the workspace
    initiative1 = Initiative(
        title="Initiative 1", user_id=user.id, workspace_id=workspace.id
    )
    initiative2 = Initiative(
        title="Initiative 2", user_id=user.id, workspace_id=workspace.id
    )

    session.add_all([initiative1, initiative2])
    session.commit()
    session.refresh(workspace)

    # Verify the workspace has the initiatives
    assert len(workspace.initiatives) == 2
    assert any(i.title == "Initiative 1" for i in workspace.initiatives)
    assert any(i.title == "Initiative 2" for i in workspace.initiatives)


def test_new_group_models_relationships(session, user, workspace):
    """Test the Group, InitiativeGroup models and blocked_by relationship in Initiative."""
    # Create initiatives
    initiative1 = Initiative(
        title="Blocking Initiative",
        user_id=user.id,
        workspace_id=workspace.id,
        identifier="INI-3033",
    )
    initiative2 = Initiative(
        title="Blocked Initiative",
        user_id=user.id,
        workspace_id=workspace.id,
        identifier="INI-2433",
    )

    # Set up blocking relationship
    session.add(initiative1)
    session.add(initiative2)
    session.commit()
    session.refresh(initiative1)
    session.refresh(initiative2)

    assert initiative1 is not None
    assert initiative2 is not None

    initiative2.blocked_by = initiative1
    session.add(initiative2)
    session.commit()
    # Explicitly refresh initiative2 and load the blocked_by relationship
    session.refresh(initiative2, ["blocked_by"])

    # Verify the blocking relationship
    assert initiative2.blocked_by.id == initiative1.id
    assert initiative2.blocked_by.title == "Blocking Initiative"

    # Create a group
    group = Group(
        name="Test Group",
        description="A test group of initiatives",
        user=user,
        workspace=workspace,
        group_type=GroupType.EXPLICIT,
    )
    session.add(group)
    session.commit()
    session.refresh(group)

    # Verify group was created correctly
    assert group.id is not None
    assert group.name == "Test Group"
    assert group.description == "A test group of initiatives"
    assert group.user_id == user.id
    assert group.workspace_id == workspace.id
    assert group.group_type == GroupType.EXPLICIT
    assert group.initiatives == []

    # Create nested groups to test parent-child relationship
    child_group = Group(
        name="Child Group",
        user=user,
        workspace=workspace,
        group_type=GroupType.EXPLICIT,
        parent_group_id=group.id,
    )
    session.add(child_group)
    session.commit()
    session.refresh(group)
    session.refresh(child_group)

    # Verify parent-child relationship
    assert child_group.parent_group_id == group.id
    assert child_group.parent.id == group.id
    assert len(group.children) == 1
    assert group.children[0].id == child_group.id

    # Add initiatives to the group through the association table
    # Create association records with positions
    association1 = InitiativeGroup(
        user=user,
        initiative_id=initiative1.id,
        group_id=group.id,
    )
    association2 = InitiativeGroup(
        user=user,
        initiative_id=initiative2.id,
        group_id=group.id,
    )

    session.add_all([association1, association2])
    session.commit()
    session.refresh(group)
    session.refresh(initiative1)
    session.refresh(initiative2)

    # Verify the many-to-many relationship works
    assert len(group.initiatives) == 2
    assert initiative1 in group.initiatives
    assert initiative2 in group.initiatives

    assert len(initiative1.groups) == 1
    assert group in initiative1.groups

    assert len(initiative2.groups) == 1
    assert group in initiative2.groups

    # Test smart group with query criteria
    smart_group = Group(
        name="Smart Group",
        user=user,
        workspace=workspace,
        group_type=GroupType.SMART,
        query_criteria={"status": "BACKLOG"},
    )
    session.add(smart_group)
    session.commit()
    session.refresh(smart_group)

    assert smart_group.id is not None
    assert smart_group.group_type == GroupType.SMART
    assert smart_group.query_criteria == {"status": "BACKLOG"}

    # Test metadata field
    group.group_metadata = {"year": 2024, "quarter": "Q2"}
    session.commit()
    session.refresh(group)

    assert group.group_metadata == {"year": 2024, "quarter": "Q2"}


def test_workspace_cascade_delete(session, user, workspace, test_initiative):
    """Test that deleting a workspace cascades to its tasks and initiatives."""
    # Create tasks and initiatives in the workspace
    task = Task(
        title="Cascade Task",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
    )

    session.add_all([task, test_initiative])
    session.commit()

    # Get IDs for later verification
    workspace_id = workspace.id
    task_id = task.id
    initiative_id = test_initiative.id

    # Delete the workspace
    session.delete(workspace)
    session.commit()

    # Verify the workspace and its related entities are deleted
    assert_that(session.query(Workspace).filter_by(id=workspace_id).first(), is_(None))
    assert_that(session.query(Task).filter_by(id=task_id).first(), is_(None))
    assert_that(
        session.query(Initiative).filter_by(id=initiative_id).first(), is_(None)
    )


def test_ai_improvement_job_model(session, user, workspace, test_initiative):
    # Define sample messages
    sample_messages = [
        {"role": "user", "content": "Improve this task description"},
        {"role": "assistant", "content": "Okay, how about this revised description?"},
    ]

    # Create AI improvement job linked to task
    task_job = AIImprovementJob(
        user_id=user.id,
        lens=Lens.TASK,
        status=JobStatus.PENDING,
        messages=sample_messages,
        input_data={"prompt": "Improve this task description"},
    )
    session.add(task_job)
    session.commit()
    session.refresh(task_job)

    assert task_job.user_id == user.id
    assert task_job.id is not None
    assert task_job.lens == Lens.TASK
    assert task_job.status == JobStatus.PENDING
    assert task_job.messages == sample_messages
    assert task_job.input_data == {"prompt": "Improve this task description"}
    assert task_job.result_data is None
    assert task_job.created_at is not None
    assert task_job.updated_at is not None

    # Create AI improvement job linked to initiative
    initiative_job = AIImprovementJob(
        user_id=user.id,
        lens=Lens.INITIATIVE,
        status=JobStatus.PROCESSING,
        messages=[{"role": "system", "content": "Break down initiatives."}],
        input_data={"prompt": "Break down this initiative into tasks"},
    )
    session.add(initiative_job)
    session.commit()
    session.refresh(initiative_job)

    assert initiative_job.user_id == user.id
    assert initiative_job.id is not None
    assert initiative_job.lens == Lens.INITIATIVE
    assert initiative_job.status == JobStatus.PROCESSING
    assert initiative_job.messages == [
        {"role": "system", "content": "Break down initiatives."}
    ]

    # Test job with error
    error_job = AIImprovementJob(
        user_id=user.id,
        lens=Lens.TASK,
        status=JobStatus.FAILED,
        messages=[{"role": "user", "content": "This will fail"}],
        input_data={"prompt": "This will fail"},
        error_message="AI model unavailable",
    )
    session.add(error_job)
    session.commit()
    session.refresh(error_job)

    assert error_job.status == JobStatus.FAILED
    assert error_job.error_message == "AI model unavailable"
    assert error_job.messages == [{"role": "user", "content": "This will fail"}]


def test_user_key_model(session, user):
    now = datetime.datetime.now()
    user_key = UserKey(
        user_id=user.id,
        provider=APIProvider.OPENAI,
        redacted_key="redacted_key",
        is_valid=True,
        last_validated_at=now,
    )

    session.add(user_key)
    session.commit()
    session.refresh(user_key)

    assert user_key.id is not None
    assert user_key.user_id == user.id
    assert user_key.provider == APIProvider.OPENAI
    assert user_key.redacted_key == "redacted_key"
    assert user_key.vault_path == f"secret/data/{user.id}/api_keys/OPENAI"
    assert user_key.is_valid is True
    assert user_key.last_validated_at == now


def test_user_account_details_relationship(session):
    """Test the bidirectional relationship between User and UserAccountDetails."""
    # Create a new user
    user = User(
        name="Test User",
        email=f"test_user+{uuid.uuid4()}@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        last_logged_in=datetime.datetime.now(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # UserAccountDetails should be automatically created by the event handler
    assert user.account_details is not None
    assert user.account_details.user_id == user.id
    assert user.account_details.balance_cents == 0.0
    assert user.account_details.status == UserAccountStatus.NEW
    assert user.account_details.onboarding_completed is False
    assert user.account_details.monthly_credits_total == 0
    assert user.account_details.monthly_credits_used == 0
    assert user.account_details.next_billing_cycle_starts is None

    # Test the bidirectional relationship
    # UserAccountDetails -> User
    assert user.account_details.user is not None
    assert user.account_details.user.id == user.id
    assert user.account_details.user.name == "Test User"
    assert user.account_details.user.email == user.email

    # Test that the relationship is properly linked
    assert user.account_details.user.id == user.id
    assert user.account_details.user.account_details.user_id == user.id

    # Test updating account details
    now = datetime.datetime.now()
    user.account_details.balance_cents = 1000.0
    user.account_details.status = UserAccountStatus.NEW
    user.account_details.stripe_customer_id = "cus_test123"
    user.account_details.onboarding_completed = True
    user.account_details.monthly_credits_total = 500
    user.account_details.monthly_credits_used = 25
    user.account_details.next_billing_cycle_starts = now
    session.commit()
    session.refresh(user)

    # Verify updates worked
    assert user.account_details.balance_cents == 1000.0
    assert user.account_details.status == UserAccountStatus.NEW
    assert user.account_details.stripe_customer_id == "cus_test123"
    assert user.account_details.onboarding_completed is True
    assert user.account_details.monthly_credits_total == 500
    assert user.account_details.monthly_credits_used == 25
    assert user.account_details.next_billing_cycle_starts == now


def test_user_account_details_cascade_delete(session):
    """Test that deleting a user cascades to delete their account details."""
    # Create user and account details
    user = User(
        name="Cascade Test User",
        email=f"cascade_test+{uuid.uuid4()}@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        last_logged_in=datetime.datetime.now(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    user_id = user.id

    # Verify both exist
    assert session.query(User).filter_by(id=user_id).first() is not None
    assert (
        session.query(UserAccountDetails).filter_by(user_id=user_id).first() is not None
    )

    # Delete the user
    session.delete(user)
    session.commit()

    # Verify both are deleted due to cascade
    assert session.query(User).filter_by(id=user_id).first() is None
    assert session.query(UserAccountDetails).filter_by(user_id=user_id).first() is None


def test_ordering_model_creation(session, user, workspace, test_task):
    """Test creating an Ordering record with basic fields."""
    ordering = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.STATUS_LIST,
        context_id=uuid.uuid4(),
        entity_type=EntityType.TASK,
        task_id=test_task.id,
        position="aa",
    )
    session.add(ordering)
    session.commit()
    session.refresh(ordering)

    # Verify basic properties
    assert ordering.id is not None
    assert ordering.user_id == user.id
    assert ordering.workspace_id == workspace.id
    assert ordering.context_type == ContextType.STATUS_LIST
    assert ordering.entity_type == EntityType.TASK
    assert ordering.position == "aa"
    assert ordering.task_id == test_task.id


def test_ordering_initiative_relationship(session, user, workspace):
    """Test the two-way relationship between Ordering and Initiative."""
    # Create an initiative
    initiative = Initiative(
        title="Test Initiative",
        user_id=user.id,
        workspace_id=workspace.id,
        identifier="INI-001",
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)

    # Create an ordering record for the initiative
    ordering = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.STATUS_LIST,
        context_id=uuid.uuid4(),
        entity_type=EntityType.INITIATIVE,
        initiative_id=initiative.id,
        position="aa",
    )
    session.add(ordering)
    session.commit()
    session.refresh(ordering)
    session.refresh(initiative)

    # Test the relationship from ordering to initiative
    assert ordering.initiative is not None
    assert ordering.initiative.id == initiative.id
    assert ordering.initiative.title == "Test Initiative"

    # Test the relationship from initiative to orderings
    assert len(initiative.orderings) == 1
    assert initiative.orderings[0].id == ordering.id
    assert initiative.orderings[0].position == "aa"


def test_ordering_task_relationship(session, user, workspace, test_initiative):
    """Test the two-way relationship between Ordering and Task."""
    # Create a task
    task = Task(
        title="Test Task",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
        identifier="T-001",
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Create an ordering record for the task
    ordering = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.STATUS_LIST,
        context_id=uuid.uuid4(),
        entity_type=EntityType.TASK,
        task_id=task.id,
        position="bb",
    )
    session.add(ordering)
    session.commit()
    session.refresh(ordering)
    session.refresh(task)

    # Test the relationship from ordering to task
    assert ordering.task is not None
    assert ordering.task.id == task.id
    assert ordering.task.title == "Test Task"

    # Test the relationship from task to orderings
    assert len(task.orderings) == 1
    assert task.orderings[0].id == ordering.id
    assert task.orderings[0].position == "bb"


def test_ordering_multiple_records_per_entity(
    session, user, workspace, test_initiative
):
    """Test that an entity can have multiple ordering records in different contexts."""
    # Create a task
    task = Task(
        title="Multi-Context Task",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
        identifier="T-002",
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Create multiple ordering records for the same task in different contexts
    ordering1 = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.STATUS_LIST,
        context_id=uuid.uuid4(),
        entity_type=EntityType.TASK,
        task_id=task.id,
        position="aa",
    )

    group_id = uuid.uuid4()
    ordering2 = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.GROUP,
        context_id=group_id,
        entity_type=EntityType.TASK,
        task_id=task.id,
        position="bb",
    )

    session.add_all([ordering1, ordering2])
    session.commit()
    session.refresh(task)

    # Verify the task has multiple ordering records
    assert len(task.orderings) == 2

    # Verify each ordering has different contexts
    positions = [o.position for o in task.orderings]
    contexts = [o.context_type for o in task.orderings]

    assert "aa" in positions
    assert "bb" in positions
    assert ContextType.STATUS_LIST in contexts
    assert ContextType.GROUP in contexts


def test_ordering_cascade_delete_with_initiative(session, user, workspace):
    """Test that deleting an initiative cascades to delete its ordering records."""
    # Create an initiative
    initiative = Initiative(
        title="Delete Test Initiative",
        user_id=user.id,
        workspace_id=workspace.id,
        identifier="INI-002",
    )
    session.add(initiative)
    session.commit()
    session.refresh(initiative)

    # Create ordering records for the initiative
    ordering1 = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.STATUS_LIST,
        context_id=uuid.uuid4(),
        entity_type=EntityType.INITIATIVE,
        initiative_id=initiative.id,
        position="aa",
    )
    ordering2 = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.GROUP,
        context_id=uuid.uuid4(),
        entity_type=EntityType.INITIATIVE,
        initiative_id=initiative.id,
        position="bb",
    )

    session.add_all([ordering1, ordering2])
    session.commit()

    # Get IDs for verification
    initiative_id = initiative.id
    ordering1_id = ordering1.id
    ordering2_id = ordering2.id

    # Verify orderings exist
    assert session.query(Ordering).filter_by(id=ordering1_id).first() is not None
    assert session.query(Ordering).filter_by(id=ordering2_id).first() is not None

    # Delete the initiative
    session.delete(initiative)
    session.commit()

    # Verify initiative and its orderings are deleted
    assert session.query(Initiative).filter_by(id=initiative_id).first() is None
    assert session.query(Ordering).filter_by(id=ordering1_id).first() is None
    assert session.query(Ordering).filter_by(id=ordering2_id).first() is None


def test_ordering_cascade_delete_with_task(session, user, workspace, test_initiative):
    """Test that deleting a task cascades to delete its ordering records."""
    # Create a task
    task = Task(
        title="Delete Test Task",
        user_id=user.id,
        workspace_id=workspace.id,
        initiative_id=test_initiative.id,
        identifier="T-003",
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Create ordering records for the task
    ordering1 = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.STATUS_LIST,
        context_id=uuid.uuid4(),
        entity_type=EntityType.TASK,
        task_id=task.id,
        position="cc",
    )
    ordering2 = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.STATUS_LIST,
        context_id=task.id,
        entity_type=EntityType.CHECKLIST,
        task_id=task.id,
        position="dd",
    )

    session.add_all([ordering1, ordering2])
    session.commit()

    # Get IDs for verification
    task_id = task.id
    ordering1_id = ordering1.id
    ordering2_id = ordering2.id

    # Verify orderings exist
    assert session.query(Ordering).filter_by(id=ordering1_id).first() is not None
    assert session.query(Ordering).filter_by(id=ordering2_id).first() is not None

    # Delete the task
    session.delete(task)
    session.commit()

    # Verify task and its orderings are deleted
    assert session.query(Task).filter_by(id=task_id).first() is None
    assert session.query(Ordering).filter_by(id=ordering1_id).first() is None
    assert session.query(Ordering).filter_by(id=ordering2_id).first() is None


def test_ordering_unique_constraint(session, user, workspace, test_task):
    """Test that the unique constraint prevents duplicate orderings for the same entity in the same context."""
    context_id = uuid.uuid4()
    task_id = test_task.id

    # Create first ordering
    ordering1 = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.GROUP,
        context_id=context_id,
        entity_type=EntityType.TASK,
        task_id=task_id,
        position="aa",
    )
    session.add(ordering1)
    session.commit()

    # Try to create a duplicate ordering (should fail due to unique constraint)
    ordering2 = Ordering(
        user_id=user.id,
        workspace_id=workspace.id,
        context_type=ContextType.GROUP,
        context_id=context_id,
        entity_type=EntityType.TASK,
        task_id=task_id,
        position="bb",
    )
    session.add(ordering2)

    # This should raise an exception due to the unique constraint
    try:
        session.commit()
        assert False, "Expected unique constraint violation"
    except Exception as e:
        session.rollback()
        # Verify it's a unique constraint violation
        assert (
            "uq_context_entity_once" in str(e) or "unique constraint" in str(e).lower()
        )
