import React, { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useTasksContext } from '#contexts/TasksContext';
import { TaskDto, TaskStatus } from '#types';
import KanbanBoardView from '#components/reusable/KanbanBoardView';
import { OrderedEntity } from '#hooks/useOrderings';
import { computeOrderingIds } from '#utils/dragDropUtils';

/**
 * Canonical display order for task status columns in the Kanban board.
 * This ensures consistent column ordering regardless of how statuses are passed in.
 */
const TASK_STATUS_ORDER: TaskStatus[] = [
    TaskStatus.TO_DO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.BLOCKED,
    TaskStatus.DONE,
    TaskStatus.ARCHIVED,
];

type TasksKanbanBoardProps = {
    filterToInitiativeId?: string;
    reloadCounter?: number;
    onUpdate?: () => void;
    filterToStatus: TaskStatus[];
};

const TasksKanbanBoard = ({ filterToInitiativeId, reloadCounter, onUpdate, filterToStatus }: TasksKanbanBoardProps) => {
    const { tasks, shouldShowSkeleton, error, updateTask, reloadTasks, setInitiativeId, reorderTask, moveTaskToStatus } = useTasksContext();
    const navigate = useNavigate();

    // Sort selected statuses according to canonical order
    const orderedStatuses = TASK_STATUS_ORDER.filter(status =>
        filterToStatus.includes(status)
    );

    // Update the context when filterToInitiativeId changes
    useEffect(() => {
        setInitiativeId(filterToInitiativeId);
    }, [filterToInitiativeId, setInitiativeId]);

    useEffect(() => {
        reloadTasks();
    }, [reloadCounter]);

    useEffect(() => {
        if (filterToInitiativeId !== null) {
            reloadTasks();
        }
    }, [filterToInitiativeId]);

    // Called when an item is dragged to a new column.
    const handleItemDrag = async (task: OrderedEntity<TaskDto>, dropIndex: number) => {
        if (!tasks) {
            console.error('[TasksKanbanBoard] handleItemDrag: tasks is undefined');
            return;
        }

        const oldTask = tasks.find(t => t.id === task.id);
        if (!oldTask) {
            console.error('[TasksKanbanBoard] handleItemDrag: oldTask is undefined');
            return;
        }

        const orderedByStatus = tasks?.filter(t => t.status === task.status);
        const newIndex = dropIndex;
        const oldIndex = orderedByStatus.findIndex(t => t.id === task.id)
        const newStatus = task.status
        const oldStatus = oldTask.status

        if (newIndex === oldIndex && newStatus === oldStatus) {
            return;
        }

        const { beforeId, afterId } = computeOrderingIds(orderedByStatus, oldTask.id, newIndex);

        if (task.status === oldTask.status) {
            await reorderTask(task.id, afterId, beforeId);
        } else {
            await moveTaskToStatus(task.id, task.status as TaskStatus, afterId, beforeId);
        }
    };

    /**
     * Navigate to task detail when a card is clicked.
     */
    const handleCardClick = (task: TaskDto) => {
        navigate(`/workspace/initiatives/${filterToInitiativeId}/tasks/${task.id}`);
    };

    const hasBlockedTasks = tasks?.some(t => t.status === TaskStatus.BLOCKED);

    return (
        <KanbanBoardView<TaskDto>
            data={tasks || undefined}
            loading={shouldShowSkeleton}
            error={error ? new Error(error) : null}
            onCardClick={handleCardClick}
            onItemDrag={handleItemDrag}
            type="task"
            showBlocked={hasBlockedTasks}
            disabled={filterToInitiativeId === undefined}
            disabledMessage="Select an initiative to view tasks."
            filterToStatus={orderedStatuses}
        />
    );
};

export default TasksKanbanBoard;
