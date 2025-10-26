import { useQuery } from '@tanstack/react-query';
import { getStrategicInitiativesByTheme } from '#api/productStrategy';
import { StrategicInitiativeDto } from '#types';

/**
 * Custom hook for fetching strategic initiatives for a specific theme
 * @param {string} workspaceId - The workspace ID
 * @param {string} themeId - The theme ID to filter by
 * @returns {object} Object containing strategic initiatives data, loading state, and error
 */
export function useStrategicInitiativesByTheme(workspaceId: string, themeId: string) {
  const {
    data: strategicInitiatives,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['strategic-initiatives', 'theme', workspaceId, themeId],
    queryFn: () => getStrategicInitiativesByTheme(workspaceId, themeId),
    enabled: !!workspaceId && !!themeId,
  });

  return {
    strategicInitiatives: strategicInitiatives || [],
    isLoading,
    error,
  };
}
