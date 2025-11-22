import React from 'react';
import { RoadmapHeader } from '#components/strategyAndRoadmap/RoadmapHeader';
import { RoadmapFilterControls } from '#components/strategyAndRoadmap/RoadmapFilterControls';
import { RoadmapListView } from '#components/strategyAndRoadmap/RoadmapListView';
import { RoadmapSummaryPanel } from '#components/strategyAndRoadmap/RoadmapSummaryPanel';
import { useStoryArcs } from '#hooks/strategyAndRoadmap/useStoryArcs';
import { useWorkspaces } from '#hooks/useWorkspaces';

/**
 * Roadmap Overview page displays a strategic narrative timeline of roadmap themes (arcs)
 * organized by quarter. Users can view arcs grouped by time period, filter by narrative
 * elements (heroes, villains, themes, status), and see overall roadmap statistics.
 */
export function RoadmapOverview() {
  const { currentWorkspace } = useWorkspaces();
  const { arcs, isLoading } = useStoryArcs(currentWorkspace?.id || '');

  const handleViewArc = (arcId: string) => {
    console.log('View Arc:', arcId);
    // TODO: Navigate to arc detail view
  };

  const handleViewBeats = (arcId: string) => {
    console.log('View Beats/Retrospective:', arcId);
    // TODO: Navigate to beats view
  };

  const handleEditArc = (arcId: string) => {
    console.log('Edit Arc:', arcId);
    // TODO: Navigate to arc edit view
  };

  const handleArcMoreOptions = (arcId: string) => {
    console.log('More Options for Arc:', arcId);
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
    <div className="h-full flex flex-col bg-neutral-50">
      {/* Page Header */}
      <RoadmapHeader
        workspaceName="Workspace Name"
        onViewToggle={(view) => console.log('View changed to:', view)}
      />

      {/* Filter Controls */}
      <RoadmapFilterControls
        onZoomChange={(zoom) => console.log('Zoom changed to:', zoom)}
      />

      {/* Main Content - List View */}
      <div className="flex-1 overflow-y-auto">
        <RoadmapListView
          arcs={arcs}
          isLoading={isLoading}
          onViewArc={handleViewArc}
          onViewBeats={handleViewBeats}
          onEdit={handleEditArc}
          onMoreOptions={handleArcMoreOptions}
        />
      </div>

      {/* Summary Panel */}
      <RoadmapSummaryPanel
        arcs={arcs}
        onViewAllHeroes={handleViewAllHeroes}
        onViewAllVillains={handleViewAllVillains}
        onRunConsistencyCheck={handleRunConsistencyCheck}
      />
    </div>
  );
}

export default RoadmapOverview;
