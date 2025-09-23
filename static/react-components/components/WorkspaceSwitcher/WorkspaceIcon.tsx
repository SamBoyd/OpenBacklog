import { WorkspaceDto } from '#types';
import React from 'react';

/**
 * Size options for workspace icons
 */
type IconSize = 'small' | 'medium' | 'large';

/**
 * Props for the WorkspaceIcon component
 */
interface WorkspaceIconProps {
    workspace: WorkspaceDto;
    size?: IconSize;
}

/**
 * Component for displaying workspace icons with fallback to initials
 */
const WorkspaceIcon: React.FC<WorkspaceIconProps> = ({ workspace, size = 'medium' }) => {
    const sizeClasses = {
        small: 'w-5 h-5 text-sm',
        medium: 'w-6 h-6 text-sm',
        large: 'w-8 h-8 text-sm',
    };

    const classes = sizeClasses[size];

    if (workspace.icon) {
        return (
            <img
                src={workspace.icon}
                alt={`${workspace.name} icon`}
                className={`${classes} rounded-full object-cover`}
                data-testid="workspace-icon-image"
            />
        );
    }

    return (
        <div
            className={`${classes} bg-blue-500 rounded-full flex items-center justify-center text-white`}
            data-testid="workspace-icon-initial"
        >
            {workspace.name.charAt(0).toUpperCase()}
        </div>
    );
};

export default WorkspaceIcon;
