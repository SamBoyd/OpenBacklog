import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ConflictDto, ConflictStatus } from '#types';
import { getAllConflicts, getConflictById, ConflictFilters } from '#api/conflicts';

/**
 * Interface for conflict query filters.
 */
export interface UseConflictsFilters extends ConflictFilters {
    id?: string; // For fetching a single conflict
}

/**
 * Interface for conflict query result.
 */
export interface UseConflictsResult {
    conflicts: ConflictDto[] | null;
    error: string | null;
    isLoading: boolean;
    isFetching: boolean;
    refetch: () => void;
}

/**
 * Hook for fetching and managing conflicts data with React Query.
 * @param {UseConflictsFilters} [filters] - Optional filters for conflicts
 * @returns {UseConflictsResult} Query result with data and loading states
 */
export function useConflicts(filters?: UseConflictsFilters): UseConflictsResult {
    // Build query key including filters for proper cache management
    const queryKey = useMemo(() => ['conflicts', filters ?? {}], [filters]);

    const {
        data: rawData,
        isLoading,
        isFetching,
        isError,
        error: queryError,
        refetch,
    } = useQuery<ConflictDto | ConflictDto[], Error>({
        queryKey,
        queryFn: async () => {
            if (filters?.id) {
                // Fetch single conflict by ID
                return getConflictById(filters.id);
            }
            // Fetch all conflicts with optional filters
            return getAllConflicts(filters);
        },
        staleTime: 1000 * 60 * 5, // 5 minutes
    });

    // Normalize data to always be an array
    const conflicts = useMemo(() => {
        if (filters?.id && rawData && !Array.isArray(rawData)) {
            return [rawData];
        }
        return (rawData as ConflictDto[] | undefined) ?? null;
    }, [filters?.id, rawData]);

    // Create error message
    const error: string | null = queryError
        ? `Error loading ${filters?.id ? 'conflict' : 'conflicts'}`
        : null;

    return {
        conflicts,
        error,
        isLoading,
        isFetching,
        refetch,
    };
}

/**
 * Hook for fetching conflicts filtered by status.
 * @param {ConflictStatus | ConflictStatus[]} status - Status or array of statuses to filter by
 * @returns {UseConflictsResult} Query result with data and loading states
 */
export function useConflictsByStatus(
    status: ConflictStatus | ConflictStatus[]
): UseConflictsResult {
    return useConflicts({ status });
}

/**
 * Hook for fetching conflicts for a specific hero.
 * @param {string} heroId - UUID of the hero
 * @returns {UseConflictsResult} Query result with data and loading states
 */
export function useConflictsByHero(heroId: string): UseConflictsResult {
    return useConflicts({ heroId });
}

/**
 * Hook for fetching conflicts for a specific villain.
 * @param {string} villainId - UUID of the villain
 * @returns {UseConflictsResult} Query result with data and loading states
 */
export function useConflictsByVillain(villainId: string): UseConflictsResult {
    return useConflicts({ villainId });
}

/**
 * Hook for fetching a single conflict by ID.
 * @param {string} conflictId - UUID of the conflict
 * @returns {UseConflictsResult} Query result with data and loading states
 */
export function useConflictById(conflictId: string): UseConflictsResult {
    return useConflicts({ id: conflictId });
}
