import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { useOptimisticMutation, createEntityListCacheUpdater, createEntityListRollback, OptimisticMutationConfig } from './useOptimisticMutation';

// Mock data types for testing
interface TestEntity {
    id: string;
    name: string;
    version: number;
}

// Test data used across multiple test suites
const initialData: TestEntity[] = [
    { id: '1', name: 'Entity 1', version: 1 },
    { id: '2', name: 'Entity 2', version: 1 },
];

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
 * @param {object} props - Component props
 * @param {ReactNode} props.children - Child components
 * @returns {React.ReactElement} Wrapped component
 */
const TestWrapper: React.FC<{ children: React.ReactNode; queryClient?: QueryClient }> = ({ 
    children, 
    queryClient = createTestQueryClient() 
}) => (
    <QueryClientProvider client={queryClient}>
        {children}
    </QueryClientProvider>
);

describe('useOptimisticMutation', () => {
    let queryClient: QueryClient;
    const queryKey = ['test-entities'];

    beforeEach(() => {
        queryClient = createTestQueryClient();
        // Pre-populate cache with initial data
        queryClient.setQueryData(queryKey, initialData);
    });

    afterEach(() => {
        vi.clearAllMocks();
        queryClient.clear();
    });

    it('should apply optimistic updates immediately', async () => {
        const mockMutationFn = vi.fn().mockResolvedValue({ id: '1', name: 'Updated Entity 1', version: 2 });
        const mockUpdateCache = vi.fn();
        
        const config: OptimisticMutationConfig<TestEntity, Error, Partial<TestEntity>> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey],
            createOptimisticData: (variables) => ({ id: '1', name: 'Optimistic Update', version: 1.5 } as TestEntity),
            updateCache: mockUpdateCache,
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        await act(async () => {
            result.current.mutate({ id: '1', name: 'Updated Entity 1' });
        });

        // Verify optimistic update was applied immediately
        expect(mockUpdateCache).toHaveBeenCalledWith(
            { id: '1', name: 'Optimistic Update', version: 1.5 },
            { id: '1', name: 'Updated Entity 1' },
            queryClient
        );

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        // Verify final update with server response
        expect(mockUpdateCache).toHaveBeenCalledWith(
            { id: '1', name: 'Updated Entity 1', version: 2 },
            { id: '1', name: 'Updated Entity 1' },
            queryClient
        );

        // Verify mutationFn was called with correct parameters
        expect(mockMutationFn).toHaveBeenCalledTimes(1);
        expect(mockMutationFn).toHaveBeenCalledWith({ id: '1', name: 'Updated Entity 1' });
    });

    it('should cancel queries before optimistic update', async () => {
        const mockMutationFn = vi.fn().mockResolvedValue({ id: '1', name: 'Updated', version: 2 });
        const cancelQueriesSpy = vi.spyOn(queryClient, 'cancelQueries');
        
        const config: OptimisticMutationConfig<TestEntity, Error, Partial<TestEntity>> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey, ['other-query']],
            createOptimisticData: () => ({ id: '1', name: 'Optimistic', version: 1.5 } as TestEntity),
            updateCache: vi.fn(),
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        await act(async () => {
            result.current.mutate({ id: '1', name: 'Updated' });
        });

        expect(cancelQueriesSpy).toHaveBeenCalledWith({ queryKey });
        expect(cancelQueriesSpy).toHaveBeenCalledWith({ queryKey: ['other-query'] });
    });

    it('should call mutationFn with correct parameters and timing', async () => {
        const mockMutationFn = vi.fn().mockImplementation(async (variables) => {
            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 50));
            return { ...variables, id: '1', serverField: 'computed', version: 2 };
        });
        const mockUpdateCache = vi.fn();
        
        const config: OptimisticMutationConfig<TestEntity, Error, Partial<TestEntity>> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey],
            createOptimisticData: (variables) => ({ id: '1', name: 'Optimistic', version: 1 } as TestEntity),
            updateCache: mockUpdateCache,
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        const variables = { name: 'Updated Entity', id: '1' };
        
        // Start mutation
        await act(async () => {
            result.current.mutate(variables);
        });

        // Verify optimistic update happened
        expect(mockUpdateCache).toHaveBeenCalledWith(
            { id: '1', name: 'Optimistic', version: 1 },
            variables,
            queryClient
        );

        // Verify mutationFn was called with exact variables
        expect(mockMutationFn).toHaveBeenCalledTimes(1);
        expect(mockMutationFn).toHaveBeenCalledWith(variables);

        // Wait for mutation to complete
        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        // Verify server response is applied
        expect(mockUpdateCache).toHaveBeenCalledWith(
            { name: 'Updated Entity', id: '1', serverField: 'computed', version: 2 },
            variables,
            queryClient
        );
    });

    it('should rollback optimistic update on error', async () => {
        const mockError = new Error('API Error');
        const mockMutationFn = vi.fn().mockRejectedValue(mockError);
        const mockRollbackCache = vi.fn();
        const mockCaptureContext = vi.fn().mockReturnValue({ previousData: initialData });
        
        const config: OptimisticMutationConfig<TestEntity, Error, Partial<TestEntity>, { previousData: TestEntity[] }> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey],
            createOptimisticData: () => ({ id: '1', name: 'Optimistic', version: 1.5 } as TestEntity),
            updateCache: vi.fn(),
            captureContext: mockCaptureContext,
            rollbackCache: mockRollbackCache,
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        act(() => {
            result.current.mutate({ id: '1', name: 'Updated' });
        });

        await waitFor(() => {
            expect(result.current.isError).toBe(true);
        });

        expect(mockCaptureContext).toHaveBeenCalledWith({ id: '1', name: 'Updated' }, queryClient);
        expect(mockRollbackCache).toHaveBeenCalledWith({ previousData: initialData }, queryClient);
    });

    it('should execute success callback after server response', async () => {
        const serverResponse = { id: '1', name: 'Server Response', version: 2 };
        const mockMutationFn = vi.fn().mockResolvedValue(serverResponse);
        const mockOnSuccess = vi.fn();
        
        const config: OptimisticMutationConfig<TestEntity, Error, Partial<TestEntity>> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey],
            createOptimisticData: () => ({ id: '1', name: 'Optimistic', version: 1.5 } as TestEntity),
            updateCache: vi.fn(),
            onSuccessCallback: mockOnSuccess,
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        const variables = { id: '1', name: 'Updated' };

        act(() => {
            result.current.mutate(variables);
        });

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        expect(mockOnSuccess).toHaveBeenCalledWith(serverResponse, variables, queryClient);
    });

    it('should use separate server response handler when provided', async () => {
        const serverResponse = { id: '1', name: 'Server Response', version: 2, serverOnly: true };
        const mockMutationFn = vi.fn().mockResolvedValue(serverResponse);
        const mockUpdateCache = vi.fn();
        const mockUpdateCacheWithServerResponse = vi.fn();
        
        const config: OptimisticMutationConfig<TestEntity, Error, Partial<TestEntity>> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey],
            createOptimisticData: () => ({ id: '1', name: 'Optimistic', version: 1 } as TestEntity),
            updateCache: mockUpdateCache,
            updateCacheWithServerResponse: mockUpdateCacheWithServerResponse,
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        const variables = { id: '1', name: 'Updated' };

        await act(async () => {
            await result.current.mutateAsync(variables);
        });

        // Verify optimistic update used regular updateCache
        expect(mockUpdateCache).toHaveBeenCalledWith(
            { id: '1', name: 'Optimistic', version: 1 },
            variables,
            queryClient
        );

        // Verify server response used separate handler
        expect(mockUpdateCacheWithServerResponse).toHaveBeenCalledWith(
            serverResponse,
            variables,
            queryClient
        );

        // Verify regular updateCache was NOT called for server response
        expect(mockUpdateCache).not.toHaveBeenCalledWith(
            serverResponse,
            variables,
            queryClient
        );
    });
});

