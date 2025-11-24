import React from 'react';
import { MetricsSectionProps } from '#types/storyArc';

/**
 * MetricsSection displays quantitative progress and health metrics for a story arc.
 * Shows completion percentage, scenes progress, beats breakdown, and timeline.
 * @param {MetricsSectionProps} props - Component props
 * @returns {React.ReactElement} The MetricsSection component
 */
const MetricsSection: React.FC<MetricsSectionProps> = ({
    completionPercent,
    scenesComplete,
    scenesTotal,
    beatsComplete,
    beatsInProgress,
    beatsPlanned,
    startDate,
    lastActivityDate,
}) => {
    const totalBeats = beatsComplete + beatsInProgress + beatsPlanned;

    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        } catch {
            return dateString;
        }
    };

    return (
        <div className="border border-border rounded-lg p-6 bg-background">
            <h2 className="text-lg font-semibold text-foreground mb-6">Metrics</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Completion Progress */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Completion</span>
                        <span className="text-sm font-semibold text-foreground">{completionPercent}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${completionPercent}%` }}
                        />
                    </div>
                </div>

                {/* Scenes Progress */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Scenes</span>
                        <span className="text-sm font-semibold text-foreground">
                            {scenesComplete} / {scenesTotal} complete
                        </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                            className="h-full bg-success transition-all duration-300"
                            style={{ width: `${scenesTotal > 0 ? (scenesComplete / scenesTotal) * 100 : 0}%` }}
                        />
                    </div>
                </div>

                {/* Beats Breakdown */}
                <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Beats Breakdown</span>
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Complete</span>
                            <span className="font-medium text-success">{beatsComplete} / {totalBeats}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">In Progress</span>
                            <span className="font-medium text-status-in-progress">{beatsInProgress} / {totalBeats}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Planned</span>
                            <span className="font-medium text-status-todo">{beatsPlanned} / {totalBeats}</span>
                        </div>
                    </div>
                </div>

                {/* Timeline */}
                <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Timeline</span>
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Started</span>
                            <span className="font-medium text-foreground">{formatDate(startDate)}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Last Activity</span>
                            <span className="font-medium text-foreground">{formatDate(lastActivityDate)}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer Note */}
            <div className="mt-6 pt-4 border-t border-border">
                <p className="text-xs text-muted-foreground italic">
                    Additional metrics will be available when wired to analytics
                </p>
            </div>
        </div>
    );
};

export default MetricsSection;
