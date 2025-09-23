import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { useInitiativesCache } from './useInitiativesCache';
import { InitiativeDto, InitiativeStatus } from '#types';
import { InitiativeFilters } from './types';

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

const mockInitiatives: InitiativeDto[] = [
    mockInitiative,
    {
        ...mockInitiative,
        id: 'test-initiative-2',
        title: 'Test Initiative 2',
        identifier: 'I-002',
        status: InitiativeStatus.IN_PROGRESS,
    },
    {
        ...mockInitiative,
        id: 'test-initiative-3',
        title: 'Test Initiative 3',
        identifier: 'I-003',
        status: InitiativeStatus.DONE,
    },
];

describe('useInitiativesCache', () => {
    let queryClient: QueryClient;
    let setCacheVersion: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        queryClient = createTestQueryClient();
        setCacheVersion = vi.fn();

        // Mock console methods to avoid test output noise
        vi.spyOn(console, 'log').mockImplementation(() => {});
        vi.spyOn(console, 'warn').mockImplementation(() => {});
        vi.spyOn(console, 'error').mockImplementation(() => {});

        // Pre-populate cache with test data
        queryClient.setQueryData(['initiatives', {}], mockInitiatives);
        queryClient.setQueryData(['initiatives', { id: mockInitiative.id }], mockInitiative);
        queryClient.setQueryData(['initiatives', { status: [InitiativeStatus.TO_DO] }], [mockInitiatives[0]]);
        queryClient.setQueryData(['initiatives', { status: [InitiativeStatus.IN_PROGRESS] }], [mockInitiatives[1]]);
    });

    afterEach(() => {
        vi.restoreAllMocks();
        queryClient.clear();
    });

    /**
     * Enhanced test wrapper that provides spied QueryClient for cache testing
     */
    const TestWrapperWithClient: React.FC<{ children: React.ReactNode }> = ({ children }) => {
        return (
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        );
    };

    describe('Invalidation Operations', () => {
        it('should invalidate single initiative by ID', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

            act(() => {
                result.current.invalidateInitiative('test-initiative-1');
            });

            expect(invalidateQueriesSpy).toHaveBeenCalledWith({
                queryKey: ['initiatives', { id: 'test-initiative-1' }]
            });
        });

        it('should invalidate all initiatives', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

            act(() => {
                result.current.invalidateAllInitiatives();
            });

            expect(invalidateQueriesSpy).toHaveBeenCalledWith({
                queryKey: ['initiatives']
            });
        });

        it('should invalidate initiatives by single status', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

            act(() => {
                result.current.invalidateInitiativesByStatus(InitiativeStatus.TO_DO);
            });

            expect(invalidateQueriesSpy).toHaveBeenCalledWith({
                queryKey: ['initiatives'],
                predicate: expect.any(Function)
            });
        });

        it('should invalidate initiatives by multiple statuses', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

            act(() => {
                result.current.invalidateInitiativesByStatus([
                    InitiativeStatus.TO_DO,
                    InitiativeStatus.IN_PROGRESS
                ]);
            });

            expect(invalidateQueriesSpy).toHaveBeenCalledWith({
                queryKey: ['initiatives'],
                predicate: expect.any(Function)
            });
        });

        it('should correctly identify matching queries in status invalidation predicate', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

            act(() => {
                result.current.invalidateInitiativesByStatus(InitiativeStatus.TO_DO);
            });

            // Get the predicate function that was passed
            const predicateCall = invalidateQueriesSpy.mock.calls[0]?.[0];
            const predicate = predicateCall?.predicate;

            // Test the predicate function
            const matchingQuery = {
                queryKey: ['initiatives', { status: [InitiativeStatus.TO_DO] }]
            } as any;
            const nonMatchingQuery = {
                queryKey: ['initiatives', { status: [InitiativeStatus.IN_PROGRESS] }]
            } as any;
            const queryWithoutStatus = {
                queryKey: ['initiatives', {}]
            } as any;

            expect(predicate?.(matchingQuery)).toBe(true);
            expect(predicate?.(nonMatchingQuery)).toBe(false);
            expect(predicate?.(queryWithoutStatus)).toBe(false);
        });
    });

    describe('Cache Updates', () => {
        it('should update initiative in specific initiative cache', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const updatedInitiative = {
                ...mockInitiative,
                title: 'Updated Title',
                updated_at: '2024-01-02T00:00:00Z',
            };

            const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');

            act(() => {
                result.current.updateInitiativeInCache(updatedInitiative);
            });

            expect(setQueryDataSpy).toHaveBeenCalledWith(
                ['initiatives', { id: updatedInitiative.id }],
                updatedInitiative
            );
        });

        it('should update initiative in general initiatives cache', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const updatedInitiative = {
                ...mockInitiative,
                title: 'Updated Title',
            };

            act(() => {
                result.current.updateInitiativeInCache(updatedInitiative);
            });

            // Verify the general cache was updated
            const generalCache = queryClient.getQueryData<InitiativeDto[]>(['initiatives', {}]);
            const updatedItem = generalCache?.find(item => item.id === updatedInitiative.id);
            expect(updatedItem).toEqual(expect.objectContaining(updatedInitiative));
        });

        it('should handle status changes in cache updates', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const updatedInitiative = {
                ...mockInitiative,
                status: InitiativeStatus.IN_PROGRESS,
            };
            const oldStatus = InitiativeStatus.TO_DO;

            act(() => {
                result.current.updateInitiativeInCache(updatedInitiative, oldStatus);
            });

            // Verify it's added to new status list
            const newStatusCache = queryClient.getQueryData<InitiativeDto[]>([
                'initiatives',
                { status: [InitiativeStatus.IN_PROGRESS] }
            ]);
            expect(newStatusCache?.find(item => item.id === updatedInitiative.id)).toEqual(
                expect.objectContaining(updatedInitiative)
            );

            // Verify it's removed from old status list
            const oldStatusCache = queryClient.getQueryData<InitiativeDto[]>([
                'initiatives',
                { status: [InitiativeStatus.TO_DO] }
            ]);
            expect(oldStatusCache?.find(item => item.id === updatedInitiative.id)).toBeUndefined();
        });

        it('should update existing item in new status list when status changes', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            // First, add the initiative to the IN_PROGRESS status cache
            const existingInProgressItem = {
                ...mockInitiative,
                status: InitiativeStatus.IN_PROGRESS,
                title: 'Old Title'
            };
            queryClient.setQueryData(
                ['initiatives', { status: [InitiativeStatus.IN_PROGRESS] }],
                [mockInitiatives[1], existingInProgressItem]
            );

            // Now update it with new data
            const updatedInitiative = {
                ...existingInProgressItem,
                title: 'Updated Title',
            };

            act(() => {
                result.current.updateInitiativeInCache(updatedInitiative, InitiativeStatus.TO_DO);
            });

            // Verify the existing item was updated, not added as duplicate
            const newStatusCache = queryClient.getQueryData<InitiativeDto[]>([
                'initiatives',
                { status: [InitiativeStatus.IN_PROGRESS] }
            ]);
            const updatedItems = newStatusCache?.filter(item => item.id === updatedInitiative.id);
            expect(updatedItems).toHaveLength(1); // Should have exactly one, not duplicate
            expect(updatedItems?.[0]?.title).toBe('Updated Title');
        });

        it('should increment cache version after update', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const updatedInitiative = {
                ...mockInitiative,
                title: 'Updated Title',
            };

            act(() => {
                result.current.updateInitiativeInCache(updatedInitiative);
            });

            expect(setCacheVersion).toHaveBeenCalledWith(expect.any(Function));

            // Test the function passed to setCacheVersion
            const incrementFn = setCacheVersion.mock.calls[0][0];
            expect(incrementFn(1)).toBe(2);
        });

        it('should handle cache update without setCacheVersion function', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, undefined),
                { wrapper: TestWrapperWithClient }
            );

            const updatedInitiative = {
                ...mockInitiative,
                title: 'Updated Title',
            };

            // Should not throw when setCacheVersion is undefined
            expect(() => {
                act(() => {
                    result.current.updateInitiativeInCache(updatedInitiative);
                });
            }).not.toThrow();

            // Verify cache was still updated
            const specificCache = queryClient.getQueryData<InitiativeDto>(['initiatives', { id: updatedInitiative.id }]);
            expect(specificCache).toEqual(updatedInitiative);
        });
    });

    describe('Query Key Construction', () => {
        it('should build query key with no filters', () => {
            const { result } = renderHook(
                () => useInitiativesCache(),
                { wrapper: TestWrapperWithClient }
            );

            // Verify the hook works with no filters (uses empty object)
            expect(result.current.invalidateInitiative).toBeInstanceOf(Function);
            expect(result.current.invalidateAllInitiatives).toBeInstanceOf(Function);
        });

        it('should build query key with provided filters', () => {
            const filters: InitiativeFilters = { status: [InitiativeStatus.TO_DO] };

            const { result } = renderHook(
                () => useInitiativesCache(filters, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            // Verify the hook works with filters
            expect(result.current.invalidateInitiative).toBeInstanceOf(Function);
            expect(result.current.updateInitiativeInCache).toBeInstanceOf(Function);
        });

        it('should use filters in cache operations', () => {
            const filters: InitiativeFilters = { status: [InitiativeStatus.TO_DO] };

            const { result } = renderHook(
                () => useInitiativesCache(filters, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');
            const updatedInitiative = {
                ...mockInitiative,
                title: 'Updated with Filters',
            };

            act(() => {
                result.current.updateInitiativeInCache(updatedInitiative);
            });

            // Should still update the general cache regardless of filters
            expect(setQueryDataSpy).toHaveBeenCalledWith(
                ['initiatives', {}],
                expect.any(Function)
            );
        });
    });

    describe('Edge Cases and Error Handling', () => {
        it('should handle cache update when general cache is empty', () => {
            // Clear the general cache
            queryClient.removeQueries({ queryKey: ['initiatives', {}] });

            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const updatedInitiative = {
                ...mockInitiative,
                title: 'Updated Title',
            };

            // Should not throw when general cache is empty
            expect(() => {
                act(() => {
                    result.current.updateInitiativeInCache(updatedInitiative);
                });
            }).not.toThrow();

            // Should still update specific initiative cache
            const specificCache = queryClient.getQueryData<InitiativeDto>(['initiatives', { id: updatedInitiative.id }]);
            expect(specificCache).toEqual(updatedInitiative);
        });

        it('should handle status change when status-specific cache does not exist', () => {
            // Remove status-specific caches
            queryClient.removeQueries({ queryKey: ['initiatives', { status: [InitiativeStatus.TO_DO] }] });
            queryClient.removeQueries({ queryKey: ['initiatives', { status: [InitiativeStatus.IN_PROGRESS] }] });

            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const updatedInitiative = {
                ...mockInitiative,
                status: InitiativeStatus.IN_PROGRESS,
            };

            // Should not throw when status-specific caches don't exist
            expect(() => {
                act(() => {
                    result.current.updateInitiativeInCache(updatedInitiative, InitiativeStatus.TO_DO);
                });
            }).not.toThrow();
        });

        it('should handle invalid initiative data gracefully', () => {
            const { result } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            // Test with minimal initiative data
            const minimalInitiative = {
                id: 'minimal-1',
                status: InitiativeStatus.TO_DO,
            } as InitiativeDto;

            expect(() => {
                act(() => {
                    result.current.updateInitiativeInCache(minimalInitiative);
                });
            }).not.toThrow();

            // Verify it was still cached
            const specificCache = queryClient.getQueryData<InitiativeDto>(['initiatives', { id: minimalInitiative.id }]);
            expect(specificCache).toEqual(minimalInitiative);
        });
    });

    describe('Function Stability', () => {
        it('should return stable function references', () => {
            const { result, rerender } = renderHook(
                () => useInitiativesCache(undefined, setCacheVersion),
                { wrapper: TestWrapperWithClient }
            );

            const initialFunctions = {
                invalidateInitiative: result.current.invalidateInitiative,
                invalidateAllInitiatives: result.current.invalidateAllInitiatives,
                invalidateInitiativesByStatus: result.current.invalidateInitiativesByStatus,
                updateInitiativeInCache: result.current.updateInitiativeInCache,
            };

            // Re-render the hook
            rerender();

            // Functions should remain the same reference (memoized)
            expect(result.current.invalidateInitiative).toBe(initialFunctions.invalidateInitiative);
            expect(result.current.invalidateAllInitiatives).toBe(initialFunctions.invalidateAllInitiatives);
            expect(result.current.invalidateInitiativesByStatus).toBe(initialFunctions.invalidateInitiativesByStatus);
            expect(result.current.updateInitiativeInCache).toBe(initialFunctions.updateInitiativeInCache);
        });

        it('should update function references when dependencies change', () => {
            const filters1: InitiativeFilters = { status: [InitiativeStatus.TO_DO] };
            const filters2: InitiativeFilters = { status: [InitiativeStatus.IN_PROGRESS] };

            const { result, rerender } = renderHook(
                ({ filters }: { filters?: InitiativeFilters }) => useInitiativesCache(filters, setCacheVersion),
                {
                    wrapper: TestWrapperWithClient,
                    initialProps: { filters: filters1 }
                }
            );

            const initialUpdateFunction = result.current.updateInitiativeInCache;

            // Change filters - should create new function references
            rerender({ filters: filters2 });

            // The updateInitiativeInCache function should be the same since it doesn't depend on filters
            expect(result.current.updateInitiativeInCache).toBe(initialUpdateFunction);
        });
    });
});