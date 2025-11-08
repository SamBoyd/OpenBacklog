import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useOnboardingPolling } from './useOnboardingPolling';
import * as workspacesApi from '#api/workspaces';
import * as initiativesApi from '#api/initiatives';

// Mock the API modules
vi.mock('#api/workspaces');
vi.mock('#api/initiatives');

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
    });

    it('should call getAllWorkspaces on mount', async () => {
      const getAllWorkspacesSpy = vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([]);

      renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(getAllWorkspacesSpy).toHaveBeenCalled();
      });
    });

    it('should transition to polling-initiatives when workspace is detected', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([
        { id: '1', name: 'Test Workspace', icon: null, description: null }
      ]);

      vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue([]);

      const { result } = renderHook(() => useOnboardingPolling());

      // Wait for status to update to polling-initiatives
      await waitFor(() => {
        expect(result.current.status).toBe('polling-initiatives');
      });

      expect(result.current.hasWorkspace).toBe(true);
      expect(result.current.workspaceCount).toBe(1);
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

  describe('Stage 2: Initiative Polling', () => {
    it('should poll for initiatives after workspace is detected', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([
        { id: '1', name: 'Test Workspace', icon: null, description: null }
      ]);

      const getAllInitiativesSpy = vi.spyOn(initiativesApi, 'getAllInitiatives').mockResolvedValue([]);

      renderHook(() => useOnboardingPolling());

      // Wait for workspace detection and initiative polling to start
      await waitFor(() => {
        expect(getAllInitiativesSpy).toHaveBeenCalled();
      });
    });

    it('should transition to complete when initiatives are detected', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([
        { id: '1', name: 'Test Workspace', icon: null, description: null }
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

      // Wait for completion
      await waitFor(() => {
        expect(result.current.status).toBe('complete');
      });

      expect(result.current.hasWorkspace).toBe(true);
      expect(result.current.hasInitiatives).toBe(true);
      expect(result.current.initiativeCount).toBe(1);
    });

    it('should handle initiative API errors gracefully', async () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([
        { id: '1', name: 'Test Workspace', icon: null, description: null }
      ]);

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.spyOn(initiativesApi, 'getAllInitiatives').mockRejectedValue(new Error('Network error'));

      renderHook(() => useOnboardingPolling());

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Error polling initiatives:', expect.any(Error));
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Cleanup', () => {
    it('should cleanup on unmount without errors', () => {
      vi.spyOn(workspacesApi, 'getAllWorkspaces').mockResolvedValue([]);

      const { unmount } = renderHook(() => useOnboardingPolling());

      // Should unmount without errors
      expect(() => unmount()).not.toThrow();
    });
  });
});
