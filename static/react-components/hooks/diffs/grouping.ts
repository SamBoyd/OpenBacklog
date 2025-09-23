/**
 * Interface representing a grouped set of suggestions for an initiative
 */
export interface InitiativeSuggestionGroup {
    entitySuggestion?: any;
    fieldSuggestions: Record<string, any>;
    taskSuggestions: Record<string, any>;
    identifier: string;
}

/**
 * Groups initiative suggestions by their identifier.
 * Separates entity, field, and task suggestions into organized groups.
 * 
 * @param suggestions - Array of suggestions with path properties
 * @returns Object mapping initiative identifiers to their grouped suggestions
 */
export function groupInitiativeSuggestionsByIdentifier(
    suggestions: Array<{ path: string; [key: string]: any }>
): Record<string, InitiativeSuggestionGroup> {
    const initiativeGroups: Record<string, InitiativeSuggestionGroup> = {};

    if (!suggestions || !Array.isArray(suggestions)) {
        return initiativeGroups;
    }

    suggestions.forEach((suggestion) => {
        const path = suggestion.path;
        if (!path.startsWith('initiative.')) {
            return; // Skip non-initiative suggestions
        }

        const pathParts = path.split('.');
        if (pathParts.length < 2 || !pathParts[1]) {
            return; // Skip invalid paths or empty identifiers
        }

        const identifier = pathParts[1];

        // Initialize group if it doesn't exist
        if (!initiativeGroups[identifier]) {
            initiativeGroups[identifier] = {
                fieldSuggestions: {},
                taskSuggestions: {},
                identifier
            };
        }

        const group = initiativeGroups[identifier];

        if (path.includes('.tasks.')) {
            // Task-related suggestions (entity or field level within tasks)
            const taskPathParts = path.split('.tasks.');
            if (taskPathParts.length > 1) {
                const taskPath = taskPathParts[1];
                group.taskSuggestions[taskPath] = suggestion;
            }
        } else if (suggestion.type === 'entity') {
            // Only assign entity suggestion if it's at the initiative level (not tasks)
            group.entitySuggestion = suggestion;
        } else if (suggestion.type === 'field' && suggestion.fieldName) {
            // Field suggestions at the initiative level
            group.fieldSuggestions[suggestion.fieldName] = suggestion;
        }
    });

    return initiativeGroups;
}

/**
 * Selects the entity suggestion for a specific base path from suggestions.
 * 
 * @param suggestions - Array of suggestions with path properties
 * @param basePath - The base path to search for (e.g., "initiative.INIT-123")
 * @returns The entity suggestion matching the base path, or undefined if not found
 */
export function selectEntitySuggestionForBasePath(
    suggestions: Array<{ path: string; [key: string]: any }>,
    basePath: string
): any | undefined {
    if (!basePath || !suggestions || !Array.isArray(suggestions)) {
        return undefined;
    }

    const suggestion = suggestions.find(s => s.path === basePath);
    return suggestion?.type === 'entity' ? suggestion : undefined;
}

/**
 * Checks if there are any task-related suggestions under a specific base path.
 * 
 * @param suggestions - Array of suggestions with path properties
 * @param basePath - The base path to check under (e.g., "initiative.INIT-123")
 * @returns True if task suggestions exist under the base path, false otherwise
 */
export function hasTaskSuggestionsUnderPath(
    suggestions: Array<{ path: string; [key: string]: any }>,
    basePath: string
): boolean {
    if (!basePath || !suggestions || !Array.isArray(suggestions)) {
        return false;
    }

    const taskPrefix = `${basePath}.tasks.`;
    
    return suggestions.some(s => 
        s.path.startsWith(taskPrefix)
    );
}

/**
 * Checks if there are any suggestions under a specific base path (including the path itself).
 * 
 * @param suggestions - Array of suggestions with path properties
 * @param basePath - The base path to check under (e.g., "initiative.INIT-123")
 * @returns True if any suggestions exist at or under the base path, false otherwise
 */
export function hasAnySuggestionsUnderPath(
    suggestions: Array<{ path: string; [key: string]: any }>,
    basePath: string
): boolean {
    if (!basePath || !suggestions || !Array.isArray(suggestions)) {
        return false;
    }

    return suggestions.some(s => 
        s.path === basePath || s.path.startsWith(`${basePath}.`)

    );
}