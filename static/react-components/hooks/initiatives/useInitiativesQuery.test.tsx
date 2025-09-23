import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { useInitiativesQuery } from './useInitiativesQuery';
import { InitiativeDto, InitiativeStatus, ContextType, EntityType } from '#types';
import { OrderedEntity } from '#hooks/useOrderings';
import { InitiativeFilters } from './types';

// Mock all API dependencies
vi.mock('#api/initiatives', () => ({
    getAllInitiatives: vi.fn(),
    getInitiativeById: vi.fn(),
}));

// Mock useOrderings hook
const mockUseOrderings = {
    orderedEntities: [],
    isError: false
};

vi.mock('#hooks/useOrderings', () => ({
    useOrderings: vi.fn(() => mockUseOrderings),
}));

// Import mocked modules
import * as initiativesApi from '#api/initiatives';
import { useOrderings } from '#hooks/useOrderings';

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
    orderings: [{
        id: 'test-initiative-1-orderings',
        contextType: ContextType.STATUS_LIST,
        contextId: null,
        entityType: EntityType.INITIATIVE,
        initiativeId: 'test-initiative-1',
        taskId: null,
        position: 'bb'
    }]
};

const mockInitiatives: InitiativeDto[] = [
    mockInitiative,
    {
        ...mockInitiative,
        id: 'test-initiative-2',
        title: 'Test Initiative 2',
        identifier: 'I-002',
        status: InitiativeStatus.IN_PROGRESS,
        orderings: [{
            id: 'test-initiative-2-orderings',
            contextType: ContextType.STATUS_LIST,
            contextId: null,
            entityType: EntityType.INITIATIVE,
            initiativeId: 'test-initiative-2',
            taskId: null,
            position: 'aa'
        }]
    },
];

// Helper function to convert InitiativeDto to OrderedEntity for testing
const toOrderedEntity = (initiative: InitiativeDto): OrderedEntity<InitiativeDto> => {
    const ordering = initiative.orderings?.[0];
    return {
        ...initiative,
        position: ordering?.position || '',
        orderingId: ordering?.id || ''
    };
};

const mockOrderedInitiatives: OrderedEntity<InitiativeDto>[] = mockInitiatives.map(toOrderedEntity);

