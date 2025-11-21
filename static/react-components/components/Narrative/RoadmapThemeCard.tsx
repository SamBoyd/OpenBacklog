import React from 'react';
import { ThemeDto } from '#api/productStrategy';
import Card from '../reusable/Card';

/**
 * Props for RoadmapThemeCard component.
 */
export interface RoadmapThemeCardProps {
    /**
     * The theme data to display
     */
    theme: ThemeDto;
    /**
     * Number of outcomes linked to this theme
     */
    outcomeCount?: number;
    /**
     * Whether the card is expanded
     */
    isExpanded?: boolean;
    /**
     * Callback when expand/collapse is toggled
     */
    onToggleExpand?: (expanded: boolean) => void;
    /**
     * Callback when card is clicked
     */
    onClick?: () => void;
    /**
     * Additional CSS classes
     */
    className?: string;
    /**
     * Test ID for testing
     */
    dataTestId?: string;
}

/**
 * Truncates description to a specified character limit.
 * @param {string | null} description - The full description
 * @param {number} maxLength - Maximum character length (default: 100)
 * @returns {string} Truncated description with ellipsis if needed
 */
const truncateDescription = (description: string | null, maxLength: number = 100): string => {
    if (!description) {
        return '';
    }
    if (description.length <= maxLength) {
        return description;
    }
    return description.substring(0, maxLength).trim() + '...';
};

/**
 * Formats time horizon in months to a readable string.
 * @param {number | null} months - Time horizon in months
 * @returns {string} Formatted time horizon
 */
const formatTimeHorizon = (months: number | null): string => {
    if (!months) return '';
    if (months < 12) return `${months} month${months !== 1 ? 's' : ''}`;
    const years = Math.round(months / 12);
    return `${years} year${years !== 1 ? 's' : ''}`;
};

/**
 * RoadmapThemeCard displays a roadmap theme with problem statement, hypothesis, and time horizon.
 * @param {RoadmapThemeCardProps} props - Component props
 * @returns {React.ReactElement} The RoadmapThemeCard component
 */
const RoadmapThemeCard: React.FC<RoadmapThemeCardProps> = ({
    theme,
    outcomeCount = 0,
    isExpanded = false,
    onToggleExpand,
    onClick,
    className = '',
    dataTestId = 'roadmap-theme-card',
}) => {
    const handleToggle = (e: React.MouseEvent) => {
        e.stopPropagation();
        onToggleExpand?.(!isExpanded);
    };

    return (
        <Card
            className={`border border-border p-6 ${onClick ? 'cursor-pointer hover:bg-accent/30' : ''} ${className}`}
            onClick={onClick}
            dataTestId={dataTestId}
        >
            {/* Header: Name and Expand Button */}
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1" data-testid={`${dataTestId}-header`}>
                    <h3 className="text-base font-semibold text-foreground mb-2" data-testid={`${dataTestId}-name`}>
                        {theme.name}
                    </h3>
                    <p className="text-sm text-muted-foreground line-clamp-2" data-testid={`${dataTestId}-problem-statement`}>
                        {truncateDescription(theme.problem_statement, 120)}
                    </p>
                </div>
                {/* Expand/Collapse Button */}
                <button
                    onClick={handleToggle}
                    className="p-2 rounded-lg text-muted-foreground hover:bg-accent/50 transition-colors flex-shrink-0"
                    data-testid={`${dataTestId}-expand-button`}
                >
                    <span className={`text-lg transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                        ▼
                    </span>
                </button>
            </div>

            {/* Metadata Section */}
            <div className="flex flex-wrap gap-4 mb-4" data-testid={`${dataTestId}-metadata`}>
                {theme.time_horizon_months && (
                    <div className="flex items-center gap-1" data-testid={`${dataTestId}-time-horizon`}>
                        <span className="text-xs text-muted-foreground">Time Horizon:</span>
                        <span className="text-sm font-semibold text-foreground">
                            {formatTimeHorizon(theme.time_horizon_months)}
                        </span>
                    </div>
                )}
                <div className="flex items-center gap-1" data-testid={`${dataTestId}-outcome-count`}>
                    <span className="text-xs text-muted-foreground">Linked to</span>
                    <span className="text-sm font-semibold text-foreground">
                        {outcomeCount} outcome{outcomeCount !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            {/* Hypothesis Section */}
            {theme.hypothesis && (
                <div className="mb-4 pb-4 border-b border-border" data-testid={`${dataTestId}-hypothesis`}>
                    <h4 className="text-xs font-medium text-muted-foreground mb-1">Our Hypothesis:</h4>
                    <p className="text-sm text-muted-foreground italic">{truncateDescription(theme.hypothesis, 150)}</p>
                </div>
            )}

            {/* Expanded Content */}
            {isExpanded && (
                <div className="mt-4 pt-4 border-t border-border space-y-4" data-testid={`${dataTestId}-expanded`}>
                    <div>
                        <h4 className="text-xs font-medium text-muted-foreground mb-2">Problem Statement:</h4>
                        <p className="text-sm text-foreground leading-relaxed">{theme.problem_statement}</p>
                    </div>
                    {theme.hypothesis && (
                        <div>
                            <h4 className="text-xs font-medium text-muted-foreground mb-2">Hypothesis:</h4>
                            <p className="text-sm text-foreground leading-relaxed">{theme.hypothesis}</p>
                        </div>
                    )}
                    {theme.indicative_metrics && (
                        <div>
                            <h4 className="text-xs font-medium text-muted-foreground mb-2">Indicative Metrics:</h4>
                            <p className="text-sm text-foreground leading-relaxed">{theme.indicative_metrics}</p>
                        </div>
                    )}
                </div>
            )}
        </Card>
    );
};

export default RoadmapThemeCard;
