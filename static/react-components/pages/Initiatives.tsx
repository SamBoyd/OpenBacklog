import React, { useState, useCallback, useEffect } from 'react';

import CompactCreateInitiative from '#components/CompactCreateInitiative';
import InitiativesKanbanBoard from '#components/InitiativesKanbanBoard';
import InitiativesTopBar from '#components/InitiativesTopBar';
import InitiativesList from '#components/InitiativesList';
import { useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext';
import InitiativesListDiff from '#components/diffs/InitiativesListDiff';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import ThemeSidebar from '#components/ThemeSidebar';

import { useUserPreferences } from '#hooks/useUserPreferences';

import { InitiativeStatus } from '#types';

/**
 * Container component for the Initiatives page
 * 
 * @returns A React component
 */
const Initiatives = () => {
    const { suggestions } = useSuggestionsToBeResolved();
    const { initiativesData } = useInitiativesContext();
    const { preferences, updateSelectedInitiativeStatuses, updateInitiativesShowListView } = useUserPreferences();

    const showListView = preferences.initiativesShowListView;
    const [initiativeReloadCounter, setInitiativeReloadCounter] = useState(0);
    const [focusCompactCreateInitiative, setFocusCompactCreateInitiative] = useState(false);

    // State for filter visibility
    const [isFilterOpen, setIsFilterOpen] = useState(false);

    const setExpandCompactCreateInitiative = () => {
        setFocusCompactCreateInitiative(true);
        setTimeout(() => {
            setFocusCompactCreateInitiative(false);
        }, 1000);
    }

    // Toggle filter visibility
    const toggleFilter = useCallback(() => {
        setIsFilterOpen(prev => !prev);
    }, []);

    // Handle status toggle in the filter component
    const handleStatusToggle = useCallback((status: InitiativeStatus) => {
        const prevSelectedStatus = preferences.selectedInitiativeStatuses.includes(status);
        const newSelectedStatuses = prevSelectedStatus
            ? preferences.selectedInitiativeStatuses.filter(s => s !== status)
            : [...preferences.selectedInitiativeStatuses, status];
        updateSelectedInitiativeStatuses(newSelectedStatuses);
    }, [preferences, updateSelectedInitiativeStatuses]);

    // Function to close the filter
    const closeFilter = useCallback(() => {
        setIsFilterOpen(false);
    }, []);

    // Toggle view between list and kanban
    const toggleView = useCallback(() => {
        updateInitiativesShowListView(!showListView);
    }, [showListView, updateInitiativesShowListView]);

    const onCreateInitiative = useCallback(() => {
    }, []);

    return (
        <div className="">
            <ThemeSidebar />
            
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
                        isFilterOpen={isFilterOpen}
                        selectedStatuses={preferences.selectedInitiativeStatuses as InitiativeStatus[]}
                        availableStatuses={Object.values(InitiativeStatus)}
                        onToggleView={toggleView}
                        onToggleFilter={toggleFilter}
                        onStatusToggle={handleStatusToggle}
                        onCloseFilter={closeFilter}
                        onCreateInitiative={setExpandCompactCreateInitiative}
                        withBottomBorder={showListView}
                    />

                    {showListView ? (
                        <InitiativesList
                            selectedStatuses={preferences.selectedInitiativeStatuses as InitiativeStatus[]}
                        />
                    ) : (
                        <InitiativesKanbanBoard
                            reloadCounter={initiativeReloadCounter}
                            selectedStatuses={preferences.selectedInitiativeStatuses as InitiativeStatus[]}
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
        </div>
    )
}

export default Initiatives;
