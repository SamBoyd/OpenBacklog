import React, { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { PrimaryButton, SecondaryButton } from '#components/reusable/Button';
import AppBackground from '#components/AppBackground';
import useSubscriptionComplete from '#hooks/useSubscriptionComplete';
import { useBillingUsage } from '#hooks/useBillingUsage';
import {
  trackSubscriptionSetupSuccess,
  trackSubscriptionSetupFailed,
  trackFreeToPaidConversion,
} from '#services/tracking/onboarding';
import { SafeStorage } from '#hooks/useUserPreferences';

/**
 * SubscriptionComplete page component
 * Displays success or error state after subscription setup attempt
 * @returns {React.ReactElement} The subscription completion page
 */
const SubscriptionCompletePage: React.FC = () => {
  const navigate = useNavigate();
  const { invalidateUserAccountDetails } = useBillingUsage();
  const { isLoading, hasError, errorMessage, onboardingComplete } = useSubscriptionComplete();

  // Track success or failure when loading completes
  useEffect(() => {
    if (!isLoading) {
      if (hasError) {
        trackSubscriptionSetupFailed(errorMessage || undefined);
      } else if (onboardingComplete) {
        trackSubscriptionSetupSuccess();

        // Track free-to-paid conversion if user was previously free tier
        const isFreeUser = SafeStorage.safeGet('is_free_tier_user', (val): val is boolean => typeof val === 'boolean', false);
        if (isFreeUser) {
          const conversionTrigger = SafeStorage.safeGet('conversion_trigger', (val): val is string => typeof val === 'string', undefined);
          trackFreeToPaidConversion(conversionTrigger);
          // Clear free tier flag after conversion
          SafeStorage.safeSet('is_free_tier_user', false);
        }
      }
    }
  }, [isLoading, hasError, errorMessage, onboardingComplete]);

  // Auto-redirect only on success
  useEffect(() => {
    if (!isLoading && !hasError && onboardingComplete) {
      const timer = setTimeout(async () => {
        await invalidateUserAccountDetails();
        navigate('/workspace/billing');
      }, 10000);

      return () => clearTimeout(timer);
    }
    
    // Return empty cleanup function for other cases
    return () => {};
  }, [navigate, isLoading, hasError, onboardingComplete]);

  /**
   * Handle navigation to billing page
   */
  const handleGoToBilling = async () => {
    await invalidateUserAccountDetails();
    navigate('/workspace/billing');
  };

  /**
   * Handle navigation to main workspace
   */
  const handleGoToWorkspace = async () => {
    await invalidateUserAccountDetails();
    navigate('/workspace/initiatives');
  };

  /**
   * Handle retry subscription setup
   */
  const handleRetrySetup = async () => {
    await invalidateUserAccountDetails();
    navigate('/workspace/billing/subscription/checkout');
  };

  // Loading state
  if (isLoading) {
    return (
      <AppBackground>
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
          <div className="max-w-md mx-auto bg-card border border-border rounded-lg p-8 text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
            </div>
            <p className="text-muted-foreground">Processing subscription...</p>
          </div>
        </div>
      </AppBackground>
    );
  }

  // Error state
  if (hasError) {
    return (
      <AppBackground>
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
          <div className="max-w-md mx-auto bg-card border border-border rounded-lg p-8 text-center space-y-6">
            {/* Error Icon */}
            <div className="flex justify-center">
              <div className="w-16 h-16 bg-destructive/20 rounded-full flex items-center justify-center">
                <div className="text-destructive text-2xl">⚠</div>
              </div>
            </div>

            {/* Error Message */}
            <div className="space-y-3">
              <h1 className="text-2xl font-bold text-foreground">
                Setup Incomplete
              </h1>
              <p className="text-muted-foreground">
                {errorMessage || 'There was an issue setting up your subscription.'}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-3">
              <PrimaryButton
                onClick={handleRetrySetup}
                className="w-full"
              >
                Try Again
              </PrimaryButton>
              <SecondaryButton
                onClick={handleGoToWorkspace}
                className="w-full"
              >
                Continue to Workspace
              </SecondaryButton>
            </div>
          </div>
        </div>
      </AppBackground>
    );
  }

  // Success state - only show when onboarding is actually complete
  if (onboardingComplete) {
    return (
      <AppBackground>
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
          <div className="max-w-md mx-auto bg-card border border-border rounded-lg p-8 text-center space-y-6">
            {/* Success Icon */}
            <div className="flex justify-center">
              <div className="w-16 h-16 bg-success/20 rounded-full flex items-center justify-center">
                <div className="text-success text-2xl">✓</div>
              </div>
            </div>

            {/* Success Message */}
            <div className="space-y-3">
              <h1 className="text-2xl font-bold text-foreground">
                Subscription Active!
              </h1>
              <p className="text-muted-foreground">
                Your monthly subscription has been set up successfully. You now have access to unlimited task management and included AI credits.
              </p>
            </div>

            {/* Features Reminder */}
            <div className="bg-primary/10 border border-primary/20 rounded-lg p-4 text-left">
              <h3 className="font-semibold text-foreground mb-2">What's included:</h3>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <span className="text-primary">✓</span>
                  Unlimited task management & MCP tools
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-primary">✓</span>
                  Included AI credits to get started
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-primary">✓</span>
                  Fair pay-as-you-go for additional AI usage
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-primary">✓</span>
                  Cancel anytime - no commitment
                </li>
              </ul>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-3">
              <PrimaryButton
                onClick={handleGoToBilling}
                className="w-full"
              >
                View Billing & Usage
              </PrimaryButton>
              <button
                onClick={handleGoToWorkspace}
                className="text-muted-foreground hover:text-foreground transition-colors text-sm"
              >
                Continue to Workspace
              </button>
            </div>

            {/* Auto-redirect Notice */}
            <p className="text-xs text-muted-foreground">
              You'll be redirected to your billing page automatically in 10 seconds
            </p>
          </div>
        </div>
      </AppBackground>
    );
  }

  // Fallback state (should rarely be reached with proper hook logic)
  return (
    <AppBackground>
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-md mx-auto bg-card border border-border rounded-lg p-8 text-center space-y-6">
          <div className="flex justify-center">
            <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
          </div>
          <p className="text-muted-foreground">Processing subscription...</p>
        </div>
      </div>
    </AppBackground>
  );
};

export default SubscriptionCompletePage;