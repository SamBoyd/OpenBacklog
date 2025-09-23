import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';

import { useSuggestedImprovements } from '#hooks/diffs/useSuggestedImprovements';

// Mock the hooks first
vi.mock('#hooks/diffs/useSuggestedImprovements', () => ({
  useSuggestedImprovements: vi.fn()
}));

vi.mock('#contexts/TasksContext', () => ({
  useTasksContext: vi.fn()
}));

vi.mock('#contexts/InitiativesContext', () => ({
  useInitiativesContext: vi.fn()
}));

vi.mock('#contexts/AiImprovementsContext', () => ({
  useAiImprovementsContext: vi.fn().mockReturnValue({
    jobResult: {},
    deleteJob: vi.fn(),
  })
}));

import {
  setupDefaultMocks,
  setupEmptyImprovements,
  renderSuggestionsHook
} from './SuggestionsToBeResolvedContext.testUtils';

const DEFAULT_RESOLUTION_STATE = {
  isResolved: false,
  isAccepted: false,
  resolvedValue: null
};

describe('SuggestionsToBeResolvedContext - Basic Functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  describe('when both initiativeImprovements and taskImprovements are empty', () => {
    beforeEach(() => {
      setupEmptyImprovements();
    });

    it('should return empty suggestions and allResolved as true', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toEqual([]);
      expect(result.current.fieldSuggestions).toEqual([]);
      expect(result.current.entitySuggestions).toEqual([]);
      expect(result.current.resolutions).toEqual({});
      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges()).toEqual([]);
    });

    it('should provide all required functions', () => {
      const { result } = renderSuggestionsHook();

      expect(typeof result.current.resolve).toBe('function');
      expect(typeof result.current.rollback).toBe('function');
      expect(typeof result.current.acceptAll).toBe('function');
      expect(typeof result.current.rejectAll).toBe('function');
      expect(typeof result.current.rollbackAll).toBe('function');
      expect(typeof result.current.getResolutionState).toBe('function');
      expect(typeof result.current.isFullyResolved).toBe('function');
    });
  });

  describe('core resolution functions', () => {
    beforeEach(() => {
      // Set up a simple test case with one suggestion
      (useSuggestedImprovements as any).mockReturnValue({
        initiativeImprovements: {
          'new-0': {
            action: 'CREATE',
            title: 'Test Initiative',
            description: 'Test description',
            workspace_identifier: 'workspace-1'
          }
        },
        taskImprovements: {}
      });
    });

    it('should handle basic resolution workflow', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(1);
      expect(result.current.allResolved).toBe(false);

      const suggestionPath = result.current.suggestions[0].path;

      // Test resolve function
      act(() => {
        result.current.resolve(suggestionPath, true);
      });

      expect(result.current.allResolved).toBe(true);
      expect(result.current.getResolutionState(suggestionPath)?.isResolved).toBe(true);
      expect(result.current.getResolutionState(suggestionPath)?.isAccepted).toBe(true);

      // Test rollback function
      act(() => {
        result.current.rollback(suggestionPath);
      });

      expect(result.current.allResolved).toBe(false);
      expect(result.current.getResolutionState(suggestionPath)).toEqual(DEFAULT_RESOLUTION_STATE);
    });

    it('should handle acceptance with custom values', () => {
      const { result } = renderSuggestionsHook();
      const suggestionPath = result.current.suggestions[0].path;
      const customValue = 'Custom Modified Title';

      act(() => {
        result.current.resolve(suggestionPath, true, customValue);
      });

      const resolutionState = result.current.getResolutionState(suggestionPath);
      expect(resolutionState?.resolvedValue).toBe(customValue);
    });

    it('should handle rejection properly', () => {
      const { result } = renderSuggestionsHook();
      const suggestionPath = result.current.suggestions[0].path;

      act(() => {
        result.current.resolve(suggestionPath, false);
      });

      const resolutionState = result.current.getResolutionState(suggestionPath);
      expect(resolutionState?.isResolved).toBe(true);
      expect(resolutionState?.isAccepted).toBe(false);
      expect(resolutionState?.resolvedValue == null).toBe(true); // Could be null or undefined
      expect(result.current.getAcceptedChanges()).toHaveLength(0);
    });

    it('should implement isFullyResolved function correctly', () => {
      const { result } = renderSuggestionsHook();
      const suggestionPath = result.current.suggestions[0].path;

      expect(result.current.isFullyResolved()).toBe(false);
      expect(result.current.isFullyResolved('initiative.new-0')).toBe(false);

      act(() => {
        result.current.resolve(suggestionPath, true);
      });

      expect(result.current.isFullyResolved()).toBe(true);
      expect(result.current.isFullyResolved('initiative.new-0')).toBe(true);
    });
  });

  describe('bulk operations', () => {
    beforeEach(() => {
      // Set up multiple suggestions for bulk operations
      (useSuggestedImprovements as any).mockReturnValue({
        initiativeImprovements: {
          'new-0': {
            action: 'CREATE',
            title: 'First Initiative',
            description: 'First description',
            workspace_identifier: 'workspace-1'
          },
          'new-1': {
            action: 'CREATE',
            title: 'Second Initiative',
            description: 'Second description',
            workspace_identifier: 'workspace-1'
          }
        },
        taskImprovements: {}
      });
    });

    it('should accept all suggestions with acceptAll', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(2);
      expect(result.current.allResolved).toBe(false);

      act(() => {
        result.current.acceptAll();
      });

      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges()).toHaveLength(2);
    });

    it('should reject all suggestions with rejectAll', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(2);

      act(() => {
        result.current.rejectAll();
      });

      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges()).toHaveLength(0);
    });

    it('should rollback all resolutions with rollbackAll', () => {
      const { result } = renderSuggestionsHook();

      // First accept all
      act(() => {
        result.current.acceptAll();
      });

      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges()).toHaveLength(2);

      // Then rollback all
      act(() => {
        result.current.rollbackAll();
      });

      expect(result.current.allResolved).toBe(false);
      expect(result.current.getAcceptedChanges()).toHaveLength(0);

      // All resolution states should be null
      result.current.suggestions.forEach(suggestion => {
        expect(result.current.getResolutionState(suggestion.path)).toEqual(DEFAULT_RESOLUTION_STATE);
      });
    });
  });

  describe('edge cases and error handling', () => {
    beforeEach(() => {
      setupEmptyImprovements();
    });

    it('should handle resolution of non-existent paths gracefully', () => {
      const { result } = renderSuggestionsHook();

      // Try to resolve a path that doesn't exist
      act(() => {
        result.current.resolve('non-existent.path', true);
      });

      // The behavior might create a resolution state even for non-existent paths
      // This is acceptable behavior - let's verify it doesn't break anything
      expect(result.current.allResolved).toBe(true); // Still true because no real suggestions
    });

    it('should handle rollback of non-existent paths gracefully', () => {
      const { result } = renderSuggestionsHook();

      // Try to rollback a path that doesn't exist
      act(() => {
        result.current.rollback('non-existent.path');
      });

      expect(result.current.getResolutionState('non-existent.path')).toEqual(DEFAULT_RESOLUTION_STATE);
    });

    it('should handle bulk operations on empty suggestions', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(0);

      // These should not throw errors
      act(() => {
        result.current.acceptAll();
        result.current.rejectAll();
        result.current.rollbackAll();
      });

      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges()).toHaveLength(0);
    });
  });
});