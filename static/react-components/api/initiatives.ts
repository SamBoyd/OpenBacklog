import { EntityType, InitiativeDto, InitiativeDtoSchema } from '#types';
import { fetchCurrentWorkspace } from '#services/workspaceApi';
import { getPostgrestClient, withApiCall } from '#api/api-utils';
import { loadAndValidateJWT } from '#api/jwt';
import { createTask, postTask, taskFromData } from '#api/tasks';
import { orderingsFromData } from './orderings';
import { InitiativeFilters } from '#contexts/InitiativesContext';

export function initiativeFromData(data: any): InitiativeDto {
    const response: Partial<InitiativeDto> = {
        id: data.id,
        identifier: data.identifier,
        user_id: data.user_id,
        title: data.title,
        created_at: data.created_at,
        updated_at: data.updated_at,
        status: data.status,
        has_pending_job: data.has_pending_job,
        tasks: data.tasks?.map((task: any) => taskFromData(task)),
        properties: data.properties,
        orderings: data.orderings ? orderingsFromData(data.orderings) : undefined,
    };

    if (data.description) {
        response.description = data.description;
    }

    if (data.type) {
        response.type = data.type;
    }

    return response as InitiativeDto;
}

export function initiativeToPayloadJSON(data: Partial<InitiativeDto>): any {
    return {
        id: data.id,
        identifier: data.identifier,
        user_id: data.user_id,
        title: data.title,
        description: data.description || '',
        created_at: data.created_at,
        updated_at: data.updated_at,
        status: data.status,
        type: data.type,
        has_pending_job: data.has_pending_job ? data.has_pending_job : false,
        properties: data.properties,
    }
}

export async function getAllInitiatives(filters?: InitiativeFilters): Promise<InitiativeDto[]> {
    // Get the current workspace
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        // Start building the query
        let query = getPostgrestClient()
            .from('initiative')
            .select(
                `
              *,
              task(*, checklist(*), orderings(*)),
              orderings(*)
          `,
            )
            .eq('workspace_id', currentWorkspace.id);

        // Apply ID array filter if provided
        if (filters?.ids && filters.ids.length > 0) {
            query = query.in('id', filters.ids);
        }

        // Apply status filter if it exists
        if (filters?.status && filters.status.length > 0) {
            query = query.in('status', filters.status);
        }

        // Add other filters here as needed...

        // Execute the query
        return await query.then((response): InitiativeDto[] => {
            if (response.error) {
                console.error('Error loading initiatives', response.error);
                throw new Error('Error loading initiatives');
            }

            // Rename task to tasks and preserve the data
            response.data = response.data.map((initiative: any) => {
                return {
                    ...initiative,
                    tasks: initiative.task || [],
                    task: undefined
                }
            });

            const parsedData = InitiativeDtoSchema.array().safeParse(response.data);
            if (!parsedData.success) {
                console.error(
                    'Error loading initiatives - data format',
                    parsedData.error,
                );
                throw new Error(`Error loading initiatives:`);
            }

            return parsedData.data.map(initiative =>
                initiativeFromData(initiative),
            );
        });
    })
}

/**
 * Creates a new initiative using the FastAPI endpoint.
 * @param {Partial<InitiativeDto>} initiative - The initiative data to create
 * @returns {Promise<InitiativeDto>} The created initiative
 */
