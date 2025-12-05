import { useMemo } from 'react';
import { useThemePrioritization } from '#hooks/useThemePrioritization';
import { useHeroes } from '#hooks/useHeroes';
import { useVillains } from '#hooks/useVillains';
import { useProductOutcomes } from '#hooks/useProductOutcomes';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { ThemeDto } from '#api/productStrategy';

/**
 * Custom hook for fetching and combining story arc data for the roadmap overview.
 * Transforms prioritized and unprioritized themes into arcs by mapping hero_ids
 * and villain_ids to full objects.
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing prioritized/unprioritized arcs, loading state, and error
 */
export function  useRoadmapThemes(workspaceId: string) {
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

  const {
    outcomes = [],
    isLoading: isLoadingOutcomes,
    error: outcomesError,
  } = useProductOutcomes(workspaceId);

  const {
    pillars = [],
    isLoading: isLoadingPillars,
    error: pillarsError,
  } = useStrategicPillars(workspaceId);

  // Helper function to enrich themes with heroes/villains/outcomes/pillars
  const enrichThemesWithNarratives = (themes: ThemeDto[]): ThemeDto[] => {
    const heroMap = new Map(heroes.map((h) => [h.id, h]));
    const villainMap = new Map(villains.map((v) => [v.id, v]));
    const outcomeMap = new Map(outcomes.map((o) => [o.id, o]));
    const pillarMap = new Map(pillars.map((p) => [p.id, p]));

    return themes.map((theme) => {
      const themeHeroes = theme.hero_ids
        .map((heroId) => heroMap.get(heroId))
        .filter((hero) => hero !== undefined) as typeof heroes;

      const themeVillains = theme.villain_ids
        .map((villainId) => villainMap.get(villainId))
        .filter((villain) => villain !== undefined) as typeof villains;

      const themeOutcomes = theme.outcome_ids
        .map((outcomeId) => outcomeMap.get(outcomeId))
        .filter((outcome) => outcome !== undefined) as typeof outcomes;

      // Derive unique pillars from theme outcomes
      const derivedPillarIds = new Set<string>();
      themeOutcomes.forEach((outcome) => {
        outcome.pillar_ids?.forEach((pillarId) => derivedPillarIds.add(pillarId));
      });

      const themePillars = Array.from(derivedPillarIds)
        .map((pillarId) => pillarMap.get(pillarId))
        .filter((pillar) => pillar !== undefined) as typeof pillars;

      return {
        ...theme,
        heroes: themeHeroes,
        villains: themeVillains,
        outcomes: themeOutcomes,
        pillars: themePillars,
      };
    });
  };

  const prioritizedThemesWithNarratives = useMemo(
    () => enrichThemesWithNarratives(prioritizedThemes),
    [prioritizedThemes, heroes, villains, outcomes, pillars]
  );

  const unprioritizedThemesWithNarratives = useMemo(
    () => enrichThemesWithNarratives(unprioritizedThemes),
    [unprioritizedThemes, heroes, villains, outcomes, pillars]
  );

  return {
    prioritizedThemes: prioritizedThemesWithNarratives,
    unprioritizedThemes: unprioritizedThemesWithNarratives,
    isLoadingPrioritized,
    isLoadingUnprioritized,
    isLoading: isLoadingPrioritized || isLoadingUnprioritized || isLoadingHeroes || isLoadingVillains || isLoadingOutcomes || isLoadingPillars,
    error: prioritizedError || unprioritizedError || heroesError || villainsError || outcomesError || pillarsError,
  };
}