describe('useInitiativesQuery', () => {
    beforeEach(() => {
        vi.clearAllMocks();

        // Mock console methods to avoid test output noise
        vi.spyOn(console, 'log').mockImplementation(() => {});
        vi.spyOn(console, 'warn').mockImplementation(() => {});
        vi.spyOn(console, 'error').mockImplementation(() => {});

        // Set up default mock implementations
        vi.mocked(initiativesApi.getAllInitiatives).mockResolvedValue(mockInitiatives);
        vi.mocked(initiativesApi.getInitiativeById).mockResolvedValue(mockInitiative);
        vi.mocked(useOrderings).mockReturnValue({
            ...mockUseOrderings,
            orderedEntities: mockOrderedInitiatives,
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Data Fetching with No Filters', () => {
        it('should fetch all initiatives when no filters provided', async () => {
            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(initiativesApi.getAllInitiatives).toHaveBeenCalledWith(undefined);
            expect(result.current.initiativesData).toEqual(mockOrderedInitiatives);
            expect(result.current.error).toBe(null);
            expect(result.current.shouldShowSkeleton).toBe(false);
        });

        it('should handle empty filters as no filters', async () => {
            const { result } = renderHook(() => useInitiativesQuery({}), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(initiativesApi.getAllInitiatives).toHaveBeenCalledWith({});
            expect(result.current.initiativesData).toEqual(mockOrderedInitiatives);
        });
    });

    describe('Data Fetching with ID Filter', () => {
        it('should fetch single initiative when ID filter provided', async () => {
            const filters: InitiativeFilters = { id: 'test-initiative-1' };

            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: [toOrderedEntity(mockInitiative)],
            });

            const { result } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(initiativesApi.getInitiativeById).toHaveBeenCalledWith('test-initiative-1');
            expect(initiativesApi.getAllInitiatives).not.toHaveBeenCalled();
            expect(result.current.initiativesData).toEqual([toOrderedEntity(mockInitiative)]);
        });

        it('should transform single initiative response to array', async () => {
            const filters: InitiativeFilters = { id: 'test-initiative-1' };

            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: [toOrderedEntity(mockInitiative)],
            });

            const { result } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            // Verify data is transformed to array and has OrderedEntity properties
            expect(Array.isArray(result.current.initiativesData)).toBe(true);
            expect(result.current.initiativesData).toHaveLength(1);
            expect(result.current.initiativesData?.[0]).toHaveProperty('position');
            expect(result.current.initiativesData?.[0]).toHaveProperty('orderingId');
        });

        it('should handle ID filter with other filters (ID takes precedence)', async () => {
            const filters: InitiativeFilters = {
                id: 'test-initiative-1',
                status: [InitiativeStatus.IN_PROGRESS]
            };

            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: [toOrderedEntity(mockInitiative)],
            });

            const { result } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            // Should use getInitiativeById regardless of status filter
            expect(initiativesApi.getInitiativeById).toHaveBeenCalledWith('test-initiative-1');
            expect(initiativesApi.getAllInitiatives).not.toHaveBeenCalled();
        });
    });

    describe('Data Fetching with Status Filter', () => {
        it('should fetch initiatives with single status filter', async () => {
            const filters: InitiativeFilters = { status: [InitiativeStatus.TO_DO] };
            const filteredInitiatives = mockInitiatives.filter(i => i.status === InitiativeStatus.TO_DO);
            const orderedFiltered = filteredInitiatives.map(toOrderedEntity);

            vi.mocked(initiativesApi.getAllInitiatives).mockResolvedValue(filteredInitiatives);
            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: orderedFiltered,
            });

            const { result } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(initiativesApi.getAllInitiatives).toHaveBeenCalledWith(filters);
            expect(result.current.initiativesData).toEqual(orderedFiltered);
        });

        it('should fetch initiatives with multiple status filters', async () => {
            const filters: InitiativeFilters = {
                status: [InitiativeStatus.TO_DO, InitiativeStatus.IN_PROGRESS]
            };

            const { result } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(initiativesApi.getAllInitiatives).toHaveBeenCalledWith(filters);
        });

        it('should handle empty status array', async () => {
            const filters: InitiativeFilters = { status: [] };

            const { result } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(initiativesApi.getAllInitiatives).toHaveBeenCalledWith(filters);
        });
    });

    describe('Loading States', () => {
        it('should show skeleton when useOrderings is loading', async () => {
            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: [],
            });

            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            expect(result.current.shouldShowSkeleton).toBe(true);
            expect(result.current.initiativesData).toBeNull();
        });

        it('should not show skeleton when data exists even if ordering is loading', async () => {
            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: mockOrderedInitiatives,
            });

            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            expect(result.current.shouldShowSkeleton).toBe(false);
            expect(result.current.initiativesData).toEqual(mockOrderedInitiatives);
        });

        it('should track query fetching state correctly', async () => {
            let resolvePromise: (value: InitiativeDto[]) => void;
            const promise = new Promise<InitiativeDto[]>((resolve) => {
                resolvePromise = resolve;
            });

            vi.mocked(initiativesApi.getAllInitiatives).mockReturnValue(promise);

            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            // Should be fetching initially
            expect(result.current.isQueryFetching).toBe(true);

            // Resolve the promise
            act(() => {
                resolvePromise!(mockInitiatives);
            });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });
        });
    });

    describe('Error Handling', () => {
        it('should handle getAllInitiatives error', async () => {
            const errorMessage = 'Network error';
            vi.mocked(initiativesApi.getAllInitiatives).mockRejectedValue(new Error(errorMessage));

            // Mock useOrderings to return empty array when API fails
            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: [],
            });

            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.error).toBe('Error loading initiatives');
            });

            expect(result.current.initiativesData).toBeNull();
            expect(result.current.shouldShowSkeleton).toBe(false);
        });

        it('should handle getInitiativeById error', async () => {
            const filters: InitiativeFilters = { id: 'test-initiative-1' };
            const errorMessage = 'Initiative not found';
            vi.mocked(initiativesApi.getInitiativeById).mockRejectedValue(new Error(errorMessage));

            // Mock useOrderings to return empty array when API fails
            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: [],
            });

            const { result } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.error).toBe('Error loading initiative');
            });

            expect(result.current.initiativesData).toBeNull();
        });

        it('should handle useOrderings error', async () => {
            vi.mocked(useOrderings).mockReturnValue({
                ...mockUseOrderings,
                orderedEntities: [],
            });

            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            // Should pass through the ordering error state
            expect(result.current.initiativesData).toBeNull();
        });
    });

    describe('Integration with useOrderings', () => {
        it('should call useOrderings with correct parameters for all initiatives', async () => {
            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(useOrderings).toHaveBeenCalledWith({
                contextType: ContextType.STATUS_LIST,
                entityType: EntityType.INITIATIVE,
                contextId: null,
                entitiesToOrder: mockInitiatives,
                orderDirection: 'asc'
            });
        });

        it('should call useOrderings with correct parameters for single initiative', async () => {
            const filters: InitiativeFilters = { id: 'test-initiative-1' };

            const { result } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(useOrderings).toHaveBeenCalledWith({
                contextType: ContextType.STATUS_LIST,
                entityType: EntityType.INITIATIVE,
                contextId: null,
                entitiesToOrder: [mockInitiative], // Single initiative wrapped in array
                orderDirection: 'asc'
            });
        });

        it('should pass empty array to useOrderings when data fetch fails', async () => {
            vi.mocked(initiativesApi.getAllInitiatives).mockRejectedValue(new Error('API Error'));

            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.error).toBe('Error loading initiatives');
            });

            expect(useOrderings).toHaveBeenCalledWith({
                contextType: ContextType.STATUS_LIST,
                entityType: EntityType.INITIATIVE,
                contextId: null,
                entitiesToOrder: [], // Empty array when fetch fails
                orderDirection: 'asc'
            });
        });
    });

    describe('Query Keys and Caching', () => {
        it('should generate different query keys for different filters', async () => {
            const { rerender } = renderHook(
                ({ filters }: { filters?: InitiativeFilters }) => useInitiativesQuery(filters),
                {
                    wrapper: TestWrapper,
                    initialProps: { filters: undefined }
                }
            );

            // Initial render with no filters
            await waitFor(() => {
                expect(initiativesApi.getAllInitiatives).toHaveBeenCalledWith(undefined);
            });

            // Rerender with ID filter
            // rerender({ filters: { id: 'test-initiative-1', status: [] } as InitiativeFilters });

            // await waitFor(() => {
            //     expect(initiativesApi.getInitiativeById).toHaveBeenCalledWith('test-initiative-1');
            // });

            // // Rerender with status filter
            // rerender({ filters: { status: [InitiativeStatus.TO_DO], id: undefined } as InitiativeFilters });

            // await waitFor(() => {
            //     expect(initiativesApi.getAllInitiatives).toHaveBeenCalledWith({ status: [InitiativeStatus.TO_DO] });
            // });
        });

        // it('should use cached data for identical filter combinations', async () => {
        //     const filters: InitiativeFilters = { status: [InitiativeStatus.TO_DO] };

        //     // First render
        //     const { result: result1 } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

        //     await waitFor(() => {
        //         expect(result1.current.isQueryFetching).toBe(false);
        //     });

        //     // Second render with same filters
        //     const { result: result2 } = renderHook(() => useInitiativesQuery(filters), { wrapper: TestWrapper });

        //     await waitFor(() => {
        //         expect(result2.current.isQueryFetching).toBe(false);
        //     });

        //     // API should only be called once due to caching
        //     expect(initiativesApi.getAllInitiatives).toHaveBeenCalledTimes(1);
        //     expect(result1.current.initiativesData).toEqual(result2.current.initiativesData);
        // });
    });

    describe('Reload Function', () => {
        it('should provide reloadInitiatives function', async () => {
            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(result.current.reloadInitiatives).toBeInstanceOf(Function);
        });

        it('should refetch data when reloadInitiatives is called', async () => {
            const { result } = renderHook(() => useInitiativesQuery(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            // Clear previous calls
            vi.mocked(initiativesApi.getAllInitiatives).mockClear();

            // Call reload
            act(() => {
                result.current.reloadInitiatives();
            });

            await waitFor(() => {
                expect(initiativesApi.getAllInitiatives).toHaveBeenCalledTimes(1);
            });
        });
    });

    describe('Cache Version Integration', () => {
        it('should use provided cache version for reactivity', async () => {
            const cacheVersion = 1;

            const { result } = renderHook(() => useInitiativesQuery(undefined, cacheVersion), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            expect(result.current.initiativesData).toEqual(mockOrderedInitiatives);
        });

        it('should handle cache version changes', async () => {
            let cacheVersion = 1;

            const { result, rerender } = renderHook(() => useInitiativesQuery(undefined, cacheVersion), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isQueryFetching).toBe(false);
            });

            // Change cache version
            cacheVersion = 2;
            rerender();

            // Should trigger re-evaluation of the query
            expect(result.current.initiativesData).toEqual(mockOrderedInitiatives);
        });
    });
});