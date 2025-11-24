import React from 'react';
import { Flame } from 'lucide-react';
import { ConflictsStakesSectionProps } from '#types/storyArc';

/**
 * ConflictsStakesSection displays active conflicts and stakes for a story arc.
 * Shows conflict cards with status, progress, and affected beats.
 * @param {ConflictsStakesSectionProps} props - Component props
 * @returns {React.ReactElement} The ConflictsStakesSection component
 */
const ConflictsStakesSection: React.FC<ConflictsStakesSectionProps> = ({
    conflicts,
    arcId,
    onAddConflict,
}) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'RESOLVED':
                return 'bg-success text-success-foreground';
            case 'RESOLVING':
                return 'bg-status-in-progress text-status-in-progress-foreground';
            case 'OPEN':
                return 'bg-status-todo text-status-todo-foreground';
            case 'ESCALATING':
                return 'bg-destructive text-destructive-foreground';
            default:
                return 'bg-muted text-muted-foreground';
        }
    };

    return (
        <div className="border border-border rounded-lg p-6 bg-background">
            <h2 className="text-lg font-semibold text-foreground mb-6">Conflicts & Stakes</h2>

            {/* Conflicts Subsection */}
            <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-semibold text-foreground">
                        Conflicts ({conflicts.length})
                    </h3>
                    <button
                        disabled
                        onClick={onAddConflict}
                        className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Coming soon"
                    >
                        + Add Conflict
                    </button>
                </div>

                {conflicts.length === 0 ? (
                    <div className="border border-border rounded-lg p-6 bg-muted/20 text-center">
                        <p className="text-sm text-muted-foreground">
                            No conflicts defined. What obstacles does this arc overcome?
                        </p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {conflicts.map((conflict) => (
                            <div
                                key={conflict.id}
                                className="border border-border rounded-lg p-4 hover:bg-accent/30 transition-colors"
                            >
                                <div className="flex items-start gap-3">
                                    <Flame className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-2 mb-2">
                                            <h4 className="text-sm font-semibold text-foreground">
                                                {conflict.identifier}
                                            </h4>
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(conflict.status)}`}>
                                                {conflict.status}
                                            </span>
                                        </div>
                                        <p className="text-sm text-muted-foreground mb-3">
                                            {conflict.description}
                                        </p>

                                        {/* Hero vs Villain */}
                                        {(conflict.hero || conflict.villain) && (
                                            <div className="text-xs text-muted-foreground">
                                                {conflict.hero?.name || 'Unknown Hero'} vs {conflict.villain?.name || 'Unknown Villain'}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Stakes Subsection */}
            <div>
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-semibold text-foreground">Stakes</h3>
                    <button
                        disabled
                        className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Coming soon"
                    >
                        Edit
                    </button>
                </div>

                <div className="border border-border rounded-lg p-6 bg-muted/20 space-y-3">
                    <div>
                        <span className="text-sm font-medium text-foreground">Success: </span>
                        <span className="text-sm text-muted-foreground italic">(undefined - coming soon)</span>
                    </div>
                    <div>
                        <span className="text-sm font-medium text-foreground">Failure: </span>
                        <span className="text-sm text-muted-foreground italic">(undefined - coming soon)</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ConflictsStakesSection;
