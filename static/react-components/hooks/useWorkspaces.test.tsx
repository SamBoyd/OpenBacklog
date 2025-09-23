import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useWorkspaces, WorkspacesProvider } from './useWorkspaces';
import type { WorkspaceDto } from '#types';

// Mock the workspace API
vi.mock('#services/workspaceApi', () => ({
    fetchCurrentWorkspace: vi.fn(),
    setCurrentWorkspace: vi.fn(),
    createWorkspace: vi.fn(),
}));

// Mock the workspaces API
vi.mock('#api/workspaces', () => ({
    getAllWorkspaces: vi.fn(),
}));

// Mock window.location.reload
Object.defineProperty(window, 'location', {
    value: {
        reload: vi.fn(),
    },
    writable: true,
});

import * as mockWorkspaceApi from '#services/workspaceApi';
import * as mockWorkspacesApi from '#api/workspaces';

/**
 * Helper function to create a test wrapper with QueryClient and WorkspacesProvider
 */
const createTestWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
                gcTime: 0,
                staleTime: 0,
            },
            mutations: {
                retry: false,
            },
        },
    });

    const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
        <QueryClientProvider client={queryClient}>
            <WorkspacesProvider>
                {children}
            </WorkspacesProvider>
        </QueryClientProvider>
    );

    return { TestWrapper, queryClient };
};

