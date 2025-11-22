import React, { useState } from 'react';
import { ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';

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
    <div className="bg-white border-b border-neutral-200 flex flex-col gap-4 py-4 px-8">
      {/* Filter Row */}
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-neutral-600 uppercase tracking-wider">
          Filters:
        </span>

        {/* Hero Filter Dropdown */}
        <button className="border border-neutral-300 rounded-[10px] px-4 py-2 flex items-center gap-2 hover:bg-neutral-50 transition-colors">
          <span className="text-sm text-neutral-950">Hero</span>
          <ChevronDown size={16} className="text-neutral-400" />
        </button>

        {/* Villain Filter Dropdown */}
        <button className="border border-neutral-300 rounded-[10px] px-4 py-2 flex items-center gap-2 hover:bg-neutral-50 transition-colors">
          <span className="text-sm text-neutral-950">Villain</span>
          <ChevronDown size={16} className="text-neutral-400" />
        </button>

        {/* Theme Filter Dropdown */}
        <button className="border border-neutral-300 rounded-[10px] px-4 py-2 flex items-center gap-2 hover:bg-neutral-50 transition-colors">
          <span className="text-sm text-neutral-950">Theme</span>
          <ChevronDown size={16} className="text-neutral-400" />
        </button>

        {/* Status Filter Dropdown */}
        <button className="border border-neutral-300 rounded-[10px] px-4 py-2 flex items-center gap-2 hover:bg-neutral-50 transition-colors">
          <span className="text-sm text-neutral-950">Status</span>
          <ChevronDown size={16} className="text-neutral-400" />
        </button>
      </div>

      {/* Time Period & Zoom Row */}
      <div className="flex items-center justify-between">
        {/* Time Period Selector */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-neutral-600 uppercase tracking-wider">
            Time Period:
          </span>

          <div className="flex items-center gap-2">
            <button className="p-1.5 rounded hover:bg-neutral-100 transition-colors">
              <ChevronLeft size={16} />
            </button>

            <div className="bg-neutral-100 rounded px-3 py-1.5 flex-1 min-w-48">
              <span className="text-sm text-neutral-950">Q1 2024 - Q1 2025</span>
            </div>

            <button className="p-1.5 rounded hover:bg-neutral-100 transition-colors">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {/* Zoom Control */}
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-neutral-600 uppercase tracking-wider">
            Zoom:
          </span>

          <div className="bg-neutral-100 rounded-[10px] p-1 flex gap-1">
            {(['years', 'quarters', 'months', 'weeks'] as const).map((zoomLevel) => (
              <button
                key={zoomLevel}
                onClick={() => {
                  setZoom(zoomLevel);
                  onZoomChange?.(zoomLevel);
                }}
                className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
                  zoom === zoomLevel
                    ? 'bg-white shadow-sm text-neutral-900'
                    : 'text-neutral-600 hover:text-neutral-900'
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
