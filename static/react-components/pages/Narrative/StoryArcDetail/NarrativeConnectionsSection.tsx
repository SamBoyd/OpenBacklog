import React from 'react';
import { User, AlertTriangle, Star } from 'lucide-react';
import { NarrativeConnectionsSectionProps } from '#types/storyArc';

/**
 * NarrativeConnectionsSection displays relationships between hero, villains, and themes.
 * Shows hero card, villain cards with impact levels, and theme cards.
 * @param {NarrativeConnectionsSectionProps} props - Component props
 * @returns {React.ReactElement} The NarrativeConnectionsSection component
 */
const NarrativeConnectionsSection: React.FC<NarrativeConnectionsSectionProps> = ({
    hero,
    villains,
    themes,
    onEditLinks,
}) => {
    const getImpactColor = (impact?: string) => {
        switch (impact?.toLowerCase()) {
            case 'high':
                return 'bg-destructive text-destructive-foreground';
            case 'medium':
                return 'bg-status-in-progress text-status-in-progress-foreground';
            case 'low':
                return 'bg-status-todo text-status-todo-foreground';
            default:
                return 'bg-muted text-muted-foreground';
        }
    };

    return (
        <div className="border border-border rounded-lg p-6 bg-background">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-foreground">Narrative Connections</h2>
                <button
                    disabled
                    onClick={onEditLinks}
                    className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Coming soon"
                >
                    Edit Links
                </button>
            </div>

            <div className="space-y-6">
                {/* Hero Card */}
                <div>
                    <h3 className="text-base font-semibold text-foreground mb-3">Hero</h3>
                    {hero ? (
                        <div className="border border-border rounded-lg p-4 bg-card">
                            <div className="flex items-start gap-3">
                                <User className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <h4 className="text-sm font-semibold text-foreground">{hero.name}</h4>
                                        {hero.is_primary && (
                                            <span className="px-2 py-1 rounded bg-primary/10 text-primary text-xs font-medium">
                                                Primary
                                            </span>
                                        )}
                                    </div>
                                    {hero.description && (
                                        <p className="text-sm text-muted-foreground mb-3">
                                            {hero.description}
                                        </p>
                                    )}
                                    <button
                                        disabled
                                        className="text-sm text-primary hover:underline disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline"
                                        title="Coming soon"
                                    >
                                        View Hero Detail →
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="border border-border rounded-lg p-6 bg-muted/20 text-center">
                            <p className="text-sm text-muted-foreground">No Hero defined for this arc</p>
                        </div>
                    )}
                </div>

                {/* Villains */}
                <div>
                    <h3 className="text-base font-semibold text-foreground mb-3">
                        Villains ({villains.length})
                    </h3>
                    {villains.length === 0 ? (
                        <div className="border border-border rounded-lg p-6 bg-muted/20 text-center">
                            <p className="text-sm text-muted-foreground">
                                No Villains identified – what problems does this solve?
                            </p>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-3">
                            {villains.map((villain) => (
                                <div
                                    key={villain.id}
                                    className="border border-border rounded-lg p-4 bg-card hover:bg-accent/30 transition-colors"
                                >
                                    <div className="flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-2 mb-2">
                                                <h4 className="text-sm font-semibold text-foreground">{villain.name}</h4>
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${villain.severity >= 7 ? 'bg-destructive text-destructive-foreground' : villain.severity >= 4 ? 'bg-status-in-progress text-status-in-progress-foreground' : 'bg-status-todo text-status-todo-foreground'}`}>
                                                    {villain.villain_type}
                                                </span>
                                            </div>
                                            {villain.description && (
                                                <p className="text-sm text-muted-foreground mb-3">
                                                    {villain.description}
                                                </p>
                                            )}
                                            <button
                                                disabled
                                                className="text-sm text-primary hover:underline disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline"
                                                title="Coming soon"
                                            >
                                                View Villain Detail →
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Themes */}
                <div>
                    <h3 className="text-base font-semibold text-foreground mb-3">
                        Themes ({themes.length})
                    </h3>
                    {themes.length === 0 ? (
                        <div className="border border-border rounded-lg p-6 bg-muted/20 text-center">
                            <p className="text-sm text-muted-foreground">No Themes connected to this arc</p>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-3">
                            {themes.map((theme) => (
                                <div
                                    key={theme.id}
                                    className="border border-border rounded-lg p-4 bg-card hover:bg-accent/30 transition-colors"
                                >
                                    <div className="flex items-start gap-3">
                                        <Star className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-sm font-semibold text-foreground mb-2">{theme.name}</h4>
                                            {theme.description && (
                                                <p className="text-sm text-muted-foreground">
                                                    {theme.description}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NarrativeConnectionsSection;