describe('createEntityListCacheUpdater', () => {
    let queryClient: QueryClient;
    const queryKeys = [['entities'], ['entities', 'filtered']];

    beforeEach(() => {
        queryClient = createTestQueryClient();
        
        // Pre-populate both caches
        queryClient.setQueryData(queryKeys[0], initialData);
        queryClient.setQueryData(queryKeys[1], [initialData[0]]);
    });

    afterEach(() => {
        queryClient.clear();
    });

    it('should update entity in multiple cache keys', () => {
        const updater = createEntityListCacheUpdater<TestEntity>(queryKeys);
        const updatedEntity: TestEntity = { id: '1', name: 'Updated Entity', version: 2 };

        updater(updatedEntity, { id: '1' }, queryClient);

        // Check first cache
        const data1 = queryClient.getQueryData<TestEntity[]>(queryKeys[0]);
        expect(data1?.[0]).toEqual(updatedEntity);
        expect(data1?.[1]).toEqual(initialData[1]); // Other entities unchanged

        // Check second cache
        const data2 = queryClient.getQueryData<TestEntity[]>(queryKeys[1]);
        expect(data2?.[0]).toEqual(updatedEntity);
    });

    it('should use custom entity ID getter', () => {
        const customIdGetter = (entity: TestEntity) => entity.name;
        const updater = createEntityListCacheUpdater<TestEntity>(queryKeys, customIdGetter);
        
        const updatedEntity: TestEntity = { id: '999', name: 'Entity 1', version: 2 };

        updater(updatedEntity, {}, queryClient);

        const data = queryClient.getQueryData<TestEntity[]>(queryKeys[0]);
        expect(data?.[0]).toEqual(updatedEntity); // Found by name, not ID
    });
});

