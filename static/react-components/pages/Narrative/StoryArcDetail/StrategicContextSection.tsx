import React from 'react';
import { Lightbulb, Target, TrendingUp } from 'lucide-react';
import { StrategicContextSectionProps } from '#types/storyArc';
import { PillarDto } from '#api/productStrategy';

/**
 * OutcomeCard displays a single outcome with its description.
 * Inline component for simplicity.
 */
interface OutcomeCardProps {
  name: string;
  description: string | null;
  pillars: PillarDto[];
  progress?: number;
  onView: () => void;
}

const OutcomeCard: React.FC<OutcomeCardProps> = ({ name, description, pillars, progress, onView }) => {
  return (
    <button
      onClick={onView}
      className="w-80 text-left p-3 border border-border rounded-lg bg-card hover:bg-accent/50 transition-colors group flex flex-col gap-2"
    >
      <div className="flex items-start justify-start gap-2">
        <Lightbulb size={18} className="text-foreground" />
        <h4 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
          {name}
        </h4>
        {progress && (
          <span className="text-xs font-medium text-muted-foreground shrink-0">
            {progress}%
          </span>
        )}
      </div>

      {pillars.map(pillar => (
        
        <div key={pillar.id} className="text-xs font-medium text-muted-foreground">
          {pillar.name}
        </div>
      ))}

      {description && (
        <p className="text-xs text-muted-foreground line-clamp-2">{description}</p>
      )}
    </button>
  );
};

/**
 * StrategicContextSection displays the product vision and linked outcomes.
 * Shows the strategic context for the theme with progress tracking.
 *
 * @param {StrategicContextSectionProps} props - Component props
 * @returns {React.ReactElement} The strategic context section
 */
const StrategicContextSection: React.FC<StrategicContextSectionProps> = ({
  visionText,
  outcomes,
  pillars,
  progressPercent,
  onViewOutcome,
}) => {
  const handleViewOutcome = (outcomeId: string) => {
    if (onViewOutcome) {
      onViewOutcome(outcomeId);
    }
  };

  return (
    <div className="border border-border rounded-lg bg-card p-6">
      {/* Section Header */}
      <div className="flex items-center gap-2 mb-4">
        <Target className="w-5 h-5 text-primary" />
        <h3 className="text-base font-semibold text-foreground">Strategic Context</h3>
      </div>

      {/* Product Vision */}
      {visionText && (
        <div className="mb-4 pb-4 border-b border-border">
          <p className="text-sm italic text-blue-600 dark:text-blue-400 leading-relaxed">
            {visionText}
          </p>
        </div>
      )}

      {/* Outcomes */}
      {outcomes.length > 0 ? (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-foreground">Outcomes</h4>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <TrendingUp className="w-3 h-3" />
              <span>{progressPercent}% complete</span>
            </div>
          </div>
          <div className="flex flex-row gap-x-2 gap-y-2">
            {outcomes.map(outcome => (
              <OutcomeCard
                key={outcome.id}
                name={outcome.name}
                description={outcome.description}
                pillars={outcome.pillar_ids.map(pillarId => pillars.find(pillar => pillar.id === pillarId)).filter(item => item !== undefined)}
                onView={() => handleViewOutcome(outcome.id)}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-6">
          <Target className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">No outcomes linked yet</p>
        </div>
      )}
    </div>
  );
};

export default StrategicContextSection;
