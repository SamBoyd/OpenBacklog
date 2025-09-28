import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { ManagedEntityAction } from '#types';


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
    markJobAsResolved: vi.fn(),
  })
}));

import {
  setupDefaultMocks,
  setupInitiativeImprovement,
  setupInitiativesContextWith,
  renderSuggestionsHook,
  testInitiativeData,
  testContextData,
  expectEntitySuggestionStructure,
  expectFieldSuggestionStructure,
  expectResolutionState
} from './SuggestionsToBeResolvedContext.testUtils';

describe('SuggestionsToBeResolvedContext - Initiative Operations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  describe('CREATE initiative operations', () => {
    beforeEach(() => {
      setupInitiativeImprovement('new-0', testInitiativeData.createInitiative);
    });

    it('should transform CREATE initiative into entity suggestion', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(1);
      expect(result.current.entitySuggestions).toHaveLength(1);
      expect(result.current.fieldSuggestions).toHaveLength(0);

      const suggestion = result.current.suggestions[0];
      expectEntitySuggestionStructure(suggestion, 'initiative.new-0', ManagedEntityAction.CREATE, 'new-0');
      expect(suggestion.suggestedValue.title).toBe('New Initiative');
      expect(suggestion.suggestedValue.description).toBe('A new initiative to create');
    });

    it('should show allResolved as false when not resolved', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.allResolved).toBe(false);
      expect(result.current.isFullyResolved()).toBe(false);
      expect(result.current.getResolutionState('initiative.new-0')).toEqual({
        isResolved: false,
        isAccepted: false,
        resolvedValue: null
      });
    });

    it('should accept CREATE initiative suggestion', () => {
      const { result } = renderSuggestionsHook();

      act(() => {
        result.current.resolve('initiative.new-0', true);
      });

      const resolutionState = result.current.getResolutionState('initiative.new-0');
      expectResolutionState(resolutionState, true, true);
      expect(resolutionState?.resolvedValue.title).toBe('New Initiative');

      expect(result.current.allResolved).toBe(true);
      expect(result.current.isFullyResolved()).toBe(true);

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);
      expect(acceptedChanges[0].action).toBe('CREATE');
      if (acceptedChanges[0].action === 'CREATE') {
        expect(acceptedChanges[0].title).toBe('New Initiative');
      }
    });

    it('should reject CREATE initiative suggestion', () => {
      const { result } = renderSuggestionsHook();

      act(() => {
        result.current.resolve('initiative.new-0', false);
      });

      const resolutionState = result.current.getResolutionState('initiative.new-0');
      expectResolutionState(resolutionState, true, false, null);

      expect(result.current.allResolved).toBe(true);
      expect(result.current.isFullyResolved()).toBe(true);

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });

    it('should handle accept then rollback CREATE initiative suggestion', () => {
      const { result } = renderSuggestionsHook();

      // Accept first
      act(() => {
        result.current.resolve('initiative.new-0', true);
      });
      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges()).toHaveLength(1);

      // Then rollback
      act(() => {
        result.current.rollback('initiative.new-0');
      });

      expect(result.current.getResolutionState('initiative.new-0')).toEqual({
        isResolved: false,
        isAccepted: false,
        resolvedValue: null
      });
      expect(result.current.allResolved).toBe(false);
      expect(result.current.isFullyResolved()).toBe(false);
      expect(result.current.getAcceptedChanges()).toHaveLength(0);
    });

    it('should have no originalValue for CREATE initiatives (entity-level only)', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.fieldSuggestions).toHaveLength(0);
      expect(result.current.entitySuggestions).toHaveLength(1);

      const entitySuggestion = result.current.entitySuggestions[0];
      expect(entitySuggestion.type).toBe('entity');
      expect(entitySuggestion.action).toBe('CREATE');
      expect(entitySuggestion.originalValue).toBeUndefined();
    });
  });

  describe('DELETE initiative operations', () => {
    beforeEach(() => {
      setupInitiativeImprovement('INIT-123', testInitiativeData.deleteInitiative);
    });

    it('should transform DELETE initiative into entity suggestion', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(1);
      expect(result.current.entitySuggestions).toHaveLength(1);
      expect(result.current.fieldSuggestions).toHaveLength(0);

      const suggestion = result.current.suggestions[0];
      expectEntitySuggestionStructure(suggestion, 'initiative.INIT-123', ManagedEntityAction.DELETE, 'INIT-123');
      expect(suggestion.suggestedValue.action).toBe('DELETE');
      expect(suggestion.suggestedValue.identifier).toBe('INIT-123');
    });

    it('should show allResolved as false when not resolved', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.allResolved).toBe(false);
      expect(result.current.isFullyResolved()).toBe(false);
      expect(result.current.getResolutionState('initiative.INIT-123')).toEqual({
        isResolved: false,
        isAccepted: false,
        resolvedValue: null
      });
    });

    it('should accept DELETE initiative suggestion', () => {
      const { result } = renderSuggestionsHook();

      act(() => {
        result.current.resolve('initiative.INIT-123', true);
      });

      const resolutionState = result.current.getResolutionState('initiative.INIT-123');
      expectResolutionState(resolutionState, true, true);
      expect(resolutionState?.resolvedValue.action).toBe('DELETE');
      expect(resolutionState?.resolvedValue.identifier).toBe('INIT-123');

      expect(result.current.allResolved).toBe(true);

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);
      expect(acceptedChanges[0].action).toBe('DELETE');
      if (acceptedChanges[0].action === 'DELETE') {
        expect(acceptedChanges[0].identifier).toBe('INIT-123');
      }
    });

    it('should reject DELETE initiative suggestion', () => {
      const { result } = renderSuggestionsHook();

      act(() => {
        result.current.resolve('initiative.INIT-123', false);
      });

      const resolutionState = result.current.getResolutionState('initiative.INIT-123');
      expectResolutionState(resolutionState, true, false, null);

      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges()).toHaveLength(0);
    });

    it('should handle accept then rollback DELETE initiative suggestion', () => {
      const { result } = renderSuggestionsHook();

      // Accept first
      act(() => {
        result.current.resolve('initiative.INIT-123', true);
      });
      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges()).toHaveLength(1);

      // Then rollback
      act(() => {
        result.current.rollback('initiative.INIT-123');
      });

      expect(result.current.getResolutionState('initiative.INIT-123')).toEqual({
        isResolved: false,
        isAccepted: false,
        resolvedValue: null
      });
      expect(result.current.allResolved).toBe(false);
      expect(result.current.getAcceptedChanges()).toHaveLength(0);
    });
  });

  describe('UPDATE initiative with field-level suggestions', () => {
    beforeEach(() => {
      setupInitiativeImprovement('INIT-123', testInitiativeData.updateInitiative);
    });

    it('should transform UPDATE with title+description into field suggestions', () => {
      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(3);
      expect(result.current.entitySuggestions).toHaveLength(1);
      expect(result.current.fieldSuggestions).toHaveLength(2);

      // Check entity-level suggestion
      const entitySuggestion = result.current.entitySuggestions[0];
      expectEntitySuggestionStructure(entitySuggestion, 'initiative.INIT-123', ManagedEntityAction.UPDATE, 'INIT-123');

      // Check title field suggestion
      const titleSuggestion = result.current.fieldSuggestions.find(s => s.fieldName === 'title');
      expect(titleSuggestion).toBeDefined();
      expectFieldSuggestionStructure(
        titleSuggestion!,
        'initiative.INIT-123.title',
        'title',
        'Updated Initiative Title',
        'INIT-123'
      );

      // Check description field suggestion
      const descSuggestion = result.current.fieldSuggestions.find(s => s.fieldName === 'description');
      expect(descSuggestion).toBeDefined();
      expectFieldSuggestionStructure(
        descSuggestion!,
        'initiative.INIT-123.description',
        'description',
        'Updated description content',
        'INIT-123'
      );
    });

    it('should populate originalValue for field suggestions when initiative exists', () => {
      setupInitiativesContextWith([testContextData.existingInitiative]);

      const { result } = renderSuggestionsHook();

      const titleSuggestion = result.current.fieldSuggestions.find(s => s.fieldName === 'title');
      expect(titleSuggestion).toBeDefined();
      expect(titleSuggestion!.originalValue).toBe('Original Initiative Title');
      expect(titleSuggestion!.suggestedValue).toBe('Updated Initiative Title');

      const descSuggestion = result.current.fieldSuggestions.find(s => s.fieldName === 'description');
      expect(descSuggestion).toBeDefined();
      expect(descSuggestion!.originalValue).toBe('Original initiative description');
      expect(descSuggestion!.suggestedValue).toBe('Updated description content');
    });

    it('should handle originalValue when initiative not found in context', () => {
      setupInitiativesContextWith([]);

      const { result } = renderSuggestionsHook();

      const titleSuggestion = result.current.fieldSuggestions.find(s => s.fieldName === 'title');
      expect(titleSuggestion).toBeDefined();
      expect(titleSuggestion!.originalValue).toBeUndefined();
      expect(titleSuggestion!.suggestedValue).toBe('Updated Initiative Title');
    });

    it('should accept title field but reject description field', () => {
      const { result } = renderSuggestionsHook();

      // Accept title field
      act(() => {
        result.current.resolve('initiative.INIT-123.title', true);
      });

      // Reject description field
      act(() => {
        result.current.resolve('initiative.INIT-123.description', false);
      });

      // Verify individual field resolutions
      expect(result.current.getResolutionState('initiative.INIT-123.title')?.isAccepted).toBe(true);
      expect(result.current.getResolutionState('initiative.INIT-123.description')?.isAccepted).toBe(false);
      expect(result.current.getResolutionState('initiative.INIT-123')).toEqual({
        isResolved: false,
        isAccepted: false,
        resolvedValue: null
      }); // Entity still unresolved

      expect(result.current.isFullyResolved('initiative.INIT-123')).toBe(true);
      expect(result.current.allResolved).toBe(true);

      // Accepted changes should contain only title update
      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);
      expect(acceptedChanges[0].action).toBe('UPDATE');
      if (acceptedChanges[0].action === 'UPDATE') {
        expect(acceptedChanges[0].identifier).toBe('INIT-123');
        expect(acceptedChanges[0].title).toBe('Updated Initiative Title');
        expect(acceptedChanges[0].description).toBeUndefined(); // Description rejected
      }
    });

    it('should accept both field suggestions individually', () => {
      const { result } = renderSuggestionsHook();

      // Accept both fields individually
      act(() => {
        result.current.resolve('initiative.INIT-123.title', true);
        result.current.resolve('initiative.INIT-123.description', true);
      });

      // Both fields should be accepted
      expect(result.current.getResolutionState('initiative.INIT-123.title')?.isAccepted).toBe(true);
      expect(result.current.getResolutionState('initiative.INIT-123.description')?.isAccepted).toBe(true);

      // Accepted changes should contain both updates
      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);
      expect(acceptedChanges[0].action).toBe('UPDATE');
      if (acceptedChanges[0].action === 'UPDATE') {
        expect(acceptedChanges[0].identifier).toBe('INIT-123');
        expect(acceptedChanges[0].title).toBe('Updated Initiative Title');
        expect(acceptedChanges[0].description).toBe('Updated description content');
      }
    });

    it('should handle field-level resolution with custom values', () => {
      const { result } = renderSuggestionsHook();

      // Accept title with custom value, reject description
      act(() => {
        result.current.resolve('initiative.INIT-123.title', true, 'Custom Modified Title');
        result.current.resolve('initiative.INIT-123.description', false);
      });

      // Verify custom value in resolution state
      const titleResolution = result.current.getResolutionState('initiative.INIT-123.title');
      expect(titleResolution?.resolvedValue).toBe('Custom Modified Title');

      // Accepted changes should use custom value
      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);
      if (acceptedChanges[0].action === 'UPDATE') {
        expect(acceptedChanges[0].title).toBe('Custom Modified Title');
        expect(acceptedChanges[0].description).toBeUndefined();
      }
    });

    it('should support field-level rollback functionality', () => {
      const { result } = renderSuggestionsHook();

      // Accept both fields
      act(() => {
        result.current.resolve('initiative.INIT-123.title', true);
        result.current.resolve('initiative.INIT-123.description', true);
      });

      expect(result.current.getAcceptedChanges()).toHaveLength(1);

      // Rollback only title
      act(() => {
        result.current.rollback('initiative.INIT-123.title');
      });

      // Title should be unresolved, description still resolved
      expect(result.current.getResolutionState('initiative.INIT-123.title')).toEqual({
        isResolved: false,
        isAccepted: false,
        resolvedValue: null
      });
      expect(result.current.getResolutionState('initiative.INIT-123.description')?.isAccepted).toBe(true);

      // Accepted changes should only have description
      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);
      if (acceptedChanges[0].action === 'UPDATE') {
        expect(acceptedChanges[0].title).toBeUndefined();
        expect(acceptedChanges[0].description).toBe('Updated description content');
      }
    });
  });

  describe('UPDATE initiative with single field', () => {
    it('should create only title field suggestion when description absent', () => {
      setupInitiativeImprovement('INIT-456', testInitiativeData.updateInitiativeWithTitleOnly);

      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(2);
      expect(result.current.entitySuggestions).toHaveLength(1);
      expect(result.current.fieldSuggestions).toHaveLength(1);

      // Should only have title field suggestion
      const titleSuggestion = result.current.fieldSuggestions[0];
      expectFieldSuggestionStructure(
        titleSuggestion,
        'initiative.INIT-456.title',
        'title',
        'Only Title Updated',
        'INIT-456'
      );

      // Should not have description field suggestion
      const descSuggestion = result.current.fieldSuggestions.find(s => s.fieldName === 'description');
      expect(descSuggestion).toBeUndefined();
    });

    it('should create only description field suggestion when title absent', () => {
      setupInitiativeImprovement('INIT-789', testInitiativeData.updateInitiativeWithDescriptionOnly);

      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(2);
      expect(result.current.entitySuggestions).toHaveLength(1);
      expect(result.current.fieldSuggestions).toHaveLength(1);

      // Should only have description field suggestion
      const descSuggestion = result.current.fieldSuggestions[0];
      expectFieldSuggestionStructure(
        descSuggestion,
        'initiative.INIT-789.description',
        'description',
        'Only Description Updated',
        'INIT-789'
      );

      // Should not have title field suggestion
      const titleSuggestion = result.current.fieldSuggestions.find(s => s.fieldName === 'title');
      expect(titleSuggestion).toBeUndefined();
    });
  });

  describe('field-level rejection uses original value', () => {
    beforeEach(() => {
      setupInitiativesContextWith([testContextData.existingInitiative]);
      setupInitiativeImprovement('INIT-123', testInitiativeData.updateInitiative);
    });

    it('should set resolvedValue to original when initiative field is rejected', () => {
      const { result } = renderSuggestionsHook();

      act(() => {
        result.current.resolve('initiative.INIT-123.title', false);
        result.current.resolve('initiative.INIT-123.description', false);
      });

      const titleResolution = result.current.getResolutionState('initiative.INIT-123.title');
      const descResolution = result.current.getResolutionState('initiative.INIT-123.description');

      expectResolutionState(titleResolution, true, false, 'Original Initiative Title');
      expect(titleResolution?.resolvedValue).not.toBe('Updated Initiative Title');

      expectResolutionState(descResolution, true, false, 'Original initiative description');
      expect(descResolution?.resolvedValue).not.toBe('Updated description content');

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });
  });
});