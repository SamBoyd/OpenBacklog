import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getWorkspaceVision,
  upsertWorkspaceVision,
  VisionDto,
  VisionUpdateRequest,
} from '#api/productStrategy';

export function useProductVision(workspaceId: string) {
  const queryClient = useQueryClient();

  const {
    data: vision,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['workspace-vision', workspaceId],
    queryFn: () => getWorkspaceVision(workspaceId),
    enabled: !!workspaceId,
  });

  const upsertMutation = useMutation({
    mutationFn: (request: VisionUpdateRequest) =>
      upsertWorkspaceVision(workspaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['workspace-vision', workspaceId],
      });
    },
  });

  return {
    vision,
    isLoading,
    error,
    upsertVision: upsertMutation.mutate,
    isUpserting: upsertMutation.isPending,
    upsertError: upsertMutation.error,
  };
}
