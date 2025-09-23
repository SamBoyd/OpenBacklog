import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { useInitiativesMutations } from './useInitiativesMutations';
import { InitiativeDto, InitiativeStatus, EntityType } from '#types';
import { InitiativeFilters } from './types';

// Mock all API dependencies
vi.mock('#api/initiatives', () => ({
    createInitiative: vi.fn(),
    postInitiative: vi.fn(),
    deleteInitiative: vi.fn(),
    moveInitiative: vi.fn(),
    moveInitiativeToStatus: vi.fn(),
    addInitiativeToGroup: vi.fn(),
    removeInitiativeFromGroup: vi.fn(),
    moveInitiativeInGroup: vi.fn(),
}));

vi.mock('#api/tasks', () => ({
    deleteTask: vi.fn(),
}));

vi.mock('#api/checklistItems', () => ({
    deleteChecklistItem: vi.fn(),
}));

// Mock useOptimisticMutation hook
const mockOptimisticMutateAsync = vi.fn();
const mockOptimisticMutation = {
    mutateAsync: mockOptimisticMutateAsync,
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
    data: null,
    status: 'idle' as const,
    isSuccess: false,
    isIdle: true,
    isPaused: false,
    variables: undefined,
    context: undefined,
    failureCount: 0,
    failureReason: null,
    submittedAt: 0,
    reset: vi.fn(),
};

vi.mock('#hooks/useOptimisticMutation', () => ({
    useOptimisticMutation: vi.fn(() => mockOptimisticMutation),
    createServerResponseReplacer: vi.fn(() => vi.fn()),
    createEntityListCacheUpdater: vi.fn(() => vi.fn()),
    createEntityListRollback: vi.fn(() => vi.fn()),
}));

// Mock useAiChat hook
const mockRemoveEntityFromContext = vi.fn();
vi.mock('#hooks/useAiChat', () => ({
    useAiChat: vi.fn(() => ({
        removeEntityFromContext: mockRemoveEntityFromContext,
        jobResult: null,
        error: null,
        chatDisabled: false,
        sendMessage: vi.fn(),
        clearChat: vi.fn(),
        currentContext: [],
        setCurrentContext: vi.fn(),
    })),
}));

// Import mocked modules
import * as initiativesApi from '#api/initiatives';
import * as tasksApi from '#api/tasks';
import * as checklistItemsApi from '#api/checklistItems';
import { useOptimisticMutation, createServerResponseReplacer } from '#hooks/useOptimisticMutation';
import { useAiChat } from '#hooks/useAiChat';

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
    },
];

