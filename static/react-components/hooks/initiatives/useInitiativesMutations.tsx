import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useOptimisticMutation, createServerResponseReplacer } from '#hooks/useOptimisticMutation';
import { useCallback } from 'react';
import {
  createInitiative,
  postInitiative,
  deleteInitiative as apiDeleteInitiative,
  moveInitiative as moveInitiativeApi,
  moveInitiativeToStatus as moveInitiativeToStatusApi,
  moveInitiativeInGroup as apiMoveInitiativeInGroup,
} from '#api/initiatives';
import { deleteTask as apiDeleteTask } from '#api/tasks';
import { deleteChecklistItem as apiDeleteChecklistItem } from '#api/checklistItems';
import { InitiativeDto, InitiativeStatus, EntityType } from '#types';
import { InitiativesMutationOperations, InitiativeFilters, InitiativeMutationContext } from './types';
import { SafeStorage } from '#hooks/useUserPreferences';
import { trackFirstInitiativeCreated } from '#services/tracking/onboarding';

/**
 * Hook for managing all initiative mutation operations
 * @param {InitiativeFilters} [filters] - Current filters for building query keys
 * @param {Function} updateInitiativeInCache - Function to update initiative in cache
 * @param {Function} setCacheVersion - Function to increment cache version
 * @param {Function} reloadInitiatives - Function to reload initiatives
 * @returns {InitiativesMutationOperations} All mutation operations and loading states
 */
