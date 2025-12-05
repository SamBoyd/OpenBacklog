import React, { useState } from 'react';
import { RoadmapHeader } from '#components/strategyAndRoadmap/RoadmapHeader';
import { RoadmapFilterControls } from '#components/strategyAndRoadmap/RoadmapFilterControls';
import { RoadmapListView } from '#components/strategyAndRoadmap/RoadmapListView';
import { RoadmapSummaryPanel } from '#components/strategyAndRoadmap/RoadmapSummaryPanel';
import { useRoadmapThemes } from '#hooks/strategyAndRoadmap/useRoadmapThemes';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { RoadmapCalendarView } from '#components/strategyAndRoadmap/RoadmapCalendarView';
import { RoadmapTimelineView } from '#components/strategyAndRoadmap/RoadmapTimelineView';

/**
 * Roadmap Overview page displays roadmap themes organized by prioritization status.
 * Users can view prioritized themes (active roadmap, max 5) and unprioritized themes (backlog),
 * with narrative context including heroes and villains. Supports list, timeline, and calendar views.
 */
export function RoadmapOverview() {
  const { currentWorkspace } = useWorkspaces();
  const {
    prioritizedThemes,
    unprioritizedThemes,
    isLoading
  } = useRoadmapThemes(currentWorkspace?.id || '');

  const [currentView, setCurrentView] = useState<'timeline' | 'list' | 'calendar'>('list');
  
  const handleViewTheme = (themeId: string) => {
    console.log('View Theme:', themeId);
    // TODO: Navigate to theme detail view
  };

  const handleViewInitiatives = (themeId: string) => {
    console.log('View Initiatives/Retrospective:', themeId);
    // TODO: Navigate to Initiatives view
  };

  const handleThemeMoreOptions = (themeId: string) => {
    console.log('More Options for Theme:', themeId);
    // TODO: Show context menu
  };

  const handleViewAllHeroes = () => {
    console.log('View All Heroes');
    // TODO: Navigate to heroes page
  };

  const handleViewAllVillains = () => {
    console.log('View All Villains');
    // TODO: Navigate to villains page
  };

  const handleRunConsistencyCheck = () => {
    console.log('Run Consistency Check');
    // TODO: Trigger consistency check analysis
  };

  return (
    <div className="h-full flex flex-col">
      {/* Page Header */}
      <RoadmapHeader
        workspaceName="Workspace Name"
        onViewToggle={(view) => {
          console.log('View changed to:', view);
          setCurrentView(view);
        }}
      />

      {/* Filter Controls */}
      <RoadmapFilterControls
        onZoomChange={(zoom) => console.log('Zoom changed to:', zoom)}
      />

      {/* Main Content - List View */}
      {currentView === 'list' && (
        <div className="flex-1 overflow-y-auto">
          <RoadmapListView
            prioritizedThemes={prioritizedThemes}
            unprioritizedThemes={unprioritizedThemes}
            isLoading={isLoading}
            onViewTheme={handleViewTheme}
            onViewInitiatives={handleViewInitiatives}
            onMoreOptions={handleThemeMoreOptions}
          />
        </div>
      )}

      {currentView === 'timeline' && (
        <div className="flex-1 overflow-y-auto">
          <RoadmapTimelineView
            themes={[]}
            isLoading={isLoading}
            onViewTheme={handleViewTheme}
            onViewInitiatives={handleViewInitiatives}
          />
        </div>
      )}

      {currentView === 'calendar' && (
        <div className="flex-1 overflow-y-auto">
          <RoadmapCalendarView
            themes={[]}
            isLoading={isLoading}
            onViewTheme={handleViewTheme}
            onViewInitiatives={handleViewInitiatives}
          />
        </div>
      )}

      {/* Summary Panel */}
      <RoadmapSummaryPanel
        themes={[...prioritizedThemes, ...unprioritizedThemes]}
        onViewAllHeroes={handleViewAllHeroes}
        onViewAllVillains={handleViewAllVillains}
        onRunConsistencyCheck={handleRunConsistencyCheck}
      />
    </div>
  );
}

export default RoadmapOverview;
