import React, { useCallback, useEffect, useState } from 'react';
import { MdOutlineViewKanban, MdViewHeadline } from 'react-icons/md';
import { GrDocumentText } from 'react-icons/gr';

import { InitiativeDto, TaskStatus, InitiativeStatus, statusDisplay, EntityType } from '#types';

import { useActiveEntity } from '#hooks/useActiveEntity'
import { useParams } from '#hooks/useParams';

import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useUserPreferences } from '#hooks/useUserPreferences';

import TasksKanbanBoard from '#components/TasksKanbanBoard';
import CompactCreateTask from '#components/CompactCreateTask';
import ItemView from '#components/reusable/ItemView';
import EntityDetailsEditor from '#components/reusable/EntityDetailsEditor';
import DescriptionSection from '#components/DescriptionSection';
import TasksList from '#components/TasksList';
import { Button } from '#components/reusable/Button';
import TitleInput from '#components/reusable/TitleInput';
import StatusFilter from './StatusFilter';

/**
 * ViewInitiative component for displaying and editing initiative details
 * @returns {React.ReactElement} The ViewInitiative component
 */
const ViewInitiative = () => {
    const { initiativeId } = useParams();
    const {
        initiativesData,
        shouldShowSkeleton,
        isDeletingInitiative,
        error,
        updateInitiative,
        deleteInitiative,
        reloadInitiatives,
    } = useInitiativesContext();

    const initiativeData = initiativesData?.find(i => i.id === initiativeId);

    const { preferences, updateViewInitiativeShowListView, updateSelectedTaskStatuses } = useUserPreferences();
    const showListView = preferences.viewInitiativeShowListView;
    const [tasksReloadCounter, setTasksReloadCounter] = React.useState(0);

    const { setActiveInitiative } = useActiveEntity();

    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const closeFilter = useCallback(() => {
        setIsFilterOpen(false);
    }, []);

    // Toggle filter visibility
    const toggleFilter = useCallback(() => {
        setIsFilterOpen(prev => !prev);
    }, []);

    const handleStatusToggle = useCallback((status: string) => {
        const prevSelectedStatus = preferences.selectedTaskStatuses.includes(status);
        const newSelectedStatuses = prevSelectedStatus
            ? preferences.selectedTaskStatuses.filter(s => s !== status)
            : [...preferences.selectedTaskStatuses, status];
        updateSelectedTaskStatuses(newSelectedStatuses);
    }, [preferences, updateSelectedTaskStatuses]);

    // Set the active initiative id
    React.useEffect(() => {
        if (initiativeId) {
            setActiveInitiative(initiativeId);
        }
        return () => {
            setActiveInitiative(null);
        };
    }, [initiativeId, setActiveInitiative]);

    // Add a function to reload tasks
    const reloadTasks = () => {
        setTasksReloadCounter(prev => prev + 1);
    };

    // Combined refresh function for both initiatives and tasks
    const handleRefresh = React.useCallback(async () => {
        try {
            await reloadInitiatives();
            reloadTasks();
        } catch (error) {
            console.error('Failed to refresh data:', error);
        }
    }, [reloadInitiatives, reloadTasks]);

    /**
     * Whenever a field changes, update localData and mark as changed if different from original.
     */
    const handleFieldChange = async <K extends keyof InitiativeDto>(
        field: K,
        value: InitiativeDto[K] | null
    ) => {
        const updated = { ...initiativeData, [field]: value };

        try {
            await updateInitiative({
                ...updated,
                updated_at: new Date().toISOString(),
            });
        } catch (err) {
            console.error('Failed to save changes', err);
        }
    };

    /**
     * Whenever a property changes, update localData and mark as changed if different from original.
     */
    const handlePropertyChange = async <K extends keyof InitiativeDto>(
        field_definition_id: string,
        value: InitiativeDto[K] | null
    ) => {
        const prevProperties = initiativeData?.properties || {};
        const updatedProperties = { ...prevProperties, [field_definition_id]: value };
        const updated = { ...initiativeData, properties: updatedProperties };

        try {
            await updateInitiative({
                ...updated,
                updated_at: new Date().toISOString(),
            });
        } catch (err) {
            console.error('Failed to save changes', err);
        }
    };

    const handleDeleteInitiative = async () => {
        if (!initiativeData) {
            console.error('tried to delete initiative but no initiative data found');
            return;
        }
        await deleteInitiative(initiativeData.id);
    };

    const pageShouldShowSkeleton = shouldShowSkeleton || isDeletingInitiative;

    // View switch button handler
    const toggleView = () => {
        updateViewInitiativeShowListView(!showListView);
    };

    if (!pageShouldShowSkeleton && !initiativeData) {
        return <div>Initiative not found</div>;
    }

    return (
        <>
            <ItemView
                identifier={initiativeData?.identifier}
                status={initiativeData?.status ? statusDisplay(initiativeData.status) : ''}
                loading={pageShouldShowSkeleton}
                error={error}
                createdAt={initiativeData?.created_at}
                updatedAt={initiativeData?.updated_at}
                isEntityLocked={false}
                onDelete={handleDeleteInitiative}
                onRefresh={handleRefresh}
                dataTestId="view-initiative"
            >

                {/* --- Content --- */}
                <div
                    className={
                        `mt-4 p-4 border border-border rounded bg-background bg-opacity-80`
                    }
                    data-testid="bottom-content"
                >
                    {/* Title */}
                    <TitleInput
                        value={initiativeData?.title || ''}
                        onChange={(value) => handleFieldChange('title', value)}
                        loading={pageShouldShowSkeleton || !initiativeData}
                        placeholder="Title of your initiative"
                        maxLength={200}
                        showCharCount={true}
                    />

                    {/* --- Details Section --- */}
                    <EntityDetailsEditor
                        entityType={EntityType.INITIATIVE}
                        data={initiativeData as Record<string, any>}
                        onFieldChange={(field, value) => handleFieldChange(field as keyof InitiativeDto, value)}
                        onPropertyChange={handlePropertyChange}
                        onAddField={(field, value) => {
                            handleFieldChange(field as keyof InitiativeDto, value);
                        }}
                        onDeleteField={(field) => {
                            handleFieldChange(field as keyof InitiativeDto, null);
                        }}
                        loading={pageShouldShowSkeleton || !initiativeData}
                        error={error}
                        fieldOptions={{
                            status: [InitiativeStatus.BACKLOG, InitiativeStatus.TO_DO, InitiativeStatus.IN_PROGRESS, InitiativeStatus.DONE],
                            type: ['FEATURE', 'BUGFIX', 'RESEARCH', 'CHORE'],
                        }}
                    />

                    {/* Description */}
                    <DescriptionSection
                        description={initiativeData?.description || ''}
                        loading={pageShouldShowSkeleton || !initiativeData}
                        testId="initiative-description-section"
                    />

                    {/* View switch button */}
                    <div className="flex flex-row justify-between">
                        <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light">
                            <GrDocumentText />
                            <span className="ml-2.5">Tasks</span>
                        </div>
                        <div className="flex justify-end gap-2">
                            <Button
                                id="switch-task-view"
                                data-testid="switch-task-view"
                                onClick={toggleView}
                                title={showListView ? "Switch to Kanban View" : "Switch to List View"}
                            >
                                {!showListView ? (
                                    <MdOutlineViewKanban stroke='1' size='24' />
                                ) : (
                                    <MdViewHeadline stroke='1' size='24' />
                                )}
                            </Button>

                            <div className="relative">
                                <Button
                                    onClick={toggleFilter}
                                    data-testid="filter-button"
                                    aria-expanded={isFilterOpen}
                                    aria-controls="initiative-filter-popover"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5"
                                        stroke="currentColor" className="size-6">
                                        <path strokeLinecap="round" strokeLinejoin="round"
                                            d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z" />
                                    </svg> Filter
                                </Button>

                                {isFilterOpen && (
                                    <div id="initiative-filter-popover">
                                        <StatusFilter
                                            availableStatuses={Object.values(TaskStatus)}
                                            selectedStatuses={preferences.selectedTaskStatuses as TaskStatus[]}
                                            onStatusToggle={handleStatusToggle}
                                            onClose={closeFilter}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Tasks view */}
                    {!pageShouldShowSkeleton && !error && showListView && (
                        <TasksList
                            initiativeId={initiativeId || ''}
                            reloadCounter={tasksReloadCounter}
                            onUpdate={reloadTasks}
                            filterToStatus={preferences.selectedTaskStatuses as TaskStatus[]}
                        />
                    )}
                    {!pageShouldShowSkeleton && !error && !showListView && (
                        <TasksKanbanBoard
                            filterToInitiativeId={initiativeId}
                            reloadCounter={tasksReloadCounter}
                            onUpdate={reloadTasks}
                            filterToStatus={preferences.selectedTaskStatuses as TaskStatus[]}
                        />
                    )}

                    {/* Compact Create Task */}
                    <div className="mt-4 mb-8" data-testid="compact-create-task">
                        <CompactCreateTask
                            disabled={pageShouldShowSkeleton || !!error}
                            initiativeId={initiativeId}
                            onTaskCreated={reloadTasks}
                        />
                    </div>
                </div>
            </ItemView>
        </>
    );
};

export default ViewInitiative;
