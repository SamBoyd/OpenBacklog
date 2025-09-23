import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { useInitiativesContext } from './useInitiativesContext';
import { InitiativeDto, InitiativeStatus } from '#types';
import { InitiativeFilters } from './types';

// Mock all sub-hooks
const mockQueryResult = {
    initiativesData: [],
    error: null,
    shouldShowSkeleton: false,
    isQueryFetching: false,
    reloadInitiatives: vi.fn(),
};

const mockCacheOperations = {
    invalidateInitiative: vi.fn(),
    invalidateAllInitiatives: vi.fn(),
    invalidateInitiativesByStatus: vi.fn(),
    updateInitiativeInCache: vi.fn(),
};

const mockMutationOperations = {
    isCreatingInitiative: false,
    isUpdatingInitiative: false,
    isDeletingInitiative: false,
    isBatchUpdatingInitiatives: false,
    isDeletingTask: false,
    isDeletingChecklistItem: false,
    createInitiative: vi.fn(),
    updateInitiative: vi.fn(),
    updateInitiatives: vi.fn(),
    deleteInitiative: vi.fn(),
    deleteTask: vi.fn(),
    deleteChecklistItem: vi.fn(),
    reorderInitiative: vi.fn(),
    moveInitiativeToStatus: vi.fn(),
    moveInitiativeInGroup: vi.fn(),
};

// Mock the sub-hooks
vi.mock('./useInitiativesQuery', () => ({
    useInitiativesQuery: vi.fn(() => mockQueryResult),
}));

vi.mock('./useInitiativesCache', () => ({
    useInitiativesCache: vi.fn(() => mockCacheOperations),
}));

vi.mock('./useInitiativesMutations', () => ({
    useInitiativesMutations: vi.fn(() => mockMutationOperations),
}));

// Mock useInitiativesQueryCacheVersion
const mockCacheVersion = 1;
const mockSetCacheVersion = vi.fn();
vi.mock('./useInitiativesQuery', () => ({
    useInitiativesQuery: vi.fn(() => mockQueryResult),
    useInitiativesQueryCacheVersion: vi.fn(() => [mockCacheVersion, mockSetCacheVersion]),
}));

// Import mocked modules
import { useInitiativesQuery, useInitiativesQueryCacheVersion } from './useInitiativesQuery';
import { useInitiativesCache } from './useInitiativesCache';
import { useInitiativesMutations } from './useInitiativesMutations';

/**
 * Creates a test QueryClient with disabled retries and caching for consistent test results
 * @returns {QueryClient} Configured test QueryClient
 */
const createTestQueryClient = (): QueryClient => new QueryClient({
    defaultOptions: {
        queries: {
            retry: false,
            staleTime: 0,
            gcTime: 0,
        },
        mutations: {
            retry: false,
        },
    },
});

/**
 * Test wrapper component that provides QueryClient context
 * @param {React.ReactNode} children - Child components to wrap
 * @returns {React.ReactElement} Wrapped component
 */
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [queryClient] = React.useState(() => createTestQueryClient());
    return (
        <QueryClientProvider client={queryClient}>
            {children}
        </QueryClientProvider>
    );
};

// Mock data
const mockInitiative: InitiativeDto = {
    id: 'test-initiative-1',
    title: 'Test Initiative',
    description: 'Test Description',
    status: InitiativeStatus.TO_DO,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    identifier: 'I-001',
    user_id: 'test-user-1',
    type: null,
    tasks: [],
    has_pending_job: null,
    orderings: []
};

const mockInitiatives = [mockInitiative];

