import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';

import { useSaveSuggestions } from './useSaveSuggestions';
import { useSuggestionsToBeResolvedContext } from '#contexts/SuggestionsToBeResolvedContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useTasksContext } from '#contexts/TasksContext';
import { AiImprovementJobResult, CreateInitiativeModel, ManagedEntityAction, ManagedInitiativeModel } from '#types';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';

// Mock the contexts
vi.mock('#contexts/SuggestionsToBeResolvedContext');
vi.mock('#contexts/InitiativesContext');
vi.mock('#contexts/TasksContext');
vi.mock('#contexts/AiImprovementsContext');

describe('useSaveSuggestions', () => {
  const mockUseSuggestionsToBeResolvedContext = vi.mocked(useSuggestionsToBeResolvedContext);
  const mockUseInitiativesContext = vi.mocked(useInitiativesContext);
  const mockUseTasksContext = vi.mocked(useTasksContext);
  const mockUseAiImprovementsContext = vi.mocked(useAiImprovementsContext);

  // Mock context function implementations
  const mockCreateInitiative = vi.fn();
  const mockUpdateInitiative = vi.fn();
  const mockDeleteInitiative = vi.fn();
  const mockCreateTask = vi.fn();
  const mockUpdateTask = vi.fn();
  const mockDeleteTask = vi.fn();
  const mockMarkJobAsResolved = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Setup initiative context mock
    mockUseInitiativesContext.mockReturnValue({
      createInitiative: mockCreateInitiative,
      updateInitiative: mockUpdateInitiative,
      deleteInitiative: mockDeleteInitiative,
      // Add mock initiatives data for ID resolution
      initiativesData: [
        { id: 'initiative-uuid-123', identifier: 'INIT-123', title: 'Test Initiative 1' },
        { id: 'initiative-uuid-456', identifier: 'INIT-456', title: 'Test Initiative 2' },
        { id: 'initiative-uuid-789', identifier: 'INIT-789', title: 'Test Initiative 3' },
        { id: 'initiative-uuid-999', identifier: 'INIT-999', title: 'Test Initiative 4' },
      ] as any[],
      error: null,
      shouldShowSkeleton: false,
      isQueryFetching: false,
      isCreatingInitiative: false,
      isUpdatingInitiative: false,
      isDeletingInitiative: false,
      isBatchUpdatingInitiatives: false,
      isDeletingTask: false,
      isDeletingChecklistItem: false,
      updateInitiatives: vi.fn(),
      reloadInitiatives: vi.fn(),
      deleteTask: vi.fn(),
      deleteChecklistItem: vi.fn(),
      invalidateInitiative: vi.fn(),
      invalidateAllInitiatives: vi.fn(),
      invalidateInitiativesByStatus: vi.fn(),
      reorderInitiative: vi.fn(),
      moveInitiativeToStatus: vi.fn(),
      moveInitiativeInGroup: vi.fn(),
      updateInitiativeInCache: vi.fn(),
    });

    // Setup ai improvements context mock
    mockUseAiImprovementsContext.mockReturnValue({
      markJobAsResolved: mockMarkJobAsResolved,
      setThreadId: vi.fn(),
      jobResult: null,
      initiativeImprovements: {},
      taskImprovements: {},
      loading: false,
      error: null,
      isEntityLocked: false,
      requestImprovement: vi.fn(),
      updateImprovement: vi.fn(),
      resetError: vi.fn(),
    });

    // Setup task context mock  
    mockUseTasksContext.mockReturnValue({
      createTask: mockCreateTask,
      updateTask: mockUpdateTask,
      deleteTask: mockDeleteTask,
      // Add mock tasks data for ID resolution
      tasks: [
        { id: 'task-uuid-456', identifier: 'TASK-456', title: 'Test Task 1' },
        { id: 'task-uuid-789', identifier: 'TASK-789', title: 'Test Task 2' },
      ] as any[],
      error: null,
      shouldShowSkeleton: false,
      isQueryFetching: false,
      isCreatingTask: false,
      isUpdatingTask: false,
      isDeletingTask: false,
      isPolling: false,
      reloadTasks: vi.fn(),
      invalidateTasks: vi.fn(),
      setInitiativeId: vi.fn(),
      setTaskId: vi.fn(),
      startPolling: vi.fn(),
      stopPolling: vi.fn(),
      reorderTask: vi.fn(),
      moveTaskToStatus: vi.fn(),
      updateChecklistItem: vi.fn(),
      updateChecklistItemDebounced: vi.fn(),
      addChecklistItem: vi.fn(),
      removeChecklistItem: vi.fn(),
      reorderChecklistItems: vi.fn(),
    });

    // Setup default resolved promises for context functions
    mockCreateInitiative.mockResolvedValue({ id: 'created-initiative' });
    mockUpdateInitiative.mockResolvedValue({ id: 'updated-initiative' });
    mockDeleteInitiative.mockResolvedValue(undefined);
    mockCreateTask.mockResolvedValue({ id: 'created-task' });
    mockUpdateTask.mockResolvedValue({ id: 'updated-task' });
    mockDeleteTask.mockResolvedValue(undefined);
  });

  describe('error cases', () => {
    it('should throw error when suggestions are not fully resolved', async () => {
      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(false),
        getAcceptedChanges: vi.fn(),
        suggestions: {},
        resolutions: {},
        allResolved: false,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await expect(result.current.saveSuggestions()).rejects.toThrow('Suggestions are not fully resolved');
    });

    it('should throw error when initiative identifier cannot be resolved for UPDATE', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'UNKNOWN-INIT',
          title: 'Updated Initiative Title'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await expect(result.current.saveSuggestions()).rejects.toThrow('Cannot find initiative with identifier "UNKNOWN-INIT". Entity may not exist or may not be loaded.');
    });

    it('should throw error when task identifier cannot be resolved for UPDATE', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          tasks: [
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'UNKNOWN-TASK',
              title: 'Updated Task Title',
              description: 'Updated task description',
              checklist: []
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await expect(result.current.saveSuggestions()).rejects.toThrow('Cannot find task with identifier "UNKNOWN-TASK". Entity may not exist or may not be loaded.');
    });
  });

  describe('single initiative operations - no tasks', () => {
    it('should handle single initiative update', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          description: 'Updated description content'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative update was called with correct data including resolved ID
      expect(mockUpdateInitiative).toHaveBeenCalledTimes(1);
      expect(mockUpdateInitiative).toHaveBeenCalledWith({
        id: 'initiative-uuid-123', // Resolved from identifier 'INIT-123'
        identifier: 'INIT-123',
        title: 'Updated Initiative Title',
        description: 'Updated description content'
      });
      
      // Verify no task operations were called
      expect(mockCreateTask).not.toHaveBeenCalled();
      expect(mockUpdateTask).not.toHaveBeenCalled();
      expect(mockDeleteTask).not.toHaveBeenCalled();
      
      // Verify no other initiative operations were called
      expect(mockCreateInitiative).not.toHaveBeenCalled();
      expect(mockDeleteInitiative).not.toHaveBeenCalled();
    });

    it('should handle single initiative create', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.CREATE,
          title: 'New Initiative',
          description: 'A new initiative to create',
          workspace_identifier: 'workspace-1'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative create was called with correct data
      expect(mockCreateInitiative).toHaveBeenCalledTimes(1);
      expect(mockCreateInitiative).toHaveBeenCalledWith({
        title: 'New Initiative',
        description: 'A new initiative to create',
        workspace_identifier: 'workspace-1'
      });
      
      // Verify no task operations were called
      expect(mockCreateTask).not.toHaveBeenCalled();
      expect(mockUpdateTask).not.toHaveBeenCalled();
      expect(mockDeleteTask).not.toHaveBeenCalled();
      
      // Verify no other initiative operations were called
      expect(mockUpdateInitiative).not.toHaveBeenCalled();
      expect(mockDeleteInitiative).not.toHaveBeenCalled();
    });

    it('should handle single initiative delete', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.DELETE,
          identifier: 'INIT-123'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative delete was called with correct ID (resolved from identifier)
      expect(mockDeleteInitiative).toHaveBeenCalledTimes(1);
      expect(mockDeleteInitiative).toHaveBeenCalledWith('initiative-uuid-123');
      
      // Verify no task operations were called
      expect(mockCreateTask).not.toHaveBeenCalled();
      expect(mockUpdateTask).not.toHaveBeenCalled();
      expect(mockDeleteTask).not.toHaveBeenCalled();
      
      // Verify no other initiative operations were called
      expect(mockCreateInitiative).not.toHaveBeenCalled();
      expect(mockUpdateInitiative).not.toHaveBeenCalled();
    });
  });

  describe('initiative operations with specific task operations', () => {
    it('should handle initiative update with create task', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'New Task for Initiative',
              description: 'Task description',
              checklist: [],
              initiative_identifier: 'INIT-123'
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative update was called with resolved ID
      expect(mockUpdateInitiative).toHaveBeenCalledTimes(1);
      expect(mockUpdateInitiative).toHaveBeenCalledWith({
        id: 'initiative-uuid-123', // Resolved from identifier 'INIT-123'
        identifier: 'INIT-123',
        title: 'Updated Initiative Title'
      });
      
      // Verify task create was called with resolved initiative_id
      expect(mockCreateTask).toHaveBeenCalledTimes(1);
      expect(mockCreateTask).toHaveBeenCalledWith({
        title: 'New Task for Initiative',
        description: 'Task description',
        checklist: [],
        initiative_id: 'initiative-uuid-123' // Resolved from initiative_identifier 'INIT-123'
      });
      
      // Verify no other operations were called
      expect(mockCreateInitiative).not.toHaveBeenCalled();
      expect(mockDeleteInitiative).not.toHaveBeenCalled();
      expect(mockUpdateTask).not.toHaveBeenCalled();
      expect(mockDeleteTask).not.toHaveBeenCalled();
    });

    it('should handle initiative update with delete task', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          tasks: [
            {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-456'
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative update was called with resolved ID
      expect(mockUpdateInitiative).toHaveBeenCalledTimes(1);
      expect(mockUpdateInitiative).toHaveBeenCalledWith({
        id: 'initiative-uuid-123', // Resolved from identifier 'INIT-123'
        identifier: 'INIT-123',
        title: 'Updated Initiative Title'
      });
      
      // Verify task delete was called with resolved ID
      expect(mockDeleteTask).toHaveBeenCalledTimes(1);
      expect(mockDeleteTask).toHaveBeenCalledWith('task-uuid-456');
      
      // Verify no other operations were called
      expect(mockCreateInitiative).not.toHaveBeenCalled();
      expect(mockDeleteInitiative).not.toHaveBeenCalled();
      expect(mockCreateTask).not.toHaveBeenCalled();
      expect(mockUpdateTask).not.toHaveBeenCalled();
    });

    it('should handle initiative update with update task', () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          tasks: [
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Updated Task Title',
              description: 'Updated task description',
              checklist: []
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      expect(() => result.current.saveSuggestions()).not.toThrow();
      expect(mockUseSuggestionsToBeResolvedContext().getAcceptedChanges).toHaveBeenCalled();
    });

    it('should handle initiative update with mixture of task operations', () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'New Task',
              description: 'New task description',
              checklist: [],
              initiative_identifier: 'INIT-123'
            },
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Updated Task Title',
              description: null,
              checklist: []
            },
            {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-789'
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      expect(() => result.current.saveSuggestions()).not.toThrow();
      expect(mockUseSuggestionsToBeResolvedContext().getAcceptedChanges).toHaveBeenCalled();
    });

    it('should handle initiative create with multiple task creates', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.CREATE,
          title: 'New Initiative',
          description: 'A new initiative with tasks',
          workspace_identifier: 'workspace-1',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'First New Task',
              description: 'First task description',
              checklist: [],
              initiative_identifier: 'new-initiative'
            },
            {
              action: ManagedEntityAction.CREATE,
              title: 'Second New Task',
              description: 'Second task description',
              checklist: [],
              initiative_identifier: 'new-initiative'
            },
            {
              action: ManagedEntityAction.CREATE,
              title: 'Third New Task',
              description: 'Third task description',
              checklist: [],
              initiative_identifier: 'new-initiative'
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative create was called with full payload including tasks (cleaned)
      expect(mockCreateInitiative).toHaveBeenCalledTimes(1);
      expect(mockCreateInitiative).toHaveBeenCalledWith({
        title: 'New Initiative',
        description: 'A new initiative with tasks',
        workspace_identifier: 'workspace-1',
        tasks: [
          {
            title: 'First New Task',
            description: 'First task description',
            checklist: [],
            initiative_identifier: 'new-initiative'
          },
          {
            title: 'Second New Task',
            description: 'Second task description',
            checklist: [],
            initiative_identifier: 'new-initiative'
          },
          {
            title: 'Third New Task',
            description: 'Third task description',
            checklist: [],
            initiative_identifier: 'new-initiative'
          }
        ]
      });
      
      // Verify no individual task operations were called (API handles task creation)
      expect(mockCreateTask).not.toHaveBeenCalled();
      expect(mockUpdateTask).not.toHaveBeenCalled();
      expect(mockDeleteTask).not.toHaveBeenCalled();
      
      // Verify no other initiative operations were called
      expect(mockUpdateInitiative).not.toHaveBeenCalled();
      expect(mockDeleteInitiative).not.toHaveBeenCalled();
    });
  });

  describe('multiple initiative operations', () => {
    it('should handle multiple initiative updates', () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative 1'
        },
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-456',
          title: 'Updated Initiative 2',
          description: 'Updated description 2'
        },
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-789',
          description: 'Only description updated'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      expect(() => result.current.saveSuggestions()).not.toThrow();
      expect(mockUseSuggestionsToBeResolvedContext().getAcceptedChanges).toHaveBeenCalled();
    });

    it('should handle multiple initiative creates', () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.CREATE,
          title: 'First New Initiative',
          description: 'First description',
          workspace_identifier: 'workspace-1'
        },
        {
          action: ManagedEntityAction.CREATE,
          title: 'Second New Initiative',
          description: 'Second description',
          workspace_identifier: 'workspace-1'
        },
        {
          action: ManagedEntityAction.CREATE,
          title: 'Third New Initiative',
          description: 'Third description',
          workspace_identifier: 'workspace-2'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      expect(() => result.current.saveSuggestions()).not.toThrow();
      expect(mockUseSuggestionsToBeResolvedContext().getAcceptedChanges).toHaveBeenCalled();
    });

    it('should handle multiple initiative deletes', () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.DELETE,
          identifier: 'INIT-123'
        },
        {
          action: ManagedEntityAction.DELETE,
          identifier: 'INIT-456'
        },
        {
          action: ManagedEntityAction.DELETE,
          identifier: 'INIT-789'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      expect(() => result.current.saveSuggestions()).not.toThrow();
      expect(mockUseSuggestionsToBeResolvedContext().getAcceptedChanges).toHaveBeenCalled();
    });

    it('should handle multiple mixed initiative operations', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.CREATE,
          title: 'New Initiative',
          description: 'New description',
          workspace_identifier: 'workspace-1',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'Task for new initiative',
              description: 'Task description',
              checklist: [],
              initiative_identifier: 'new-init'
            }
          ]
        },
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative',
          tasks: [
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Updated task title',
              description: null,
              checklist: []
            },
            {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-789'
            }
          ]
        },
        {
          action: ManagedEntityAction.DELETE,
          identifier: 'INIT-999'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify CREATE initiative was called with full payload (including tasks, cleaned)
      expect(mockCreateInitiative).toHaveBeenCalledTimes(1);
      expect(mockCreateInitiative).toHaveBeenCalledWith({
        title: 'New Initiative',
        description: 'New description',
        workspace_identifier: 'workspace-1',
        tasks: [
          {
            title: 'Task for new initiative',
            description: 'Task description',
            checklist: [],
            initiative_identifier: 'new-init'
          }
        ]
      });
      
      // Verify UPDATE initiative was called (excluding tasks) with resolved ID
      expect(mockUpdateInitiative).toHaveBeenCalledTimes(1);
      expect(mockUpdateInitiative).toHaveBeenCalledWith({
        id: 'initiative-uuid-123', // Resolved from identifier 'INIT-123'
        identifier: 'INIT-123',
        title: 'Updated Initiative'
      });
      
      // Verify DELETE initiative was called
      expect(mockDeleteInitiative).toHaveBeenCalledTimes(1);
      expect(mockDeleteInitiative).toHaveBeenCalledWith('initiative-uuid-999');
      
      // Verify task operations for UPDATE initiative only
      expect(mockUpdateTask).toHaveBeenCalledTimes(1);
      expect(mockUpdateTask).toHaveBeenCalledWith({
        id: 'task-uuid-456', // Resolved from identifier 'TASK-456'
        identifier: 'TASK-456',
        title: 'Updated task title',
        description: undefined, // null converted to undefined
        checklist: []
      });
      expect(mockDeleteTask).toHaveBeenCalledTimes(1);
      expect(mockDeleteTask).toHaveBeenCalledWith('task-uuid-789');
      
      // Verify no extra task create calls (CREATE initiative handles its own tasks)
      expect(mockCreateTask).not.toHaveBeenCalled();
    });
  });

  describe('should delete job when all suggestions are resolved', () => {
    it('should delete job when all suggestions are resolved', async () => {
      mockUseAiImprovementsContext.mockReturnValue({
        markJobAsResolved: mockMarkJobAsResolved,
        setThreadId: vi.fn(),
        jobResult: { id: 'job-id'} as AiImprovementJobResult,
        initiativeImprovements: {},
        taskImprovements: {},
        loading: false,
        error: null,
        isEntityLocked: false,
        requestImprovement: vi.fn(),
        updateImprovement: vi.fn(),
        resetError: vi.fn(),
      });

      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.CREATE,
          title: 'New Initiative',
          description: 'New description',
          workspace_identifier: 'workspace-1',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'Task for new initiative',
              description: 'Task description',
              checklist: [],
              initiative_identifier: 'new-init'
            }
          ]
        },
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();

      expect(mockMarkJobAsResolved).toHaveBeenCalledWith('job-id');
    });
  });

  describe('isSaving loading state', () => {
    it('should start with isSaving as false', () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      expect(result.current.isSaving).toBe(false);
    });

    it('should return isSaving to false after successful save', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      expect(result.current.isSaving).toBe(false);

      // Wait for the operation to complete
      await result.current.saveSuggestions();

      // isSaving should be false after completion
      expect(result.current.isSaving).toBe(false);
    });

    it('should return isSaving to false after validation error', async () => {
      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(false),
        getAcceptedChanges: vi.fn(),
        suggestions: {},
        resolutions: {},
        allResolved: false,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      expect(result.current.isSaving).toBe(false);

      // Wait for the operation to fail
      await expect(result.current.saveSuggestions()).rejects.toThrow('Suggestions are not fully resolved');

      // isSaving should be false after error
      expect(result.current.isSaving).toBe(false);
    });

    it('should return isSaving to false after API error', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      // Make updateInitiative fail
      mockUpdateInitiative.mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() => useSaveSuggestions());

      expect(result.current.isSaving).toBe(false);

      // Wait for the operation to fail
      await expect(result.current.saveSuggestions()).rejects.toThrow('API Error');

      // isSaving should be false after error
      expect(result.current.isSaving).toBe(false);
    });
  });

  describe('single initiative operations - with missing fields', () => {
    it('should handle single initiative update with missing title', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          // title is missing
          description: 'Updated description'
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative update was called with correct data including resolved ID
      expect(mockUpdateInitiative).toHaveBeenCalledTimes(1);
      expect(mockUpdateInitiative).toHaveBeenCalledWith({
        id: 'initiative-uuid-123', // Resolved from identifier 'INIT-123'
        identifier: 'INIT-123',
        title: undefined,
        description: 'Updated description'
      });
    })

    it('should handle single initiative update with missing description', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Updated Initiative Title',
          // description is missing
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative update was called with correct data including resolved ID
      expect(mockUpdateInitiative).toHaveBeenCalledTimes(1);
      expect(mockUpdateInitiative).toHaveBeenCalledWith({
        id: 'initiative-uuid-123', // Resolved from identifier 'INIT-123'
        identifier: 'INIT-123',
        title: 'Updated Initiative Title',
        description: undefined // description is not "" so it doesnt override the existing description
      });
    });

    it('should handle single initiative update with missing title and description', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          // title and description are missing
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'Task for new initiative',
              description: 'Task description',
              checklist: [],
              initiative_identifier: 'INIT-123'
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative update was not called
      expect(mockUpdateInitiative).toHaveBeenCalledTimes(0);

      // Verify task create was called with correct data
      expect(mockCreateTask).toHaveBeenCalledTimes(1);
      expect(mockCreateTask).toHaveBeenCalledWith({
        title: 'Task for new initiative',
        description: 'Task description',
        checklist: [],
        initiative_id: 'initiative-uuid-123'
      });
    })

    it('should handle single initiative create with missing description', async () => {
      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.CREATE,
          title: 'New Initiative',
          // description is missing
          workspace_identifier: 'workspace-1'
        } as CreateInitiativeModel
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      await result.current.saveSuggestions();
      
      // Verify initiative create was called with correct data
      expect(mockCreateInitiative).toHaveBeenCalledTimes(1);
      expect(mockCreateInitiative).toHaveBeenCalledWith({
        title: 'New Initiative',
        description: undefined,
        workspace_identifier: 'workspace-1'
      });

    });
  })

  describe('parallel task execution', () => {
    it('should execute multiple task operations in parallel', async () => {
      // Setup mock to track call order/timing
      const callOrder: string[] = [];

      mockCreateTask.mockImplementation(async (data) => {
        callOrder.push(`createTask-${data.title}`);
        await new Promise(resolve => setTimeout(resolve, 50));
        return { id: 'new-task-id' };
      });

      mockUpdateTask.mockImplementation(async (data) => {
        callOrder.push(`updateTask-${data.identifier}`);
        await new Promise(resolve => setTimeout(resolve, 50));
        return { id: data.id };
      });

      mockDeleteTask.mockImplementation(async (id) => {
        callOrder.push(`deleteTask-${id}`);
        await new Promise(resolve => setTimeout(resolve, 50));
        return;
      });

      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Initiative with multiple tasks',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'New Task 1',
              description: 'Task 1 description',
              checklist: []
            },
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Updated Task',
              description: 'Updated description',
              checklist: []
            },
            {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-789'
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      const startTime = Date.now();
      await result.current.saveSuggestions();
      const duration = Date.now() - startTime;

      // Verify all operations were called
      expect(mockCreateTask).toHaveBeenCalledTimes(1);
      expect(mockUpdateTask).toHaveBeenCalledTimes(1);
      expect(mockDeleteTask).toHaveBeenCalledTimes(1);

      // Verify all calls started before any completed (parallel execution)
      // All 3 tasks should start immediately, not wait for each other
      expect(callOrder).toHaveLength(3);

      // With parallel execution, total time should be ~50ms (one operation)
      // With sequential execution, it would be ~150ms (three operations)
      // Add some buffer for test execution overhead
      expect(duration).toBeLessThan(120); // Less than 2.5x single operation time
    });

    it('should handle partial task operation failures', async () => {
      mockCreateTask.mockResolvedValue({ id: 'new-task-id' });
      mockUpdateTask.mockRejectedValue(new Error('Update failed'));
      mockDeleteTask.mockResolvedValue(undefined);

      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Initiative Title',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'New Task',
              description: 'Description',
              checklist: []
            },
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Task to fail',
              description: 'Description',
              checklist: []
            },
            {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-789'
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      // Should throw error with failure details
      await expect(result.current.saveSuggestions()).rejects.toThrow('Task operations failed');

      // Verify all operations were attempted despite the failure
      expect(mockCreateTask).toHaveBeenCalled();
      expect(mockUpdateTask).toHaveBeenCalled();
      expect(mockDeleteTask).toHaveBeenCalled();
    });

    it('should include all failure reasons in error message', async () => {
      mockCreateTask.mockRejectedValue(new Error('Create failed'));
      mockUpdateTask.mockRejectedValue(new Error('Update failed'));
      mockDeleteTask.mockResolvedValue(undefined);

      const mockAcceptedChanges: ManagedInitiativeModel[] = [
        {
          action: ManagedEntityAction.UPDATE,
          identifier: 'INIT-123',
          title: 'Initiative',
          tasks: [
            {
              action: ManagedEntityAction.CREATE,
              title: 'New Task',
              description: 'Description',
              checklist: []
            },
            {
              action: ManagedEntityAction.UPDATE,
              identifier: 'TASK-456',
              title: 'Updated Task',
              description: 'Updated description',
              checklist: []
            },
            {
              action: ManagedEntityAction.DELETE,
              identifier: 'TASK-789'
            }
          ]
        }
      ];

      mockUseSuggestionsToBeResolvedContext.mockReturnValue({
        isFullyResolved: vi.fn().mockReturnValue(true),
        getAcceptedChanges: vi.fn().mockReturnValue(mockAcceptedChanges),
        suggestions: {},
        resolutions: {},
        allResolved: true,
        resolve: vi.fn(),
        rollback: vi.fn(),
        acceptAll: vi.fn(),
        rejectAll: vi.fn(),
        rollbackAll: vi.fn(),
        getResolutionState: vi.fn(),
      });

      const { result } = renderHook(() => useSaveSuggestions());

      try {
        await result.current.saveSuggestions();
        expect.fail('Should have thrown error');
      } catch (error: any) {
        // Verify error message contains both failure reasons
        expect(error.message).toContain('Task operations failed');
        expect(error.message).toContain('Create failed');
        expect(error.message).toContain('Update failed');
      }
    });
  })
});