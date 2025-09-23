import React, { ReactNode } from 'react';
import { ChevronRight } from 'lucide-react';

interface SettingsRowProps {
    label: string;
    value?: ReactNode;
    onClick?: () => void;
    showChevron?: boolean;
    className?: string;
}

/**
 * A reusable component for rendering a settings row with a label and value
 */
const SettingsRow: React.FC<SettingsRowProps> = ({
    label,
    value,
    onClick,
    showChevron = true,
    className = ''
}) => {
    return (
        <div
            className={`flex items-center justify-between py-2 ${onClick ? 'cursor-pointer' : ''} ${className}`}
            onClick={onClick}
        >
            <span>{label}</span>
            <div className="flex items-center justify-between text-muted-foreground">
                <span className="mr-2">{value}</span>
                {showChevron && onClick && <ChevronRight size={16} />}
            </div>
        </div>
    );
};

export default SettingsRow; 