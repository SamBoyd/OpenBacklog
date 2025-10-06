/**
 * Onboarding funnel analytics tracking
 * Tracks user progression through the onboarding flow
 */

import { trackEvent, setUserProperties } from '#services/analytics';

// Step name constants for consistency
export const ONBOARDING_STEPS = {
  PROJECT_NAME: 'Project Name',
  GITHUB_INSTALL: 'GitHub Install',
  CLAUDE_CODE_SETUP: 'Claude Code Setup',
  PRICING: 'Pricing',
} as const;

/**
 * Track when user enters the onboarding funnel
 */
export const trackOnboardingStart = (): void => {
  trackEvent('Onboarding Started', {
    referrer: document.referrer,
    timestamp: new Date().toISOString(),
  });

  setUserProperties({
    onboarding_started_at: new Date().toISOString(),
    onboarding_current_step: 0,
  });
};

/**
 * Track when user views the Project Name step
 */
export const trackProjectNameStepViewed = (): void => {
  trackEvent('Onboarding Project Name Viewed', {
    step_number: 0,
    timestamp: new Date().toISOString(),
  });

  setUserProperties({
    onboarding_current_step: 0,
    onboarding_furthest_step: 0,
  });
};

/**
 * Track when user completes the Project Name step
 */
export const trackProjectNameStepCompleted = (metadata?: Record<string, any>): void => {
  trackEvent('Onboarding Project Name Completed', {
    step_number: 0,
    ...metadata,
    timestamp: new Date().toISOString(),
  });
};

/**
 * Track when user views the GitHub Install step
 */
export const trackGitHubInstallStepViewed = (): void => {
  trackEvent('Onboarding GitHub Install Viewed', {
    step_number: 1,
    timestamp: new Date().toISOString(),
  });

  setUserProperties({
    onboarding_current_step: 1,
    onboarding_furthest_step: 1,
  });
};

/**
 * Track when user completes the GitHub Install step
 */
export const trackGitHubInstallStepCompleted = (metadata?: Record<string, any>): void => {
  trackEvent('Onboarding GitHub Install Completed', {
    step_number: 1,
    ...metadata,
    timestamp: new Date().toISOString(),
  });
};

/**
 * Track when user views the Claude Code Setup step
 */
export const trackClaudeCodeSetupStepViewed = (): void => {
  trackEvent('Onboarding Claude Code Setup Viewed', {
    step_number: 2,
    timestamp: new Date().toISOString(),
  });

  setUserProperties({
    onboarding_current_step: 2,
    onboarding_furthest_step: 2,
  });
};

/**
 * Track when user completes the Claude Code Setup step
 */
export const trackClaudeCodeSetupStepCompleted = (metadata?: Record<string, any>): void => {
  trackEvent('Onboarding Claude Code Setup Completed', {
    step_number: 2,
    ...metadata,
    timestamp: new Date().toISOString(),
  });
};

/**
 * Track when user views the Pricing step
 */
export const trackPricingStepViewed = (): void => {
  trackEvent('Onboarding Pricing Viewed', {
    step_number: 3,
    timestamp: new Date().toISOString(),
  });

  setUserProperties({
    onboarding_current_step: 3,
    onboarding_furthest_step: 3,
  });
};

/**
 * Track when user completes the Pricing step
 */
export const trackPricingStepCompleted = (metadata?: Record<string, any>): void => {
  trackEvent('Onboarding Pricing Completed', {
    step_number: 3,
    ...metadata,
    timestamp: new Date().toISOString(),
  });
};

/**
 * Track successful workspace creation
 */
export const trackWorkspaceCreated = (workspaceName: string): void => {
  trackEvent('Onboarding Workspace Created', {
    workspace_name: workspaceName,
    timestamp: new Date().toISOString(),
  });

  setUserProperties({
    has_created_workspace: true,
    workspace_created_at: new Date().toISOString(),
  });
};

/**
 * Track when user completes the entire onboarding funnel
 */
export const trackOnboardingComplete = (): void => {
  trackEvent('Onboarding Completed', {
    timestamp: new Date().toISOString(),
  });

  setUserProperties({
    onboarding_completed_at: new Date().toISOString(),
    onboarding_current_step: 4, // Final step
  });
};
