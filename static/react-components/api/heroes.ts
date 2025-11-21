import { HeroDto, HeroDtoSchema } from '#types';
import { getPostgrestClient, withApiCall } from '#api/api-utils';
import { fetchCurrentWorkspace } from '#services/workspaceApi';

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
        const response = await getPostgrestClient()
            .from('heroes')
            .select('*')
            .eq('workspace_id', workspaceId);

        if (response.error) {
            console.error('Error loading heroes', response.error);
            throw new Error('Error loading heroes');
        }

        const parsedData = HeroDtoSchema.array().safeParse(response.data);
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
        const response = await getPostgrestClient()
            .from('heroes')
            .select('*')
            .eq('id', heroId);

        if (response.error) {
            console.error('Error loading hero', response.error);
            throw new Error('Error loading hero');
        }

        if (response.data.length === 0) {
            throw new Error('Hero not found');
        }

        if (response.data.length > 1) {
            console.error('Error loading hero - multiple heroes found');
            throw new Error('Error loading hero');
        }

        const parsedData = HeroDtoSchema.safeParse(response.data[0]);
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
        const response = await getPostgrestClient()
            .from('heroes')
            .select('*')
            .eq('identifier', identifier);

        if (response.error) {
            console.error('Error loading hero by identifier', response.error);
            throw new Error('Error loading hero');
        }

        if (response.data.length === 0) {
            throw new Error('Hero not found');
        }

        if (response.data.length > 1) {
            console.error('Error loading hero - multiple heroes found with same identifier');
            throw new Error('Error loading hero');
        }

        const parsedData = HeroDtoSchema.safeParse(response.data[0]);
        if (!parsedData.success) {
            console.error('Error loading hero - data format', parsedData.error);
            throw new Error('Error loading hero');
        }

        return heroFromData(parsedData.data);
    });
}
