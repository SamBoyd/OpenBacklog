import React, { useState } from 'react';
import { DraggableProvided, DraggableStateSnapshot } from '@hello-pangea/dnd';
import { ThemeWithInitiatives } from '#hooks/useRoadmapWithInitiatives';
import InitiativeListItem from './InitiativeListItem';

export interface RoadmapThemeCardProps {
  theme: ThemeWithInitiatives;
  provided: DraggableProvided;
  snapshot: DraggableStateSnapshot;
  isDragDisabled: boolean;
}

/**
 * Card component displaying a roadmap theme with its details and associated initiatives
 * Supports drag and drop functionality
 * @param {RoadmapThemeCardProps} props - Component props
 * @returns {React.ReactElement} The roadmap theme card
 */
const RoadmapThemeCard: React.FC<RoadmapThemeCardProps> = ({
  theme,
  provided,
  snapshot,
  isDragDisabled,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const truncateLength = 150;
  const shouldTruncate = theme.problem_statement.length > truncateLength;
  const displayStatement = shouldTruncate && !isExpanded
    ? `${theme.problem_statement.substring(0, truncateLength)}...`
    : theme.problem_statement;

  return (
    <div
      ref={provided.innerRef}
      {...provided.draggableProps}
      {...provided.dragHandleProps}
      className={`border border-border rounded-md p-4 mb-3 bg-card transition-all ${
        snapshot.isDragging ? 'opacity-60 rotate-1 shadow-lg' : 'hover:bg-accent/5'
      } ${
        isDragDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-grab active:cursor-grabbing'
      }`}
    >
      {/* Theme Name */}
      <h3 className="text-base font-semibold text-foreground mb-2">
        {theme.name}
      </h3>

      {/* Problem Statement */}
      <div className="mb-3">
        <p className="text-sm text-foreground/80">
          {displayStatement}
        </p>
        {shouldTruncate && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-primary hover:underline mt-1"
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Hypothesis (if present) */}
      {theme.hypothesis && (
        <div className="mb-2">
          <p className="text-xs font-medium text-muted-foreground">Hypothesis:</p>
          <p className="text-sm text-foreground/70">{theme.hypothesis}</p>
        </div>
      )}

      {/* Indicative Metrics (if present) */}
      {theme.indicative_metrics && (
        <div className="mb-2">
          <p className="text-xs font-medium text-muted-foreground">Metrics:</p>
          <p className="text-sm text-foreground/70">{theme.indicative_metrics}</p>
        </div>
      )}

      {/* Time Horizon (if present) */}
      {theme.time_horizon_months !== null && theme.time_horizon_months !== undefined && (
        <div className="mb-3">
          <p className="text-xs text-muted-foreground">
            Time horizon: {theme.time_horizon_months} {theme.time_horizon_months === 1 ? 'month' : 'months'}
          </p>
        </div>
      )}

      {/* Divider */}
      {theme.strategicInitiatives.length > 0 && (
        <div className="border-t border-border my-3"></div>
      )}

      {/* Strategic Initiatives List */}
      {theme.isLoadingInitiatives ? (
        <div className="text-xs text-muted-foreground py-2">
          Loading initiatives...
        </div>
      ) : theme.strategicInitiatives.length > 0 ? (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">
            Initiatives ({theme.strategicInitiatives.length}):
          </p>
          <div className="space-y-1">
            {theme.strategicInitiatives.map((strategicInitiative) => (
              <InitiativeListItem
                key={strategicInitiative.id}
                strategicInitiative={strategicInitiative}
              />
            ))}
          </div>
        </div>
      ) : (
        <p className="text-xs text-muted-foreground italic">
          No initiatives assigned to this theme
        </p>
      )}
    </div>
  );
};

export default RoadmapThemeCard;
