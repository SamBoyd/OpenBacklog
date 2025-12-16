import React from 'react';
import { ThemeDto } from '#api/productStrategy';
import { Eye, MoreHorizontal, ShieldAlert, UserRound, Target, Compass } from 'lucide-react';
import { Button, IconButton } from '#components/reusable/Button';

interface ThemeCardProps {
  theme: ThemeDto;
  onViewTheme?: (themeId: string) => void;
  onViewInitiatives?: (themeId: string) => void;
  onMoreOptions?: (themeId: string) => void;
}

/**
 * Displays a single roadmap theme with narrative context (heroes/villains).
 * Shows theme information and action buttons for viewing details.
 */
export const ThemeCard: React.FC<ThemeCardProps> = ({
  theme,
  onViewTheme,
  onViewInitiatives,
  onMoreOptions,
}) => {
  return (
    <div className="bg-background text-foreground border-border rounded-lg p-5 space-y-4 hover:border-border transition-colors">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-foreground0 mb-2">{theme.identifier}: {theme.name}</h3>
        <p className="text-sm text-foreground line-clamp-2">
          {theme.description}
        </p>
      </div>

      {/* Heroes & Villains & Strategic Context Metadata */}
      <div className="space-y-2 text-sm">
        {(theme.heroes ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <UserRound className="text-primary"/>
            <span className="text-foreground font-medium">Heroes:</span>
            <span className="text-foreground">
              {theme.heroes?.map((h) => h.name).join(', ')}
            </span>
          </div>
        )}
        {(theme.villains ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <ShieldAlert className="text-destructive"/>
            <span className="text-foreground font-medium">Villains:</span>
            <span className="text-foreground">
              {theme.villains?.map((v) => v.name).join(', ')}
            </span>
          </div>
        )}
        {(theme.outcomes ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <Target className="text-success/30"/>
            <span className="text-foreground font-medium">Outcomes:</span>
            <span className="text-foreground">
              {theme.outcomes?.map((o) => o.name).join(', ')}
            </span>
          </div>
        )}
        {(theme.pillars ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <Compass className="text-accent/50"/>
            <span className="text-foreground font-medium">Pillars:</span>
            <span className="text-foreground">
              {theme.pillars?.map((p) => p.name).join(', ')}
            </span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2 border-t border-border">
        {onViewTheme && (
          <Button
            onClick={() => onViewTheme(theme.id)}
          >
            <Eye />
            View Theme
          </Button>
        )}
        {onViewInitiatives && (
          <Button
            onClick={() => onViewInitiatives(theme.id)}
          >
            View Initiatives
          </Button>
        )}
        {onMoreOptions && (
          <IconButton
            onClick={() => onMoreOptions(theme.id)}
            icon={<MoreHorizontal size={14} />}
          >
            More options
          </IconButton>
        )}
      </div>
    </div>
  );
};
