import React from 'react';
import { HeroDto } from '#types';
import ItemView from '../reusable/ItemView';

export interface HeroDetailProps {
    hero: HeroDto | null;
    loading: boolean;
    error: string | null;
    onDelete?: () => void;
    onRefresh?: () => void;
    className?: string;
    dataTestId?: string;
}

/**
 * HeroDetail component displays the full profile of a hero (user persona).
 * Uses ItemView wrapper for consistent layout with other detail views.
 * @param {HeroDetailProps} props - The component props
 * @returns {React.ReactElement} The HeroDetail component
 */
const HeroDetail: React.FC<HeroDetailProps> = ({
    hero,
    loading,
    error,
    onDelete = () => {},
    onRefresh,
    className,
    dataTestId = 'hero-detail',
}) => {
    if (loading) {
        return (
            <div className="p-8 text-center" data-testid={`${dataTestId}-loading`}>
                <div className="text-muted-foreground">Loading hero...</div>
            </div>
        );
    }

    if (!hero) {
        return (
            <div className="p-8 text-center" data-testid={`${dataTestId}-empty`}>
                <div className="text-muted-foreground">No hero data available</div>
            </div>
        );
    }

    return (
        <ItemView
            identifier={hero.identifier}
            status={hero.is_primary ? 'PRIMARY' : 'SECONDARY'}
            loading={loading}
            isEntityLocked={false}
            error={error}
            createdAt={hero.created_at}
            updatedAt={hero.updated_at}
            onDelete={onDelete}
            onRefresh={onRefresh}
            className={className}
            dataTestId={dataTestId}
        >
            {/* Name */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-foreground" data-testid={`${dataTestId}-name`}>
                    {hero.name}
                </h1>
            </div>

            {/* Primary Badge */}
            {hero.is_primary && (
                <div className="mb-6">
                    <div>
                        <label className="text-xs text-muted-foreground block mb-1">Status</label>
                        <span
                            className="text-sm px-3 py-1.5 rounded border bg-primary/10 text-primary border-primary/20"
                            data-testid={`${dataTestId}-primary-badge`}
                        >
                            PRIMARY HERO
                        </span>
                    </div>
                </div>
            )}

            {/* Description */}
            <div className="mb-6">
                <label className="text-xs text-muted-foreground block mb-2">
                    Description
                </label>
                {hero.description ? (
                    <div
                        className="text-sm text-foreground whitespace-pre-wrap border border-border rounded p-4 bg-card"
                        data-testid={`${dataTestId}-description`}
                    >
                        {hero.description}
                    </div>
                ) : (
                    <div
                        className="text-sm text-muted-foreground italic border border-border rounded p-4 bg-card"
                        data-testid={`${dataTestId}-no-description`}
                    >
                        No description provided
                    </div>
                )}
            </div>
        </ItemView>
    );
};

export default HeroDetail;
