import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getStrategicPillars,
  createStrategicPillar,
  updateStrategicPillar,
  deleteStrategicPillar,
  reorderStrategicPillars,
  PillarDto,
  PillarCreateRequest,
  PillarUpdateRequest,
  PillarReorderRequest,
} from '#api/productStrategy';

/**
 * Custom hook for managing strategic pillars for a workspace
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing pillars data, loading states, and mutation functions
 */
export function useStrategicPillars(workspaceId: string) {
  const queryClient = useQueryClient();

  const {
    data: pillars,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['strategic-pillars', workspaceId],
    queryFn: () => getStrategicPillars(workspaceId),
    enabled: !!workspaceId,
  });

  const createMutation = useMutation({
    mutationFn: (request: PillarCreateRequest) =>
      createStrategicPillar(workspaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['strategic-pillars', workspaceId],
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ pillarId, request }: { pillarId: string; request: PillarUpdateRequest }) =>
      updateStrategicPillar(workspaceId, pillarId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['strategic-pillars', workspaceId],
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (pillarId: string) =>
      deleteStrategicPillar(workspaceId, pillarId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['strategic-pillars', workspaceId],
      });
    },
  });

  const reorderMutation = useMutation({
    mutationFn: (request: PillarReorderRequest) =>
      reorderStrategicPillars(workspaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['strategic-pillars', workspaceId],
      });
    },
  });

  return {
    pillars: pillars || [],
    isLoading,
    error,
    createPillar: createMutation.mutate,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    updatePillar: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,
    deletePillar: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,
    reorderPillars: reorderMutation.mutate,
    isReordering: reorderMutation.isPending,
    reorderError: reorderMutation.error,
  };
}
