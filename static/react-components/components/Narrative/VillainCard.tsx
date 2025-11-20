import React from 'react';
import { VillainDto, VillainType } from '#types';
import Card from '../reusable/Card';

export interface VillainCardProps {
    villain: VillainDto;
    onClick?: () => void;
    className?: string;
    dataTestId?: string;
}

/**
 * Returns the Tailwind CSS color class for a given villain type.
 * @param {VillainType} villainType - The type of villain
 * @returns {string} Tailwind CSS classes for badge styling
 */
const getVillainTypeBadgeColor = (villainType: VillainType): string => {
    switch (villainType) {
        case VillainType.EXTERNAL:
            return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
        case VillainType.INTERNAL:
            return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
        case VillainType.TECHNICAL:
            return 'bg-red-500/10 text-red-500 border-red-500/20';
        case VillainType.WORKFLOW:
            return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
        case VillainType.OTHER:
            return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
        default:
            return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
};

/**
 * Returns the Tailwind CSS color class for a given severity level.
 * @param {number} severity - The severity level (1-5)
 * @returns {string} Tailwind CSS classes for severity indicator
 */
const getSeverityColor = (severity: number): string => {
    if (severity >= 5) {
        return 'text-destructive';
    } else if (severity >= 4) {
        return 'text-orange-500';
    } else if (severity >= 3) {
        return 'text-yellow-500';
    } else if (severity >= 2) {
        return 'text-muted-foreground';
    } else {
        return 'text-success';
    }
};

/**
 * Formats villain type enum value to display text.
 * @param {VillainType} villainType - The villain type enum
 * @returns {string} Formatted display text
 */
const formatVillainType = (villainType: VillainType): string => {
    return villainType.replace(/_/g, ' ');
};

/**
 * Truncates description to a specified character limit.
 * @param {string} description - The full description
 * @param {number} maxLength - Maximum character length (default: 100)
 * @returns {string} Truncated description with ellipsis if needed
 */
const truncateDescription = (description: string, maxLength: number = 100): string => {
    if (description.length <= maxLength) {
        return description;
    }
    return description.substring(0, maxLength).trim() + '...';
};

/**
 * VillainCard component displays a summary card for a villain (problem/obstacle).
 * @param {VillainCardProps} props - The component props
 * @returns {React.ReactElement} The VillainCard component
 */
const VillainCard: React.FC<VillainCardProps> = ({
    villain,
    onClick,
    className = '',
    dataTestId = 'villain-card',
}) => {
    return (
        <Card
            className={`border border-border p-4 ${onClick ? 'cursor-pointer hover:bg-accent/50' : ''} ${className}`}
            onClick={onClick}
            dataTestId={dataTestId}
        >
            {/* Header with identifier and defeated badge */}
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-mono text-muted-foreground" data-testid={`${dataTestId}-identifier`}>
                        {villain.identifier}
                    </span>
                    {villain.is_defeated && (
                        <span
                            className="text-xs px-2 py-0.5 rounded border bg-success/10 text-success border-success/20"
                            data-testid={`${dataTestId}-defeated-badge`}
                        >
                            DEFEATED
                        </span>
                    )}
                </div>
            </div>

            {/* Name */}
            <h3 className="text-lg font-semibold text-foreground mb-2" data-testid={`${dataTestId}-name`}>
                {villain.name}
            </h3>

            {/* Type and Severity */}
            <div className="flex items-center gap-3 mb-3">
                <span
                    className={`text-xs px-2 py-1 rounded border ${getVillainTypeBadgeColor(villain.villain_type)}`}
                    data-testid={`${dataTestId}-type-badge`}
                >
                    {formatVillainType(villain.villain_type)}
                </span>
                <div className="flex items-center gap-1" data-testid={`${dataTestId}-severity`}>
                    <span className="text-xs text-muted-foreground">Severity:</span>
                    <span className={`text-sm font-semibold ${getSeverityColor(villain.severity)}`}>
                        {villain.severity}/5
                    </span>
                </div>
            </div>

            {/* Description preview */}
            <p className="text-sm text-muted-foreground line-clamp-2" data-testid={`${dataTestId}-description`}>
                {truncateDescription(villain.description, 120)}
            </p>
        </Card>
    );
};

export default VillainCard;
