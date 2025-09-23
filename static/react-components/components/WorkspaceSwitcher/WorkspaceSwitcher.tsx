import React, { useState, useRef, useEffect } from 'react';
import { useWorkspaces } from '#hooks/useWorkspaces';
import WorkspaceSwitcherPresenter from './WorkspaceSwitcherPresenter';
import WorkspaceCreateModal from './WorkspaceCreateModal';
import CreateFirstWorkspaceModal from './CreateFirstWorkspaceModal';
import { setCurrentWorkspace } from '#services/workspaceApi';
import { WorkspaceDto } from '#types';
import { createDefaultFieldDefinitions } from '#hooks/useFieldDefinitions';


// TODO - need a constants file
const ACCOUNT_URL = '/account';


interface WorkspaceSwitcherProps {
    workspaceLimit: number;
}
/**
 * Container component for handling workspace switching logic
 */
const WorkspaceSwitcher: React.FC<WorkspaceSwitcherProps> = ({ workspaceLimit }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const [isFirstTimeUser, setIsFirstTimeUser] = useState(false);
    const {
        workspaces,
        currentWorkspace,
        isLoading,
        isProcessing,
        changeWorkspace,
        addWorkspace,
        refresh,
        error,
    } = useWorkspaces();

    // Determine if this is a first-time user (no workspaces)
    useEffect(() => {
        if (isLoading) {
            setIsFirstTimeUser(false);
            return;
        }
        setIsFirstTimeUser(workspaces.length === 0);
    }, [workspaces, isLoading]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const toggleDropdown = () => {
        setIsOpen(!isOpen);
    };

    const handleWorkspaceSelect = (workspace: WorkspaceDto) => {
        changeWorkspace(workspace);
        setIsOpen(false);
    };

    const handleAddWorkspace = () => {
        setIsOpen(false);
        setIsCreateModalOpen(true);
    };

    const handleWorkspaceSettings = () => {
        window.location.href = ACCOUNT_URL;
    }

    const handleCreateWorkspace = async (name: string) => {
        await addWorkspace({
            name,
            icon: null,
            description: null
        })
            .then(() => {
                setIsCreateModalOpen(false);
            }
            ).catch((error) => {
                console.error('Failed to create workspace:', error);
                // TODO - handle error
            });
    };

    return (
        <>
            <WorkspaceSwitcherPresenter
                currentWorkspace={currentWorkspace || undefined}
                workspaces={workspaces}
                isOpen={isOpen}
                isLoading={isLoading && !currentWorkspace}
                isProcessing={isProcessing}
                toggleDropdown={toggleDropdown}
                onWorkspaceSelect={handleWorkspaceSelect}
                onAddWorkspace={handleAddWorkspace}
                onWorkspaceSettings={handleWorkspaceSettings}
                dropdownRef={dropdownRef}
            />

            <WorkspaceCreateModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSubmit={handleCreateWorkspace}
                isProcessing={isProcessing}
                isEnabled={workspaceLimit ? workspaces.length < workspaceLimit : true}
            />

            {/* Show the first workspace creation modal for new users */}
            <CreateFirstWorkspaceModal
                isOpen={isFirstTimeUser}
                onClose={() => {/* No-op - users must create a workspace */ }}
                onSubmit={handleCreateWorkspace}
                isProcessing={isProcessing}
                error={error?.message || null}
            />
        </>
    );
};

export default WorkspaceSwitcher;
