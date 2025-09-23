import React, { ReactNode } from 'react';

interface SettingsSectionProps {
    title: string;
    children: ReactNode;
    icon?: ReactNode;
    className?: string;
}

/**
 * A reusable component for rendering a settings section with a title
 */
const SettingsSection: React.FC<SettingsSectionProps> = ({
    title,
    children,
    icon,
    className = ''
}) => {
    return (
        <div className={`${className}`}>
            <div className="flex items-center gap-2 mb-2">
                {icon && <span className="text-muted-foreground">{icon}</span>}
                <span className="font-medium">{title}</span>
            </div>
            <div className="mt-2">
                {children}
            </div>
        </div>
    );
};

export default SettingsSection; 