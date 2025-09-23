import {
    GroupDto,
    GroupDtoSchema,
    InitiativeDto,
    InitiativeDtoSchema,
    InitiativeGroupDto,
    InitiativeGroupDtoSchema,
    EntityType,
    ContextType,
} from '#types';
import { fetchCurrentWorkspace } from '#services/workspaceApi';
import { getPostgrestClient, withApiCall } from './api-utils';
import { any, z } from 'zod';
import { addInitiativeToGroup as addInitiativeToGroupApi, initiativeFromData, removeInitiativeFromGroup as apiRemoveInitiativeFromGroup} from './initiatives';

/**
 * Maps raw data to a GroupDto object.
 * @param {any} data - The raw data from the API.
 * @returns {GroupDto} The mapped GroupDto object.
 */
export function groupFromData(data: any): GroupDto {
    return {
        id: data.id,
        user_id: data.user_id,
        workspace_id: data.workspace_id,
        name: data.name,
        description: data.description,
        group_type: data.group_type,
        group_metadata: data.group_metadata,
        query_criteria: data.query_criteria,
        parent_group_id: data.parent_group_id,
        children: data.children,
        initiatives: data.initiatives ? data.initiatives.map((i: any) => initiativeFromData(i)) : [],
    }
}

/**
 * Converts a partial GroupDto object to a JSON payload for the API.
 * Excludes fields not needed for create/update operations.
 * @param {Partial<GroupDto>} data - The partial GroupDto object.
 * @returns {any} The JSON payload.
 */
export function groupToPayloadJSON(data: Partial<GroupDto>): any {
    // Exclude fields that shouldn't be sent in create/update payloads
    // like id (usually), created_at, updated_at, children, initiatives
    const payload: any = {
        user_id: data.user_id,
        workspace_id: data.workspace_id,
        name: data.name,
        description: data.description,
        group_type: data.group_type,
        group_metadata: data.group_metadata,
        query_criteria: data.query_criteria,
        parent_group_id: data.parent_group_id,
    };

    // Add id only if it exists (for updates)
    if (data.id) {
        payload.id = data.id;
    }

    return payload;
}

/**
 * Maps raw data to an InitiativeGroupDto object.
 * @param {any} data - The raw data from the API.
 * @returns {InitiativeGroupDto} The mapped InitiativeGroupDto object.
 */
export function initiativeGroupFromData(data: any): InitiativeGroupDto {
    const parsedData = InitiativeGroupDtoSchema.safeParse(data);
    if (!parsedData.success) {
        console.error(
            'Error validating initiative group data',
            parsedData.error,
            'Raw data:',
            data,
        );
        throw new Error(
            `Error validating initiative group data: ${parsedData.error}`,
        );
    }
    return parsedData.data;
}

/**
 * Fetches a group by its ID.
 * @param {string} id - The ID of the group.
 * @returns {Promise<GroupDto>} The group data.
 */
export async function getGroupById(id: string): Promise<GroupDto> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('group')
            .select(`
                *,
                initiative_group(
                    *,
                    initiative(
                        *, tasks:task(*, checklist(*)), orderings(*)
                    )
                )
            `)
            .eq('workspace_id', currentWorkspace.id)
            .eq('id', id)
            .maybeSingle();

        if (response.error) {
            console.error('Error loading group', response.error);
            throw new Error(`Error loading group: ${response.error.message}`);
        }

        if (!response.data) {
            throw new Error('Group not found');
        }

        const rawData = response.data;
        // Extract initiatives from initiative_group, sort by position, and map to InitiativeDto
        const initiatives = (rawData.initiative_group || [])
            .sort((a: any, b: any) => a.position - b.position)
            .map((ig: any) => ig.initiative as InitiativeDto); // Assuming ig.initiative is a full InitiativeDto based on the select query

        // Pass the transformed data (with an 'initiatives' array) to groupFromData
        return groupFromData({ ...rawData, initiatives });
    });
}

/**
 * Fetches all groups for the current workspace.
 * Includes nested children and associated initiatives.
 * @returns {Promise<GroupDto[]>} A list of groups.
 */
export async function getGroups(): Promise<GroupDto[]> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        const query = getPostgrestClient()
            .from('group')
            .select(`
                *,
                initiative_group(
                    *,
                    initiative(
                        *, tasks:task(*, checklist(*)), orderings(*)
                    )
                )
            `)
            .eq('workspace_id', currentWorkspace.id)
            .is('parent_group_id', null)
    
        return await query.then((response: any): GroupDto[] => {
            if (response.error) {
                console.error('Error loading groups', response.error);
                throw new Error(`Error loading groups: ${response.error.message}`);
            }

            const transformedResponse = response.data.map((group: any) => {
                const initiatives: InitiativeDto[] = group.initiative_group.map((ig: any) => ig.initiative) || []
                return {
                    ...group,
                    initiatives: initiatives,
                    initiative_group: undefined
                }
            })

            const parsedData = GroupDtoSchema.array().safeParse(transformedResponse);
            if (!parsedData.success) {
                console.error(
                    'Error loading groups - data format',
                    parsedData.error,
                );
                throw new Error(`Error loading groups:`);
            }

            return parsedData.data.map(group => 
                groupFromData(group)
            )
        })
    });
}

/**
 * Creates or updates a group.
 * @param {Partial<GroupDto>} group - The group data. If ID is present, it updates; otherwise, it creates.
 * @param {Array<{id: string }>} initiatives - Optional array of initiatives to associate with this group
 * @returns {Promise<GroupDto>} The created or updated group data.
 */
export async function postGroup(
    group: Partial<GroupDto>,
): Promise<GroupDto> {
    const currentWorkspace = await fetchCurrentWorkspace();

    // Create a payload just for the group itself, without initiative_group
    const groupPayload = {
        ...groupToPayloadJSON(group), // Use the original function without initiatives
        workspace_id: currentWorkspace.id,
    };

    return withApiCall(async () => {
        // First, update or create the group
        const groupResponse = await getPostgrestClient()
            .from('group')
            .update(groupPayload)
            .eq('id', group.id)
            .select('*')
            .single();

        if (groupResponse.error) {
            console.error('Error posting group', groupResponse.error);
            throw new Error(`Error posting group: ${groupResponse.error.message}`);
        }

        if (!groupResponse.data) {
            throw new Error('No group created or updated');
        }

        const updatedGroupId = groupResponse.data.id;

        // Finally get the full group with relationships
        return getGroupById(updatedGroupId);
    });
}

/**
 * Deletes a group by its ID.
 * @param {string} id - The ID of the group to delete.
 * @returns {Promise<void>}
 */
export async function deleteGroup(id: string): Promise<void> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        const { error } = await getPostgrestClient()
            .from('group')
            .delete()
            .eq('id', id)
            .eq('workspace_id', currentWorkspace.id);

        if (error) {
            console.error('Error deleting group', error);
            throw new Error(`Error deleting group: ${error.message}`);
        }

        const { error: deleteOrderingError } = await getPostgrestClient()
            .from('orderings')
            .delete()
            .eq('context_type', ContextType.GROUP)
            .eq('context_id', id)
            .eq('entity_type', EntityType.INITIATIVE);
        
        if (deleteOrderingError) {
            console.error('Error deleting ordering', deleteOrderingError);
            throw new Error(`Error deleting ordering: ${deleteOrderingError.message}`);
        }
    });
}
