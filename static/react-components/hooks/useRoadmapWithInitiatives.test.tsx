import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useRoadmapWithInitiatives } from './useRoadmapWithInitiatives';
import * as themePrioritizationHook from '#hooks/useThemePrioritization';
import * as productStrategyApi from '#api/productStrategy';
import { ThemeDto } from '#api/productStrategy';
import { StrategicInitiativeDto } from '#types';

// Mock the dependencies
vi.mock('#hooks/useThemePrioritization');
vi.mock('#api/productStrategy');

const mockUseThemePrioritization = vi.spyOn(themePrioritizationHook, 'useThemePrioritization');
const mockGetStrategicInitiativesByTheme = vi.spyOn(productStrategyApi, 'getStrategicInitiativesByTheme');

/**
 * Helper to create mock theme data
 */
const createMockTheme = (id: string, name: string): ThemeDto => ({
  id,
  workspace_id: 'workspace-1',
  name,
  description: `Description for ${name}: addressing key user problems and validating our hypothesis through measurable outcomes.`,
  outcome_ids: [],
  hero_ids: [],
  villain_ids: [],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
});

/**
 * Helper to create mock strategic initiative data
 */
const createMockInitiative = (id: string, initiativeId: string, themeId: string): StrategicInitiativeDto => ({
  id,
  initiative_id: initiativeId,
  workspace_id: 'workspace-1',
  pillar_id: null,
  theme_id: themeId,
  description: null,
  narrative_intent: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
});

/**
 * Helper to create complete mock return value for useThemePrioritization
 */
const createMockThemePrioritizationHook = (
  prioritizedThemes: ThemeDto[],
  unprioritizedThemes: ThemeDto[],
  isLoading: boolean = false,
  prioritizedError: Error | null = null,
  unprioritizedError: Error | null = null
) => ({
  prioritizedThemes,
  unprioritizedThemes,
  isLoading,
  isLoadingPrioritized: isLoading,
  isLoadingUnprioritized: isLoading,
  prioritizedError,
  unprioritizedError,
  prioritizeTheme: vi.fn(),
  isPrioritizing: false,
  prioritizeError: null,
  deprioritizeTheme: vi.fn(),
  isDeprioritizing: false,
  deprioritizeError: null,
  reorderPrioritizedThemes: vi.fn(),
  isReordering: false,
  reorderError: null,
});

