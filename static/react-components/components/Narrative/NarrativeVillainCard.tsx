import React from 'react';
import { VillainDto, VillainType } from '#types';
import Card from '../reusable/Card';
import { CompactButton } from '#components/reusable/Button';
import { ChevronDownIcon, SkullIcon, TargetIcon, UserIcon, AlertTriangleIcon } from 'lucide-react';

/**
 * Props for NarrativeVillainCard component.
 */
export interface NarrativeVillainCardProps {
    /**
     * The villain data to display
     */
    villain: VillainDto;
    /**
     * Number of roadmap themes this villain appears in
     */
    themeCount?: number;
    /**
     * Number of heroes this villain opposes
     */
    heroCount?: number;
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
 * Returns the display label for a villain type.
 * @param {VillainType} villainType - The villain type enum value
 * @returns {string} Human-readable label
 */
const getVillainTypeLabel = (villainType: VillainType): string => {
    const labels: Record<VillainType, string> = {
        [VillainType.EXTERNAL]: 'External',
        [VillainType.INTERNAL]: 'Internal',
        [VillainType.WORKFLOW]: 'Workflow',
        [VillainType.TECHNICAL]: 'Technical',
        [VillainType.OTHER]: 'Other',
    };
    return labels[villainType] || 'Unknown';
};

/**
 * Returns severity styling based on the severity level.
 * @param {number} severity - Severity level (1-5)
 * @returns {{ bgColor: string, textColor: string }} Color classes
 */
const getSeverityStyle = (severity: number): { bgColor: string; textColor: string } => {
    if (severity >= 4) return { bgColor: 'bg-destructive/20', textColor: 'text-destructive' };
    if (severity >= 3) return { bgColor: 'bg-amber-500/20', textColor: 'text-amber-500' };
    return { bgColor: 'bg-muted/10', textColor: 'text-muted-foreground' };
};

/**
 * NarrativeVillainCard displays a detailed villain card for the story bible.
 * Shows villain name, type, severity, themes confronted, and heroes opposed.
 * @param {NarrativeVillainCardProps} props - Component props
 * @returns {React.ReactElement} The NarrativeVillainCard component
 */
const NarrativeVillainCard: React.FC<NarrativeVillainCardProps> = ({
    villain,
    themeCount = 0,
    heroCount = 0,
    isExpanded = false,
    onToggleExpand,
    onClick,
    className = '',
    dataTestId = 'narrative-villain-card',
}) => {
    const handleToggle = (e: React.MouseEvent) => {
        e.stopPropagation();
        onToggleExpand?.(!isExpanded);
    };

    const severityStyle = getSeverityStyle(villain.severity);

    return (
        <Card
            className={`border border-border p-5 transition-colors ${onClick ? 'cursor-pointer hover:bg-accent/30' : ''} ${className}`}
            onClick={onClick}
            dataTestId={dataTestId}
        >
            {/* Header: Icon, Name, Type Badge, and Expand Button */}
            <div className="flex items-start gap-4">
                {/* Villain Icon */}
                <div className="p-2 rounded-lg bg-destructive/10 flex-shrink-0">
                    <SkullIcon className="w-5 h-5 text-destructive" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    {/* Name and Type Badge */}
                    <div className="flex items-center gap-2 mb-1 flex-wrap" data-testid={`${dataTestId}-header`}>
                        <span className="px-2 py-0.5 text-xs font-mono font-medium rounded bg-muted/10 text-muted-foreground flex-shrink-0">
                            {villain.identifier}
                        </span>
                        <h3 className="text-base font-semibold text-foreground" data-testid={`${dataTestId}-name`}>
                            {villain.name}
                        </h3>
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-muted/10 text-muted-foreground flex-shrink-0">
                            {getVillainTypeLabel(villain.villain_type)}
                        </span>
                        {villain.is_defeated && (
                            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-success/20 text-success flex-shrink-0">
                                Defeated
                            </span>
                        )}
                    </div>

                    {/* Description */}
                    {villain.description && (
                        <p
                            className={`text-sm text-muted-foreground ${isExpanded ? '' : 'line-clamp-2'}`}
                            data-testid={`${dataTestId}-description`}
                        >
                            {villain.description}
                        </p>
                    )}

                    {/* Stats Section */}
                    <div className="flex flex-wrap gap-4 mt-3" data-testid={`${dataTestId}-stats`}>
                        {/* Severity */}
                        <div className="flex items-center gap-1.5" data-testid={`${dataTestId}-severity`}>
                            <AlertTriangleIcon className={`w-3.5 h-3.5 ${severityStyle.textColor}`} />
                            <span className="text-xs text-muted-foreground">
                                Severity: <span className={`font-medium ${severityStyle.textColor}`}>{villain.severity}/5</span>
                            </span>
                        </div>
                        {/* Theme Count */}
                        <div className="flex items-center gap-1.5" data-testid={`${dataTestId}-theme-count`}>
                            <TargetIcon className="w-3.5 h-3.5 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                                <span className="font-medium text-foreground">{themeCount}</span> theme{themeCount !== 1 ? 's' : ''}
                            </span>
                        </div>
                        {/* Hero Count */}
                        <div className="flex items-center gap-1.5" data-testid={`${dataTestId}-hero-count`}>
                            <UserIcon className="w-3.5 h-3.5 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                                Opposes <span className="font-medium text-primary">{heroCount}</span> hero{heroCount !== 1 ? 'es' : ''}
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
            {isExpanded && villain.description && (
                <div className="mt-4 pt-4 border-t border-border ml-12" data-testid={`${dataTestId}-expanded`}>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">Full Description</h4>
                    <p className="text-sm text-foreground leading-relaxed">
                        {villain.description}
                    </p>
                </div>
            )}
        </Card>
    );
};

export default NarrativeVillainCard;
