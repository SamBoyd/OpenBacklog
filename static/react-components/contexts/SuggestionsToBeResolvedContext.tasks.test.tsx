import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { CreateTaskModel, ManagedEntityAction, UpdateInitiativeModel } from '#types';

import { useTasksContext } from '#contexts/TasksContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';

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
  setupTaskImprovement,
  setupMixedImprovements,
  setupTasksContextWith,
  renderSuggestionsHook,
  testTaskData,
  testContextData,
  expectResolutionState,
  setupInitiativesContextWith
} from './SuggestionsToBeResolvedContext.testUtils';

describe('SuggestionsToBeResolvedContext - Task Operations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  describe('existing task improvements', () => {
    beforeEach(() => {
      // Mock TasksContext with existing tasks
      setupTasksContextWith([
        { id: '1', identifier: 'TASK-456', initiative_id: 'INIT-123', title: 'Existing Task' },
        { id: '2', identifier: 'TASK-789', initiative_id: 'INIT-456', title: 'Another Task' }
      ]);
    });

    it('should transform CREATE task with initiative_identifier into initiative UPDATE suggestion', () => {
      (useInitiativesContext as any).mockReturnValue({
        initiativesData: [
          { id: '1', identifier: 'INIT-123', title: 'Existing Initiative' }
        ]
      });
      (useTasksContext as any).mockReturnValue({
        tasks: [
          { id: '1', identifier: 'TASK-456', initiative_id: '1', title: 'Existing Task' }
        ]
      });

      setupTaskImprovement('task-new-0', testTaskData.createTask);

      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions.map(s => s.path)).toEqual([
        'initiative.INIT-123',
        'initiative.INIT-123.tasks.new-task-0',
        'initiative.INIT-123.tasks.new-task-0.title',
        'initiative.INIT-123.tasks.new-task-0.description',
      ])
      expect(result.current.entitySuggestions).toHaveLength(2);
      expect(result.current.fieldSuggestions).toHaveLength(2);

      const suggestion = result.current.suggestions.find(s => s.path === 'initiative.INIT-123.tasks.new-task-0');
      expect(suggestion).toEqual({
        path: 'initiative.INIT-123.tasks.new-task-0',
        type: 'entity',
        action: ManagedEntityAction.CREATE,
        entityIdentifier: 'INIT-123',
        suggestedValue: {
          action: 'CREATE',
          initiative_identifier: 'INIT-123',
          title: 'New Task for Initiative',
          description: 'Task description',
        },
        originalValue: undefined,
      })

      const initiativeSuggestion = result.current.suggestions.find(s => s.path === 'initiative.INIT-123');
      expect(initiativeSuggestion).toEqual({
        path: 'initiative.INIT-123',
        type: 'entity',
        action: ManagedEntityAction.UPDATE,
        entityIdentifier: 'INIT-123',
        suggestedValue: {
          action: 'UPDATE',
          identifier: 'INIT-123',
          tasks: [
            {
              action: 'CREATE',
              initiative_identifier: 'INIT-123',
              title: 'New Task for Initiative',
              description: 'Task description',
            }
          ]
        },
        originalValue: {
          id: '1',
          identifier: 'INIT-123',
          title: 'Existing Initiative',
        },
      })
    });

    it('should transform UPDATE task into initiative UPDATE suggestion', () => {
      (useInitiativesContext as any).mockReturnValue({
        initiativesData: [
          { id: '1', identifier: 'INIT-123', title: 'Existing Initiative' }
        ]
      });
      (useTasksContext as any).mockReturnValue({
        tasks: [
          { id: '1', identifier: 'TASK-456', initiative_id: '1', title: 'Existing Task', description: 'Existing task description' }
        ]
      });

      setupTaskImprovement('TASK-456', testTaskData.updateTask);

      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions.map(s => s.path)).toEqual([
        'initiative.INIT-123',
        'initiative.INIT-123.tasks.TASK-456',
        'initiative.INIT-123.tasks.TASK-456.title',
        'initiative.INIT-123.tasks.TASK-456.description',
      ])

      const suggestion = result.current.suggestions.find(s => s.path === 'initiative.INIT-123.tasks.TASK-456');
      expect(suggestion).toEqual({
        path: 'initiative.INIT-123.tasks.TASK-456',
        type: 'entity',
        action: ManagedEntityAction.UPDATE,
        entityIdentifier: 'INIT-123',
        suggestedValue: {
          action: 'UPDATE',
          identifier: 'TASK-456',
          title: 'Updated Task Title',
          description: 'Updated description',
        },
        originalValue: {
          id: '1',
          identifier: 'TASK-456',
          initiative_id: '1',
          title: 'Existing Task',
          description: 'Existing task description',
        },
      })
    });

    it('should transform DELETE task into initiative UPDATE suggestion', () => {
      (useInitiativesContext as any).mockReturnValue({
        initiativesData: [
          { id: '1', identifier: 'INIT-123', title: 'Existing Initiative' }
        ]
      });
      (useTasksContext as any).mockReturnValue({
        tasks: [
          { id: '1', identifier: 'TASK-456', initiative_id: '1', title: 'Existing Task', description: 'Existing task description' }
        ]
      });

      setupTaskImprovement('TASK-456', testTaskData.deleteTask);

      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions).toHaveLength(2);

      const suggestion = result.current.suggestions.find(s => s.path === 'initiative.INIT-123.tasks.TASK-456');
      expect(suggestion).toEqual({
        path: 'initiative.INIT-123.tasks.TASK-456',
        type: 'entity',
        action: ManagedEntityAction.DELETE,
        entityIdentifier: 'INIT-123',
        suggestedValue: {
          action: 'DELETE',
          identifier: 'TASK-456',
        },
        originalValue: {
          id: '1',
          identifier: 'TASK-456',
          initiative_id: '1',
          title: 'Existing Task',
          description: 'Existing task description',
        },
      })
    });

    it('should aggregate multiple task operations for same initiative', () => {
      (useInitiativesContext as any).mockReturnValue({
        initiativesData: [
          { id: '1', identifier: 'INIT-123', title: 'Existing Initiative' }
        ]
      });
      (useTasksContext as any).mockReturnValue({
        tasks: [
          { id: '1', identifier: 'TASK-456', initiative_id: '1', title: 'Existing Task', description: 'Existing task description' }
        ]
      });

      setupMixedImprovements({}, {
        'task-new-0': {
          action: ManagedEntityAction.CREATE,
          title: 'New Task',
          description: 'Task description',
          initiative_identifier: 'INIT-123'
        },
        'TASK-456': {
          action: ManagedEntityAction.UPDATE,
          identifier: 'TASK-456',
          title: 'Updated Task'
        }
      });

      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions.map(s => s.path)).toEqual([
        'initiative.INIT-123',
        'initiative.INIT-123.tasks.new-task-0',
        'initiative.INIT-123.tasks.new-task-0.title',
        'initiative.INIT-123.tasks.new-task-0.description',
        'initiative.INIT-123.tasks.TASK-456',
        'initiative.INIT-123.tasks.TASK-456.title',
      ])
    });

    it('should create separate suggestions for tasks across different initiatives', () => {
      (useInitiativesContext as any).mockReturnValue({
        initiativesData: [
          { id: '1', identifier: 'INIT-123', title: 'Existing Initiative' },
          { id: '2', identifier: 'INIT-456', title: 'Another Initiative' }
        ]
      });
      (useTasksContext as any).mockReturnValue({
        tasks: [
          { id: '1', identifier: 'TASK-456', initiative_id: '1', title: 'Existing Task', description: 'Existing task description' },
          { id: '2', identifier: 'TASK-789', initiative_id: '2', title: 'Another Task', description: 'Another task description' }
        ]
      });
      setupMixedImprovements({}, {
        'TASK-456': {
          action: ManagedEntityAction.UPDATE,
          identifier: 'TASK-456',
          title: 'Updated Task for INIT-123'
        },
        'TASK-789': {
          action: ManagedEntityAction.UPDATE,
          identifier: 'TASK-789',
          title: 'Updated Task for INIT-456'
        }
      });

      const { result } = renderSuggestionsHook();

      expect(result.current.suggestions.map(s => s.path)).toEqual([
        'initiative.INIT-123',
        'initiative.INIT-123.tasks.TASK-456',
        'initiative.INIT-123.tasks.TASK-456.title',
        'initiative.INIT-456',
        'initiative.INIT-456.tasks.TASK-789',
        'initiative.INIT-456.tasks.TASK-789.title',
      ])
    });

    it('should accept task-derived suggestion and include in accepted changes', () => {
      (useInitiativesContext as any).mockReturnValue({
        initiativesData: [
          { id: '1', identifier: 'INIT-123', title: 'Existing Initiative' }
        ]
      });
      (useTasksContext as any).mockReturnValue({
        tasks: [
          { id: '1', identifier: 'TASK-456', initiative_id: '1', title: 'Existing Task', description: 'Existing task description' }
        ]
      });

      setupTaskImprovement('task-new-0', testTaskData.createTask);

      const { result } = renderSuggestionsHook();

      const suggestionPath = 'initiative.INIT-123.tasks.new-task-0';

      // Accept the suggestion
      act(() => {
        result.current.resolve(suggestionPath, true);
      });

      // Check resolution state
      const resolutionState = result.current.getResolutionState(suggestionPath);
      expectResolutionState(resolutionState, true, true);
      expect(resolutionState?.resolvedValue.action).toBe('CREATE');

      // todo: this should be true
      expect(result.current.allResolved).toBe(true);

      // Check accepted changes
      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(1);

      expect(acceptedChanges[0].action).toBe('UPDATE');
      expect((acceptedChanges[0] as UpdateInitiativeModel).identifier).toBe('INIT-123');

      expect((acceptedChanges[0] as UpdateInitiativeModel).tasks).toHaveLength(1);
      expect((acceptedChanges[0] as UpdateInitiativeModel).tasks![0].action).toBe(ManagedEntityAction.CREATE);
      expect(((acceptedChanges[0] as UpdateInitiativeModel).tasks![0] as CreateTaskModel).title).toBe('New Task for Initiative');
      expect(((acceptedChanges[0] as UpdateInitiativeModel).tasks![0] as CreateTaskModel).description).toBe('Task description');
    });

    it('should throw an error when task not found in TasksContext', () => {
      setupTaskImprovement('TASK-999', {
        action: ManagedEntityAction.UPDATE,
        identifier: 'TASK-999',
        title: 'Non-existent Task'
      });

      expect(() => renderSuggestionsHook()).toThrowError('Task TASK-999 not found in TasksContext');
    });
  });

  describe('task originalValue population from TasksContext', () => {
    it('should populate originalValue for task field suggestions when task exists in TasksContext', () => {
      // Mock TasksContext with existing task that has original values
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

  describe('task field-level rejection uses original value', () => {
    it('should set resolvedValue to original when task field is rejected', () => {
      setupTasksContextWith([testContextData.existingTask]);

      setupMixedImprovements({
        'INIT-123': {
          action: 'UPDATE',
          identifier: 'INIT-123',
          tasks: [
            {
              action: 'UPDATE',
              identifier: 'TASK-456',
              title: 'Updated Task Title',
              description: 'Updated task description'
            }
          ]
        }
      }, {});

      const { result } = renderSuggestionsHook();

      act(() => {
        result.current.resolve('initiative.INIT-123.tasks.TASK-456.title', false);
        result.current.resolve('initiative.INIT-123.tasks.TASK-456.description', false);
      });

      const taskTitleRes = result.current.getResolutionState('initiative.INIT-123.tasks.TASK-456.title');
      const taskDescRes = result.current.getResolutionState('initiative.INIT-123.tasks.TASK-456.description');

      expectResolutionState(taskTitleRes, true, false, 'Current Task Title in Context');
      expect(taskTitleRes?.resolvedValue).not.toBe('Updated Task Title');

      expectResolutionState(taskDescRes, true, false, 'Current task description in context');
      expect(taskDescRes?.resolvedValue).not.toBe('Updated task description');

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });
  });

  describe('task entity-level rejection', () => {
    it('should set resolvedValue to empty when rejecting normalized task entity suggestion (UPDATE from taskImprovements)', () => {
      setupInitiativesContextWith([
        { id: '1', identifier: 'INIT-123', title: 'Existing Initiative' }
      ]);
      setupTasksContextWith([
        { id: '1', identifier: 'TASK-456', initiative_id: '1', title: 'Existing Task', description: 'Existing task description' }
      ]);

      setupTaskImprovement('TASK-456', {
        action: ManagedEntityAction.UPDATE,
        identifier: 'TASK-456',
        title: 'Updated Task Title',
        initiative_identifier: 'INIT-123'
      });

      const { result } = renderSuggestionsHook();

      const path = 'initiative.INIT-123.tasks.TASK-456';

      act(() => {
        result.current.resolve(path, false);
      });

      const res = result.current.getResolutionState(path);
      expect(res?.isResolved).toBe(true);
      expect(res?.isAccepted).toBe(false);
      expect(res?.resolvedValue).toEqual({
        identifier: 'TASK-456',
        id: '1',
        title: 'Existing Task',
        description: 'Existing task description',
        initiative_id: '1'
      });

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
      expect(result.current.allResolved).toBe(true);
    });
  });

  describe('task field-level rejection for CREATE tasks', () => {
    it('should set resolvedValue undefined when rejecting CREATE task field (no original exists)', () => {
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
            }
          ]
        }
      }, {});

      const { result } = renderSuggestionsHook();

      const titlePath = 'initiative.new-0.tasks.new-task-0.title';
      const titleSuggestion = result.current.suggestions.find(s => s.path === titlePath);
      expect(titleSuggestion).toBeDefined();

      act(() => {
        result.current.resolve(titlePath, false);
      });

      const titleRes = result.current.getResolutionState(titlePath);
      expectResolutionState(titleRes, true, false);
      expect(titleRes?.resolvedValue).toBeUndefined();
      expect(titleRes?.resolvedValue).not.toBe('Embedded Task 1');

      const acceptedChanges = result.current.getAcceptedChanges();
      expect(acceptedChanges).toHaveLength(0);
    });
  });
});