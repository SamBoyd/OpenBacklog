import React from 'react';
import OnboardingStep from '../OnboardingStep';
import { PrimaryButton } from '#components/reusable/Button';

interface PricingStepProps {
  onSetupSubscription: () => void;
  isCompletingOnboarding: boolean;
  projectName?: string;
}

/**
 * Fourth onboarding step - Hybrid Pricing Model
 * Shows pricing information and subscription setup action
 */
const PricingStep: React.FC<PricingStepProps> = ({
  onSetupSubscription,
  isCompletingOnboarding,
  projectName
}) => {
  return (
    <OnboardingStep
      title="Hybrid Pricing Model"
      description="A low monthly fee for platform access, plus fair pay-as-you-go pricing for AI features."
      icon="💳"
      content={
        <div className="space-y-4 sm:space-y-6">
          {projectName && (
            <div className="bg-success/10 border border-success/20 rounded-lg p-3 sm:p-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg sm:text-xl">🎉</span>
                <span className="font-semibold text-success text-sm sm:text-base">Workspace Created!</span>
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Your <span className="font-semibold text-foreground">"{projectName}"</span> workspace is ready to go.
              </p>
            </div>
          )}
          <div className="bg-card border rounded-lg p-3 sm:p-6 relative">
            {isCompletingOnboarding && (
              <div className="absolute right-2 top-2">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              </div>
            )}
            <h3 className="text-muted-foreground font-semibold mb-2 sm:mb-3 text-sm sm:text-base">How It Works</h3>
            <ul className="space-y-2 text-muted-foreground mb-3 sm:mb-4 text-sm sm:text-base">
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Low monthly fee covers platform access + included AI credits
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Additional AI usage billed transparently per token
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                No cross-subsidies - pay for what you actually use
              </li>
            </ul>

            <div className="bg-primary/10 border border-primary/20 rounded-lg p-3 sm:p-4 mb-3 sm:mb-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl sm:text-2xl">✨</span>
                <span className="font-semibold text-foreground text-sm sm:text-base">Developer-Friendly Pricing</span>
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Fair, sustainable pricing designed for solo developers - not bloated enterprise plans
              </p>
            </div>

            <div className="flex justify-center">
              <PrimaryButton
                onClick={onSetupSubscription}
                disabled={isCompletingOnboarding}
                className="w-full sm:w-auto text-xs sm:text-sm px-4 sm:px-6 py-2 sm:py-3"
              >
                <span className="hidden sm:inline">Setup Monthly Subscription</span>
                <span className="sm:hidden">Setup Subscription</span>
              </PrimaryButton>
            </div>

          </div>
        </div>
      }
    />
  );
};

export default PricingStep;