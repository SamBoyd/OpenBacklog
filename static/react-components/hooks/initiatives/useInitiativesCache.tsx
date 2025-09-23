import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { InitiativeDto, InitiativeStatus, EntityType } from '#types';
import { InitiativesCacheOperations, InitiativeFilters } from './types';

/**
 * Hook for managing initiatives cache operations
 * @param {InitiativeFilters} [filters] - Current filters for building query keys
 * @param {Function} setCacheVersion - Function to increment cache version for reactivity
 * @returns {InitiativesCacheOperations} Cache management operations
 */
export function useInitiativesCache(
  filters?: InitiativeFilters,
  setCacheVersion?: (fn: (prev: number) => number) => void
): InitiativesCacheOperations {
  const queryClient = useQueryClient();

  // Build the main query key
  const queryKey = ['initiatives', filters ?? {}];

  /**
   * Invalidates the cache for a specific initiative by ID.
   * @param {string} initiativeId - The ID of the initiative to invalidate.
   */
  const invalidateInitiative = useCallback((initiativeId: string) => {
    queryClient.invalidateQueries({ queryKey: ['initiatives', { id: initiativeId }] });
  }, [queryClient]);

  /**
   * Invalidates the cache for all initiatives.
   */
  const invalidateAllInitiatives = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['initiatives'] });
  }, [queryClient]);

  /**
   * Invalidates the cache for initiatives with specific status(es).
   * @param {InitiativeStatus | InitiativeStatus[]} status - The status(es) to invalidate.
   */
  const invalidateInitiativesByStatus = useCallback((status: InitiativeStatus | InitiativeStatus[]) => {
    const statuses = Array.isArray(status) ? status : [status];
    queryClient.invalidateQueries({
      queryKey: ['initiatives'],
      predicate: (query) => {
        // Check if the query has filters with status
        const filters = query.queryKey[1] as { status?: string[] } | undefined;
        if (!filters?.status) return false;

        // Check if any of the statuses match
        return statuses.some(s => filters.status?.includes(s));
      }
    });
  }, [queryClient]);

  /**
   * Helper function to update initiative data in all relevant cache entries
   * @param {InitiativeDto} updatedInitiative - The updated initiative data
   * @param {string} [oldStatus] - The previous status if changed (for status-based cache updates)
   */
  const updateInitiativeInCache = useCallback((updatedInitiative: InitiativeDto, oldStatus?: string) => {
    // Update the specific initiative cache
    queryClient.setQueryData<InitiativeDto>(['initiatives', { id: updatedInitiative.id }], updatedInitiative);

    // Update the general initiatives query data
    queryClient.setQueryData<InitiativeDto[]>(['initiatives', {}], (oldData) => {
      if (!oldData) return oldData;
      return oldData.map(item =>
        item.id === updatedInitiative.id ? { ...item, ...updatedInitiative } : item
      );
    });

    // Handle status-based cache updates if status changed
    if (oldStatus && oldStatus !== updatedInitiative.status) {
      // Add to new status list
      queryClient.setQueryData<InitiativeDto[]>(['initiatives', { status: [updatedInitiative.status] }], (oldData) => {
        if (!oldData) return oldData;
        const existingItem = oldData.find(item => item.id === updatedInitiative.id);
        if (existingItem) {
          return oldData.map(item =>
            item.id === updatedInitiative.id ? { ...item, ...updatedInitiative } : item
          );
        } else {
          return [...oldData, updatedInitiative];
        }
      });

      // Remove from old status list
      queryClient.setQueryData<InitiativeDto[]>(['initiatives', { status: [oldStatus] }], (oldData) => {
        if (!oldData) return oldData;
        return oldData.filter(item => item.id !== updatedInitiative.id);
      });
    }

    // Increment cache version to trigger reactive data updates
    setCacheVersion?.(prev => prev + 1);
  }, [queryClient, setCacheVersion]);

  return {
    invalidateInitiative,
    invalidateAllInitiatives,
    invalidateInitiativesByStatus,
    updateInitiativeInCache,
  };
}