describe('useInitiativesContext', () => {
    beforeEach(() => {
        vi.clearAllMocks();

        // Mock console methods to avoid test output noise
        vi.spyOn(console, 'log').mockImplementation(() => {});
        vi.spyOn(console, 'warn').mockImplementation(() => {});
        vi.spyOn(console, 'error').mockImplementation(() => {});

        // Reset default mock returns
        vi.mocked(useInitiativesQuery).mockReturnValue(mockQueryResult);
        vi.mocked(useInitiativesCache).mockReturnValue(mockCacheOperations);
        vi.mocked(useInitiativesMutations).mockReturnValue(mockMutationOperations);
        vi.mocked(useInitiativesQueryCacheVersion).mockReturnValue([mockCacheVersion, mockSetCacheVersion]);
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Hook Composition', () => {
        it('should compose all sub-hooks with correct parameters', () => {
            const filters: InitiativeFilters = { status: [InitiativeStatus.TO_DO] };

            renderHook(() => useInitiativesContext(filters), { wrapper: TestWrapper });

            expect(useInitiativesQueryCacheVersion).toHaveBeenCalledTimes(1);
            expect(useInitiativesQuery).toHaveBeenCalledWith(filters, mockCacheVersion);
            expect(useInitiativesCache).toHaveBeenCalledWith(filters, mockSetCacheVersion);
            expect(useInitiativesMutations).toHaveBeenCalledWith(
                mockCacheOperations.updateInitiativeInCache,
                filters,
                mockSetCacheVersion,
                mockQueryResult.reloadInitiatives
            );
        });

        it('should compose hooks with undefined filters', () => {
            renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            expect(useInitiativesQuery).toHaveBeenCalledWith(undefined, mockCacheVersion);
            expect(useInitiativesCache).toHaveBeenCalledWith(undefined, mockSetCacheVersion);
            expect(useInitiativesMutations).toHaveBeenCalledWith(
                mockCacheOperations.updateInitiativeInCache,
                undefined,
                mockSetCacheVersion,
                mockQueryResult.reloadInitiatives
            );
        });

        it('should pass updateInitiativeInCache from cache operations to mutations', () => {
            const customUpdateFunction = vi.fn();
            vi.mocked(useInitiativesCache).mockReturnValue({
                ...mockCacheOperations,
                updateInitiativeInCache: customUpdateFunction,
            });

            renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            expect(useInitiativesMutations).toHaveBeenCalledWith(
                customUpdateFunction,
                undefined,
                mockSetCacheVersion,
                mockQueryResult.reloadInitiatives
            );
        });

        it('should pass reloadInitiatives from query result to mutations', () => {
            const customReloadFunction = vi.fn();
            vi.mocked(useInitiativesQuery).mockReturnValue({
                ...mockQueryResult,
                reloadInitiatives: customReloadFunction,
            });

            renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            expect(useInitiativesMutations).toHaveBeenCalledWith(
                mockCacheOperations.updateInitiativeInCache,
                undefined,
                mockSetCacheVersion,
                customReloadFunction
            );
        });
    });

    describe('Return Value Composition', () => {
        it('should return complete context interface with all properties', () => {
            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            // Query result properties
            expect(result.current.initiativesData).toBe(mockQueryResult.initiativesData);
            expect(result.current.error).toBe(mockQueryResult.error);
            expect(result.current.shouldShowSkeleton).toBe(mockQueryResult.shouldShowSkeleton);
            expect(result.current.isQueryFetching).toBe(mockQueryResult.isQueryFetching);
            expect(result.current.reloadInitiatives).toBe(mockQueryResult.reloadInitiatives);

            // Cache operations properties
            expect(result.current.invalidateInitiative).toBe(mockCacheOperations.invalidateInitiative);
            expect(result.current.invalidateAllInitiatives).toBe(mockCacheOperations.invalidateAllInitiatives);
            expect(result.current.invalidateInitiativesByStatus).toBe(mockCacheOperations.invalidateInitiativesByStatus);

            // Mutation operations properties - loading states
            expect(result.current.isCreatingInitiative).toBe(mockMutationOperations.isCreatingInitiative);
            expect(result.current.isUpdatingInitiative).toBe(mockMutationOperations.isUpdatingInitiative);
            expect(result.current.isDeletingInitiative).toBe(mockMutationOperations.isDeletingInitiative);
            expect(result.current.isBatchUpdatingInitiatives).toBe(mockMutationOperations.isBatchUpdatingInitiatives);
            expect(result.current.isDeletingTask).toBe(mockMutationOperations.isDeletingTask);
            expect(result.current.isDeletingChecklistItem).toBe(mockMutationOperations.isDeletingChecklistItem);

            // Mutation operations properties - functions
            expect(result.current.createInitiative).toBe(mockMutationOperations.createInitiative);
            expect(result.current.updateInitiative).toBe(mockMutationOperations.updateInitiative);
            expect(result.current.updateInitiatives).toBe(mockMutationOperations.updateInitiatives);
            expect(result.current.deleteInitiative).toBe(mockMutationOperations.deleteInitiative);
            expect(result.current.deleteTask).toBe(mockMutationOperations.deleteTask);
            expect(result.current.deleteChecklistItem).toBe(mockMutationOperations.deleteChecklistItem);
            expect(result.current.reorderInitiative).toBe(mockMutationOperations.reorderInitiative);
            expect(result.current.moveInitiativeToStatus).toBe(mockMutationOperations.moveInitiativeToStatus);
            expect(result.current.moveInitiativeInGroup).toBe(mockMutationOperations.moveInitiativeInGroup);
        });

        it('should maintain the exact InitiativesContextType interface', () => {
            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            // Verify the return type matches InitiativesContextType exactly
            const contextValue = result.current;

            // Check that all required properties exist
            expect(contextValue).toHaveProperty('initiativesData');
            expect(contextValue).toHaveProperty('error');
            expect(contextValue).toHaveProperty('shouldShowSkeleton');
            expect(contextValue).toHaveProperty('isQueryFetching');
            expect(contextValue).toHaveProperty('reloadInitiatives');

            expect(contextValue).toHaveProperty('invalidateInitiative');
            expect(contextValue).toHaveProperty('invalidateAllInitiatives');
            expect(contextValue).toHaveProperty('invalidateInitiativesByStatus');

            expect(contextValue).toHaveProperty('isCreatingInitiative');
            expect(contextValue).toHaveProperty('isUpdatingInitiative');
            expect(contextValue).toHaveProperty('isDeletingInitiative');
            expect(contextValue).toHaveProperty('isBatchUpdatingInitiatives');
            expect(contextValue).toHaveProperty('isDeletingTask');
            expect(contextValue).toHaveProperty('isDeletingChecklistItem');

            expect(contextValue).toHaveProperty('createInitiative');
            expect(contextValue).toHaveProperty('updateInitiative');
            expect(contextValue).toHaveProperty('updateInitiatives');
            expect(contextValue).toHaveProperty('deleteInitiative');
            expect(contextValue).toHaveProperty('deleteTask');
            expect(contextValue).toHaveProperty('deleteChecklistItem');
            expect(contextValue).toHaveProperty('reorderInitiative');
            expect(contextValue).toHaveProperty('moveInitiativeToStatus');
            expect(contextValue).toHaveProperty('moveInitiativeInGroup');
        });
    });

    describe('Memoization', () => {
        it('should memoize the return value correctly', () => {
            const { result, rerender } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            const initialValue = result.current;

            // Re-render without changing any dependencies
            rerender();

            // The returned value should be the same object reference due to useMemo
            expect(result.current).toBe(initialValue);
        });

        it('should re-create return value when sub-hook results change', () => {
            const { result, rerender } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            const initialValue = result.current;

            // Change one of the sub-hook results
            vi.mocked(useInitiativesQuery).mockReturnValue({
                ...mockQueryResult,
                isQueryFetching: true, // Changed value
            });

            rerender();

            // The returned value should be a new object reference
            expect(result.current).not.toBe(initialValue);
            expect(result.current.isQueryFetching).toBe(true);
        });

        it('should include all dependencies in useMemo dependency array', () => {
            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            const initialValue = result.current;

            // Change cache operations
            const newCacheOperations = {
                ...mockCacheOperations,
                invalidateInitiative: vi.fn(), // New function reference
            };
            vi.mocked(useInitiativesCache).mockReturnValue(newCacheOperations);

            const { result: result2 } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            // Should be a different object since cache operations changed
            expect(result2.current).not.toBe(initialValue);
            expect(result2.current.invalidateInitiative).toBe(newCacheOperations.invalidateInitiative);
        });
    });

    describe('Cache Version Management', () => {
        it('should use cache version from useInitiativesQueryCacheVersion', () => {
            const customCacheVersion = 5;
            const customSetCacheVersion = vi.fn();
            vi.mocked(useInitiativesQueryCacheVersion).mockReturnValue([customCacheVersion, customSetCacheVersion]);

            renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            expect(useInitiativesQuery).toHaveBeenCalledWith(undefined, customCacheVersion);
            expect(useInitiativesCache).toHaveBeenCalledWith(undefined, customSetCacheVersion);
            expect(useInitiativesMutations).toHaveBeenCalledWith(
                mockCacheOperations.updateInitiativeInCache,
                undefined,
                customSetCacheVersion,
                mockQueryResult.reloadInitiatives
            );
        });

        it('should pass setCacheVersion to both cache and mutations hooks', () => {
            const customSetCacheVersion = vi.fn();
            vi.mocked(useInitiativesQueryCacheVersion).mockReturnValue([1, customSetCacheVersion]);

            renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            // Both cache and mutations should receive the same setCacheVersion function
            expect(useInitiativesCache).toHaveBeenCalledWith(
                undefined,
                customSetCacheVersion
            );
            expect(useInitiativesMutations).toHaveBeenCalledWith(
                mockCacheOperations.updateInitiativeInCache,
                undefined,
                customSetCacheVersion,
                mockQueryResult.reloadInitiatives
            );
        });
    });

    describe('Filters Handling', () => {
        it('should pass filters to all relevant sub-hooks', () => {
            const filters: InitiativeFilters = {
                id: 'test-id',
                status: [InitiativeStatus.TO_DO, InitiativeStatus.IN_PROGRESS]
            };

            renderHook(() => useInitiativesContext(filters), { wrapper: TestWrapper });

            expect(useInitiativesQuery).toHaveBeenCalledWith(filters, mockCacheVersion);
            expect(useInitiativesCache).toHaveBeenCalledWith(filters, mockSetCacheVersion);
            expect(useInitiativesMutations).toHaveBeenCalledWith(
                mockCacheOperations.updateInitiativeInCache,
                filters,
                mockSetCacheVersion,
                mockQueryResult.reloadInitiatives
            );
        });

        it('should handle filter changes correctly', () => {
            const initialFilters: InitiativeFilters = { status: [InitiativeStatus.TO_DO] };
            const updatedFilters: InitiativeFilters = { status: [InitiativeStatus.IN_PROGRESS] };

            const { rerender } = renderHook(
                ({ filters }: { filters?: InitiativeFilters }) => useInitiativesContext(filters),
                {
                    wrapper: TestWrapper,
                    initialProps: { filters: initialFilters }
                }
            );

            expect(useInitiativesQuery).toHaveBeenLastCalledWith(initialFilters, mockCacheVersion);

            // Update filters
            rerender({ filters: updatedFilters });

            expect(useInitiativesQuery).toHaveBeenLastCalledWith(updatedFilters, mockCacheVersion);
            expect(useInitiativesCache).toHaveBeenLastCalledWith(updatedFilters, mockSetCacheVersion);
            expect(useInitiativesMutations).toHaveBeenLastCalledWith(
                mockCacheOperations.updateInitiativeInCache,
                updatedFilters,
                mockSetCacheVersion,
                mockQueryResult.reloadInitiatives
            );
        });

        it('should handle empty filters correctly', () => {
            const emptyFilters: InitiativeFilters = {};

            renderHook(() => useInitiativesContext(emptyFilters), { wrapper: TestWrapper });

            expect(useInitiativesQuery).toHaveBeenCalledWith(emptyFilters, mockCacheVersion);
            expect(useInitiativesCache).toHaveBeenCalledWith(emptyFilters, mockSetCacheVersion);
            expect(useInitiativesMutations).toHaveBeenCalledWith(
                mockCacheOperations.updateInitiativeInCache,
                emptyFilters,
                mockSetCacheVersion,
                mockQueryResult.reloadInitiatives
            );
        });
    });

    describe('Integration Testing', () => {
        it('should propagate data changes through the composition', () => {
            const mockInitiativesData = [{ ...mockInitiative, position: 'aa', orderingId: 'order-1' }];

            vi.mocked(useInitiativesQuery).mockReturnValue({
                ...mockQueryResult,
                initiativesData: mockInitiativesData,
                isQueryFetching: true,
            });

            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            expect(result.current.initiativesData).toBe(mockInitiativesData);
            expect(result.current.isQueryFetching).toBe(true);
        });

        it('should propagate loading states from mutations', () => {
            vi.mocked(useInitiativesMutations).mockReturnValue({
                ...mockMutationOperations,
                isCreatingInitiative: true,
                isUpdatingInitiative: true,
                isDeletingInitiative: true,
            });

            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            expect(result.current.isCreatingInitiative).toBe(true);
            expect(result.current.isUpdatingInitiative).toBe(true);
            expect(result.current.isDeletingInitiative).toBe(true);
        });

        it('should propagate error states from query', () => {
            const errorMessage = 'Test error';

            vi.mocked(useInitiativesQuery).mockReturnValue({
                ...mockQueryResult,
                error: errorMessage,
                shouldShowSkeleton: true,
            });

            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            expect(result.current.error).toBe(errorMessage);
            expect(result.current.shouldShowSkeleton).toBe(true);
        });

        it('should maintain function stability from sub-hooks', () => {
            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            const initialFunctions = {
                reloadInitiatives: result.current.reloadInitiatives,
                createInitiative: result.current.createInitiative,
                invalidateInitiative: result.current.invalidateInitiative,
            };

            // Verify functions came from the mocked sub-hooks
            expect(initialFunctions.reloadInitiatives).toBe(mockQueryResult.reloadInitiatives);
            expect(initialFunctions.createInitiative).toBe(mockMutationOperations.createInitiative);
            expect(initialFunctions.invalidateInitiative).toBe(mockCacheOperations.invalidateInitiative);
        });
    });

    describe('Edge Cases', () => {
        it('should handle undefined sub-hook results gracefully', () => {
            // This shouldn't happen in practice, but test defensive programming
            vi.mocked(useInitiativesQuery).mockReturnValue({
                ...mockQueryResult,
                initiativesData: null,
                error: null,
            });

            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            expect(result.current.initiativesData).toBe(null);
            expect(result.current.error).toBe(null);
        });

        it('should handle all sub-hooks returning different data types correctly', () => {
            const customQueryResult = {
                ...mockQueryResult,
                initiativesData: [{ ...mockInitiative, position: 'aa', orderingId: 'order-1' }],
                shouldShowSkeleton: true,
            };

            const customCacheOperations = {
                ...mockCacheOperations,
                invalidateInitiative: vi.fn(),
            };

            const customMutationOperations = {
                ...mockMutationOperations,
                isCreatingInitiative: true,
            };

            vi.mocked(useInitiativesQuery).mockReturnValue(customQueryResult);
            vi.mocked(useInitiativesCache).mockReturnValue(customCacheOperations);
            vi.mocked(useInitiativesMutations).mockReturnValue(customMutationOperations);

            const { result } = renderHook(() => useInitiativesContext(), { wrapper: TestWrapper });

            // Should combine all results correctly
            expect(result.current.initiativesData).toBe(customQueryResult.initiativesData);
            expect(result.current.shouldShowSkeleton).toBe(customQueryResult.shouldShowSkeleton);
            expect(result.current.invalidateInitiative).toBe(customCacheOperations.invalidateInitiative);
            expect(result.current.isCreatingInitiative).toBe(customMutationOperations.isCreatingInitiative);
        });
    });
});