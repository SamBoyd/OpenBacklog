import React, { useState, useCallback, useEffect } from 'react';

import CompactCreateInitiative from '#components/CompactCreateInitiative';
import InitiativesKanbanBoard from '#components/InitiativesKanbanBoard';
import InitiativesTopBar from '#components/InitiativesTopBar';
import InitiativesList from '#components/InitiativesList';
import { useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext';
import InitiativesListDiff from '#components/diffs/InitiativesListDiff';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useUserPreferences } from '#hooks/useUserPreferences';
import { useInitiativeIdsByTheme } from '#hooks/useInitiativeIdsByTheme';
import { useThemePrioritization } from '#hooks/useThemePrioritization';

import { InitiativeStatus } from '#types';

/**
 * Container component for the Initiatives page
 *
 * @returns A React component
 */
const Initiatives = () => {
    const { suggestions } = useSuggestionsToBeResolved();
    const { currentWorkspace } = useWorkspaces();
    const { preferences, updateSelectedInitiativeStatuses, updateSelectedThemes, updateInitiativesShowListView } = useUserPreferences();

    // Fetch theme data
    const {
        prioritizedThemes,
        unprioritizedThemes,
    } = useThemePrioritization(currentWorkspace?.id || '');

    // Derive initiative IDs based on selected themes
    const initiativeIds = useInitiativeIdsByTheme(
        currentWorkspace?.id || '',
        preferences.selectedThemeIds
    );

    // Pass IDs to context via filters
    const filters = {
        ids: initiativeIds.length > 0 ? initiativeIds : undefined,
    };

    const { initiativesData } = useInitiativesContext(filters);

    const showListView = preferences.initiativesShowListView;
    const [initiativeReloadCounter, setInitiativeReloadCounter] = useState(0);
    const [focusCompactCreateInitiative, setFocusCompactCreateInitiative] = useState(false);

    const setExpandCompactCreateInitiative = () => {
        setFocusCompactCreateInitiative(true);
        setTimeout(() => {
            setFocusCompactCreateInitiative(false);
        }, 1000);
    }

    // Handle status toggle in the filter component
    const handleStatusToggle = useCallback((status: InitiativeStatus) => {
        const prevSelectedStatus = preferences.selectedInitiativeStatuses.includes(status);
        const newSelectedStatuses = prevSelectedStatus
            ? preferences.selectedInitiativeStatuses.filter(s => s !== status)
            : [...preferences.selectedInitiativeStatuses, status];
        updateSelectedInitiativeStatuses(newSelectedStatuses);
    }, [preferences, updateSelectedInitiativeStatuses]);

    // Handle theme toggle in the filter component
    const handleThemeToggle = useCallback((themeId: string) => {
        const isSelected = preferences.selectedThemeIds.includes(themeId);

        if (isSelected) {
            // Deselect
            const newSelection = preferences.selectedThemeIds.filter(id => id !== themeId);
            updateSelectedThemes(newSelection.length > 0 ? newSelection : ['all-prioritized-themes']);
        } else {
            // Select - remove special values when selecting specific theme
            const filteredSelection = preferences.selectedThemeIds.filter(
                id => id !== 'all-prioritized-themes' && id !== 'unthemed'
            );
            updateSelectedThemes([...filteredSelection, themeId]);
        }
    }, [preferences.selectedThemeIds, updateSelectedThemes]);

    // Toggle view between list and kanban
    const toggleView = useCallback(() => {
        updateInitiativesShowListView(!showListView);
    }, [showListView, updateInitiativesShowListView]);

    const onCreateInitiative = useCallback(() => {
    }, []);

    return (
        <div className="flex flex-col justify-between gap-2 pt-10">
            <div className="flex flex-col h-full justify-start px-5">

                {
                    suggestions.length > 0 && (
                        <InitiativesListDiff />
                    )
                }

                {/* Top bar */}
                <InitiativesTopBar
                    showListView={showListView}
                    selectedStatuses={preferences.selectedInitiativeStatuses as InitiativeStatus[]}
                    availableStatuses={Object.values(InitiativeStatus)}
                    prioritizedThemes={prioritizedThemes}
                    unprioritizedThemes={unprioritizedThemes}
                    selectedThemeIds={preferences.selectedThemeIds}
                    onToggleView={toggleView}
                    onStatusToggle={handleStatusToggle}
                    onThemeToggle={handleThemeToggle}
                    onCreateInitiative={setExpandCompactCreateInitiative}
                    withBottomBorder={showListView}
                />

                    {showListView ? (
                        <InitiativesList
                            selectedStatuses={preferences.selectedInitiativeStatuses as InitiativeStatus[]}
                            data={initiativesData}
                        />
                    ) : (
                        <InitiativesKanbanBoard
                            reloadCounter={initiativeReloadCounter}
                            selectedStatuses={preferences.selectedInitiativeStatuses as InitiativeStatus[]}
                            data={initiativesData}
                        />
                    )}

                    {initiativesData?.length === 0 ? (
                        <div className="bg-card text-foreground rounded opacity-15 h-52 flex items-center justify-center">
                            <span>Create your first initiative.</span>
                        </div>
                    ) : null}

                <CompactCreateInitiative
                    focus={focusCompactCreateInitiative}
                    onCreate={onCreateInitiative}
                    startExpanded={initiativesData?.length === 0}
                />
            </div>
        </div>
    )
}

export default Initiatives;
