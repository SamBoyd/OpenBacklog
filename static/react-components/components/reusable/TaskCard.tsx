import React from 'react';
import { NoBorderButton } from '#components/reusable/Button';
import InlineMarkdownPreview from '#components/reusable/InlineMarkdownPreview';
import { TaskDto, TaskStatus, statusDisplay } from '#types';
import { Circle, CircleCheckBig, CircleX, Clock, Eye } from 'lucide-react';

/**
 * Props for the TaskCard component
 */
interface TaskCardProps {
  task: Partial<TaskDto>;
  onViewTask?: () => void;
}

/**
 * Gets the status emoji based on task status
 * @param {string} status - The task status
 * @returns {string} Emoji representing the status
 */
const getStatusEmoji = (status: string | undefined): React.ReactNode => {
  switch (status) {
    case TaskStatus.DONE:
      return <CircleCheckBig className='w-4 h-4 text-foreground' />;
    case TaskStatus.IN_PROGRESS:
      return <Clock className='w-4 h-4 text-foreground' />;
    case TaskStatus.BLOCKED:
      return <CircleX className='w-4 h-4 text-foreground' />;
    case TaskStatus.TO_DO:
    default:
      return <Circle className='w-4 h-4 text-foreground' />;
  }
};

/**
 * Gets the status badge styling based on task status
 * @param {string} status - The task status
 * @returns {string} Tailwind CSS classes for the badge
 */
const getStatusBadgeStyle = (status: string | undefined): string => {
  switch (status) {
    case TaskStatus.DONE:
      return 'bg-foreground text-background';
    case TaskStatus.IN_PROGRESS:
      return 'bg-status-in-progress text-status-in-progress-foreground';
    case TaskStatus.BLOCKED:
      return 'bg-destructive text-destructive-foreground';
    case TaskStatus.TO_DO:
    default:
      return 'bg-foreground text-background';
  }
};

/**
 * TaskCard displays a task with status emoji, badge, description, and view button
 * Designed for use in the Strategic Initiative detail view
 * @param {object} props - The component props
 * @param {Partial<TaskDto>} props.task - The task data to display
 * @param {function} [props.onViewTask] - Callback when "View Scene" is clicked
 * @returns {React.ReactElement} The task card component
 */
const TaskCard: React.FC<TaskCardProps> = ({ task, onViewTask }) => (
  <div
    className="bg-background border border-border rounded-lg p-4"
    data-testid={`task-card-${task.id}`}
  >
    {/* Status emoji and title */}
    <div className="flex items-start gap-3">

      <div className="flex items-center justify-center h-6">
        {getStatusEmoji(task.status)}
      </div>

      <div className="flex-1 min-w-0 gap-y-2 flex flex-col items-start">
        {/* Title */}
        <div>
          <h3 className="text-base text-foreground">{task.title}</h3>
        </div>

        {/* Status badge */}
        <div
          className={`w-fit px-2 py-0.5 text-xs font-medium rounded-lg ${getStatusBadgeStyle(task.status)}`}
        >
          {statusDisplay(task.status as TaskStatus)}
        </div>

        {/* Description (2 lines max) with inline markdown */}
        {task.description && (
          <p className="text-sm text-muted-foreground leading-5 line-clamp-2">
            <InlineMarkdownPreview content={task.description} />
          </p>
        )}

        {/* View Scene button */}
        {onViewTask && (
          <NoBorderButton
            onClick={onViewTask}
            className="text-sm font-medium text-foreground"
          >
            <Eye size={16} />
            View Task
          </NoBorderButton>
        )}
      </div>
    </div>
  </div>
);

export default TaskCard;
