import React from 'react';
import { HeroDto } from '#types';
import Card from '../reusable/Card';

export interface HeroCardProps {
    hero: HeroDto;
    onClick?: () => void;
    className?: string;
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
 * HeroCard component displays a summary card for a hero (user persona).
 * @param {HeroCardProps} props - The component props
 * @returns {React.ReactElement} The HeroCard component
 */
const HeroCard: React.FC<HeroCardProps> = ({
    hero,
    onClick,
    className = '',
    dataTestId = 'hero-card',
}) => {
    return (
        <Card
            className={`border border-border p-4 ${onClick ? 'cursor-pointer hover:bg-accent/50' : ''} ${className}`}
            onClick={onClick}
            dataTestId={dataTestId}
        >
            {/* Header with identifier and primary badge */}
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-mono text-muted-foreground" data-testid={`${dataTestId}-identifier`}>
                        {hero.identifier}
                    </span>
                    {hero.is_primary && (
                        <span
                            className="text-xs px-2 py-0.5 rounded border bg-primary/10 text-primary border-primary/20"
                            data-testid={`${dataTestId}-primary-badge`}
                        >
                            PRIMARY
                        </span>
                    )}
                </div>
            </div>

            {/* Name */}
            <h3 className="text-lg font-semibold text-foreground mb-2" data-testid={`${dataTestId}-name`}>
                {hero.name}
            </h3>

            {/* Description preview */}
            {hero.description && (
                <p className="text-sm text-muted-foreground line-clamp-2" data-testid={`${dataTestId}-description`}>
                    {truncateDescription(hero.description, 120)}
                </p>
            )}

            {!hero.description && (
                <p className="text-sm text-muted-foreground italic" data-testid={`${dataTestId}-no-description`}>
                    No description provided
                </p>
            )}
        </Card>
    );
};

export default HeroCard;
