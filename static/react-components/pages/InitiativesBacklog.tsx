import React, { useState, useCallback } from 'react';

import CompactCreateInitiative from '#components/CompactCreateInitiative';
import InitiativesTopBar from '#components/InitiativesTopBar';
import { InitiativeStatus, GroupDto, GroupType } from '#types';
import InitiativesList from '#components/InitiativesList';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';
import InitiativesListDiff from '#components/diffs/InitiativesListDiff';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import GroupsSelectionHeader from '#components/groups/GroupsSelectionHeader';
import GroupInitiativesDisplay from '#components/GroupInitiativesDisplay';
import { Skeleton } from '#components/reusable/Skeleton';
import { useUserPreferences } from '#hooks/useUserPreferences';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';

// Define the default "All" group - must match the one in GroupsSelectionHeader
const defaultGroupAll: GroupDto = {
    id: 'all-pseudo-group',
    name: 'All',
    user_id: '',
    workspace_id: '',
    description: null,
    group_type: GroupType.SMART,
    group_metadata: null,
    query_criteria: null,
    parent_group_id: null
};

/**
 * Container component for the Initiatives page
 * 
 * @returns A React component
 */
const InitiativesBacklog = () => {
    const { initiativeImprovements } = useAiImprovementsContext();
    const { initiativesData, updateInitiative, shouldShowSkeleton } = useInitiativesContext()

    const { allGroupsInWorkspace } = useInitiativeGroups()
    const { preferences } = useUserPreferences()

    const isAllGroupSelected = preferences.selectedGroupIds.some(gId => gId === defaultGroupAll.id);
    const specificGroupsToDisplay = allGroupsInWorkspace.filter(
        group => preferences.selectedGroupIds.includes(group.id)
    ).filter(
        g => g.id !== defaultGroupAll.id
    );

    const [focusCompactCreateInitiative, setFocusCompactCreateInitiative] = useState(false);

    const backlogInitiatives = initiativesData?.filter((i: any) => i.status === InitiativeStatus.BACKLOG)
    const countBacklogInitiatives = backlogInitiatives?.filter((i: any) => i.status === InitiativeStatus.BACKLOG).length


    const setExpandCompactCreateInitiative = () => {
        setFocusCompactCreateInitiative(true);
        setTimeout(() => {
            setFocusCompactCreateInitiative(false);
        }, 1000);
    }

    const moveToStatus = (initiativeId: string) => (status: InitiativeStatus) => (event: React.MouseEvent<HTMLDivElement>) => {
        event.preventDefault();
        event.stopPropagation();

        console.log(`Moving initiative ${initiativeId} to status ${status}`);

        const initiative = initiativesData?.find((i: any) => i.id === initiativeId);
        if (!initiative) return;

        const updatedInitiative = { ...initiative, status };
        updateInitiative(updatedInitiative);

    }

    return (
        <div className="flex flex-col justify-between gap-2 pt-10">
            <div className="flex flex-col h-full justify-start px-5">
                {Object.keys(initiativeImprovements).length > 0 && (
                    <InitiativesListDiff />
                )}

                {/* Top bar */}
                <InitiativesTopBar
                    showListView={true}
                    showToggleView={false}
                    showFilterView={false}
                    isFilterOpen={false}
                    selectedStatuses={[InitiativeStatus.BACKLOG]}
                    availableStatuses={Object.values(InitiativeStatus)}
                    onToggleView={() => { }}
                    onToggleFilter={() => { }}
                    onStatusToggle={() => { }}
                    onCloseFilter={() => { }}
                    onCreateInitiative={setExpandCompactCreateInitiative}
                    withBottomBorder={true}
                />

                <div className="relative">
                    <GroupsSelectionHeader />
                </div>

                {/* Display initiatives for each selected group */}
                {!shouldShowSkeleton && specificGroupsToDisplay.map((group, index) => (
                    <div key={group.id} className="mt-2">
                        <GroupInitiativesDisplay
                            group={group}
                            allInitiatives={backlogInitiatives || []}
                            selectedStatuses={[InitiativeStatus.BACKLOG]}
                        />
                    </div>
                ))}

                {/* Display main InitiativesList if "All" is selected */}
                {!shouldShowSkeleton && isAllGroupSelected && countBacklogInitiatives && countBacklogInitiatives > 0 && (
                    <div className="mt-2 mb-4">
                        <InitiativesList
                            selectedStatuses={[InitiativeStatus.BACKLOG]}
                            moveToStatus={moveToStatus}
                        />
                    </div>
                )}

                {shouldShowSkeleton && (
                    <>
                        <div className="mt-6P bg-transparent">
                            <Skeleton type="text" width="w-24" height="h-5" />
                            <Skeleton type="text" width="w-96" height="h-5" />
                        </div>
                        <div className="mt-6 bg-transparent">
                            <Skeleton type="text" width="w-24" height="h-5" />
                            <Skeleton type="text" width="w-96" height="h-5" />
                        </div>
                        <div className="mt-6 mb-4 bg-transparent">
                            <Skeleton type="text" width="w-24" height="h-5" />
                            <Skeleton type="text" width="w-96" height="h-5" />
                        </div>
                    </>
                )}

                {!shouldShowSkeleton && countBacklogInitiatives === 0 ? (
                    <div className="bg-card text-foreground rounded opacity-15 h-52 flex items-center justify-center">
                        <span>You dont have any initiatives in your backlog.</span>
                    </div>
                ) : null}

                <CompactCreateInitiative
                    focus={focusCompactCreateInitiative}
                    startExpanded={backlogInitiatives?.length === 0}
                    defaultInitiativeStatus={InitiativeStatus.BACKLOG}
                />
            </div>

        </div>
    )
}

export default InitiativesBacklog;
