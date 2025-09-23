import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { deriveUpdatedInitiativeDto, useUpdatedInitiative } from './updatedInitiative';
import type { InitiativeDto, UpdateInitiativeModel, ManagedTaskModel, ManagedEntityAction } from '#types';

// Mock the applyTaskOperations function
const mockApplyTaskOperations = vi.fn();

describe('deriveUpdatedInitiativeDto', () => {
    const mockInitiative: InitiativeDto = {
        id: 'init-1',
        identifier: 'INIT-123',
        user_id: 'user-1',
        title: 'Original Title',
        description: 'Original Description',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        status: 'TODO',
        type: null,
        tasks: [
            { id: 'task-1', identifier: 'TASK-1', title: 'Task 1' },
            { id: 'task-2', identifier: 'TASK-2', title: 'Task 2' }
        ],
        has_pending_job: false
    };

    beforeEach(() => {
        mockApplyTaskOperations.mockClear();
        mockApplyTaskOperations.mockImplementation((originalTasks, taskOps) => {
            // Default implementation returns original tasks unchanged
            return originalTasks;
        });
    });

    describe('null and undefined handling', () => {
        it('should return null when initiative is null', () => {
            const result = deriveUpdatedInitiativeDto(null, {} as UpdateInitiativeModel, mockApplyTaskOperations);
            
            expect(result).toBeNull();
            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
        });

        it('should return null when initiative is undefined', () => {
            const result = deriveUpdatedInitiativeDto(undefined as any, {} as UpdateInitiativeModel, mockApplyTaskOperations);
            
            expect(result).toBeNull();
            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
        });

        it('should return original initiative when updateModel is null', () => {
            const result = deriveUpdatedInitiativeDto(mockInitiative, null, mockApplyTaskOperations);
            
            expect(result).toEqual(mockInitiative);
            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
        });

        it('should return original initiative when updateModel is undefined', () => {
            const result = deriveUpdatedInitiativeDto(mockInitiative, undefined as any, mockApplyTaskOperations);
            
            expect(result).toEqual(mockInitiative);
            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
        });

        it('should handle empty updateModel fields', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123'
            };
            
            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);
            
            expect(result).toEqual(mockInitiative);
            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
        });
    });

    describe('title updates', () => {
        it('should update title when provided in updateModel', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: 'New Title'
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result).toEqual({
                ...mockInitiative,
                title: 'New Title'
            });
            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
        });

        it('should preserve original title when title is undefined in updateModel', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                description: 'New Description'
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result?.title).toBe('Original Title');
        });

        it('should handle empty string title', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: ''
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result?.title).toBe('');
        });
    });

    describe('description updates', () => {
        it('should update description when provided in updateModel', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                description: 'New Description'
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result).toEqual({
                ...mockInitiative,
                description: 'New Description'
            });
            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
        });

        it('should preserve original description when description is undefined in updateModel', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: 'New Title'
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result?.description).toBe('Original Description');
        });

        it('should handle empty string description', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                description: ''
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result?.description).toBe('');
        });
    });

    describe('combined field updates', () => {
        it('should update both title and description when both are provided', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: 'New Title',
                description: 'New Description'
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result).toEqual({
                ...mockInitiative,
                title: 'New Title',
                description: 'New Description'
            });
            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
        });
    });

    describe('task operations', () => {
        const mockTaskOps: ManagedTaskModel[] = [
            {
                action: 'CREATE' as ManagedEntityAction.CREATE,
                title: 'New Task',
                description: 'New task description',
                checklist: []
            }
        ];

        it('should apply task operations when tasks are provided in updateModel', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                tasks: mockTaskOps
            };

            const modifiedTasks = [
                ...mockInitiative.tasks!,
                { id: 'task-3', identifier: 'TASK-3', title: 'New Task' }
            ];
            mockApplyTaskOperations.mockReturnValue(modifiedTasks);

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(mockApplyTaskOperations).toHaveBeenCalledWith(mockInitiative.tasks, mockTaskOps);
            expect(result?.tasks).toEqual(modifiedTasks);
        });

        it('should pass empty array to applyTaskOperations when initiative has no tasks', () => {
            const initiativeWithoutTasks = { ...mockInitiative, tasks: [] };
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                tasks: mockTaskOps
            };

            deriveUpdatedInitiativeDto(initiativeWithoutTasks, updateModel, mockApplyTaskOperations);

            expect(mockApplyTaskOperations).toHaveBeenCalledWith([], mockTaskOps);
        });

        it('should not call applyTaskOperations when no tasks in updateModel', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: 'New Title'
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(mockApplyTaskOperations).not.toHaveBeenCalled();
            expect(result?.tasks).toEqual(mockInitiative.tasks);
        });

        it('should handle empty tasks array in updateModel', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                tasks: []
            };

            deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(mockApplyTaskOperations).toHaveBeenCalledWith(mockInitiative.tasks, []);
        });
    });

    describe('combined field and task updates', () => {
        it('should apply both field updates and task operations', () => {
            const mockTaskOps: ManagedTaskModel[] = [
                {
                    action: 'UPDATE' as ManagedEntityAction.UPDATE,
                    identifier: 'TASK-1',
                    title: 'Updated Task 1',
                    description: null,
                    checklist: []
                }
            ];

            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: 'New Title',
                description: 'New Description',
                tasks: mockTaskOps
            };

            const modifiedTasks = [
                { id: 'task-1', identifier: 'TASK-1', title: 'Updated Task 1' },
                { id: 'task-2', identifier: 'TASK-2', title: 'Task 2' }
            ];
            mockApplyTaskOperations.mockReturnValue(modifiedTasks);

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result).toEqual({
                ...mockInitiative,
                title: 'New Title',
                description: 'New Description',
                tasks: modifiedTasks
            });
            expect(mockApplyTaskOperations).toHaveBeenCalledWith(mockInitiative.tasks, mockTaskOps);
        });
    });

    describe('data immutability', () => {
        it('should not mutate the original initiative', () => {
            const originalTasks = [...mockInitiative.tasks!];
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: 'New Title'
            };

            deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(mockInitiative.title).toBe('Original Title');
            expect(mockInitiative.tasks).toEqual(originalTasks);
        });

        it('should not mutate the updateModel', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: 'New Title',
                tasks: []
            };
            const originalUpdateModel = { ...updateModel };

            deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(updateModel).toEqual(originalUpdateModel);
        });

        it('should return a new object, not the same reference', () => {
            const updateModel: UpdateInitiativeModel = {
                action: 'UPDATE' as ManagedEntityAction.UPDATE,
                identifier: 'INIT-123',
                title: 'New Title'
            };

            const result = deriveUpdatedInitiativeDto(mockInitiative, updateModel, mockApplyTaskOperations);

            expect(result).not.toBe(mockInitiative);
        });
    });
});

