import React from 'react';
import { PillarDto, OutcomeDto } from '#api/productStrategy';
import Card from '../reusable/Card';

/**
 * Props for StrategicPillarCard component.
 */
export interface StrategicPillarCardProps {
    /**
     * The pillar data to display
     */
    pillar: PillarDto;
    /**
     * Number of outcomes linked to this pillar
     */
    outcomeCount?: number;
    /**
     * The outcomes linked to this pillar
     */
    outcomes?: OutcomeDto[];
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
 * StrategicPillarCard displays a strategic pillar with name and description.
 * @param {StrategicPillarCardProps} props - Component props
 * @returns {React.ReactElement} The StrategicPillarCard component
 */
const StrategicPillarCard: React.FC<StrategicPillarCardProps> = ({
    pillar,
    outcomeCount = 0,
    outcomes = [],
    isExpanded = false,
    onToggleExpand,
    onClick,
    className = '',
    dataTestId = 'strategic-pillar-card',
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
                        {pillar.name}
                    </h3>
                    {pillar.description && (
                        <p className="text-sm text-muted-foreground line-clamp-2" data-testid={`${dataTestId}-description`}>
                            {truncateDescription(pillar.description, 120)}
                        </p>
                    )}
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

            {/* Stats Section */}
            <div className="flex items-center gap-4 mb-4" data-testid={`${dataTestId}-stats`}>
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
                    {pillar.description && (
                        <div>
                            <h4 className="text-xs font-medium text-muted-foreground mb-2">Description:</h4>
                            <p className="text-sm text-foreground leading-relaxed">{pillar.description}</p>
                        </div>
                    )}
                    {outcomes && outcomes.length > 0 && (
                        <div>
                            <h4 className="text-xs font-medium text-muted-foreground mb-2">Linked Outcomes:</h4>
                            <ul className="space-y-2">
                                {outcomes.map(outcome => (
                                    <li key={outcome.id} className="text-sm">
                                        <span className="font-medium text-foreground">{outcome.name}</span>
                                        {outcome.description && (
                                            <p className="text-xs text-muted-foreground mt-0.5">
                                                {truncateDescription(outcome.description, 80)}
                                            </p>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </Card>
    );
};

export default StrategicPillarCard;