export async function createInitiative(initiative: Partial<InitiativeDto>): Promise<InitiativeDto> {
    // Get the current workspace
    const currentWorkspace = await fetchCurrentWorkspace();

    // Validate title length
    if (initiative.title && initiative.title.length > 200) {
        throw new Error('Title must be 200 characters or less');
    }

    const requestPayload = {
        title: initiative.title,
        description: initiative.description || '',
        status: initiative.status || 'TO_DO',
        type: initiative.type || null,
        workspace_id: currentWorkspace.id,
    };

    return withApiCall(async () => {
        const response = await fetch('/api/initiatives', {
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

        const createdInitiativeData = await response.json();
        const createdInitiative = initiativeFromData(createdInitiativeData);

        // Create tasks if provided
        const tasksWithInitiativeId = initiative.tasks?.map(tasks => {
            return {
                ...tasks,
                initiative_id: createdInitiative.id
            }
        });

        if (tasksWithInitiativeId && tasksWithInitiativeId.length > 0) {
            // TODO - creating tasks in parallel will create them out of order
            const receivedTasks = await Promise.all(tasksWithInitiativeId.map(task => createTask(task)));
            return {
                ...createdInitiative,
                tasks: receivedTasks
            };
        } else {
            return createdInitiative
        }
    })
}


export async function postInitiative(initiative: Partial<InitiativeDto>): Promise<InitiativeDto> {
    // Get the current workspace
    const currentWorkspace = await fetchCurrentWorkspace();

    // Validate title length
    if (initiative.title && initiative.title.length > 200) {
        throw new Error('Title must be 200 characters or less');
    }

    const jsonPayload = {
        ...initiativeToPayloadJSON(initiative),
        workspace_id: currentWorkspace.id
    };

    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('initiative')
            .update(jsonPayload)
            .eq('id', initiative.id)
            .select('*, orderings(*)')
            .then(response => {
            if (response.error) {
                console.error('Error posting initiative', response);
                throw new Error(response.error.message);
            }

            return response.data as Partial<InitiativeDto>[];
        });


        // Check that we have a response and that it's not an empty array
        if (!response || response.length === 0) {
            throw new Error('No initiative created');
        }

        const createdInitiative = initiativeFromData(response[0]);

        const tasksWithInitiativeId = initiative.tasks?.map(tasks => {
            return {
                ...tasks,
                initiative_id: createdInitiative.id
            }
        });

        if (tasksWithInitiativeId && tasksWithInitiativeId.length > 0) {
            const receivedTasks = await Promise.all(tasksWithInitiativeId.map(task => task.id ? postTask(task) : createTask(task)));
            return {
                ...createdInitiative,
                task: receivedTasks
            };
        } else {
            return createdInitiative
        }
    })
}

/**
 * Deletes an initiative using the FastAPI endpoint.
 * @param {string} initiativeId - The ID of the initiative to delete
 * @returns {Promise<void>} 
 */
