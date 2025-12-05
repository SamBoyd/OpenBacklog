import React from 'react';
import { ArcDto } from '#api/productStrategy';
import { ArcCard } from './ArcCard';

interface RoadmapListViewProps {
  prioritizedArcs: ArcDto[];
  unprioritizedArcs: ArcDto[];
  isLoading?: boolean;
  onViewArc?: (arcId: string) => void;
  onViewInitiatives?: (arcId: string) => void;
  onMoreOptions?: (arcId: string) => void;
}

/**
 * List view of roadmap themes grouped by prioritization status.
 * Displays prioritized themes (max 5) with priority badges, followed by backlog themes.
 */
export const RoadmapListView: React.FC<RoadmapListViewProps> = ({
  prioritizedArcs,
  unprioritizedArcs,
  isLoading = false,
  onViewArc,
  onViewInitiatives,
  onMoreOptions,
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-foreground">Loading roadmap...</div>
      </div>
    );
  }

  if (prioritizedArcs.length === 0 && unprioritizedArcs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-foreground">
        <p className="text-lg font-medium">No themes yet</p>
        <p className="text-sm mt-2">Create your first roadmap theme to get started</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 px-8 py-8">
      {/* Prioritized Themes Section */}
      <div>
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-foreground">
            Prioritized Themes
            <span className="ml-2 text-sm font-normal text-foreground">
              ({prioritizedArcs.length}/5)
            </span>
          </h2>
        </div>
        {prioritizedArcs.length > 0 ? (
          <div className="space-y-4 pl-8">
            {prioritizedArcs.map((arc, index) => (
              <div key={arc.id} className="relative border-2 border-primary/50 rounded-lg">
                <ArcCard
                  arc={arc}
                  onViewArc={onViewArc}
                  onViewInitiatives={onViewInitiatives}
                  onMoreOptions={onMoreOptions}
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-foreground pl-8">
            No prioritized themes. Use MCP to prioritize themes from the backlog.
          </div>
        )}
      </div>

      {/* Backlog Section */}
      <div>
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-foreground">
            Backlog
            <span className="ml-2 text-sm font-normal text-foreground">
              ({unprioritizedArcs.length})
            </span>
          </h2>
        </div>
        {unprioritizedArcs.length > 0 ? (
          <div className="space-y-4 pl-8">
            {unprioritizedArcs.map((arc) => (
              <ArcCard
                key={arc.id}
                arc={arc}
                onViewArc={onViewArc}
                onViewInitiatives={onViewInitiatives}
                onMoreOptions={onMoreOptions}
              />
            ))}
          </div>
        ) : (
          <div className="text-sm text-foreground pl-8">
            All themes are prioritized.
          </div>
        )}
      </div>
    </div>
  );
};
