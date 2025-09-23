/**
 * Builds a base path for initiative suggestions using the identifier.
 * Used to construct paths for suggestion resolution and grouping.
 * 
 * @param initiative_identifier - The initiative identifier (e.g., "INIT-123")
 * @param task_identifier - The task identifier (e.g., "T-123")
 * @returns The base path for the initiative (e.g., "initiative.INIT-123")
 */
export function buildBasePath(initiative_identifier: string, task_identifier?: string): string {
    if (!initiative_identifier || typeof initiative_identifier !== 'string') {
        return '';
    }

    if (task_identifier === undefined) {
        return `initiative.${initiative_identifier}`;
    } else {
        return `initiative.${initiative_identifier}.tasks.${task_identifier}`;
    }
}