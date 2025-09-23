import { TaskDto, TaskSchema } from '#types';
import { getPostgrestClient, withApiCall } from './api-utils';
import { checklistItemFromData, deleteChecklistItem, postChecklistItem } from './checklistItems';
import { getCurrentWorkspaceFromCookie } from '#services/workspaceApi';
import { orderingsFromData } from './orderings';
import { loadAndValidateJWT } from '#api/jwt';

export function taskFromData(data: any): TaskDto {
    return {
        id: data.id,
        identifier: data.identifier,
        user_id: data.user_id,
        initiative_id: data.initiative_id,
        title: data.title,
        description: data.description,
        created_at: data.created_at,
        updated_at: data.updated_at,
        status: data.status,
        type: data.type,
        has_pending_job: data.has_pending_job,
        checklist: data.checklist?.map((item: any) =>
            checklistItemFromData(item),
        ),
        workspace: data.workspace,
        orderings: data.orderings ? orderingsFromData(data.orderings) : undefined,
    };
}

export function taskToPayloadJSON(data: Partial<TaskDto>): any {
    return {
        id: data.id,
        identifier: data.identifier,
        user_id: data.user_id,
        initiative_id: data.initiative_id,
        title: data.title,
        description: data.description,
        created_at: data.created_at,
        updated_at: data.updated_at,
        status: data.status,
        type: data.type,
        has_pending_job: data.has_pending_job,
    }
}

