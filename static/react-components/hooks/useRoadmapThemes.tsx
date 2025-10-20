import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getRoadmapThemes,
  createRoadmapTheme,
  updateRoadmapTheme,
  deleteRoadmapTheme,
  reorderRoadmapThemes,
  ThemeDto,
  ThemeCreateRequest,
  ThemeUpdateRequest,
  ThemeReorderRequest,
} from '#api/productStrategy';

/**
 * Custom hook for managing roadmap themes for a workspace
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing themes data, loading states, and mutation functions
 */
export function useRoadmapThemes(workspaceId: string) {
  const queryClient = useQueryClient();

  const {
    data: themes,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['roadmap-themes', workspaceId],
    queryFn: () => getRoadmapThemes(workspaceId),
    enabled: !!workspaceId,
  });

  const createMutation = useMutation({
    mutationFn: (request: ThemeCreateRequest) =>
      createRoadmapTheme(workspaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', workspaceId],
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ themeId, request }: { themeId: string; request: ThemeUpdateRequest }) =>
      updateRoadmapTheme(workspaceId, themeId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', workspaceId],
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (themeId: string) =>
      deleteRoadmapTheme(workspaceId, themeId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', workspaceId],
      });
    },
  });

  const reorderMutation = useMutation({
    mutationFn: (request: ThemeReorderRequest) =>
      reorderRoadmapThemes(workspaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', workspaceId],
      });
    },
  });

  return {
    themes: themes || [],
    isLoading,
    error,
    createTheme: createMutation.mutate,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    updateTheme: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,
    deleteTheme: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,
    reorderThemes: reorderMutation.mutate,
    isReordering: reorderMutation.isPending,
    reorderError: reorderMutation.error,
  };
}
