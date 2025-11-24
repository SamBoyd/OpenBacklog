import React from 'react';
import { ChevronRight, MoreHorizontal } from 'lucide-react';
import { HeaderSectionProps } from '#types/storyArc';

/**
 * HeaderSection displays the sticky header for the story arc detail page.
 * Shows breadcrumb, title, status, and action buttons.
 * @param {HeaderSectionProps} props - Component props
 * @returns {React.ReactElement} The HeaderSection component
 */
const HeaderSection: React.FC<HeaderSectionProps> = ({
    arcTitle,
    arcSubtitle,
    arcStatus = 'planning',
    onEditMode,
    onViewRoadmap,
    onShare,
    onLinkEntity,
    onDelete,
}) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'complete':
                return 'bg-status-done text-status-done-foreground';
            case 'climax':
                return 'bg-destructive text-destructive-foreground';
            case 'in_progress':
                return 'bg-status-in-progress text-status-in-progress-foreground';
            case 'planning':
                return 'bg-status-todo text-status-todo-foreground';
            case 'archived':
                return 'bg-muted text-muted-foreground';
            default:
                return 'bg-muted text-muted-foreground';
        }
    };

    const formatStatus = (status: string) => {
        return status
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    return (
        <div className="sticky top-0 z-50 bg-background border-b border-border">
            <div className="px-6 py-4">
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 mb-3">
                    <button className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                        Story Bible
                    </button>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    <button className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                        Arcs
                    </button>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-foreground font-medium">{arcTitle}</span>
                </div>

                {/* Title and Status */}
                <div className="flex items-start justify-between gap-4 mb-4">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                            <h1 className="text-2xl font-bold text-foreground truncate">{arcTitle}</h1>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(arcStatus)}`}>
                                {formatStatus(arcStatus)}
                            </span>
                        </div>
                        {arcSubtitle && (
                            <p className="text-sm text-muted-foreground">{arcSubtitle}</p>
                        )}
                    </div>
                </div>

                {/* Global Commands */}
                <div className="flex flex-wrap items-center gap-2">
                    <button
                        disabled
                        onClick={onEditMode}
                        className="px-3 py-1.5 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Coming soon"
                    >
                        Edit Mode
                    </button>
                    <button
                        onClick={onViewRoadmap}
                        className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                    >
                        View in Roadmap
                    </button>
                    <button
                        disabled
                        onClick={onShare}
                        className="px-3 py-1.5 border border-border bg-background text-foreground rounded-lg text-sm font-medium hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Coming soon"
                    >
                        Share/Export
                    </button>
                    <button
                        disabled
                        onClick={onLinkEntity}
                        className="px-3 py-1.5 border border-border bg-background text-foreground rounded-lg text-sm font-medium hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Coming soon"
                    >
                        Link Entity
                    </button>
                    <button
                        disabled
                        onClick={onDelete}
                        className="px-3 py-1.5 border border-border bg-background text-foreground rounded-lg text-sm font-medium hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Coming soon"
                    >
                        <MoreHorizontal className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default HeaderSection;
