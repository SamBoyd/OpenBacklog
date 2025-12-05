import React from 'react';
import { ArcDto } from '#api/productStrategy';
import { MoreHorizontal } from 'lucide-react';
import { Button } from '#components/reusable/Button';

interface ArcCardProps {
  arc: ArcDto;
  onViewArc?: (arcId: string) => void;
  onViewInitiatives?: (arcId: string) => void;
  onEdit?: (arcId: string) => void;
  onMoreOptions?: (arcId: string) => void;
}

/**
 * Displays a single roadmap theme with narrative context (heroes/villains).
 * Shows theme information and action buttons for viewing details.
 */
export const ArcCard: React.FC<ArcCardProps> = ({
  arc,
  onViewArc,
  onViewInitiatives,
  onEdit,
  onMoreOptions,
}) => {
  return (
    <div className="bg-background text-foreground border-border rounded-lg p-5 space-y-4 hover:border-border transition-colors">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-foreground0 mb-2">{arc.name}</h3>
        <p className="text-sm text-foreground line-clamp-2">
          {arc.description}
        </p>
      </div>

      {/* Heroes & Villains Metadata */}
      <div className="space-y-2 text-sm">
        {(arc.heroes ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <span className="text-foreground font-medium">Heroes:</span>
            <span className="text-foreground">
              {arc.heroes?.map((h) => h.name).join(', ')}
            </span>
          </div>
        )}
        {(arc.villains ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <span className="text-foreground font-medium">Villains:</span>
            <span className="text-foreground">
              {arc.villains?.map((v) => v.name).join(', ')}
            </span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2 border-t border-border">
        {onViewArc && (
          <Button
            onClick={() => onViewArc(arc.id)}
          >
            View Theme
          </Button>
        )}
        {onViewInitiatives && (
          <Button
            onClick={() => onViewInitiatives(arc.id)}
          >
            View Initiatives
          </Button>
        )}
        {onEdit && (
          <Button
            onClick={() => onEdit(arc.id)}
            title="Edit theme"
          >
            ✎
          </Button>
        )}
        {onMoreOptions && (
          <Button
            onClick={() => onMoreOptions(arc.id)}
            title="More options"
          >
            <MoreHorizontal size={14} />
          </Button>
        )}
      </div>
    </div>
  );
};
