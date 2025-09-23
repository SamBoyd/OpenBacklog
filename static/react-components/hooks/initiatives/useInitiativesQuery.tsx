import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { InitiativeDto, ContextType, EntityType } from '#types';
import { getAllInitiatives, getInitiativeById } from '#api/initiatives';
import { useOrderings, OrderedEntity } from '#hooks/useOrderings';
import { InitiativeFilters, InitiativesQueryResult } from './types';

/**
 * Hook for fetching and managing initiatives data
 * @param {InitiativeFilters} [filters] - Optional filters for initiatives
 * @param {number} [cacheVersion] - External cache version for reactivity
 * @returns {InitiativesQueryResult} Query result with data and loading states
 */
export function useInitiativesQuery(filters?: InitiativeFilters, cacheVersion?: number): InitiativesQueryResult {
  const queryClient = useQueryClient();

  // Build query key including filters
  const queryKey = useMemo(() => ['initiatives', filters ?? {}], [filters]);

  const {
    data: rawData,
    isLoading: queryIsLoading,
    isFetching: queryIsFetching,
    isError: queryIsError,
    error: queryError,
    refetch: reloadInitiatives,
  } = useQuery<InitiativeDto | InitiativeDto[], Error>({
    queryKey,
    queryFn: async () => {
      if (filters?.id) {
        // Fetch single initiative by ID
        return getInitiativeById(filters.id);
      }
      // Fetch all initiatives, passing filters to the API function
      const initiatives = await getAllInitiatives(filters);
      return initiatives;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Adjust data derivation based on filters
  const rawInitiativesData = useMemo(() => {
    if (filters?.id && rawData && !Array.isArray(rawData)) {
      return [rawData];
    }
    return (rawData as InitiativeDto[] | undefined);
  }, [filters?.id, rawData]);

  // Create reactive data source that immediately reflects cache updates
  const currentInitiativesData = useMemo(() => {
    // Get the latest data from cache, fallback to rawData
    const latestData = queryClient.getQueryData<InitiativeDto[]>(queryKey);
    if (latestData) {
      // Apply the same filtering logic as rawInitiativesData
      return filters?.id && !Array.isArray(latestData) ? [latestData] : latestData;
    }
    return rawInitiativesData;
  }, [rawInitiativesData, cacheVersion, queryClient, queryKey, filters?.id]);

  // Use ordering hook to get properly ordered entities
  const { orderedEntities } = useOrderings<InitiativeDto>({
    contextType: ContextType.STATUS_LIST,
    entityType: EntityType.INITIATIVE,
    contextId: null,
    entitiesToOrder: currentInitiativesData ?? [],
    orderDirection: 'asc'
  });

  // Use ordered entities as the main initiativesData array
  const initiativesData = orderedEntities.length > 0 ? orderedEntities : null;

  // Create error message
  const error: string | null = queryError
    ? `Error loading ${filters?.id ? 'initiative' : 'initiatives'}`
    : null;

  return {
    initiativesData,
    error,
    shouldShowSkeleton: queryIsLoading && !initiativesData,
    isQueryFetching: queryIsFetching,
    reloadInitiatives,
  };
}

/**
 * Expose cache version setter for use by cache management hook
 */
export function useInitiativesQueryCacheVersion() {
  return useState(0);
}