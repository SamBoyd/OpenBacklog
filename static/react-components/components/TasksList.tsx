import React from 'react';
import { useTasksContext } from '#contexts/TasksContext';
import { useNavigate } from 'react-router';
import TasksListView from './TasksListView'; // Import the new presentational component
import { InitiativeStatus, TaskDto, TaskStatus } from '#types';
import { OrderedEntity } from '#hooks/useOrderings';

type TasksListContainerProps = {
    initiativeId: string | null;
    reloadCounter?: number;
    filterToStatus?: TaskStatus[];
    onUpdate?: () => void; // Keep onUpdate if needed for other purposes, otherwise remove
};

/**
 * Container component for managing and displaying tasks related to an initiative.
 * Handles data fetching, state management, and navigation logic.
 * @param {TasksListContainerProps} props - The component props.
 * @param {string | null} props.initiativeId - The ID of the initiative whose tasks are to be displayed.
 * @param {number} [props.reloadCounter] - A counter that triggers reshouldShowSkeleton when changed.
 * @param {TaskStatus[]} [props.filterToStatus] - The statuses to filter the tasks by.
 * @param {() => void} [props.onUpdate] - Optional callback function.
 * @returns {React.ReactElement} The rendered container component.
 */
export default function TasksList({ initiativeId, reloadCounter, filterToStatus }: TasksListContainerProps) {
    const { tasks, shouldShowSkeleton, error, reloadTasks, updateTask, setInitiativeId, reorderTask, moveTaskToStatus } = useTasksContext();
    const navigate = useNavigate();

    // Update the context on mount
    React.useEffect(() => {
        setInitiativeId(initiativeId);
    }, []);

    const filteredTasks = tasks?.filter(task => filterToStatus?.includes(task.status as TaskStatus));
    // Reload tasks when the reloadCounter changes
    React.useEffect(() => {
        if (reloadCounter !== undefined) { // Only reload if reloadCounter is provided
            reloadTasks();
        }
    }, [reloadCounter]);

    // Navigate to task detail when clicked.
    const handleTaskClick = (taskId: string) => {
        if (shouldShowSkeleton || error || !initiativeId) return; // Ensure initiativeId exists
        const task = tasks?.find(t => t.id === taskId);
        if (!task) return;

        navigate(`/workspace/initiatives/${initiativeId}/tasks/${task.id}`);
    };

    const handleOrderChange = async (updatedEntity: OrderedEntity<TaskDto>, afterId: string | null, beforeId: string | null) => {
        await reorderTask(updatedEntity.id, afterId, beforeId);
    };

    const handleStatusChange = async (updatedEntity: OrderedEntity<TaskDto>, newStatus: TaskStatus | InitiativeStatus, afterId: string | null, beforeId: string | null) => {
        await moveTaskToStatus(updatedEntity.id, newStatus as TaskStatus, afterId, beforeId);
    };

    return (
        <TasksListView
            tasks={filteredTasks || []}
            loading={shouldShowSkeleton}
            error={error?.toString() || ''}
            onTaskClick={handleTaskClick}
            onOrderChange={handleOrderChange}
            onStatusChange={handleStatusChange}
            initiativeId={initiativeId} // Pass initiativeId for empty state check
            selectedStatues={filterToStatus}
        />
    );
}
