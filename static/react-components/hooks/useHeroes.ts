import { useQuery } from '@tanstack/react-query';
import { getAllHeroes, getHeroById, getHeroByIdentifier } from '#api/heroes';
import { HeroDto } from '#types';

/**
 * Filter options for heroes query.
 */
export interface HeroFilters {
  isPrimary?: boolean;
}

/**
 * Custom hook for fetching all heroes for a workspace with optional filtering.
 * @param {string} workspaceId - The workspace ID
 * @param {HeroFilters} [filters] - Optional filters for the heroes query
 * @returns {object} Object containing heroes data, loading state, error, and refetch function
 */
export function useHeroes(workspaceId: string, filters?: HeroFilters) {
  const {
    data: heroes,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['heroes', workspaceId, filters],
    queryFn: async () => {
      const allHeroes = await getAllHeroes(workspaceId);

      // Apply filters if provided
      if (filters?.isPrimary !== undefined) {
        return allHeroes.filter(hero => hero.is_primary === filters.isPrimary);
      }

      return allHeroes;
    },
    enabled: !!workspaceId,
  });

  return {
    heroes: heroes || [],
    isLoading,
    error,
    refetch,
  };
}

/**
 * Custom hook for fetching a single hero by ID.
 * @param {string} heroId - The hero ID
 * @returns {object} Object containing hero data, loading state, error, and refetch function
 */
export function useHeroById(heroId: string) {
  const {
    data: hero,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['hero', heroId],
    queryFn: () => getHeroById(heroId),
    enabled: !!heroId,
  });

  return {
    hero: hero || null,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Custom hook for fetching a single hero by identifier (e.g., "H-2003").
 * @param {string} identifier - The hero identifier
 * @returns {object} Object containing hero data, loading state, error, and refetch function
 */
export function useHeroByIdentifier(identifier: string) {
  const {
    data: hero,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['hero', 'identifier', identifier],
    queryFn: () => getHeroByIdentifier(identifier),
    enabled: !!identifier,
  });

  return {
    hero: hero || null,
    isLoading,
    error,
    refetch,
  };
}
