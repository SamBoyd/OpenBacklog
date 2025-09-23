import React from 'react';
import ListDiffPresentation from './ListDiffPresentation';
import { useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext';

/**
 * Component for displaying and managing initiative list differences using AI suggestions.
 * Refactored to use the SuggestionsToBeResolvedContext via the adapter hook pattern.
 */
export default function InitiativesListDiff() {
    const {
        entitySuggestions,
        resolutions,
        resolve,
        rollback,
        acceptAll,
        rejectAll,
        rollbackAll,
        allResolved,
        getResolutionState,
        saveSuggestions
    } = useSuggestionsToBeResolved();
    

    const initiativeEntitySuggestions = Object.values(entitySuggestions)
        .filter(suggestion => !suggestion.path.includes('tasks'));

    return (
        <ListDiffPresentation
            suggestions={initiativeEntitySuggestions}
            resolutions={resolutions}
            resolve={resolve}
            rollback={rollback}
            acceptAll={() => acceptAll()}
            rejectAll={() => rejectAll()}
            rollbackAll={() => rollbackAll()}
            getResolutionState={getResolutionState}
            allResolved={allResolved}
            saveSuggestions={saveSuggestions}
            // Legacy props
            entityType="initiative"
            error={null} 
        />
    );
}
