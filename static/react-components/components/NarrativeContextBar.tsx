import React from 'react';
import { HeroDto, VillainDto } from '#types';
import { ThemeDto } from '#api/productStrategy';

export interface NarrativeContextBarProps {
  parentTheme?: ThemeDto;
  heroes: HeroDto[];
  villains: VillainDto[];
  progress: number; // 0-100
  scenesCount: { total: number; completed: number };
}

/**
 * NarrativeContextBar displays narrative context at the top of ViewStrategicInitiative
 * Shows parent theme, heroes, villains, and overall progress
 * @param {NarrativeContextBarProps} props - The component props
 * @returns {React.ReactElement} The NarrativeContextBar component
 */
const NarrativeContextBar: React.FC<NarrativeContextBarProps> = ({
  parentTheme,
  heroes,
  villains,
  progress,
  scenesCount,
}) => {
  return (
    <div className="bg-background border-b border-border px-6 py-4">
      <div className="max-w-7xl mx-auto">
        {/* Parent Theme Info */}
        {parentTheme && (
          <div className="mb-4">
            <p className="text-xs text-muted-foreground mb-2">THEME</p>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 text-xs font-mono font-medium rounded bg-muted/10 text-muted-foreground">
                {parentTheme.identifier}
              </span>
              <h2 className="text-lg font-semibold text-foreground">{parentTheme.name}</h2>
            </div>
            {parentTheme.description && (
              <p className="text-sm text-muted-foreground mt-1 line-clamp-1">
                {parentTheme.description}
              </p>
            )}
          </div>
        )}

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-medium text-muted-foreground">
              SCENES: {scenesCount.completed} of {scenesCount.total} completed
            </p>
            <span className="text-xs font-semibold text-foreground">{progress}%</span>
          </div>
          <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Heroes and Villains Grid */}
        {(heroes.length > 0 || villains.length > 0) && (
          <div className="grid grid-cols-auto gap-3">
            {/* Heroes */}
            {heroes.map((hero) => (
              <div key={hero.id} className="flex-shrink-0">
                <div className="text-xs text-muted-foreground mb-1">HERO</div>
                <div className="px-3 py-2 rounded border border-primary/20 bg-primary/5">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-xs font-mono font-medium text-primary">{hero.identifier}</span>
                    <p className="text-sm font-medium text-foreground">{hero.name}</p>
                  </div>
                  {hero.is_primary && (
                    <span className="text-xs text-primary font-semibold">Primary</span>
                  )}
                </div>
              </div>
            ))}

            {/* Villains */}
            {villains.map((villain) => (
              <div key={villain.id} className="flex-shrink-0">
                <div className="text-xs text-muted-foreground mb-1">OBSTACLE</div>
                <div className="px-3 py-2 rounded border border-destructive/20 bg-destructive/5">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="text-xs font-mono font-medium text-destructive">{villain.identifier}</span>
                    <p className="text-sm font-medium text-foreground">{villain.name}</p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Severity: {villain.severity}/5
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NarrativeContextBar;
