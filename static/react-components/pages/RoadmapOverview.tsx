import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router';

import { RoadmapHeader } from '#components/strategyAndRoadmap/RoadmapHeader';
import { RoadmapFilterControls } from '#components/strategyAndRoadmap/RoadmapFilterControls';
import { RoadmapListView } from '#components/strategyAndRoadmap/RoadmapListView';
import { RoadmapSummaryPanel } from '#components/strategyAndRoadmap/RoadmapSummaryPanel';
import { useRoadmapThemes } from '#hooks/strategyAndRoadmap/useRoadmapThemes';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useHeroes } from '#hooks/useHeroes';
import { useVillains } from '#hooks/useVillains';
import { RoadmapCalendarView } from '#components/strategyAndRoadmap/RoadmapCalendarView';
import { RoadmapTimelineView } from '#components/strategyAndRoadmap/RoadmapTimelineView';
import { ThemeDto, HeroRef, VillainRef } from '#api/productStrategy';

/**
 * Filters themes based on selected hero and villain IDs.
 * A theme is included if it has at least one of the selected heroes
 * AND at least one of the selected villains (when filters are active).
 * If no heroes/villains are selected for a filter, that filter is ignored.
 *
 * @param themes - The themes to filter
 * @param selectedHeroIds - Selected hero IDs (empty means no filter)
 * @param selectedVillainIds - Selected villain IDs (empty means no filter)
 * @returns Filtered themes
 */
function filterThemes(
  themes: ThemeDto[],
  selectedHeroIds: string[],
  selectedVillainIds: string[]
): ThemeDto[] {
  return themes.filter((theme) => {
    const matchesHeroFilter =
      selectedHeroIds.length === 0 ||
      theme.hero_ids?.some((heroId) => selectedHeroIds.includes(heroId));

    const matchesVillainFilter =
      selectedVillainIds.length === 0 ||
      theme.villain_ids?.some((villainId) => selectedVillainIds.includes(villainId));

    return matchesHeroFilter && matchesVillainFilter;
  });
}

/**
 * Roadmap Overview page displays roadmap themes organized by prioritization status.
 * Users can view prioritized themes (active roadmap, max 5) and unprioritized themes (backlog),
 * with narrative context including heroes and villains. Supports list, timeline, and calendar views.
 */
export function RoadmapOverview() {
  const navigate = useNavigate();
  const { currentWorkspace } = useWorkspaces();
  const workspaceId = currentWorkspace?.id || '';

  const {
    prioritizedThemes,
    unprioritizedThemes,
    isLoading: isLoadingThemes,
  } = useRoadmapThemes(workspaceId);

  const { heroes = [], isLoading: isLoadingHeroes } = useHeroes(workspaceId);
  const { villains = [], isLoading: isLoadingVillains } = useVillains(workspaceId);

  const [currentView, setCurrentView] = useState<'timeline' | 'list' | 'calendar'>('list');
  const [selectedHeroIds, setSelectedHeroIds] = useState<string[]>([]);
  const [selectedVillainIds, setSelectedVillainIds] = useState<string[]>([]);

  const isLoading = isLoadingThemes || isLoadingHeroes || isLoadingVillains;

  const heroRefs: HeroRef[] = useMemo(
    () =>
      heroes.map((hero) => ({
        id: hero.id,
        name: hero.name,
        identifier: hero.identifier,
        description: hero.description,
        is_primary: hero.is_primary,
      })),
    [heroes]
  );

  const villainRefs: VillainRef[] = useMemo(
    () =>
      villains.map((villain) => ({
        id: villain.id,
        name: villain.name,
        identifier: villain.identifier,
        description: villain.description || '',
        villain_type: villain.villain_type,
        severity: villain.severity,
        is_defeated: villain.is_defeated,
      })),
    [villains]
  );

  const filteredPrioritizedThemes = useMemo(
    () => filterThemes(prioritizedThemes, selectedHeroIds, selectedVillainIds),
    [prioritizedThemes, selectedHeroIds, selectedVillainIds]
  );

  const filteredUnprioritizedThemes = useMemo(
    () => filterThemes(unprioritizedThemes, selectedHeroIds, selectedVillainIds),
    [unprioritizedThemes, selectedHeroIds, selectedVillainIds]
  );

  const allFilteredThemes = useMemo(
    () => [...filteredPrioritizedThemes, ...filteredUnprioritizedThemes],
    [filteredPrioritizedThemes, filteredUnprioritizedThemes]
  );

  const handleViewTheme = (themeId: string) => {
    navigate(`/workspace/story-bible/theme/${themeId}`);
  };

  const handleViewInitiatives = (themeId: string) => {
    navigate(`/workspace/story-bible/theme/${themeId}`);
  };

  const handleThemeMoreOptions = (themeId: string) => {
    console.log('More Options for Theme:', themeId);
  };

  const handleViewAllHeroes = () => {
    navigate(`/workspace/story-bible?tab=heroes`);
  };

  const handleViewAllVillains = () => {
    navigate(`/workspace/story-bible?tab=villains`);
  };

  const handleRunConsistencyCheck = () => {
    console.log('Run Consistency Check');
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
        heroes={heroRefs}
        villains={villainRefs}
        selectedHeroIds={selectedHeroIds}
        selectedVillainIds={selectedVillainIds}
        onHeroFilterChange={setSelectedHeroIds}
        onVillainFilterChange={setSelectedVillainIds}
        onZoomChange={(zoom) => console.log('Zoom changed to:', zoom)}
      />

      {/* Main Content - List View */}
      {currentView === 'list' && (
        <div className="flex-1 overflow-y-auto">
          <RoadmapListView
            prioritizedThemes={filteredPrioritizedThemes}
            unprioritizedThemes={filteredUnprioritizedThemes}
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
            themes={allFilteredThemes}
            isLoading={isLoading}
            onViewTheme={handleViewTheme}
            onViewInitiatives={handleViewInitiatives}
          />
        </div>
      )}

      {currentView === 'calendar' && (
        <div className="flex-1 overflow-y-auto">
          <RoadmapCalendarView
            themes={allFilteredThemes}
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
