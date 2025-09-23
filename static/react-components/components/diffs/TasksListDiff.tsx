import React, { useMemo } from 'react';

import ListDiffPresentation from './ListDiffPresentation';
import { useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { buildBasePath } from '#hooks/diffs/basePath';


export default function TasksListDiff({ selectedInitiativeId }: { selectedInitiativeId: string }) {
    const { initiativesData } = useInitiativesContext();
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

    const initiative = useMemo(
        () => (initiativesData || []).find(i => i.id === selectedInitiativeId) || null,
        [initiativesData, selectedInitiativeId]
    );

    const taskEntitySuggestions = useMemo(
        () => entitySuggestions.filter(s => s.path.startsWith(`initiative.${initiative?.identifier}.tasks`)),
        [entitySuggestions, initiative]
    );

    const basePath = buildBasePath(initiative?.identifier || '');

    return (
        <ListDiffPresentation
            entityType="task"
            suggestions={taskEntitySuggestions}
            resolutions={resolutions}
            allResolved={allResolved}
            resolve={resolve}
            rollback={rollback}
            acceptAll={() => acceptAll(basePath)}
            rejectAll={() => rejectAll(basePath)}
            rollbackAll={() => rollbackAll(basePath)}
            getResolutionState={getResolutionState}
            saveSuggestions={saveSuggestions}
            error={null}
        />
    );
}
