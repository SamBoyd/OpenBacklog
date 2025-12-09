import React from 'react';
import Card from '#components/reusable/Card';
import { BookOpenIcon } from 'lucide-react';

/**
 * Props for NarrativeSummaryCard component.
 */
export interface NarrativeSummaryCardProps {
    /**
     * The narrative summary text content
     */
    summary: string;
    /**
     * Narrative health percentage (0-100)
     */
    healthPercentage?: number;
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
 * Returns health status color based on percentage.
 * @param {number} percentage - Health percentage (0-100)
 * @returns {string} Tailwind color class
 */
const getHealthColor = (percentage: number): string => {
    if (percentage >= 80) return 'text-success';
    if (percentage >= 50) return 'text-amber-500';
    return 'text-destructive';
};

/**
 * Returns health bar color based on percentage.
 * @param {number} percentage - Health percentage (0-100)
 * @returns {string} Tailwind background color class
 */
const getHealthBarColor = (percentage: number): string => {
    if (percentage >= 80) return 'bg-success';
    if (percentage >= 50) return 'bg-amber-500';
    return 'bg-destructive';
};

/**
 * Returns health status label based on percentage.
 * @param {number} percentage - Health percentage (0-100)
 * @returns {string} Status label
 */
const getHealthLabel = (percentage: number): string => {
    if (percentage >= 80) return 'Healthy';
    if (percentage >= 50) return 'Needs Attention';
    return 'At Risk';
};

/**
 * NarrativeSummaryCard displays the product narrative summary with health indicator.
 * @param {NarrativeSummaryCardProps} props - Component props
 * @returns {React.ReactElement} The NarrativeSummaryCard component
 */
const NarrativeSummaryCard: React.FC<NarrativeSummaryCardProps> = ({
    summary,
    healthPercentage = 72,
    className = '',
    dataTestId = 'narrative-summary-card',
}) => {
    const healthColor = getHealthColor(healthPercentage);
    const healthBarColor = getHealthBarColor(healthPercentage);
    const healthLabel = getHealthLabel(healthPercentage);

    return (
        <Card
            className={`border border-border p-6 ${className}`}
            dataTestId={dataTestId}
        >
            {/* Header Section */}
            <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                        <BookOpenIcon className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-foreground" data-testid={`${dataTestId}-title`}>
                            Product Narrative
                        </h2>
                        <p className="text-sm text-muted-foreground">The story we're telling</p>
                    </div>
                </div>

                {/* Narrative Health Section */}
                <div className="flex flex-col items-end gap-1">
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">Narrative Health</span>
                        <span className={`text-sm font-semibold ${healthColor}`} data-testid={`${dataTestId}-health-percentage`}>
                            {healthPercentage}%
                        </span>
                    </div>
                    <div className="w-32 h-1.5 bg-muted/10 rounded-full overflow-hidden" data-testid={`${dataTestId}-health-bar`}>
                        <div
                            className={`h-full ${healthBarColor} transition-all duration-300`}
                            style={{ width: `${healthPercentage}%` }}
                        />
                    </div>
                    <span className={`text-xs ${healthColor}`}>{healthLabel}</span>
                </div>
            </div>

            {/* Summary Text */}
            {summary ? (
                <div className="prose prose-sm max-w-none" data-testid={`${dataTestId}-summary`}>
                    <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                        {summary}
                    </p>
                </div>
            ) : (
                <div className="text-center py-8 text-muted-foreground" data-testid={`${dataTestId}-empty`}>
                    <p className="text-sm">No narrative summary defined yet.</p>
                    <p className="text-xs mt-1">Add heroes, villains, and themes to build your product story.</p>
                </div>
            )}
        </Card>
    );
};

export default NarrativeSummaryCard;
