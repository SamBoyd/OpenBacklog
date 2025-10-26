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

  // Enrich themes with their strategic initiatives
  const enrichThemes = (themes: ThemeDto[]): ThemeWithInitiatives[] => {
    return themes.map((theme, index) => {
      const queryResult = initiativeQueries[allThemes.findIndex((t) => t.id === theme.id)];
      return {
        ...theme,
        strategicInitiatives: queryResult?.data || [],
        isLoadingInitiatives: queryResult?.isLoading || false,
      };
    });
  };

  const prioritizedThemesWithInitiatives = useMemo(
    () => enrichThemes(prioritizedThemes),
    [prioritizedThemes, initiativeQueries]
  );

  const unprioritizedThemesWithInitiatives = useMemo(
    () => enrichThemes(unprioritizedThemes),
    [unprioritizedThemes, initiativeQueries]
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
