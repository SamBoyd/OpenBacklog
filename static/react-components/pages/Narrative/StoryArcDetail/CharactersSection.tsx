import React from 'react';
import { Users, User, Skull } from 'lucide-react';
import { CharactersSectionProps } from '#types/storyArc';

/**
 * CharactersSection displays the hero and villains linked to the theme.
 * Provides quick access buttons to view character details.
 *
 * @param {CharactersSectionProps} props - Component props
 * @returns {React.ReactElement} The characters section
 */
const CharactersSection: React.FC<CharactersSectionProps> = ({
  hero,
  villains,
  onViewHero,
  onViewVillain,
}) => {
  const handleViewHero = () => {
    if (hero && onViewHero) {
      onViewHero(hero.id);
    }
  };

  const handleViewVillain = (villainId: string) => {
    if (onViewVillain) {
      onViewVillain(villainId);
    }
  };

  const hasCharacters = hero || villains.length > 0;

  return (
    <div className="border border-border rounded-lg bg-card p-6">
      {/* Section Header */}
      <div className="flex items-center gap-2 mb-4">
        <Users className="w-5 h-5 text-primary" />
        <h3 className="text-base font-semibold text-foreground">Characters</h3>
      </div>

      {hasCharacters ? (
        <div className="flex flex-row gap-x-2 gap-y-2">
          {/* Hero */}
          {hero && (
            <div className="min-w-80 w-1/2">
              <h4 className="text-xs font-medium text-muted-foreground uppercase mb-2">Hero</h4>
              <button
                onClick={handleViewHero}
                className="w-full text-left p-3 border border-border rounded-lg bg-card hover:bg-accent/50 transition-colors group"
              >
                <div className="flex items-start gap-2">
                  <User className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h5 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                      {hero.name}
                    </h5>
                    {hero.description && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                        {hero.description}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            </div>
          )}

          {/* Villains */}
          {villains.length > 0 && (
            <div className="min-w-80 w-1/2">
              <h4 className="text-xs font-medium text-muted-foreground uppercase mb-2">
                Villains ({villains.length})
              </h4>
              <div className="space-y-2">
                {villains.map(villain => (
                  <button
                    key={villain.id}
                    onClick={() => handleViewVillain(villain.id)}
                    className="w-full text-left p-3 border border-border rounded-lg bg-card hover:bg-accent/50 transition-colors group"
                  >
                    <div className="flex items-start gap-2">
                      <Skull className="w-4 h-4 text-destructive mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h5 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                            {villain.name}
                          </h5>
                          <span className="text-xs text-muted-foreground">
                            Severity: {villain.severity}/10
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {villain.description}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-6">
          <Users className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">No characters linked yet</p>
        </div>
      )}
    </div>
  );
};

export default CharactersSection;
