import { fn } from '@storybook/test';
import * as actual from './useOnboardingPolling';
import { OnboardingPollingState } from './useOnboardingPolling';



export const useOnboardingPolling = fn(actual.useOnboardingPolling).mockName('useOnboardingPolling');

/**
 * Mock implementation of useOnboardingPolling for Storybook stories
 *
 * @param {Partial<OnboardingPollingState>} [overrides] - Optional state overrides
 * @returns {OnboardingPollingState} Mock onboarding polling state
 *
 * @example
 * ```tsx
 * // In a story
 * vi.mock('#hooks/useOnboardingPolling', () => ({
 *   useOnboardingPolling: () => mockUseOnboardingPolling({ status: 'complete' })
 * }));
 * ```
 */
export function mockUseOnboardingPolling(
  overrides?: Partial<OnboardingPollingState>
): OnboardingPollingState {
  return {
    status: 'polling-workspace',
    hasWorkspace: false,
    hasInitiatives: false,
    workspaceCount: 0,
    initiativeCount: 0,
    ...overrides,
  };
}

/**
 * Mock for polling workspace stage
 */
export const mockPollingWorkspace: OnboardingPollingState = {
  status: 'polling-workspace',
  hasWorkspace: false,
  hasInitiatives: false,
  workspaceCount: 0,
  initiativeCount: 0,
};

/**
 * Mock for polling initiatives stage
 */
export const mockPollingInitiatives: OnboardingPollingState = {
  status: 'polling-initiatives',
  hasWorkspace: true,
  hasInitiatives: false,
  workspaceCount: 1,
  initiativeCount: 0,
};

/**
 * Mock for complete stage
 */
export const mockComplete: OnboardingPollingState = {
  status: 'complete',
  hasWorkspace: true,
  hasInitiatives: true,
  workspaceCount: 1,
  initiativeCount: 3,
};
