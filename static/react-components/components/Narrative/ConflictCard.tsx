import React from 'react';
import { ConflictDto, ConflictStatus, HeroDto, VillainDto } from '#types';
import Card from '#components/reusable/Card';

/**
 * Props for ConflictCard component.
 */
export interface ConflictCardProps {
    conflict: ConflictDto;
    hero?: HeroDto;
    villain?: VillainDto;
    onClick?: () => void;
    className?: string;
    dataTestId?: string;
}

/**
 * Get status badge color classes based on conflict status.
 * @param {ConflictStatus} status - The conflict status
 * @returns {string} Tailwind CSS classes for the badge
 */
function getStatusBadgeClasses(status: ConflictStatus): string {
    switch (status) {
        case ConflictStatus.OPEN:
            return 'bg-destructive text-destructive-foreground';
        case ConflictStatus.ESCALATING:
            return 'bg-amber-500 text-white';
        case ConflictStatus.RESOLVING:
            return 'bg-primary text-primary-foreground';
        case ConflictStatus.RESOLVED:
            return 'bg-success text-success-foreground';
        default:
            return 'bg-muted/10 text-muted-foreground';
    }
}

/**
 * Format status enum for display.
 * @param {ConflictStatus} status - The conflict status
 * @returns {string} Formatted status string
 */
function formatStatus(status: ConflictStatus): string {
    return status.charAt(0) + status.slice(1).toLowerCase().replace(/_/g, ' ');
}

/**
 * ConflictCard component displays a conflict summary showing hero vs villain tension.
 * @param {ConflictCardProps} props - Component props
 * @returns {React.ReactElement} The ConflictCard component
 */
const ConflictCard: React.FC<ConflictCardProps> = ({
    conflict,
    hero,
    villain,
    onClick,
    className = '',
    dataTestId = 'conflict-card',
}) => {
    // Use provided hero/villain or fallback to conflict data
    const heroData = hero || conflict.hero;
    const villainData = villain || conflict.villain;

    // Truncate description to first 100 characters
    const truncatedDescription =
        conflict.description.length > 100
            ? conflict.description.substring(0, 100) + '...'
            : conflict.description;

    return (
        <Card
            className={`border border-border p-4 hover:shadow-md transition-shadow ${
                onClick ? 'cursor-pointer' : ''
            } ${className}`}
            onClick={onClick}
            dataTestId={dataTestId}
        >
            {/* Header: Identifier and Status Badge */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-muted-foreground">
                        {conflict.identifier}
                    </span>
                    <span
                        className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeClasses(
                            conflict.status
                        )}`}
                    >
                        {formatStatus(conflict.status)}
                    </span>
                </div>
            </div>

            {/* Hero vs Villain Display */}
            <div className="flex items-center gap-3 mb-3">
                {/* Hero Section */}
                <div className="flex-1 text-left">
                    <div className="text-xs text-muted-foreground mb-1">Hero</div>
                    <div className="font-medium text-sm">
                        {heroData?.name || (
                            <span className="text-muted-foreground italic">
                                {conflict.hero_id.substring(0, 8)}...
                            </span>
                        )}
                    </div>
                    {heroData?.identifier && (
                        <div className="text-xs text-muted-foreground font-mono">
                            {heroData.identifier}
                        </div>
                    )}
                </div>

                {/* VS Separator */}
                <div className="flex-shrink-0">
                    <div className="px-3 py-1 rounded-full bg-muted/10 text-muted-foreground font-bold text-xs">
                        VS
                    </div>
                </div>

                {/* Villain Section */}
                <div className="flex-1 text-right">
                    <div className="text-xs text-muted-foreground mb-1">Villain</div>
                    <div className="font-medium text-sm">
                        {villainData?.name || (
                            <span className="text-muted-foreground italic">
                                {conflict.villain_id.substring(0, 8)}...
                            </span>
                        )}
                    </div>
                    {villainData?.identifier && (
                        <div className="text-xs text-muted-foreground font-mono">
                            {villainData.identifier}
                        </div>
                    )}
                </div>
            </div>

            {/* Conflict Description Preview */}
            <div className="text-sm text-foreground border-t border-border pt-3">
                {truncatedDescription}
            </div>
        </Card>
    );
};

export default ConflictCard;
