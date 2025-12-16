import React from 'react';
import { PillarDto } from '#api/productStrategy';
import { OutcomeDto } from '#api/productOutcomes';
import Card from '../reusable/Card';
import { CompactButton } from '#components/reusable/Button';
import { ChevronDownIcon, LayersIcon, TargetIcon, CheckCircleIcon } from 'lucide-react';

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
 * StrategicPillarCard displays a strategic pillar with name, description, and linked outcomes.
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
            className={`border border-border p-5 transition-colors ${onClick ? 'cursor-pointer hover:bg-accent/30' : ''} ${className}`}
            onClick={onClick}
            dataTestId={dataTestId}
        >
            {/* Header: Icon, Name, and Expand Button */}
            <div className="flex items-start gap-4">
                {/* Pillar Icon */}
                <div className="p-2 rounded-lg bg-accent/50 flex-shrink-0">
                    <LayersIcon className="w-5 h-5 text-accent-foreground" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    {/* Name */}
                    <div className="flex items-center gap-2 mb-1" data-testid={`${dataTestId}-header`}>
                        <h3 className="text-base font-semibold text-foreground" data-testid={`${dataTestId}-name`}>
                            {pillar.name}
                        </h3>
                    </div>

                    {/* Description */}
                    {pillar.description && (
                        <p
                            className={`text-sm text-muted-foreground ${isExpanded ? '' : 'line-clamp-2'}`}
                            data-testid={`${dataTestId}-description`}
                        >
                            {pillar.description}
                        </p>
                    )}

                    {/* Stats Section */}
                    <div className="flex flex-wrap gap-4 mt-3" data-testid={`${dataTestId}-stats`}>
                        <div className="flex items-center gap-1.5" data-testid={`${dataTestId}-outcome-count`}>
                            <TargetIcon className="w-3.5 h-3.5 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                                <span className="font-medium text-foreground">{outcomeCount}</span> outcome{outcomeCount !== 1 ? 's' : ''}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Expand/Collapse Button */}
                <CompactButton
                    onClick={handleToggle}
                    className="p-1.5 rounded-lg text-muted-foreground hover:bg-accent/50 transition-colors flex-shrink-0"
                    data-testid={`${dataTestId}-expand-button`}
                >
                    <ChevronDownIcon className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
                </CompactButton>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
                <div className="mt-4 pt-4 border-t border-border ml-12 space-y-4" data-testid={`${dataTestId}-expanded`}>
                    {pillar.description && (
                        <div>
                            <h4 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">Full Description</h4>
                            <p className="text-sm text-foreground leading-relaxed">{pillar.description}</p>
                        </div>
                    )}
                    {outcomes && outcomes.length > 0 && (
                        <div>
                            <h4 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">Linked Outcomes</h4>
                            <ul className="space-y-2">
                                {outcomes.map(outcome => (
                                    <li key={outcome.id} className="flex items-start gap-2 text-sm">
                                        <CheckCircleIcon className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                                        <div>
                                            <span className="font-medium text-foreground">{outcome.name}</span>
                                            {outcome.description && (
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {truncateDescription(outcome.description, 100)}
                                                </p>
                                            )}
                                        </div>
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
