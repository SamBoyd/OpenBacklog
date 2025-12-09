import React from 'react';
import { HeroDto } from '#types';
import Card from '../reusable/Card';
import { CompactButton } from '#components/reusable/Button';
import { ChevronDownIcon, UserIcon, TargetIcon, SwordsIcon } from 'lucide-react';

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
 * Shows hero name, description, featured themes, and opposing villains.
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
            className={`border border-border p-5 transition-colors ${onClick ? 'cursor-pointer hover:bg-accent/30' : ''} ${className}`}
            onClick={onClick}
            dataTestId={dataTestId}
        >
            {/* Header: Icon, Name, Badge, and Expand Button */}
            <div className="flex items-start gap-4">
                {/* Hero Icon */}
                <div className="p-2 rounded-lg bg-primary/10 flex-shrink-0">
                    <UserIcon className="w-5 h-5 text-primary" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    {/* Name and Primary Badge */}
                    <div className="flex items-center gap-2 mb-1" data-testid={`${dataTestId}-header`}>
                        <h3 className="text-base font-semibold text-foreground truncate" data-testid={`${dataTestId}-name`}>
                            {hero.name}
                        </h3>
                        {hero.is_primary && (
                            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-primary/20 text-primary flex-shrink-0">
                                Primary
                            </span>
                        )}
                    </div>

                    {/* Description */}
                    {hero.description && (
                        <p
                            className={`text-sm text-muted-foreground ${isExpanded ? '' : 'line-clamp-2'}`}
                            data-testid={`${dataTestId}-description`}
                        >
                            {hero.description}
                        </p>
                    )}

                    {/* Stats Section */}
                    <div className="flex flex-wrap gap-4 mt-3" data-testid={`${dataTestId}-stats`}>
                        <div className="flex items-center gap-1.5" data-testid={`${dataTestId}-roadmapTheme-count`}>
                            <TargetIcon className="w-3.5 h-3.5 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                                <span className="font-medium text-foreground">{roadmapThemeCount}</span> theme{roadmapThemeCount !== 1 ? 's' : ''}
                            </span>
                        </div>
                        <div className="flex items-center gap-1.5" data-testid={`${dataTestId}-villain-count`}>
                            <SwordsIcon className="w-3.5 h-3.5 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                                <span className={`font-medium ${villainCount > 0 ? 'text-destructive' : 'text-foreground'}`}>{villainCount}</span> villain{villainCount !== 1 ? 's' : ''}
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
            {isExpanded && hero.description && (
                <div className="mt-4 pt-4 border-t border-border ml-12" data-testid={`${dataTestId}-expanded`}>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">Full Description</h4>
                    <p className="text-sm text-foreground leading-relaxed">
                        {hero.description}
                    </p>
                </div>
            )}
        </Card>
    );
};

export default NarrativeHeroCard;
