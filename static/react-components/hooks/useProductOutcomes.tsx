import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getProductOutcomes,
  createProductOutcome,
  OutcomeDto,
  OutcomeCreateRequest,
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

  return {
    outcomes: outcomes || [],
    isLoading,
    error,
    createOutcome: createMutation.mutate,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
  };
}

