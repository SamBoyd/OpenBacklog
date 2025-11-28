import { useMemo } from 'react';
import { useThemePrioritization } from '#hooks/useThemePrioritization';
import { useHeroes } from '#hooks/useHeroes';
import { useVillains } from '#hooks/useVillains';
import { ArcDto, ThemeDto } from '#api/productStrategy';

/**
 * Custom hook for fetching and combining story arc data for the roadmap overview.
 * Transforms prioritized and unprioritized themes into arcs by mapping hero_ids
 * and villain_ids to full objects.
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing prioritized/unprioritized arcs, loading state, and error
 */
export function useStoryArcs(workspaceId: string) {
  const {
    prioritizedThemes = [],
    unprioritizedThemes = [],
    isLoadingPrioritized,
    isLoadingUnprioritized,
    prioritizedError,
    unprioritizedError,
  } = useThemePrioritization(workspaceId);

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

  // Helper function to enrich themes with heroes/villains
  const enrichThemesWithNarratives = (themes: ThemeDto[]): ArcDto[] => {
    const heroMap = new Map(heroes.map((h) => [h.id, h]));
    const villainMap = new Map(villains.map((v) => [v.id, v]));

    return themes.map((theme) => {
      const themeHeroes = theme.hero_ids
        .map((heroId) => heroMap.get(heroId))
        .filter((hero) => hero !== undefined) as typeof heroes;

      const themeVillains = theme.villain_ids
        .map((villainId) => villainMap.get(villainId))
        .filter((villain) => villain !== undefined) as typeof villains;

      return {
        ...theme,
        heroes: themeHeroes,
        villains: themeVillains,
      };
    });
  };

  const prioritizedArcs = useMemo(
    () => enrichThemesWithNarratives(prioritizedThemes),
    [prioritizedThemes, heroes, villains]
  );

  const unprioritizedArcs = useMemo(
    () => enrichThemesWithNarratives(unprioritizedThemes),
    [unprioritizedThemes, heroes, villains]
  );

  return {
    prioritizedArcs,
    unprioritizedArcs,
    isLoadingPrioritized,
    isLoadingUnprioritized,
    isLoading: isLoadingPrioritized || isLoadingUnprioritized || isLoadingHeroes || isLoadingVillains,
    error: prioritizedError || unprioritizedError || heroesError || villainsError,
  };
}