describe('useRoadmapWithInitiatives', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    // Create a new QueryClient for each test with retry disabled
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
          staleTime: 0,
        },
      },
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  /**
   * Test wrapper component that provides QueryClient
   */
  const createWrapper = () => {
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  describe('Basic Loading States', () => {
    it('should return loading state when themes are loading', () => {
      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([], [], true)
      );

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.prioritizedThemes).toEqual([]);
      expect(result.current.unprioritizedThemes).toEqual([]);
    });

    it('should return loading state when initiatives are loading', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1], [], false)
      );

      // Mock initiative query to take some time
      mockGetStrategicInitiativesByTheme.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve([]), 100))
      );

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      // Initially, initiatives should be loading
      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(true);
      });

      // Themes should be populated even while initiatives are loading
      expect(result.current.prioritizedThemes).toHaveLength(1);
      expect(result.current.prioritizedThemes[0].id).toBe('theme-1');
      expect(result.current.prioritizedThemes[0].isLoadingInitiatives).toBe(true);
    });

    it('should return false for all loading states when data is loaded', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');
      const initiative1 = createMockInitiative('si-1', 'init-1', 'theme-1');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1], [], false)
      );

      mockGetStrategicInitiativesByTheme.mockResolvedValue([initiative1]);

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isLoadingInitiatives).toBe(false);
      });
    });
  });

  describe('Data Enrichment', () => {
    it('should successfully enrich prioritized themes with initiatives', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');
      const theme2 = createMockTheme('theme-2', 'Theme 2');
      const initiative1 = createMockInitiative('si-1', 'init-1', 'theme-1');
      const initiative2 = createMockInitiative('si-2', 'init-2', 'theme-1');
      const initiative3 = createMockInitiative('si-3', 'init-3', 'theme-2');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1, theme2], [], false)
      );

      mockGetStrategicInitiativesByTheme.mockImplementation((workspaceId, themeId) => {
        if (themeId === 'theme-1') return Promise.resolve([initiative1, initiative2]);
        if (themeId === 'theme-2') return Promise.resolve([initiative3]);
        return Promise.resolve([]);
      });

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      expect(result.current.prioritizedThemes).toHaveLength(2);
      expect(result.current.prioritizedThemes[0].strategicInitiatives).toHaveLength(2);
      expect(result.current.prioritizedThemes[0].strategicInitiatives[0].id).toBe('si-1');
      expect(result.current.prioritizedThemes[1].strategicInitiatives).toHaveLength(1);
      expect(result.current.prioritizedThemes[1].strategicInitiatives[0].id).toBe('si-3');
    });

    it('should successfully enrich unprioritized themes with initiatives', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');
      const initiative1 = createMockInitiative('si-1', 'init-1', 'theme-1');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([], [theme1], false)
      );

      mockGetStrategicInitiativesByTheme.mockResolvedValue([initiative1]);

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      expect(result.current.unprioritizedThemes).toHaveLength(1);
      expect(result.current.unprioritizedThemes[0].strategicInitiatives).toHaveLength(1);
      expect(result.current.unprioritizedThemes[0].strategicInitiatives[0].id).toBe('si-1');
    });

    it('should handle empty theme arrays', () => {
      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([], [], false)
      );

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      expect(result.current.prioritizedThemes).toEqual([]);
      expect(result.current.unprioritizedThemes).toEqual([]);
      expect(result.current.isLoadingInitiatives).toBe(false);
    });

    it('should handle themes with no initiatives (empty arrays)', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1], [], false)
      );

      mockGetStrategicInitiativesByTheme.mockResolvedValue([]);

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      expect(result.current.prioritizedThemes).toHaveLength(1);
      expect(result.current.prioritizedThemes[0].strategicInitiatives).toEqual([]);
    });

    it('should correctly map initiatives to themes with both prioritized and unprioritized', async () => {
      const prioritizedTheme = createMockTheme('theme-p1', 'Prioritized Theme');
      const unprioritizedTheme = createMockTheme('theme-u1', 'Unprioritized Theme');
      const initiativeP = createMockInitiative('si-p', 'init-p', 'theme-p1');
      const initiativeU = createMockInitiative('si-u', 'init-u', 'theme-u1');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([prioritizedTheme], [unprioritizedTheme], false)
      );

      mockGetStrategicInitiativesByTheme.mockImplementation((workspaceId, themeId) => {
        if (themeId === 'theme-p1') return Promise.resolve([initiativeP]);
        if (themeId === 'theme-u1') return Promise.resolve([initiativeU]);
        return Promise.resolve([]);
      });

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      // Verify correct mapping
      expect(result.current.prioritizedThemes[0].strategicInitiatives[0].id).toBe('si-p');
      expect(result.current.unprioritizedThemes[0].strategicInitiatives[0].id).toBe('si-u');
    });
  });

  describe('Error Handling', () => {
    it('should surface theme query errors in error field', () => {
      const themeError = new Error('Failed to load themes');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([], [], false, themeError, null)
      );

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      expect(result.current.error).toBe(themeError);
    });

    it('should handle individual initiative query failures with empty arrays', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');
      const theme2 = createMockTheme('theme-2', 'Theme 2');
      const initiative2 = createMockInitiative('si-2', 'init-2', 'theme-2');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1, theme2], [], false)
      );

      // First theme fails, second succeeds
      mockGetStrategicInitiativesByTheme.mockImplementation((workspaceId, themeId) => {
        if (themeId === 'theme-1') return Promise.reject(new Error('Initiative load failed'));
        if (themeId === 'theme-2') return Promise.resolve([initiative2]);
        return Promise.resolve([]);
      });

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      // Failed theme should have empty initiatives array
      expect(result.current.prioritizedThemes[0].strategicInitiatives).toEqual([]);
      // Successful theme should have data
      expect(result.current.prioritizedThemes[1].strategicInitiatives).toHaveLength(1);
      expect(result.current.prioritizedThemes[1].strategicInitiatives[0].id).toBe('si-2');
    });

    it('should prioritize prioritized theme errors over unprioritized', () => {
      const prioritizedError = new Error('Prioritized themes failed');
      const unprioritizedError = new Error('Unprioritized themes failed');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([], [], false, prioritizedError, unprioritizedError)
      );

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      expect(result.current.error).toBe(prioritizedError);
    });
  });

  describe('Memoization Behavior', () => {
    it('should maintain stable references when data has not changed', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');
      const initiative1 = createMockInitiative('si-1', 'init-1', 'theme-1');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1], [], false)
      );

      mockGetStrategicInitiativesByTheme.mockResolvedValue([initiative1]);

      const { result, rerender } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      const firstPrioritizedThemes = result.current.prioritizedThemes;

      // Force a re-render with same data
      rerender();

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      // CRITICAL: This test will fail with the memoization bug
      // After fixing, the reference should be stable
      expect(result.current.prioritizedThemes).toBe(firstPrioritizedThemes);
    });

    it('should recalculate when theme data changes', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');
      const theme2 = createMockTheme('theme-2', 'Theme 2');
      const initiative1 = createMockInitiative('si-1', 'init-1', 'theme-1');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1], [], false)
      );

      mockGetStrategicInitiativesByTheme.mockResolvedValue([initiative1]);

      const { result, rerender } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      expect(result.current.prioritizedThemes).toHaveLength(1);

      // Change the theme data
      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1, theme2], [], false)
      );

      rerender();

      await waitFor(() => {
        expect(result.current.prioritizedThemes).toHaveLength(2);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle workspaceId changes', async () => {
      const theme1 = createMockTheme('theme-1', 'Theme 1');
      const initiative1 = createMockInitiative('si-1', 'init-1', 'theme-1');

      mockUseThemePrioritization.mockReturnValue(
        createMockThemePrioritizationHook([theme1], [], false)
      );

      mockGetStrategicInitiativesByTheme.mockResolvedValue([initiative1]);

      const { result, rerender } = renderHook(
        ({ workspaceId }) => useRoadmapWithInitiatives(workspaceId),
        {
          wrapper: createWrapper(),
          initialProps: { workspaceId: 'workspace-1' }
        }
      );

      await waitFor(() => {
        expect(result.current.isLoadingInitiatives).toBe(false);
      });

      expect(mockGetStrategicInitiativesByTheme).toHaveBeenCalledWith('workspace-1', 'theme-1');

      // Change workspace ID
      rerender({ workspaceId: 'workspace-2' });

      await waitFor(() => {
        expect(mockGetStrategicInitiativesByTheme).toHaveBeenCalledWith('workspace-2', 'theme-1');
      });
    });

    it('should pass through mutation functions from useThemePrioritization', () => {
      const mockPrioritize = vi.fn();
      const mockDeprioritize = vi.fn();
      const mockReorder = vi.fn();

      mockUseThemePrioritization.mockReturnValue({
        ...createMockThemePrioritizationHook([], [], false),
        prioritizeTheme: mockPrioritize,
        deprioritizeTheme: mockDeprioritize,
        reorderPrioritizedThemes: mockReorder,
      });

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      expect(result.current.prioritizeTheme).toBe(mockPrioritize);
      expect(result.current.deprioritizeTheme).toBe(mockDeprioritize);
      expect(result.current.reorderPrioritizedThemes).toBe(mockReorder);
    });

    it('should pass through mutation loading states', () => {
      mockUseThemePrioritization.mockReturnValue({
        ...createMockThemePrioritizationHook([], [], false),
        isPrioritizing: true,
        isDeprioritizing: false,
        isReordering: true,
      });

      const { result } = renderHook(
        () => useRoadmapWithInitiatives('workspace-1'),
        { wrapper: createWrapper() }
      );

      expect(result.current.isPrioritizing).toBe(true);
      expect(result.current.isDeprioritizing).toBe(false);
      expect(result.current.isReordering).toBe(true);
    });
  });
});
