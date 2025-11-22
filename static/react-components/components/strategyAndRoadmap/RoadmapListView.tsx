import React, { useMemo } from 'react';
import { ArcDto } from '#api/productStrategy';
import { ArcCard } from './ArcCard';

interface RoadmapListViewProps {
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
export const RoadmapListView: React.FC<RoadmapListViewProps> = ({
  arcs,
  isLoading = false,
  onViewArc,
  onViewBeats,
  onEdit,
  onMoreOptions,
}) => {
  const arcsByQuarter = useMemo(() => {
    const grouped: ArcsByQuarter = {};

    arcs.forEach((arc) => {
      const quarter = arc.started_quarter || 'Unscheduled';
      if (!grouped[quarter]) {
        grouped[quarter] = [];
      }
      grouped[quarter].push(arc);
    });

    return grouped;
  }, [arcs]);

  // Sort quarters in chronological order
  const sortedQuarters = useMemo(() => {
    return Object.keys(arcsByQuarter).sort((a, b) => {
      // Extract year and quarter from "Q1 2024" format
      const [aQuarter, aYear] = a.split(' ');
      const [bQuarter, bYear] = b.split(' ');

      if (aYear !== bYear) {
        return parseInt(aYear) - parseInt(bYear);
      }

      const aQuarterNum = parseInt(aQuarter.substring(1));
      const bQuarterNum = parseInt(bQuarter.substring(1));
      return aQuarterNum - bQuarterNum;
    });
  }, [arcsByQuarter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-neutral-500">Loading roadmap...</div>
      </div>
    );
  }

  if (arcs.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-neutral-500">No arcs found. Create your first strategic arc to get started.</div>
      </div>
    );
  }

  return (
    <div className="space-y-8 px-8 py-8">
      {sortedQuarters.map((quarter) => (
        <div key={quarter}>
          {/* Quarter Header with Divider */}
          <div className="flex items-center gap-4 mb-6">
            <div className="flex-1 h-px bg-neutral-300" />
            <h2 className="text-lg font-medium text-neutral-700 px-4">
              {quarter}
            </h2>
            <div className="flex-1 h-px bg-neutral-300" />
          </div>

          {/* Arc Cards for this Quarter */}
          <div className="space-y-4 pl-4">
            {arcsByQuarter[quarter].map((arc) => (
              <ArcCard
                key={arc.id}
                arc={arc}
                onViewArc={onViewArc}
                onViewBeats={onViewBeats}
                onEdit={onEdit}
                onMoreOptions={onMoreOptions}
              />
            ))}
          </div>

          {/* Empty State for Quarter */}
          {arcsByQuarter[quarter].length === 0 && (
            <div className="bg-neutral-50 rounded-lg p-8 text-center text-neutral-500">
              No arcs starting this quarter
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
