import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getPrioritizedThemes,
  getUnprioritizedThemes,
  prioritizeTheme,
  deprioritizeTheme,
  reorderRoadmapThemes,
  ThemeDto,
  ThemePrioritizeRequest,
  ThemeReorderRequest,
} from '#api/productStrategy';

/**
 * Custom hook for managing roadmap theme prioritization
 * Separates themes into prioritized (active work) and unprioritized (backlog)
 *
 * @param {string} workspaceId - The workspace ID
 * @returns {object} Object containing prioritized/unprioritized themes and mutation functions
 */
export function useThemePrioritization(workspaceId: string) {
  const queryClient = useQueryClient();

  // Query for prioritized themes (active work)
  const {
    data: prioritizedThemes,
    isLoading: isLoadingPrioritized,
    error: prioritizedError,
  } = useQuery({
    queryKey: ['roadmap-themes', 'prioritized', workspaceId],
    queryFn: () => getPrioritizedThemes(workspaceId),
    enabled: !!workspaceId,
  });

  // Query for unprioritized themes (backlog)
  const {
    data: unprioritizedThemes,
    isLoading: isLoadingUnprioritized,
    error: unprioritizedError,
  } = useQuery({
    queryKey: ['roadmap-themes', 'unprioritized', workspaceId],
    queryFn: () => getUnprioritizedThemes(workspaceId),
    enabled: !!workspaceId,
  });

  // Mutation for prioritizing a theme (move from backlog to active)
  const prioritizeMutation = useMutation({
    mutationFn: ({ themeId, position }: { themeId: string; position: number }) =>
      prioritizeTheme(workspaceId, themeId, { position }),
    onSuccess: () => {
      // Invalidate all theme-related queries to ensure consistency
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', 'prioritized', workspaceId],
      });
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', 'unprioritized', workspaceId],
      });
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', workspaceId],
      });
    },
  });

  // Mutation for deprioritizing a theme (move from active to backlog)
  const deprioritizeMutation = useMutation({
    mutationFn: (themeId: string) => deprioritizeTheme(workspaceId, themeId),
    onSuccess: () => {
      // Invalidate all theme-related queries to ensure consistency
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', 'prioritized', workspaceId],
      });
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', 'unprioritized', workspaceId],
      });
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', workspaceId],
      });
    },
  });

  // Mutation for reordering prioritized themes
  const reorderMutation = useMutation({
    mutationFn: (request: ThemeReorderRequest) =>
      reorderRoadmapThemes(workspaceId, request),
    onSuccess: () => {
      // Invalidate all theme-related queries to ensure consistency
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', 'prioritized', workspaceId],
      });
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', 'unprioritized', workspaceId],
      });
      queryClient.invalidateQueries({
        queryKey: ['roadmap-themes', workspaceId],
      });
    },
  });

  return {
    // Prioritized themes data
    prioritizedThemes: prioritizedThemes || [],
    isLoadingPrioritized,
    prioritizedError,

    // Unprioritized themes data
    unprioritizedThemes: unprioritizedThemes || [],
    isLoadingUnprioritized,
    unprioritizedError,

    // Loading states
    isLoading: isLoadingPrioritized || isLoadingUnprioritized,

    // Prioritize mutation
    prioritizeTheme: prioritizeMutation.mutate,
    isPrioritizing: prioritizeMutation.isPending,
    prioritizeError: prioritizeMutation.error,

    // Deprioritize mutation
    deprioritizeTheme: deprioritizeMutation.mutate,
    isDeprioritizing: deprioritizeMutation.isPending,
    deprioritizeError: deprioritizeMutation.error,

    // Reorder mutation
    reorderPrioritizedThemes: reorderMutation.mutate,
    isReordering: reorderMutation.isPending,
    reorderError: reorderMutation.error,
  };
}
