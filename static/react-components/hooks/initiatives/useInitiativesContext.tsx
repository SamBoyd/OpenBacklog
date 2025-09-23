import { useMemo } from 'react';
import { useInitiativesQuery, useInitiativesQueryCacheVersion } from './useInitiativesQuery';
import { useInitiativesCache } from './useInitiativesCache';
import { useInitiativesMutations } from './useInitiativesMutations';
import { InitiativesContextType, InitiativeFilters } from './types';

/**
 * Main composition hook that combines all initiatives functionality
 * @param {InitiativeFilters} [filters] - Optional filters for initiatives
 * @returns {InitiativesContextType} Complete initiatives context interface
 */
export function useInitiativesContext(filters?: InitiativeFilters): InitiativesContextType {
  // Cache version management for reactive updates
  const [cacheVersion, setCacheVersion] = useInitiativesQueryCacheVersion();

  // Data fetching hook
  const queryResult = useInitiativesQuery(filters, cacheVersion);

  // Cache management hook
  const cacheOperations = useInitiativesCache(filters, setCacheVersion);

  // Mutations hook
  const mutationOperations = useInitiativesMutations(
    cacheOperations.updateInitiativeInCache,
    filters,
    setCacheVersion,
    queryResult.reloadInitiatives
  );

  // Combine all operations into the complete context interface
  const value: InitiativesContextType = useMemo(() => ({
    // From query hook
    ...queryResult,

    // From cache hook
    ...cacheOperations,

    // From mutations hook
    ...mutationOperations,
  }), [
    queryResult,
    cacheOperations,
    mutationOperations,
  ]);

  return value;
}