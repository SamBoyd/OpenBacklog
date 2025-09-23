import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useTaskDiff } from './useTaskDiff';
import { ManagedEntityAction, TaskDto, UpdateTaskModel, WorkspaceDto } from '#types';
import * as diff from 'diff';
import * as reactDiffView from 'react-diff-view';
import { FileData } from 'react-diff-view';

const testWorkspace: WorkspaceDto = {
  id: '1',
  name: 'Personal',
  description: null,
  icon: null
};


// Mock the external dependencies
vi.mock('diff', () => ({
  createPatch: vi.fn()
}));

vi.mock('react-diff-view', () => ({
  parseDiff: vi.fn()
}));

describe.skip('useTaskDiff', () => {
  // Mock console methods to prevent test output pollution
  const originalConsoleError = console.error;
  const originalConsoleDebug = console.debug;

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();

    // Mock console methods
    console.error = vi.fn();
    console.debug = vi.fn();

    // Mock implementation for createPatch
    (diff.createPatch as any).mockImplementation(
      (filename: string, oldStr: string, newStr: string) => {
        if (oldStr === newStr) return '';
        return `firstheader\n====\nmock diff for ${filename}`;
      }
    );

    // Mock implementation for parseDiff
    (reactDiffView.parseDiff as any).mockImplementation((diffString: string) => {
      if (!diffString) return [];
      return [{
        hunks: [{ changes: [{ type: 'insert', content: 'new content' }] }],
        oldPath: 'old/path',
        newPath: 'new/path',
        type: 'modify'
      } as FileData];
    });
  });

  afterEach(() => {
    // Restore console methods
    console.error = originalConsoleError;
    console.debug = originalConsoleDebug;
  });

  // Create mock tasks for testing
  const createMockTask = (
    title: string = 'Original Task Title',
    description: string | null = 'Original Task Description'
  ): TaskDto => ({
    id: '1',
    identifier: 'TASK-1',
    user_id: 'user1',
    initiative_id: 'init1',
    title,
    description: description ?? '', // Use empty string as default when description is null
    created_at: '2023-01-01',
    updated_at: '2023-01-01',
    status: 'TO_DO',
    type: 'CODING',
    checklist: [],
    has_pending_job: null,
    workspace: testWorkspace,
  });

  const createMockUpdateTask = (
    title: string = 'Original Task Title',
    description: string | null = 'Original Task Description'
  ): UpdateTaskModel => ({
    action: ManagedEntityAction.UPDATE,
    identifier: 'TASK-1',
    title,
    description,
    checklist: [],
  });

  it('should detect no changes when tasks are identical', () => {
    const original = createMockTask();
    const changed = createMockUpdateTask();

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.titleChanged).toBe(false);
    expect(result.current.descriptionChanged).toBe(false);
    expect(result.current.hasTitleChanges).toBe(false);
    expect(result.current.hasDescriptionChanges).toBe(false);
    expect(result.current.titleDiff).toBeNull();
    expect(result.current.descriptionDiff).toBeNull();
  });

  it('should detect title changes', () => {
    const original = createMockTask('Original Task Title');
    const changed = createMockUpdateTask('Changed Task Title');

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.titleChanged).toBe(true);
    expect(result.current.hasTitleChanges).toBe(true);
    expect(diff.createPatch).toHaveBeenCalledWith(
      'title',
      'Original Task Title\n',
      'Changed Task Title\n',
      '',
      '',
      { context: 3 }
    );
  });

  it('should detect description changes', () => {
    const original = createMockTask('Task Title', 'Original Task Description');
    const changed = createMockUpdateTask('Task Title', 'Changed Task Description');

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.descriptionChanged).toBe(true);
    expect(result.current.hasDescriptionChanges).toBe(true);
    expect(diff.createPatch).toHaveBeenCalledWith(
      'description',
      'Original Task Description\n',
      'Changed Task Description\n',
      '',
      '',
      { context: 3 }
    );
  });

  it('should handle null descriptions', () => {
    const original = createMockTask('Task Title', null);
    const changed = createMockUpdateTask('Task Title', 'New Task Description');

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.descriptionChanged).toBe(true);
    expect(diff.createPatch).toHaveBeenCalledWith(
      'description',
      '\n',
      'New Task Description\n',
      '',
      '',
      { context: 3 }
    );
  });

  it('should handle errors in createPatch', () => {
    const original = createMockTask();
    const changed = createMockUpdateTask('Changed Task Title');

    // Mock createPatch to throw an error
    (diff.createPatch as any).mockImplementationOnce(() => {
      throw new Error('Mock error in createPatch');
    });

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(console.error).toHaveBeenCalled();
    expect(result.current.titleDiff).toBeNull();
  });

  it('should handle errors in parseDiff', () => {
    const original = createMockTask();
    const changed = createMockUpdateTask('Changed Task Title');

    // Mock parseDiff to throw an error
    (reactDiffView.parseDiff as any).mockImplementationOnce(() => {
      throw new Error('Mock error in parseDiff');
    });

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(console.error).toHaveBeenCalled();
    expect(result.current.titleDiff).toBeNull();
  });

  it('should handle empty diff strings', () => {
    const original = createMockTask();
    const changed = createMockUpdateTask();

    // Force createPatch to return empty string
    (diff.createPatch as any).mockReturnValue('');

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.titleDiff).toBeNull();
    expect(result.current.descriptionDiff).toBeNull();
  });

  it('should handle invalid parsed diffs', () => {
    const original = createMockTask();
    const changed = createMockUpdateTask('Changed Task Title');

    // Mock parseDiff to return invalid structure
    (reactDiffView.parseDiff as any).mockReturnValueOnce([]);

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.titleDiff).toBeNull();
  });

  it('should detect when checklist items are added', () => {
    const original = createMockTask();
    const changed = createMockUpdateTask();

    // Add checklist items to the changed task
    changed.checklist = [
      { id: '1', title: 'New checklist item', order: 1, task_id: '1', is_complete: false }
    ];

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.checklistItemsChanged).toBe(true);
    expect(result.current.originalChecklistItems).toEqual([]);
    expect(result.current.changedChecklistItems).toEqual(changed.checklist);
  });

  it('should detect when checklist items are removed', () => {
    const original = createMockTask();
    original.checklist = [
      { id: '1', title: 'Checklist item', order: 1, task_id: '1', is_complete: false }
    ];

    const changed = createMockUpdateTask();
    changed.checklist = [];

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.checklistItemsChanged).toBe(true);
    expect(result.current.originalChecklistItems).toEqual(original.checklist);
    expect(result.current.changedChecklistItems).toEqual([]);
  });

  it('should detect when checklist item properties are modified', () => {
    const original = createMockTask();
    original.checklist = [
      { id: '1', title: 'Original title', order: 1, task_id: '1', is_complete: false }
    ];

    const changed = createMockUpdateTask();
    changed.checklist = [
      { id: '1', title: 'Modified title', order: 1, task_id: '1', is_complete: false }
    ];

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.checklistItemsChanged).toBe(true);
    expect(result.current.originalChecklistItems).toEqual(original.checklist);
    expect(result.current.changedChecklistItems).toEqual(changed.checklist);
  });

  it('should detect when checklist item completion status changes', () => {
    const original = createMockTask();
    original.checklist = [
      { id: '1', title: 'Checklist item', order: 1, task_id: '1', is_complete: false }
    ];

    const changed = createMockUpdateTask();
    changed.checklist = [
      { id: '1', title: 'Checklist item', order: 1, task_id: '1', is_complete: true }
    ];

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.checklistItemsChanged).toBe(true);
  });

  it('should detect when checklist item order changes', () => {
    const original = createMockTask();
    original.checklist = [
      { id: '1', title: 'First item', order: 1, task_id: '1', is_complete: false },
      { id: '2', title: 'Second item', order: 2, task_id: '1', is_complete: false }
    ];

    const changed = createMockUpdateTask();
    changed.checklist = [
      { id: '1', title: 'First item', order: 2, task_id: '1', is_complete: false },
      { id: '2', title: 'Second item', order: 1, task_id: '1', is_complete: false }
    ];

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.checklistItemsChanged).toBe(true);
  });

  it('should not detect changes when checklist items are identical', () => {
    const checklistItems = [
      { id: '1', title: 'Checklist item', order: 1, task_id: '1', is_complete: false }
    ];

    const original = createMockTask();
    original.checklist = [...checklistItems];

    const changed = createMockUpdateTask();
    changed.checklist = [...checklistItems];

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.checklistItemsChanged).toBe(false);
    expect(result.current.originalChecklistItems).toEqual(checklistItems);
    expect(result.current.changedChecklistItems).toEqual(checklistItems);
  });

  it('should handle multiple checklist item changes simultaneously', () => {
    const original = createMockTask();
    original.checklist = [
      { id: '1', title: 'Item to keep', order: 1, task_id: '1', is_complete: false },
      { id: '2', title: 'Item to modify', order: 2, task_id: '1', is_complete: false },
      { id: '3', title: 'Item to remove', order: 3, task_id: '1', is_complete: false }
    ];

    const changed = createMockUpdateTask();
    changed.checklist = [
      { id: '1', title: 'Item to keep', order: 1, task_id: '1', is_complete: false },
      { id: '2', title: 'Modified item', order: 2, task_id: '1', is_complete: true },
      { id: '4', title: 'New item', order: 3, task_id: '1', is_complete: false }
    ];

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.checklistItemsChanged).toBe(true);
    expect(result.current.originalChecklistItems).toHaveLength(3);
    expect(result.current.changedChecklistItems).toHaveLength(3);
  });

  it('should not detect changes when both checklist item lists are empty', () => {
    const original = createMockTask();
    original.checklist = [];

    const changed = createMockUpdateTask();
    changed.checklist = [];

    const { result } = renderHook(() => useTaskDiff(original, changed));

    expect(result.current.checklistItemsChanged).toBe(false);
    expect(result.current.originalChecklistItems).toEqual([]);
    expect(result.current.changedChecklistItems).toEqual([]);
  });
});
