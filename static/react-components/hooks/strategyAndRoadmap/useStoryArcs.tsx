import { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes';
import { useHeroes } from '#hooks/useHeroes';
import { useVillains } from '#hooks/useVillains';
import { ArcDto } from '#api/productStrategy';

/**
 * Custom hook for fetching and combining story arc data for the roadmap overview.
 * Transforms themes into arcs by mapping hero_ids and villain_ids to full objects,
 * and adding arc-specific metadata (status, progress, quarters).
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing arcs data, loading state, and error
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

  // Transform themes into arcs with hero/villain lookups
  const arcs = useMemo(() => {
    // Create lookup maps for heroes and villains by ID
    const heroMap = new Map(heroes.map((h) => [h.id, h]));
    const villainMap = new Map(villains.map((v) => [v.id, v]));

    return themes.map((theme) => {
      // Map hero_ids to full hero objects
      const themeHeroes = theme.hero_ids
        .map((heroId) => heroMap.get(heroId))
        .filter(
          (hero) => hero !== undefined
        ) as typeof heroes;

      // Map villain_ids to full villain objects
      const themeVillains = theme.villain_ids
        .map((villainId) => villainMap.get(villainId))
        .filter(
          (villain) => villain !== undefined
        ) as typeof villains;

      const arc: ArcDto = {
        ...theme,
        heroes: themeHeroes,
        villains: themeVillains,
        status: ['in_progress', 'complete', 'planned'][
          Math.floor(Math.random() * 3)
        ] as 'in_progress' | 'complete' | 'planned',
        progress_percentage: Math.floor(Math.random() * 100) + 1,
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
