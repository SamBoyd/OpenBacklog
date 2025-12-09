import React from 'react';
import { HeroDto } from '#types';
import Card from '../reusable/Card';
import { CompactButton } from '#components/reusable/Button';
import { ChevronDownIcon } from 'lucide-react';

/**
 * Props for NarrativeHeroCard component.
 */
export interface NarrativeHeroCardProps {
    /**
     * The hero data to display
     */
    hero: HeroDto;
    /**
     * Number of roadmap themes this hero is featured in
     */
    roadmapThemeCount?: number;
    /**
     * Number of villains opposing this hero
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
 * NarrativeHeroCard displays a detailed hero card for the story bible.
 * Shows hero name, role, core promise, featured arcs, and opposing villains.
 * @param {NarrativeHeroCardProps} props - Component props
 * @returns {React.ReactElement} The NarrativeHeroCard component
 */
const NarrativeHeroCard: React.FC<NarrativeHeroCardProps> = ({
    hero,
    roadmapThemeCount = 0,
    villainCount = 0,
    isExpanded = false,
    onToggleExpand,
    onClick,
    className = '',
    dataTestId = 'narrative-hero-card',
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
            {/* Header: Name and Role */}
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1" data-testid={`${dataTestId}-header`}>
                    <h3 className="text-base font-semibold text-foreground mb-1" data-testid={`${dataTestId}-name`}>
                        {hero.name}
                    </h3>
                    <p className="text-sm text-muted-foreground" data-testid={`${dataTestId}-role`}>
                        {hero.description || 'No role specified'}
                    </p>
                </div>
                {/* Expand/Collapse Button */}
                <CompactButton
                    onClick={handleToggle}
                    className="p-2 rounded-lg text-muted-foreground hover:bg-accent/50 transition-colors flex-shrink-0"
                    data-testid={`${dataTestId}-expand-button`}
                >
                    <span className={`text-lg transform ${isExpanded ? 'rotate-180' : 'rotate-0'}`}>
                        <ChevronDownIcon />
                    </span>
                </CompactButton>
            </div>

            {/* Core Promise Section */}
            <div className="mb-4 pb-4 border-b border-border">
                <h4 className="text-xs font-medium text-muted-foreground mb-1">Core Promise:</h4>
                <p className="text-sm text-muted-foreground italic" data-testid={`${dataTestId}-core-promise`}>
                    {hero.description ? `"${hero.description.substring(0, 100)}"` : 'No core promise defined'}
                </p>
            </div>

            {/* Stats Section */}
            <div className="flex gap-4" data-testid={`${dataTestId}-stats`}>
                <div className="flex items-center gap-1" data-testid={`${dataTestId}-roadmapTheme-count`}>
                    <span className="text-xs text-muted-foreground">Featured in</span>
                    <span className="text-sm font-semibold text-foreground">{roadmapThemeCount} theme{roadmapThemeCount !== 1 ? 's' : ''}</span>
                </div>
                <div className="flex items-center gap-1" data-testid={`${dataTestId}-villain-count`}>
                    <span className="text-xs text-muted-foreground">Opposed by</span>
                    <span className="text-sm font-semibold text-destructive">
                        {villainCount} villain{villainCount !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && hero.description && (
                <div className="mt-4 pt-4 border-t border-border" data-testid={`${dataTestId}-expanded`}>
                    <p className="text-sm text-foreground leading-relaxed">
                        {hero.description}
                    </p>
                </div>
            )}
        </Card>
    );
};

export default NarrativeHeroCard;