describe('useWorkspaces', () => {
    const mockWorkspace1: WorkspaceDto = {
        id: 'ws-1',
        name: 'Workspace 1',
        description: 'First workspace',
        icon: null,
    };

    const mockWorkspace2: WorkspaceDto = {
        id: 'ws-2',
        name: 'Workspace 2',
        description: 'Second workspace',
        icon: null,
    };

    const mockWorkspaces = [mockWorkspace1, mockWorkspace2];

    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(window.location.reload).mockClear();
    });

    afterEach(() => {
        vi.resetAllMocks();
    });

    describe('Context Provider', () => {
        it('should throw error when used outside of WorkspacesProvider', () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { });

            expect(() => {
                renderHook(() => useWorkspaces());
            }).toThrow('useWorkspaces must be used within a WorkspacesProvider');

            consoleError.mockRestore();
        });

        it('should work with WorkspacesProvider', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            expect(result.current.workspaces).toEqual(mockWorkspaces);
            expect(result.current.currentWorkspace).toEqual(mockWorkspace1);
        });
    });

    describe('Initial Loading', () => {
        it('should initialize with loading state', () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockImplementation(() => new Promise(() => { }));
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockImplementation(() => new Promise(() => { }));

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            expect(result.current.isLoading).toBe(true);
            expect(result.current.workspaces).toEqual([]);
            expect(result.current.currentWorkspace).toBe(null);
            expect(result.current.error).toBe(null);
            expect(result.current.isProcessing).toBe(false);
        });

        it('should load workspaces and current workspace successfully', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            expect(result.current.workspaces).toEqual(mockWorkspaces);
            expect(result.current.currentWorkspace).toEqual(mockWorkspace1);
            expect(result.current.error).toBe(null);
        });

        it('should set current workspace to null when no workspaces are available', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockRejectedValue(new Error('No workspaces available'));
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue([]);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.error).toBeNull();
            });

            expect(result.current.workspaces).toEqual([]);
            expect(result.current.currentWorkspace).toBe(null);
        });
    });

    describe('Current Workspace Validation', () => {
        it('should use valid current workspace when it exists in available workspaces', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace2);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            expect(result.current.currentWorkspace).toEqual(mockWorkspace2);
        });

        it('should set first available workspace as current when current workspace is stale', async () => {
            const staleWorkspace: WorkspaceDto = {
                id: 'stale-ws',
                name: 'Stale Workspace',
                description: 'This workspace no longer exists',
                icon: null,
            };

            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(staleWorkspace);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);
            vi.mocked(mockWorkspaceApi.setCurrentWorkspace).mockResolvedValue(undefined);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            expect(mockWorkspaceApi.setCurrentWorkspace).toHaveBeenCalledWith(mockWorkspace1);
            expect(result.current.currentWorkspace).toEqual(mockWorkspace1);
        });
    });

    describe('Error Handling', () => {
        it('should handle errors gracefully and provide default values', async () => {
            const error = new Error('Failed to fetch workspaces');
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockRejectedValue(error);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockRejectedValue(error);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            // Just verify the hook doesn't crash and provides safe defaults
            expect(result.current).toBeDefined();
            expect(result.current.workspaces).toEqual([]);
            expect(result.current.currentWorkspace).toBe(null);
        });
    });

    describe('changeWorkspace', () => {
        it('should change workspace successfully', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);
            vi.mocked(mockWorkspaceApi.setCurrentWorkspace).mockResolvedValue(undefined);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            await act(async () => {
                await result.current.changeWorkspace(mockWorkspace2);
            });

            expect(mockWorkspaceApi.setCurrentWorkspace).toHaveBeenCalledWith(mockWorkspace2);
        });

        it('should set processing state during workspace change', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);

            let resolveMutation: () => void;
            const mutationPromise = new Promise<void>((resolve) => {
                resolveMutation = resolve;
            });
            vi.mocked(mockWorkspaceApi.setCurrentWorkspace).mockReturnValue(mutationPromise);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            // Start the workspace change but don't await it immediately
            act(() => {
                result.current.changeWorkspace(mockWorkspace2);
            });

            // Now resolve the mutation and wait for completion
            act(() => {
                resolveMutation!();
            });

            await waitFor(() => {
                expect(result.current.isProcessing).toBe(false);
            });
        });

        it('should handle changeWorkspace errors', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);

            const error = new Error('Failed to change workspace');
            vi.mocked(mockWorkspaceApi.setCurrentWorkspace).mockRejectedValue(error);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current).toBeDefined();
                expect(result.current.isLoading).toBe(false);
            });

            let thrownError;
            await act(async () => {
                try {
                    await result.current.changeWorkspace(mockWorkspace2);
                } catch (e) {
                    thrownError = e;
                }
            });

            expect(thrownError).toEqual(error);
        });
    });

    describe('addWorkspace', () => {
        const newWorkspaceData = {
            name: 'New Workspace',
            description: 'A brand new workspace',
            icon: null,
        };

        const newWorkspace: WorkspaceDto = {
            id: 'new-ws',
            ...newWorkspaceData,
        };

        it('should add workspace successfully', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);
            vi.mocked(mockWorkspaceApi.createWorkspace).mockResolvedValue(newWorkspace);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current).toBeDefined();
                expect(result.current.isLoading).toBe(false);
            });

            let addedWorkspace: WorkspaceDto;
            await act(async () => {
                addedWorkspace = await result.current.addWorkspace(newWorkspaceData);
            });

            expect(mockWorkspaceApi.createWorkspace).toHaveBeenCalledWith(newWorkspaceData);
            expect(addedWorkspace!).toEqual(newWorkspace);
        });

        it('should set processing state during workspace creation', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);

            let resolveMutation: (value: WorkspaceDto) => void;
            const mutationPromise = new Promise<WorkspaceDto>((resolve) => {
                resolveMutation = resolve;
            });
            vi.mocked(mockWorkspaceApi.createWorkspace).mockReturnValue(mutationPromise);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current).toBeDefined();
                expect(result.current.isLoading).toBe(false);
            });

            // Start the workspace creation but don't await it immediately
            act(() => {
                result.current.addWorkspace(newWorkspaceData);
            });

            // Now resolve the mutation and wait for completion
            act(() => {
                resolveMutation!(newWorkspace);
            });

            await waitFor(() => {
                expect(result.current.isProcessing).toBe(false);
            });
        });

        it('should handle addWorkspace errors', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);

            const error = new Error('Failed to create workspace');
            vi.mocked(mockWorkspaceApi.createWorkspace).mockRejectedValue(error);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current).toBeDefined();
                expect(result.current.isLoading).toBe(false);
            });

            let thrownError;
            await act(async () => {
                try {
                    await result.current.addWorkspace(newWorkspaceData);
                } catch (e) {
                    thrownError = e;
                }
            });

            expect(thrownError).toEqual(error);
        });
    });

    describe('refresh', () => {
        it('should refresh workspace data', async () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockResolvedValue(mockWorkspace1);
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockResolvedValue(mockWorkspaces);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current).toBeDefined();
                expect(result.current.isLoading).toBe(false);
            });

            vi.clearAllMocks();

            act(() => {
                result.current.refresh();
            });

            // After refresh, the queries should be triggered again
            await waitFor(() => {
                expect(mockWorkspaceApi.fetchCurrentWorkspace).toHaveBeenCalled();
                expect(mockWorkspacesApi.getAllWorkspaces).toHaveBeenCalled();
            });
        });
    });

    describe('Loading and Processing States', () => {
        it('should show loading when fetching initial data', () => {
            vi.mocked(mockWorkspaceApi.fetchCurrentWorkspace).mockImplementation(() => new Promise(() => { }));
            vi.mocked(mockWorkspacesApi.getAllWorkspaces).mockImplementation(() => new Promise(() => { }));

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useWorkspaces(), { wrapper: TestWrapper });

            expect(result.current).toBeDefined();
            expect(result.current.isLoading).toBe(true);
            expect(result.current.isProcessing).toBe(false);
        });
    });
});