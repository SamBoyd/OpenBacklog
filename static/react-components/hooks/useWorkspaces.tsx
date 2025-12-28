import React, {
    createContext,
    useContext,
    useCallback,
    useMemo,
    ReactNode
} from 'react';
import {
    useQuery,
    useMutation,
    useQueryClient,
    UseQueryResult,
    UseMutationResult
} from '@tanstack/react-query';
import {
    fetchCurrentWorkspace,
    setCurrentWorkspace,
    createWorkspace
} from '#services/workspaceApi';
import { WorkspaceDto } from '#types';
import { getAllWorkspaces } from '#api/workspaces';

/**
 * Interface for the return value of useWorkspaces hook
 */
export interface WorkspacesHookResult {
    /** List of all available workspaces */
    workspaces: WorkspaceDto[];
    /** Currently selected workspace */
    currentWorkspace: WorkspaceDto | null;
    /** Whether workspaces data is being loaded */
    isLoading: boolean;
    /** Whether any workspace operation is in progress */
    isProcessing: boolean;
    /** Error that occurred during workspace operations, if any */
    error: Error | null;
    /** Function to change the current workspace */
    changeWorkspace: (workspace: WorkspaceDto) => Promise<void>;
    /** Function to add a new workspace */
    addWorkspace: (workspace: Omit<WorkspaceDto, 'id'>) => Promise<WorkspaceDto>;
    /** Function to manually refresh workspace data */
    refresh: () => void;
};

/**
 * Query keys for workspace-related queries
 */
const QUERY_KEYS = {
    workspaces: ['workspaces'] as const,
    currentWorkspace: ['workspaces', 'current'] as const,
} as const;

/**
 * Interface for the workspace context type
 */
export interface WorkspacesContextType {
    /** List of all available workspaces */
    workspaces: WorkspaceDto[];
    /** Currently selected workspace */
    currentWorkspace: WorkspaceDto | null;
    /** Whether workspaces data is being loaded */
    isLoading: boolean;
    /** Whether any workspace operation is in progress */
    isProcessing: boolean;
    /** Error that occurred during workspace operations, if any */
    error: Error | null;
    /** Function to change the current workspace */
    changeWorkspace: (workspace: WorkspaceDto) => Promise<void>;
    /** Function to add a new workspace */
    addWorkspace: (workspace: Omit<WorkspaceDto, 'id'>) => Promise<WorkspaceDto>;
    /** Function to manually refresh workspace data */
    refresh: () => void;
    /** TanStack Query result for workspaces (for advanced usage) */
    workspacesQuery: UseQueryResult<WorkspaceDto[], Error>;
    /** TanStack Query result for current workspace (for advanced usage) */
    currentWorkspaceQuery: UseQueryResult<WorkspaceDto, Error>;
    /** Change workspace mutation */
    changeWorkspaceMutation: UseMutationResult<void, Error, WorkspaceDto, unknown>;
    /** Add workspace mutation */
    addWorkspaceMutation: UseMutationResult<WorkspaceDto, Error, Omit<WorkspaceDto, 'id'>, unknown>;
};

/**
 * Default context value with warning functions
 */
const defaultContextValue: WorkspacesContextType = {
    workspaces: [],
    currentWorkspace: null,
    isLoading: false,
    isProcessing: false,
    error: null,
    changeWorkspace: async () => { console.warn('WorkspacesProvider not found'); },
    addWorkspace: async () => { console.warn('WorkspacesProvider not found'); throw new Error('WorkspacesProvider not found'); },
    refresh: () => { console.warn('WorkspacesProvider not found'); },
    workspacesQuery: {} as UseQueryResult<WorkspaceDto[], Error>,
    currentWorkspaceQuery: {} as UseQueryResult<WorkspaceDto, Error>,
    changeWorkspaceMutation: {} as UseMutationResult<void, Error, WorkspaceDto, unknown>,
    addWorkspaceMutation: {} as UseMutationResult<WorkspaceDto, Error, Omit<WorkspaceDto, 'id'>, unknown>,
};

/**
 * Create the workspace context
 */
const WorkspacesContext = createContext<WorkspacesContextType | undefined>(
    undefined
);

/**
 * Props for the WorkspacesProvider component
 */
export interface WorkspacesProviderProps {
    /** Child components to be wrapped by the provider */
    children: ReactNode;
}

/**
 * Provider component that manages and distributes workspace state using TanStack Query.
 * @param {WorkspacesProviderProps} props - Component props.
 * @returns {React.ReactElement} The provider component.
 */
