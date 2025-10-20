import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getProductOutcomes,
  createProductOutcome,
  updateProductOutcome,
  deleteProductOutcome,
  reorderProductOutcomes,
  OutcomeDto,
  OutcomeCreateRequest,
  OutcomeUpdateRequest,
  OutcomeReorderRequest,
} from '#api/productStrategy';

/**
 * Custom hook for managing product outcomes for a workspace
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing outcomes data, loading states, and mutation functions
 */
export function useProductOutcomes(workspaceId: string) {
  const queryClient = useQueryClient();

  const {
    data: outcomes,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['product-outcomes', workspaceId],
    queryFn: () => getProductOutcomes(workspaceId),
    enabled: !!workspaceId,
  });

  const createMutation = useMutation({
    mutationFn: (request: OutcomeCreateRequest) =>
      createProductOutcome(workspaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['product-outcomes', workspaceId],
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ outcomeId, request }: { outcomeId: string; request: OutcomeUpdateRequest }) =>
      updateProductOutcome(workspaceId, outcomeId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['product-outcomes', workspaceId],
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (outcomeId: string) =>
      deleteProductOutcome(workspaceId, outcomeId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['product-outcomes', workspaceId],
      });
    },
  });

  const reorderMutation = useMutation({
    mutationFn: (request: OutcomeReorderRequest) =>
      reorderProductOutcomes(workspaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['product-outcomes', workspaceId],
      });
    },
  });

  return {
    outcomes: outcomes || [],
    isLoading,
    error,
    createOutcome: createMutation.mutate,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    updateOutcome: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,
    deleteOutcome: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,
    reorderOutcomes: reorderMutation.mutate,
    isReordering: reorderMutation.isPending,
    reorderError: reorderMutation.error,
  };
}