export function useInitiativesMutations(
  updateInitiativeInCache: (initiative: InitiativeDto, oldStatus?: string) => void,
  filters?: InitiativeFilters,
  setCacheVersion?: (fn: (prev: number) => number) => void,
  reloadInitiatives?: () => void
): InitiativesMutationOperations {
  const queryClient = useQueryClient();

  // Build the main query key
  const queryKey = ['initiatives', filters ?? {}];

  // CREATE MUTATION
  const generateTempInitiativeData = (initiative: Partial<InitiativeDto>): InitiativeDto => {
    const tempId = `temp-${crypto.randomUUID()}`;
    const tempIdentifier = `I-TEMP-${Date.now()}`;

    return {
      id: tempId,
      identifier: tempIdentifier,
      user_id: initiative.user_id || '',
      title: initiative.title || '',
      description: initiative.description || '',
      status: initiative.status || 'BACKLOG',
      type: initiative.type || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      tasks: initiative.tasks || [],
      has_pending_job: false,
      properties: initiative.properties || {},
      orderings: []
    };
  };

  const createMutation = useOptimisticMutation<InitiativeDto, Error, [Partial<InitiativeDto>], InitiativeMutationContext>({
    mutationFn: ([initiative]) => createInitiative(initiative),

    queryKeysToCancel: () => [queryKey],

    createOptimisticData: ([initiative], context) => {
      return generateTempInitiativeData(initiative);
    },

    updateCache: (optimisticInitiative) => {
      queryClient.setQueryData<InitiativeDto[]>(queryKey, (oldData) => {
        if (!oldData) return [optimisticInitiative];
        return [optimisticInitiative, ...oldData];
      });
      setCacheVersion?.(prev => prev + 1);
    },

    updateCacheWithServerResponse: createServerResponseReplacer<InitiativeDto>(
      [queryKey],
      (optimisticEntity) => optimisticEntity.id,
      (entity) => entity.id
    ),

    captureContext: () => ({
      previousInitiatives: queryClient.getQueryData<InitiativeDto[]>(queryKey),
      queryKey
    }),

    rollbackCache: (context) => {
      if (context?.previousInitiatives) {
        queryClient.setQueryData<InitiativeDto[]>(queryKey, context.previousInitiatives);
        setCacheVersion?.(prev => prev + 1);
      }
    },

    onSuccessCallback: async (data) => {
      // queryClient.invalidateQueries({ queryKey: ['initiatives'] });
      // queryClient.invalidateQueries({ queryKey: ['initiatives', { status: data.status }] });
      // queryClient.invalidateQueries({ queryKey: ['initiatives', { id: data.id }] });

      // Track first initiative creation for time-to-value metric
      const hasTrackedFirstInitiative = SafeStorage.safeGet('hasTrackedFirstInitiative', (val): val is boolean => typeof val === 'boolean', false);
      if (!hasTrackedFirstInitiative) {
        // Get signup timestamp from user account details cache
        const onboardingCompletedAt = SafeStorage.safeGet('onboarding_completed_at', (val): val is string => typeof val === 'string', null);
        trackFirstInitiativeCreated(onboardingCompletedAt || undefined);
        SafeStorage.safeSet('hasTrackedFirstInitiative', true);
      }
    },
  });

  // UPDATE MUTATION
  const updateMutation = useOptimisticMutation<InitiativeDto, Error, Partial<InitiativeDto>, InitiativeMutationContext>({
    mutationFn: postInitiative,

    queryKeysToCancel: () => [queryKey],

    createOptimisticData: (updatedInitiativeData, context) => {
      const previousInitiatives = context?.previousInitiatives || queryClient.getQueryData<InitiativeDto[]>(queryKey);
      const existingInitiative = previousInitiatives?.find((initiative: InitiativeDto) => initiative.id === updatedInitiativeData.id);

      if (existingInitiative) {
        return { ...existingInitiative, ...updatedInitiativeData };
      }
      return null;
    },

    updateCache: (optimisticInitiative) => {
      if (optimisticInitiative && updateInitiativeInCache) {
        // Find the previous initiative to get old status for cache updates
        const previousInitiatives = queryClient.getQueryData<InitiativeDto[]>(queryKey);
        const existingInitiative = previousInitiatives?.find(initiative => initiative.id === optimisticInitiative.id);
        updateInitiativeInCache(optimisticInitiative, existingInitiative?.status);
      }
    },

    updateCacheWithServerResponse: (serverInitiative) => {
      if (serverInitiative && updateInitiativeInCache) {
        updateInitiativeInCache(serverInitiative, undefined);
      }
    },

    captureContext: () => ({
      previousInitiatives: queryClient.getQueryData<InitiativeDto[]>(queryKey),
      queryKey,
    }),

    rollbackCache: (context) => {
      if (context?.previousInitiatives && context?.queryKey) {
        queryClient.setQueryData<InitiativeDto[]>(context.queryKey, context.previousInitiatives);
        setCacheVersion?.(prev => prev + 1);
      }
    },

    onSuccessCallback: async (data) => {
      queryClient.invalidateQueries({ queryKey: ['initiatives'] });
      queryClient.invalidateQueries({ queryKey: ['initiatives', { status: data.status }] });
      queryClient.invalidateQueries({ queryKey: ['initiatives', { id: data.id }] });
    },
  });

  // DELETE MUTATION
  const deleteMutation = useOptimisticMutation<void, Error, string, InitiativeMutationContext>({
    mutationFn: apiDeleteInitiative,

    queryKeysToCancel: () => [queryKey],

    createOptimisticData: () => null,

    updateCache: (_, initiativeId) => {
      queryClient.setQueryData<InitiativeDto[]>(queryKey, (oldData) => {
        if (!oldData) return oldData;
        return oldData.filter(initiative => initiative.id !== initiativeId);
      });
      setCacheVersion?.(prev => prev + 1);
    },

    updateCacheWithServerResponse: (_, initiativeId) => {
      queryClient.removeQueries({ queryKey: ['initiatives', { id: initiativeId }] });
      queryClient.removeQueries({ queryKey: ['orderings', { entityType: EntityType.INITIATIVE, entityId: initiativeId }] });
    },

    captureContext: (initiativeId) => {
      const previousInitiatives = queryClient.getQueryData<InitiativeDto[]>(queryKey);
      const deletedInitiative = previousInitiatives?.find(initiative => initiative.id === initiativeId);
      return {
        previousInitiatives,
        deletedInitiative,
        queryKey
      };
    },

    rollbackCache: (context) => {
      if (context?.previousInitiatives) {
        queryClient.setQueryData<InitiativeDto[]>(queryKey, context.previousInitiatives);
        setCacheVersion?.(prev => prev + 1);
      }
    },

    onSuccessCallback: async () => {
      queryClient.invalidateQueries({ queryKey: ['initiatives'] });
    },
  });

  // BATCH UPDATE MUTATION
  const updateBatchMutation = useMutation<InitiativeDto[], Error, Partial<InitiativeDto>[]>({
    mutationFn: async (initiatives) => {
      console.warn('updateInitiatives batch function might need cache adjustments.');
      const results: InitiativeDto[] = [];
      for (const initiative of initiatives) {
        results.push(await postInitiative(initiative));
      }
      return results;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['initiatives'] });
      queryClient.invalidateQueries({ queryKey: ['initiatives', { status: data[0].status }] });
      for (const initiative of data) {
        queryClient.invalidateQueries({ queryKey: ['initiatives', { id: initiative.id }] });
      }
    },
  });

  // DELETE TASK MUTATION
  const deleteTaskMutation = useMutation<void, Error, string>({
    mutationFn: async (taskId) => {
      await apiDeleteTask(taskId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['initiatives'] });
    },
  });

  // DELETE CHECKLIST ITEM MUTATION
  const deleteChecklistItemMutation = useMutation<void, Error, string>({
    mutationFn: async (checklistItemId) => {
      await apiDeleteChecklistItem(checklistItemId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['initiatives'] });
    },
  });

  // REORDER INITIATIVE MUTATION
  const reorderInitiativeMutation = useOptimisticMutation<InitiativeDto, Error, {
    initiativeId: string;
    afterId: string | null;
    beforeId: string | null;
  }, InitiativeMutationContext>({
    mutationFn: ({initiativeId, afterId, beforeId}) => moveInitiativeApi(initiativeId, afterId, beforeId),

    queryKeysToCancel: () => [queryKey],

    createOptimisticData: ({initiativeId}, context) => {
      const previousInitiatives = context?.previousInitiatives || queryClient.getQueryData<InitiativeDto[]>(queryKey);
      const existingInitiative = previousInitiatives?.find((initiative: InitiativeDto) => initiative.id === initiativeId);
      return existingInitiative || null;
    },

    updateCache: (optimisticInitiative) => {
      if (optimisticInitiative && updateInitiativeInCache) {
        updateInitiativeInCache(optimisticInitiative);
      }
    },

    updateCacheWithServerResponse: (serverInitiative) => {
      if (serverInitiative && updateInitiativeInCache) {
        updateInitiativeInCache(serverInitiative);
      }
    },

    captureContext: () => ({
      previousInitiatives: queryClient.getQueryData<InitiativeDto[]>(queryKey),
      queryKey
    }),

    rollbackCache: (context) => {
      if (context?.previousInitiatives) {
        queryClient.setQueryData<InitiativeDto[]>(queryKey, context.previousInitiatives);
        setCacheVersion?.(prev => prev + 1);
      }
    },
  });

  // MOVE TO STATUS MUTATION
  const moveInitiativeToStatusMutation = useOptimisticMutation<InitiativeDto, Error, {
    initiativeId: string;
    newStatus: InitiativeStatus;
    afterId: string | null;
    beforeId: string | null;
  }, InitiativeMutationContext>({
    mutationFn: ({initiativeId, newStatus, afterId, beforeId}) => moveInitiativeToStatusApi(initiativeId, newStatus, afterId, beforeId),

    queryKeysToCancel: () => [queryKey],

    createOptimisticData: ({initiativeId, newStatus}, context) => {
      const previousInitiatives = context?.previousInitiatives || queryClient.getQueryData<InitiativeDto[]>(queryKey);
      const existingInitiative = previousInitiatives?.find((initiative: InitiativeDto) => initiative.id === initiativeId);

      if (existingInitiative) {
        return { ...existingInitiative, status: newStatus };
      }
      return null;
    },

    updateCache: (optimisticInitiative, {initiativeId}) => {
      if (optimisticInitiative && updateInitiativeInCache) {
        const previousInitiatives = queryClient.getQueryData<InitiativeDto[]>(queryKey);
        const existingInitiative = previousInitiatives?.find(initiative => initiative.id === initiativeId);
        updateInitiativeInCache(optimisticInitiative, existingInitiative?.status);
      }
    },

    updateCacheWithServerResponse: (serverInitiative, {initiativeId}) => {
      if (serverInitiative && updateInitiativeInCache) {
        const previousInitiatives = queryClient.getQueryData<InitiativeDto[]>(queryKey);
        const existingInitiative = previousInitiatives?.find(initiative => initiative.id === initiativeId);
        updateInitiativeInCache(serverInitiative, existingInitiative?.status);
      }
    },

    captureContext: ({initiativeId}) => {
      const previousInitiatives = queryClient.getQueryData<InitiativeDto[]>(queryKey);
      const existingInitiative = previousInitiatives?.find(initiative => initiative.id === initiativeId);

      return {
        previousInitiatives,
        oldStatus: existingInitiative?.status,
        queryKey
      };
    },

    rollbackCache: (context) => {
      if (context?.previousInitiatives) {
        queryClient.setQueryData<InitiativeDto[]>(queryKey, context.previousInitiatives);
        setCacheVersion?.(prev => prev + 1);
      }
    },
  });

  // Callback functions
  const reorderInitiative = useCallback(async (initiativeId: string, afterId: string | null, beforeId: string | null): Promise<void> => {
    await reorderInitiativeMutation.mutateAsync({initiativeId, afterId, beforeId});
  }, [reorderInitiativeMutation]);

  const moveInitiativeToStatus = useCallback(async (initiativeId: string, newStatus: InitiativeStatus, afterId: string | null, beforeId: string | null): Promise<void> => {
    await moveInitiativeToStatusMutation.mutateAsync({initiativeId, newStatus, afterId, beforeId});
  }, [moveInitiativeToStatusMutation]);

  const moveInitiativeInGroup = useCallback(async (initiativeId: string, groupId: string, afterId: string | null, beforeId: string | null) => {
    // Get current initiatives data to find the initiative
    const initiativesData = queryClient.getQueryData<InitiativeDto[]>(queryKey);
    const initiative = initiativesData?.find(i => i.id === initiativeId);

    if (initiative && updateInitiativeInCache) {
      const updatedInitiative = await apiMoveInitiativeInGroup(initiativeId, groupId, afterId, beforeId);
      updateInitiativeInCache(updatedInitiative);
    }
  }, [queryKey, queryClient, updateInitiativeInCache]);

  return {
    // Loading states
    isCreatingInitiative: createMutation.isPending,
    isUpdatingInitiative: updateMutation.isPending,
    isDeletingInitiative: deleteMutation.isPending,
    isBatchUpdatingInitiatives: updateBatchMutation.isPending,
    isDeletingTask: deleteTaskMutation.isPending,
    isDeletingChecklistItem: deleteChecklistItemMutation.isPending,

    // Mutation functions
    createInitiative: (initiative, orderingContext) => createMutation.mutateAsync([initiative]),
    updateInitiative: updateMutation.mutateAsync,
    updateInitiatives: updateBatchMutation.mutateAsync,
    deleteInitiative: deleteMutation.mutateAsync,
    deleteTask: deleteTaskMutation.mutateAsync,
    deleteChecklistItem: deleteChecklistItemMutation.mutateAsync,

    // Reordering functions
    reorderInitiative,
    moveInitiativeToStatus,
    moveInitiativeInGroup,
  };
}