describe('createEntityListRollback', () => {
    let queryClient: QueryClient;
    const queryKeys = [['entities'], ['entities', 'filtered']];

    beforeEach(() => {
        queryClient = createTestQueryClient();
    });

    afterEach(() => {
        queryClient.clear();
    });

    it('should rollback multiple cache keys to previous data', () => {
        const rollback = createEntityListRollback<TestEntity>(
            (context) => context.queryKeys,
            (context) => context.previousData
        );

        // Set some modified data
        const modifiedData = [{ id: '1', name: 'Modified', version: 2 }];
        queryClient.setQueryData(queryKeys[0], modifiedData);
        queryClient.setQueryData(queryKeys[1], modifiedData);

        const context = {
            queryKeys,
            previousData: initialData,
        };

        rollback(context, queryClient);

        // Verify rollback
        expect(queryClient.getQueryData(queryKeys[0])).toEqual(initialData);
        expect(queryClient.getQueryData(queryKeys[1])).toEqual(initialData);
    });
});

describe('Integration Tests - Full Optimistic Flow', () => {
    let queryClient: QueryClient;
    const queryKey = ['items'];

    beforeEach(() => {
        queryClient = createTestQueryClient();
        queryClient.setQueryData(queryKey, []);
    });

    afterEach(() => {
        vi.clearAllMocks();
        queryClient.clear();
    });

    it('should handle create operation with temporary ID replacement', async () => {
        // Simulate create operation where optimistic item has temp ID and server returns real ID
        const mockMutationFn = vi.fn().mockImplementation(async (variables) => {
            await new Promise(resolve => setTimeout(resolve, 50));
            return {
                id: 'real-server-uuid',
                title: variables.title,
                created_at: '2025-01-15T10:00:00Z',
                updated_at: '2025-01-15T10:00:00Z',
                order: 1,
                parent_id: variables.parent_id,
            };
        });

        const mockUpdateCache = vi.fn();
        const mockUpdateCacheWithServerResponse = vi.fn();

        // Store items for verification
        let optimisticItem: any = null;
        let serverItem: any = null;

        const updateCache = (item: any) => {
            optimisticItem = item;
            mockUpdateCache(item);
        };

        const updateCacheWithServerResponse = (item: any) => {
            serverItem = item;
            mockUpdateCacheWithServerResponse(item);
        };

        const config: OptimisticMutationConfig<any, Error, any> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey],
            createOptimisticData: (variables) => ({
                id: `temp-${Date.now()}`,
                title: variables.title,
                parent_id: variables.parent_id,
                created_at: new Date().toISOString(),
                order: 0, // Optimistic guess
            }),
            updateCache: updateCache,
            updateCacheWithServerResponse: updateCacheWithServerResponse,
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        const variables = { title: 'New Item', parent_id: 'parent-123' };

        // Execute mutation
        await act(async () => {
            result.current.mutate(variables);
        });

        // Wait for optimistic update to be called
        await waitFor(() => {
            expect(mockUpdateCache).toHaveBeenCalled();
        });

        // Verify optimistic data
        expect(optimisticItem).toBeDefined();
        expect(optimisticItem.id).toMatch(/^temp-/);
        expect(optimisticItem.title).toBe('New Item');
        expect(optimisticItem.order).toBe(0); // Optimistic value

        // Wait for server response
        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        // Wait for server response handler to be called
        await waitFor(() => {
            expect(mockUpdateCacheWithServerResponse).toHaveBeenCalled();
        });

        // Verify server response data
        expect(serverItem).toBeDefined();
        expect(serverItem.id).toBe('real-server-uuid'); // Server ID replaced temp ID
        expect(serverItem.title).toBe('New Item');
        expect(serverItem.order).toBe(1); // Server computed value
        expect(serverItem.created_at).toBe('2025-01-15T10:00:00Z'); // Server timestamp

        // Verify mutation function was called correctly
        expect(mockMutationFn).toHaveBeenCalledWith(variables);
    });

    it('should handle update operation preserving server-computed fields', async () => {
        // Setup existing item in cache
        const existingItem = {
            id: 'existing-123',
            title: 'Original Title',
            created_at: '2025-01-10T08:00:00Z',
            updated_at: '2025-01-10T08:00:00Z',
            version: 1,
        };
        queryClient.setQueryData(queryKey, [existingItem]);

        const mockMutationFn = vi.fn().mockImplementation(async (variables) => {
            await new Promise(resolve => setTimeout(resolve, 30));
            return {
                ...existingItem,
                ...variables,
                updated_at: '2025-01-15T10:00:00Z', // Server updates timestamp
                version: 2, // Server increments version
            };
        });

        const mockUpdateCache = vi.fn();
        const mockUpdateCacheWithServerResponse = vi.fn();

        // Store items for verification
        let optimisticItem: any = null;
        let serverItem: any = null;

        const updateCache = (item: any) => {
            optimisticItem = item;
            mockUpdateCache(item);
        };

        const updateCacheWithServerResponse = (item: any) => {
            serverItem = item;
            mockUpdateCacheWithServerResponse(item);
        };

        const config: OptimisticMutationConfig<any, Error, any> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey],
            createOptimisticData: (variables, context) => {
                const existing = (context?.existingItems || queryClient.getQueryData(queryKey) as any[])?.[0];
                return existing ? { ...existing, ...variables } : null;
            },
            updateCache: updateCache,
            updateCacheWithServerResponse: updateCacheWithServerResponse,
            captureContext: () => ({
                existingItems: queryClient.getQueryData(queryKey),
            }),
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        const variables = { id: 'existing-123', title: 'Updated Title' };

        await act(async () => {
            result.current.mutate(variables);
        });

        // Wait for mutation to complete
        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        // Wait for server response handler to be called
        await waitFor(() => {
            expect(mockUpdateCacheWithServerResponse).toHaveBeenCalled();
        });

        // Verify server response has server-computed fields
        expect(serverItem).toBeDefined();
        expect(serverItem).toEqual({
            id: 'existing-123',
            title: 'Updated Title',
            created_at: '2025-01-10T08:00:00Z', // Preserved original
            updated_at: '2025-01-15T10:00:00Z', // Server updated
            version: 2, // Server incremented
        });

        expect(mockMutationFn).toHaveBeenCalledWith(variables);
    });

    it('should handle error rollback correctly in create operation', async () => {
        const mockMutationFn = vi.fn().mockRejectedValue(new Error('Server Error'));

        const config: OptimisticMutationConfig<any, Error, any, { previousItems: any[] }> = {
            mutationFn: mockMutationFn,
            queryKeysToCancel: () => [queryKey],
            createOptimisticData: (variables) => ({
                id: `temp-${Date.now()}`,
                title: variables.title,
            }),
            updateCache: (optimisticItem) => {
                queryClient.setQueryData(queryKey, (oldData: any[] = []) => [...oldData, optimisticItem]);
            },
            captureContext: () => ({
                previousItems: queryClient.getQueryData(queryKey) as any[] || [],
            }),
            rollbackCache: (context) => {
                queryClient.setQueryData(queryKey, context.previousItems);
            },
        };

        const { result } = renderHook(
            () => useOptimisticMutation(config),
            { wrapper: ({ children }) => <TestWrapper queryClient={queryClient}>{children}</TestWrapper> }
        );

        const initialCache = queryClient.getQueryData(queryKey) as any[] || [];
        const variables = { title: 'New Item' };

        // Execute mutation that will fail
        await act(async () => {
            result.current.mutate(variables);
        });

        await waitFor(() => {
            expect(result.current.isError).toBe(true);
        });

        // Verify cache was rolled back to initial state
        const finalCache = queryClient.getQueryData(queryKey) as any[] || [];
        expect(finalCache).toEqual(initialCache);

        expect(mockMutationFn).toHaveBeenCalledWith(variables);
    });
});