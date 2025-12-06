import React, { useState } from 'react';
import { ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button, NoBorderButton } from '#components/reusable/Button';

interface RoadmapFilterControlsProps {
  onHeroFilterChange?: (heroId: string | null) => void;
  onVillainFilterChange?: (villainId: string | null) => void;
  onThemeFilterChange?: (themeId: string | null) => void;
  onStatusFilterChange?: (status: string | null) => void;
  onTimePeriodChange?: (period: string) => void;
  onZoomChange?: (zoom: 'years' | 'quarters' | 'months' | 'weeks') => void;
}

/**
 * Filter controls for the roadmap overview.
 * Includes filter dropdowns, time period navigation, and zoom level controls.
 * Note: Currently UI-only, filters are non-functional.
 */
export const RoadmapFilterControls: React.FC<RoadmapFilterControlsProps> = ({
  onHeroFilterChange,
  onVillainFilterChange,
  onThemeFilterChange,
  onStatusFilterChange,
  onTimePeriodChange,
  onZoomChange,
}) => {
  const [zoom, setZoom] = useState<'years' | 'quarters' | 'months' | 'weeks'>('quarters');

  return (
    <div className="bg-background text-foreground   border-b border-border flex flex-col gap-4 py-4 px-8">
      {/* Filter Row */}
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-foreground uppercase tracking-wider">
          Filters:
        </span>

        {/* Hero Filter Dropdown */}
        <Button onClick={() => {}}>
          <span className="text-sm text-foreground0">Hero</span>
          <ChevronDown size={16} className="text-foreground" />
        </Button>

        {/* Villain Filter Dropdown */}
        <Button onClick={() => {}}>
          <span className="text-sm text-foreground0">Villain</span>
          <ChevronDown size={16} className="text-foreground" />
        </Button>

        {/* Theme Filter Dropdown */}
        <Button onClick={() => {}}>
          <span className="text-sm text-foreground0">Theme</span>
          <ChevronDown size={16} className="text-foreground" />
        </Button>

        {/* Status Filter Dropdown */}
        <Button onClick={() => {}}>
          <span className="text-sm text-foreground0">Status</span>
          <ChevronDown size={16} className="text-foreground" />
        </Button>
      </div>

      {/* Time Period & Zoom Row */}
      <div className="flex items-center justify-between">
        {/* Time Period Selector */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-foreground uppercase tracking-wider">
            Time Period:
          </span>

          <div className="flex items-center gap-2">
            <NoBorderButton onClick={() => {}}>
              <ChevronLeft size={16} />
            </NoBorderButton>

            <div className="bg-background border border-border rounded px-3 py-1.5 flex-1 min-w-48">
              <span className="text-sm text-foreground0">Q1 2024 - Q1 2025</span>
            </div>

            <NoBorderButton onClick={() => {}}>
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
