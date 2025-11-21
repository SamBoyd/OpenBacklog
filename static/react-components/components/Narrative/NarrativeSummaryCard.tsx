import React from 'react';
import Card from '#components/reusable/Card';

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
     * Whether narrative needs attention
     */
    needsAttention?: boolean;
    /**
     * Callback when Edit button is clicked
     */
    onEdit?: () => void;
    /**
     * Callback when Regenerate button is clicked
     */
    onRegenerate?: () => void;
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
 * NarrativeSummaryCard displays the product narrative summary with health indicator.
 * @param {NarrativeSummaryCardProps} props - Component props
 * @returns {React.ReactElement} The NarrativeSummaryCard component
 */
const NarrativeSummaryCard: React.FC<NarrativeSummaryCardProps> = ({
    summary,
    healthPercentage = 72,
    needsAttention = true,
    onEdit,
    onRegenerate,
    className = '',
    dataTestId = 'narrative-summary-card',
}) => {
    return (
        <Card
            className={`border border-border p-6 ${className}`}
            dataTestId={dataTestId}
        >
            {/* Header Section */}
            <div className="flex items-start justify-between mb-6">
                <h2 className="text-base font-medium text-foreground" data-testid={`${dataTestId}-title`}>
                    What story are we telling?
                </h2>

                {/* Narrative Health Section */}
                <div className="text-right">
                    <div className="text-sm text-muted-foreground mb-1">Narrative Health</div>
                    <div className="flex items-end gap-2">
                        {/* Progress Bar */}
                        <div className="w-32 h-2 bg-muted rounded-full overflow-hidden" data-testid={`${dataTestId}-health-bar`}>
                            <div
                                className="h-full bg-foreground transition-all"
                                style={{ width: `${healthPercentage}%` }}
                            />
                        </div>
                        <div className="text-sm font-medium text-amber-500 min-w-fit" data-testid={`${dataTestId}-health-percentage`}>
                            {healthPercentage}%
                        </div>
                    </div>
                    {needsAttention && (
                        <div className="text-xs text-muted-foreground mt-1">Needs Attention</div>
                    )}
                </div>
            </div>

            {/* Summary Text */}
            <div className="prose prose-sm max-w-none mb-6" data-testid={`${dataTestId}-summary`}>
                <p className="text-base text-foreground leading-relaxed whitespace-pre-wrap">
                    {summary}
                </p>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2" data-testid={`${dataTestId}-actions`}>
                <button
                    onClick={onEdit}
                    className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-accent/50 transition-colors"
                    data-testid={`${dataTestId}-edit-button`}
                >
                    <span>✏️</span>
                    <span>Edit</span>
                </button>
                <button
                    onClick={onRegenerate}
                    className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-accent/50 transition-colors"
                    data-testid={`${dataTestId}-regenerate-button`}
                >
                    <span>🔄</span>
                    <span>Regenerate</span>
                </button>
            </div>
        </Card>
    );
};

export default NarrativeSummaryCard;
