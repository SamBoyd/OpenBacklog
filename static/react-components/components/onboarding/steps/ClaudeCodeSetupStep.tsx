import React from 'react';
import OnboardingStep from '../OnboardingStep';

/**
 * Placeholder step component for Claude Code MCP setup during onboarding
 * This will be fully implemented in task TM-116
 * @returns {React.ReactElement} The Claude Code setup placeholder step
 */
const ClaudeCodeSetupStep: React.FC = () => {
  return (
    <OnboardingStep
      title="Add OpenBacklog to Claude Code"
      description="Generate an API token to connect Claude Code with your workspace."
      icon="🤖"
      content={
        <div className="max-w-xs sm:max-w-md mx-auto">
          <div className="space-y-4 sm:space-y-6">
            <div className="bg-muted/50 border border-border rounded-lg p-4 sm:p-6">
              <p className="text-sm sm:text-base text-muted-foreground text-center">
                Claude Code MCP setup step will be implemented in task TM-116
              </p>
            </div>
          </div>
        </div>
      }
    />
  );
};

export default ClaudeCodeSetupStep;
