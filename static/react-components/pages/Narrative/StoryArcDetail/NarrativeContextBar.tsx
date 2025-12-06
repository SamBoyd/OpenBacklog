import React from 'react';
import { NarrativeContextBarProps } from '#types/storyArc';

/**
 * NarrativeContextBar displays arc context at a glance in a sticky navigation bar.
 * Shows hero, villains, themes, progress, and health indicators.
 * @param {NarrativeContextBarProps} props - Component props
 * @returns {React.ReactElement} The NarrativeContextBar component
 */
const NarrativeContextBar: React.FC<NarrativeContextBarProps> = ({
    hero,
    villains,
    themes,
    progressPercent,
    healthPercent,
    onHeroClick,
    onVillainClick,
    onThemeClick,
}) => {
    const maxDisplayCount = 3;
    const displayVillains = villains.slice(0, maxDisplayCount);
    const remainingVillains = Math.max(0, villains.length - maxDisplayCount);

    const maxThemeDisplayCount = 2;
    const displayThemes = themes.slice(0, maxThemeDisplayCount);
    const remainingThemes = Math.max(0, themes.length - maxThemeDisplayCount);

    const getHealthColor = () => {
        if (healthPercent >= 80) return 'text-success';
        if (healthPercent >= 50) return 'text-status-in-progress';
        return 'text-destructive';
    };

    const getHealthDotColor = () => {
        if (healthPercent >= 80) return 'bg-success';
        if (healthPercent >= 50) return 'bg-status-in-progress';
        return 'bg-destructive';
    };

    return (
        <div className="sticky top-0 z-40 bg-background/95 backdrop-blur-sm border-b border-border">
            <div className="px-6 py-4">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
                    {/* Hero */}
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-muted-foreground">Hero:</span>
                        {hero ? (
                            <button
                                onClick={() => onHeroClick?.(hero.id)}
                                className="text-sm font-medium text-primary hover:underline disabled:opacity-70 disabled:cursor-not-allowed disabled:no-underline truncate"
                                title="Coming soon"
                            >
                                {hero.name}
                            </button>
                        ) : (
                            <span className="text-sm text-muted-foreground italic">None</span>
                        )}
                    </div>

                    {/* Villains */}
                    <div className="flex items-center gap-2 md:col-span-2">
                        <span className="text-xs font-medium text-muted-foreground flex-shrink-0">Villains:</span>
                        {villains.length === 0 ? (
                            <span className="text-sm text-muted-foreground italic">None</span>
                        ) : (
                            <div className="flex items-center gap-1 flex-wrap">
                                {displayVillains.map((villain, index) => (
                                    <React.Fragment key={villain.id}>
                                        <button
                                            onClick={() => onVillainClick?.(villain.id)}
                                            className="text-sm text-destructive hover:underline disabled:opacity-70 disabled:cursor-not-allowed disabled:no-underline truncate"
                                            title="Coming soon"
                                        >
                                            {villain.name}
                                        </button>
                                        {index < displayVillains.length - 1 && (
                                            <span className="text-muted-foreground">,</span>
                                        )}
                                    </React.Fragment>
                                ))}
                                {remainingVillains > 0 && (
                                    <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-medium ml-1">
                                        +{remainingVillains}
                                    </span>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Themes */}
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-muted-foreground flex-shrink-0">Themes:</span>
                        {themes.length === 0 ? (
                            <span className="text-sm text-muted-foreground italic">None</span>
                        ) : (
                            <div className="flex items-center gap-1 flex-wrap">
                                {displayThemes.map((theme, index) => (
                                    <React.Fragment key={theme.id}>
                                        <button
                                            onClick={() => onThemeClick?.(theme.id)}
                                            className="text-sm text-primary hover:underline disabled:opacity-70 disabled:cursor-not-allowed disabled:no-underline truncate"
                                            title="Coming soon"
                                        >
                                            {theme.name}
                                        </button>
                                        {index < displayThemes.length - 1 && (
                                            <span className="text-muted-foreground">,</span>
                                        )}
                                    </React.Fragment>
                                ))}
                                {remainingThemes > 0 && (
                                    <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-medium ml-1">
                                        +{remainingThemes}
                                    </span>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Progress & Health */}
                    <div className="flex items-center gap-4 md:justify-end">
                        {/* Progress */}
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-medium text-muted-foreground">Progress:</span>
                            <div className="flex items-center gap-1">
                                <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary transition-all duration-300"
                                        style={{ width: `${progressPercent}%` }}
                                    />
                                </div>
                                <span className="text-xs font-medium text-foreground">{progressPercent}%</span>
                            </div>
                        </div>

                        {/* Health */}
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-medium text-muted-foreground">Health:</span>
                            <div className="flex items-center gap-1">
                                <div className={`w-2 h-2 rounded-full ${getHealthDotColor()}`} />
                                <span className={`text-xs font-medium ${getHealthColor()}`}>
                                    {healthPercent}%
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NarrativeContextBar;
