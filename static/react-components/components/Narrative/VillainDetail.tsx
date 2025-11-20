import React from 'react';
import { VillainDto, VillainType } from '#types';
import ItemView from '../reusable/ItemView';

export interface VillainDetailProps {
    villain: VillainDto | null;
    loading: boolean;
    error: string | null;
    onDelete?: () => void;
    onRefresh?: () => void;
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
 * Renders a visual severity indicator (stars or dots).
 * @param {number} severity - The severity level (1-5)
 * @returns {React.ReactElement} The severity indicator component
 */
const SeverityIndicator: React.FC<{ severity: number; dataTestId?: string }> = ({
    severity,
    dataTestId = 'severity-indicator',
}) => {
    const color = getSeverityColor(severity);

    return (
        <div className="flex items-center gap-1" data-testid={dataTestId}>
            {[1, 2, 3, 4, 5].map((level) => (
                <div
                    key={level}
                    className={`w-3 h-3 rounded-full ${
                        level <= severity ? color.replace('text-', 'bg-') : 'bg-border'
                    }`}
                    title={`Severity level ${level}`}
                />
            ))}
        </div>
    );
};

/**
 * VillainDetail component displays the full profile of a villain (problem/obstacle).
 * Uses ItemView wrapper for consistent layout with other detail views.
 * @param {VillainDetailProps} props - The component props
 * @returns {React.ReactElement} The VillainDetail component
 */
const VillainDetail: React.FC<VillainDetailProps> = ({
    villain,
    loading,
    error,
    onDelete = () => {},
    onRefresh,
    className,
    dataTestId = 'villain-detail',
}) => {
    if (loading) {
        return (
            <div className="p-8 text-center" data-testid={`${dataTestId}-loading`}>
                <div className="text-muted-foreground">Loading villain...</div>
            </div>
        );
    }

    if (!villain) {
        return (
            <div className="p-8 text-center" data-testid={`${dataTestId}-empty`}>
                <div className="text-muted-foreground">No villain data available</div>
            </div>
        );
    }

    return (
        <ItemView
            identifier={villain.identifier}
            status={villain.is_defeated ? 'DEFEATED' : 'ACTIVE'}
            loading={loading}
            isEntityLocked={false}
            error={error}
            createdAt={villain.created_at}
            updatedAt={villain.updated_at}
            onDelete={onDelete}
            onRefresh={onRefresh}
            className={className}
            dataTestId={dataTestId}
        >
            {/* Name */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-foreground" data-testid={`${dataTestId}-name`}>
                    {villain.name}
                </h1>
            </div>

            {/* Type and Status Badges */}
            <div className="flex items-center gap-3 mb-6">
                <div>
                    <label className="text-xs text-muted-foreground block mb-1">Type</label>
                    <span
                        className={`text-sm px-3 py-1.5 rounded border ${getVillainTypeBadgeColor(villain.villain_type)}`}
                        data-testid={`${dataTestId}-type-badge`}
                    >
                        {formatVillainType(villain.villain_type)}
                    </span>
                </div>
                {villain.is_defeated && (
                    <div>
                        <label className="text-xs text-muted-foreground block mb-1">Status</label>
                        <span
                            className="text-sm px-3 py-1.5 rounded border bg-success/10 text-success border-success/20"
                            data-testid={`${dataTestId}-defeated-badge`}
                        >
                            DEFEATED
                        </span>
                    </div>
                )}
            </div>

            {/* Severity */}
            <div className="mb-6">
                <label className="text-xs text-muted-foreground block mb-2">
                    Severity Level
                </label>
                <div className="flex items-center gap-3">
                    <SeverityIndicator severity={villain.severity} dataTestId={`${dataTestId}-severity-indicator`} />
                    <span className={`text-lg font-semibold ${getSeverityColor(villain.severity)}`} data-testid={`${dataTestId}-severity-value`}>
                        {villain.severity}/5
                    </span>
                </div>
            </div>

            {/* Description */}
            <div className="mb-6">
                <label className="text-xs text-muted-foreground block mb-2">
                    Description
                </label>
                <div
                    className="text-sm text-foreground whitespace-pre-wrap border border-border rounded p-4 bg-card"
                    data-testid={`${dataTestId}-description`}
                >
                    {villain.description}
                </div>
            </div>
        </ItemView>
    );
};

export default VillainDetail;
