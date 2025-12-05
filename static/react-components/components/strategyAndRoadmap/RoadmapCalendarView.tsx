import React, { useMemo } from 'react';
import { ArcDto } from '#api/productStrategy';
import { ArcCard } from './ArcCard';

interface RoadmapCalendarViewProps {
  arcs: ArcDto[];
  isLoading?: boolean;
  onViewArc?: (arcId: string) => void;
  onViewInitiatives?: (arcId: string) => void;
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
export const RoadmapCalendarView: React.FC<RoadmapCalendarViewProps> = ({
  arcs,
  isLoading = false,
  onViewArc,
  onViewInitiatives,
  onEdit,
  onMoreOptions,
}) => {

    // Coming soon placeholder view
    return (
        <div className="flex items-center justify-center h-96">
            <div className="text-foreground">Calendar view coming soon</div>
        </div>
    );
};

export default RoadmapCalendarView;