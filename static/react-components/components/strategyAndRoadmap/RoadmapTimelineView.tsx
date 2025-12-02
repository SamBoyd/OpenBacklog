import React, { useMemo } from 'react';
import { ArcDto } from '#api/productStrategy';
import { ArcCard } from './ArcCard';

interface RoadmapTimelineViewProps {
  arcs: ArcDto[];
  isLoading?: boolean;
  onViewArc?: (arcId: string) => void;
  onViewBeats?: (arcId: string) => void;
  onEdit?: (arcId: string) => void;
  onMoreOptions?: (arcId: string) => void;
}

interface ArcsByQuarter {
  [quarter: string]: ArcDto[];
}

/**
 * List view of roadmap arcs grouped by quarter.
 * Displays arcs in chronological order with quarter separators.
 */
export const RoadmapTimelineView: React.FC<RoadmapTimelineViewProps> = ({
  arcs,
  isLoading = false,
  onViewArc,
  onViewBeats,
  onEdit,
  onMoreOptions,
}) => {

    // Coming soon placeholder view
    return (
        <div className="flex items-center justify-center h-96">
            <div className="text-foreground">Timeline view coming soon</div>
        </div>
    );
};

export default RoadmapTimelineView;