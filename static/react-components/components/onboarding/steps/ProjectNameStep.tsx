import React, { useEffect, useRef, useState } from 'react';
import OnboardingStep from '../OnboardingStep';

interface ProjectNameStepProps {
  currentStep?: number;
  stepIndex?: number;
  projectName?: string;
  onProjectNameChange: (projectName: string) => void;
  isCreatingWorkspace?: boolean;
  workspaceCreated?: boolean;
}

const PLACEHOLDER_OPTIONS = [
  "Yet Another Todo App",
  "Hacker News Clone",
  "Twitter But Better",
  "Not Another Blog Engine",
  "Definitely Not Slack",
  "My SaaS Idea",
  "Weekend URL Shortener",
  "Totally Original Chat App",
  "The Next Facebook",
  "Pokemon Go Clone",
  "Markdown Editor Supreme",
  "Revolutionary CMS",
  "Billion Dollar Idea"
];

/**
 * Step component for collecting the user's project name during onboarding
 * @param {object} props - The component props
 * @param {number} [props.currentStep] - Current active step index
 * @param {number} [props.stepIndex] - This step's index
 * @param {string} [props.projectName] - Current project name value
 * @param {function} props.onProjectNameChange - Callback when project name changes
 * @param {boolean} [props.isCreatingWorkspace] - Whether workspace is being created
 * @param {boolean} [props.workspaceCreated] - Whether workspace has been created
 * @returns {React.ReactElement} The project name input step component
 */
const ProjectNameStep: React.FC<ProjectNameStepProps> = ({
  currentStep,
  stepIndex,
  projectName,
  onProjectNameChange,
  isCreatingWorkspace = false,
  workspaceCreated = false
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [placeholder] = useState(() => {
    // Choose random placeholder on component mount
    return PLACEHOLDER_OPTIONS[Math.floor(Math.random() * PLACEHOLDER_OPTIONS.length)];
  });

  // Auto-focus when this step becomes active
  useEffect(() => {
    if (currentStep === stepIndex && inputRef.current && !isCreatingWorkspace && !workspaceCreated) {
      // Small delay to ensure the step transition is complete
      const timeoutId = setTimeout(() => {
        inputRef.current?.focus();
      }, 350); // Slightly longer than the transition duration (300ms)

      return () => clearTimeout(timeoutId);
    }
    return () => null
  }, [currentStep, stepIndex, isCreatingWorkspace, workspaceCreated]);

  return (
    <OnboardingStep
      title="Create your workspace"
      description="Give your project a name. You can always change this later."
      icon="🚀"
      content={
        <div className="max-w-xs sm:max-w-md mx-auto">
          <div className="space-y-4 sm:space-y-6">
            <div className="text-left">
              <label 
                htmlFor="project-name" 
                className="block text-xs sm:text-sm font-medium text-foreground mb-2"
              >
                Project Name
              </label>
              <input
                ref={inputRef}
                id="project-name"
                type="text"
                value={projectName}
                onChange={(e) => onProjectNameChange(e.target.value)}
                placeholder={placeholder}
                className="w-full px-3 sm:px-4 py-2 sm:py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-foreground bg-background text-sm sm:text-base"
                disabled={isCreatingWorkspace || workspaceCreated}
              />
            </div>

            {isCreatingWorkspace && !workspaceCreated && (
              <div className="flex items-center justify-center py-4">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                  <span className="text-sm text-muted-foreground">Creating workspace...</span>
                </div>
              </div>
            )}

            {workspaceCreated && (
              <div className="flex items-center justify-center py-4">
                <div className="flex items-center space-x-2">
                  <div className="rounded-full h-5 w-5 bg-green-500 flex items-center justify-center">
                    <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-sm text-green-600">Workspace created successfully!</span>
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 sm:mt-6 text-xs sm:text-sm text-muted-foreground">
            <p>You can change this later in workspace settings.</p>
          </div>
        </div>
      }
    />
  );
};

export default ProjectNameStep;