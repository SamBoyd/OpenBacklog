import React from 'react';

/**
 * Props for the InitiativeProgressBar component
 */
interface InitiativeProgressBarProps {
  progress: number;
  completed: number;
  total: number;
  label?: string;
}

/**
 * InitiativeProgressBar displays a horizontal progress bar with percentage and completion count
 * @param {object} props - The component props
 * @param {number} props.progress - Progress percentage (0-100)
 * @param {number} props.completed - Number of completed items
 * @param {number} props.total - Total number of items
 * @param {string} [props.label='Scenes'] - Label for the completion count
 * @returns {React.ReactElement} The progress bar component
 */
const InitiativeProgressBar: React.FC<InitiativeProgressBarProps> = ({
  progress,
  completed,
  total,
  label = 'Scenes',
}) => (
  <div className="border-b border-border px-6 py-2.5">
    <div className="flex items-center gap-4">
      <div className="flex-1 flex flex-col gap-2">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Progress</span>
          <span className="text-foreground font-medium">{progress}%</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      <div className="text-sm text-muted-foreground whitespace-nowrap">
        {label}: <span className="text-foreground font-medium">{completed} / {total}</span> complete
      </div>
    </div>
  </div>
);

export default InitiativeProgressBar;

