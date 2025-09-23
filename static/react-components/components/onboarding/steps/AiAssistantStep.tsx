import React from 'react';
import OnboardingStep from '../OnboardingStep';

/**
 * Second onboarding step - AI Assistant Integration
 * Explains how AI coding assistants integrate with the platform
 */
const AiAssistantStep: React.FC = () => {
  return (
    <OnboardingStep
      title="AI Coding Assistants"
      description="Connect your local AI coding assistants to automatically update task checklists as you work."
      icon="🤖"
      content={
        <div className="space-y-4">
          <div className="bg-card border rounded-lg p-3 sm:p-6">
            <h3 className="text-muted-foreground font-semibold mb-2 sm:mb-3 text-sm sm:text-base">Smart Integration</h3>
            <ul className="space-y-2 text-muted-foreground text-sm sm:text-base">
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Works with Claude, Cursor, and other AI assistants
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Automatically updates task progress as you code
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Syncs checklist items with your development workflow
              </li>
            </ul>
          </div>
        </div>
      }
    />
  );
};

export default AiAssistantStep;