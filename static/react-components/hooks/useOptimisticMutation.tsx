import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { useCallback } from 'react';

/**
 * Configuration for optimistic mutation behavior
 * @template TData - The type of data returned by the mutation
 * @template TError - The type of error that can be thrown
 * @template TVariables - The type of variables passed to the mutation
 * @template TContext - The type of context returned from onMutate
 */
export interface OptimisticMutationConfig<TData, TError, TVariables, TContext = unknown> {
    /** The mutation function to call the API */
    mutationFn: (variables: TVariables) => Promise<TData>;
    
    /** Query keys that should be cancelled before optimistic update */
    queryKeysToCancel: (variables: TVariables) => any[][];
    
    /** Function to create optimistic data from variables */
    createOptimisticData: (variables: TVariables, previousData?: any) => TData | null;
    
    /** Function to update cache with optimistic data */
    updateCache: (optimisticData: TData, variables: TVariables, queryClient: any) => void;
    
    /** Function to update cache with server response (defaults to updateCache if not provided) */
    updateCacheWithServerResponse?: (serverData: TData, variables: TVariables, queryClient: any) => void;
    
    /** Function to rollback cache on error */
    rollbackCache?: (context: TContext, queryClient: any) => void;
    
    /** Function to handle successful mutation */
    onSuccessCallback?: (data: TData, variables: TVariables, queryClient: any) => void | Promise<void>;
    
    /** Function to capture context for potential rollback */
    captureContext?: (variables: TVariables, queryClient: any) => TContext;
}

/**
 * Custom hook for optimistic mutations with automatic cache updates and rollback
 * @template TData - The type of data returned by the mutation
 * @template TError - The type of error that can be thrown  
 * @template TVariables - The type of variables passed to the mutation
 * @template TContext - The type of context returned from onMutate
 * @param {OptimisticMutationConfig} config - Configuration for the optimistic mutation
 * @returns {object} Mutation object with mutate functions
 */
export function useOptimisticMutation<
    TData = unknown,
    TError = Error,
    TVariables = void,
    TContext = unknown
>(config: OptimisticMutationConfig<TData, TError, TVariables, TContext>) {
    const queryClient = useQueryClient();

    const mutation = useMutation<TData, TError, TVariables, TContext>({
        mutationFn: config.mutationFn,
        
        onMutate: async (variables) => {
            // Cancel outgoing queries for affected query keys
            const queryKeys = config.queryKeysToCancel(variables);
            await Promise.all(
                queryKeys.map(queryKey => 
                    queryClient.cancelQueries({ queryKey })
                )
            );

            // Capture context for potential rollback
            const context = config.captureContext?.(variables, queryClient);

            // Create and apply optimistic update
            const optimisticData = config.createOptimisticData(variables, context);
            if (optimisticData) {
                config.updateCache(optimisticData, variables, queryClient);
            }

            return context;
        },

        onSuccess: async (data, variables) => {
            // Update cache with real server response using dedicated function or fallback to updateCache
            const serverUpdateFn = config.updateCacheWithServerResponse || config.updateCache;
            serverUpdateFn(data, variables, queryClient);
            
            // Execute additional success callback
            await config.onSuccessCallback?.(data, variables, queryClient);
        },

        onError: (error, variables, context) => {
            console.error('[useOptimisticMutation] Error occurred:', error);
            
            // Rollback optimistic update
            if (context && config.rollbackCache) {
                config.rollbackCache(context, queryClient);
            }
        }
    });

    return mutation;
}

/**
 * Helper function to create a cache update function for entity lists
 * @template TEntity - The type of entity being updated
 * @param {any[]} queryKeys - Query keys to update
 * @param {(entity: TEntity) => any} getEntityId - Function to get entity ID
 * @returns {Function} Cache update function
 */