export const WorkspacesProvider: React.FC<WorkspacesProviderProps> = ({ children }) => {
    const queryClient = useQueryClient();

    // Query for all workspaces
    const workspacesQuery = useQuery({
        queryKey: QUERY_KEYS.workspaces,
        queryFn: getAllWorkspaces,
        staleTime: 5 * 60 * 1000, // 5 minutes
        retry: 2,
        throwOnError: false, // Ensure errors are captured in error state
    });

    // Query for current workspace with validation logic
    const currentWorkspaceQuery = useQuery({
        queryKey: QUERY_KEYS.currentWorkspace,
        queryFn: async (): Promise<WorkspaceDto> => {
            try {
                const [currentWorkspace, allWorkspaces] = await Promise.all([
                    fetchCurrentWorkspace(),
                    getAllWorkspaces()
                ]);

                if (allWorkspaces.length === 0) {
                    throw new Error('No workspaces available');
                }

                // Check if current workspace exists in available workspaces
                const validWorkspace = allWorkspaces.find(ws => ws.id === currentWorkspace.id);

                if (validWorkspace) {
                    // Current workspace is valid, use the server version to ensure data consistency
                    return validWorkspace;
                } else {
                    // Current workspace is stale/deleted, set first available workspace as current
                    await setCurrentWorkspace(allWorkspaces[0]);

                    // Invalidate initiatives cache since workspace changed - prevents stale data
                    // from being served when a user logs in with a stale workspace cookie
                    queryClient.invalidateQueries({ queryKey: ['initiatives'] });

                    return allWorkspaces[0];
                }
            } catch (error) {
                throw error
            }
        },
        staleTime: 2 * 60 * 1000, // 2 minutes
        retry: 2,
        throwOnError: false, // Ensure errors are captured in error state
    });

    // Mutation for changing workspace
    const changeWorkspaceMutation = useMutation({
        mutationFn: async (workspace: WorkspaceDto) => {
            await setCurrentWorkspace(workspace);
        },
        onSuccess: () => {
            // Invalidate and refetch workspace queries
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.currentWorkspace });
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.workspaces });
            // Note: Removed page reload as requested in plan
        },
        onError: (error) => {
            console.error('Failed to change workspace:', error);
        },
        throwOnError: true, // Allow errors to be thrown to the caller
    });

    // Mutation for adding workspace
    const addWorkspaceMutation = useMutation({
        mutationFn: createWorkspace,
        onSuccess: (newWorkspace) => {
            // Update workspace list with optimistic update
            queryClient.setQueryData<WorkspaceDto[]>(QUERY_KEYS.workspaces, (old) => {
                return old ? [...old, newWorkspace] : [newWorkspace];
            });
            // Invalidate and refetch queries to ensure consistency
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.workspaces });
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.currentWorkspace });
        },
        onError: (error) => {
            console.error('Failed to create workspace:', error);
        },
        throwOnError: true, // Allow errors to be thrown to the caller
    });

    // Convenient wrapper functions
    const changeWorkspace = useCallback(async (workspace: WorkspaceDto): Promise<void> => {
        return changeWorkspaceMutation.mutateAsync(workspace);
    }, [changeWorkspaceMutation]);

    const addWorkspace = useCallback(async (workspace: Omit<WorkspaceDto, 'id'>): Promise<WorkspaceDto> => {
        return addWorkspaceMutation.mutateAsync(workspace);
    }, [addWorkspaceMutation]);

    const refresh = useCallback(() => {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.workspaces });
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.currentWorkspace });
    }, [queryClient]);

    // Compute derived state
    const workspaces = workspacesQuery.data || [];
    const currentWorkspace = currentWorkspaceQuery.data || null;
    const isLoading = workspacesQuery.isLoading || currentWorkspaceQuery.isLoading;
    const error = workspacesQuery.error || currentWorkspaceQuery.error;
    const isProcessing = changeWorkspaceMutation.isPending || addWorkspaceMutation.isPending;

    // Memoize the context value to prevent unnecessary re-renders
    const contextValue = useMemo(() => ({
        workspaces,
        currentWorkspace,
        isLoading,
        isProcessing,
        error,
        changeWorkspace,
        addWorkspace,
        refresh,
        workspacesQuery,
        currentWorkspaceQuery,
        changeWorkspaceMutation,
        addWorkspaceMutation,
    }), [
        workspaces,
        currentWorkspace,
        isLoading,
        isProcessing,
        error,
        changeWorkspace,
        addWorkspace,
        refresh,
        workspacesQuery,
        currentWorkspaceQuery,
        changeWorkspaceMutation,
        addWorkspaceMutation,
    ]);

    return (
        <WorkspacesContext.Provider value={contextValue}>
            {children}
        </WorkspacesContext.Provider>
    );
};

/**
 * Custom hook for managing workspace data and operations
 * @returns {WorkspacesHookResult} Object containing workspace data and operations
 */
export const useWorkspaces = (): WorkspacesHookResult => {
    const context = useContext(WorkspacesContext);

    if (context === undefined) {
        throw new Error('useWorkspaces must be used within a WorkspacesProvider');
    }

    // Return only the public interface, hiding TanStack Query internals
    return {
        workspaces: context.workspaces,
        currentWorkspace: context.currentWorkspace,
        isLoading: context.isLoading,
        isProcessing: context.isProcessing,
        error: context.error,
        changeWorkspace: context.changeWorkspace,
        addWorkspace: context.addWorkspace,
        refresh: context.refresh,
    };
};
