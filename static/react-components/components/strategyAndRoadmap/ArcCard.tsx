import React from 'react';
import { ArcDto } from '#api/productStrategy';
import { MoreHorizontal } from 'lucide-react';

interface ArcCardProps {
  arc: ArcDto;
  onViewArc?: (arcId: string) => void;
  onViewBeats?: (arcId: string) => void;
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
  onViewBeats,
  onEdit,
  onMoreOptions,
}) => {
  return (
    <div className="bg-white border-2 border-neutral-200 rounded-lg p-5 space-y-4 hover:border-neutral-300 transition-colors">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-neutral-950 mb-2">{arc.name}</h3>
        <p className="text-sm text-neutral-600 line-clamp-2">
          {arc.description}
        </p>
      </div>

      {/* Heroes & Villains Metadata */}
      <div className="space-y-2 text-sm">
        {(arc.heroes ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <span className="text-neutral-500 font-medium">Heroes:</span>
            <span className="text-neutral-700">
              {arc.heroes?.map((h) => h.name).join(', ')}
            </span>
          </div>
        )}
        {(arc.villains ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <span className="text-neutral-500 font-medium">Villains:</span>
            <span className="text-neutral-700">
              {arc.villains?.map((v) => v.name).join(', ')}
            </span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2 border-t border-neutral-100">
        {onViewArc && (
          <button
            onClick={() => onViewArc(arc.id)}
            className="px-3 py-1.5 text-xs font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded transition-colors"
          >
            View Theme
          </button>
        )}
        {onViewBeats && (
          <button
            onClick={() => onViewBeats(arc.id)}
            className="px-3 py-1.5 text-xs font-medium text-neutral-700 bg-neutral-100 hover:bg-neutral-200 rounded transition-colors"
          >
            View Beats
          </button>
        )}
        {onEdit && (
          <button
            onClick={() => onEdit(arc.id)}
            className="p-1.5 text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded transition-colors"
            title="Edit theme"
          >
            ✎
          </button>
        )}
        {onMoreOptions && (
          <button
            onClick={() => onMoreOptions(arc.id)}
            className="p-1.5 text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded transition-colors"
            title="More options"
          >
            <MoreHorizontal size={14} />
          </button>
        )}
      </div>
    </div>
  );
};
