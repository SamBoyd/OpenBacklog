import React from 'react';

interface OnboardingStepProps {
  title: string;
  description: string;
  icon: string;
  content: React.ReactNode;
}

/**
 * Individual step component for the onboarding carousel
 * Displays step content with consistent styling and layout
 */
const OnboardingStep: React.FC<OnboardingStepProps> = ({
  title,
  description,
  icon,
  content
}) => {
  return (
    <div className="flex flex-col items-center justify-center max-w-sm sm:max-w-2xl mx-auto text-center px-2 sm:px-4">
      {/* Icon */}
      <div className="text-4xl sm:text-6xl mb-4 sm:mb-6">
        {icon}
      </div>
      
      {/* Title */}
      <h2 className="text-xl sm:text-2xl font-bold text-foreground mb-2 sm:mb-3">
        {title}
      </h2>
      
      {/* Description */}
      <p className="text-base sm:text-lg text-muted-foreground mb-4 sm:mb-8 max-w-xs sm:max-w-xl">
        {description}
      </p>
      
      {/* Content */}
      <div className="w-full">
        {content}
      </div>
    </div>
  );
};

export default OnboardingStep;