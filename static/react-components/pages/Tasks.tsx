import React, { useCallback, useEffect, useRef } from 'react';
import { MdOutlineViewKanban, MdViewHeadline } from 'react-icons/md';

import { useUserPreferences } from '#hooks/useUserPreferences';
import { useTasksContext } from '#contexts/TasksContext';
import { useContainerWidth } from '#hooks/useContainerWidth';
import { useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';

import TasksKanbanBoard from '#components/TasksKanbanBoard';
import CompactCreateTask from '#components/CompactCreateTask';
import Card from '#components/reusable/Card';
import { Button } from '#components/reusable/Button';
import WorkspaceSwitcher from '#components/WorkspaceSwitcher/WorkspaceSwitcher';
import TasksList from '#components/TasksList';
import StatusFilter from '#components/StatusFilter';
import { InitiativeFilter } from '#components/InitiativeFilter';
import InitiativesListDiff from '#components/diffs/InitiativesListDiff';

import { TaskStatus } from '#types';

const Tasks = () => {
    const { suggestions } = useSuggestionsToBeResolved();
    const { preferences, updateFilterTasksToInitiative, updateSelectedTaskStatuses, updateTasksShowListView } = useUserPreferences();

    const headerRef = useRef<HTMLDivElement>(null);
    const { isNarrow } = useContainerWidth(headerRef, 700);

    const [selectedInitiativeId, setSelectedInitiativeId] = React.useState<string>(
        preferences.filterTasksToInitiative || ''
    );
    const { tasks, reloadTasks, setInitiativeId } = useTasksContext();

    // Update the context when selectedInitiativeId changes
    useEffect(() => {
        setInitiativeId(selectedInitiativeId);
    }, [selectedInitiativeId, setInitiativeId]);
    const { initiativesData } = useInitiativesContext();

    const showListView = preferences.tasksShowListView;
    const [tasksReloadCounter, setTasksReloadCounter] = React.useState(0);
    const [focusCompactCreateTask, setFocusCompactCreateTask] = React.useState(false);
    const [isFilterOpen, setIsFilterOpen] = React.useState(false);

    useEffect(() => {
        updateFilterTasksToInitiative(selectedInitiativeId === undefined ? null : selectedInitiativeId);
    }, [selectedInitiativeId, updateFilterTasksToInitiative]);

    const setExpandCompactCreateTask = () => {
        setFocusCompactCreateTask(true);
        setTimeout(() => {
            setFocusCompactCreateTask(false);
        }, 1000);
    }

    // Handle status toggle in the filter component
    const handleStatusToggle = useCallback((status: string) => {
        const prevSelectedStatus = preferences.selectedTaskStatuses.includes(status);
        const newSelectedStatuses = prevSelectedStatus
            ? preferences.selectedTaskStatuses.filter(s => s !== status)
            : [...preferences.selectedTaskStatuses, status];
        updateSelectedTaskStatuses(newSelectedStatuses);
    }, [preferences, updateSelectedTaskStatuses]);

    const onCloseFilter = useCallback(() => {
        setIsFilterOpen(false);
    }, []);

    const toggleView = useCallback(() => {
        updateTasksShowListView(!showListView);
    }, [showListView, updateTasksShowListView]);

    return (
        <div className="flex flex-col justify-between gap-2 pt-10 ">
            <div className="flex-grow-1">
                {
                    suggestions.length > 0 && (
                        <InitiativesListDiff />
                    )
                }


                <div ref={headerRef}>
                    <Card
                        className={`
                            relative border-t border-x border-border rounded-b-none flex gap-2 justify-between items-center p-4
                            bg-background ${showListView ? 'border-b' : ''}
                        `}>
                        <div className="flex items-center gap-5">
                            <WorkspaceSwitcher
                                workspaceLimit={1}
                            />

                            <InitiativeFilter
                                id="initiative-select"
                                placeholder="Filter by initiative"
                                onChange={setSelectedInitiativeId}
                                value={selectedInitiativeId}
                                options={initiativesData?.map(initiative => ({
                                    value: initiative.id,
                                    label: initiative.title
                                })) || []}
                                dropdownMaxHeight="52"
                                dropdownWidth="72"
                                searchBar={true}
                            />
                        </div>

                        <div className="flex items-center gap-x-2">
                            <Button
                                id="switch-task-view"
                                data-testid="switch-task-view"
                                className={``}
                                onClick={toggleView}
                            >
                                {!showListView ? (
                                    <MdOutlineViewKanban stroke='1' size='24' />
                                ) : (
                                    <MdViewHeadline stroke='1' size='24' />
                                )}
                            </Button>

                            <div className="relative">
                                <Button
                                    onClick={() => setIsFilterOpen(prev => !prev)}
                                    data-testid="filter-button"
                                    aria-expanded={isFilterOpen}
                                    aria-controls="initiative-filter-popover"
                                    title="Filter tasks"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5"
                                        stroke="currentColor" className="size-6">
                                        <path strokeLinecap="round" strokeLinejoin="round"
                                            d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z" />
                                    </svg> {!isNarrow && 'Filter'}
                                </Button>
                                {isFilterOpen && (
                                    <div id="initiative-filter-popover">
                                        <StatusFilter
                                            availableStatuses={Object.values(TaskStatus)}
                                            selectedStatuses={preferences.selectedTaskStatuses as TaskStatus[]}
                                            onStatusToggle={handleStatusToggle}
                                            onClose={onCloseFilter}
                                        />
                                    </div>
                                )}
                            </div>

                            <Button
                                onClick={() => setExpandCompactCreateTask()}
                                className="gap-x-1.5 px-2.5 py-1.5"
                                disabled={selectedInitiativeId === undefined}
                                title="Create task"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    strokeWidth="1.5"
                                    stroke="currentColor"
                                    className="size-6"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M12 4.5v15m7.5-7.5h-15"
                                    />
                                </svg>
                                {!isNarrow && <span>Create task</span>}
                            </Button>
                        </div>
                    </Card>
                </div>

                {showListView && (
                    <TasksList
                        initiativeId={selectedInitiativeId || null}
                        reloadCounter={tasksReloadCounter}
                        filterToStatus={preferences.selectedTaskStatuses as TaskStatus[]}
                    />
                ) || (
                        <TasksKanbanBoard
                            filterToInitiativeId={selectedInitiativeId}
                            filterToStatus={preferences.selectedTaskStatuses as TaskStatus[]}
                            reloadCounter={tasksReloadCounter}
                        />
                    )}

                {selectedInitiativeId === undefined ? (
                    <div className="text-foreground rounded opacity-15 h-52 flex items-center justify-center">
                        <span>Select an initiative to view tasks.</span>
                    </div>
                ) : null}

                {selectedInitiativeId !== undefined && tasks.length === 0 ? (
                    <div className="bg-card text-foreground rounded opacity-15 h-52 flex items-center justify-center">
                        <span>Create your first task.</span>
                    </div>
                ) : null}

                <CompactCreateTask
                    initiativeId={selectedInitiativeId}
                    onTaskCreated={reloadTasks}
                    focus={focusCompactCreateTask}
                    disabled={selectedInitiativeId === undefined}
                />
            </div>
        </div>
    )
}

export default Tasks;
