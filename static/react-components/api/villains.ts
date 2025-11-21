import { VillainDto, VillainDtoSchema } from '#types';
import { getPostgrestClient, withApiCall } from '#api/api-utils';
import { fetchCurrentWorkspace } from '#services/workspaceApi';

/**
 * Transforms raw API response data into a VillainDto.
 * @param {any} data - The raw API response data
 * @returns {VillainDto} The transformed villain object
 */
export function villainFromData(data: any): VillainDto {
    return {
        id: data.id,
        identifier: data.identifier,
        user_id: data.user_id,
        workspace_id: data.workspace_id,
        name: data.name,
        villain_type: data.villain_type,
        description: data.description,
        severity: data.severity,
        is_defeated: data.is_defeated,
        created_at: data.created_at,
        updated_at: data.updated_at,
    };
}

/**
 * Fetches all villains for a workspace.
 * @param {string} workspaceId - The workspace ID
 * @returns {Promise<VillainDto[]>} Array of villain objects
 */
export async function getAllVillains(workspaceId: string): Promise<VillainDto[]> {
    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('villains')
            .select('*')
            .eq('workspace_id', workspaceId);

        if (response.error) {
            console.error('Error loading villains', response.error);
            throw new Error('Error loading villains');
        }

        const parsedData = VillainDtoSchema.array().safeParse(response.data);
        if (!parsedData.success) {
            console.error('Error loading villains - data format', parsedData.error);
            throw new Error('Error loading villains');
        }

        return parsedData.data.map(villain => villainFromData(villain));
    });
}

/**
 * Fetches a single villain by ID.
 * @param {string} villainId - The villain ID
 * @returns {Promise<VillainDto>} The villain object
 */
export async function getVillainById(villainId: string): Promise<VillainDto> {
    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('villains')
            .select('*')
            .eq('id', villainId);

        if (response.error) {
            console.error('Error loading villain', response.error);
            throw new Error('Error loading villain');
        }

        if (response.data.length === 0) {
            throw new Error('Villain not found');
        }

        if (response.data.length > 1) {
            console.error('Error loading villain - multiple villains found');
            throw new Error('Error loading villain');
        }

        const parsedData = VillainDtoSchema.safeParse(response.data[0]);
        if (!parsedData.success) {
            console.error('Error loading villain - data format', parsedData.error);
            throw new Error('Error loading villain');
        }

        return villainFromData(parsedData.data);
    });
}

/**
 * Fetches a single villain by identifier (e.g., "V-2003").
 * @param {string} identifier - The villain identifier
 * @returns {Promise<VillainDto>} The villain object
 */
export async function getVillainByIdentifier(identifier: string): Promise<VillainDto> {
    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('villains')
            .select('*')
            .eq('identifier', identifier);

        if (response.error) {
            console.error('Error loading villain by identifier', response.error);
            throw new Error('Error loading villain');
        }

        if (response.data.length === 0) {
            throw new Error('Villain not found');
        }

        if (response.data.length > 1) {
            console.error('Error loading villain - multiple villains found with same identifier');
            throw new Error('Error loading villain');
        }

        const parsedData = VillainDtoSchema.safeParse(response.data[0]);
        if (!parsedData.success) {
            console.error('Error loading villain - data format', parsedData.error);
            throw new Error('Error loading villain');
        }

        return villainFromData(parsedData.data);
    });
}
