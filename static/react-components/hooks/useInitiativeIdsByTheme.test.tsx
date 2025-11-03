import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useInitiativeIdsByTheme } from './useInitiativeIdsByTheme';
import * as roadmapHook from '#hooks/useRoadmapWithInitiatives';
import * as initiativesApi from '#api/initiatives';

// Create a test QueryClient
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

// Test wrapper component
const createWrapper = () => {
  const queryClient = createTestQueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Helper to create mock return value for useRoadmapWithInitiatives
const createMockRoadmapHook = (
  prioritizedThemes: any[],
  unprioritizedThemes: any[],
  isLoading: boolean = false
) => ({
  prioritizedThemes,
  unprioritizedThemes,
  isLoading,
  isLoadingInitiatives: false,
  error: null,
  prioritizeTheme: vi.fn(),
  isPrioritizing: false,
  deprioritizeTheme: vi.fn(),
  isDeprioritizing: false,
  reorderPrioritizedThemes: vi.fn(),
  isReordering: false,
});

describe('useInitiativeIdsByTheme', () => {
  const workspaceId = 'workspace-123';

  // Test data
  const prioritizedTheme1 = {
    id: 'prioritized-theme-1',
    workspace_id: workspaceId,
    name: 'Prioritized Theme 1',
    problem_statement: 'Problem 1',
    hypothesis: null,
    indicative_metrics: null,
    time_horizon_months: null,
    outcome_ids: [],
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
    strategicInitiatives: [
      { id: 'si-1', initiative_id: 'init-1', workspace_id: workspaceId, pillar_id: null, theme_id: 'prioritized-theme-1', user_need: null, connection_to_vision: null, success_criteria: null, out_of_scope: null, created_at: '2025-01-01', updated_at: '2025-01-01' },
      { id: 'si-2', initiative_id: 'init-2', workspace_id: workspaceId, pillar_id: null, theme_id: 'prioritized-theme-1', user_need: null, connection_to_vision: null, success_criteria: null, out_of_scope: null, created_at: '2025-01-01', updated_at: '2025-01-01' },
    ],
    isLoadingInitiatives: false,
  };

  const prioritizedTheme2 = {
    id: 'prioritized-theme-2',
    workspace_id: workspaceId,
    name: 'Prioritized Theme 2',
    problem_statement: 'Problem 2',
    hypothesis: null,
    indicative_metrics: null,
    time_horizon_months: null,
    outcome_ids: [],
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
    strategicInitiatives: [
      { id: 'si-3', initiative_id: 'init-3', workspace_id: workspaceId, pillar_id: null, theme_id: 'prioritized-theme-2', user_need: null, connection_to_vision: null, success_criteria: null, out_of_scope: null, created_at: '2025-01-01', updated_at: '2025-01-01' },
    ],
    isLoadingInitiatives: false,
  };

  const unprioritizedTheme1 = {
    id: 'unprioritized-theme-1',
    workspace_id: workspaceId,
    name: 'Unprioritized Theme 1',
    problem_statement: 'Problem 3',
    hypothesis: null,
    indicative_metrics: null,
    time_horizon_months: null,
    outcome_ids: [],
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
    strategicInitiatives: [
      { id: 'si-4', initiative_id: 'init-4', workspace_id: workspaceId, pillar_id: null, theme_id: 'unprioritized-theme-1', user_need: null, connection_to_vision: null, success_criteria: null, out_of_scope: null, created_at: '2025-01-01', updated_at: '2025-01-01' },
    ],
    isLoadingInitiatives: false,
  };

  const allInitiativesData = [
    { id: 'init-1', identifier: 'INIT-1', user_id: 'user-1', title: 'Initiative 1', description: '', created_at: '2025-01-01', updated_at: '2025-01-01', status: 'TODO', type: null, tasks: [], has_pending_job: false, properties: {} },
    { id: 'init-2', identifier: 'INIT-2', user_id: 'user-1', title: 'Initiative 2', description: '', created_at: '2025-01-01', updated_at: '2025-01-01', status: 'TODO', type: null, tasks: [], has_pending_job: false, properties: {} },
    { id: 'init-3', identifier: 'INIT-3', user_id: 'user-1', title: 'Initiative 3', description: '', created_at: '2025-01-01', updated_at: '2025-01-01', status: 'TODO', type: null, tasks: [], has_pending_job: false, properties: {} },
    { id: 'init-4', identifier: 'INIT-4', user_id: 'user-1', title: 'Initiative 4', description: '', created_at: '2025-01-01', updated_at: '2025-01-01', status: 'TODO', type: null, tasks: [], has_pending_job: false, properties: {} },
    { id: 'init-5-unthemed', identifier: 'INIT-5', user_id: 'user-1', title: 'Initiative 5 Unthemed', description: '', created_at: '2025-01-01', updated_at: '2025-01-01', status: 'TODO', type: null, tasks: [], has_pending_job: false, properties: {} },
    { id: 'init-6-unthemed', identifier: 'INIT-6', user_id: 'user-1', title: 'Initiative 6 Unthemed', description: '', created_at: '2025-01-01', updated_at: '2025-01-01', status: 'TODO', type: null, tasks: [], has_pending_job: false, properties: {} },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Scenarios', () => {
    it('should return empty array when selectedThemeIds is empty', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, []),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual([]);
    });

    it('should return empty array when themes are loading', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([], [], true)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['prioritized-theme-1']),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual([]);
    });

    it('should return empty array when no themes exist', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([], [], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['non-existent-theme']),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual([]);
    });
  });

  describe('Specific Theme IDs', () => {
    it('should return initiatives for a single prioritized theme', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['prioritized-theme-1']),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual(['init-1', 'init-2']);
    });

    it('should return initiatives for a single unprioritized theme', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['unprioritized-theme-1']),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual(['init-4']);
    });

    it('should return initiatives for multiple specific themes', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['prioritized-theme-1', 'unprioritized-theme-1']),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual(['init-1', 'init-2', 'init-4']);
    });
  });

  describe('Special Value: all-prioritized-themes', () => {
    it('should return all initiatives from prioritized themes', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['all-prioritized-themes']),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual(['init-1', 'init-2', 'init-3']);
    });

    it('should return empty array when there are no prioritized themes', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([], [unprioritizedTheme1], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['all-prioritized-themes']),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual([]);
    });
  });

  describe('Special Value: unthemed', () => {
    it('should return unthemed initiatives only', async () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue(allInitiativesData);

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['unthemed']),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current).toEqual(['init-5-unthemed', 'init-6-unthemed']);
      });
    });

    it('should return empty array when no unthemed initiatives exist', async () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      const themedOnlyData = allInitiativesData.filter(i => !i.id.includes('unthemed'));
      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue(themedOnlyData);

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['unthemed']),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current).toEqual([]);
      });
    });

    it('should not fetch all initiatives when unthemed is not selected', () => {
      const getAllInitiativesSpy = vi.spyOn(initiativesApi, 'getAllInitiatives');

      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1], [], false)
      );

      renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['prioritized-theme-1']),
        { wrapper: createWrapper() }
      );

      expect(getAllInitiativesSpy).not.toHaveBeenCalled();
    });
  });

  describe('Combinations: FIXED - Union Behavior', () => {
    it('should return union of all-prioritized-themes + specific unprioritized theme', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['all-prioritized-themes', 'unprioritized-theme-1']),
        { wrapper: createWrapper() }
      );

      // FIXED: Now returns union of all prioritized themes + the specific unprioritized theme
      expect(result.current).toEqual(['init-1', 'init-2', 'init-3', 'init-4']);
    });

    it('should return union of all-prioritized-themes + specific prioritized theme (deduped)', () => {
      // Create a third prioritized theme that's not selected
      const prioritizedTheme3 = {
        ...prioritizedTheme2,
        id: 'prioritized-theme-3',
        strategicInitiatives: [
          { id: 'si-5', initiative_id: 'init-5', workspace_id: workspaceId, pillar_id: null, theme_id: 'prioritized-theme-3', user_need: null, connection_to_vision: null, success_criteria: null, out_of_scope: null, created_at: '2025-01-01', updated_at: '2025-01-01' },
        ],
      };

      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2, prioritizedTheme3], [], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['all-prioritized-themes', 'prioritized-theme-1']),
        { wrapper: createWrapper() }
      );

      // FIXED: Now processes both selections (though prioritized-theme-1 is redundant since it's in all-prioritized)
      // The deduplication at the end ensures no duplicates
      expect(result.current).toEqual(['init-1', 'init-2', 'init-3', 'init-5']);
    });
  });

  describe('Combinations: EXPECTED BEHAVIOR - After Fix', () => {
    it('should return all-prioritized-themes + unthemed', async () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue(allInitiativesData);

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['all-prioritized-themes', 'unthemed']),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current).toEqual([
          'init-1', 'init-2', 'init-3', 'init-5-unthemed', 'init-6-unthemed'
        ]);
      });
    });

    it('should return specific themes + unthemed', async () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1, prioritizedTheme2], [unprioritizedTheme1], false)
      );

      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue(allInitiativesData);

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['prioritized-theme-1', 'unthemed']),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current).toEqual([
          'init-1', 'init-2', 'init-5-unthemed', 'init-6-unthemed'
        ]);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should deduplicate initiative IDs', async () => {
      // Create a theme with duplicate initiative (edge case that shouldn't happen but good to handle)
      const themeWithDupe = {
        ...prioritizedTheme1,
        strategicInitiatives: [
          ...prioritizedTheme1.strategicInitiatives,
          { id: 'si-1-dupe', initiative_id: 'init-1', workspace_id: workspaceId, pillar_id: null, theme_id: 'prioritized-theme-1', user_need: null, connection_to_vision: null, success_criteria: null, out_of_scope: null, created_at: '2025-01-01', updated_at: '2025-01-01' },
        ],
      };

      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([themeWithDupe], [], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['prioritized-theme-1']),
        { wrapper: createWrapper() }
      );

      // Should deduplicate init-1
      expect(result.current).toEqual(['init-1', 'init-2']);
    });

    it('should handle theme with no initiatives', () => {
      const emptyTheme = {
        ...prioritizedTheme1,
        id: 'empty-theme',
        strategicInitiatives: [],
      };

      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([emptyTheme], [], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['empty-theme']),
        { wrapper: createWrapper() }
      );

      expect(result.current).toEqual([]);
    });

    it('should handle selecting both regular and non-existent theme IDs', () => {
      vi.spyOn(roadmapHook, 'useRoadmapWithInitiatives').mockReturnValue(
        createMockRoadmapHook([prioritizedTheme1], [], false)
      );

      const { result } = renderHook(
        () => useInitiativeIdsByTheme(workspaceId, ['prioritized-theme-1', 'non-existent-theme']),
        { wrapper: createWrapper() }
      );

      // Should return only initiatives from the existing theme
      expect(result.current).toEqual(['init-1', 'init-2']);
    });
  });
});