export async function createTask(task: Partial<TaskDto>): Promise<TaskDto> {
    const workspace = getCurrentWorkspaceFromCookie();
    
    if (!workspace?.id) {
        throw new Error('No workspace found');
    }

    // Validate title length
    if (task.title && task.title.length > 200) {
        throw new Error('Title must be 200 characters or less');
    }

    const requestPayload = {
        title: task.title,
        status: task.status || 'TO_DO',
        type: task.type || null,
        description: task.description || null,
        checklist: task.checklist?.map(item => ({
            title: item.title,
            is_complete: item.is_complete || false,
            order: item.order || 0
        })) || [],
        workspace_id: workspace.id,
        initiative_id: task.initiative_id
    };

    return withApiCall(async () => {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${loadAndValidateJWT()}`
            },
            body: JSON.stringify(requestPayload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const createdTaskData = await response.json();
        return taskFromData(createdTaskData);
    });
}

export async function postTask(task: Partial<TaskDto>): Promise<TaskDto> {
    const workspace = getCurrentWorkspaceFromCookie();
    
    // Validate title length
    if (task.title && task.title.length > 200) {
        throw new Error('Title must be 200 characters or less');
    }
    
    const jsonPayload = taskToPayloadJSON(task);
    jsonPayload['workspace_id'] = workspace?.id;

    const response = await withApiCall(async () => {
        return await getPostgrestClient()
            .from('task')
            .update(jsonPayload)
            .eq('id', task.id)
            .select("*, checklist(*), orderings(*)")
            .then(response => {
                if (response.error) {
                    console.error('Error posting task', response);
                    throw new Error(response.error.message);
                }

                return response.data as Partial<TaskDto>[];
            })
    })


    if (!response || response.length === 0) {
        throw new Error('No task created');
    }

    const createdTask = taskFromData(response[0]);

    const checklistItemsWithTaskId = task.checklist?.map(item => {
        const workspace = getCurrentWorkspaceFromCookie();
        return {
            ...item,
            task_id: createdTask.id,
            workspace_id: workspace?.id,
        };
    }) || [];

    await Promise.all(checklistItemsWithTaskId.map(item => postChecklistItem(item)));

    if (createdTask.checklist && createdTask.checklist.length > 0) {
        // After creating the createdTask, compare and delete checklist items that are not in the passed task
        const deletedChecklistItems = createdTask.checklist.filter(
            (createdItem) =>
                !task.checklist?.some(
                    (passedItem) => passedItem.id === createdItem.id
                )
        );

        // Delete the checklist items that have been removed
        await Promise.all(
            deletedChecklistItems.map((item) => item.id ? deleteChecklistItem(item.id) : Promise.resolve())
        );

        // Remove the deleted checklist items from the createdTask
        const updatedTask = {
            ...createdTask,
            checklist: createdTask.checklist.filter(
                (item) =>
                    task.checklist?.some((passedItem) => passedItem.id === item.id)
            )
        };

        return updatedTask;
    } else {
        return createdTask;
    }
};

export async function deleteTask(taskId: string): Promise<void> {
    return withApiCall(async () => {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${loadAndValidateJWT()}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
    });
}

export async function getTaskById(id: string): Promise<TaskDto> {
    const workspace = getCurrentWorkspaceFromCookie();

    return withApiCall(async () => {
        return await getPostgrestClient()
            .from('task')
            .select(
                `
                    *,
                    checklist(*),
                    orderings(*)
                `
            )
            .eq('id', id)
            .eq('workspace_id', workspace?.id)
            .then(response => {
                if (response.error) {
                    console.error('Error loading task', response.error);
                    throw new Error('Error loading task');
                }

                if (response.data.length == 0) {
                    throw new Error('Task not found');
                }

                if (response.data.length > 1) {
                    console.error('Error loading task - multiple tasks found');
                    throw new Error('Error loading task');
                }

                const parsedData = TaskSchema.safeParse(response.data[0]);
                if (!parsedData.success) {
                    console.error('Error loading task - data format', parsedData.error);
                    throw new Error(`Error loading task`);
                }

                return taskFromData(parsedData.data);
            });
    })
}

export async function getAllTasks(): Promise<TaskDto[]> {
    const workspace = getCurrentWorkspaceFromCookie();

    return withApiCall(async () => {
        return await getPostgrestClient()
            .from('task')
            .select(
                `
                *,
                checklist(*),
                orderings(*)
            `   
            )
            .eq('workspace_id', workspace?.id)
            .then(response => {
                if (response.error) {
                    console.error('Error loading tasks', response.error);
                    throw new Error('Error loading tasks');
                }

                const parsedData = TaskSchema.array().safeParse(response.data);
                if (!parsedData.success) {
                    console.error('Error loading tasks - data format', parsedData.error);
                    throw new Error(`Error loading tasks ${parsedData.error}`);
                }

                return parsedData.data.map(task => taskFromData(task));
            });
    })
}

export async function getAllTasksForInitiatives(initiativeId: string): Promise<TaskDto[]> {
    const workspace = getCurrentWorkspaceFromCookie();

    return withApiCall(async () => {
        return await getPostgrestClient()
            .from('task')
            .select(
            `
              *,
              checklist(*),
              orderings(*)
          `,
        )
        .eq('initiative_id', initiativeId)
        .eq('workspace_id', workspace?.id)
        .then(response => {
            if (response.error) {
                console.error('Error loading tasks', response.error);
                throw new Error('Error loading tasks');
            }

            const parsedData = TaskSchema.array().safeParse(response.data);
            if (!parsedData.success) {
                console.error('Error loading tasks - data format', parsedData.error);
                throw new Error(`Error loading tasks`);
            }

                return parsedData.data.map(task => taskFromData(task));
            });
    })
}

/**
 * Moves a task to a new position within the same status.
 * @param {string} taskId - The ID of the task to move
 * @param {string} [afterId] - The ID of the task to move after
 * @param {string} [beforeId] - The ID of the task to move before
 * @returns {Promise<TaskDto>} The updated task
 */
export async function moveTask(
    taskId: string,
    afterId: string | null,
    beforeId: string | null
): Promise<TaskDto> {
    const requestPayload = {
        after_id: afterId,
        before_id: beforeId
    };

    return withApiCall(async () => {
        const response = await fetch(`/api/tasks/${taskId}/move`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${loadAndValidateJWT()}`
            },
            body: JSON.stringify(requestPayload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const updatedTaskData = await response.json();
        return taskFromData(updatedTaskData);
    });
}

/**
 * Moves a task to a new status and optionally to a new position within that status.
 * @param {string} taskId - The ID of the task to move
 * @param {string} newStatus - The new status for the task
 * @param {string} [afterId] - The ID of the task to move after
 * @param {string} [beforeId] - The ID of the task to move before
 * @returns {Promise<TaskDto>} The updated task
 */
export async function moveTaskToStatus(
    taskId: string,
    newStatus: string,
    afterId: string | null,
    beforeId: string | null
): Promise<TaskDto> {
    const requestPayload = {
        new_status: newStatus,
        after_id: afterId,
        before_id: beforeId
    };

    return withApiCall(async () => {
        const response = await fetch(`/api/tasks/${taskId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${loadAndValidateJWT()}`
            },
            body: JSON.stringify(requestPayload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const updatedTaskData = await response.json();
        return taskFromData(updatedTaskData);
    });
}
