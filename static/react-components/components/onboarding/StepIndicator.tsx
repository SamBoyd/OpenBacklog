import React from 'react';

interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
  onStepClick: (stepIndex: number) => void;
}

/**
 * Dot indicator component for the onboarding carousel
 * Shows progress through steps with clickable dots
 */
const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  totalSteps,
  onStepClick
}) => {
  return (
    <div className="flex items-center gap-2 sm:gap-3">
      {Array.from({ length: totalSteps }, (_, index) => (
        <button
          key={index}
          onClick={() => onStepClick(index)}
          className={`
            w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full transition-all duration-200 
            ${index === currentStep 
              ? 'bg-primary scale-125' 
              : index < currentStep 
                ? 'bg-primary/60 hover:bg-primary/80' 
                : 'bg-muted border border-muted-foreground hover:bg-muted/60'
            }
          `}
          aria-label={`Go to step ${index + 1}`}
        />
      ))}
    </div>
  );
};

export default StepIndicator;