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
    deleteJob: vi.fn(),
  })
}));

import {
  setupDefaultMocks,
  setupMixedImprovements,
  setupTasksContextWith,
  renderSuggestionsHook,
  testContextData,
  expectEntitySuggestionStructure,
  expectResolutionState
} from './SuggestionsToBeResolvedContext.testUtils';

describe('SuggestionsToBeResolvedContext - Initiatives with Embedded Tasks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  describe('CREATE initiative with embedded tasks', () => {
    beforeEach(() => {
      setupMixedImprovements({
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
      }, {});
    });

    it('should generate individual task suggestions', () => {
      const { result } = renderSuggestionsHook();

      // Should create 7 suggestions: initiative entity + 2 task entities + 4 task fields
      expect(result.current.suggestions).toHaveLength(7);
      expect(result.current.entitySuggestions).toHaveLength(3); // initiative + 2 tasks
      expect(result.current.fieldSuggestions).toHaveLength(4); // 2 tasks × 2 fields each

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      // Verify initiative suggestion
      const initiativeEntity = result.current.suggestions.find(s => s.path === 'initiative.new-0');
      expect(initiativeEntity).toBeDefined();
      expect(initiativeEntity!.type).toBe('entity');

      // Verify individual task entity suggestions  
      const task1Entity = result.current.suggestions.find(s => s.path === 'initiative.new-0.tasks.new-task-0');
      expect(task1Entity).toBeDefined();
      expect(task1Entity!.type).toBe('entity');

      // Verify individual task field suggestions
      const task1Title = result.current.suggestions.find(s => s.path === 'initiative.new-0.tasks.new-task-0.title');
      expect(task1Title).toBeDefined();
      expect(task1Title!.type).toBe('field');
      expect(task1Title!.fieldName).toBe('title');
    });

    it('should accept initiative and some tasks, reject others', () => {
      const { result } = renderSuggestionsHook();

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      // Accept initiative and first task, reject second task
      act(() => {
        result.current.resolve('initiative.new-0', true);
        result.current.resolve('initiative.new-0.tasks.new-task-0', true);
        result.current.resolve('initiative.new-0.tasks.new-task-0.title', true);
        result.current.resolve('initiative.new-0.tasks.new-task-0.description', true);
        result.current.resolve('initiative.new-0.tasks.new-task-1', false);
        result.current.resolve('initiative.new-0.tasks.new-task-1.title', false);
        result.current.resolve('initiative.new-0.tasks.new-task-1.description', false);
      });

      expect(result.current.allResolved).toBe(true);

      // Verify resolutions contains all resolved paths
      expect(Object.keys(result.current.resolutions)).toHaveLength(7);

      // Check accepted resolutions
      expect(result.current.resolutions['initiative.new-0']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: expect.objectContaining({
          action: 'CREATE',
          title: 'New Initiative with Tasks'
        })
      });

      expect(result.current.resolutions['initiative.new-0.tasks.new-task-0']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: expect.objectContaining({
          action: 'CREATE',
          title: 'Embedded Task 1'
        })
      });

      expect(result.current.resolutions['initiative.new-0.tasks.new-task-0.title']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: 'Embedded Task 1'
      });

      // Check rejected resolutions
      expect(result.current.resolutions['initiative.new-0.tasks.new-task-1']).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined // Rejected entities have undefined originalValue
      });

      expect(result.current.resolutions['initiative.new-0.tasks.new-task-1.title']).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined // Rejected fields have undefined originalValue
      });

      // Check accepted changes - should include initiative + first task + task fields
      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges.length).toBeGreaterThan(0);

      // Should have initiative entity
      const initiativeChange = acceptedChanges.find(c => (c as any).title === 'New Initiative with Tasks');
      expect(initiativeChange).toBeDefined();
    });

    it('should support field-level task customization', () => {
      const { result } = renderSuggestionsHook();

      const customTitle = 'Custom Task Title';

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      // Accept with custom value for task title
      act(() => {
        result.current.resolve('initiative.new-0', true);
        result.current.resolve('initiative.new-0.tasks.new-task-0', true);
        result.current.resolve('initiative.new-0.tasks.new-task-0.title', true, customTitle);
        result.current.resolve('initiative.new-0.tasks.new-task-0.description', true);
        result.current.resolve('initiative.new-0.tasks.new-task-1', false);
        result.current.resolve('initiative.new-0.tasks.new-task-1.title', false);
        result.current.resolve('initiative.new-0.tasks.new-task-1.description', false);
      });

      // Verify resolutions contains custom value
      expect(result.current.resolutions['initiative.new-0.tasks.new-task-0.title']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: customTitle
      });

      // Verify non-custom field resolution
      expect(result.current.resolutions['initiative.new-0.tasks.new-task-0.description']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: 'First embedded task'
      });
    });

    it('should handle partial task field acceptance', () => {
      const { result } = renderSuggestionsHook();

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      // Accept task entity and title, but reject description
      act(() => {
        result.current.resolve('initiative.new-0', true);
        result.current.resolve('initiative.new-0.tasks.new-task-0', true);
        result.current.resolve('initiative.new-0.tasks.new-task-0.title', true);
        result.current.resolve('initiative.new-0.tasks.new-task-0.description', false);
        result.current.resolve('initiative.new-0.tasks.new-task-1', false);
        result.current.resolve('initiative.new-0.tasks.new-task-1.title', false);
        result.current.resolve('initiative.new-0.tasks.new-task-1.description', false);
      });

      expect(result.current.allResolved).toBe(true);

      // Verify resolutions contains partial acceptance
      expect(Object.keys(result.current.resolutions)).toHaveLength(7);

      // Check accepted task field
      expect(result.current.resolutions['initiative.new-0.tasks.new-task-0.title']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: 'Embedded Task 1'
      });

      // Check rejected task field
      expect(result.current.resolutions['initiative.new-0.tasks.new-task-0.description']).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);
    });
  });

  describe('UPDATE initiative with embedded tasks', () => {
    beforeEach(() => {
      setupMixedImprovements({
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
            }
          ]
        }
      }, {});
    });

    it('should handle mixed initiative and task acceptance', () => {
      const { result } = renderSuggestionsHook();

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      // Accept initiative fields but reject one task
      act(() => {
        result.current.resolve('initiative.INIT-123', true);
        result.current.resolve('initiative.INIT-123.title', true);
        result.current.resolve('initiative.INIT-123.description', true);
        result.current.resolve('initiative.INIT-123.tasks.new-task-0', true); // Accept CREATE task
        result.current.resolve('initiative.INIT-123.tasks.new-task-0.title', true);
        result.current.resolve('initiative.INIT-123.tasks.new-task-0.description', true);
        result.current.resolve('initiative.INIT-123.tasks.TASK-456', false); // Reject UPDATE task
        result.current.resolve('initiative.INIT-123.tasks.TASK-456.title', false);
      });

      expect(result.current.allResolved).toBe(true);

      // Verify resolutions contains all resolved paths (8 total)
      expect(Object.keys(result.current.resolutions)).toHaveLength(8);

      // Check accepted initiative resolutions
      expect(result.current.resolutions['initiative.INIT-123']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: expect.objectContaining({
          action: 'UPDATE',
          identifier: 'INIT-123',
          title: 'Updated Initiative Title'
        })
      });

      expect(result.current.resolutions['initiative.INIT-123.title']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: 'Updated Initiative Title'
      });

      // Check accepted CREATE task resolutions
      expect(result.current.resolutions['initiative.INIT-123.tasks.new-task-0']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: expect.objectContaining({
          action: 'CREATE',
          title: 'New Task in Update'
        })
      });

      // Check rejected UPDATE task resolutions
      expect(result.current.resolutions['initiative.INIT-123.tasks.TASK-456']).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined // Rejected entities have undefined originalValue
      });

      expect(result.current.resolutions['initiative.INIT-123.tasks.TASK-456.title']).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined // Rejected fields have undefined originalValue
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges.length).toBeGreaterThan(0);

      // Should include initiative and accepted task changes
      const initiativeChange = acceptedChanges.find(c => (c as any).identifier === 'INIT-123' || (c as any).title === 'Updated Initiative Title');
      expect(initiativeChange).toBeDefined();
    });
  });

  describe('task originalValue population for embedded tasks', () => {
    it('should populate originalValue for UPDATE initiative with embedded task field suggestions', () => {
      // Mock TasksContext with existing tasks that have original values
      setupTasksContextWith([testContextData.existingTask]);

      setupMixedImprovements({
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
            }
          ]
        }
      }, {});

      const { result } = renderSuggestionsHook();

      // Find the task field suggestions
      const taskTitleField = result.current.fieldSuggestions.find(s =>
        s.path === 'initiative.INIT-123.tasks.TASK-456.title'
      );
      const taskDescField = result.current.fieldSuggestions.find(s =>
        s.path === 'initiative.INIT-123.tasks.TASK-456.description'
      );

      // Verify task title field suggestion has originalValue from TasksContext
      expect(taskTitleField).toBeDefined();
      expect(taskTitleField!.originalValue).toBe('Current Task Title in Context');
      expect(taskTitleField!.suggestedValue).toBe('Updated Task Title');
      expect(taskTitleField!.fieldName).toBe('title');

      // Verify task description field suggestion has originalValue from TasksContext
      expect(taskDescField).toBeDefined();
      expect(taskDescField!.originalValue).toBe('Current task description in context');
      expect(taskDescField!.suggestedValue).toBe('Updated task description');
      expect(taskDescField!.fieldName).toBe('description');
    });

    it('should have undefined originalValue for UPDATE task fields when task not found in TasksContext', () => {
      // Mock TasksContext without the task we're looking for
      setupTasksContextWith([]);

      setupMixedImprovements({
        'INIT-123': {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          tasks: [
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-999', // This task doesn't exist in TasksContext
              title: 'Updated Task Title'
            }
          ]
        }
      }, {});

      const { result } = renderSuggestionsHook();

      // Find the task field suggestion
      const taskTitleField = result.current.fieldSuggestions.find(s =>
        s.path === 'initiative.INIT-123.tasks.TASK-999.title'
      );

      // Verify originalValue is undefined when task not found
      expect(taskTitleField).toBeDefined();
      expect(taskTitleField!.originalValue).toBeUndefined();
      expect(taskTitleField!.suggestedValue).toBe('Updated Task Title');
    });

    it('should have undefined originalValue for CREATE task fields (no original data exists)', () => {
      setupMixedImprovements({
        'INIT-123': {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'New Task Title',
              description: 'New task description'
            }
          ]
        }
      }, {});

      const { result } = renderSuggestionsHook();

      // Find the task field suggestions for CREATE task
      const taskTitleField = result.current.fieldSuggestions.find(s =>
        s.path === 'initiative.INIT-123.tasks.new-task-0.title'
      );
      const taskDescField = result.current.fieldSuggestions.find(s =>
        s.path === 'initiative.INIT-123.tasks.new-task-0.description'
      );

      // Verify originalValue is undefined for CREATE tasks (they have no original data)
      expect(taskTitleField).toBeDefined();
      expect(taskTitleField!.originalValue).toBeUndefined();
      expect(taskTitleField!.suggestedValue).toBe('New Task Title');

      expect(taskDescField).toBeDefined();
      expect(taskDescField!.originalValue).toBeUndefined();
      expect(taskDescField!.suggestedValue).toBe('New task description');
    });
  });

  describe('embedded task entity-level rejection', () => {
    it('should set resolvedValue to empty when rejecting embedded task entity suggestion (UPDATE)', () => {
      setupMixedImprovements({
        'INIT-123': {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          tasks: [
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456'
            }
          ]
        }
      }, {});

      const { result } = renderSuggestionsHook();

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      const path = 'initiative.INIT-123.tasks.TASK-456';
      const suggestedValue = result.current.suggestions.find(s => s.path === path)?.suggestedValue;

      act(() => {
        result.current.resolve(path, false);
      });

      // Verify resolution was added to resolutions map
      expect(result.current.resolutions[path]).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined // Rejected entity has undefined originalValue
      });

      const res = result.current.getResolutionState(path);
      expectResolutionState(res, true, false);
      expect(res?.resolvedValue == null).toBe(true);
      expect(res?.resolvedValue).not.toEqual(suggestedValue);

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });
  });

  describe('complex mixed resolution scenarios', () => {
    beforeEach(() => {
      setupMixedImprovements({
        'INIT-123': {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          description: 'Updated Initiative Description',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'New Embedded Task',
              description: 'New task description'
            },
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Updated Embedded Task'
            }
          ]
        }
      }, {});
    });

    it('should handle partial acceptance across multiple entity levels', () => {
      const { result } = renderSuggestionsHook();

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      // Accept initiative entity and title field
      // Accept CREATE task entity and fields
      // Reject UPDATE task entity and fields
      // Reject initiative description field
      act(() => {
        result.current.resolve('initiative.INIT-123', true);
        result.current.resolve('initiative.INIT-123.title', true);
        result.current.resolve('initiative.INIT-123.description', false);

        result.current.resolve('initiative.INIT-123.tasks.new-task-0', true);
        result.current.resolve('initiative.INIT-123.tasks.new-task-0.title', true);
        result.current.resolve('initiative.INIT-123.tasks.new-task-0.description', true);

        result.current.resolve('initiative.INIT-123.tasks.TASK-456', false);
        result.current.resolve('initiative.INIT-123.tasks.TASK-456.title', false);
      });

      expect(result.current.allResolved).toBe(true);

      // Verify resolutions contains all resolved paths (8 total)
      expect(Object.keys(result.current.resolutions)).toHaveLength(8);

      // Check accepted initiative resolutions
      expect(result.current.resolutions['initiative.INIT-123']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: expect.objectContaining({
          action: 'UPDATE',
          title: 'Updated Initiative Title'
        })
      });

      expect(result.current.resolutions['initiative.INIT-123.title']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: 'Updated Initiative Title'
      });

      // Check rejected initiative description
      expect(result.current.resolutions['initiative.INIT-123.description']).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined
      });

      // Check accepted CREATE task resolutions
      expect(result.current.resolutions['initiative.INIT-123.tasks.new-task-0']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: expect.objectContaining({
          action: 'CREATE',
          title: 'New Embedded Task'
        })
      });

      expect(result.current.resolutions['initiative.INIT-123.tasks.new-task-0.title']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: 'New Embedded Task'
      });

      // Check rejected UPDATE task resolutions
      expect(result.current.resolutions['initiative.INIT-123.tasks.TASK-456']).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined // Rejected entity has undefined originalValue
      });

      expect(result.current.resolutions['initiative.INIT-123.tasks.TASK-456.title']).toEqual({
        isResolved: true,
        isAccepted: false,
        resolvedValue: undefined
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges.length).toBeGreaterThan(0);

      // Verify expected changes are included
      const hasInitiativeUpdate = acceptedChanges.some(c =>
        (c as any).title === 'Updated Initiative Title'
      );
      expect(hasInitiativeUpdate).toBe(true);
    });

    it('should support bulk operations on mixed suggestion types', () => {
      const { result } = renderSuggestionsHook();

      const initialSuggestionCount = result.current.suggestions.length;
      expect(initialSuggestionCount).toBeGreaterThan(5); // Should have multiple suggestions

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      // Accept all suggestions
      act(() => {
        result.current.acceptAll();
      });

      expect(result.current.allResolved).toBe(true);
      expect(result.current.getAcceptedChanges().length).toBeGreaterThan(0);

      // Verify resolutions contains all suggestions as accepted
      expect(Object.keys(result.current.resolutions)).toHaveLength(initialSuggestionCount);

      Object.values(result.current.resolutions).forEach(resolution => {
        expect(resolution.isResolved).toBe(true);
        expect(resolution.isAccepted).toBe(true);
        expect(resolution.resolvedValue).toBeDefined();
      });

      // Rollback all
      act(() => {
        result.current.rollbackAll();
      });

      expect(result.current.allResolved).toBe(false);
      expect(result.current.getAcceptedChanges()).toHaveLength(0);

      // Verify resolutions is empty again
      expect(result.current.resolutions).toEqual({});

      // All resolution states should be null
      result.current.suggestions.forEach(suggestion => {
        expect(result.current.getResolutionState(suggestion.path)).toEqual({
          isResolved: false,
          isAccepted: false,
          resolvedValue: null
        });
      });
    });

    it('should handle resolution state queries for nested paths', () => {
      const { result } = renderSuggestionsHook();

      // Verify resolutions is initially empty
      expect(result.current.resolutions).toEqual({});

      // Test partial resolution
      act(() => {
        result.current.resolve('initiative.INIT-123.title', true);
        result.current.resolve('initiative.INIT-123.tasks.new-task-0.title', true);
      });

      // Verify partial resolutions are in the map
      expect(Object.keys(result.current.resolutions)).toHaveLength(2);
      expect(result.current.resolutions['initiative.INIT-123.title']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: 'Updated Initiative Title'
      });
      expect(result.current.resolutions['initiative.INIT-123.tasks.new-task-0.title']).toEqual({
        isResolved: true,
        isAccepted: true,
        resolvedValue: 'New Embedded Task'
      });

      // Check specific path resolution states
      expect(result.current.isFullyResolved('initiative.INIT-123')).toBe(false); // Not all fields resolved
      expect(result.current.isFullyResolved('initiative.INIT-123.tasks')).toBe(false); // Not all tasks resolved
      expect(result.current.isFullyResolved()).toBe(false); // Not all suggestions resolved

      // Complete resolution of title-related suggestions
      act(() => {
        result.current.resolve('initiative.INIT-123', true);
        result.current.resolve('initiative.INIT-123.description', true);
        result.current.resolve('initiative.INIT-123.tasks.new-task-0', true);
        result.current.resolve('initiative.INIT-123.tasks.new-task-0.description', true);
        result.current.resolve('initiative.INIT-123.tasks.TASK-456', true);
        result.current.resolve('initiative.INIT-123.tasks.TASK-456.title', true);
      });

      // Verify all resolutions are now in the map (8 total)
      expect(Object.keys(result.current.resolutions)).toHaveLength(8);

      // All resolutions should be accepted
      Object.values(result.current.resolutions).forEach(resolution => {
        expect(resolution.isResolved).toBe(true);
        expect(resolution.isAccepted).toBe(true);
        expect(resolution.resolvedValue).toBeDefined();
      });

      expect(result.current.isFullyResolved()).toBe(true);
      expect(result.current.allResolved).toBe(true);
    });
  });
});