export function createEntityListCacheUpdater<TEntity extends { id: any }>(
    queryKeys: any[][],
    getEntityId: (entity: TEntity) => any = (entity) => entity.id
) {
    return (updatedEntity: TEntity, variables: any, queryClient: any) => {
        queryKeys.forEach(queryKey => {
            queryClient.setQueryData(queryKey, (oldData: TEntity[] = []) =>
                oldData.map(entity => 
                    getEntityId(entity) === getEntityId(updatedEntity) 
                        ? updatedEntity 
                        : entity
                )
            );
        });
    };
}

/**
 * Helper function to create a rollback function for entity lists
 * @template TEntity - The type of entity in the list
 * @param {(context: any) => any[][]} getQueryKeysFromContext - Function to get query keys from context
 * @param {(context: any) => TEntity[]} getPreviousDataFromContext - Function to get previous data from context
 * @returns {Function} Rollback function
 */
export function createEntityListRollback<TEntity>(
    getQueryKeysFromContext: (context: any) => any[][],
    getPreviousDataFromContext: (context: any) => TEntity[]
) {
    return (context: any, queryClient: any) => {
        const queryKeys = getQueryKeysFromContext(context);
        const previousData = getPreviousDataFromContext(context);
        
        queryKeys.forEach(queryKey => {
            if (previousData) {
                queryClient.setQueryData(queryKey, previousData);
            }
        });
    };
}

/**
 * Helper function to create a server response handler that replaces optimistic data
 * Useful for create operations where optimistic item has temp ID and server returns real ID
 * @template TEntity - The type of entity being handled
 * @param {any[][]} queryKeys - Query keys to update
 * @param {(optimisticEntity: TEntity, variables: any) => any} getOptimisticId - Function to get optimistic entity ID
 * @param {(entity: TEntity) => any} getEntityId - Function to get entity ID
 * @returns {Function} Server response cache updater
 */
export function createServerResponseReplacer<TEntity extends { id: any }>(
    queryKeys: any[][],
    getOptimisticId: (optimisticEntity: TEntity, variables: any) => any,
    getEntityId: (entity: TEntity) => any = (entity) => entity.id
) {
    return (serverEntity: TEntity, variables: any, queryClient: any) => {
        queryKeys.forEach(queryKey => {
            queryClient.setQueryData(queryKey, (oldData: TEntity[] = []) => {
                // Try to find and replace optimistic entity
                const optimisticEntityIndex = oldData.findIndex(entity => {
                    const entityOptimisticId = getOptimisticId(entity, variables);
                    return entityOptimisticId && entityOptimisticId.toString().startsWith('temp-');
                });
                
                if (optimisticEntityIndex >= 0) {
                    // Replace optimistic entity with server response
                    const newData = [...oldData];
                    newData[optimisticEntityIndex] = serverEntity;
                    return newData;
                } else {
                    // If optimistic entity not found, try to update by real ID or add new
                    const existingIndex = oldData.findIndex(entity => 
                        getEntityId(entity) === getEntityId(serverEntity)
                    );
                    
                    if (existingIndex >= 0) {
                        // Update existing entity
                        const newData = [...oldData];
                        newData[existingIndex] = serverEntity;
                        return newData;
                    } else {
                        // Add new entity (fallback case)
                        return [...oldData, serverEntity];
                    }
                }
            });
        });
    };
}

/**
 * Helper function to create a simple server response handler for entity lists
 * Uses the same logic as createEntityListCacheUpdater but designed for server responses
 * @template TEntity - The type of entity being updated
 * @param {any[]} queryKeys - Query keys to update
 * @param {(entity: TEntity) => any} getEntityId - Function to get entity ID
 * @returns {Function} Server response cache updater
 */
export function createServerResponseUpdater<TEntity extends { id: any }>(
    queryKeys: any[][],
    getEntityId: (entity: TEntity) => any = (entity) => entity.id
) {
    return (serverEntity: TEntity, variables: any, queryClient: any) => {
        queryKeys.forEach(queryKey => {
            queryClient.setQueryData(queryKey, (oldData: TEntity[] = []) =>
                oldData.map(entity => 
                    getEntityId(entity) === getEntityId(serverEntity) 
                        ? serverEntity 
                        : entity
                )
            );
        });
    };
}