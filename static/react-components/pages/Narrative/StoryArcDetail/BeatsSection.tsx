import React from 'react';
import { CheckCircle, Circle, Clock, EyeIcon, ListTodo } from 'lucide-react';
import { BeatsSectionProps } from '#types/storyArc';
import { NoBorderButton } from '#components/reusable/Button';

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
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-status-done/10 text-status-done text-xs font-medium">
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
                <span className="inline-flex items-center gap-1 px-2.5 py-1  rounded bg-status-in-progress/10 text-status-in-progress text-xs font-medium">
                    <Clock className='w-3 h-3' /> In Progress {percent}%
                </span>
            );
        }

        return (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-status-todo/10 text-muted-foreground text-xs font-medium">
                <Circle className='w-3 h-3' /> Planned
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
                <div className="flex flex-col gap-4">
                    {beats.map((beat, index) => {
                        const completedScenes = beat.tasks.filter(t => t.status === 'DONE').length;
                        const totalScenes = beat.tasks.length;

                        return (
                            <div
                                key={beat.id}
                                className="border border-border rounded-lg p-4 bg-card hover:shadow-md transition-shadow flex flex-col gap-2"
                            >
                                {/* Circle Number */}
                                <div className="flex flex-row items-start gap-3">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-sm font-bold">
                                        {index + 1}
                                    </div>

                                    <div className="flex flex-col gap-2">
                                        <div className="flex items-center h-8 ">
                                        <h3 className="text-sm font-bold text-foreground line-clamp-2">
                                                {beat.title}
                                            </h3>
                                        </div>

                                        {/* Initiative Description */}
                                        <div className="text-xs text-muted-foreground line-clamp-2">
                                            {beat.description}
                                        </div>

                                        {/* Scenes Progress */}
                                        <div className="flex items-center justify-start text-xs text-muted-foreground gap-x-2">
                                            {getStatusBadge(beat)}

                                            <span>Scenes: {completedScenes} / {totalScenes} complete</span>
                                        </div>

                                        {/* Action Buttons */}
                                        <div className="flex gap-2">
                                            <NoBorderButton
                                                onClick={() => onViewBeat(beat.initiativeId)}
                                                className="text-xs"
                                            >
                                                <EyeIcon className="w-4 h-4" /> View Beat
                                            </NoBorderButton>
                                            <NoBorderButton
                                                disabled
                                                title="Coming soon"
                                                onClick={() => { }}
                                                className="text-xs"
                                            >
                                                <ListTodo className='w-4 h-4'/>
                                                View Scenes
                                            </NoBorderButton>
                                        </div>
                                    </div>
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
