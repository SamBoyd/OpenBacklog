import { VillainDto, VillainDtoSchema } from '#types';
import { withApiCall } from '#api/api-utils';
import { loadAndValidateJWT } from '#api/jwt';

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
        const response = await fetch(`/api/workspaces/${workspaceId}/villains`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${loadAndValidateJWT()}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Validate response data
        const parsedData = VillainDtoSchema.array().safeParse(data);
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
        const response = await fetch(`/api/villains/${villainId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${loadAndValidateJWT()}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Validate response data
        const parsedData = VillainDtoSchema.safeParse(data);
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
        const response = await fetch(`/api/villains/identifier/${identifier}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${loadAndValidateJWT()}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Validate response data
        const parsedData = VillainDtoSchema.safeParse(data);
        if (!parsedData.success) {
            console.error('Error loading villain - data format', parsedData.error);
            throw new Error('Error loading villain');
        }

        return villainFromData(parsedData.data);
    });
}
