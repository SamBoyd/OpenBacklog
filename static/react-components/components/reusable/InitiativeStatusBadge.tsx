import React from 'react';
import { InitiativeStatus, statusDisplay } from '#types';

/**
 * Props for the InitiativeStatusBadge component
 */
interface InitiativeStatusBadgeProps {
  status: string | undefined;
  className?: string;
}

/**
 * Gets the status badge styling based on initiative status
 * @param {string} status - The initiative status
 * @returns {string} Tailwind CSS classes for the badge
 */
const getStatusBadgeStyle = (status: string | undefined): string => {
  switch (status) {
    case InitiativeStatus.IN_PROGRESS:
      return 'bg-status-in-progress border-status-in-progress text-status-in-progress-foreground';
    case InitiativeStatus.DONE:
      return 'bg-status-done border-status-done text-status-done-foreground';
    case InitiativeStatus.BLOCKED:
      return 'bg-destructive border-destructive text-destructive-foreground';
    case InitiativeStatus.TO_DO:
      return 'bg-status-todo border-status-todo text-status-todo-foreground';
    case InitiativeStatus.BACKLOG:
      return 'bg-muted border-muted text-muted-foreground';
    default:
      return 'bg-muted border-muted text-muted-foreground';
  }
};

/**
 * InitiativeStatusBadge displays a status badge with appropriate styling
 * @param {object} props - The component props
 * @param {string} props.status - The initiative status value
 * @param {string} [props.className] - Additional CSS classes
 * @returns {React.ReactElement} The status badge component
 */
const InitiativeStatusBadge: React.FC<InitiativeStatusBadgeProps> = ({
  status,
  className = '',
}) => (
  <span
    className={`px-3 py-1 text-xs font-medium rounded-lg border ${getStatusBadgeStyle(status)} ${className}`}
  >
    {statusDisplay(status as any)}
  </span>
);

export default InitiativeStatusBadge;

export { getStatusBadgeStyle };

