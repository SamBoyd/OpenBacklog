import React from 'react';
import OnboardingStep from '../OnboardingStep';

/**
 * Third onboarding step - Context-Aware Development
 * Explains how the platform provides context to AI assistants
 */
const ContextAwareDevelopmentStep: React.FC = () => {
  return (
    <OnboardingStep
      title="Context-Aware Development"
      description="Provide rich context to your AI assistants and maintain task progression automatically."
      icon="💻"
      content={
        <div className="space-y-4">
          <div className="bg-card border rounded-lg p-3 sm:p-6">
            <h3 className="text-muted-foreground font-semibold mb-2 sm:mb-3 text-sm sm:text-base">Enhanced Productivity</h3>
            <ul className="space-y-2 text-muted-foreground text-sm sm:text-base">
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Share project context and requirements with AI
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Track code changes and link them to tasks
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Maintain detailed development history
              </li>
            </ul>
          </div>
        </div>
      }
    />
  );
};

export default ContextAwareDevelopmentStep;