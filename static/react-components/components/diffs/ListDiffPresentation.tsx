import React, { useMemo, useState } from 'react';

import ErrorToast from '#components/reusable/ErrorToast';
import { ResolveAllButtons } from '#components/diffs/reusable/ActionButtons';
import { ListItem } from '#components/diffs/ListDiffListItem';
import { ResolutionMap, ResolutionState, UnifiedSuggestion } from '#contexts/SuggestionsToBeResolvedContext';

export interface ListDiffPresentationProps {
    entityType: 'initiative' | 'task';
    error: string | null;

    /** Whether suggestions are currently being saved */
    isSaving: boolean;

    /** All suggestions as array */
    suggestions: UnifiedSuggestion[];
    /** Resolution state map */
    resolutions: ResolutionMap;
    /** Whether all suggestions are resolved */
    allResolved: boolean;

    /** Core operations */
    resolve: (path: string, accepted: boolean, value?: any) => void;
    rollback: (path: string) => void;
    acceptAll: (pathPrefix?: string) => void;
    rejectAll: (pathPrefix?: string) => void;
    rollbackAll: (pathPrefix?: string) => void;

    /** Utilities */
    getResolutionState: (path: string) => ResolutionState;
    saveSuggestions: () => Promise<void>;
}

const ListDiffPresentation = ({
    entityType,
    suggestions,
    resolutions,
    allResolved,
    resolve,
    rollback,
    acceptAll,
    rejectAll,
    rollbackAll,
    getResolutionState,
    saveSuggestions,
    isSaving,
    // Legacy props
    error,
}: ListDiffPresentationProps) => {
    const [dots, setDots] = useState('...');
    const entityTypeCapitalized = entityType.charAt(0).toUpperCase() + entityType.slice(1);

    const entitySuggestions = useMemo(() => {
        return suggestions.filter(suggestion => suggestion.type === 'entity');
    }, [suggestions, entityType]);

    const hasSuggestions = entitySuggestions.length > 0;

    const hasAnyResolution = useMemo(() => {
        return Object.values(resolutions).some(resolution => resolution.isResolved);
    }, [resolutions]);

    return (
        <div className="flex flex-col gap-4">
            {hasSuggestions && (
                <div className="relative flex flex-wrap justify-between items-center gap-2 mb-4 border-b border-border pb-4">
                    <h2 className="font-semibold text-foreground text-base">{entityTypeCapitalized} Suggestions</h2>
                    <div className="flex flex-wrap space-x-2 gap-y-2">
                        <ResolveAllButtons
                            loading={isSaving}
                            hasAnyResolution={hasAnyResolution}
                            allSuggestionsResolved={allResolved}
                            acceptAllSuggestions={acceptAll}
                            rejectAllSuggestions={rejectAll}
                            rollbackAllSuggestions={rollbackAll}
                            onSaveChanges={saveSuggestions}
                        />
                    </div>
                </div>
            )}

            <div className="flex flex-col gap-4">
                <div className="w-full">
                    <nav
                        aria-label={`Suggested ${entityTypeCapitalized}s`}
                        className="h-full"
                        data-testid="suggestions-list-nav"
                    >
                        <ul
                            role="list"
                            className=""
                            data-testid="suggestions-list"
                        >
                            {entitySuggestions
                                .map((suggestion, index) => (
                                    <ListItem
                                        key={index}
                                        suggestion={suggestion}
                                        accept={() => resolve(suggestion.path, true)}
                                        reject={() => resolve(suggestion.path, false)}
                                        rollback={() => rollback(suggestion.path)}
                                        resolution={getResolutionState(suggestion.path)}
                                        entityType={entityType}
                                    />
                                ))}
                        </ul>
                    </nav>
                </div>
            </div>

            <ErrorToast error={error} />
        </div>
    );
};

export default ListDiffPresentation; 