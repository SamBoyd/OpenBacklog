import { useMemo } from 'react';
import { useQueries } from '@tanstack/react-query';
import { useThemePrioritization } from '#hooks/useThemePrioritization';
import { getStrategicInitiativesByTheme } from '#api/productStrategy';
import { ThemeDto } from '#api/productStrategy';
import { StrategicInitiativeDto } from '#types';

export interface ThemeWithInitiatives extends ThemeDto {
  strategicInitiatives: StrategicInitiativeDto[];
  isLoadingInitiatives: boolean;
}

/**
 * Custom hook that combines roadmap theme prioritization with strategic initiatives data
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing enriched theme data with strategic initiatives
 */
export function useRoadmapWithInitiatives(workspaceId: string) {
  const {
    prioritizedThemes,
    unprioritizedThemes,
    isLoading: isLoadingThemes,
    prioritizedError,
    unprioritizedError,
    prioritizeTheme,
    isPrioritizing,
    deprioritizeTheme,
    isDeprioritizing,
    reorderPrioritizedThemes,
    isReordering,
  } = useThemePrioritization(workspaceId);

  // Fetch strategic initiatives for all themes in parallel
  const allThemes = useMemo(
    () => [...prioritizedThemes, ...unprioritizedThemes],
    [prioritizedThemes, unprioritizedThemes]
  );

  const initiativeQueries = useQueries({
    queries: allThemes.map((theme) => ({
      queryKey: ['strategic-initiatives', 'theme', workspaceId, theme.id],
      queryFn: () => getStrategicInitiativesByTheme(workspaceId, theme.id),
      enabled: !!workspaceId && !!theme.id,
    })),
  });

  // Create a Map for O(1) theme ID to query index lookups (performance optimization)
  const themeIndexMap = useMemo(
    () => new Map(allThemes.map((theme, idx) => [theme.id, idx])),
    [allThemes]
  );

  // Extract stable query data to prevent unnecessary memoization recalculations
  // useQueries returns a new array reference on every render, so we need to derive
  // stable dependencies based on the actual data content
  const queryDataSnapshot = useMemo(
    () => initiativeQueries.map(q => ({
      data: q.data,
      isLoading: q.isLoading,
    })),
    // Only recalculate when the stringified data changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(initiativeQueries.map(q => ({ data: q.data, isLoading: q.isLoading })))]
  );

  // Enrich themes with their strategic initiatives
  const enrichThemes = useMemo(
    () => (themes: ThemeDto[]): ThemeWithInitiatives[] => {
      return themes.map((theme) => {
        const queryIndex = themeIndexMap.get(theme.id);
        const queryData = queryIndex !== undefined ? queryDataSnapshot[queryIndex] : undefined;
        return {
          ...theme,
          strategicInitiatives: queryData?.data || [],
          isLoadingInitiatives: queryData?.isLoading || false,
        };
      });
    },
    [themeIndexMap, queryDataSnapshot]
  );

  const prioritizedThemesWithInitiatives = useMemo(
    () => enrichThemes(prioritizedThemes),
    [prioritizedThemes, enrichThemes]
  );

  const unprioritizedThemesWithInitiatives = useMemo(
    () => enrichThemes(unprioritizedThemes),
    [unprioritizedThemes, enrichThemes]
  );

  const isLoadingAnyInitiatives = initiativeQueries.some((query) => query.isLoading);
  const error = prioritizedError || unprioritizedError;

  return {
    prioritizedThemes: prioritizedThemesWithInitiatives,
    unprioritizedThemes: unprioritizedThemesWithInitiatives,
    isLoading: isLoadingThemes,
    isLoadingInitiatives: isLoadingAnyInitiatives,
    error,
    prioritizeTheme,
    isPrioritizing,
    deprioritizeTheme,
    isDeprioritizing,
    reorderPrioritizedThemes,
    isReordering,
  };
}
