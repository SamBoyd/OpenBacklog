import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { renderHook } from '@testing-library/react';

import { useUnifiedSuggestions } from './useUnifiedSuggestions';
import { ManagedEntityAction } from '#types';

// Mock the useSuggestedImprovements hook
vi.mock('#hooks/diffs/useSuggestedImprovements', () => ({
  useSuggestedImprovements: vi.fn()
}));

// Mock the TasksContext hook
vi.mock('#contexts/TasksContext', () => ({
  useTasksContext: vi.fn()
}));

// Mock the InitiativesContext hook
vi.mock('#contexts/InitiativesContext', () => ({
  useInitiativesContext: vi.fn()
}));

import { useSuggestedImprovements } from '#hooks/diffs/useSuggestedImprovements';
import { useTasksContext } from '#contexts/TasksContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';

describe('useUnifiedSuggestions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock for TasksContext
    (useTasksContext as any).mockReturnValue({
      tasks: []
    });
    // Default mock for InitiativesContext
    (useInitiativesContext as any).mockReturnValue({
      initiativesData: []
    });
  });

  describe('when both improvements are empty', () => {
    beforeEach(() => {
      (useSuggestedImprovements as Mock).mockReturnValue({
        initiativeImprovements: {},
        taskImprovements: {}
      });
    });

    it('should return empty suggestions object', () => {
      const { result } = renderHook(() => useUnifiedSuggestions());

      expect(result.current).toEqual({});
      expect(Object.keys(result.current)).toHaveLength(0);
    });
  });

  describe('with CREATE initiative improvement', () => {
    beforeEach(() => {
      (useSuggestedImprovements as Mock).mockReturnValue({
        initiativeImprovements: {
          'new-0': {
            action: ManagedEntityAction.CREATE,
            title: 'New Initiative',
            description: 'A new initiative to create',
            workspace_identifier: 'workspace-1'
          }
        },
        taskImprovements: {}
      });
    });

    it('should transform CREATE into entity suggestion', () => {
      const { result } = renderHook(() => useUnifiedSuggestions());

      expect(Object.keys(result.current)).toHaveLength(1);
      expect(result.current['initiative.new-0']).toBeDefined();

      const suggestion = result.current['initiative.new-0'];
      expect(suggestion.path).toBe('initiative.new-0');
      expect(suggestion.type).toBe('entity');
      expect(suggestion.action).toBe(ManagedEntityAction.CREATE);
      expect(suggestion.entityIdentifier).toBe('new-0');
      expect(suggestion.suggestedValue.title).toBe('New Initiative');
      expect(suggestion.suggestedValue.description).toBe('A new initiative to create');
    });
  });

  describe('with UPDATE initiative improvement', () => {
    beforeEach(() => {
      (useSuggestedImprovements as Mock).mockReturnValue({
        initiativeImprovements: {
          'INIT-123': {
            action: ManagedEntityAction.UPDATE,
            identifier: 'INIT-123',
            title: 'Updated Initiative Title',
            description: 'Updated description'
          }
        },
        taskImprovements: {}
      });
    });

    it('should transform UPDATE into entity and field suggestions', () => {
      const { result } = renderHook(() => useUnifiedSuggestions());

      // Should create 3 suggestions: entity + title field + description field
      expect(Object.keys(result.current)).toHaveLength(3);

      // Check entity-level suggestion
      expect(result.current['initiative.INIT-123']).toBeDefined();
      const entitySuggestion = result.current['initiative.INIT-123'];
      expect(entitySuggestion.path).toBe('initiative.INIT-123');
      expect(entitySuggestion.type).toBe('entity');
      expect(entitySuggestion.action).toBe(ManagedEntityAction.UPDATE);
      expect(entitySuggestion.entityIdentifier).toBe('INIT-123');
      expect(entitySuggestion.suggestedValue.title).toBe('Updated Initiative Title');

      // Check title field suggestion
      expect(result.current['initiative.INIT-123.title']).toBeDefined();
      const titleSuggestion = result.current['initiative.INIT-123.title'];
      expect(titleSuggestion.path).toBe('initiative.INIT-123.title');
      expect(titleSuggestion.type).toBe('field');
      expect(titleSuggestion.action).toBe(ManagedEntityAction.UPDATE);
      expect(titleSuggestion.fieldName).toBe('title');
      expect(titleSuggestion.suggestedValue).toBe('Updated Initiative Title');
      expect(titleSuggestion.entityIdentifier).toBe('INIT-123');

      // Check description field suggestion
      expect(result.current['initiative.INIT-123.description']).toBeDefined();
      const descSuggestion = result.current['initiative.INIT-123.description'];
      expect(descSuggestion.path).toBe('initiative.INIT-123.description');
      expect(descSuggestion.type).toBe('field');
      expect(descSuggestion.action).toBe(ManagedEntityAction.UPDATE);
      expect(descSuggestion.fieldName).toBe('description');
      expect(descSuggestion.suggestedValue).toBe('Updated description');
      expect(descSuggestion.entityIdentifier).toBe('INIT-123');
    });

    it('should populate originalValue for field suggestions from InitiativesContext', () => {
      // Mock existing initiative data in InitiativesContext
      (useInitiativesContext as any).mockReturnValue({
        initiativesData: [
          {
            id: 'uuid-123',
            identifier: 'INIT-123',
            title: 'Current Title in Context',
            description: 'Current description in context'
          }
        ]
      });

      const { result } = renderHook(() => useUnifiedSuggestions());

      // Check title field suggestion has populated originalValue
      const titleSuggestion = result.current['initiative.INIT-123.title'];
      expect(titleSuggestion).toBeDefined();
      expect(titleSuggestion.originalValue).toBe('Current Title in Context');
      expect(titleSuggestion.suggestedValue).toBe('Updated Initiative Title');

      // Check description field suggestion has populated originalValue
      const descSuggestion = result.current['initiative.INIT-123.description'];
      expect(descSuggestion).toBeDefined();
      expect(descSuggestion.originalValue).toBe('Current description in context');
      expect(descSuggestion.suggestedValue).toBe('Updated description');
    });

    it('should have undefined originalValue when initiative not found in InitiativesContext', () => {
      // Mock empty initiatives (initiative not found)
      (useInitiativesContext as any).mockReturnValue({
        initiativesData: []
      });

      const { result } = renderHook(() => useUnifiedSuggestions());

      // Check that originalValue is undefined when initiative not found
      const titleSuggestion = result.current['initiative.INIT-123.title'];
      expect(titleSuggestion).toBeDefined();
      expect(titleSuggestion.originalValue).toBeUndefined();
      expect(titleSuggestion.suggestedValue).toBe('Updated Initiative Title');
    });
  });

  describe('with DELETE initiative improvement', () => {
    beforeEach(() => {
      (useSuggestedImprovements as Mock).mockReturnValue({
        initiativeImprovements: {
          'INIT-123': {
            action: ManagedEntityAction.DELETE,
            identifier: 'INIT-123'
          }
        },
        taskImprovements: {}
      });
    });

    it('should transform DELETE into entity suggestion', () => {
      const { result } = renderHook(() => useUnifiedSuggestions());

      expect(Object.keys(result.current)).toHaveLength(1);
      expect(result.current['initiative.INIT-123']).toBeDefined();

      const suggestion = result.current['initiative.INIT-123'];
      expect(suggestion.path).toBe('initiative.INIT-123');
      expect(suggestion.type).toBe('entity');
      expect(suggestion.action).toBe(ManagedEntityAction.DELETE);
      expect(suggestion.entityIdentifier).toBe('INIT-123');
    });
  });

  describe('with multiple initiative improvements', () => {
    beforeEach(() => {
      (useSuggestedImprovements as Mock).mockReturnValue({
        initiativeImprovements: {
          'new-0': {
            action: ManagedEntityAction.CREATE,
            title: 'New Initiative 1'
          },
          'new-1': {
            action: ManagedEntityAction.CREATE,
            title: 'New Initiative 2'
          },
          'INIT-123': {
            action: ManagedEntityAction.UPDATE,
            identifier: 'INIT-123',
            title: 'Updated Title'
          }
        },
        taskImprovements: {}
      });
    });

    it('should transform all improvements into separate suggestions', () => {
      const { result } = renderHook(() => useUnifiedSuggestions());

      // Should create 5 suggestions:
      // new-0: CREATE entity (1)
      // new-1: CREATE entity (1) 
      // INIT-123: UPDATE entity + title field (2, no description in this test data)
      expect(Object.keys(result.current)).toHaveLength(4);
      expect(result.current['initiative.new-0']).toBeDefined();
      expect(result.current['initiative.new-1']).toBeDefined();
      expect(result.current['initiative.INIT-123']).toBeDefined();
      expect(result.current['initiative.INIT-123.title']).toBeDefined();

      // Verify each suggestion has correct properties
      expect(result.current['initiative.new-0'].action).toBe(ManagedEntityAction.CREATE);
      expect(result.current['initiative.new-1'].action).toBe(ManagedEntityAction.CREATE);
      expect(result.current['initiative.INIT-123'].action).toBe(ManagedEntityAction.UPDATE);
      expect(result.current['initiative.INIT-123.title'].action).toBe(ManagedEntityAction.UPDATE);
    });
  });

  describe('with task improvements', () => {
    describe('CREATE task normalization', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {}
        });
        (useTasksContext as any).mockReturnValue({
          tasks: []
        });
      });

      it('should throw error when CREATE task has no initiative_identifier', () => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'new-task-0': {
              action: ManagedEntityAction.CREATE,
              title: 'Task without Initiative',
              description: 'Task description'
              // Missing initiative_identifier
            }
          }
        });

        expect(() => renderHook(() => useUnifiedSuggestions())).toThrow(
          'CREATE task without initiative_identifier'
        );
      });

      it('should throw error when CREATE task references non-existent initiative', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-456', title: 'Different Initiative' }
          ]
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'new-task-0': {
              action: ManagedEntityAction.CREATE,
              title: 'Task for Non-existent Initiative',
              description: 'Task description',
              initiative_identifier: 'INIT-999' // This initiative doesn't exist
            }
          }
        });

        expect(() => renderHook(() => useUnifiedSuggestions())).toThrow(
          'Initiative INIT-999 not found in InitiativesContext'
        );
      });

      it('should succeed when CREATE task references existing initiative', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-123', title: 'Existing Initiative' }
          ]
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'new-task-0': {
              action: ManagedEntityAction.CREATE,
              title: 'Task for Existing Initiative',
              description: 'Task description',
              initiative_identifier: 'INIT-123' // This initiative exists
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should successfully create suggestions
        expect(Object.keys(result.current)).toHaveLength(4);
        expect(result.current['initiative.INIT-123']).toBeDefined();
        expect(result.current['initiative.INIT-123.tasks.new-task-0']).toBeDefined();
        expect(result.current['initiative.INIT-123.tasks.new-task-0.title']).toBeDefined();
        expect(result.current['initiative.INIT-123.tasks.new-task-0.description']).toBeDefined();
      });

      it('should transform CREATE task with initiative_identifier into initiative UPDATE', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-123', title: 'Existing Initiative' }
          ]
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'new-task-0': {
              action: ManagedEntityAction.CREATE,
              title: 'New Task',
              description: 'Task description',
              initiative_identifier: 'INIT-123'
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        expect(Object.keys(result.current)).toEqual([
          'initiative.INIT-123',
          'initiative.INIT-123.tasks.new-task-0',
          'initiative.INIT-123.tasks.new-task-0.title',
          'initiative.INIT-123.tasks.new-task-0.description'
        ]);
        expect(result.current['initiative.INIT-123']).toBeDefined();
        expect(result.current['initiative.INIT-123.tasks.new-task-0']).toBeDefined();
        expect(result.current['initiative.INIT-123.tasks.new-task-0.title']).toBeDefined();
        expect(result.current['initiative.INIT-123.tasks.new-task-0.description']).toBeDefined();

        const suggestion = result.current['initiative.INIT-123.tasks.new-task-0'];
        expect(suggestion.path).toBe('initiative.INIT-123.tasks.new-task-0');
        expect(suggestion.type).toBe('entity');
        expect(suggestion.action).toBe(ManagedEntityAction.CREATE);
        expect(suggestion.entityIdentifier).toBe('INIT-123');
        expect(suggestion.suggestedValue.action).toBe('CREATE');
        expect(suggestion.suggestedValue.title).toBe('New Task');
        expect(suggestion.suggestedValue.description).toBe('Task description');
        expect(suggestion.suggestedValue.initiative_identifier).toBe('INIT-123');
      });

      it('should aggregate multiple CREATE tasks for same initiative', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-123', title: 'Existing Initiative' }
          ]
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'task-new-0': {
              action: ManagedEntityAction.CREATE,
              title: 'Task 1',
              initiative_identifier: 'INIT-123'
            },
            'task-new-1': {
              action: ManagedEntityAction.CREATE,
              title: 'Task 2',
              initiative_identifier: 'INIT-123'
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        expect(Object.keys(result.current)).toEqual([
          'initiative.INIT-123',
          'initiative.INIT-123.tasks.new-task-0',
          'initiative.INIT-123.tasks.new-task-0.title',
          'initiative.INIT-123.tasks.new-task-1',
          'initiative.INIT-123.tasks.new-task-1.title',
        ]);

        const suggestion = result.current['initiative.INIT-123.tasks.new-task-0'];
        expect(suggestion).toEqual({
          path: 'initiative.INIT-123.tasks.new-task-0',
          type: 'entity',
          action: ManagedEntityAction.CREATE,
          entityIdentifier: 'INIT-123',
          suggestedValue: {
            action: 'CREATE',
            title: 'Task 1',
            description: undefined,
            initiative_identifier: 'INIT-123'
          },
          originalValue: undefined,
          fieldName: undefined
        })
      });

      it('should create separate suggestions for CREATE tasks with different initiatives', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-123', title: 'First Initiative' },
            { id: 'initiative-2', identifier: 'INIT-456', title: 'Second Initiative' }
          ]
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'task-new-0': {
              action: ManagedEntityAction.CREATE,
              title: 'Task for INIT-123',
              initiative_identifier: 'INIT-123'
            },
            'task-new-1': {
              action: ManagedEntityAction.CREATE,
              title: 'Task for INIT-456',
              initiative_identifier: 'INIT-456'
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        expect(Object.keys(result.current)).toHaveLength(6);
        expect(result.current['initiative.INIT-123.tasks.new-task-0']).toBeDefined();
        expect(result.current['initiative.INIT-456.tasks.new-task-0']).toBeDefined();

      });
    });

    describe('UPDATE task normalization', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {}
        });
      });

      it('should transform UPDATE task into initiative UPDATE using TasksContext', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-789', title: 'Existing Initiative' }
          ]
        });
        (useTasksContext as any).mockReturnValue({
          tasks: [
            { id: '1', identifier: 'TASK-123', initiative_id: 'initiative-1', title: 'Existing Task' }
          ]
        });

        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'TASK-123': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-123',
              title: 'Updated Task Title'
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        expect(Object.keys(result.current)).toHaveLength(3);

        expect(result.current['initiative.INIT-789.tasks.TASK-123']).toEqual({
          path: 'initiative.INIT-789.tasks.TASK-123',
          type: 'entity',
          action: ManagedEntityAction.UPDATE,
          entityIdentifier: 'INIT-789',
          suggestedValue: {
            action: 'UPDATE',
            title: 'Updated Task Title',
            identifier: 'TASK-123',
          },
          originalValue: {
            id: '1',
            identifier: 'TASK-123',
            initiative_id: 'initiative-1',
            title: 'Existing Task'
          },
        })
      });

      it('should throw error when UPDATE task not found in TasksContext', () => {
        (useTasksContext as any).mockReturnValue({
          tasks: []
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'TASK-999': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-999',
              title: 'Updated Task Title'
            }
          }
        });

        expect(() => renderHook(() => useUnifiedSuggestions())).toThrow(
          'Task TASK-999 not found in TasksContext'
        );
      });

      it('should aggregate multiple UPDATE tasks for same initiative', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-789', title: 'Existing Initiative' }
          ]
        });
        (useTasksContext as any).mockReturnValue({
          tasks: [
            { id: '1', identifier: 'TASK-123', initiative_id: 'initiative-1', title: 'Existing Task 123' },
            { id: '2', identifier: 'TASK-124', initiative_id: 'initiative-1', title: 'Existing Task 124' }
          ]
        });

        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'TASK-123': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-123',
              title: 'Updated Task 1'
            },
            'TASK-124': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-124',
              title: 'Updated Task 2'
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        expect(Object.keys(result.current)).toHaveLength(5);

        const suggestion = result.current['initiative.INIT-789.tasks.TASK-123'];
        expect(suggestion).toEqual({
          path: 'initiative.INIT-789.tasks.TASK-123',
          type: 'entity',
          action: ManagedEntityAction.UPDATE,
          entityIdentifier: 'INIT-789',
          suggestedValue: {
            action: 'UPDATE',
            title: 'Updated Task 1',
            identifier: 'TASK-123',
          },
          originalValue: {
            id: '1',
            identifier: 'TASK-123',
            initiative_id: 'initiative-1',
            title: 'Existing Task 123'
          }
        })

        const suggestion2 = result.current['initiative.INIT-789.tasks.TASK-124'];
        expect(suggestion2).toEqual({
          path: 'initiative.INIT-789.tasks.TASK-124',
          type: 'entity',
          action: ManagedEntityAction.UPDATE,
          entityIdentifier: 'INIT-789',
          suggestedValue: {
            action: 'UPDATE',
            title: 'Updated Task 2',
            identifier: 'TASK-124',
          },
          originalValue: {
            id: '2',
            identifier: 'TASK-124',
            initiative_id: 'initiative-1',
            title: 'Existing Task 124'
          },
        })

        const suggestion3 = result.current['initiative.INIT-789.tasks.TASK-123.title'];
        expect(suggestion3).toEqual({
          path: 'initiative.INIT-789.tasks.TASK-123.title',
          type: 'field',
          action: ManagedEntityAction.UPDATE,
          entityIdentifier: 'INIT-789',
          suggestedValue: 'Updated Task 1',
          originalValue: 'Existing Task 123',
          fieldName: 'title'
        })
      });
    });

    describe('DELETE task normalization', () => {
      it('should transform DELETE task into initiative UPDATE using TasksContext', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-789', title: 'Existing Initiative' }
          ]
        });
        (useTasksContext as any).mockReturnValue({
          tasks: [
            { id: '1', identifier: 'TASK-123', initiative_id: 'initiative-1', title: 'Existing Task' }
          ]
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'TASK-123': {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-123'
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        expect(Object.keys(result.current)).toHaveLength(2);

        const suggestion = result.current['initiative.INIT-789.tasks.TASK-123'];
        expect(suggestion).toEqual({
          path: 'initiative.INIT-789.tasks.TASK-123',
          type: 'entity',
          action: ManagedEntityAction.DELETE,
          entityIdentifier: 'INIT-789',
          suggestedValue: {
            action: 'DELETE',
            identifier: 'TASK-123',
          },
          originalValue: {
            id: '1',
            identifier: 'TASK-123',
            initiative_id: 'initiative-1',
            title: 'Existing Task'
          }
        })

        const suggestion2 = result.current['initiative.INIT-789'];
        expect(suggestion2).toEqual({
          path: 'initiative.INIT-789',
          type: 'entity',
          action: ManagedEntityAction.UPDATE,
          entityIdentifier: 'INIT-789',
          suggestedValue: {
            action: 'UPDATE',
            identifier: 'INIT-789',
            tasks: [
              {
                action: 'DELETE',
                identifier: 'TASK-123',
              }
            ]
          },
          originalValue: {
            id: 'initiative-1',
            identifier: 'INIT-789',
            title: 'Existing Initiative'
          }
        })
      });

      it('should throw error when DELETE task not found in TasksContext', () => {
        (useTasksContext as any).mockReturnValue({
          tasks: []
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'TASK-999': {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-999'
            }
          }
        });

        expect(() => renderHook(() => useUnifiedSuggestions())).toThrow(
          'Task TASK-999 not found in TasksContext'
        );
      });
    });

    describe('mixed task operations', () => {
      it('should aggregate CREATE, UPDATE, DELETE tasks for same initiative', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-789', title: 'Existing Initiative' }
          ]
        });
        (useTasksContext as any).mockReturnValue({
          tasks: [
            { id: '1', identifier: 'TASK-123', initiative_id: 'initiative-1', title: 'Existing Task 123' },
            { id: '2', identifier: 'TASK-124', initiative_id: 'initiative-1', title: 'Existing Task 124' }
          ]
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'task-new-0': {
              action: ManagedEntityAction.CREATE,
              title: 'New Task',
              initiative_identifier: 'INIT-789'
            },
            'TASK-123': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-123',
              title: 'Updated Task'
            },
            'TASK-124': {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-124'
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        expect(Object.keys(result.current)).toHaveLength(6);
        for (const key of Object.keys(result.current)) {
          expect(key).toMatch(/^initiative\.INIT-789/);
        }
      });

      it('should create separate suggestions for task operations across different initiatives', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-789', title: 'Existing Initiative' },
            { id: 'initiative-2', identifier: 'INIT-999', title: 'Existing Initiative' }
          ]
        });
        (useTasksContext as any).mockReturnValue({
          tasks: [
            { id: '1', identifier: 'TASK-123', initiative_id: 'initiative-1', title: 'Existing Task 123' },
            { id: '2', identifier: 'TASK-456', initiative_id: 'initiative-2', title: 'Existing Task 456' }
          ]
        });
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'task-new-0': {
              action: ManagedEntityAction.CREATE,
              title: 'New Task',
              initiative_identifier: 'INIT-789'
            },
            'TASK-456': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Updated Task'
            }
          }
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        expect(Object.keys(result.current)).toHaveLength(6);

        const init789Key = Object.keys(result.current).find(k => k.includes('INIT-789'));
        const init999Key = Object.keys(result.current).find(k => k.includes('INIT-999'));

        expect(init789Key).toBeDefined();
        expect(init999Key).toBeDefined();
      });
    });
  });

  describe('field-level suggestions for UPDATE initiatives', () => {
    describe('with title-only UPDATE', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-456': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-456',
              title: 'Only Title Updated'
              // No description field
            }
          },
          taskImprovements: {}
        });
      });

      it('should create entity and title field suggestions only', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should create 2 suggestions: entity + title field (no description)
        expect(Object.keys(result.current)).toHaveLength(2);
        expect(result.current['initiative.INIT-456']).toBeDefined();
        expect(result.current['initiative.INIT-456.title']).toBeDefined();
        expect(result.current['initiative.INIT-456.description']).toBeUndefined();

        // Check title field suggestion structure
        const titleSuggestion = result.current['initiative.INIT-456.title'];
        expect(titleSuggestion.path).toBe('initiative.INIT-456.title');
        expect(titleSuggestion.type).toBe('field');
        expect(titleSuggestion.action).toBe(ManagedEntityAction.UPDATE);
        expect(titleSuggestion.fieldName).toBe('title');
        expect(titleSuggestion.suggestedValue).toBe('Only Title Updated');
        expect(titleSuggestion.entityIdentifier).toBe('INIT-456');
      });
    });

    describe('with description-only UPDATE', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-789': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-789',
              description: 'Only Description Updated'
              // No title field
            }
          },
          taskImprovements: {}
        });
      });

      it('should create entity and description field suggestions only', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should create 2 suggestions: entity + description field (no title)
        expect(Object.keys(result.current)).toHaveLength(2);
        expect(result.current['initiative.INIT-789']).toBeDefined();
        expect(result.current['initiative.INIT-789.description']).toBeDefined();
        expect(result.current['initiative.INIT-789.title']).toBeUndefined();

        // Check description field suggestion structure
        const descSuggestion = result.current['initiative.INIT-789.description'];
        expect(descSuggestion.path).toBe('initiative.INIT-789.description');
        expect(descSuggestion.type).toBe('field');
        expect(descSuggestion.action).toBe(ManagedEntityAction.UPDATE);
        expect(descSuggestion.fieldName).toBe('description');
        expect(descSuggestion.suggestedValue).toBe('Only Description Updated');
        expect(descSuggestion.entityIdentifier).toBe('INIT-789');
      });
    });

    describe('with multiple UPDATE initiatives with mixed fields', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-100': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-100',
              title: 'Full Update Title',
              description: 'Full Update Description'
            },
            'INIT-200': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-200',
              title: 'Title Only Update'
              // No description
            },
            'INIT-300': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-300',
              description: 'Description Only Update'
              // No title
            }
          },
          taskImprovements: {}
        });
      });

      it('should create correct field suggestions for each initiative', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should create 8 suggestions total:
        // INIT-100: entity + title + description (3)
        // INIT-200: entity + title (2)  
        // INIT-300: entity + description (2)
        // Total: 7 suggestions
        expect(Object.keys(result.current)).toHaveLength(7);

        // INIT-100 - should have both field suggestions
        expect(result.current['initiative.INIT-100']).toBeDefined();
        expect(result.current['initiative.INIT-100.title']).toBeDefined();
        expect(result.current['initiative.INIT-100.description']).toBeDefined();

        // INIT-200 - should have only title field
        expect(result.current['initiative.INIT-200']).toBeDefined();
        expect(result.current['initiative.INIT-200.title']).toBeDefined();
        expect(result.current['initiative.INIT-200.description']).toBeUndefined();

        // INIT-300 - should have only description field  
        expect(result.current['initiative.INIT-300']).toBeDefined();
        expect(result.current['initiative.INIT-300.description']).toBeDefined();
        expect(result.current['initiative.INIT-300.title']).toBeUndefined();

        // Verify field suggestion values
        expect(result.current['initiative.INIT-100.title'].suggestedValue).toBe('Full Update Title');
        expect(result.current['initiative.INIT-100.description'].suggestedValue).toBe('Full Update Description');
        expect(result.current['initiative.INIT-200.title'].suggestedValue).toBe('Title Only Update');
        expect(result.current['initiative.INIT-300.description'].suggestedValue).toBe('Description Only Update');
      });
    });

    describe('with UPDATE having null/undefined fields', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-NULL': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-NULL',
              title: 'Valid Title',
              description: null // Explicit null
            }
          },
          taskImprovements: {}
        });
      });

      it('should not create field suggestion for null/undefined fields', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should create 2 suggestions: entity + title field (description is null)
        expect(Object.keys(result.current)).toHaveLength(2);
        expect(result.current['initiative.INIT-NULL']).toBeDefined();
        expect(result.current['initiative.INIT-NULL.title']).toBeDefined();
        expect(result.current['initiative.INIT-NULL.description']).toBeUndefined();

        // Title field should be created correctly
        const titleSuggestion = result.current['initiative.INIT-NULL.title'];
        expect(titleSuggestion.suggestedValue).toBe('Valid Title');
        expect(titleSuggestion.fieldName).toBe('title');
      });
    });

    describe('with empty string fields', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-EMPTY': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-EMPTY',
              title: '',  // Empty string
              description: 'Valid Description'
            }
          },
          taskImprovements: {}
        });
      });

      it('should create field suggestion for empty string values', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should create 3 suggestions: entity + both fields (empty string is valid)
        expect(Object.keys(result.current)).toHaveLength(3);
        expect(result.current['initiative.INIT-EMPTY.title']).toBeDefined();
        expect(result.current['initiative.INIT-EMPTY.description']).toBeDefined();

        // Empty string should be preserved as suggested value
        expect(result.current['initiative.INIT-EMPTY.title'].suggestedValue).toBe('');
        expect(result.current['initiative.INIT-EMPTY.description'].suggestedValue).toBe('Valid Description');
      });
    });
  });

  describe('with initiative improvements containing embedded tasks as individual suggestions', () => {
    describe('CREATE initiative with embedded tasks', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'new-0': {
              action: ManagedEntityAction.CREATE,
              title: 'New Initiative with Tasks',
              description: 'Initiative with embedded tasks',
              workspace_identifier: 'workspace-1',
              tasks: [
                {
                  action: ManagedEntityAction.CREATE,
                  title: 'Embedded Task 1',
                  description: 'First embedded task'
                },
                {
                  action: ManagedEntityAction.CREATE,
                  title: 'Embedded Task 2',
                  description: 'Second embedded task'
                }
              ]
            }
          },
          taskImprovements: {}
        });
      });

      it('should create initiative entity + individual task entity and field suggestions', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should create 7 suggestions:
        // 1 initiative entity + 2 task entities + 4 task fields (title + description for each task)
        expect(Object.keys(result.current)).toHaveLength(7);

        // Verify initiative entity suggestion
        expect(result.current['initiative.new-0']).toBeDefined();
        expect(result.current['initiative.new-0'].type).toBe('entity');
        expect(result.current['initiative.new-0'].action).toBe(ManagedEntityAction.CREATE);

        // Verify individual task entity suggestions
        expect(result.current['initiative.new-0.tasks.new-task-0']).toBeDefined();
        expect(result.current['initiative.new-0.tasks.new-task-1']).toBeDefined();

        const task1Entity = result.current['initiative.new-0.tasks.new-task-0'];
        expect(task1Entity.type).toBe('entity');
        expect(task1Entity.action).toBe(ManagedEntityAction.CREATE);
        expect(task1Entity.entityIdentifier).toBe('new-0'); // Initiative remains the entity identifier
        expect(task1Entity.suggestedValue.title).toBe('Embedded Task 1');

        // Verify individual task field suggestions
        expect(result.current['initiative.new-0.tasks.new-task-0.title']).toBeDefined();
        expect(result.current['initiative.new-0.tasks.new-task-0.description']).toBeDefined();
        expect(result.current['initiative.new-0.tasks.new-task-1.title']).toBeDefined();
        expect(result.current['initiative.new-0.tasks.new-task-1.description']).toBeDefined();

        const task1TitleField = result.current['initiative.new-0.tasks.new-task-0.title'];
        expect(task1TitleField.type).toBe('field');
        expect(task1TitleField.fieldName).toBe('title');
        expect(task1TitleField.suggestedValue).toBe('Embedded Task 1');
        expect(task1TitleField.entityIdentifier).toBe('new-0');
      });
    });

    describe('UPDATE initiative with embedded tasks with existing identifiers', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-123': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-123',
              title: 'Updated Initiative Title',
              description: 'Updated description',
              tasks: [
                {
                  action: ManagedEntityAction.CREATE,
                  title: 'New Task in Update',
                  description: 'Task to be created'
                },
                {
                  action: ManagedEntityAction.UPDATE,
                  identifier: 'TASK-456',
                  title: 'Updated Task Title'
                },
                {
                  action: ManagedEntityAction.DELETE,
                  identifier: 'TASK-789'
                }
              ]
            }
          },
          taskImprovements: {}
        });
      });

      it('should create initiative + field suggestions + individual task suggestions', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should create 10 suggestions:
        // initiative entity (1) + initiative title field (1) + initiative description field (1)
        // + task entities (3) + task fields (3: new-task title+desc, update task title only)
        expect(Object.keys(result.current)).toHaveLength(9);

        // Verify initiative suggestions
        expect(result.current['initiative.INIT-123']).toBeDefined();
        expect(result.current['initiative.INIT-123.title']).toBeDefined();
        expect(result.current['initiative.INIT-123.description']).toBeDefined();

        // Verify task entity suggestions
        expect(result.current['initiative.INIT-123.tasks.new-task-0']).toBeDefined(); // CREATE task
        expect(result.current['initiative.INIT-123.tasks.TASK-456']).toBeDefined(); // UPDATE task
        expect(result.current['initiative.INIT-123.tasks.TASK-789']).toBeDefined(); // DELETE task

        // Verify CREATE task has field suggestions
        expect(result.current['initiative.INIT-123.tasks.new-task-0.title']).toBeDefined();
        expect(result.current['initiative.INIT-123.tasks.new-task-0.description']).toBeDefined();

        // Verify UPDATE task has field suggestion only for title
        expect(result.current['initiative.INIT-123.tasks.TASK-456.title']).toBeDefined();
        expect(result.current['initiative.INIT-123.tasks.TASK-456.description']).toBeUndefined();

        // Verify DELETE task has no field suggestions (only entity)
        expect(result.current['initiative.INIT-123.tasks.TASK-789.title']).toBeUndefined();
        expect(result.current['initiative.INIT-123.tasks.TASK-789.description']).toBeUndefined();

        // Verify task actions are preserved
        expect(result.current['initiative.INIT-123.tasks.new-task-0'].action).toBe(ManagedEntityAction.CREATE);
        expect(result.current['initiative.INIT-123.tasks.TASK-456'].action).toBe(ManagedEntityAction.UPDATE);
        expect(result.current['initiative.INIT-123.tasks.TASK-789'].action).toBe(ManagedEntityAction.DELETE);
      });
    });

    describe('with mixed task scenarios', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-MIXED': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-MIXED',
              tasks: [
                {
                  action: ManagedEntityAction.CREATE,
                  title: 'Task with title only'
                  // No description
                },
                {
                  action: ManagedEntityAction.UPDATE,
                  identifier: 'TASK-001',
                  description: 'Task with description only'
                  // No title
                }
              ]
            }
          },
          taskImprovements: {}
        });
      });

      it('should only create field suggestions for present fields', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Should create 5 suggestions:
        // initiative entity (1) + task entities (2) + task fields (2: task1 title, task2 description)
        expect(Object.keys(result.current)).toHaveLength(5);

        // First task: only title field
        expect(result.current['initiative.INIT-MIXED.tasks.new-task-0.title']).toBeDefined();
        expect(result.current['initiative.INIT-MIXED.tasks.new-task-0.description']).toBeUndefined();

        // Second task: only description field
        expect(result.current['initiative.INIT-MIXED.tasks.TASK-001.title']).toBeUndefined();
        expect(result.current['initiative.INIT-MIXED.tasks.TASK-001.description']).toBeDefined();
      });
    });

    describe('with null or empty embedded tasks', () => {
      beforeEach(() => {
        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-NULL': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-NULL',
              title: 'Valid Title',
              tasks: null // Explicit null
            },
            'INIT-EMPTY': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-EMPTY',
              description: 'Valid Description',
              tasks: [] // Empty array
            }
          },
          taskImprovements: {}
        });
      });

      it('should not create task suggestions for null tasks', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // INIT-NULL: entity + title field only (no task suggestions)
        expect(result.current['initiative.INIT-NULL']).toBeDefined();
        expect(result.current['initiative.INIT-NULL.title']).toBeDefined();

        // No task suggestions for INIT-NULL
        const nullTaskSuggestions = Object.keys(result.current).filter(key =>
          key.startsWith('initiative.INIT-NULL.tasks.')
        );
        expect(nullTaskSuggestions).toHaveLength(0);
      });

      it('should not create task suggestions for empty array', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // INIT-EMPTY: entity + description field only (no task suggestions)
        expect(result.current['initiative.INIT-EMPTY']).toBeDefined();
        expect(result.current['initiative.INIT-EMPTY.description']).toBeDefined();

        // No task suggestions for INIT-EMPTY
        const emptyTaskSuggestions = Object.keys(result.current).filter(key =>
          key.startsWith('initiative.INIT-EMPTY.tasks.')
        );
        expect(emptyTaskSuggestions).toHaveLength(0);
      });
    });
  });

  describe('task originalValue population from TasksContext', () => {
    describe('UPDATE initiative with embedded tasks', () => {
      beforeEach(() => {
        // Mock TasksContext with existing tasks that have original values
        (useTasksContext as any).mockReturnValue({
          tasks: [
            {
              id: 'uuid-task-456',
              identifier: 'TASK-456',
              initiative_id: 'INIT-123',
              title: 'Current Task Title in Context',
              description: 'Current task description in context'
            },
            {
              id: 'uuid-task-789',
              identifier: 'TASK-789',
              initiative_id: 'INIT-123',
              title: 'Another Task Title',
              description: 'Another task description'
            }
          ]
        });

        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {
            'INIT-123': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'INIT-123',
              title: 'Updated Initiative Title',
              tasks: [
                {
                  action: ManagedEntityAction.UPDATE,
                  identifier: 'TASK-456',
                  title: 'Updated Task Title',
                  description: 'Updated task description'
                },
                {
                  action: ManagedEntityAction.CREATE,
                  title: 'New Task Title',
                  description: 'New task description'
                }
              ]
            }
          },
          taskImprovements: {}
        });
      });

      it('should populate originalValue for UPDATE task field suggestions from TasksContext', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Find UPDATE task field suggestions
        const taskTitleField = result.current['initiative.INIT-123.tasks.TASK-456.title'];
        const taskDescField = result.current['initiative.INIT-123.tasks.TASK-456.description'];

        // Verify UPDATE task title field has originalValue from TasksContext
        expect(taskTitleField).toBeDefined();
        expect(taskTitleField.originalValue).toBe('Current Task Title in Context');
        expect(taskTitleField.suggestedValue).toBe('Updated Task Title');
        expect(taskTitleField.type).toBe('field');
        expect(taskTitleField.fieldName).toBe('title');
        expect(taskTitleField.action).toBe(ManagedEntityAction.UPDATE);

        // Verify UPDATE task description field has originalValue from TasksContext
        expect(taskDescField).toBeDefined();
        expect(taskDescField.originalValue).toBe('Current task description in context');
        expect(taskDescField.suggestedValue).toBe('Updated task description');
        expect(taskDescField.type).toBe('field');
        expect(taskDescField.fieldName).toBe('description');
        expect(taskDescField.action).toBe(ManagedEntityAction.UPDATE);
      });

      it('should have undefined originalValue for CREATE task field suggestions (no original data)', () => {
        const { result } = renderHook(() => useUnifiedSuggestions());

        // Find CREATE task field suggestions
        const createTaskTitleField = result.current['initiative.INIT-123.tasks.new-task-1.title'];
        const createTaskDescField = result.current['initiative.INIT-123.tasks.new-task-1.description'];

        // Verify CREATE task fields have undefined originalValue (they're new)
        expect(createTaskTitleField).toBeDefined();
        expect(createTaskTitleField.originalValue).toBeUndefined();
        expect(createTaskTitleField.suggestedValue).toBe('New Task Title');
        expect(createTaskTitleField.type).toBe('field');
        expect(createTaskTitleField.action).toBe(ManagedEntityAction.CREATE);

        expect(createTaskDescField).toBeDefined();
        expect(createTaskDescField.originalValue).toBeUndefined();
        expect(createTaskDescField.suggestedValue).toBe('New task description');
        expect(createTaskDescField.type).toBe('field');
        expect(createTaskDescField.action).toBe(ManagedEntityAction.CREATE);
      });

      it('should have undefined originalValue when UPDATE task not found in TasksContext', () => {
        // Mock a different set of tasks that doesn't include the task we're updating
        (useTasksContext as any).mockReturnValue({
          tasks: [
            {
              id: 'uuid-different',
              identifier: 'TASK-DIFFERENT',
              initiative_id: 'INIT-123',
              title: 'Some Other Task Title'
            }
          ]
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        // Find UPDATE task field suggestions
        const taskTitleField = result.current['initiative.INIT-123.tasks.TASK-456.title'];

        // Verify originalValue is undefined when task not found in TasksContext
        expect(taskTitleField).toBeDefined();
        expect(taskTitleField.originalValue).toBeUndefined();
        expect(taskTitleField.suggestedValue).toBe('Updated Task Title');
        expect(taskTitleField.type).toBe('field');
        expect(taskTitleField.action).toBe(ManagedEntityAction.UPDATE);
      });
    });

    describe('standalone task improvements', () => {
      beforeEach(() => {
        // Mock TasksContext with existing tasks for standalone task improvements
        (useTasksContext as any).mockReturnValue({
          tasks: [
            {
              id: 'uuid-task-456',
              identifier: 'TASK-456',
              initiative_id: 'INIT-789',
              title: 'Existing Task Title',
              description: 'Existing task description'
            }
          ]
        });

        (useSuggestedImprovements as Mock).mockReturnValue({
          initiativeImprovements: {},
          taskImprovements: {
            'TASK-456': {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Updated Task Title',
              description: 'Updated task description'
            }
          }
        });
      });

      it('should populate originalValue for standalone UPDATE task improvements from TasksContext', () => {
        (useInitiativesContext as any).mockReturnValue({
          initiativesData: [
            { id: 'initiative-1', identifier: 'INIT-789', title: 'Existing Initiative' }
          ]
        });
        (useTasksContext as any).mockReturnValue({
          tasks: [
            { id: '1', identifier: 'TASK-456', initiative_id: 'initiative-1', title: 'Existing Task 456' }
          ]
        });

        const { result } = renderHook(() => useUnifiedSuggestions());

        // Note: Standalone task improvements get transformed into initiative UPDATE suggestions
        // The key format will be different: initiative.INIT-789.tasks.TASK-456 (entity level only)

        // Verify the entity-level suggestion exists
        const taskEntitySuggestion = result.current['initiative.INIT-789.tasks.TASK-456'];
        expect(taskEntitySuggestion).toEqual({
          path: 'initiative.INIT-789.tasks.TASK-456',
          type: 'entity',
          action: ManagedEntityAction.UPDATE,
          entityIdentifier: 'INIT-789',
          suggestedValue: {
            action: 'UPDATE',
            identifier: 'TASK-456',
            title: 'Updated Task Title',
            description: 'Updated task description'
          },
          originalValue: {
            id: '1',
            identifier: 'TASK-456',
            initiative_id: 'initiative-1',
            title: 'Existing Task 456'
          }
        })
      });
    });
  });
});