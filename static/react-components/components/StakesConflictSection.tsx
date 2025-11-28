import React from 'react';
import { ConflictDto, ConflictStatus } from '#types';
import Card from './reusable/Card';

export interface StakesConflictSectionProps {
  conflicts: ConflictDto[];
}

/**
 * Gets the status badge color for a conflict
 * @param {ConflictStatus} status - The conflict status
 * @returns {string} Tailwind CSS color classes
 */
const getStatusBadgeColor = (status: ConflictStatus): string => {
  switch (status) {
    case ConflictStatus.OPEN:
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    case ConflictStatus.ESCALATING:
      return 'bg-red-500/10 text-red-500 border-red-500/20';
    case ConflictStatus.RESOLVING:
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    case ConflictStatus.RESOLVED:
      return 'bg-green-500/10 text-green-500 border-green-500/20';
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
  }
};

/**
 * Formats conflict status for display
 * @param {ConflictStatus} status - The conflict status
 * @returns {string} Formatted status text
 */
const formatStatus = (status: ConflictStatus): string => {
  return status.replace(/_/g, ' ');
};

/**
 * StakesConflictSection displays the conflicts and their stakes
 * @param {StakesConflictSectionProps} props - The component props
 * @returns {React.ReactElement} The StakesConflictSection component
 */
const StakesConflictSection: React.FC<StakesConflictSectionProps> = ({
  conflicts,
}) => {
  if (!conflicts || conflicts.length === 0) {
    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-3">Stakes & Conflicts</h3>
        <p className="text-sm text-muted-foreground italic">
          No conflicts defined for this initiative
        </p>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">Stakes & Conflicts</h3>

      <div className="space-y-4">
        {conflicts.map((conflict) => (
          <Card
            key={conflict.id}
            className="border border-border p-4"
          >
            {/* Conflict Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <p className="text-xs text-muted-foreground font-mono mb-1">
                  {conflict.identifier}
                </p>
                <h4 className="text-base font-semibold text-foreground mb-2">
                  {conflict.hero?.name || 'Unknown Hero'} vs {conflict.villain?.name || 'Unknown Obstacle'}
                </h4>
              </div>
              <span
                className={`text-xs px-2 py-1 rounded border font-medium whitespace-nowrap ml-2 ${getStatusBadgeColor(
                  conflict.status
                )}`}
              >
                {formatStatus(conflict.status)}
              </span>
            </div>

            {/* Conflict Description */}
            {conflict.description && (
              <p className="text-sm text-muted-foreground mb-3">
                {conflict.description}
              </p>
            )}

            {/* Success/Failure Stakes */}
            <div className="grid grid-cols-2 gap-3">
              {/* Success Stakes */}
              <div className="p-3 rounded border border-success/20 bg-success/5">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">✓</span>
                  <p className="text-xs font-semibold text-success">SUCCESS</p>
                </div>
                <p className="text-xs text-muted-foreground">
                  Resolving this conflict enables progress
                </p>
              </div>

              {/* Failure Stakes */}
              <div className="p-3 rounded border border-destructive/20 bg-destructive/5">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">✕</span>
                  <p className="text-xs font-semibold text-destructive">RISK</p>
                </div>
                <p className="text-xs text-muted-foreground">
                  Ignoring this conflict blocks success
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default StakesConflictSection;
