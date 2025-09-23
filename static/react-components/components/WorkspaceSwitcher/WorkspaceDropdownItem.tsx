import React from 'react';
import WorkspaceIcon from './WorkspaceIcon';
import { WorkspaceDto } from '#types';
import { Button } from '#components/reusable/Button';

/**
 * Props for the WorkspaceDropdownItem component
 */
interface WorkspaceDropdownItemProps {
    workspace: WorkspaceDto;
    isActive: boolean;
    onClick: () => void;
}

/**
 * Component for rendering individual workspace items in the dropdown
 */
const WorkspaceDropdownItem: React.FC<WorkspaceDropdownItemProps> = ({
    workspace,
    isActive,
    onClick
}) => {
    return (
        <button
            onClick={onClick}
            className={
                `rounded 
                text-foreground
                hover:bg-muted-foreground/10 
                flex items-center justify-start
                gap-x-1.5 text-sm w -full
                `
            }
            data-testId={`workspace-option-${workspace.id}`}
            disabled={isActive}
        >
            <span >{workspace.name}</span>
        </button>
    );
};

export default WorkspaceDropdownItem;
