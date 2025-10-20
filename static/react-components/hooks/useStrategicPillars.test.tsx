import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useStrategicPillars } from './useStrategicPillars';
import type { PillarDto } from '#api/productStrategy';

// Mock the product strategy API
vi.mock('#api/productStrategy', () => ({
  getStrategicPillars: vi.fn(),
  createStrategicPillar: vi.fn(),
}));

import * as mockProductStrategyApi from '#api/productStrategy';

/**
 * Helper function to create a test wrapper with QueryClient
 * @returns {object} Object containing TestWrapper component and queryClient instance
 */
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { TestWrapper, queryClient };
};

describe('useStrategicPillars', () => {
  const workspaceId = 'test-workspace-id';

  const mockPillar1: PillarDto = {
    id: 'pillar-1',
    workspace_id: workspaceId,
    name: 'Developer Experience',
    description: 'Make developers love our product',
    anti_strategy: 'Not enterprise features',
    display_order: 0,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };

  const mockPillar2: PillarDto = {
    id: 'pillar-2',
    workspace_id: workspaceId,
    name: 'AI-Native',
    description: 'Build AI into core product',
    anti_strategy: null,
    display_order: 1,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  };

  const mockPillars = [mockPillar1, mockPillar2];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Initial Loading', () => {
    it('should initialize with loading state', () => {
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockImplementation(
        () => new Promise(() => {})
      );

      const { TestWrapper } = createTestWrapper();
      const { result } = renderHook(() => useStrategicPillars(workspaceId), {
        wrapper: TestWrapper,
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.pillars).toEqual([]);
      expect(result.current.error).toBe(null);
      expect(result.current.isCreating).toBe(false);
    });

    it('should load pillars successfully', async () => {
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockResolvedValue(
        mockPillars
      );

      const { TestWrapper } = createTestWrapper();
      const { result } = renderHook(() => useStrategicPillars(workspaceId), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.pillars).toEqual(mockPillars);
      expect(result.current.error).toBe(null);
    });

    it('should return empty array when no pillars exist', async () => {
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockResolvedValue([]);

      const { TestWrapper } = createTestWrapper();
      const { result } = renderHook(() => useStrategicPillars(workspaceId), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.pillars).toEqual([]);
      expect(result.current.error).toBe(null);
    });
  });

  describe('Error Handling', () => {
    it('should handle fetch errors gracefully', async () => {
      const error = new Error('Failed to fetch pillars');
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockRejectedValue(error);

      const { TestWrapper } = createTestWrapper();
      const { result } = renderHook(() => useStrategicPillars(workspaceId), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.pillars).toEqual([]);
      expect(result.current.error).toBeDefined();
    });
  });

  describe('createPillar', () => {
    const newPillarRequest = {
      name: 'New Pillar',
      description: 'A new pillar',
      anti_strategy: null,
    };

    const newPillar: PillarDto = {
      id: 'pillar-3',
      workspace_id: workspaceId,
      name: newPillarRequest.name,
      description: newPillarRequest.description,
      anti_strategy: newPillarRequest.anti_strategy,
      display_order: 2,
      created_at: '2025-01-03T00:00:00Z',
      updated_at: '2025-01-03T00:00:00Z',
    };

    it('should create pillar successfully', async () => {
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockResolvedValue(
        mockPillars
      );
      vi.mocked(mockProductStrategyApi.createStrategicPillar).mockResolvedValue(
        newPillar
      );

      const { TestWrapper } = createTestWrapper();
      const { result } = renderHook(() => useStrategicPillars(workspaceId), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.createPillar(newPillarRequest);
      });

      expect(mockProductStrategyApi.createStrategicPillar).toHaveBeenCalledWith(
        workspaceId,
        newPillarRequest
      );

      // Wait for the query to refetch
      await waitFor(() => {
        expect(result.current.isCreating).toBe(false);
      });
    });

    it('should set creating state during pillar creation', async () => {
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockResolvedValue(
        mockPillars
      );

      let resolveMutation: (value: PillarDto) => void;
      const mutationPromise = new Promise<PillarDto>((resolve) => {
        resolveMutation = resolve;
      });
      vi.mocked(mockProductStrategyApi.createStrategicPillar).mockReturnValue(
        mutationPromise
      );

      const { TestWrapper } = createTestWrapper();
      const { result } = renderHook(() => useStrategicPillars(workspaceId), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Start the pillar creation but don't await it immediately
      act(() => {
        result.current.createPillar(newPillarRequest);
      });

      // Now resolve the mutation and wait for completion
      act(() => {
        resolveMutation!(newPillar);
      });

      await waitFor(() => {
        expect(result.current.isCreating).toBe(false);
      });
    });

    it('should handle createPillar errors', async () => {
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockResolvedValue(
        mockPillars
      );

      const error = new Error('Failed to create pillar');
      vi.mocked(mockProductStrategyApi.createStrategicPillar).mockRejectedValue(
        error
      );

      const { TestWrapper } = createTestWrapper();
      const { result } = renderHook(() => useStrategicPillars(workspaceId), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        result.current.createPillar(newPillarRequest);
      });

      await waitFor(() => {
        expect(result.current.createError).toBeDefined();
      });
    });
  });

  describe('Workspace ID Dependency', () => {
    it('should not fetch when workspaceId is empty', () => {
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockResolvedValue(
        mockPillars
      );

      const { TestWrapper } = createTestWrapper();
      renderHook(() => useStrategicPillars(''), {
        wrapper: TestWrapper,
      });

      expect(mockProductStrategyApi.getStrategicPillars).not.toHaveBeenCalled();
    });

    it('should fetch when workspaceId is provided', async () => {
      vi.mocked(mockProductStrategyApi.getStrategicPillars).mockResolvedValue(
        mockPillars
      );

      const { TestWrapper } = createTestWrapper();
      renderHook(() => useStrategicPillars(workspaceId), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(mockProductStrategyApi.getStrategicPillars).toHaveBeenCalledWith(
          workspaceId
        );
      });
    });
  });
});
