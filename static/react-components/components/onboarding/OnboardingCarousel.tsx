import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useBillingUsage } from '#hooks/useBillingUsage';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { PrimaryButton, SecondaryButton } from '#components/reusable/Button';
import StepIndicator from './StepIndicator';
import ProjectPlanningStep from './steps/ProjectPlanningStep';
import AiAssistantStep from './steps/AiAssistantStep';
import ContextAwareDevelopmentStep from './steps/ContextAwareDevelopmentStep';
import ProjectNameStep from './steps/ProjectNameStep';
import PricingStep from './steps/PricingStep';

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

  const totalSteps = 5;

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
    // If we're on the project name step (step 3, index 3), create workspace first
    if (currentStep === 3) {
      await handleCreateWorkspace();
    } else if (currentStep < totalSteps - 1) {
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
          {/* Step 1: Product Planning */}
          <div className="w-full flex-shrink-0 flex items-center justify-center" style={{ minWidth: '100%' }}>
            <ProjectPlanningStep />
          </div>

          {/* Step 2: AI Assistant Integration */}
          <div className="w-full flex-shrink-0 flex items-center justify-center" style={{ minWidth: '100%' }}>
            <AiAssistantStep />
          </div>

          {/* Step 3: Coding with Context */}
          <div className="w-full flex-shrink-0 flex items-center justify-center" style={{ minWidth: '100%' }}>
            <ContextAwareDevelopmentStep />
          </div>

          {/* Step 4: Project Name */}
          <div className="w-full flex-shrink-0 flex items-center justify-center" style={{ minWidth: '100%' }}>
            <ProjectNameStep
              currentStep={currentStep}
              stepIndex={3}
              projectName={projectName}
              onProjectNameChange={setProjectName}
              isCreatingWorkspace={isCreatingWorkspace}
              workspaceCreated={workspaceCreated}
            />
          </div>

          {/* Step 5: Pricing */}
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
      <div className="fixed w-screen left-0 bottom-0 flex justify-between items-center mt-4 sm:mt-8">
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
              disabled={currentStep === 3 && (!projectName.trim() || isCreatingWorkspace)}
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