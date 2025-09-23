import React, { useState } from 'react';
import { Navigate } from 'react-router';
import { useBillingUsage } from '#hooks/useBillingUsage';
import { useIsDeviceMobile } from '#hooks/isDeviceMobile';

import NavBar from '#components/reusable/NavBar';
import AppBackground from '#components/AppBackground';
import OnboardingCarousel from '#components/onboarding/OnboardingCarousel';

/**
 * Onboarding page with carousel-style flow
 * Shows product introduction steps and pricing options
 */
const Onboarding: React.FC = () => {
  const isMobile = useIsDeviceMobile();


  return (
    <AppBackground>
      <div className="inset-0 flex flex-col h-screen w-screen">
        {/* Navigation bar */}
        {!isMobile && <NavBar enableNavigation={false} />}

        {/* Carousel onboarding flow */}
        <div className="flex-1 flex items-center justify-center">
          <OnboardingCarousel />
        </div>
      </div>
    </AppBackground>
  );
};

export default Onboarding;