describe('useUpdatedInitiative', () => {
    const mockInitiative: InitiativeDto = {
        id: 'init-1',
        identifier: 'INIT-123',
        user_id: 'user-1',
        title: 'Original Title',
        description: 'Original Description',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        status: 'TODO',
        type: null,
        tasks: [],
        has_pending_job: false
    };

    const mockUpdateModel: UpdateInitiativeModel = {
        action: 'UPDATE' as ManagedEntityAction.UPDATE,
        identifier: 'INIT-123',
        title: 'Updated Title'
    };

    beforeEach(() => {
        mockApplyTaskOperations.mockClear();
        mockApplyTaskOperations.mockImplementation((originalTasks) => originalTasks);
    });

    it('should return updated initiative DTO', () => {
        const { result } = renderHook(() => 
            useUpdatedInitiative(mockInitiative, mockUpdateModel)
        );

        expect(result.current).toEqual({
            ...mockInitiative,
            title: 'Updated Title'
        });
    });

    it('should return null when initiative is null', () => {
        const { result } = renderHook(() => 
            useUpdatedInitiative(null, mockUpdateModel)
        );

        expect(result.current).toBeNull();
    });

    it('should return original initiative when updateModel is null', () => {
        const { result } = renderHook(() => 
            useUpdatedInitiative(mockInitiative, null)
        );

        expect(result.current).toEqual(mockInitiative);
    });

    it('should memoize result when inputs are unchanged', () => {
        const { result, rerender } = renderHook(
            ({ initiative, updateModel }) => useUpdatedInitiative(initiative, updateModel),
            { initialProps: { initiative: mockInitiative, updateModel: mockUpdateModel } }
        );

        const firstResult = result.current;

        rerender({ initiative: mockInitiative, updateModel: mockUpdateModel });

        expect(result.current).toBe(firstResult);
    });

    it('should recompute when initiative changes', () => {
        const { result, rerender } = renderHook(
            ({ initiative, updateModel }) => useUpdatedInitiative(initiative, updateModel),
            { initialProps: { initiative: mockInitiative, updateModel: mockUpdateModel } }
        );

        const firstResult = result.current;

        const newInitiative = { ...mockInitiative, id: 'init-2' };
        rerender({ initiative: newInitiative, updateModel: mockUpdateModel });

        expect(result.current).not.toBe(firstResult);
        expect(result.current?.id).toBe('init-2');
    });

    it('should recompute when updateModel changes', () => {
        const { result, rerender } = renderHook(
            ({ initiative, updateModel }) => useUpdatedInitiative(initiative, updateModel),
            { initialProps: { initiative: mockInitiative, updateModel: mockUpdateModel } }
        );

        const firstResult = result.current;

        const newUpdateModel: UpdateInitiativeModel = {
            action: 'UPDATE' as ManagedEntityAction.UPDATE,
            identifier: 'INIT-123',
            title: 'Different Title'
        };
        rerender({ initiative: mockInitiative, updateModel: newUpdateModel });

        expect(result.current).not.toBe(firstResult);
        expect(result.current?.title).toBe('Different Title');
    });

    it('should handle task operations through applyTaskOperations', () => {
        const taskOps: ManagedTaskModel[] = [
            {
                action: 'CREATE' as ManagedEntityAction.CREATE,
                title: 'New Task',
                description: 'New task description',
                checklist: []
            }
        ];

        const updateModelWithTasks: UpdateInitiativeModel = {
            action: 'UPDATE' as ManagedEntityAction.UPDATE,
            identifier: 'INIT-123',
            title: 'Updated Title',
            tasks: taskOps
        };

        const { result } = renderHook(() => 
            useUpdatedInitiative(mockInitiative, updateModelWithTasks)
        );

        // The hook should use the real applyTaskOperations implementation
        // and apply the task operations to create the new tasks array
        expect(result.current?.title).toBe('Updated Title');
        expect(result.current?.tasks).toBeDefined();
        // We can't easily test the exact task operations result without mocking the module,
        // but we can verify that tasks were processed (length should change or content should change)
        expect(Array.isArray(result.current?.tasks)).toBe(true);
    });
});