import React from 'react';
import { CompactButton } from '#components/reusable/Button';
import { HeroDto } from '#types';

/**
 * Props for the HeroCard component
 */
interface HeroCardProps {
  hero: HeroDto;
  onViewDetail?: () => void;
}

/**
 * HeroCard displays a hero character with primary color styling
 * @param {object} props - The component props
 * @param {HeroDto} props.hero - The hero data to display
 * @param {function} [props.onViewDetail] - Callback when "View Hero Detail" is clicked
 * @returns {React.ReactElement} The hero card component
 */
const HeroCard: React.FC<HeroCardProps> = ({ hero, onViewDetail }) => (
  <div className="bg-primary/10 border border-primary/20 rounded-lg p-3">
    <p className="text-sm font-medium text-foreground">{hero.name}</p>
    {hero.description && (
      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
        Core Promise: "{hero.description}"
      </p>
    )}
    <CompactButton
      onClick={onViewDetail || (() => {})}
      className="text-primary font-medium mt-2"
    >
      View Hero Detail
    </CompactButton>
  </div>
);

export default HeroCard;

