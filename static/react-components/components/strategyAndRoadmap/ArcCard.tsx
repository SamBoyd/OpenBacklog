import React from 'react';
import { ArcDto } from '#api/productStrategy';
import { ChevronDown, MoreHorizontal } from 'lucide-react';

interface ArcCardProps {
  arc: ArcDto;
  onViewArc?: (arcId: string) => void;
  onViewBeats?: (arcId: string) => void;
  onEdit?: (arcId: string) => void;
  onMoreOptions?: (arcId: string) => void;
}

/**
 * Displays a single story arc (narrative theme) in the roadmap overview.
 * Shows hero/villain context, progress, and action buttons.
 */
export const ArcCard: React.FC<ArcCardProps> = ({
  arc,
  onViewArc,
  onViewBeats,
  onEdit,
  onMoreOptions,
}) => {
  const getStatusBadge = () => {
    switch (arc.status) {
      case 'in_progress':
        return (
          <div className="bg-green-100 rounded-full px-3 py-1.5 inline-flex items-center gap-2">
            <span>🟢</span>
            <span className="text-sm font-medium text-green-700">
              In Progress - Act 2
            </span>
            {arc.progress_percentage && (
              <span className="text-sm text-green-700">
                ({arc.progress_percentage}%)
              </span>
            )}
          </div>
        );
      case 'complete':
        return (
          <div className="bg-green-100 rounded-full px-3 py-1.5 inline-flex items-center gap-2">
            <span>✅</span>
            <span className="text-sm font-medium text-green-700">Complete</span>
          </div>
        );
      case 'planned':
        return (
          <div className="bg-blue-100 rounded-full px-3 py-1.5 inline-flex items-center gap-2">
            <span>🔵</span>
            <span className="text-sm font-medium text-blue-700">Planned</span>
          </div>
        );
    }
  };

  return (
    <div className="bg-white border-2 border-neutral-200 rounded-lg p-5 space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-neutral-950 mb-2">{arc.name}</h3>
        <p className="text-sm text-neutral-600 line-clamp-1">
          {arc.description}
        </p>
      </div>

      {/* Status Badge */}
      <div>{getStatusBadge()}</div>

      {/* Progress Section */}
      {arc.status === 'in_progress' && arc.scenes_total && (
        <div className="text-xs text-neutral-500">
          Progress: {arc.scenes_completed} / {arc.scenes_total} scenes complete
        </div>
      )}

      {/* Metadata Section */}
      <div className="space-y-2 text-sm">
        {(arc.heroes ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <span className="text-neutral-500">Hero:</span>
            <span className="text-neutral-700">
              {(arc.heroes ?? []).map((h) => h.name).join(', ')}
            </span>
          </div>
        )}

        {(arc.villains ?? []).length > 0 && (
          <div className="flex gap-2 items-start">
            <span className="text-neutral-500">Villains:</span>
            <span className="text-neutral-700">
              {(arc.villains ?? []).map((v) => v.name).join(', ')}
            </span>
          </div>
        )}

        {arc.name && (
          <div className="flex gap-2 items-start">
            <span className="text-neutral-500">Theme:</span>
            <span className="text-neutral-700">{arc.name}</span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2">
        <button
          onClick={() => onViewArc?.(arc.id)}
          className="px-3 py-2 text-xs border border-neutral-300 rounded hover:bg-neutral-50 transition-colors"
        >
          View Arc
        </button>

        <button
          onClick={() => onViewBeats?.(arc.id)}
          className="px-3 py-2 text-xs border border-neutral-300 rounded hover:bg-neutral-50 transition-colors"
        >
          {arc.status === 'complete' ? 'View Retrospective' : 'View Beats'}
        </button>

        <button
          onClick={() => onEdit?.(arc.id)}
          className="px-2.5 py-2 text-xs border border-neutral-300 rounded hover:bg-neutral-50 transition-colors"
          title="Edit arc"
        >
          ✎
        </button>

        <button
          onClick={() => onMoreOptions?.(arc.id)}
          className="px-2.5 py-2 text-xs border border-neutral-300 rounded hover:bg-neutral-50 transition-colors"
          title="More options"
        >
          <MoreHorizontal size={14} className="inline" />
        </button>
      </div>

      {/* Timeline Info */}
      <div className="flex gap-8 text-xs text-neutral-500 pt-2 border-t border-neutral-100">
        {arc.started_quarter && (
          <div>Started: {arc.started_quarter}</div>
        )}
        {arc.expected_quarter && (
          <div>
            {arc.status === 'complete' ? 'Completed' : 'Expected'}:{' '}
            {arc.expected_quarter}
          </div>
        )}
      </div>
    </div>
  );
};
