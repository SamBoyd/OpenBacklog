import { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes';
import { useHeroes } from '#hooks/useHeroes';
import { useVillains } from '#hooks/useVillains';
import { ArcDto } from '#api/productStrategy';

/**
 * Custom hook for fetching and combining story arc data for the roadmap overview.
 * Combines themes (arcs), heroes, and villains into enriched arc objects.
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing arcs data, loading state, error, and refetch function
 */
export function useStoryArcs(workspaceId: string) {
  const {
    themes = [],
    isLoading: isLoadingThemes,
    error: themesError,
  } = useRoadmapThemes(workspaceId);

  const {
    heroes = [],
    isLoading: isLoadingHeroes,
    error: heroesError,
  } = useHeroes(workspaceId);

  const {
    villains = [],
    isLoading: isLoadingVillains,
    error: villainsError,
  } = useVillains(workspaceId);

  // Combine themes with mock arc data
  const arcs = useMemo(() => {
    return themes.map((theme) => {
      const arc: ArcDto = {
        ...theme,
        heroes: heroes.slice(0, 2), // Mock: assign first 2 heroes
        villains: villains.slice(0, 2), // Mock: assign first 2 villains
        status: ['in_progress', 'complete', 'planned'][
          Math.floor(Math.random() * 3)
        ] as 'in_progress' | 'complete' | 'planned',
        progress_percentage:
          Math.floor(Math.random() * 100) + 1,
        scenes_completed: Math.floor(Math.random() * 28) + 1,
        scenes_total: 28,
        started_quarter: 'Q1 2024',
        expected_quarter: 'Q2 2024',
      };
      return arc;
    });
  }, [themes, heroes, villains]);

  return {
    arcs,
    isLoading: isLoadingThemes || isLoadingHeroes || isLoadingVillains,
    error: themesError || heroesError || villainsError,
  };
}
