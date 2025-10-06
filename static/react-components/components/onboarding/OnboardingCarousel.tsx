import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useBillingUsage } from '#hooks/useBillingUsage';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { PrimaryButton, SecondaryButton } from '#components/reusable/Button';
import StepIndicator from './StepIndicator';
import ProjectNameStep from './steps/ProjectNameStep';
import GitHubInstallStep from './steps/GitHubInstallStep';
import ClaudeCodeSetupStep from './steps/ClaudeCodeSetupStep';
import PricingStep from './steps/PricingStep';
import {
  trackOnboardingStart,
  trackProjectNameStepViewed,
  trackProjectNameStepCompleted,
  trackGitHubInstallStepViewed,
  trackGitHubInstallStepCompleted,
  trackClaudeCodeSetupStepViewed,
  trackClaudeCodeSetupStepCompleted,
  trackPricingStepViewed,
  trackPricingStepCompleted,
  trackWorkspaceCreated,
  trackOnboardingComplete,
} from '#services/tracking/onboarding';

/**
 * A simple carousel component for onboarding flow with step indicators and navigation
 */
const OnboardingCarousel = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isCompletingOnboarding, setIsCompletingOnboarding] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);
  const [workspaceCreated, setWorkspaceCreated] = useState(false);

  const navigate = useNavigate();
  
  const { workspaces, addWorkspace } = useWorkspaces();

  const totalSteps = 4;

  // Track onboarding start on mount
  useEffect(() => {
    trackOnboardingStart();
  }, []);

  // Track step views when currentStep changes
  useEffect(() => {
    const stepViewTrackers = [
      trackProjectNameStepViewed,
      trackGitHubInstallStepViewed,
      trackClaudeCodeSetupStepViewed,
      trackPricingStepViewed,
    ];
    stepViewTrackers[currentStep]();
  }, [currentStep]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowRight' && currentStep < totalSteps - 1) {
        setCurrentStep(currentStep + 1);
      } else if (event.key === 'ArrowLeft' && currentStep > 0) {
        setCurrentStep(currentStep - 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStep, totalSteps]);

  useEffect(() => {
    // Updates the carousel if the user has already created a workspace when they load the onboard
    // This can happen if they progress pass the Project Name step then reload
    if (workspaces.length > 0 && projectName == '' && !isCreatingWorkspace) {
      setProjectName(workspaces[0].name)
      setWorkspaceCreated(true)
    }
  }, [workspaces, projectName])

  const handleCreateWorkspace = async () => {
    if (workspaceCreated) {
      setCurrentStep(currentStep + 1);
      return; // workspace already created
    }

    if (projectName.trim() === '') {
      return; // Don't proceed if no project name
    }

    setIsCreatingWorkspace(true);
    try {
      await addWorkspace({ name: projectName.trim(), description: null, icon: null });
      setWorkspaceCreated(true);

      // Track workspace creation
      trackWorkspaceCreated(projectName.trim());

      // Wait a bit to show the success state
      setTimeout(() => {
        setCurrentStep(currentStep + 1);
        setIsCreatingWorkspace(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to create workspace:', error);
      setIsCreatingWorkspace(false);
    }
  };

  const handleNext = async () => {
    const stepCompletionTrackers = [
      trackProjectNameStepCompleted,
      trackGitHubInstallStepCompleted,
      trackClaudeCodeSetupStepCompleted,
      trackPricingStepCompleted,
    ];

    // If we're on the project name step (step 0, index 0), create workspace first
    if (currentStep === 0) {
      await handleCreateWorkspace();
      // Track step completion (workspace creation is tracked separately)
      stepCompletionTrackers[currentStep]();
    } else if (currentStep < totalSteps - 1) {
      // Track step completion before moving to next
      stepCompletionTrackers[currentStep]();
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSetupSubscription = async () => {
    setIsCompletingOnboarding(true);

    // Track onboarding funnel completion
    trackOnboardingComplete();

    navigate('/workspace/billing/subscription/checkout')
  };


  const handleStepClick = (stepIndex: number) => {
    setCurrentStep(stepIndex);
  };

  const isLastStep = currentStep === totalSteps - 1;
  const isFirstStep = currentStep === 0;

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto p-3 sm:p-6">
      {/* Step Indicator */}
      <div className="flex justify-center mb-8">
        <StepIndicator
          currentStep={currentStep}
          totalSteps={totalSteps}
          onStepClick={handleStepClick}
        />
      </div>

      {/* Carousel Container */}
      <div className="flex-1 relative overflow-hidden">
        <div
          className="flex transition-transform duration-300 ease-in-out h-full"
          style={{ transform: `translateX(-${currentStep * 100}%)` }}
        >
          {/* Step 1: Create Workspace */}
          <div className="w-full flex-shrink-0 flex items-center justify-center" style={{ minWidth: '100%' }}>
            <ProjectNameStep
              currentStep={currentStep}
              stepIndex={0}
              projectName={projectName}
              onProjectNameChange={setProjectName}
              isCreatingWorkspace={isCreatingWorkspace}
              workspaceCreated={workspaceCreated}
            />
          </div>

          {/* Step 2: Connect GitHub */}
          <div className="w-full flex-shrink-0 flex items-center justify-center" style={{ minWidth: '100%' }}>
            <GitHubInstallStep />
          </div>

          {/* Step 3: Claude Code MCP Setup */}
          <div className="w-full flex-shrink-0 flex items-center justify-center" style={{ minWidth: '100%' }}>
            <ClaudeCodeSetupStep />
          </div>

          {/* Step 4: Set up Subscription */}
          <div className="w-full flex-shrink-0 flex items-center justify-center" style={{ minWidth: '100%' }}>
            <PricingStep
              onSetupSubscription={handleSetupSubscription}
              isCompletingOnboarding={isCompletingOnboarding}
              projectName={projectName}
            />
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex justify-between items-center mt-4 sm:mt-8 pt-4 sm:pt-6">
        <div className="w-16 sm:w-24">
          {!isFirstStep && (
            <SecondaryButton
              onClick={handlePrevious}
              disabled={isCompletingOnboarding || isCreatingWorkspace}
              className="text-xs sm:text-sm px-2 sm:px-4 py-1 sm:py-2"
            >
              <span className="hidden sm:inline">Previous</span>
              <span className="sm:hidden">‹</span>
            </SecondaryButton>
          )}
        </div>

        <div className="text-xs sm:text-sm text-muted-foreground">
          {currentStep + 1} of {totalSteps}
        </div>

        <div className="w-16 sm:w-24 flex justify-end">
          {!isLastStep && (
            <PrimaryButton
              onClick={handleNext}
              disabled={currentStep === 0 && (!projectName.trim() || isCreatingWorkspace)}
              className="text-xs sm:text-sm px-2 sm:px-4 py-1 sm:py-2"
            >
              <span className="hidden sm:inline">Next</span>
              <span className="sm:hidden">›</span>
            </PrimaryButton>
          )}
        </div>
      </div>
    </div>
  );
};

export default OnboardingCarousel;