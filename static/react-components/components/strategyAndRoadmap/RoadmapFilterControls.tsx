import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { NoBorderButton } from '#components/reusable/Button';
import { MultiSelectDropdown, MultiSelectOption } from '#components/reusable/MultiSelectDropdown';
import { HeroRef, VillainRef } from '#api/productStrategy';

const getCurrentQuarter = (): { quarter: number; year: number } => {
  const now = new Date();
  const month = now.getMonth();
  const quarter = Math.floor(month / 3) + 1;
  const year = now.getFullYear();
  return { quarter, year };
};

const formatQuarterRange = (): string => {
  const { quarter, year } = getCurrentQuarter();
  const endYear = year + 1;
  return `Q${quarter} ${year} - Q${quarter} ${endYear}`;
};

interface RoadmapFilterControlsProps {
  heroes?: HeroRef[];
  villains?: VillainRef[];
  selectedHeroIds: string[];
  selectedVillainIds: string[];
  onHeroFilterChange: (heroIds: string[]) => void;
  onVillainFilterChange: (villainIds: string[]) => void;
  onZoomChange?: (zoom: 'years' | 'quarters' | 'months' | 'weeks') => void;
}

/**
 * Filter controls for the roadmap overview.
 * Includes filter dropdowns for heroes and villains, time period navigation, and zoom level controls.
 */
export const RoadmapFilterControls: React.FC<RoadmapFilterControlsProps> = ({
  heroes = [],
  villains = [],
  selectedHeroIds,
  selectedVillainIds,
  onHeroFilterChange,
  onVillainFilterChange,
  onZoomChange,
}) => {
  const [zoom, setZoom] = useState<'years' | 'quarters' | 'months' | 'weeks'>('quarters');
  const quarterRange = useMemo(() => formatQuarterRange(), []);

  const heroOptions: MultiSelectOption[] = heroes.map((hero) => ({
    id: hero.id,
    label: hero.name,
    description: hero.is_primary ? 'Primary Hero' : undefined,
  }));

  const villainOptions: MultiSelectOption[] = villains.map((villain) => ({
    id: villain.id,
    label: villain.name,
    description: villain.villain_type ? villain.villain_type.toLowerCase() : undefined,
  }));

  return (
    <div className="bg-background text-foreground border-b border-border flex flex-col gap-4 py-4 px-8">
      {/* Filter Row */}
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-foreground uppercase tracking-wider">
          Filters:
        </span>

        <MultiSelectDropdown
          label="Heroes"
          options={heroOptions}
          selectedIds={selectedHeroIds}
          onChange={onHeroFilterChange}
          placeholder="All"
          disabled={heroes.length === 0}
        />

        <MultiSelectDropdown
          label="Villains"
          options={villainOptions}
          selectedIds={selectedVillainIds}
          onChange={onVillainFilterChange}
          placeholder="All"
          disabled={villains.length === 0}
        />
      </div>

      {/* Time Period & Zoom Row */}
      <div className="flex items-center justify-between">
        {/* Time Period Selector */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-foreground uppercase tracking-wider">
            Time Period:
          </span>

          <div className="flex items-center gap-2">
            <NoBorderButton disabled={true} onClick={() => {}}>
              <ChevronLeft size={16} />
            </NoBorderButton>

            <div className="bg-background border border-border rounded px-3 py-1.5 flex-1 min-w-48">
              <span className="text-sm text-foreground">{quarterRange}</span>
            </div>

            <NoBorderButton disabled={true} onClick={() => {}}>
              <ChevronRight size={16} />
            </NoBorderButton>
          </div>
        </div>

        {/* Zoom Control */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-foreground uppercase tracking-wider">
            Zoom:
          </span>

          <div className="bg-muted/10 border border-border rounded-[10px] p-1 flex gap-1">
            {(['years', 'quarters', 'months', 'weeks'] as const).map((zoomLevel) => (
              <button
                disabled={true}
                key={zoomLevel}
                onClick={() => {
                  setZoom(zoomLevel);
                  onZoomChange?.(zoomLevel);
                }}
                className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
                  zoom === zoomLevel
                    ? 'bg-background text-foreground  border border-border shadow-sm'
                    : 'text-foreground hover:text-foreground'
                }`}
              >
                {zoomLevel.charAt(0).toUpperCase() + zoomLevel.slice(1)}
                {zoomLevel === 'quarters' && ' ✓'}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
