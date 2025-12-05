import React, { useMemo } from 'react';
import { ThemeDto } from '#api/productStrategy';

interface RoadmapTimelineViewProps {
  themes: ThemeDto[];
  isLoading?: boolean;
  onViewTheme?: (themeId: string) => void;
  onViewInitiatives?: (themeId: string) => void;
  onEdit?: (themeId: string) => void;
  onMoreOptions?: (themeId: string) => void;
}

/**
 * Timeline view of roadmap themes.
 * Displays themes in chronological order with quarter separators.
 */
export const RoadmapTimelineView: React.FC<RoadmapTimelineViewProps> = ({
  themes,
  isLoading = false,
  onViewTheme,
  onViewInitiatives,
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