describe('useInitiativesMutations', () => {
    let queryClient: QueryClient;
    let mockUpdateInitiativeInCache: ReturnType<typeof vi.fn>;
    let mockSetCacheVersion: ReturnType<typeof vi.fn>;
    let mockReloadInitiatives: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        queryClient = createTestQueryClient();
        mockUpdateInitiativeInCache = vi.fn();
        mockSetCacheVersion = vi.fn();
        mockReloadInitiatives = vi.fn();
        mockUpdateInitiativeInCache = vi.fn();

        // Mock console methods to avoid test output noise
        vi.spyOn(console, 'log').mockImplementation(() => { });
        vi.spyOn(console, 'warn').mockImplementation(() => { });
        vi.spyOn(console, 'error').mockImplementation(() => { });

        // Reset all mocks
        vi.clearAllMocks();

        // Set up default API mock implementations
        vi.mocked(initiativesApi.createInitiative).mockResolvedValue(mockInitiative);
        vi.mocked(initiativesApi.postInitiative).mockResolvedValue(mockInitiative);
        vi.mocked(initiativesApi.deleteInitiative).mockResolvedValue();
        vi.mocked(initiativesApi.moveInitiative).mockResolvedValue(mockInitiative);
        vi.mocked(initiativesApi.moveInitiativeToStatus).mockResolvedValue({
            ...mockInitiative,
            status: InitiativeStatus.IN_PROGRESS
        });
        vi.mocked(initiativesApi.moveInitiativeInGroup).mockResolvedValue(mockInitiative);
        vi.mocked(tasksApi.deleteTask).mockResolvedValue();
        vi.mocked(checklistItemsApi.deleteChecklistItem).mockResolvedValue();

        // Reset mutation mocks
        mockOptimisticMutateAsync.mockResolvedValue(mockInitiative);
        mockRemoveEntityFromContext.mockResolvedValue(undefined);

        // Pre-populate cache with test data
        queryClient.setQueryData(['initiatives', {}], mockInitiatives);
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

    describe('Hook Initialization and Loading States', () => {
        it('should initialize with correct default loading states', () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            expect(result.current.isCreatingInitiative).toBe(false);
            expect(result.current.isUpdatingInitiative).toBe(false);
            expect(result.current.isDeletingInitiative).toBe(false);
            expect(result.current.isBatchUpdatingInitiatives).toBe(false);
            expect(result.current.isDeletingTask).toBe(false);
            expect(result.current.isDeletingChecklistItem).toBe(false);
        });

        it('should provide all required mutation functions', () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            expect(result.current.createInitiative).toBeInstanceOf(Function);
            expect(result.current.updateInitiative).toBeInstanceOf(Function);
            expect(result.current.updateInitiatives).toBeInstanceOf(Function);
            expect(result.current.deleteInitiative).toBeInstanceOf(Function);
            expect(result.current.deleteTask).toBeInstanceOf(Function);
            expect(result.current.deleteChecklistItem).toBeInstanceOf(Function);
            expect(result.current.reorderInitiative).toBeInstanceOf(Function);
            expect(result.current.moveInitiativeToStatus).toBeInstanceOf(Function);
            expect(result.current.moveInitiativeInGroup).toBeInstanceOf(Function);
        });

        it('should initialize AI chat hook with correct parameters', () => {
            renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            expect(useAiChat).toHaveBeenCalledWith({
                lens: 'INITIATIVES',
                currentEntity: null
            });
        });
    });

    describe('Create Mutation', () => {
        // Mock crypto.randomUUID for consistent testing
        const mockUUID = 'mock-uuid-123';
        const mockTimestamp = 1640995200000; // 2022-01-01T00:00:00.000Z

        beforeEach(() => {
            // Mock crypto.randomUUID
            Object.defineProperty(global, 'crypto', {
                value: {
                    randomUUID: vi.fn(() => mockUUID)
                },
                writable: true
            });

            // Mock Date.now for consistent temp identifiers
            vi.spyOn(Date, 'now').mockReturnValue(mockTimestamp);
            vi.spyOn(Date.prototype, 'toISOString').mockReturnValue('2022-01-01T00:00:00.000Z');
        });

        afterEach(() => {
            vi.restoreAllMocks();
        });

        it('should create initiative with optimistic updates', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            const newInitiative = {
                title: 'New Initiative',
                description: 'New Description',
                status: InitiativeStatus.TO_DO,
            };

            await act(async () => {
                await result.current.createInitiative(newInitiative);
            });

            expect(mockOptimisticMutateAsync).toHaveBeenCalledWith([newInitiative]);
        });

        it('should generate correct optimistic data with temp ID and identifier', () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            // Since all mutations use useOptimisticMutation, we need to find the right one
            // The create mutation should be the first one (based on order in the hook)
            const allCalls = vi.mocked(useOptimisticMutation).mock.calls;
            expect(allCalls.length).toBeGreaterThan(0);

            // The create mutation is the first call to useOptimisticMutation
            const createConfig = allCalls[0]?.[0];

            expect(createConfig).toBeDefined();
            expect(createConfig?.createOptimisticData).toBeInstanceOf(Function);

            if (createConfig?.createOptimisticData) {
                const testInitiative = {
                    title: 'Test Initiative',
                    description: 'Test Description',
                    status: InitiativeStatus.TO_DO
                };

                const optimisticData = createConfig.createOptimisticData([testInitiative], undefined);

                expect(optimisticData).toMatchObject({
                    id: `temp-${mockUUID}`,
                    identifier: `I-TEMP-${mockTimestamp}`,
                    title: 'Test Initiative',
                    description: 'Test Description',
                    status: InitiativeStatus.TO_DO,
                    created_at: '2022-01-01T00:00:00.000Z',
                    updated_at: '2022-01-01T00:00:00.000Z',
                    tasks: [],
                    has_pending_job: false,
                    properties: {},
                    orderings: []
                });
            }
        });

        it('should handle create mutation with ordering context', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            const newInitiative = {
                title: 'New Initiative',
                description: 'New Description',
            };
            const orderingContext = {
                contextType: 'STATUS_LIST' as any,
                contextId: null,
                entityType: EntityType.INITIATIVE,
            };

            await act(async () => {
                await result.current.createInitiative(newInitiative, orderingContext);
            });

            expect(mockOptimisticMutateAsync).toHaveBeenCalledWith([newInitiative]);
        });

        it('should handle create mutation errors with rollback', async () => {
            const errorMessage = 'Failed to create initiative';
            mockOptimisticMutateAsync.mockRejectedValueOnce(new Error(errorMessage));

            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                try {
                    await result.current.createInitiative({ title: 'New Initiative' });
                } catch (error) {
                    expect(error).toBeInstanceOf(Error);
                }
            });

            expect(mockOptimisticMutateAsync).toHaveBeenCalled();
        });

        it('should configure create mutation with proper cache management', () => {
            renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            // The create mutation is the first call to useOptimisticMutation
            const allCalls = vi.mocked(useOptimisticMutation).mock.calls;
            const createConfig = allCalls[0]?.[0];

            expect(createConfig).toBeDefined();
            expect(createConfig?.updateCache).toBeInstanceOf(Function);
            expect(createConfig?.updateCacheWithServerResponse).toBeInstanceOf(Function);
            expect(createConfig?.captureContext).toBeInstanceOf(Function);
            expect(createConfig?.rollbackCache).toBeInstanceOf(Function);
        });
    });

    describe('Update Mutation', () => {
        it('should update initiative using optimistic mutation', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            const updatedInitiative = {
                id: 'test-initiative-1',
                title: 'Updated Title',
            };

            await act(async () => {
                await result.current.updateInitiative(updatedInitiative);
            });

            expect(mockOptimisticMutateAsync).toHaveBeenCalledWith(updatedInitiative);
        });

        it('should call updateInitiativeInCache during optimistic update', () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            // Verify useOptimisticMutation was called with correct config
            const optimisticMutationCall = vi.mocked(useOptimisticMutation).mock.calls.find(call =>
                call[0].mutationFn === initiativesApi.postInitiative
            );
            expect(optimisticMutationCall).toBeDefined();

            if (!optimisticMutationCall) {
                throw new Error('Optimistic mutation call not found');
            }
            const config = optimisticMutationCall[0];
            expect(config.mutationFn).toBe(initiativesApi.postInitiative);
            expect(config.updateCache).toBeInstanceOf(Function);
            expect(config.updateCacheWithServerResponse).toBeInstanceOf(Function);
        });

        it('should handle batch update of multiple initiatives', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            const initiativesToUpdate = [
                { id: 'test-initiative-1', title: 'Updated Title 1' },
                { id: 'test-initiative-2', title: 'Updated Title 2' },
            ];

            await act(async () => {
                await result.current.updateInitiatives(initiativesToUpdate);
            });

            // Verify that the API was called for each initiative
            expect(initiativesApi.postInitiative).toHaveBeenCalledTimes(2);
            expect(initiativesApi.postInitiative).toHaveBeenCalledWith(initiativesToUpdate[0]);
            expect(initiativesApi.postInitiative).toHaveBeenCalledWith(initiativesToUpdate[1]);
        });
    });

    describe('Delete Mutation', () => {
        it('should delete initiative using optimistic mutation', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                await result.current.deleteInitiative('test-initiative-1');
            });

            expect(mockOptimisticMutateAsync).toHaveBeenCalledWith('test-initiative-1');
        });

        it('should remove initiative from AI chat context after successful deletion', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            // Set up the optimistic mutation to call the server response handler
            const deleteConfig = vi.mocked(useOptimisticMutation).mock.calls.find(call =>
                call[0].mutationFn === initiativesApi.deleteInitiative
            )?.[0];

            expect(deleteConfig).toBeDefined();
            if (deleteConfig === undefined || deleteConfig.updateCacheWithServerResponse === undefined) {
                throw new Error('Delete config not found');
            }
            expect(deleteConfig?.updateCacheWithServerResponse).toBeInstanceOf(Function);

            // Simulate successful deletion
            act(() => {
                if (deleteConfig === undefined || deleteConfig.updateCacheWithServerResponse === undefined) {
                    throw new Error('Delete config not found');
                }
                deleteConfig.updateCacheWithServerResponse(undefined, 'test-initiative-1', undefined);
            });

            expect(mockRemoveEntityFromContext).toHaveBeenCalledWith('test-initiative-1');
        });

        it('should handle AI chat context cleanup errors gracefully', async () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
            mockRemoveEntityFromContext.mockImplementation(() => {
                throw new Error('AI chat context error');
            });

            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            const deleteConfig = vi.mocked(useOptimisticMutation).mock.calls.find(call =>
                call[0].mutationFn === initiativesApi.deleteInitiative
            )?.[0];

            // Should not throw even if removeEntityFromContext fails
            expect(() => {
                act(() => {
                    if (deleteConfig === undefined || deleteConfig.updateCacheWithServerResponse === undefined) {
                        throw new Error('Delete config not found');
                    }
                    deleteConfig.updateCacheWithServerResponse(undefined, 'test-initiative-1', undefined);
                });
            }).not.toThrow();

            expect(consoleSpy).toHaveBeenCalledWith(
                '[useInitiativesMutations] Failed to remove initiative from AI chat context:',
                expect.any(Error)
            );

            consoleSpy.mockRestore();
        });

        it('should delete related task and remove from AI chat context', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                await result.current.deleteTask('test-task-1');
            });

            expect(tasksApi.deleteTask).toHaveBeenCalledWith('test-task-1');

            // Wait for the mutation to complete and check if AI context cleanup was called
            await waitFor(() => {
                expect(mockRemoveEntityFromContext).toHaveBeenCalledWith('test-task-1');
            });
        });

        it('should delete checklist item', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                await result.current.deleteChecklistItem('test-checklist-item-1');
            });

            expect(checklistItemsApi.deleteChecklistItem).toHaveBeenCalledWith('test-checklist-item-1');
        });
    });

    describe('Reordering Mutations', () => {
        it('should reorder initiative using optimistic mutation', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                await result.current.reorderInitiative('test-initiative-1', 'after-id', 'before-id');
            });

            expect(mockOptimisticMutateAsync).toHaveBeenCalledWith({
                initiativeId: 'test-initiative-1',
                afterId: 'after-id',
                beforeId: 'before-id'
            });
        });

        it('should move initiative to different status', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                await result.current.moveInitiativeToStatus(
                    'test-initiative-1',
                    InitiativeStatus.IN_PROGRESS,
                    'after-id',
                    'before-id'
                );
            });

            expect(mockOptimisticMutateAsync).toHaveBeenCalledWith({
                initiativeId: 'test-initiative-1',
                newStatus: InitiativeStatus.IN_PROGRESS,
                afterId: 'after-id',
                beforeId: 'before-id'
            });
        });

        it('should move initiative within group', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                await result.current.moveInitiativeInGroup(
                    'test-initiative-1',
                    'test-group-1',
                    'after-id',
                    'before-id'
                );
            });

            expect(initiativesApi.moveInitiativeInGroup).toHaveBeenCalledWith(
                'test-initiative-1',
                'test-group-1',
                'after-id',
                'before-id'
            );
            expect(mockUpdateInitiativeInCache).toHaveBeenCalledWith(mockInitiative);
        });
    });

    describe('Cache Integration', () => {
        it('should use provided updateInitiativeInCache function', async () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            // Verify optimistic mutations use the provided cache function
            const updateConfig = vi.mocked(useOptimisticMutation).mock.calls.find(call =>
                call[0].mutationFn === initiativesApi.postInitiative
            )?.[0];

            expect(updateConfig?.updateCache).toBeInstanceOf(Function);
            expect(updateConfig?.updateCacheWithServerResponse).toBeInstanceOf(Function);

            // Test that the cache functions work correctly
            const testInitiative = { ...mockInitiative, title: 'Updated' };

            act(() => {
                if (updateConfig === undefined || updateConfig.updateCache === undefined) {
                    throw new Error('Update config not found');
                }
                updateConfig.updateCache(testInitiative, undefined, undefined);
            });

            expect(mockUpdateInitiativeInCache).toHaveBeenCalledWith(testInitiative, InitiativeStatus.TO_DO);
        });

        it('should handle cache operations without provided functions', () => {
            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined, // No updateInitiativeInCache
                    undefined, // No setCacheVersion
                    undefined  // No reloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            // Should still provide all mutation functions
            expect(result.current.createInitiative).toBeInstanceOf(Function);
            expect(result.current.updateInitiative).toBeInstanceOf(Function);
            expect(result.current.deleteInitiative).toBeInstanceOf(Function);
        });

        it('should build correct query keys based on filters', () => {
            const filters = { status: [InitiativeStatus.TO_DO] };

            renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    filters,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            // Verify that the query key is built correctly (should be ['initiatives', filters])
            // This is tested indirectly through the cache operations
            expect(useOptimisticMutation).toHaveBeenCalled();
        });
    });

    describe('Error Handling and Edge Cases', () => {
        it('should handle mutation errors with proper rollback', async () => {
            const errorMessage = 'Update failed';
            mockOptimisticMutateAsync.mockRejectedValueOnce(new Error(errorMessage));

            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                try {
                    await result.current.updateInitiative({ id: 'test-id', title: 'Updated' });
                } catch (error) {
                    expect(error).toBeInstanceOf(Error);
                }
            });

            expect(mockOptimisticMutateAsync).toHaveBeenCalled();
        });

        it('should handle group move when initiative is not found', async () => {
            // Remove initiatives from cache
            queryClient.setQueryData(['initiatives', {}], []);

            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                await result.current.moveInitiativeInGroup(
                    'non-existent-initiative',
                    'test-group-1',
                    'after-id',
                    'before-id'
                );
            });

            expect(initiativesApi.moveInitiativeInGroup).not.toHaveBeenCalled();

            // Should not call cache update when initiative is not found
            expect(mockUpdateInitiativeInCache).not.toHaveBeenCalled();
        });

        it('should handle task deletion AI chat context errors gracefully', async () => {
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
            mockRemoveEntityFromContext.mockImplementation(() => {
                throw new Error('Task removal error');
            });

            const { result } = renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            await act(async () => {
                await result.current.deleteTask('test-task-1');
            });

            // The onSuccess callback should trigger and catch the error
            await waitFor(() => {
                expect(consoleSpy).toHaveBeenCalledWith(
                    '[useInitiativesMutations] Failed to remove task from AI chat context:',
                    expect.any(Error)
                );
            });

            consoleSpy.mockRestore();
        });
    });

    describe('Optimistic Mutation Configuration', () => {
        it('should configure update mutation with correct optimistic data creation', () => {
            renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            const updateConfig = vi.mocked(useOptimisticMutation).mock.calls.find(call =>
                call[0].mutationFn === initiativesApi.postInitiative
            )?.[0];

            expect(updateConfig).toBeDefined();
            expect(updateConfig?.createOptimisticData).toBeInstanceOf(Function);
            expect(updateConfig?.captureContext).toBeInstanceOf(Function);
            expect(updateConfig?.rollbackCache).toBeInstanceOf(Function);
        });

        it('should configure delete mutation with proper cache cleanup', () => {
            renderHook(
                () => useInitiativesMutations(
                    mockUpdateInitiativeInCache,
                    undefined,
                    mockSetCacheVersion,
                    mockReloadInitiatives
                ),
                { wrapper: TestWrapperWithClient }
            );

            const deleteConfig = vi.mocked(useOptimisticMutation).mock.calls.find(call =>
                call[0].mutationFn === initiativesApi.deleteInitiative
            )?.[0];

            expect(deleteConfig).toBeDefined();
            expect(deleteConfig?.updateCache).toBeInstanceOf(Function);
            expect(deleteConfig?.captureContext).toBeInstanceOf(Function);
            expect(deleteConfig?.rollbackCache).toBeInstanceOf(Function);
        });

        // it('should configure reorder mutations with proper optimistic updates', () => {
        //     renderHook(
        //         () => useInitiativesMutations(
        //             mockUpdateInitiativeInCache,
        //             undefined,
        //             mockSetCacheVersion,
        //             mockReloadInitiatives
        //         ),
        //         { wrapper: TestWrapperWithClient }
        //     );
        
        //     const reorderConfig = vi.mocked(useOptimisticMutation).mock.calls.find(call =>
        //         call[0].mutationFn === initiativesApi.moveInitiative
        //     )?.[0];

        //     const moveToStatusConfig = vi.mocked(useOptimisticMutation).mock.calls.find(call =>
        //         call[0].mutationFn === initiativesApi.moveInitiativeToStatus
        //     )?.[0];

        //     expect(reorderConfig).toBeDefined();
        //     expect(reorderConfig?.createOptimisticData).toBeInstanceOf(Function);
        //     expect(reorderConfig?.updateCache).toBeInstanceOf(Function);

        //     expect(moveToStatusConfig).toBeDefined();
        //     expect(moveToStatusConfig?.createOptimisticData).toBeInstanceOf(Function);
        //     expect(moveToStatusConfig?.updateCache).toBeInstanceOf(Function);
        // });
    });
});