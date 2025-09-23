import React from 'react';
import { Navigate } from 'react-router';
import { useBillingUsage } from '#hooks/useBillingUsage';
import { UserAccountStatus } from '#constants/userAccountStatus';

interface OnboardingGuardProps {
  children: React.ReactNode;
}

const OnboardingGuard: React.FC<OnboardingGuardProps> = ({ children }) => {
  const { isLoading, userIsOnboarded } = useBillingUsage();

  // Show loading while we check user status
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Check if user needs onboarding
  // NEW users who haven't completed onboarding should be redirected to onboarding
  if (!userIsOnboarded) {
    return <Navigate to="/workspace/onboarding" replace />;
  }

  // User has completed onboarding, allow access to protected routes
  return <>{children}</>;
};

export default OnboardingGuard;