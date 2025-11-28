import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useOptimisticMutation } from '#hooks/useOptimisticMutation';
import {
  getStrategicInitiative,
  createStrategicInitiative as apiCreateStrategicInitiative,
  updateStrategicInitiative as apiUpdateStrategicInitiative,
  StrategicInitiativeCreateRequest,
  StrategicInitiativeUpdateRequest,
} from '#api/productStrategy';
import { StrategicInitiativeDto } from '#types';

type StrategicInitiativeMutationContext = {
  previousData: StrategicInitiativeDto | null | undefined;
  queryKey: any[];
};

/**
 * Custom hook for managing strategic initiative context with optimistic updates
 * @param {string} initiativeId - The initiative ID
 * @returns {object} Object containing strategic initiative data, loading states, and mutation functions
 */
export function useStrategicInitiative(initiativeId: string) {
  const queryClient = useQueryClient();
  const queryKey = ['strategic-initiative', initiativeId];

  const {
    data: strategicInitiative,
    isLoading,
    error,
  } = useQuery({
    queryKey,
    queryFn: () => getStrategicInitiative(initiativeId),
    enabled: !!initiativeId,
  });

  const createMutation = useOptimisticMutation<
    StrategicInitiativeDto,
    Error,
    StrategicInitiativeCreateRequest,
    StrategicInitiativeMutationContext
  >({
    mutationFn: (request) => apiCreateStrategicInitiative(initiativeId, request),

    queryKeysToCancel: () => [queryKey],

    createOptimisticData: (request) => {
      return {
        initiative_id: initiativeId,
        ...request,
      } as StrategicInitiativeDto;
    },

    updateCache: (optimisticData) => {
      queryClient.setQueryData<StrategicInitiativeDto | undefined>(queryKey, optimisticData);
    },

    captureContext: () => ({
      previousData: queryClient.getQueryData<StrategicInitiativeDto>(queryKey),
      queryKey,
    }),

    rollbackCache: (context) => {
      queryClient.setQueryData<StrategicInitiativeDto | undefined>(
        queryKey, 
        context.previousData ?? undefined
      );
    },
  });

  const updateMutation = useOptimisticMutation<
    StrategicInitiativeDto,
    Error,
    StrategicInitiativeUpdateRequest,
    StrategicInitiativeMutationContext
  >({
    mutationFn: (request) => apiUpdateStrategicInitiative(initiativeId, request),

    queryKeysToCancel: () => [queryKey],

    createOptimisticData: (request) => {
      const currentData = queryClient.getQueryData<StrategicInitiativeDto>(queryKey);
      if (currentData) {
        return { ...currentData, ...request };
      }
      return null;
    },

    updateCache: (optimisticData) => {
      if (optimisticData) {
        queryClient.setQueryData<StrategicInitiativeDto | undefined>(queryKey, optimisticData);
      }
    },

    captureContext: () => ({
      previousData: queryClient.getQueryData<StrategicInitiativeDto>(queryKey),
      queryKey,
    }),

    rollbackCache: (context) => {
      queryClient.setQueryData<StrategicInitiativeDto | undefined>(
        queryKey, 
        context.previousData ?? undefined
      );
    },
  });

  return {
    strategicInitiative: strategicInitiative || null,
    isLoading,
    error,
    createStrategicInitiative: createMutation.mutate,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    updateStrategicInitiative: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,
  };
}

