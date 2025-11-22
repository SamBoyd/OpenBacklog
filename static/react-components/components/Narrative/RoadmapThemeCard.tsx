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
 * RoadmapThemeCard displays a roadmap theme with its description and linked outcomes.
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
                    <p className="text-sm text-muted-foreground line-clamp-2" data-testid={`${dataTestId}-description`}>
                        {truncateDescription(theme.description, 120)}
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
                <div className="flex items-center gap-1" data-testid={`${dataTestId}-outcome-count`}>
                    <span className="text-xs text-muted-foreground">Linked to</span>
                    <span className="text-sm font-semibold text-foreground">
                        {outcomeCount} outcome{outcomeCount !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
                <div className="mt-4 pt-4 border-t border-border space-y-4" data-testid={`${dataTestId}-expanded`}>
                    <div>
                        <h4 className="text-xs font-medium text-muted-foreground mb-2">Description:</h4>
                        <p className="text-sm text-foreground leading-relaxed">{theme.description}</p>
                    </div>
                </div>
            )}
        </Card>
    );
};

export default RoadmapThemeCard;
