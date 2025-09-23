import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';

import { useResolutionOperations } from './useResolutionOperations';
import { UnifiedSuggestion } from './useUnifiedSuggestions';
import { ManagedEntityAction, ManagedInitiativeModel, UpdateInitiativeModel } from '#types';

/**
 * Test suite focused on the getAcceptedChanges function's ability to aggregate
 * field-level suggestions into complete ManagedInitiativeModel objects.
 */
describe('useResolutionOperations - getAcceptedChanges field aggregation', () => {
  
  describe('initiative with field-level suggestions only', () => {
    const mockFieldOnlySuggestions: Record<string, UnifiedSuggestion> = {
      'initiative.INIT-123.title': {
        path: 'initiative.INIT-123.title',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Old Title',
        suggestedValue: 'New Title Value',
        entityIdentifier: 'INIT-123',
        fieldName: 'title'
      },
      'initiative.INIT-123.description': {
        path: 'initiative.INIT-123.description',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Old Description',
        suggestedValue: 'New Description Value',
        entityIdentifier: 'INIT-123',
        fieldName: 'description'
      }
    };

    it('should aggregate accepted initiative field suggestions into UpdateInitiativeModel', () => {
      const { result } = renderHook(() => useResolutionOperations(mockFieldOnlySuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123.title', true);
        result.current.resolve('initiative.INIT-123.description', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change.action).toBe('UPDATE');
      expect(change.identifier).toBe('INIT-123');
      expect(change.title).toBe('New Title Value');
      expect(change.description).toBe('New Description Value');
    });

    it('should include only accepted fields (title yes, description no)', () => {
      const { result } = renderHook(() => useResolutionOperations(mockFieldOnlySuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123.title', true);
        result.current.resolve('initiative.INIT-123.description', false);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change.action).toBe('UPDATE');
      expect(change.identifier).toBe('INIT-123');
      expect(change.title).toBe('New Title Value');
      expect(change.description).toBeUndefined(); // Should not include rejected description
    });

    it('should return empty array when no fields accepted', () => {
      const { result } = renderHook(() => useResolutionOperations(mockFieldOnlySuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123.title', false);
        result.current.resolve('initiative.INIT-123.description', false);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });

    it('should handle mixed acceptance across multiple initiatives', () => {
      const multiInitiativeSuggestions: Record<string, UnifiedSuggestion> = {
        ...mockFieldOnlySuggestions,
        'initiative.INIT-456.title': {
          path: 'initiative.INIT-456.title',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Another Old Title',
          suggestedValue: 'Another New Title',
          entityIdentifier: 'INIT-456',
          fieldName: 'title'
        }
      };

      const { result } = renderHook(() => useResolutionOperations(multiInitiativeSuggestions));

      act(() => {
        // Accept all fields for INIT-123
        result.current.resolve('initiative.INIT-123.title', true);
        result.current.resolve('initiative.INIT-123.description', true);
        // Accept only title for INIT-456
        result.current.resolve('initiative.INIT-456.title', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(2);

      // Find changes by identifier
      const init123Change = acceptedChanges.find(c => c.action === 'UPDATE' && (c as UpdateInitiativeModel).identifier === 'INIT-123') as UpdateInitiativeModel;
      const init456Change = acceptedChanges.find(c => c.action === 'UPDATE' && (c as UpdateInitiativeModel).identifier === 'INIT-456') as UpdateInitiativeModel;

      expect(init123Change).toBeDefined();
      expect(init123Change.title).toBe('New Title Value');
      expect(init123Change.description).toBe('New Description Value');

      expect(init456Change).toBeDefined();
      expect(init456Change.title).toBe('Another New Title');
      expect(init456Change.description).toBeUndefined();
    });
  });

  describe('initiative with task suggestions', () => {
    const mockTaskSuggestions: Record<string, UnifiedSuggestion> = {
      'initiative.INIT-123.tasks.TASK-001': {
        path: 'initiative.INIT-123.tasks.TASK-001',
        type: 'entity',
        action: ManagedEntityAction.CREATE,
        suggestedValue: {
          action: 'CREATE',
          title: 'New Task Title',
          description: 'New task description',
          initiative_identifier: 'INIT-123'
        },
        entityIdentifier: 'INIT-123'
      },
      'initiative.INIT-123.tasks.TASK-002.title': {
        path: 'initiative.INIT-123.tasks.TASK-002.title',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Old Task Title',
        suggestedValue: 'Updated Task Title',
        entityIdentifier: 'INIT-123',
        fieldName: 'title'
      },
      'initiative.INIT-123.tasks.TASK-002.description': {
        path: 'initiative.INIT-123.tasks.TASK-002.description',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Old task description',
        suggestedValue: 'Updated task description',
        entityIdentifier: 'INIT-123',
        fieldName: 'description'
      }
    };

    it('should aggregate accepted task entity suggestions into UpdateInitiativeModel.tasks', () => {
      const { result } = renderHook(() => useResolutionOperations(mockTaskSuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123.tasks.TASK-001', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change.action).toBe('UPDATE');
      expect(change.identifier).toBe('INIT-123');
      expect(change.tasks).toHaveLength(1);
      expect(change.tasks?.[0]).toEqual({
        action: 'CREATE',
        title: 'New Task Title',
        description: 'New task description',
        initiative_identifier: 'INIT-123'
      });
    });

    it('should aggregate accepted task field suggestions into UpdateInitiativeModel.tasks', () => {
      const { result } = renderHook(() => useResolutionOperations(mockTaskSuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123.tasks.TASK-002.title', true);
        result.current.resolve('initiative.INIT-123.tasks.TASK-002.description', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change.action).toBe('UPDATE');
      expect(change.identifier).toBe('INIT-123');
      expect(change.tasks).toHaveLength(1);
      expect(change.tasks?.[0]).toEqual({
        action: 'UPDATE',
        identifier: 'TASK-002',
        title: 'Updated Task Title',
        description: 'Updated task description'
      });
    });

    it('should handle mixed task entity and field suggestions', () => {
      const { result } = renderHook(() => useResolutionOperations(mockTaskSuggestions));

      act(() => {
        // Accept task entity
        result.current.resolve('initiative.INIT-123.tasks.TASK-001', true);
        // Accept task field suggestions
        result.current.resolve('initiative.INIT-123.tasks.TASK-002.title', true);
        result.current.resolve('initiative.INIT-123.tasks.TASK-002.description', false); // Reject description
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change.action).toBe('UPDATE');
      expect(change.identifier).toBe('INIT-123');
      expect(change.tasks).toHaveLength(2);

      // Should have the CREATE task
      expect(change.tasks?.[0]).toEqual({
        action: 'CREATE',
        title: 'New Task Title',
        description: 'New task description',
        initiative_identifier: 'INIT-123'
      });

      // Should have the UPDATE task with only accepted title
      expect(change.tasks?.[1]).toEqual({
        action: 'UPDATE',
        identifier: 'TASK-002',
        title: 'Updated Task Title'
        // description should not be present since it was rejected
      });
    });

    it('should include initiative fields + task aggregations in same UpdateInitiativeModel', () => {
      const mixedSuggestions: Record<string, UnifiedSuggestion> = {
        'initiative.INIT-123.title': {
          path: 'initiative.INIT-123.title',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Old Initiative Title',
          suggestedValue: 'New Initiative Title',
          entityIdentifier: 'INIT-123',
          fieldName: 'title'
        },
        ...mockTaskSuggestions
      };

      const { result } = renderHook(() => useResolutionOperations(mixedSuggestions));

      act(() => {
        // Accept initiative title
        result.current.resolve('initiative.INIT-123.title', true);
        // Accept task entity
        result.current.resolve('initiative.INIT-123.tasks.TASK-001', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change.action).toBe('UPDATE');
      expect(change.identifier).toBe('INIT-123');
      expect(change.title).toBe('New Initiative Title');
      expect(change.tasks).toHaveLength(1);
      expect(change.tasks?.[0]).toEqual({
        action: 'CREATE',
        title: 'New Task Title',
        description: 'New task description',
        initiative_identifier: 'INIT-123'
      });
    });
  });

  describe('mixed entity and field suggestions', () => {
    const mockMixedSuggestions: Record<string, UnifiedSuggestion> = {
      'initiative.INIT-123': {
        path: 'initiative.INIT-123',
        type: 'entity',
        action: ManagedEntityAction.UPDATE,
        suggestedValue: {
          action: 'UPDATE',
          identifier: 'INIT-123',
          title: 'Entity Level Title',
          description: 'Entity Level Description'
        },
        entityIdentifier: 'INIT-123'
      },
      'initiative.INIT-123.title': {
        path: 'initiative.INIT-123.title',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Old Title',
        suggestedValue: 'Field Level Title',
        entityIdentifier: 'INIT-123',
        fieldName: 'title'
      }
    };

    it('should prioritize entity-level over field-level when both exist and entity is accepted', () => {
      const { result } = renderHook(() => useResolutionOperations(mockMixedSuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123', true);
        result.current.resolve('initiative.INIT-123.title', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      // Should use entity-level suggestion, not field aggregation
      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change).toEqual({
        action: 'UPDATE',
        identifier: 'INIT-123',
        title: 'Entity Level Title',
        description: 'Entity Level Description'
      });
    });

    it('should fall back to field aggregation when entity is rejected but fields are accepted', () => {
      const { result } = renderHook(() => useResolutionOperations(mockMixedSuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123', false);
        result.current.resolve('initiative.INIT-123.title', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      // Should use field aggregation since entity was rejected
      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change).toEqual({
        action: 'UPDATE',
        identifier: 'INIT-123',
        title: 'Field Level Title'
      });
    });

    it('should return empty array when entity rejected and no fields accepted', () => {
      const { result } = renderHook(() => useResolutionOperations(mockMixedSuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123', false);
        result.current.resolve('initiative.INIT-123.title', false);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });
  });

  describe('complex multi-initiative scenarios', () => {
    const mockComplexSuggestions: Record<string, UnifiedSuggestion> = {
      // Initiative with entity suggestion
      'initiative.INIT-123': {
        path: 'initiative.INIT-123',
        type: 'entity',
        action: ManagedEntityAction.CREATE,
        suggestedValue: {
          action: 'CREATE',
          title: 'New Initiative',
          description: 'New initiative description'
        },
        entityIdentifier: 'INIT-123'
      },
      // Initiative with only field suggestions
      'initiative.INIT-456.title': {
        path: 'initiative.INIT-456.title',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Old Title 456',
        suggestedValue: 'New Title 456',
        entityIdentifier: 'INIT-456',
        fieldName: 'title'
      },
      // Initiative with mixed suggestions
      'initiative.INIT-789': {
        path: 'initiative.INIT-789',
        type: 'entity',
        action: ManagedEntityAction.DELETE,
        suggestedValue: {
          action: 'DELETE',
          identifier: 'INIT-789'
        },
        entityIdentifier: 'INIT-789'
      },
      'initiative.INIT-789.title': {
        path: 'initiative.INIT-789.title',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Old Title 789',
        suggestedValue: 'New Title 789',
        entityIdentifier: 'INIT-789',
        fieldName: 'title'
      }
    };

    it('should aggregate across multiple initiatives with different patterns', () => {
      const { result } = renderHook(() => useResolutionOperations(mockComplexSuggestions));

      act(() => {
        // Accept entity for INIT-123
        result.current.resolve('initiative.INIT-123', true);
        // Accept field for INIT-456
        result.current.resolve('initiative.INIT-456.title', true);
        // Reject entity but accept field for INIT-789
        result.current.resolve('initiative.INIT-789', false);
        result.current.resolve('initiative.INIT-789.title', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(3);

      // Check INIT-123 (entity-level CREATE)
      const init123 = acceptedChanges.find(c => 
        c.action === 'CREATE' && (c as any).title === 'New Initiative'
      );
      expect(init123).toBeDefined();

      // Check INIT-456 (field aggregation UPDATE)
      const init456 = acceptedChanges.find(c => 
        c.action === 'UPDATE' && (c as UpdateInitiativeModel).identifier === 'INIT-456'
      ) as UpdateInitiativeModel;
      expect(init456).toBeDefined();
      expect(init456.title).toBe('New Title 456');

      // Check INIT-789 (field aggregation UPDATE, entity rejected)
      const init789 = acceptedChanges.find(c => 
        c.action === 'UPDATE' && (c as UpdateInitiativeModel).identifier === 'INIT-789'
      ) as UpdateInitiativeModel;
      expect(init789).toBeDefined();
      expect(init789.title).toBe('New Title 789');
    });
  });

  describe('edge cases and validation', () => {
    it('should handle initiatives with no accepted suggestions', () => {
      const mockSuggestions: Record<string, UnifiedSuggestion> = {
        'initiative.INIT-123.title': {
          path: 'initiative.INIT-123.title',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Old Title',
          suggestedValue: 'New Title',
          entityIdentifier: 'INIT-123',
          fieldName: 'title'
        }
      };

      const { result } = renderHook(() => useResolutionOperations(mockSuggestions));

      // Don't accept anything
      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });

    it('should handle partial task resolution', () => {
      const mockSuggestions: Record<string, UnifiedSuggestion> = {
        'initiative.INIT-123.tasks.TASK-001.title': {
          path: 'initiative.INIT-123.tasks.TASK-001.title',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Old Task Title',
          suggestedValue: 'New Task Title',
          entityIdentifier: 'INIT-123',
          fieldName: 'title'
        },
        'initiative.INIT-123.tasks.TASK-001.description': {
          path: 'initiative.INIT-123.tasks.TASK-001.description',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Old Task Description',
          suggestedValue: 'New Task Description',
          entityIdentifier: 'INIT-123',
          fieldName: 'description'
        }
      };

      const { result } = renderHook(() => useResolutionOperations(mockSuggestions));

      act(() => {
        // Accept only title, reject description
        result.current.resolve('initiative.INIT-123.tasks.TASK-001.title', true);
        result.current.resolve('initiative.INIT-123.tasks.TASK-001.description', false);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      const change = acceptedChanges[0] as UpdateInitiativeModel;
      expect(change.tasks).toHaveLength(1);
      expect(change.tasks?.[0]).toEqual({
        action: 'UPDATE',
        identifier: 'TASK-001',
        title: 'New Task Title'
        // description should not be present
      });
    });

    it('should validate resulting models conform to basic ManagedInitiativeModel structure', () => {
      const mockSuggestions: Record<string, UnifiedSuggestion> = {
        'initiative.INIT-123.title': {
          path: 'initiative.INIT-123.title',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Old Title',
          suggestedValue: 'New Title',
          entityIdentifier: 'INIT-123',
          fieldName: 'title'
        }
      };

      const { result } = renderHook(() => useResolutionOperations(mockSuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123.title', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      const change = acceptedChanges[0] as UpdateInitiativeModel;
      // Basic validation that it has required fields for UpdateInitiativeModel
      expect(change.action).toBe('UPDATE');
      expect(change.identifier).toBe('INIT-123');
      expect(typeof change.title).toBe('string');
    });
  });
});