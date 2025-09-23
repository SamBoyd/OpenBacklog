import { describe, it, expect } from 'vitest';
import { applyTaskOperations } from './applyTaskOperations';
import { ManagedEntityAction, ManagedTaskModel } from '#types';

describe('applyTaskOperations', () => {
    const mockTask1 = {
        id: '1',
        identifier: 'TASK-1',
        title: 'Original Task 1',
        description: 'Original description 1',
        status: 'TO_DO'
    };

    const mockTask2 = {
        id: '2',
        identifier: 'TASK-2',
        title: 'Original Task 2',
        description: 'Original description 2',
        status: 'IN_PROGRESS'
    };

    const originalTasks = [mockTask1, mockTask2];

    describe('CREATE operations', () => {
        it('should add a new task when CREATE operation is provided', () => {
            const createOp: ManagedTaskModel = {
                action: ManagedEntityAction.CREATE,
                title: 'New Task',
                description: 'New description',
                checklist: [],
                identifier: 'TASK-3'
            } as any;

            const result = applyTaskOperations(originalTasks, [createOp]);

            expect(result).toHaveLength(3);
            expect(result.find(t => t.identifier === 'TASK-3')).toEqual(
                expect.objectContaining({
                    action: ManagedEntityAction.CREATE,
                    identifier: 'TASK-3',
                    title: 'New Task',
                    description: 'New description'
                })
            );
        });

        it('should create multiple new tasks with multiple CREATE operations', () => {
            const createOps: ManagedTaskModel[] = [
                {
                    action: ManagedEntityAction.CREATE,
                    title: 'New Task 1',
                    description: 'Description 1',
                    checklist: [],
                    identifier: 'TASK-3'
                } as any,
                {
                    action: ManagedEntityAction.CREATE,
                    title: 'New Task 2',
                    description: 'Description 2',
                    checklist: [],
                    identifier: 'TASK-4'
                } as any
            ];

            const result = applyTaskOperations(originalTasks, createOps);

            expect(result).toHaveLength(4);
            expect(result.find(t => t.identifier === 'TASK-3')).toBeDefined();
            expect(result.find(t => t.identifier === 'TASK-4')).toBeDefined();
        });
    });

    describe('UPDATE operations', () => {
        it('should update existing task when UPDATE operation is provided', () => {
            const updateOp: ManagedTaskModel = {
                action: ManagedEntityAction.UPDATE,
                identifier: 'TASK-1',
                title: 'Updated Task 1',
                description: 'Updated description 1',
                checklist: []
            };

            const result = applyTaskOperations(originalTasks, [updateOp]);

            expect(result).toHaveLength(2);
            const updatedTask = result.find(t => t.identifier === 'TASK-1');
            expect(updatedTask).toEqual(
                expect.objectContaining({
                    id: '1',
                    identifier: 'TASK-1',
                    title: 'Updated Task 1',
                    description: 'Updated description 1',
                    status: 'TO_DO', // Original field preserved
                    action: ManagedEntityAction.UPDATE
                })
            );
        });

        it('should create new task if UPDATE operation targets non-existent identifier', () => {
            const updateOp: ManagedTaskModel = {
                action: ManagedEntityAction.UPDATE,
                identifier: 'TASK-99',
                title: 'New Task from Update',
                description: 'Description',
                checklist: []
            };

            const result = applyTaskOperations(originalTasks, [updateOp]);

            expect(result).toHaveLength(3);
            expect(result.find(t => t.identifier === 'TASK-99')).toEqual(
                expect.objectContaining({
                    identifier: 'TASK-99',
                    title: 'New Task from Update',
                    description: 'Description'
                })
            );
        });

        it('should preserve original fields not specified in UPDATE operation', () => {
            const updateOp: ManagedTaskModel = {
                action: ManagedEntityAction.UPDATE,
                identifier: 'TASK-1',
                title: 'Only Title Updated',
                description: null,
                checklist: []
            };

            const result = applyTaskOperations(originalTasks, [updateOp]);

            const updatedTask = result.find(t => t.identifier === 'TASK-1');
            expect(updatedTask).toEqual(
                expect.objectContaining({
                    id: '1', // Original field preserved
                    status: 'TO_DO', // Original field preserved
                    title: 'Only Title Updated' // Updated field
                })
            );
        });
    });

    describe('DELETE operations', () => {
        it('should remove task when DELETE operation is provided', () => {
            const deleteOp: ManagedTaskModel = {
                action: ManagedEntityAction.DELETE,
                identifier: 'TASK-1'
            };

            const result = applyTaskOperations(originalTasks, [deleteOp]);

            expect(result).toHaveLength(1);
            expect(result.find(t => t.identifier === 'TASK-1')).toBeUndefined();
            expect(result.find(t => t.identifier === 'TASK-2')).toBeDefined();
        });

        it('should handle DELETE operation for non-existent identifier gracefully', () => {
            const deleteOp: ManagedTaskModel = {
                action: ManagedEntityAction.DELETE,
                identifier: 'TASK-99'
            };

            const result = applyTaskOperations(originalTasks, [deleteOp]);

            expect(result).toHaveLength(2);
            expect(result).toEqual(expect.arrayContaining([
                expect.objectContaining({ identifier: 'TASK-1' }),
                expect.objectContaining({ identifier: 'TASK-2' })
            ]));
        });
    });

    describe('Mixed operations', () => {
        it('should apply multiple different operations in sequence', () => {
            const operations: ManagedTaskModel[] = [
                {
                    action: ManagedEntityAction.UPDATE,
                    identifier: 'TASK-1',
                    title: 'Updated Task 1',
                    description: null,
                    checklist: []
                },
                {
                    action: ManagedEntityAction.DELETE,
                    identifier: 'TASK-2'
                },
                {
                    action: ManagedEntityAction.CREATE,
                    title: 'New Task',
                    description: 'New description',
                    checklist: [],
                    identifier: 'TASK-3'
                } as any
            ];

            const result = applyTaskOperations(originalTasks, operations);

            expect(result).toHaveLength(2);
            expect(result.find(t => t.identifier === 'TASK-1')).toEqual(
                expect.objectContaining({ title: 'Updated Task 1' })
            );
            expect(result.find(t => t.identifier === 'TASK-2')).toBeUndefined();
            expect(result.find(t => t.identifier === 'TASK-3')).toBeDefined();
        });

        it('should handle operations that overwrite each other (later operations win)', () => {
            const operations: ManagedTaskModel[] = [
                {
                    action: ManagedEntityAction.UPDATE,
                    identifier: 'TASK-1',
                    title: 'First Update',
                    description: null,
                    checklist: []
                },
                {
                    action: ManagedEntityAction.UPDATE,
                    identifier: 'TASK-1',
                    title: 'Second Update',
                    description: null,
                    checklist: []
                }
            ];

            const result = applyTaskOperations(originalTasks, operations);

            const updatedTask = result.find(t => t.identifier === 'TASK-1');
            expect(updatedTask?.title).toBe('Second Update');
        });
    });

    describe('Edge cases', () => {
        it('should handle empty original tasks array', () => {
            const createOp: ManagedTaskModel = {
                action: ManagedEntityAction.CREATE,
                title: 'New Task',
                description: 'Description',
                checklist: [],
                identifier: 'TASK-1'
            } as any;

            const result = applyTaskOperations([], [createOp]);

            expect(result).toHaveLength(1);
            expect(result[0]).toEqual(expect.objectContaining({
                identifier: 'TASK-1',
                title: 'New Task'
            }));
        });

        it('should handle empty operations array', () => {
            const result = applyTaskOperations(originalTasks, []);

            expect(result).toHaveLength(2);
            expect(result).toEqual(expect.arrayContaining([
                expect.objectContaining({ identifier: 'TASK-1' }),
                expect.objectContaining({ identifier: 'TASK-2' })
            ]));
        });

        it('should handle undefined/null inputs gracefully', () => {
            expect(() => applyTaskOperations(undefined, undefined)).not.toThrow();
            expect(() => applyTaskOperations(null as any, null as any)).not.toThrow();
            expect(applyTaskOperations(undefined, undefined)).toEqual([]);
        });

        it('should skip operations without identifiers', () => {
            const operations = [
                {
                    action: ManagedEntityAction.CREATE,
                    title: 'Task without identifier',
                    description: 'Description',
                    checklist: []
                } as any, // Missing identifier
                {
                    action: ManagedEntityAction.UPDATE,
                    identifier: 'TASK-1',
                    title: 'Valid Update',
                    description: null,
                    checklist: []
                }
            ];

            const result = applyTaskOperations(originalTasks, operations);

            expect(result).toHaveLength(2);
            expect(result.find(t => t.title === 'Task without identifier')).toBeUndefined();
            expect(result.find(t => t.identifier === 'TASK-1')?.title).toBe('Valid Update');
        });

        it('should handle operations with null/undefined identifiers', () => {
            const operations = [
                {
                    action: ManagedEntityAction.CREATE,
                    title: 'Task with null identifier',
                    description: 'Description',
                    checklist: [],
                    identifier: null
                } as any,
                {
                    action: ManagedEntityAction.CREATE,
                    title: 'Task with undefined identifier',
                    description: 'Description',
                    checklist: []
                    // identifier is undefined
                } as any
            ];

            const result = applyTaskOperations(originalTasks, operations);

            expect(result).toHaveLength(2); // Should still have original tasks
            expect(result.find(t => t.title === 'Task with null identifier')).toBeUndefined();
            expect(result.find(t => t.title === 'Task with undefined identifier')).toBeUndefined();
        });
    });

    describe('Data immutability', () => {
        it('should not mutate original tasks array', () => {
            const originalTasksCopy = JSON.parse(JSON.stringify(originalTasks));
            const updateOp: ManagedTaskModel = {
                action: ManagedEntityAction.UPDATE,
                identifier: 'TASK-1',
                title: 'Updated Title',
                description: null,
                checklist: []
            };

            applyTaskOperations(originalTasks, [updateOp]);

            expect(originalTasks).toEqual(originalTasksCopy);
        });

        it('should not mutate individual task objects', () => {
            const originalTask1Copy = { ...mockTask1 };
            const updateOp: ManagedTaskModel = {
                action: ManagedEntityAction.UPDATE,
                identifier: 'TASK-1',
                title: 'Updated Title',
                description: null,
                checklist: []
            };

            applyTaskOperations(originalTasks, [updateOp]);

            expect(originalTasks[0]).toEqual(originalTask1Copy);
        });
    });
});