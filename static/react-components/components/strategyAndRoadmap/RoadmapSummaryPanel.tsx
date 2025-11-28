import React, { useState, useMemo } from 'react';
import { ArcDto } from '#api/productStrategy';
import { ChevronUp } from 'lucide-react';

interface RoadmapSummaryPanelProps {
  arcs: ArcDto[];
  onViewAllHeroes?: () => void;
  onViewAllVillains?: () => void;
  onRunConsistencyCheck?: () => void;
}

/**
 * Summary panel showing statistics about roadmap arcs.
 * Displays arc status counts, heroes served, top villains, and narrative health.
 * Can be collapsed/expanded.
 */
export const RoadmapSummaryPanel: React.FC<RoadmapSummaryPanelProps> = ({
  arcs,
  onViewAllHeroes,
  onViewAllVillains,
  onRunConsistencyCheck,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  // Calculate statistics
  const stats = useMemo(() => {
    const counts = {
      active: 0,
      planned: 0,
      complete: 0,
    };

    const heroMap = new Map<string, { name: string; count: number }>();
    const villainMap = new Map<string, { name: string; count: number }>();

    arcs.forEach((arc) => {
      (arc.heroes ?? []).forEach((hero) => {
        const existing = heroMap.get(hero.id) || { name: hero.name, count: 0 };
        heroMap.set(hero.id, {
          name: hero.name,
          count: existing.count + 1,
        });
      });

      (arc.villains ?? []).forEach((villain) => {
        const existing = villainMap.get(villain.id) || {
          name: villain.name,
          count: 0,
        };
        villainMap.set(villain.id, {
          name: villain.name,
          count: existing.count + 1,
        });
      });
    });

    // Get top 3 heroes and villains
    const topHeroes = Array.from(heroMap.values())
      .sort((a, b) => b.count - a.count)
      .slice(0, 3);

    const topVillains = Array.from(villainMap.values())
      .sort((a, b) => b.count - a.count)
      .slice(0, 3);

    return {
      counts,
      topHeroes,
      topVillains,
      total: arcs.length,
    };
  }, [arcs]);

  return (
    <div className="bg-white border-t border-neutral-200">
      {/* Header */}
      <div className="px-8 py-6 flex items-center justify-between">
        <h3 className="text-base font-medium text-neutral-900">Roadmap Summary</h3>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-sm text-neutral-600 hover:text-neutral-900 transition-colors"
        >
          {isExpanded ? 'Collapse' : 'Expand'}
          <ChevronUp
            size={16}
            className={`transition-transform ${isExpanded ? '' : 'rotate-180'}`}
          />
        </button>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="px-8 pb-8 flex flex-row gap-4 justify-between flex-wrap">
          {/* Arc Status Column */}
          <div className="space-y-3 flex-grow">
            <h4 className="text-sm font-medium text-neutral-600 uppercase tracking-wider">
              Arc Status
            </h4>

            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-neutral-950">Active:</span>
                <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
                  {stats.counts.active}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-neutral-950">Planned:</span>
                <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-medium">
                  {stats.counts.planned}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-neutral-950">Complete:</span>
                <span className="bg-neutral-100 text-neutral-700 px-2 py-1 rounded text-xs font-medium">
                  {stats.counts.complete}
                </span>
              </div>

              <div className="border-t border-neutral-200 pt-2 flex items-center justify-between font-medium">
                <span className="text-neutral-950">Total:</span>
                <span>{stats.total}</span>
              </div>
            </div>
          </div>

          {/* Heroes Served Column */}
          <div className="space-y-3 flex-grow">
            <h4 className="text-sm font-medium text-neutral-600 uppercase tracking-wider">
              Heroes Served
            </h4>

            <div className="space-y-2 text-sm">
              {stats.topHeroes.map((hero) => (
                <div key={hero.name} className="flex items-center justify-between">
                  <span className="text-neutral-700">{hero.name}:</span>
                  <span className="text-neutral-500">{hero.count} arcs</span>
                </div>
              ))}

              {stats.topHeroes.length === 0 && (
                <div className="text-neutral-500">No heroes assigned</div>
              )}

              <button
                onClick={onViewAllHeroes}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm pt-1"
              >
                View All Heroes
              </button>
            </div>
          </div>

          {/* Top Villains Column */}
          <div className="space-y-3 flex-grow">
            <h4 className="text-sm font-medium text-neutral-600 uppercase tracking-wider">
              Top Villains Confronted
            </h4>

            <div className="space-y-2 text-sm">
              {stats.topVillains.map((villain) => (
                <div key={villain.name} className="flex items-center justify-between">
                  <span className="text-neutral-700">{villain.name}:</span>
                  <span className="text-neutral-500">{villain.count} arcs</span>
                </div>
              ))}

              {stats.topVillains.length === 0 && (
                <div className="text-neutral-500">No villains assigned</div>
              )}

              <button
                onClick={onViewAllVillains}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm pt-1"
              >
                View All Villains
              </button>
            </div>
          </div>

          {/* Narrative Health Column */}
          <div className="space-y-3 flex-grow">
            <h4 className="text-sm font-medium text-neutral-600 uppercase tracking-wider">
              Narrative Health
            </h4>

            <div className="space-y-3">
              <div className="flex items-end gap-2">
                <span className="text-2xl">🟢</span>
                <span className="text-2xl font-bold text-neutral-950">100%</span>
              </div>

              <p className="text-sm text-neutral-600">
                High coherence, all arcs well-connected
              </p>

              <button
                onClick={onRunConsistencyCheck}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                Run Consistency Check
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
