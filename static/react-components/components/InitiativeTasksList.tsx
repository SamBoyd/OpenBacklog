import React from 'react';
import TaskCard from '#components/reusable/TaskCard';
import { TaskDto } from '#types';

/**
 * Props for the InitiativeTasksList component
 */
interface InitiativeTasksListProps {
  tasks: Partial<TaskDto>[];
  onTaskClick: (taskId: string) => void;
}

/**
 * InitiativeTasksList displays a simple list of tasks for the Strategic Initiative view
 * No drag-and-drop or status grouping - just a clean list of TaskCards
 * @param {object} props - The component props
 * @param {Partial<TaskDto>[]} props.tasks - Array of tasks to display
 * @param {function} props.onTaskClick - Callback when a task's "View Scene" button is clicked
 * @returns {React.ReactElement} The tasks list component
 */
const InitiativeTasksList: React.FC<InitiativeTasksListProps> = ({
  tasks,
  onTaskClick,
}) => {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-muted-foreground">
          No tasks have been defined yet
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3" data-testid="initiative-tasks-list">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onViewTask={() => task.id && onTaskClick(task.id)}
        />
      ))}
    </div>
  );
};

export default InitiativeTasksList;
