import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRoadmapThemeById, ThemeDto, HeroRef, VillainRef } from '#api/productStrategy';

/**
 * Custom hook for fetching a single roadmap theme by ID with embedded heroes and villains.
 * @param {string} workspaceId - The workspace ID
 * @param {string} themeId - The theme ID
 * @returns {object} Object containing theme data with extracted heroes/villains, loading state, error, and refetch function
 */
export function useRoadmapThemeById(workspaceId: string, themeId: string) {
  const {
    data: theme,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['roadmap-theme', workspaceId, themeId],
    queryFn: () => getRoadmapThemeById(workspaceId, themeId),
    enabled: !!workspaceId && !!themeId,
  });

  // Extract heroes and villains from theme for easier consumption
  const heroes = useMemo<HeroRef[]>(() => {
    return theme?.heroes || [];
  }, [theme]);

  const villains = useMemo<VillainRef[]>(() => {
    return theme?.villains || [];
  }, [theme]);

  return {
    theme: theme || null,
    heroes,
    villains,
    isLoading,
    error,
    refetch,
  };
}
