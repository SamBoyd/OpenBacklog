import { ManagedEntityAction, ManagedTaskModel } from '#types';

/**
 * Applies a list of ManagedTaskModel operations to an existing tasks array.
 * Creates a new array with the operations applied in the order specified.
 * 
 * @param originalTasks - The original array of tasks to apply operations to
 * @param taskOps - Array of task operations (CREATE, UPDATE, DELETE) to apply
 * @returns A new array with the operations applied
 */
export function applyTaskOperations(
    originalTasks: any[] = [],
    taskOps: ManagedTaskModel[] = []
): any[] {
    if (!originalTasks || !taskOps) {
        return [];
    }

    // Create a lookup map from the original tasks by identifier
    const tasksByIdentifier: Record<string, any> = Object.fromEntries(
        (originalTasks || []).map(task => [task.identifier, { ...task }])
    );

    // Apply each operation in sequence
    for (const operation of taskOps) {
        if (!(operation as any).identifier) {
            continue; // Skip operations without identifiers
        }

        const identifier = (operation as any).identifier as string;

        switch (operation.action) {
            case ManagedEntityAction.CREATE: {
                // For CREATE operations, add the new task to the map
                const newTask = { ...operation };
                tasksByIdentifier[identifier] = newTask;
                break;
            }
            case ManagedEntityAction.UPDATE: {
                // For UPDATE operations, merge with existing task or create if doesn't exist
                const existingTask = tasksByIdentifier[identifier] || {};
                tasksByIdentifier[identifier] = {
                    ...existingTask,
                    ...operation,
                };
                break;
            }
            case ManagedEntityAction.DELETE: {
                // For DELETE operations, remove from the map
                delete tasksByIdentifier[identifier];
                break;
            }
        }
    }

    // Return all remaining tasks as an array
    return Object.values(tasksByIdentifier);
}