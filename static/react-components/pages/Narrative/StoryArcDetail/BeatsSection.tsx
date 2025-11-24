import React from 'react';
import { CheckCircle, Circle } from 'lucide-react';
import { BeatsSectionProps } from '#types/storyArc';

/**
 * BeatsSection displays the list of story beats (initiatives) for a story arc.
 * Shows beat cards with status, progress, and actions.
 * @param {BeatsSectionProps} props - Component props
 * @returns {React.ReactElement} The BeatsSection component
 */
const BeatsSection: React.FC<BeatsSectionProps> = ({
    beats,
    arcId,
    isLoading = false,
    onViewBeat,
    onAddBeat,
}) => {
    const getStatusBadge = (beat: BeatsSectionProps['beats'][0]) => {
        if (beat.status === 'done') {
            return (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-status-done/10 text-status-done text-xs font-medium">
                    <CheckCircle className="w-3 h-3" />
                    Complete
                </span>
            );
        }

        if (beat.status === 'in_progress') {
            const completedTasks = beat.tasks.filter(t => t.status === 'DONE').length;
            const totalTasks = beat.tasks.length;
            const percent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

            return (
                <span className="px-2 py-1 rounded bg-status-in-progress/10 text-status-in-progress text-xs font-medium">
                    In Progress {percent}%
                </span>
            );
        }

        return (
            <span className="px-2 py-1 rounded bg-status-todo/10 text-status-todo text-xs font-medium">
                Planned
            </span>
        );
    };

    if (isLoading) {
        return (
            <div className="border border-border rounded-lg p-6 bg-background">
                <h2 className="text-lg font-semibold text-foreground mb-6">Beats</h2>
                <div className="text-center py-12 text-muted-foreground">
                    Loading beats...
                </div>
            </div>
        );
    }

    return (
        <div className="border border-border rounded-lg p-6 bg-background">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-foreground">Beats</h2>
                <button
                    disabled
                    onClick={onAddBeat}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Coming soon"
                >
                    + Add Beat
                </button>
            </div>

            {beats.length === 0 ? (
                <div className="border border-border rounded-lg p-8 bg-muted/20 text-center">
                    <p className="text-sm text-muted-foreground">
                        No beats defined. Break this arc into major milestones.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {beats.map((beat, index) => {
                        const completedScenes = beat.tasks.filter(t => t.status === 'DONE').length;
                        const totalScenes = beat.tasks.length;

                        return (
                            <div
                                key={beat.id}
                                className="border border-border rounded-lg p-4 bg-card hover:shadow-md transition-shadow"
                            >
                                {/* Circle Number */}
                                <div className="flex items-start gap-3 mb-3">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-bold">
                                        {index + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h3 className="text-sm font-bold text-foreground line-clamp-2 mb-2">
                                            {beat.title}
                                        </h3>
                                        {getStatusBadge(beat)}
                                    </div>
                                </div>

                                {/* Scenes Progress */}
                                <div className="mb-3">
                                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                                        <span>Scenes:</span>
                                        <span>{completedScenes} / {totalScenes} complete</span>
                                    </div>
                                    {totalScenes > 0 && (
                                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-success transition-all duration-300"
                                                style={{ width: `${(completedScenes / totalScenes) * 100}%` }}
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Action Buttons */}
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => onViewBeat(beat.initiativeId)}
                                        className="flex-1 px-3 py-1.5 bg-primary text-primary-foreground rounded text-xs font-medium hover:opacity-90 transition-opacity"
                                    >
                                        View Beat
                                    </button>
                                    <button
                                        disabled
                                        className="flex-1 px-3 py-1.5 bg-secondary text-secondary-foreground rounded text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                                        title="Coming soon"
                                    >
                                        View Scenes
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default BeatsSection;
