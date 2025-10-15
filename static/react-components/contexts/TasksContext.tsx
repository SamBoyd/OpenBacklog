// hooks/useTasksContext.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useOptimisticMutation, createEntityListCacheUpdater, createEntityListRollback, createServerResponseUpdater } from '#hooks/useOptimisticMutation';
import {
    getAllTasks,
    getAllTasksForInitiatives,
    postTask,
    deleteTask as apiDeleteTask,
    getTaskById,
    createTask,
    moveTask,
    moveTaskToStatus as moveTaskToStatusApi
} from '#api/tasks';
import { 
    postChecklistItem, 
    deleteChecklistItem 
} from '#api/checklistItems';
import { TaskDto, ContextType, EntityType, OrderingDto, TaskStatus, ChecklistItemDto } from '#types';
import { useCallback, createContext, useContext, ReactNode, useState, useMemo, useRef, useEffect } from 'react';
import { useOrderings, OrderedEntity } from '#hooks/useOrderings';
import { useAiChat } from '#hooks/useAiChat';
import { LENS } from '#types';
import { SafeStorage } from '#hooks/useUserPreferences';
import { trackFirstTaskCreated } from '#services/tracking/onboarding';


// --- Context Definition ---
export interface TasksContextType {
    tasks: OrderedEntity<TaskDto>[];

    error: string | null;
    shouldShowSkeleton: boolean;
    isQueryFetching: boolean;
    isCreatingTask: boolean;
    isUpdatingTask: boolean;
    isDeletingTask: boolean;
    isPolling: boolean;

    updateTask: (task: Partial<TaskDto>) => Promise<TaskDto>;
    deleteTask: (taskId: string) => Promise<void>;
    reloadTasks: () => void;
    createTask: (
        task: Partial<TaskDto>
    ) => Promise<TaskDto>;
    invalidateTasks: () => void;
    setInitiativeId: (initiativeId: string | null | undefined) => void;
    setTaskId: (taskId: string | null | undefined) => void;
    startPolling: (intervalMs?: number) => void;
    stopPolling: () => void;
    reorderTask: (taskId: string, afterId: string | null, beforeId: string | null) => Promise<void>;
    moveTaskToStatus: (taskId: string, newStatus: TaskStatus, afterId: string | null, beforeId: string | null) => Promise<void>;
    
    // Granular checklist operations
    updateChecklistItem: (taskId: string, itemId: string, updates: Partial<ChecklistItemDto>) => Promise<ChecklistItemDto>;
    updateChecklistItemDebounced: (taskId: string, itemId: string, updates: Partial<ChecklistItemDto>, debounceMs?: number) => Promise<ChecklistItemDto>;
    addChecklistItem: (taskId: string, item: Omit<ChecklistItemDto, 'id' | 'task_id'>) => Promise<ChecklistItemDto>;
    removeChecklistItem: (taskId: string, itemId: string) => Promise<void>;
    reorderChecklistItems: (taskId: string, items: Array<Partial<ChecklistItemDto>>) => Promise<Partial<ChecklistItemDto>[]>;
}

const TasksContext = createContext<TasksContextType | undefined>(undefined);

// --- Provider Component ---
interface TasksProviderProps {
    children: ReactNode;
}

/**
 * Provider component for managing tasks state and interactions.
 * This should wrap the part of the application where tasks are relevant.
 * @param {TasksProviderProps} props - Component props.
 * @returns {React.ReactElement} The provider component.
 */
