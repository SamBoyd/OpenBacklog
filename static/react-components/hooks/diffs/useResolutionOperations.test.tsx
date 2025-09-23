import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

import { useResolutionOperations } from './useResolutionOperations';
import { UnifiedSuggestion } from './useUnifiedSuggestions';
import { ManagedEntityAction, UpdateInitiativeModel, UpdateTaskModel } from '#types';

const DEFAULT_RESOLUTION_STATE = {
  isResolved: false,
  isAccepted: false,
  resolvedValue: null
};

describe('useResolutionOperations', () => {
  // Helper function to safely get identifier from a ManagedInitiativeModel
  const getIdentifier = (change: any): string | undefined => {
    if (change.action === 'CREATE') {
      return (change as any).identifier; // CREATE models may have identifier as extra property
    } else {
      return change.identifier; // UPDATE/DELETE models have identifier in type
    }
  };

  const mockEntitySuggestions: Record<string, UnifiedSuggestion> = {
    'initiative.new-0': {
      path: 'initiative.new-0',
      type: 'entity',
      action: ManagedEntityAction.CREATE,
      suggestedValue: {
        action: 'CREATE',
        title: 'New Initiative',
        description: 'Test description'
      },
      entityIdentifier: 'new-0'
    },
    'initiative.INIT-123': {
      path: 'initiative.INIT-123',
      type: 'entity',
      action: ManagedEntityAction.UPDATE,
      suggestedValue: {
        action: 'UPDATE',
        identifier: 'INIT-123',
        title: 'Updated Title'
      },
      entityIdentifier: 'INIT-123'
    },
    'initiative.INIT-456': {
      path: 'initiative.INIT-456',
      type: 'entity',
      action: ManagedEntityAction.DELETE,
      suggestedValue: {
        action: 'DELETE',
        identifier: 'INIT-456'
      },
      entityIdentifier: 'INIT-456'
    }
  };

  const mockFieldSuggestions: Record<string, UnifiedSuggestion> = {
    'initiative.INIT-789.title': {
      path: 'initiative.INIT-789.title',
      type: 'field',
      action: ManagedEntityAction.UPDATE,
      originalValue: 'Old Title',
      suggestedValue: 'New Title Value',
      entityIdentifier: 'INIT-789',
      fieldName: 'title'
    },
    'initiative.INIT-789.description': {
      path: 'initiative.INIT-789.description',
      type: 'field',
      action: ManagedEntityAction.UPDATE,
      originalValue: 'Old Description',
      suggestedValue: 'New Description Value',
      entityIdentifier: 'INIT-789',
      fieldName: 'description'
    },
    'initiative.INIT-999.title': {
      path: 'initiative.INIT-999.title',
      type: 'field',
      action: ManagedEntityAction.UPDATE,
      originalValue: 'Another Old Title',
      suggestedValue: 'Another New Title',
      entityIdentifier: 'INIT-999',
      fieldName: 'title'
    }
  };

  const mockTaskEntitySuggestions: Record<string, UnifiedSuggestion> = {
    'initiative.INIT-123.tasks.TASK-001': {
      path: 'initiative.INIT-123.tasks.TASK-001',
      type: 'entity',
      action: ManagedEntityAction.CREATE,
      suggestedValue: {
        action: 'CREATE',
        identifier: 'TASK-001',
        title: 'New Task Title',
        description: 'New task description'
      },
      entityIdentifier: 'INIT-123'
    },
    'initiative.INIT-456.tasks.TASK-002': {
      path: 'initiative.INIT-456.tasks.TASK-002',
      type: 'entity',
      action: ManagedEntityAction.UPDATE,
      suggestedValue: {
        action: 'UPDATE',
        identifier: 'TASK-002',
        title: 'Updated Task Title',
        description: 'Updated task description'
      },
      entityIdentifier: 'INIT-456'
    },
    'initiative.new-0.tasks.new-task-0': {
      path: 'initiative.new-0.tasks.new-task-0',
      type: 'entity',
      action: ManagedEntityAction.CREATE,
      suggestedValue: {
        action: 'CREATE',
        title: 'New Task for New Initiative',
        description: 'Task in new initiative'
      },
      entityIdentifier: 'new-0'
    }
  };

  const mockTaskFieldSuggestions: Record<string, UnifiedSuggestion> = {
    'initiative.INIT-123.tasks.TASK-001.title': {
      path: 'initiative.INIT-123.tasks.TASK-001.title',
      type: 'field',
      action: ManagedEntityAction.UPDATE,
      originalValue: 'Old Task Title',
      suggestedValue: 'New Task Title Field',
      entityIdentifier: 'INIT-123',
      fieldName: 'title'
    },
    'initiative.INIT-123.tasks.TASK-001.description': {
      path: 'initiative.INIT-123.tasks.TASK-001.description',
      type: 'field',
      action: ManagedEntityAction.UPDATE,
      originalValue: 'Old task description',
      suggestedValue: 'New task description field',
      entityIdentifier: 'INIT-123',
      fieldName: 'description'
    },
    'initiative.INIT-456.tasks.TASK-002.title': {
      path: 'initiative.INIT-456.tasks.TASK-002.title',
      type: 'field',
      action: ManagedEntityAction.UPDATE,
      originalValue: 'Another old title',
      suggestedValue: 'Another new task title',
      entityIdentifier: 'INIT-456',
      fieldName: 'title'
    }
  };

  const mockMixedSuggestions: Record<string, UnifiedSuggestion> = {
    ...mockEntitySuggestions,
    ...mockFieldSuggestions,
    // Entity with both entity-level and field-level suggestions (entity should win)
    'initiative.INIT-CONFLICT': {
      path: 'initiative.INIT-CONFLICT',
      type: 'entity',
      action: ManagedEntityAction.UPDATE,
      suggestedValue: {
        action: 'UPDATE',
        identifier: 'INIT-CONFLICT',
        title: 'Entity Level Title',
        description: 'Entity Level Description'
      },
      entityIdentifier: 'INIT-CONFLICT'
    },
    'initiative.INIT-CONFLICT.title': {
      path: 'initiative.INIT-CONFLICT.title',
      type: 'field',
      action: ManagedEntityAction.UPDATE,
      originalValue: 'Original Title',
      suggestedValue: 'Field Level Title',
      entityIdentifier: 'INIT-CONFLICT',
      fieldName: 'title'
    }
  };

  const mockMixedWithTasksSuggestions: Record<string, UnifiedSuggestion> = {
    ...mockEntitySuggestions,
    ...mockFieldSuggestions,
    ...mockTaskEntitySuggestions,
    ...mockTaskFieldSuggestions
  };

  describe('with empty suggestions', () => {
    it('should initialize with empty state', () => {
      const { result } = renderHook(() => useResolutionOperations({}));

      expect(result.current.resolutions).toEqual({});
      expect(result.current.isFullyResolved()).toBe(true);
      expect(result.current.getAcceptedChanges()).toEqual([]);
    });
  });

  describe('with entity suggestions available', () => {
    it('should initialize unresolved', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      expect(result.current.resolutions).toEqual({});
      expect(result.current.isFullyResolved()).toBe(false);
      expect(result.current.getResolutionState('initiative.new-0')).toEqual(DEFAULT_RESOLUTION_STATE);
    });

    it('should resolve suggestion as accepted', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      act(() => {
        result.current.resolve('initiative.new-0', true);
      });

      const resolutionState = result.current.getResolutionState('initiative.new-0');
      expect(resolutionState?.isResolved).toBe(true);
      expect(resolutionState?.isAccepted).toBe(true);
      expect(resolutionState?.resolvedValue.title).toBe('New Initiative');
    });

    it('should resolve suggestion as rejected', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      act(() => {
        result.current.resolve('initiative.new-0', false);
      });

      const resolutionState = result.current.getResolutionState('initiative.new-0');
      expect(resolutionState?.isResolved).toBe(true);
      expect(resolutionState?.isAccepted).toBe(false);
      expect(resolutionState?.resolvedValue).toBeUndefined(); // Entity suggestions don't have originalValue
    });

    it('should resolve field suggestion as rejected with originalValue', () => {
      const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-789.title', false);
        result.current.resolve('initiative.INIT-789.description', false);
      });

      const resolutionState = result.current.getResolutionState('initiative.INIT-789.title');
      expect(resolutionState?.isResolved).toBe(true);
      expect(resolutionState?.isAccepted).toBe(false);
      expect(resolutionState?.resolvedValue).toBe('Old Title'); // Should be the originalValue

      const resolutionStateDescription = result.current.getResolutionState('initiative.INIT-789.description');
      expect(resolutionStateDescription?.isResolved).toBe(true);
      expect(resolutionStateDescription?.isAccepted).toBe(false);
      expect(resolutionStateDescription?.resolvedValue).toBe('Old Description'); // Should be the originalValue
    });

    it('should resolve with custom value', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      const customValue = { action: 'CREATE', title: 'Custom Title' };

      act(() => {
        result.current.resolve('initiative.new-0', true, customValue);
      });

      const resolutionState = result.current.getResolutionState('initiative.new-0');
      expect(resolutionState?.resolvedValue.title).toBe('Custom Title');
    });

    it('should rollback resolution', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      // First resolve
      act(() => {
        result.current.resolve('initiative.new-0', true);
      });
      expect(result.current.getResolutionState('initiative.new-0')).toEqual(
        {
          isResolved: true,
          isAccepted: true,
          resolvedValue: {
            action: 'CREATE',
            title: 'New Initiative',
            description: 'Test description'
          }
        }
      );

      // Then rollback
      act(() => {
        result.current.rollback('initiative.new-0');
      });
      expect(result.current.getResolutionState('initiative.new-0')).toEqual(DEFAULT_RESOLUTION_STATE);
    });
  });

  describe('bulk operations with entity suggestions', () => {
    it('should accept all suggestions', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      act(() => {
        result.current.acceptAll();
      });

      // All suggestions should be accepted
      expect(result.current.isFullyResolved()).toBe(true);
      expect(result.current.getResolutionState('initiative.new-0')?.isAccepted).toBe(true);
      expect(result.current.getResolutionState('initiative.INIT-123')?.isAccepted).toBe(true);
      expect(result.current.getResolutionState('initiative.INIT-456')?.isAccepted).toBe(true);

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(3);
    });

    it('should reject all suggestions', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      act(() => {
        result.current.rejectAll();
      });

      // All suggestions should be rejected
      expect(result.current.isFullyResolved()).toBe(true);
      expect(result.current.getResolutionState('initiative.new-0')?.isAccepted).toBe(false);
      expect(result.current.getResolutionState('initiative.INIT-123')?.isAccepted).toBe(false);
      expect(result.current.getResolutionState('initiative.INIT-456')?.isAccepted).toBe(false);

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });

    it('should rollback all resolutions', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      // First accept all
      act(() => {
        result.current.acceptAll();
      });
      expect(result.current.isFullyResolved()).toBe(true);

      // Then rollback all
      act(() => {
        result.current.rollbackAll();
      });

      expect(result.current.isFullyResolved()).toBe(false);
      expect(result.current.resolutions).toEqual({});
      expect(result.current.getAcceptedChanges()).toHaveLength(0);
    });

    it('should support path prefix filtering', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      // Accept only suggestions with specific prefix
      act(() => {
        result.current.acceptAll('initiative.INIT');
      });

      // Only INIT suggestions should be accepted
      expect(result.current.getResolutionState('initiative.new-0')).toEqual(DEFAULT_RESOLUTION_STATE);
      expect(result.current.getResolutionState('initiative.INIT-123')).toEqual(
        {
          isResolved: true,
          isAccepted: true,
          resolvedValue: {
            action: 'UPDATE',
            identifier: 'INIT-123',
            title: 'Updated Title',
          }
        }
      );
      expect(result.current.getResolutionState('initiative.INIT-456')).toEqual(
        {
          isResolved: true,
          isAccepted: true,
          resolvedValue: {
            action: 'DELETE',
            identifier: 'INIT-456'
          }
        }
      );

      expect(result.current.isFullyResolved('initiative.INIT')).toBe(true);
      expect(result.current.isFullyResolved()).toBe(false);
    });
  });

  describe('isFullyResolved with entity suggestions', () => {
    it('should return false when suggestions are unresolved', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      expect(result.current.isFullyResolved()).toBe(false);
    });

    it('should return true when all suggestions are resolved', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      act(() => {
        result.current.resolve('initiative.new-0', true);
        result.current.resolve('initiative.INIT-123', false);
        result.current.resolve('initiative.INIT-456', true);
      });

      expect(result.current.isFullyResolved()).toBe(true);
    });

    it('should support path prefix filtering', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      act(() => {
        result.current.resolve('initiative.INIT-123', true);
        result.current.resolve('initiative.INIT-456', false);
      });

      expect(result.current.isFullyResolved('initiative.INIT')).toBe(true);
      expect(result.current.isFullyResolved()).toBe(false);
    });
  });

  describe('isFullyResolved with entity OR field logic', () => {
    describe('when entity has both entity-level and field-level suggestions', () => {
      const mockMixedEntityFieldSuggestions: Record<string, UnifiedSuggestion> = {
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
        },
        'initiative.INIT-123.description': {
          path: 'initiative.INIT-123.description',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Old Description',
          suggestedValue: 'Field Level Description',
          entityIdentifier: 'INIT-123',
          fieldName: 'description'
        }
      };

      it('should return true when entity-level suggestion is resolved (even if field-level unresolved)', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMixedEntityFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-123', true);
          // Leave field-level suggestions unresolved
        });

        expect(result.current.isFullyResolved('initiative.INIT-123')).toBe(true);
        expect(result.current.isFullyResolved()).toBe(true);
      });

      it('should return true when all field-level suggestions are resolved (even if entity-level unresolved)', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMixedEntityFieldSuggestions));

        act(() => {
          // Leave entity-level suggestion unresolved
          result.current.resolve('initiative.INIT-123.title', true);
          result.current.resolve('initiative.INIT-123.description', true);
        });

        expect(result.current.isFullyResolved('initiative.INIT-123')).toBe(true);
        expect(result.current.isFullyResolved()).toBe(true);
      });

      it('should return false when neither entity-level nor all field-level suggestions are resolved', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMixedEntityFieldSuggestions));

        act(() => {
          // Resolve only some field-level suggestions
          result.current.resolve('initiative.INIT-123.title', true);
          // Leave entity-level and description field unresolved
        });

        expect(result.current.isFullyResolved('initiative.INIT-123')).toBe(false);
        expect(result.current.isFullyResolved()).toBe(false);
      });

      it('should return false not all field-level are resolved', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMixedEntityFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-123.title', true);
          // Leave description field unresolved
        });

        expect(result.current.isFullyResolved('initiative.INIT-123')).toBe(false);
        expect(result.current.isFullyResolved()).toBe(false);
      });
    });


    describe('with multiple entities having mixed suggestion types', () => {
      const mockMultipleEntitiesSuggestions: Record<string, UnifiedSuggestion> = {
        // Entity with both entity-level and field-level
        'initiative.INIT-123': {
          path: 'initiative.INIT-123',
          type: 'entity',
          action: ManagedEntityAction.UPDATE,
          suggestedValue: { action: 'UPDATE', identifier: 'INIT-123', title: 'Entity Title' },
          entityIdentifier: 'INIT-123'
        },
        'initiative.INIT-123.description': {
          path: 'initiative.INIT-123.description',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Old Description',
          suggestedValue: 'New Description',
          entityIdentifier: 'INIT-123',
          fieldName: 'description'
        },
        // Entity with only field-level suggestions
        'initiative.INIT-456.title': {
          path: 'initiative.INIT-456.title',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          originalValue: 'Old Title',
          suggestedValue: 'New Title',
          entityIdentifier: 'INIT-456',
          fieldName: 'title'
        },
        // Entity with only entity-level suggestion
        'initiative.INIT-789': {
          path: 'initiative.INIT-789',
          type: 'entity',
          action: ManagedEntityAction.DELETE,
          suggestedValue: { action: 'DELETE', identifier: 'INIT-789' },
          entityIdentifier: 'INIT-789'
        }
      };

      it('should handle mixed entity resolution states correctly', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMultipleEntitiesSuggestions));

        act(() => {
          // Resolve INIT-123 via entity-level (field-level stays unresolved)
          result.current.resolve('initiative.INIT-123', true);
          
          // Resolve INIT-456 via field-level (only has field-level)
          result.current.resolve('initiative.INIT-456.title', true);
          
          // Leave INIT-789 unresolved
        });

        expect(result.current.isFullyResolved('initiative.INIT-123')).toBe(true);
        expect(result.current.isFullyResolved('initiative.INIT-456')).toBe(true);
        expect(result.current.isFullyResolved('initiative.INIT-789')).toBe(false);
        expect(result.current.isFullyResolved()).toBe(false); // Because INIT-789 is not resolved
      });

      it('should return true when all entities are resolved through different methods', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMultipleEntitiesSuggestions));

        act(() => {
          // Resolve INIT-123 via entity-level
          result.current.resolve('initiative.INIT-123', true);
          
          // Resolve INIT-456 via field-level
          result.current.resolve('initiative.INIT-456.title', true);
          
          // Resolve INIT-789 via entity-level
          result.current.resolve('initiative.INIT-789', true);
        });

        expect(result.current.isFullyResolved()).toBe(true);
      });
    });
  });

  describe('getAcceptedChanges with entity suggestions', () => {
    it('should return only accepted entity changes', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      act(() => {
        result.current.resolve('initiative.new-0', true);
        result.current.resolve('initiative.INIT-123', false);
        result.current.resolve('initiative.INIT-456', true);
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(2);

      // Should contain the accepted suggestions' values
      expect(acceptedChanges.some(change =>
        change.action === 'CREATE' && (change as any).title === 'New Initiative'
      )).toBe(true);
      expect(acceptedChanges.some(change =>
        change.action === 'DELETE' && change.identifier === 'INIT-456'
      )).toBe(true);
    });

    it('should return empty array when no suggestions accepted', () => {
      const { result } = renderHook(() => useResolutionOperations(mockEntitySuggestions));

      act(() => {
        result.current.rejectAll();
      });

      expect(result.current.getAcceptedChanges()).toEqual([]);
    });
  });

  describe('field-level suggestion aggregation', () => {
    describe('with single entity field suggestions', () => {
      it('should aggregate field-level suggestions into UpdateInitiativeModel', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-789.title', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Field-level suggestions are now aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.action).toBe('UPDATE');
        expect(change.identifier).toBe('INIT-789');
        expect(change.title).toBe('New Title Value');
        expect(change.description).toBeUndefined();
      });

      it('should aggregate field-level description suggestions into UpdateInitiativeModel', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-789.description', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Field-level suggestions are now aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.action).toBe('UPDATE');
        expect(change.identifier).toBe('INIT-789');
        expect(change.title).toBeUndefined();
        expect(change.description).toBe('New Description Value');
      });

      it('should aggregate multiple field-level suggestions into single UpdateInitiativeModel', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-789.title', true);
          result.current.resolve('initiative.INIT-789.description', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Field-level suggestions are aggregated into one model
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.action).toBe('UPDATE');
        expect(change.identifier).toBe('INIT-789');
        expect(change.title).toBe('New Title Value');
        expect(change.description).toBe('New Description Value');
      });

      it('should only include accepted fields in aggregated UpdateInitiativeModel', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-789.title', true);
          result.current.resolve('initiative.INIT-789.description', false);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Only accepted fields are included
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.action).toBe('UPDATE');
        expect(change.identifier).toBe('INIT-789');
        expect(change.title).toBe('New Title Value');
        expect(change.description).toBeUndefined(); // Rejected field not included
      });

      it('should handle custom field values in aggregated UpdateInitiativeModel', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-789.title', true, 'Custom Title Value');
          result.current.resolve('initiative.INIT-789.description', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Field-level suggestions are aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.action).toBe('UPDATE');
        expect(change.identifier).toBe('INIT-789');
        expect(change.title).toBe('Custom Title Value');
        expect(change.description).toBe('New Description Value');
      });
    });

    describe('with multiple entity field suggestions', () => {
      it('should create separate UpdateInitiativeModels for different entities', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-789.title', true);
          result.current.resolve('initiative.INIT-999.title', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(2); // Separate models for different entities
        
        const init789Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-789') as UpdateInitiativeModel;
        const init999Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-999') as UpdateInitiativeModel;
        
        expect(init789Change).toBeDefined();
        expect(init789Change.title).toBe('New Title Value');
        
        expect(init999Change).toBeDefined();
        expect(init999Change.title).toBe('Another New Title');
      });

      it('should aggregate all accepted field suggestions per entity', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          // Accept all field suggestions
          result.current.resolve('initiative.INIT-789.title', true);
          result.current.resolve('initiative.INIT-789.description', true);
          result.current.resolve('initiative.INIT-999.title', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(2); // Two initiatives with accepted fields
        
        const init789Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-789') as UpdateInitiativeModel;
        const init999Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-999') as UpdateInitiativeModel;
        
        expect(init789Change).toBeDefined();
        expect(init789Change.title).toBe('New Title Value');
        expect(init789Change.description).toBe('New Description Value');
        
        expect(init999Change).toBeDefined();
        expect(init999Change.title).toBe('Another New Title');
        expect(init999Change.description).toBeUndefined();
      });
    });

    describe('entity vs field precedence', () => {
      it('should prioritize entity-level changes over field-level changes', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMixedSuggestions));

        act(() => {
          // Accept both entity and field level suggestions for same entity
          result.current.resolve('initiative.INIT-CONFLICT', true);
          result.current.resolve('initiative.INIT-CONFLICT.title', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        // Should only have entity-level changes, field-level ignored due to conflict
        const conflictChanges = acceptedChanges.filter(c => c.action !== 'CREATE' && c.identifier === 'INIT-CONFLICT');
        expect(conflictChanges).toHaveLength(1);

        const entityChange = conflictChanges[0];
        expect(entityChange.action).toBe('UPDATE');
        if (entityChange.action === 'UPDATE') {
          expect(entityChange.title).toBe('Entity Level Title');
          expect(entityChange.description).toBe('Entity Level Description');
        }
      });

      it('should return field-level changes when entity-level is rejected but fields accepted', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMixedSuggestions));

        act(() => {
          // Reject entity-level but accept field-level
          result.current.resolve('initiative.INIT-CONFLICT', false);
          result.current.resolve('initiative.INIT-CONFLICT.title', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Field-level suggestions are now aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.action).toBe('UPDATE');
        expect(change.identifier).toBe('INIT-CONFLICT');
        expect(change.title).toBe('Field Level Title');
        expect(change.description).toBeUndefined(); // Only accepted fields
      });

      it('should handle mixed entity and field suggestions correctly (both entity and aggregated field)', () => {
        const { result } = renderHook(() => useResolutionOperations(mockMixedSuggestions));

        act(() => {
          // Accept entity suggestions
          result.current.resolve('initiative.new-0', true);
          result.current.resolve('initiative.INIT-123', true);

          // Accept field suggestions for different entities (should be aggregated)
          result.current.resolve('initiative.INIT-789.title', true);
          result.current.resolve('initiative.INIT-789.description', false);
          result.current.resolve('initiative.INIT-999.title', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(4); // 2 entity-level + 2 field-aggregated suggestions

        // Check entity-level changes are preserved
        expect(acceptedChanges.some(c => c.action === 'CREATE')).toBe(true);
        expect(acceptedChanges.some(c => c.action === 'UPDATE' && (c as UpdateInitiativeModel).identifier === 'INIT-123')).toBe(true);
        
        // Check field-level aggregated changes are included
        const init789Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-789') as UpdateInitiativeModel;
        const init999Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-999') as UpdateInitiativeModel;
        
        expect(init789Change).toBeDefined();
        expect(init789Change.title).toBe('New Title Value');
        expect(init789Change.description).toBeUndefined(); // Rejected field not included
        
        expect(init999Change).toBeDefined();
        expect(init999Change.title).toBe('Another New Title');
      });
    });

    describe('field-level bulk operations', () => {
      it('should support acceptAll with field suggestions and aggregate them', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          result.current.acceptAll();
        });

        expect(result.current.isFullyResolved()).toBe(true);

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(2); // Field-level suggestions are aggregated into two initiative models

        const init789Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-789') as UpdateInitiativeModel;
        const init999Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-999') as UpdateInitiativeModel;
        
        expect(init789Change).toBeDefined();
        expect(init789Change.title).toBe('New Title Value');
        expect(init789Change.description).toBe('New Description Value');
        
        expect(init999Change).toBeDefined();
        expect(init999Change.title).toBe('Another New Title');
      });

      it('should support path prefix filtering with field suggestions and aggregate them', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        act(() => {
          result.current.acceptAll('initiative.INIT-789');
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Only INIT-789 fields are aggregated

        const init789Change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(init789Change.identifier).toBe('INIT-789');
        expect(init789Change.title).toBe('New Title Value');
        expect(init789Change.description).toBe('New Description Value');

        // INIT-999 should not be affected
        expect(result.current.getResolutionState('initiative.INIT-999.title')).toEqual(DEFAULT_RESOLUTION_STATE);
      });

      it('should support rollback of field-level resolutions and update aggregation', () => {
        const { result } = renderHook(() => useResolutionOperations(mockFieldSuggestions));

        // First accept both fields
        act(() => {
          result.current.resolve('initiative.INIT-789.title', true);
          result.current.resolve('initiative.INIT-789.description', true);
        });

        expect(result.current.getAcceptedChanges()).toHaveLength(1); // Field-level suggestions are aggregated

        // Rollback just the title
        act(() => {
          result.current.rollback('initiative.INIT-789.title');
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Still one model, but only description field
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.identifier).toBe('INIT-789');
        expect(change.title).toBeUndefined(); // Title was rolled back
        expect(change.description).toBe('New Description Value');
      });
    });
  });

  describe('individual task entity suggestions', () => {
    describe('basic task entity operations', () => {
      it('should aggregate task entity suggestions into UpdateInitiativeModel.tasks', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskEntitySuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Task entity suggestions are aggregated into initiative model
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.action).toBe('UPDATE');
        expect(change.identifier).toBe('INIT-123');
        expect(change.tasks).toHaveLength(1);
        expect(change.tasks?.[0]).toEqual({
          action: 'CREATE',
          identifier: 'TASK-001',
          title: 'New Task Title',
          description: 'New task description'
        });
      });

      it('should aggregate UPDATE task entity suggestions into UpdateInitiativeModel.tasks', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskEntitySuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-456.tasks.TASK-002', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Task entity suggestions are aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.action).toBe('UPDATE');
        expect(change.identifier).toBe('INIT-456');
        expect(change.tasks).toHaveLength(1);
        expect(change.tasks?.[0]).toEqual({
          action: 'UPDATE',
          identifier: 'TASK-002',
          title: 'Updated Task Title',
          description: 'Updated task description'
        });
      });

      it('should aggregate multiple task entity suggestions into separate initiative models', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskEntitySuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001', true);
          result.current.resolve('initiative.INIT-456.tasks.TASK-002', true);
          result.current.resolve('initiative.new-0.tasks.new-task-0', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(3); // Task entity suggestions create separate initiative models
        
        const init123Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-123') as UpdateInitiativeModel;
        const init456Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-456') as UpdateInitiativeModel;
        const new0Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'new-0') as UpdateInitiativeModel;
        
        expect(init123Change?.tasks).toHaveLength(1);
        expect(init456Change?.tasks).toHaveLength(1);
        expect(new0Change?.tasks).toHaveLength(1);
      });

      it('should handle custom task entity values in aggregated UpdateInitiativeModel', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskEntitySuggestions));

        const customTaskValue = {
          action: 'CREATE',
          identifier: 'TASK-001',
          title: 'Custom Task Title',
          description: 'Custom task description'
        };

        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001', true, customTaskValue);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Task entity suggestions are aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.tasks).toHaveLength(1);
        expect(change.tasks?.[0]).toEqual(customTaskValue);
      });
    });

    describe('bulk operations with task entities', () => {
      it('should support acceptAll with task entity suggestions and aggregate them', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskEntitySuggestions));

        act(() => {
          result.current.acceptAll();
        });

        expect(result.current.isFullyResolved()).toBe(true);

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(3); // Task entity suggestions are aggregated into initiative models
        
        const init123Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-123') as UpdateInitiativeModel;
        const init456Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-456') as UpdateInitiativeModel;
        const new0Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'new-0') as UpdateInitiativeModel;
        
        expect(init123Change?.tasks).toHaveLength(1);
        expect(init456Change?.tasks).toHaveLength(1);
        expect(new0Change?.tasks).toHaveLength(1);
      });

      it('should support rejectAll with task entity suggestions', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskEntitySuggestions));

        act(() => {
          result.current.rejectAll();
        });

        expect(result.current.isFullyResolved()).toBe(true);
        expect(result.current.getAcceptedChanges()).toHaveLength(0);
      });

      it('should support path prefix filtering for task entities and aggregate them', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskEntitySuggestions));

        act(() => {
          result.current.acceptAll('initiative.INIT-123');
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Task entity suggestions are aggregated for INIT-123
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.identifier).toBe('INIT-123');
        expect(change.tasks).toHaveLength(1);

        // Other task entities should not be resolved
        expect(result.current.getResolutionState('initiative.INIT-456.tasks.TASK-002')).toEqual(DEFAULT_RESOLUTION_STATE);
        expect(result.current.getResolutionState('initiative.new-0.tasks.new-task-0')).toEqual(DEFAULT_RESOLUTION_STATE);
      });

      it('should support rollback for task entity suggestions and update aggregation', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskEntitySuggestions));

        // First accept a task entity
        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001', true);
        });
        expect(result.current.getAcceptedChanges()).toHaveLength(1); // Task entity suggestions are aggregated

        // Then rollback
        act(() => {
          result.current.rollback('initiative.INIT-123.tasks.TASK-001');
        });
        expect(result.current.getAcceptedChanges()).toHaveLength(0); // No more accepted changes after rollback
        expect(result.current.getResolutionState('initiative.INIT-123.tasks.TASK-001')).toEqual(DEFAULT_RESOLUTION_STATE);
      });
    });

    describe('mixed task entity and regular entity suggestions', () => {
      it('should handle both initiative and task entities correctly', () => {
        const mixedSuggestions = {
          ...mockEntitySuggestions,
          ...mockTaskEntitySuggestions
        };

        const { result } = renderHook(() => useResolutionOperations(mixedSuggestions));

        act(() => {
          // Accept one initiative entity and one task entity
          result.current.resolve('initiative.new-0', true);
          result.current.resolve('initiative.INIT-123.tasks.TASK-001', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(2); // Both initiative entity and aggregated task entity

        // Should have the initiative CREATE
        const initiativeChange = acceptedChanges.find(c => c.action === 'CREATE' && (c as any).title === 'New Initiative');
        expect(initiativeChange).toBeDefined();
        
        // Should have the aggregated task entity
        const taskChange = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-123') as UpdateInitiativeModel;
        expect(taskChange).toBeDefined();
        expect(taskChange.tasks).toHaveLength(1);
      });
    });
  });

  describe('individual task field suggestions', () => {
    describe('basic task field operations', () => {
      it('should aggregate task field suggestions into UpdateInitiativeModel.tasks', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001.title', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Task field suggestions are aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.identifier).toBe('INIT-123');
        expect(change.tasks).toHaveLength(1);
        expect(change.tasks?.[0]).toEqual({
          action: 'UPDATE',
          identifier: 'TASK-001',
          title: 'New Task Title Field'
        });
      });

      it('should aggregate multiple task field suggestions into single task update', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001.title', true);
          result.current.resolve('initiative.INIT-123.tasks.TASK-001.description', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Task field suggestions are aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.identifier).toBe('INIT-123');
        expect(change.tasks).toHaveLength(1);
        expect(change.tasks?.[0]).toEqual({
          action: 'UPDATE',
          identifier: 'TASK-001',
          title: 'New Task Title Field',
          description: 'New task description field'
        });
      });

      it('should create separate initiative models for task fields in different initiatives', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001.title', true);
          result.current.resolve('initiative.INIT-456.tasks.TASK-002.title', true);
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(2); // Separate initiative models for different initiatives
        
        const init123Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-123') as UpdateInitiativeModel;
        const init456Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-456') as UpdateInitiativeModel;
        
        expect(init123Change?.tasks).toHaveLength(1);
        expect((init123Change?.tasks?.[0] as UpdateTaskModel).identifier).toBe('TASK-001');
        
        expect(init456Change?.tasks).toHaveLength(1);
        expect((init456Change?.tasks?.[0] as UpdateTaskModel).identifier).toBe('TASK-002');
      });

      it('should handle custom task field values in aggregation', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskFieldSuggestions));

        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001.title', true, 'Custom Task Title Value');
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Task field suggestions are aggregated
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect((change.tasks?.[0] as UpdateTaskModel).title).toBe('Custom Task Title Value');
      });
    });

    describe('bulk operations with task fields', () => {
      it('should support acceptAll with task field suggestions and aggregate them', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskFieldSuggestions));

        act(() => {
          result.current.acceptAll();
        });

        expect(result.current.isFullyResolved()).toBe(true);

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(2); // Task field suggestions are aggregated into initiative models

        const init123Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-123') as UpdateInitiativeModel;
        const init456Change = acceptedChanges.find(c => (c as UpdateInitiativeModel).identifier === 'INIT-456') as UpdateInitiativeModel;
        
        expect(init123Change?.tasks).toHaveLength(1);
        expect((init123Change?.tasks?.[0] as UpdateTaskModel).identifier).toBe('TASK-001');
        expect((init123Change?.tasks?.[0] as UpdateTaskModel).title).toBeDefined();
        expect((init123Change?.tasks?.[0] as UpdateTaskModel).description).toBeDefined();
        
        expect(init456Change?.tasks).toHaveLength(1);
        expect((init456Change?.tasks?.[0] as UpdateTaskModel).identifier).toBe('TASK-002');
        expect((init456Change?.tasks?.[0] as UpdateTaskModel).title).toBeDefined();
      });

      it('should support path prefix filtering for task fields and aggregate them', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskFieldSuggestions));

        act(() => {
          result.current.acceptAll('initiative.INIT-123.tasks.TASK-001');
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Task field suggestions are aggregated for TASK-001 only
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect(change.identifier).toBe('INIT-123');
        expect(change.tasks).toHaveLength(1);
        expect((change.tasks?.[0] as UpdateTaskModel).identifier).toBe('TASK-001');

        // TASK-002 should not be affected
        expect(result.current.getResolutionState('initiative.INIT-456.tasks.TASK-002.title')).toEqual(DEFAULT_RESOLUTION_STATE);
      });

      it('should support rollback for task field suggestions and update aggregation', () => {
        const { result } = renderHook(() => useResolutionOperations(mockTaskFieldSuggestions));

        // First accept task fields
        act(() => {
          result.current.resolve('initiative.INIT-123.tasks.TASK-001.title', true);
          result.current.resolve('initiative.INIT-123.tasks.TASK-001.description', true);
        });
        expect(result.current.getAcceptedChanges()).toHaveLength(1); // Task field suggestions are aggregated

        // Rollback just the title
        act(() => {
          result.current.rollback('initiative.INIT-123.tasks.TASK-001.title');
        });

        const acceptedChanges = result.current.getAcceptedChanges();
        expect(acceptedChanges).toHaveLength(1); // Still aggregated, but only description field
        
        const change = acceptedChanges[0] as UpdateInitiativeModel;
        expect((change.tasks?.[0] as UpdateTaskModel).title).toBeUndefined(); // Title was rolled back
        expect((change.tasks?.[0] as UpdateTaskModel).description).toBeDefined(); // Description still there
      });
    });
  });
});