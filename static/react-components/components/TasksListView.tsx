import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import { LoadingListItem } from '#components/reusable/ListItem';
import StatusGroupedListView from './reusable/StatusGroupedListView';
import { InitiativeStatus, TaskDto, TaskStatus } from '#types';
import { OrderedEntity } from '#hooks/useOrderings';

type TasksListViewProps = {
    tasks: OrderedEntity<TaskDto>[] | null | undefined;
    loading: boolean;
    error: string | null;
    onTaskClick: (taskId: string) => void;
    onOrderChange: (updatedEntity: OrderedEntity<TaskDto>, afterId: string | null, beforeId: string | null) => void;
    onStatusChange: (updatedEntity: OrderedEntity<TaskDto>, newStatus: TaskStatus | InitiativeStatus, afterId: string | null, beforeId: string | null) => void;
    initiativeId: string | null; // Keep initiativeId for empty state check
    selectedStatues?: TaskStatus[];
};

export const ListItem = ({ task, onClick }: { task: OrderedEntity<TaskDto>, onClick: () => void }) => {
    return (
        <div
            data-testid={`list-item-${task.id}`}
            key={task.id}
            className=""
            onClick={onClick}
        >
            <div className="flex-grow px-3 rounded hover:bg-muted-foreground/5 cursor-pointer">
                <div className="flex flex-row justify-start items-start">
                    <span className="text-sm text-muted flex-shrink-0">{task.identifier}</span>
                    <span className="ml-4 text-sm/6 text-foreground flex-grow">{task.title}</span>
                </div>
            </div>
        </div>
    );
};

/**
 * Container component for displaying a list of tasks grouped by status.
 * @param {TasksListViewProps} props - The component props.
 * @param {OrderedEntity<TaskDto>[] | null | undefined} props.tasks - The list of tasks to display.
 * @param {boolean} props.loading - Indicates if tasks are currently loading.
 * @param {string} props.error - An error object if fetching failed.
 * @param {(taskId: string) => void} props.onTaskClick - Callback function when a task is clicked.
 * @param {(updatedEntity: OrderedEntity<TaskDto>, newPosition: string) => void} props.onOrderChange - Callback function when tasks are reordered.
 * @param {(updatedEntity: OrderedEntity<TaskDto>, newStatus: TaskStatus | InitiativeStatus, position: string) => void} props.onStatusChange - Callback function when a task's status is changed.
 * @param {string | null} props.initiativeId - The ID of the parent initiative (used for empty state logic).
 * @param {TaskStatus[]} props.selectedStatues - Status columns to display
 * @returns {React.ReactElement} The rendered task list view.
 */
export default function TasksListView({ tasks, loading, error, onTaskClick, onOrderChange, onStatusChange, initiativeId, selectedStatues }: TasksListViewProps) {
    const renderTask = (task: OrderedEntity<TaskDto>, onItemClick: (id: string) => void) => (
        <ListItem
            key={task.id}
            task={task}
            onClick={() => onItemClick(task.id)}
        />
    );

    const renderLoadingTask = () => <LoadingListItem key={Math.random()} />;

    return (
        <StatusGroupedListView<TaskDto>
            items={tasks}
            loading={loading}
            error={error}
            emptyStateMessage="You currently don't have any Tasks. Create some below."
            showEmptyState={!!initiativeId}
            renderItem={renderTask}
            renderLoadingItem={renderLoadingTask}
            onItemClick={onTaskClick}
            onOrderChange={onOrderChange}
            onStatusChange={onStatusChange}
            dataTestId="task-list-nav"
            selectedStatuses={selectedStatues || [
                TaskStatus.TO_DO,
                TaskStatus.IN_PROGRESS,
                TaskStatus.DONE,
                TaskStatus.BLOCKED,
            ]}
        />
    );
}
