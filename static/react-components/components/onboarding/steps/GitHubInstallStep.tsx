import React from 'react';
import OnboardingStep from '../OnboardingStep';

/**
 * Placeholder step component for GitHub app installation during onboarding
 * This will be fully implemented in task TM-115
 * @returns {React.ReactElement} The GitHub installation placeholder step
 */
const GitHubInstallStep: React.FC = () => {
  return (
    <OnboardingStep
      title="Connect your repositories"
      description="Install the GitHub app to enable file autocomplete and seamless code referencing."
      icon="🔗"
      content={
        <div className="max-w-xs sm:max-w-md mx-auto">
          <div className="space-y-4 sm:space-y-6">
            <div className="bg-muted/50 border border-border rounded-lg p-4 sm:p-6">
              <p className="text-sm sm:text-base text-muted-foreground text-center">
                GitHub app installation step will be implemented in task TM-115
              </p>
            </div>
          </div>
        </div>
      }
    />
  );
};

export default GitHubInstallStep;
