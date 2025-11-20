import React from 'react';
import { ConflictDto, ConflictStatus, HeroDto, VillainDto } from '#types';
import ItemView from '#components/reusable/ItemView';

/**
 * Props for ConflictDetail component.
 */
export interface ConflictDetailProps {
    conflict: ConflictDto | null;
    hero?: HeroDto;
    villain?: VillainDto;
    loading: boolean;
    error: string | null;
    onDelete?: () => void;
    onRefresh?: () => void;
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
            return 'bg-muted text-muted-foreground';
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
 * Format date string for display.
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

/**
 * ConflictDetail component displays full conflict profile in read-only view.
 * @param {ConflictDetailProps} props - Component props
 * @returns {React.ReactElement} The ConflictDetail component
 */
const ConflictDetail: React.FC<ConflictDetailProps> = ({
    conflict,
    hero,
    villain,
    loading,
    error,
    onDelete,
    onRefresh,
    className,
    dataTestId = 'conflict-detail',
}) => {
    // Use provided hero/villain or fallback to conflict data
    const heroData = hero || conflict?.hero;
    const villainData = villain || conflict?.villain;

    return (
        <ItemView
            identifier={conflict?.identifier}
            status={conflict?.status}
            loading={loading}
            isEntityLocked={false}
            error={error}
            createdAt={conflict?.created_at}
            updatedAt={conflict?.updated_at}
            onDelete={onDelete || (() => {})}
            onRefresh={onRefresh}
            className={className}
            dataTestId={dataTestId}
        >
            {loading && (
                <div className="p-6 text-center text-muted-foreground">
                    Loading conflict...
                </div>
            )}

            {!loading && conflict && (
                <div className="space-y-6 p-6">
                    {/* Status Badge */}
                    <div className="flex items-center gap-2">
                        <span
                            className={`px-3 py-1 rounded text-sm font-medium ${getStatusBadgeClasses(
                                conflict.status
                            )}`}
                        >
                            {formatStatus(conflict.status)}
                        </span>
                    </div>

                    {/* Hero vs Villain Section */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4 bg-muted rounded-lg">
                        {/* Hero */}
                        <div className="space-y-2">
                            <h3 className="text-sm font-semibold text-muted-foreground uppercase">
                                Hero
                            </h3>
                            <div className="space-y-1">
                                <div className="font-medium text-lg">
                                    {heroData?.name || (
                                        <span className="text-muted-foreground italic">
                                            Unknown Hero
                                        </span>
                                    )}
                                </div>
                                {heroData?.identifier && (
                                    <div className="text-sm text-muted-foreground font-mono">
                                        {heroData.identifier}
                                    </div>
                                )}
                                {heroData?.description && (
                                    <div className="text-sm text-foreground mt-2">
                                        {heroData.description}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* VS Separator */}
                        <div className="flex items-center justify-center">
                            <div className="px-4 py-2 rounded-full bg-background text-foreground font-bold">
                                VS
                            </div>
                        </div>

                        {/* Villain */}
                        <div className="space-y-2">
                            <h3 className="text-sm font-semibold text-muted-foreground uppercase">
                                Villain
                            </h3>
                            <div className="space-y-1">
                                <div className="font-medium text-lg">
                                    {villainData?.name || (
                                        <span className="text-muted-foreground italic">
                                            Unknown Villain
                                        </span>
                                    )}
                                </div>
                                {villainData?.identifier && (
                                    <div className="text-sm text-muted-foreground font-mono">
                                        {villainData.identifier}
                                    </div>
                                )}
                                {villainData?.description && (
                                    <div className="text-sm text-foreground mt-2">
                                        {villainData.description}
                                    </div>
                                )}
                                {villainData?.severity && (
                                    <div className="text-sm text-muted-foreground mt-2">
                                        Severity: {villainData.severity}/5
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Conflict Description */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-semibold text-muted-foreground uppercase">
                            Conflict Description
                        </h3>
                        <div className="text-foreground whitespace-pre-wrap">
                            {conflict.description}
                        </div>
                    </div>

                    {/* Story Arc (if linked) */}
                    {conflict.story_arc && (
                        <div className="space-y-2">
                            <h3 className="text-sm font-semibold text-muted-foreground uppercase">
                                Story Arc
                            </h3>
                            <div className="p-3 bg-muted rounded">
                                <div className="font-medium">{conflict.story_arc.title}</div>
                                <div className="text-sm text-muted-foreground font-mono">
                                    {conflict.story_arc.identifier}
                                </div>
                                {conflict.story_arc.description && (
                                    <div className="text-sm text-foreground mt-2">
                                        {conflict.story_arc.description}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Resolution Details (if resolved) */}
                    {conflict.status === ConflictStatus.RESOLVED && (
                        <div className="space-y-2">
                            <h3 className="text-sm font-semibold text-success uppercase">
                                Resolution Details
                            </h3>
                            <div className="p-3 bg-success/10 rounded space-y-2">
                                {conflict.resolved_at && (
                                    <div className="text-sm">
                                        <span className="text-muted-foreground">
                                            Resolved on:{' '}
                                        </span>
                                        <span className="text-foreground font-medium">
                                            {formatDate(conflict.resolved_at)}
                                        </span>
                                    </div>
                                )}
                                {conflict.resolved_by_initiative && (
                                    <div className="text-sm">
                                        <span className="text-muted-foreground">
                                            Resolved by:{' '}
                                        </span>
                                        <span className="text-foreground font-medium">
                                            {conflict.resolved_by_initiative.title}
                                        </span>
                                        <span className="text-muted-foreground font-mono ml-2">
                                            {conflict.resolved_by_initiative.identifier}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {!loading && !conflict && !error && (
                <div className="p-6 text-center text-muted-foreground">
                    No conflict data available
                </div>
            )}
        </ItemView>
    );
};

export default ConflictDetail;