export function TasksProvider({ children }: TasksProviderProps) {
    const queryClient = useQueryClient();
    const [initiativeId, setInitiativeId] = useState<string | null | undefined>(undefined);
    const [taskId, setTaskId] = useState<string | null | undefined>(undefined);
    const [isPolling, setIsPolling] = useState(false);
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    
    // Cache version tracking to trigger re-renders when cache is manually updated
    const [cacheVersion, setCacheVersion] = useState(0);

    // Initialize AI chat hook for context cleanup
    // Use minimal values since we only need removeEntityFromContext
    const { removeEntityFromContext } = useAiChat({
        lens: LENS.TASKS,
        currentEntity: null
    });

    // Construct query key based on current filters
    const queryKey = useMemo(() => {
        if (taskId) return ['tasks', initiativeId, taskId];
        if (initiativeId) return ['tasks', initiativeId, null];
        return ['tasks', null, null];
    }, [taskId, initiativeId]);

    // Query for fetching tasks
    const {
        data: tasksData,
        isLoading: queryIsLoading,
        isPending: queryIsPending,
        isFetching: queryIsFetching,
        isError: queryIsError,
        error: queryError,
        refetch: reloadTasks,
    } = useQuery<TaskDto[], Error>({
        queryKey,
        queryFn: async () => {
            if (taskId) {
                return getTaskById(taskId).then(task => [task]);
            }
            if (initiativeId) {
                return getAllTasksForInitiatives(initiativeId);
            }
            return getAllTasks();
        },
        staleTime: 1000 * 60 * 5, // 5 minutes
    });

    // Create reactive data source that immediately reflects cache updates
    const currentTasksData = useMemo(() => {
        // Get the latest data from cache, fallback to rawData
        const latestData = queryClient.getQueryData<TaskDto[]>(queryKey);
        if (latestData) {
            return latestData;
        }
        return tasksData;
    }, [tasksData, cacheVersion, queryClient, queryKey]);

    // Add ordering functionality for tasks
    const { orderedEntities } = useOrderings<TaskDto>({
        contextType: ContextType.STATUS_LIST,
        entityType: EntityType.TASK,
        contextId: null,
        entitiesToOrder: currentTasksData ?? [],
        orderDirection: 'asc'
    });

    // Use ordered entities as the main tasks array
    const tasks = orderedEntities;

    const createTaskWithOrdering = async (
        task: Partial<TaskDto>
    ) => {
        const requiredFields: (keyof TaskDto)[] = ['title', 'initiative_id'];
        const missingFields = requiredFields.filter((field) => !task[field]);

        if (missingFields.length > 0) {
            throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
        }

        if (initiativeId && task.initiative_id !== initiativeId) {
            console.warn(`Task's initiative_id (${task.initiative_id}) does not match the hook's initiativeId (${initiativeId}). Task will be created, but might not appear in the current view immediately unless the query key matches.`);
        }

        const createdTask = await createTask(task);
        await reloadTasks();
        return createdTask;
    };

    // Mutation for creating tasks
    const createMutation = useMutation<TaskDto, Error, Partial<TaskDto>>({
        mutationFn: (task) => createTaskWithOrdering(task),
        onSuccess: async (data) => {
            queryClient.invalidateQueries({ queryKey: ['initiatives', { id: data.initiative_id }] });

            // Track first task creation for time-to-value metric
            const hasTrackedFirstTask = SafeStorage.safeGet('hasTrackedFirstTask', (val): val is boolean => typeof val === 'boolean', false);
            if (!hasTrackedFirstTask) {
                // Get signup timestamp from user account details cache
                const onboardingCompletedAt = SafeStorage.safeGet('onboarding_completed_at', (val): val is string => typeof val === 'string', null);
                trackFirstTaskCreated(onboardingCompletedAt || undefined);
                SafeStorage.safeSet('hasTrackedFirstTask', true);
            }
        }
    });

    // Mutation for updating tasks using optimistic updates
    const updateMutation = useOptimisticMutation<TaskDto, Error, Partial<TaskDto>, {
        previousTasks: TaskDto[] | undefined;
        queryKey: any[];
        previousStatus?: string;
    }>({
        mutationFn: postTask,
        
        queryKeysToCancel: (variables) => [queryKey],
        
        createOptimisticData: (updatedTaskData, context) => {
            const previousTasks = context?.previousTasks || queryClient.getQueryData<TaskDto[]>(queryKey);
            const existingTask = previousTasks?.find((task: TaskDto) => task.id === updatedTaskData.id);
            
            if (existingTask) {
                return { ...existingTask, ...updatedTaskData };
            }
            return null;
        },
        
        updateCache: (optimisticTask, variables) => {
            // Find the previous task to get old status for cache updates
            const previousTasks = queryClient.getQueryData<TaskDto[]>(queryKey);
            const existingTask = previousTasks?.find(task => task.id === optimisticTask.id);
            
            updateTaskInCache(optimisticTask, existingTask?.status);
        },
        
        updateCacheWithServerResponse: (serverTask, variables) => {
            // For server responses, we need to ensure all computed fields are preserved
            // and that the task properly replaces any optimistic data
            updateTaskInCache(serverTask, undefined); // No need to track old status for server responses
        },
        
        captureContext: (variables) => ({
            previousTasks: queryClient.getQueryData<TaskDto[]>(queryKey),
            queryKey,
        }),
        
        rollbackCache: (context) => {
            if (context?.previousTasks && context?.queryKey) {
                queryClient.setQueryData<TaskDto[]>(context.queryKey, context.previousTasks);
                setCacheVersion(prev => prev + 1);
            }
        },
        
        onSuccessCallback: async (data) => {
            // Invalidate related queries to trigger fresh data
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
            queryClient.invalidateQueries({ queryKey: ['initiatives', { id: data.initiative_id }] });
        },
    });

    // Mutation for deleting tasks
    const deleteMutation = useMutation<void, Error, string>({
        mutationFn: apiDeleteTask,
        onSuccess: (_, taskId) => {
            queryClient.setQueryData<TaskDto[]>(queryKey, (oldData = []) =>
                oldData.filter(task => task.id !== taskId)
            );
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
            queryClient.invalidateQueries({ queryKey: ['initiatives', { id: initiativeId }] });

            // Remove the deleted task from AI chat context
            try {
                removeEntityFromContext(taskId);
            } catch (error) {
                console.error('[TasksContext] Failed to remove task from AI chat context:', error);
            }
        },
        onError: (error) => {
            console.error('[TasksContext] deleteMutation.onError', error);
        },
    });

    // Memoize invalidateTasks callback
    const invalidateTasks = useCallback(() => {
        queryClient.invalidateQueries({ queryKey: ['tasks'] });
    }, [queryClient]);

    /**
     * Helper function to update task data in all relevant cache entries
     * @param {TaskDto} updatedTask - The updated task data
     * @param {string} [oldStatus] - The previous status if changed (for status-based cache updates)
     */
    const updateTaskInCache = useCallback((updatedTask: TaskDto, oldStatus?: string) => {
        // Update the specific task cache (if single task query exists)
        queryClient.setQueryData<TaskDto[]>(['tasks', initiativeId, updatedTask.id], [updatedTask]);
        
        // Update the general tasks query data
        queryClient.setQueryData<TaskDto[]>(queryKey, (oldData) => {
            if (!oldData) return oldData;
            return oldData.map(item => 
                item.id === updatedTask.id ? { ...item, ...updatedTask } : item
            );
        });

        // Handle status-based cache updates if status changed
        if (oldStatus && oldStatus !== updatedTask.status) {
            // Update other related query keys that might contain this task
            queryClient.setQueryData<TaskDto[]>(['tasks', updatedTask.initiative_id, null], (oldData) => {
                if (!oldData) return oldData;
                return oldData.map(item => 
                    item.id === updatedTask.id ? { ...item, ...updatedTask } : item
                );
            });

            // Update all tasks query as well
            queryClient.setQueryData<TaskDto[]>(['tasks', null, null], (oldData) => {
                if (!oldData) return oldData;
                return oldData.map(item => 
                    item.id === updatedTask.id ? { ...item, ...updatedTask } : item
                );
            });
        }
        
        // Increment cache version to trigger reactive data updates
        setCacheVersion(prev => prev + 1);
    }, [queryClient, queryKey, initiativeId, setCacheVersion]);

    // Polling functions
    const startPolling = useCallback((intervalMs: number = 5000) => {
        if (isPolling) return; // Already polling

        console.log('[TasksContext] starting polling')

        setIsPolling(true);

        const poll = async () => {
            try {
                // Reload tasks (orderings come embedded)
                await reloadTasks();
            } catch (error) {
                console.error('[TasksContext] polling error:', error);
            }

            pollingIntervalRef.current = setTimeout(poll, intervalMs);
        };

        // Start polling immediately
        poll();
    }, [isPolling, reloadTasks, initiativeId]);

    const stopPolling = useCallback(() => {
        console.log('[TasksContext] stopping polling')
        setIsPolling(false);
    }, []);

    // Cleanup polling when isPolling becomes false
    useEffect(() => {
        if (!isPolling && pollingIntervalRef.current) {
            console.log('[TasksContext] clearing timeout due to isPolling state change')
            clearTimeout(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
    }, [isPolling, pollingIntervalRef.current]);

    // Compute individual loading states
    const shouldShowSkeleton = queryIsLoading && !tasksData;
    const isQueryFetching = queryIsFetching;
    const isCreatingTask = createMutation.isPending;
    const isUpdatingTask = updateMutation.isPending;
    const isDeletingTask = deleteMutation.isPending;

    // Compute error state
    let error: string | null = null;
    if (queryError || queryIsError) error = 'Error loading tasks';
    else if (createMutation.error) error = `Error creating task: ${createMutation.error.message}`;
    else if (updateMutation.error) error = `Error updating task: ${updateMutation.error.message}`;
    else if (deleteMutation.error) error = `Error deleting task: ${deleteMutation.error.message}`;

    // Reordering functions
    const reorderTask = useCallback(async (taskId: string, afterId: string | null, beforeId: string | null) => {
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            const updatedTask = await moveTask(
                task.id,
                afterId,
                beforeId,
            );
            
            updateTaskInCache(updatedTask);
        }
    }, [tasks, moveTask, updateTaskInCache]);

    const moveTaskToStatus = useCallback(async (taskId: string, newStatus: TaskStatus, afterId: string | null, beforeId: string | null) => {
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            const updatedTask = await moveTaskToStatusApi(
                task.id,
                newStatus,
                afterId,
                beforeId
            );
            
            updateTaskInCache(updatedTask, task.status);
        }
    }, [tasks, moveTaskToStatusApi, updateTaskInCache]);

    // Optimistic mutation for updating a single checklist item
    const updateChecklistItemMutation = useOptimisticMutation<
        ChecklistItemDto,
        Error,
        {taskId: string, itemId: string, updates: Partial<ChecklistItemDto>},
        {previousTasks: TaskDto[] | undefined}
    >({
        mutationFn: ({taskId, itemId, updates}) => postChecklistItem({
            id: itemId,
            task_id: taskId,
            ...updates
        }),
        
        queryKeysToCancel: () => [queryKey],
        
        createOptimisticData: ({taskId, itemId, updates}, context) => {
            const previousTasks = context?.previousTasks || queryClient.getQueryData<TaskDto[]>(queryKey);
            const task = previousTasks?.find((t: TaskDto) => t.id === taskId);
            const existingItem = task?.checklist?.find((item: Partial<ChecklistItemDto>) => item.id === itemId);
            
            if (existingItem) {
                return { ...existingItem, ...updates } as ChecklistItemDto;
            }
            return null;
        },
        
        updateCache: (optimisticItem, {taskId}) => {
            if (!optimisticItem) return;
            
            queryClient.setQueryData<TaskDto[]>(queryKey, (oldTasks) => {
                if (!oldTasks) return oldTasks;
                
                return oldTasks.map(task => {
                    if (task.id === taskId) {
                        return {
                            ...task,
                            checklist: task.checklist?.map(item => 
                                item.id === optimisticItem.id ? optimisticItem : item
                            ) || []
                        };
                    }
                    return task;
                });
            });
            setCacheVersion(prev => prev + 1);
        },
        
        updateCacheWithServerResponse: (serverItem, {taskId}) => {
            queryClient.setQueryData<TaskDto[]>(queryKey, (oldTasks) => {
                if (!oldTasks) return oldTasks;
                
                return oldTasks.map(task => {
                    if (task.id === taskId) {
                        return {
                            ...task,
                            checklist: task.checklist?.map(item => 
                                item.id === serverItem.id ? serverItem : item
                            ) || []
                        };
                    }
                    return task;
                });
            });
            setCacheVersion(prev => prev + 1);
        },
        
        captureContext: () => ({
            previousTasks: queryClient.getQueryData<TaskDto[]>(queryKey)
        }),
        
        rollbackCache: (context) => {
            if (context?.previousTasks) {
                queryClient.setQueryData<TaskDto[]>(queryKey, context.previousTasks);
                setCacheVersion(prev => prev + 1);
            }
        }
    });

    // Optimistic mutation for adding a checklist item
    const addChecklistItemMutation = useOptimisticMutation<
        ChecklistItemDto,
        Error,
        {taskId: string, item: Omit<ChecklistItemDto, 'id' | 'task_id'>},
        {previousTasks: TaskDto[] | undefined}
    >({
        mutationFn: ({taskId, item}) => postChecklistItem({
            ...item,
            task_id: taskId,
        }),
        
        queryKeysToCancel: () => [queryKey],
        
        createOptimisticData: ({taskId, item}) => {
            return {
                id: `temp-${Date.now()}`,
                task_id: taskId,
                ...item
            } as ChecklistItemDto;
        },
        
        updateCache: (optimisticItem, {taskId}) => {
            if (!optimisticItem) return;
            
            queryClient.setQueryData<TaskDto[]>(queryKey, (oldTasks) => {
                if (!oldTasks) return oldTasks;
                
                return oldTasks.map(task => {
                    if (task.id === taskId) {
                        return {
                            ...task,
                            checklist: [...(task.checklist || []), optimisticItem]
                        };
                    }
                    return task;
                });
            });
            setCacheVersion(prev => prev + 1);
        },
        
        updateCacheWithServerResponse: (serverItem, {taskId}) => {
            queryClient.setQueryData<TaskDto[]>(queryKey, (oldTasks) => {
                if (!oldTasks) return oldTasks;
                
                return oldTasks.map(task => {
                    if (task.id === taskId) {
                        const updatedChecklist = task.checklist?.filter(item => 
                            !item.id?.startsWith('temp-')
                        ) || [];
                        return {
                            ...task,
                            checklist: [...updatedChecklist, serverItem]
                        };
                    }
                    return task;
                });
            });
            setCacheVersion(prev => prev + 1);
        },
        
        captureContext: () => ({
            previousTasks: queryClient.getQueryData<TaskDto[]>(queryKey)
        }),
        
        rollbackCache: (context) => {
            if (context?.previousTasks) {
                queryClient.setQueryData<TaskDto[]>(queryKey, context.previousTasks);
                setCacheVersion(prev => prev + 1);
            }
        }
    });

    // Optimistic mutation for removing a checklist item
    const removeChecklistItemMutation = useOptimisticMutation<
        void,
        Error,
        {taskId: string, itemId: string},
        {previousTasks: TaskDto[] | undefined}
    >({
        mutationFn: ({taskId, itemId}) => deleteChecklistItem(itemId),
        
        queryKeysToCancel: () => [queryKey],
        
        createOptimisticData: (_, itemId) => itemId, // Return null to trigger optimistic update
        
        updateCache: (_, {taskId, itemId}) => {
            queryClient.setQueryData<TaskDto[]>(queryKey, (oldTasks) => {
                if (!oldTasks) return oldTasks;
                
                console.log('[TasksContext] updateCache for removeChecklistItem', {taskId, itemId});
                
                return oldTasks.map(task => {
                    if (task.id === taskId) {
                        return {
                            ...task,
                            checklist: task.checklist?.filter(item => item.id !== itemId) || []
                        };
                    }
                    return task;
                });
            });
            setCacheVersion(prev => prev + 1);
        },
        
        updateCacheWithServerResponse: () => {
            // No additional server response update needed for delete
            console.log('[TasksContext] updateCacheWithServerResponse for removeChecklistItem - skipped');
        },
        
        captureContext: () => ({
            previousTasks: queryClient.getQueryData<TaskDto[]>(queryKey)
        }),
        
        rollbackCache: (context) => {
            if (context?.previousTasks) {
                queryClient.setQueryData<TaskDto[]>(queryKey, context.previousTasks);
                setCacheVersion(prev => prev + 1);
            }
        }
    });

    // Regular mutation for reordering checklist items (not optimistic due to complexity)
    const reorderChecklistItemsMutation = useMutation<
        Partial<ChecklistItemDto>[],
        Error,
        {taskId: string, items: Array<Partial<ChecklistItemDto>>}
    >({
        mutationFn: ({taskId, items}) => {
            const updatePromises = items.map((item) => 
                postChecklistItem({
                    ...item,
                    task_id: taskId,
                })
            );
            return Promise.all(updatePromises);
        },
        onSuccess: (updatedItems, {taskId}) => {
            queryClient.setQueryData<TaskDto[]>(queryKey, (oldTasks) => {
                if (!oldTasks) return oldTasks;
                
                return oldTasks.map(task => {
                    if (task.id === taskId) {
                        return {
                            ...task,
                            checklist: updatedItems
                        };
                    }
                    return task;
                });
            });
            setCacheVersion(prev => prev + 1);
        }
    });

    // Callback functions for granular checklist operations
    const updateChecklistItem = useCallback(async (taskId: string, itemId: string, updates: Partial<ChecklistItemDto>) => {
        console.log('[TasksContext] updateChecklistItem called:', {taskId, itemId, updates});
        const result = await updateChecklistItemMutation.mutateAsync({taskId, itemId, updates});
        console.log('[TasksContext] updateChecklistItem completed');
        return result;
    }, [updateChecklistItemMutation]);

    const addChecklistItem = useCallback(async (taskId: string, item: Omit<ChecklistItemDto, 'id' | 'task_id'>) => {
        return addChecklistItemMutation.mutateAsync({taskId, item});
    }, [addChecklistItemMutation]);

    const removeChecklistItem = useCallback(async (taskId: string, itemId: string) => {
        return removeChecklistItemMutation.mutateAsync({taskId, itemId});
    }, [removeChecklistItemMutation]);

    const reorderChecklistItems = useCallback(async (taskId: string, items: Array<Partial<ChecklistItemDto>>) => {
        return reorderChecklistItemsMutation.mutateAsync({taskId, items});
    }, [reorderChecklistItemsMutation]);

    // Debounced version of updateChecklistItem for title changes
    const debouncedUpdateTimeoutRef = useRef<{[key: string]: NodeJS.Timeout}>({});
    
    const updateChecklistItemDebounced = useCallback(async (
        taskId: string, 
        itemId: string, 
        updates: Partial<ChecklistItemDto>,
        debounceMs: number = 500
    ) => {
        const key = `${taskId}-${itemId}`;
        
        // Clear existing timeout for this item
        if (debouncedUpdateTimeoutRef.current[key]) {
            clearTimeout(debouncedUpdateTimeoutRef.current[key]);
        }
        
        // For immediate updates (like checkbox changes), don't debounce
        if (updates.is_complete !== undefined && Object.keys(updates).length === 1) {
            return updateChecklistItem(taskId, itemId, updates);
        }
        
        // For text changes, use debouncing
        return new Promise<ChecklistItemDto>((resolve, reject) => {
            debouncedUpdateTimeoutRef.current[key] = setTimeout(async () => {
                try {
                    const result = await updateChecklistItem(taskId, itemId, updates);
                    delete debouncedUpdateTimeoutRef.current[key];
                    resolve(result);
                } catch (error) {
                    delete debouncedUpdateTimeoutRef.current[key];
                    reject(error);
                }
            }, debounceMs);
        });
    }, [updateChecklistItem]);

    // Cleanup debounce timeouts on unmount
    useEffect(() => {
        return () => {
            Object.values(debouncedUpdateTimeoutRef.current).forEach(timeout => {
                clearTimeout(timeout);
            });
        };
    }, []);

    // Memoize context value
    const contextValue = useMemo<TasksContextType>(() => ({
        tasks,
        error,
        shouldShowSkeleton,
        isQueryFetching,
        isCreatingTask,
        isUpdatingTask,
        isDeletingTask,
        isPolling,
        createTask: createMutation.mutateAsync,
        updateTask: (task: Partial<TaskDto>) => {
            console.log('[TasksContext] updateTask (FULL TASK UPDATE) called:', task);
            console.trace('[TasksContext] updateTask call stack:');
            return updateMutation.mutateAsync(task);
        },
        deleteTask: deleteMutation.mutateAsync,
        reloadTasks,
        invalidateTasks,
        setInitiativeId,
        setTaskId,
        startPolling,
        stopPolling,
        reorderTask,
        moveTaskToStatus,
        updateChecklistItem,
        updateChecklistItemDebounced,
        addChecklistItem,
        removeChecklistItem,
        reorderChecklistItems,
    }), [
        tasks,
        error,
        shouldShowSkeleton,
        isQueryFetching,
        isCreatingTask,
        isUpdatingTask,
        isDeletingTask,
        isPolling,
        createMutation.mutateAsync,
        updateMutation.mutateAsync,
        deleteMutation.mutateAsync,
        reloadTasks,
        invalidateTasks,
        startPolling,
        stopPolling,
        reorderTask,
        moveTaskToStatus,
        updateChecklistItem,
        updateChecklistItemDebounced,
        addChecklistItem,
        removeChecklistItem,
        reorderChecklistItems,
    ]);

    return (
        <TasksContext.Provider value={contextValue}>
            {children}
        </TasksContext.Provider>
    );
}

// --- Consumer Hook ---

/**
 * Hook to interact with the Tasks Context.
 * @returns {TasksContextType} Object containing tasks state and functions.
 * @throws {Error} If used outside of TasksProvider
 */
export function useTasksContext(): TasksContextType {
    const context = useContext(TasksContext);

    if (context === undefined) {
        throw new Error('useTasksContext must be used within a TasksProvider');
    }

    return context;
}
