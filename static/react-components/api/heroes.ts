import { HeroDto, HeroDtoSchema } from '#types';
import { withApiCall } from '#api/api-utils';
import { loadAndValidateJWT } from '#api/jwt';

/**
 * Transforms raw API response data into a HeroDto.
 * @param {any} data - The raw API response data
 * @returns {HeroDto} The transformed hero object
 */
export function heroFromData(data: any): HeroDto {
    return {
        id: data.id,
        identifier: data.identifier,
        workspace_id: data.workspace_id,
        name: data.name,
        description: data.description,
        is_primary: data.is_primary,
        created_at: data.created_at,
        updated_at: data.updated_at,
    };
}

/**
 * Fetches all heroes for a workspace.
 * @param {string} workspaceId - The workspace ID
 * @returns {Promise<HeroDto[]>} Array of hero objects
 */
export async function getAllHeroes(workspaceId: string): Promise<HeroDto[]> {
    return withApiCall(async () => {
        const response = await fetch(`/api/workspaces/${workspaceId}/heroes`, {
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
        const parsedData = HeroDtoSchema.array().safeParse(data);
        if (!parsedData.success) {
            console.error('Error loading heroes - data format', parsedData.error);
            throw new Error('Error loading heroes');
        }

        return parsedData.data.map(hero => heroFromData(hero));
    });
}

/**
 * Fetches a single hero by ID.
 * @param {string} heroId - The hero ID
 * @returns {Promise<HeroDto>} The hero object
 */
export async function getHeroById(heroId: string): Promise<HeroDto> {
    return withApiCall(async () => {
        const response = await fetch(`/api/heroes/${heroId}`, {
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
        const parsedData = HeroDtoSchema.safeParse(data);
        if (!parsedData.success) {
            console.error('Error loading hero - data format', parsedData.error);
            throw new Error('Error loading hero');
        }

        return heroFromData(parsedData.data);
    });
}

/**
 * Fetches a single hero by identifier (e.g., "H-2003").
 * @param {string} identifier - The hero identifier
 * @returns {Promise<HeroDto>} The hero object
 */
export async function getHeroByIdentifier(identifier: string): Promise<HeroDto> {
    return withApiCall(async () => {
        const response = await fetch(`/api/heroes/identifier/${identifier}`, {
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
        const parsedData = HeroDtoSchema.safeParse(data);
        if (!parsedData.success) {
            console.error('Error loading hero - data format', parsedData.error);
            throw new Error('Error loading hero');
        }

        return heroFromData(parsedData.data);
    });
}
