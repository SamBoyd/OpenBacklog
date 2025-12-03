import React from 'react';
import { CompactButton } from '#components/reusable/Button';
import { VillainDto } from '#types';

/**
 * Props for the VillainCard component
 */
interface VillainCardProps {
  villain: VillainDto;
  onViewDetail?: () => void;
}

/**
 * VillainCard displays a villain/obstacle with accent/warning styling
 * @param {object} props - The component props
 * @param {VillainDto} props.villain - The villain data to display
 * @param {function} [props.onViewDetail] - Callback when "View Villain Detail" is clicked
 * @returns {React.ReactElement} The villain card component
 */
const VillainCard: React.FC<VillainCardProps> = ({ villain, onViewDetail }) => (
  <div className="bg-accent/20 border border-accent/40 rounded-lg p-3">
    <div className="flex items-start gap-2">
      <span className="text-accent-foreground">⚠</span>
      <div className="flex-1">
        <p className="text-sm font-medium text-foreground">{villain.name}</p>
        {villain.description && (
          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
            {villain.description}
          </p>
        )}
        <p className="text-xs text-muted-foreground mt-0.5">
          Severity: {villain.severity}/5
        </p>
        <CompactButton
          onClick={onViewDetail || (() => {})}
          className="text-accent-foreground font-medium mt-2"
        >
          View Villain Detail
        </CompactButton>
      </div>
    </div>
  </div>
);

export default VillainCard;

