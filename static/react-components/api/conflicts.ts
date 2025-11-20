import { ConflictDto, ConflictDtoSchema, ConflictStatus } from '#types';
import { fetchCurrentWorkspace } from '#services/workspaceApi';
import { getPostgrestClient, withApiCall } from '#api/api-utils';

/**
 * Transform raw API data into ConflictDto.
 * @param {any} data - Raw data from API
 * @returns {ConflictDto} Transformed conflict data
 */
export function conflictFromData(data: any): ConflictDto {
    const response: Partial<ConflictDto> = {
        id: data.id,
        identifier: data.identifier,
        workspace_id: data.workspace_id,
        hero_id: data.hero_id,
        villain_id: data.villain_id,
        description: data.description,
        status: data.status,
        story_arc_id: data.story_arc_id,
        resolved_at: data.resolved_at,
        resolved_by_initiative_id: data.resolved_by_initiative_id,
        created_at: data.created_at,
        updated_at: data.updated_at,
    };

    // Include related entities if present
    if (data.hero) {
        response.hero = {
            id: data.hero.id,
            identifier: data.hero.identifier,
            workspace_id: data.hero.workspace_id,
            name: data.hero.name,
            description: data.hero.description,
            is_primary: data.hero.is_primary,
            created_at: data.hero.created_at,
            updated_at: data.hero.updated_at,
        };
    }

    if (data.villain) {
        response.villain = {
            id: data.villain.id,
            identifier: data.villain.identifier,
            user_id: data.villain.user_id,
            workspace_id: data.villain.workspace_id,
            name: data.villain.name,
            villain_type: data.villain.villain_type,
            description: data.villain.description,
            severity: data.villain.severity,
            is_defeated: data.villain.is_defeated,
            created_at: data.villain.created_at,
            updated_at: data.villain.updated_at,
        };
    }

    if (data.story_arc) {
        response.story_arc = {
            id: data.story_arc.id,
            identifier: data.story_arc.identifier,
            workspace_id: data.story_arc.workspace_id,
            title: data.story_arc.title,
            description: data.story_arc.description,
            created_at: data.story_arc.created_at,
            updated_at: data.story_arc.updated_at,
        };
    }

    if (data.resolved_by_initiative) {
        response.resolved_by_initiative = {
            id: data.resolved_by_initiative.id,
            identifier: data.resolved_by_initiative.identifier,
            title: data.resolved_by_initiative.title,
            description: data.resolved_by_initiative.description,
            status: data.resolved_by_initiative.status,
            created_at: data.resolved_by_initiative.created_at,
            updated_at: data.resolved_by_initiative.updated_at,
        };
    }

    return response as ConflictDto;
}

/**
 * Interface for conflict filter parameters.
 */
export interface ConflictFilters {
    status?: ConflictStatus | ConflictStatus[];
    heroId?: string;
    villainId?: string;
    storyArcId?: string;
}

/**
 * Fetch all conflicts for the current workspace with optional filtering.
 * @param {ConflictFilters} [filters] - Optional filters for status, hero, villain, or story arc
 * @returns {Promise<ConflictDto[]>} Array of conflicts
 */
export async function getAllConflicts(filters?: ConflictFilters): Promise<ConflictDto[]> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        // Start building the query with related entities
        let query = getPostgrestClient()
            .from('conflicts')
            .select(
                `
                *,
                hero:heroes!hero_id(*),
                villain:villains!villain_id(*),
                story_arc:roadmap_themes!story_arc_id(*),
                resolved_by_initiative:initiative!resolved_by_initiative_id(*)
            `
            )
            .eq('workspace_id', currentWorkspace.id);

        // Apply status filter if provided
        if (filters?.status) {
            if (Array.isArray(filters.status)) {
                query = query.in('status', filters.status);
            } else {
                query = query.eq('status', filters.status);
            }
        }

        // Apply hero filter if provided
        if (filters?.heroId) {
            query = query.eq('hero_id', filters.heroId);
        }

        // Apply villain filter if provided
        if (filters?.villainId) {
            query = query.eq('villain_id', filters.villainId);
        }

        // Apply story arc filter if provided
        if (filters?.storyArcId) {
            query = query.eq('story_arc_id', filters.storyArcId);
        }

        // Execute the query
        return await query.then((response): ConflictDto[] => {
            if (response.error) {
                console.error('Error loading conflicts', response.error);
                throw new Error('Error loading conflicts');
            }

            const parsedData = ConflictDtoSchema.array().safeParse(response.data);
            if (!parsedData.success) {
                console.error('Error loading conflicts - data format', parsedData.error);
                throw new Error('Error loading conflicts');
            }

            return parsedData.data.map((conflict) => conflictFromData(conflict));
        });
    });
}

/**
 * Fetch a single conflict by ID with related entities.
 * @param {string} conflictId - UUID of the conflict
 * @returns {Promise<ConflictDto>} The conflict data
 */
export async function getConflictById(conflictId: string): Promise<ConflictDto> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        return await getPostgrestClient()
            .from('conflicts')
            .select(
                `
                *,
                hero:heroes!hero_id(*),
                villain:villains!villain_id(*),
                story_arc:roadmap_themes!story_arc_id(*),
                resolved_by_initiative:initiative!resolved_by_initiative_id(*)
            `
            )
            .eq('id', conflictId)
            .eq('workspace_id', currentWorkspace.id)
            .then((response) => {
                if (response.error) {
                    console.error('Error loading conflict', response.error);
                    throw new Error('Error loading conflict');
                }

                if (response.data.length === 0) {
                    throw new Error('Conflict not found');
                }

                if (response.data.length > 1) {
                    console.error('Error loading conflict - multiple conflicts found');
                    throw new Error('Error loading conflict');
                }

                const parsedData = ConflictDtoSchema.safeParse(response.data[0]);
                if (!parsedData.success) {
                    console.error('Error loading conflict - data format', parsedData.error);
                    throw new Error('Error loading conflict');
                }

                return conflictFromData(parsedData.data);
            });
    });
}

/**
 * Fetch a single conflict by identifier with related entities.
 * @param {string} identifier - Human-readable identifier (e.g., "C-2003")
 * @returns {Promise<ConflictDto>} The conflict data
 */
export async function getConflictByIdentifier(identifier: string): Promise<ConflictDto> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        return await getPostgrestClient()
            .from('conflicts')
            .select(
                `
                *,
                hero:heroes!hero_id(*),
                villain:villains!villain_id(*),
                story_arc:roadmap_themes!story_arc_id(*),
                resolved_by_initiative:initiative!resolved_by_initiative_id(*)
            `
            )
            .eq('identifier', identifier)
            .eq('workspace_id', currentWorkspace.id)
            .then((response) => {
                if (response.error) {
                    console.error('Error loading conflict by identifier', response.error);
                    throw new Error('Error loading conflict');
                }

                if (response.data.length === 0) {
                    throw new Error('Conflict not found');
                }

                if (response.data.length > 1) {
                    console.error(
                        'Error loading conflict - multiple conflicts found with same identifier'
                    );
                    throw new Error('Error loading conflict');
                }

                const parsedData = ConflictDtoSchema.safeParse(response.data[0]);
                if (!parsedData.success) {
                    console.error('Error loading conflict - data format', parsedData.error);
                    throw new Error('Error loading conflict');
                }

                return conflictFromData(parsedData.data);
            });
    });
}
