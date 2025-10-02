import React from 'react';
import OnboardingStep from '../OnboardingStep';
import { useGithubInstallation } from '#hooks/useGithubInstallation';
import { PrimaryButton, SecondaryButton } from '#components/reusable/Button';

/**
 * Step component for GitHub app installation during onboarding
 * Handles three states: loading, not connected, and connected
 * @returns {React.ReactElement} The GitHub installation step component
 */
const GitHubInstallStep: React.FC = () => {
  const { hasInstallation, repositoryCount, isLoading } = useGithubInstallation();

  const handleConnectGitHub = () => {
    window.location.href = '/github/install';
  };

  const handleManageAccess = () => {
    window.open('https://github.com/settings/installations', '_blank', 'noopener,noreferrer');
  };

  return (
    <OnboardingStep
      title="Connect your repositories"
      description="Install the GitHub app to enable file autocomplete and seamless code referencing."
      icon="🔗"
      content={
        <div className="max-w-xs sm:max-w-md mx-auto">
          <div className="space-y-4 sm:space-y-6">
            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                  <span className="text-sm text-muted-foreground">Checking GitHub connection...</span>
                </div>
              </div>
            )}

            {/* Not Connected State */}
            {!isLoading && !hasInstallation && (
              <>
                <div className="bg-card border rounded-lg p-4 sm:p-6">
                  <h3 className="text-muted-foreground font-semibold mb-3 text-sm sm:text-base">
                    Why connect GitHub?
                  </h3>
                  <ul className="space-y-2 text-muted-foreground mb-4 text-sm sm:text-base">
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      Type '@filename' to get instant file suggestions from your repos
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      Share precise code context with AI assistants
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      Real-time sync when you push changes
                    </li>
                  </ul>

                  <div className="flex justify-center">
                    <PrimaryButton
                      onClick={handleConnectGitHub}
                      className="w-full sm:w-auto text-xs sm:text-sm px-4 sm:px-6 py-2 sm:py-3"
                    >
                      Connect GitHub
                    </PrimaryButton>
                  </div>
                </div>
              </>
            )}

            {/* Connected State */}
            {!isLoading && hasInstallation && (
              <div className="bg-card border rounded-lg p-4 sm:p-6">
                <div className="flex items-center mb-4">
                  <div className="rounded-full h-5 w-5 bg-success flex items-center justify-center mr-2">
                    <svg className="h-3 w-3 text-success-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-foreground">GitHub app connected</h3>
                </div>

                <div className="mb-4">
                  <h4 className="text-md font-medium text-foreground mb-2">
                    Connected repositories ({repositoryCount})
                  </h4>
                  {repositoryCount === 0 && (
                    <p className="text-sm text-muted-foreground">
                      No repos connected yet. Add repository access to enable file autocomplete.
                    </p>
                  )}
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                  <SecondaryButton
                    onClick={handleManageAccess}
                    className="text-xs sm:text-sm px-4 py-2"
                  >
                    Manage repository access
                  </SecondaryButton>
                </div>
              </div>
            )}
          </div>
        </div>
      }
    />
  );
};

export default GitHubInstallStep;
