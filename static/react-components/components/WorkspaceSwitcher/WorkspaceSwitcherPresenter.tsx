import React, { useEffect } from 'react';
import WorkspaceIcon from './WorkspaceIcon';
import WorkspaceDropdownItem from './WorkspaceDropdownItem';
import { WorkspaceDto } from '#types';
import { Button } from '#components/reusable/Button';

/**
 * Props for the WorkspaceSwitcherPresenter component
 */
interface WorkspaceSwitcherPresenterProps {
    currentWorkspace?: WorkspaceDto;
    workspaces: WorkspaceDto[];
    isOpen: boolean;
    isLoading: boolean;
    isProcessing: boolean;
    toggleDropdown: () => void;
    onWorkspaceSelect: (workspace: WorkspaceDto) => void;
    onAddWorkspace: () => void;
    onWorkspaceSettings: () => void;
    dropdownRef: React.RefObject<HTMLDivElement>;
}

/**
 * Presentation component for workspace switching UI
 */
const WorkspaceSwitcherPresenter: React.FC<WorkspaceSwitcherPresenterProps> = ({
    currentWorkspace,
    workspaces,
    isOpen,
    isLoading,
    isProcessing,
    toggleDropdown,
    onWorkspaceSelect,
    onAddWorkspace,
    onWorkspaceSettings,
    dropdownRef,
}) => {

    if (isLoading) {
        return (
            <div className="px-3 py-2 rounded-md" data-testid="workspace-switcher-loading">
                <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-gray-200 animate-pulse"></div>
                    <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
                </div>
            </div>
        );
    }

    if (!currentWorkspace) {
        return (
            <div className="px-4 py-3 bg-background text-background rounded-md border-background/10" data-testid="workspace-switcher-empty">
                No workspace selected
            </div>
        );
    }

    return (
        <div className="relative" ref={dropdownRef} data-testid="workspace-switcher">
            <button
                onClick={toggleDropdown}
                disabled={isProcessing}
                data-testid="workspace-switcher-button"
                className="flex items-center"
            >
                <div className="flex items-center">
                    <span className="text-foreground ml-2 font-medium truncate max-w-[250px] hover:text-primary">
                        {currentWorkspace.name}
                    </span>
                </div>
            </button>

            {isOpen && (
                <div
                    className="z-50 absolute -left-2 mt-2 min-w-56 flex rounded-md shadow-lg bg-background ring-1 ring-foreground/10 ring-opacity-5"
                    data-testid="workspace-dropdown"
                >
                    <div className="p-2 flex flex-col gap-2 w-full" role="menu" aria-orientation="vertical">
                        <div className="px-3 py-2 text-sm font-semibold text-foreground">
                            Your Workspaces
                        </div>

                        {workspaces.length === 0 ? (
                            <div className="px-4 py-2 text-sm text-gray-500 italic">
                                No workspaces available
                            </div>
                        ) : (
                            workspaces.map((workspace) => (
                                <WorkspaceDropdownItem
                                    key={workspace.id}
                                    workspace={workspace}
                                    isActive={workspace.id === currentWorkspace.id}
                                    onClick={() => onWorkspaceSelect(workspace)}
                                />
                            ))
                        )}

                        <div className="border-t border-gray-100 my-1"></div>
                        <button
                            onClick={onAddWorkspace}
                            disabled={isProcessing}
                            data-testid="add-workspace-button"
                            className={
                                `rounded text-sm 
                                text-foreground
                                hover:bg-muted-foreground/10 
                                flex items-center justify-start
                                gap-x-1.5 px-2.5 py-1.5 border`
                            }
                        >
                            <svg
                                className="w-5 h-5 mr-2"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                            </svg>
                            Add Workspace
                        </button>
                        <button
                            onClick={onWorkspaceSettings}
                            disabled={isProcessing}
                            data-testid="add-workspace-button"
                            className={
                                `rounded text-sm 
                                text-foreground
                                hover:bg-muted-foreground/10 
                                flex items-center justify-start
                                gap-x-1.5 px-2.5 py-1.5 border`
                            }
                        >
                            <svg className="w-5 h-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                            </svg>

                            Workspace settings
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default WorkspaceSwitcherPresenter;
