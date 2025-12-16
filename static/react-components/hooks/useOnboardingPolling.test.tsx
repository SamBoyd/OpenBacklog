import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useOnboardingPolling } from './useOnboardingPolling';
import * as workspacesApi from '#api/workspaces';
import * as initiativesApi from '#api/initiatives';
import * as productStrategyApi from '#api/productStrategy';
import * as heroesApi from '#api/heroes';
import * as villainsApi from '#api/villains';
import { VillainType } from '#types';
import * as productOutcomesApi from '#api/productOutcomes';

vi.mock('#api/workspaces');
vi.mock('#api/initiatives');
vi.mock('#api/productStrategy');
vi.mock('#api/heroes');
vi.mock('#api/villains');
vi.mock('#api/productOutcomes');

describe('useOnboardingPolling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Stage 1: Workspace Polling', () => {
    it('should start in polling-workspace status', () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([]);

      const { result } = renderHook(() => useOnboardingPolling());

      expect(result.current.status).toBe('polling-workspace');
      expect(result.current.hasWorkspace).toBe(false);
      expect(result.current.hasInitiatives).toBe(false);
      expect(result.current.workspaceCount).toBe(0);
      expect(result.current.initiativeCount).toBe(0);
      expect(result.current.workspaceId).toBe(null);
      expect(result.current.foundationProgress).toEqual({
        hasVision: false,
        hasHeroes: false,
        hasVillains: false,
        hasPillars: false,
        hasOutcomes: false,
        hasThemes: false,
        hasInitiative: false,
      });
    });

    it('should call getAllWorkspaces on mount', async () => {
      const getAllWorkspacesSpy = vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([]);

      renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(getAllWorkspacesSpy).toHaveBeenCalled();
      });
    });

    it('should transition to polling-foundation when workspace is detected', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([
        { id: 'ws-1', name: 'Test Workspace', icon: null, description: null }
      ]);

      vi.spyOn(productStrategyApi, 'getWorkspaceVision').mockResolvedValue(null);
      vi.spyOn(heroesApi, 'getAllHeroes').mockResolvedValue([]);
      vi.spyOn(villainsApi, 'getAllVillains').mockResolvedValue([]);
      vi.spyOn(productStrategyApi, 'getStrategicPillars').mockResolvedValue([]);
      vi.spyOn(productOutcomesApi, 'getProductOutcomes').mockResolvedValue([]);
      vi.spyOn(productStrategyApi, 'getRoadmapThemes').mockResolvedValue([]);
      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue([]);

      const { result } = renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(result.current.status).toBe('polling-foundation');
      });

      expect(result.current.hasWorkspace).toBe(true);
      expect(result.current.workspaceCount).toBe(1);
      expect(result.current.workspaceId).toBe('ws-1');
    });

    it('should handle API errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockRejectedValue(new Error('Network error'));

      renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Error polling workspaces:', expect.any(Error));
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Stage 2: Foundation Polling', () => {
    const mockWorkspace = { id: 'ws-1', name: 'Test Workspace', icon: null, description: null };

    it('should poll for foundation entities after workspace is detected', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([mockWorkspace]);

      const getVisionSpy = vi.spyOn(productStrategyApi, 'getWorkspaceVision').mockResolvedValue(null);
      vi.spyOn(heroesApi, 'getAllHeroes').mockResolvedValue([]);
      vi.spyOn(villainsApi, 'getAllVillains').mockResolvedValue([]);
      vi.spyOn(productStrategyApi, 'getStrategicPillars').mockResolvedValue([]);
      vi.spyOn(productOutcomesApi, 'getProductOutcomes').mockResolvedValue([]);
      vi.spyOn(productStrategyApi, 'getRoadmapThemes').mockResolvedValue([]);
      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue([]);

      renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(getVisionSpy).toHaveBeenCalledWith('ws-1');
      });
    });

    it('should track foundation progress as entities are created', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([mockWorkspace]);

      vi.spyOn(productStrategyApi, 'getWorkspaceVision').mockResolvedValue({
        id: 'v-1',
        workspace_id: 'ws-1',
        vision_text: 'Test vision',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      vi.spyOn(heroesApi, 'getAllHeroes').mockResolvedValue([
        { id: 'h-1', identifier: 'H-1', workspace_id: 'ws-1', name: 'Test Hero', description: null, is_primary: true, created_at: '', updated_at: '' }
      ]);
      vi.spyOn(villainsApi, 'getAllVillains').mockResolvedValue([
        { id: 'v-1', identifier: 'V-1', user_id: 'u-1', workspace_id: 'ws-1', name: 'Test Villain', villain_type: VillainType.EXTERNAL, description: 'desc', severity: 5, is_defeated: false, created_at: '', updated_at: '' }
      ]);
      vi.spyOn(productStrategyApi, 'getStrategicPillars').mockResolvedValue([]);
      vi.spyOn(productOutcomesApi, 'getProductOutcomes').mockResolvedValue([]);
      vi.spyOn(productStrategyApi, 'getRoadmapThemes').mockResolvedValue([]);
      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue([]);

      const { result } = renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(result.current.foundationProgress.hasVision).toBe(true);
        expect(result.current.foundationProgress.hasHeroes).toBe(true);
        expect(result.current.foundationProgress.hasVillains).toBe(true);
      });
    });

    it('should transition to complete when initiative is detected', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([mockWorkspace]);

      vi.spyOn(productStrategyApi, 'getWorkspaceVision').mockResolvedValue({
        id: 'v-1',
        workspace_id: 'ws-1',
        vision_text: 'Test vision',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      vi.spyOn(heroesApi, 'getAllHeroes').mockResolvedValue([
        { id: 'h-1', identifier: 'H-1', workspace_id: 'ws-1', name: 'Test Hero', description: null, is_primary: true, created_at: '', updated_at: '' }
      ]);
      vi.spyOn(villainsApi, 'getAllVillains').mockResolvedValue([
        { id: 'v-1', identifier: 'V-1', user_id: 'u-1', workspace_id: 'ws-1', name: 'Test Villain', villain_type: VillainType.EXTERNAL, description: 'desc', severity: 5, is_defeated: false, created_at: '', updated_at: '' }
      ]);
      vi.spyOn(productStrategyApi, 'getStrategicPillars').mockResolvedValue([
        { id: 'p-1', workspace_id: 'ws-1', name: 'Pillar 1', description: null, display_order: 0, outcome_ids: [], created_at: '', updated_at: '' },
        { id: 'p-2', workspace_id: 'ws-1', name: 'Pillar 2', description: null, display_order: 1, outcome_ids: [], created_at: '', updated_at: '' },
      ]);
      vi.spyOn(productOutcomesApi, 'getProductOutcomes').mockResolvedValue([
        {
          id: 'o-1', workspace_id: 'ws-1', name: 'Outcome 1', description: null, display_order: 0, pillar_ids: [], created_at: '', updated_at: '',
          theme_ids: []
        },
        {
          id: 'o-2', workspace_id: 'ws-1', name: 'Outcome 2', description: null, display_order: 1, pillar_ids: [], created_at: '', updated_at: '',
          theme_ids: []
        },
      ]);
      vi.spyOn(productStrategyApi, 'getRoadmapThemes').mockResolvedValue([
        { id: 't-1', workspace_id: 'ws-1', name: 'Theme 1', description: 'desc', outcome_ids: [], hero_ids: [], villain_ids: [], created_at: '', updated_at: '' },
      ]);

      const mockInitiative = {
        id: '1',
        title: 'Test Initiative',
        description: '',
        status: 'TO_DO',
        identifier: 'TEST-1',
        user_id: 'user-1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        has_pending_job: false,
        tasks: [],
        type: null
      };
      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue([mockInitiative]);

      const { result } = renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(result.current.status).toBe('complete');
      });

      expect(result.current.hasWorkspace).toBe(true);
      expect(result.current.hasInitiatives).toBe(true);
      expect(result.current.initiativeCount).toBe(1);
      expect(result.current.foundationProgress.hasInitiative).toBe(true);
    });

    it('should handle foundation API errors gracefully with Promise.allSettled', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([mockWorkspace]);

      vi.spyOn(productStrategyApi, 'getWorkspaceVision').mockRejectedValue(new Error('Network error'));
      vi.spyOn(heroesApi, 'getAllHeroes').mockRejectedValue(new Error('Network error'));
      vi.spyOn(villainsApi, 'getAllVillains').mockRejectedValue(new Error('Network error'));
      vi.spyOn(productStrategyApi, 'getStrategicPillars').mockRejectedValue(new Error('Network error'));
      vi.spyOn(productOutcomesApi, 'getProductOutcomes').mockRejectedValue(new Error('Network error'));
      vi.spyOn(productStrategyApi, 'getRoadmapThemes').mockRejectedValue(new Error('Network error'));
      vi.spyOn(initiativesApi, 'getAllInitiatives').mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(result.current.status).toBe('polling-foundation');
      });

      expect(result.current.foundationProgress).toEqual({
        hasVision: false,
        hasHeroes: false,
        hasVillains: false,
        hasPillars: false,
        hasOutcomes: false,
        hasThemes: false,
        hasInitiative: false,
      });
    });
  });

  describe('Cleanup', () => {
    it('should cleanup on unmount without errors', () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([]);

      const { unmount } = renderHook(() => useOnboardingPolling());

      expect(() => unmount()).not.toThrow();
    });
  });
});
