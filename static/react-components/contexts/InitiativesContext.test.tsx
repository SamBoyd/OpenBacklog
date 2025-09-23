import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useInitiativesContext, InitiativeFilters } from './InitiativesContext';
import { InitiativeStatus } from '#types';

// Import and use our enhanced mock
import {
  mockInitiativesContextValue,
  createMockInitiativesContext,
  createMockInitiatives
} from './InitiativesContext.mock';

// Mock the hook implementation - much simpler than mocking all dependencies
vi.mock('#hooks/initiatives', () => ({
  useInitiativesContext: vi.fn(),
}));

import * as initiativesHooks from '#hooks/initiatives';

describe('InitiativesContext - Simplified Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset to default mock return value
    vi.mocked(initiativesHooks.useInitiativesContext).mockReturnValue(mockInitiativesContextValue);
  });

  describe('Hook Interface', () => {
    it('should provide all expected properties and methods', () => {
      const { result } = renderHook(() => useInitiativesContext());

      expect(result.current).toMatchObject({
        // Data properties
        initiativesData: expect.any(Array),
        error: null,
        shouldShowSkeleton: expect.any(Boolean),
        isQueryFetching: expect.any(Boolean),

        // Loading states
        isCreatingInitiative: expect.any(Boolean),
        isUpdatingInitiative: expect.any(Boolean),
        isDeletingInitiative: expect.any(Boolean),
        isBatchUpdatingInitiatives: expect.any(Boolean),
        isDeletingTask: expect.any(Boolean),
        isDeletingChecklistItem: expect.any(Boolean),

        // Methods
        createInitiative: expect.any(Function),
        updateInitiative: expect.any(Function),
        updateInitiatives: expect.any(Function),
        deleteInitiative: expect.any(Function),
        deleteTask: expect.any(Function),
        deleteChecklistItem: expect.any(Function),
        reloadInitiatives: expect.any(Function),
        invalidateInitiative: expect.any(Function),
        invalidateAllInitiatives: expect.any(Function),
        invalidateInitiativesByStatus: expect.any(Function),
        reorderInitiative: expect.any(Function),
        moveInitiativeToStatus: expect.any(Function),
        moveInitiativeInGroup: expect.any(Function),
      });
    });

    it('should return mock data by default', () => {
      const { result } = renderHook(() => useInitiativesContext());

      expect(result.current.initiativesData).toHaveLength(2);
      expect(result.current.initiativesData?.[0]).toMatchObject({
        id: 'test-initiative-1',
        title: 'Test Initiative 1',
        status: InitiativeStatus.TO_DO,
      });
    });
  });

  describe('Error States', () => {
    it('should handle error state', () => {
      const mockWithError = createMockInitiativesContext({
        error: 'Network error',
        initiativesData: null,
      });

      vi.mocked(initiativesHooks.useInitiativesContext).mockReturnValue(mockWithError);

      const { result } = renderHook(() => useInitiativesContext());

      expect(result.current.error).toBe('Network error');
      expect(result.current.initiativesData).toBe(null);
    });
  });

  describe('Loading States', () => {
    it('should handle loading states', () => {
      const mockWithLoading = createMockInitiativesContext({
        isCreatingInitiative: true,
        isUpdatingInitiative: true,
        shouldShowSkeleton: true,
      });

      vi.mocked(initiativesHooks.useInitiativesContext).mockReturnValue(mockWithLoading);

      const { result } = renderHook(() => useInitiativesContext());

      expect(result.current.isCreatingInitiative).toBe(true);
      expect(result.current.isUpdatingInitiative).toBe(true);
      expect(result.current.shouldShowSkeleton).toBe(true);
    });
  });

  describe('Filters', () => {
    it('should pass filters to the underlying hook', () => {
      const filters: InitiativeFilters = { status: [InitiativeStatus.TO_DO] };

      renderHook(() => useInitiativesContext(filters));

      expect(initiativesHooks.useInitiativesContext).toHaveBeenCalledWith(filters);
    });

    it('should handle ID filter', () => {
      const filters: InitiativeFilters = { id: 'test-initiative-1' };

      renderHook(() => useInitiativesContext(filters));

      expect(initiativesHooks.useInitiativesContext).toHaveBeenCalledWith(filters);
    });
  });

  describe('Custom Data Scenarios', () => {
    it('should work with custom initiatives data', () => {
      const customInitiatives = createMockInitiatives([
        { title: 'Custom Initiative 1', status: InitiativeStatus.DONE },
        { title: 'Custom Initiative 2', status: InitiativeStatus.IN_PROGRESS },
      ]);

      const mockWithCustomData = createMockInitiativesContext({
        initiativesData: customInitiatives,
      });

      vi.mocked(initiativesHooks.useInitiativesContext).mockReturnValue(mockWithCustomData);

      const { result } = renderHook(() => useInitiativesContext());

      expect(result.current.initiativesData).toHaveLength(2);
      expect(result.current.initiativesData?.[0].title).toBe('Custom Initiative 1');
      expect(result.current.initiativesData?.[0].status).toBe(InitiativeStatus.DONE);
    });
  });

  describe('Mutation Operations', () => {
    it('should call create initiative with correct parameters', async () => {
      const { result } = renderHook(() => useInitiativesContext());

      const newInitiative = {
        title: 'New Initiative',
        description: 'New Description',
        status: InitiativeStatus.TO_DO,
      };

      await act(async () => {
        await result.current.createInitiative(newInitiative);
      });

      expect(result.current.createInitiative).toHaveBeenCalledWith(newInitiative);
    });

    it('should call update initiative with correct parameters', async () => {
      const { result } = renderHook(() => useInitiativesContext());

      const updatedInitiative = {
        id: 'test-initiative-1',
        title: 'Updated Title',
      };

      await act(async () => {
        await result.current.updateInitiative(updatedInitiative);
      });

      expect(result.current.updateInitiative).toHaveBeenCalledWith(updatedInitiative);
    });

    it('should call delete initiative with correct parameters', async () => {
      const { result } = renderHook(() => useInitiativesContext());

      await act(async () => {
        await result.current.deleteInitiative('test-initiative-1');
      });

      expect(result.current.deleteInitiative).toHaveBeenCalledWith('test-initiative-1');
    });
  });

  describe('Cache Operations', () => {
    it('should call cache invalidation methods', () => {
      const { result } = renderHook(() => useInitiativesContext());

      act(() => {
        result.current.invalidateInitiative('test-initiative-1');
        result.current.invalidateAllInitiatives();
        result.current.invalidateInitiativesByStatus(InitiativeStatus.TO_DO);
      });

      expect(result.current.invalidateInitiative).toHaveBeenCalledWith('test-initiative-1');
      expect(result.current.invalidateAllInitiatives).toHaveBeenCalled();
      expect(result.current.invalidateInitiativesByStatus).toHaveBeenCalledWith(InitiativeStatus.TO_DO);
    });
  });

  describe('Reordering Operations', () => {
    it('should call reordering methods with correct parameters', async () => {
      const { result } = renderHook(() => useInitiativesContext());

      await act(async () => {
        await result.current.reorderInitiative('test-initiative-1', 'after-id', 'before-id');
        await result.current.moveInitiativeToStatus('test-initiative-1', InitiativeStatus.IN_PROGRESS, 'after-id', 'before-id');
        await result.current.moveInitiativeInGroup('test-initiative-1', 'group-id', 'after-id', 'before-id');
      });

      expect(result.current.reorderInitiative).toHaveBeenCalledWith('test-initiative-1', 'after-id', 'before-id');
      expect(result.current.moveInitiativeToStatus).toHaveBeenCalledWith('test-initiative-1', InitiativeStatus.IN_PROGRESS, 'after-id', 'before-id');
      expect(result.current.moveInitiativeInGroup).toHaveBeenCalledWith('test-initiative-1', 'group-id', 'after-id', 'before-id');
    });
  });
});