import React from 'react';
import { ThemeDto } from '#api/productStrategy';
import Card from '../reusable/Card';
import { CompactButton } from '#components/reusable/Button';
import { ChevronDownIcon, MapIcon, UserIcon, SkullIcon, TargetIcon } from 'lucide-react';

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
     * Number of heroes featured in this theme
     */
    heroCount?: number;
    /**
     * Number of villains confronted in this theme
     */
    villainCount?: number;
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
 * RoadmapThemeCard displays a roadmap theme with its description, heroes, villains, and outcomes.
 * @param {RoadmapThemeCardProps} props - Component props
 * @returns {React.ReactElement} The RoadmapThemeCard component
 */
const RoadmapThemeCard: React.FC<RoadmapThemeCardProps> = ({
    theme,
    outcomeCount = 0,
    heroCount,
    villainCount,
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

    // Use counts from theme data if not explicitly provided
    const displayHeroCount = heroCount ?? (theme.hero_ids?.length || 0);
    const displayVillainCount = villainCount ?? (theme.villain_ids?.length || 0);

    return (
        <Card
            className={`border border-border p-5 transition-colors ${onClick ? 'cursor-pointer hover:bg-accent/30' : ''} ${className}`}
            onClick={onClick}
            dataTestId={dataTestId}
        >
            {/* Header: Icon, Name, and Expand Button */}
            <div className="flex items-start gap-4">
                {/* Theme Icon */}
                <div className="p-2 rounded-lg bg-secondary/50 flex-shrink-0">
                    <MapIcon className="w-5 h-5 text-secondary-foreground" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    {/* Name */}
                    <div className="flex items-center gap-2 mb-1" data-testid={`${dataTestId}-header`}>
                        <span className="px-2 py-0.5 text-xs font-mono font-medium rounded bg-muted/10 text-muted-foreground flex-shrink-0">
                            {theme.identifier}
                        </span>
                        <h3 className="text-base font-semibold text-foreground" data-testid={`${dataTestId}-name`}>
                            {theme.name}
                        </h3>
                    </div>

                    {/* Description */}
                    {theme.description && (
                        <p
                            className={`text-sm text-muted-foreground ${isExpanded ? '' : 'line-clamp-2'}`}
                            data-testid={`${dataTestId}-description`}
                        >
                            {theme.description}
                        </p>
                    )}

                    {/* Stats Section */}
                    <div className="flex flex-wrap gap-4 mt-3" data-testid={`${dataTestId}-metadata`}>
                        {/* Hero Count */}
                        <div className="flex items-center gap-1.5" data-testid={`${dataTestId}-hero-count`}>
                            <UserIcon className="w-3.5 h-3.5 text-primary" />
                            <span className="text-xs text-muted-foreground">
                                <span className="font-medium text-foreground">{displayHeroCount}</span> hero{displayHeroCount !== 1 ? 'es' : ''}
                            </span>
                        </div>
                        {/* Villain Count */}
                        <div className="flex items-center gap-1.5" data-testid={`${dataTestId}-villain-count`}>
                            <SkullIcon className="w-3.5 h-3.5 text-destructive" />
                            <span className="text-xs text-muted-foreground">
                                <span className={`font-medium ${displayVillainCount > 0 ? 'text-destructive' : 'text-foreground'}`}>{displayVillainCount}</span> villain{displayVillainCount !== 1 ? 's' : ''}
                            </span>
                        </div>
                        {/* Outcome Count */}
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
            {isExpanded && theme.description && (
                <div className="mt-4 pt-4 border-t border-border ml-12" data-testid={`${dataTestId}-expanded`}>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">Full Description</h4>
                    <p className="text-sm text-foreground leading-relaxed">
                        {theme.description}
                    </p>
                </div>
            )}
        </Card>
    );
};

export default RoadmapThemeCard;
