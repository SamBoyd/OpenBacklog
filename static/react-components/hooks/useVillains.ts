import { useQuery } from '@tanstack/react-query';
import { getAllVillains, getVillainById, getVillainByIdentifier } from '#api/villains';
import { VillainDto, VillainType } from '#types';

/**
 * Filter options for villains query.
 */
export interface VillainFilters {
  isDefeated?: boolean;
  villainType?: VillainType;
  minSeverity?: number;
}

/**
 * Custom hook for fetching all villains for a workspace with optional filtering.
 * @param {string} workspaceId - The workspace ID
 * @param {VillainFilters} [filters] - Optional filters for the villains query
 * @returns {object} Object containing villains data, loading state, error, and refetch function
 */
export function useVillains(workspaceId: string, filters?: VillainFilters) {
  const {
    data: villains,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['villains', workspaceId, filters],
    queryFn: async () => {
      const allVillains = await getAllVillains(workspaceId);

      // Apply filters if provided
      let filteredVillains = allVillains;

      if (filters?.isDefeated !== undefined) {
        filteredVillains = filteredVillains.filter(villain => villain.is_defeated === filters.isDefeated);
      }

      if (filters?.villainType !== undefined) {
        filteredVillains = filteredVillains.filter(villain => villain.villain_type === filters.villainType);
      }

      if (filters?.minSeverity !== undefined) {
        const minSeverity = filters.minSeverity;
        filteredVillains = filteredVillains.filter(villain => villain.severity >= minSeverity);
      }

      return filteredVillains;
    },
    enabled: !!workspaceId,
  });

  return {
    villains: villains || [],
    isLoading,
    error,
    refetch,
  };
}

/**
 * Custom hook for fetching a single villain by ID.
 * @param {string} villainId - The villain ID
 * @returns {object} Object containing villain data, loading state, error, and refetch function
 */
export function useVillainById(villainId: string) {
  const {
    data: villain,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['villain', villainId],
    queryFn: () => getVillainById(villainId),
    enabled: !!villainId,
  });

  return {
    villain: villain || null,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Custom hook for fetching a single villain by identifier (e.g., "V-2003").
 * @param {string} identifier - The villain identifier
 * @returns {object} Object containing villain data, loading state, error, and refetch function
 */
export function useVillainByIdentifier(identifier: string) {
  const {
    data: villain,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['villain', 'identifier', identifier],
    queryFn: () => getVillainByIdentifier(identifier),
    enabled: !!identifier,
  });

  return {
    villain: villain || null,
    isLoading,
    error,
    refetch,
  };
}