export async function deleteInitiative(initiativeId: string): Promise<void> {
    return withApiCall(async () => {
        const response = await fetch(`/api/initiatives/${initiativeId}`, {
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

export async function getInitiativeById(id: string): Promise<InitiativeDto> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(
        async () => {
            return await getPostgrestClient()
                .from('initiative')
                .select(
                    `
                        *,
                        task(*, checklist(*), orderings(*)),
                        orderings(*)
                    `
                )
                .eq('workspace_id', currentWorkspace.id)
                .eq('id', id).then(response => {
                    if (response.error) {
                        console.error('Error loading initiative', response.error);
                        throw new Error('Error loading initiative');
                    }

                    if (response.data.length === 0) {
                        throw new Error('Initiative not found');
                    }

                    if (response.data.length > 1) {
                        console.error('Error loading initiative - multiple initiatives found');
                        throw new Error('Error loading initiative');
                    }

                    // Rename task to tasks and preserve the data
                    const initiative = response.data[0];
                    initiative.tasks = initiative.task || [];
                    initiative.task = undefined;

                    const parsedData = InitiativeDtoSchema.safeParse(response.data[0]);
                    if (!parsedData.success) {
                        console.error('Error loading initiative - data format', parsedData.error);
                        throw new Error(`Error loading initiative`);
                    }

                    return initiativeFromData(parsedData.data);
                });
        })
}

/**
 * Moves an initiative to a new position in the same status list.
 * @param {string} initiativeId - The ID of the initiative to move
 * @param {string} [afterId] - ID of initiative to move after (optional)
 * @param {string} [beforeId] - ID of initiative to move before (optional)
 * @returns {Promise<InitiativeDto>} The updated initiative
 */
export async function moveInitiative(
    initiativeId: string,
    afterId: string | null,
    beforeId: string | null
): Promise<InitiativeDto> {
    const requestPayload = {
        after_id: afterId || null,
        before_id: beforeId || null
    };

    return withApiCall(async () => {
        const response = await fetch(`/api/initiatives/${initiativeId}/move`, {
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

        const updatedInitiativeData = await response.json();
        return initiativeFromData(updatedInitiativeData);
    });
}

/**
 * Moves an initiative to a different status list.
 * @param {string} initiativeId - The ID of the initiative to move
 * @param {string} newStatus - The new status to move the initiative to
 * @param {string} [afterId] - ID of initiative to move after (optional)
 * @param {string} [beforeId] - ID of initiative to move before (optional)
 * @returns {Promise<InitiativeDto>} The updated initiative
 */
export async function moveInitiativeToStatus(
    initiativeId: string,
    newStatus: string,
    afterId: string | null,
    beforeId: string | null
): Promise<InitiativeDto> {
    const requestPayload = {
        new_status: newStatus,
        after_id: afterId || null,
        before_id: beforeId || null
    };

    return withApiCall(async () => {
        const response = await fetch(`/api/initiatives/${initiativeId}/status`, {
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

        const updatedInitiativeData = await response.json();
        
        return initiativeFromData(updatedInitiativeData);
    });
}

/**
 * Adds an initiative to a group.
 * @param {string} initiativeId - The ID of the initiative to add to group
 * @param {string} groupId - The ID of the group to add the initiative to
 * @param {string} [afterId] - ID of initiative to move after within the group (optional)
 * @param {string} [beforeId] - ID of initiative to move before within the group (optional)
 * @returns {Promise<InitiativeDto>} The updated initiative
 */
export async function addInitiativeToGroup(
    initiativeId: string,
    groupId: string,
    afterId: string | null,
    beforeId: string | null
): Promise<InitiativeDto> {
    const requestPayload = {
        group_id: groupId,
        after_id: afterId || null,
        before_id: beforeId || null
    };

    return withApiCall(async () => {
        const response = await fetch(`/api/initiatives/${initiativeId}/groups`, {
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

        const updatedInitiativeData = await response.json();
        return initiativeFromData(updatedInitiativeData);
    });
}


/**
    * Removes an initiative from a group.
    * @param {string} initiativeId - The ID of the initiative to remove from group
    * @param {string} groupId - The ID of the group to remove the initiative from
    * @returns {Promise<{message: string}>} Success or error message
    */
export async function removeInitiativeFromGroup(
    initiativeId: string,
    groupId: string
): Promise<{ message: string }> {
    return withApiCall(async () => {
        const response = await fetch(`/api/initiatives/${initiativeId}/groups/${groupId}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${loadAndValidateJWT()}`
            }
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    });
}


/**
 * Moves an initiative in a groupd.
 * @param {string} initiativeId - The ID of the initiative to move
 * @param {string} groupId - ID of the group
 * @param {string} [afterId] - ID of initiative to move after (optional)
 * @param {string} [beforeId] - ID of initiative to move before (optional)
 * @returns {Promise<InitiativeDto>} The updated initiative
 */
export async function moveInitiativeInGroup(
    initiativeId: string,
    groupId: string,
    afterId: string | null,
    beforeId: string | null
): Promise<InitiativeDto> {
    const requestPayload = {
        after_id: afterId || null,
        before_id: beforeId || null
    };

    return withApiCall(async () => {
        const response = await fetch(`/api/initiatives/${initiativeId}/groups/${groupId}/move`, {
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

        const updatedInitiativeData = await response.json();
        
        return initiativeFromData(updatedInitiativeData);
    });
}