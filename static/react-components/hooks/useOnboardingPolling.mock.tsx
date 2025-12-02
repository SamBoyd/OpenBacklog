import { fn } from '@storybook/test';
import * as actual from './useOnboardingPolling';
import { OnboardingPollingState, FoundationProgress } from './useOnboardingPolling';

export const useOnboardingPolling = fn(actual.useOnboardingPolling).mockName('useOnboardingPolling');

/**
 * Default foundation progress (all false)
 */
const EMPTY_FOUNDATION_PROGRESS: FoundationProgress = {
  hasVision: false,
  hasHeroes: false,
  hasVillains: false,
  hasPillars: false,
  hasOutcomes: false,
  hasThemes: false,
  hasInitiative: false,
};

/**
 * Foundation progress with vision defined
 */
const VISION_PROGRESS: FoundationProgress = {
  hasVision: true,
  hasHeroes: false,
  hasVillains: false,
  hasPillars: false,
  hasOutcomes: false,
  hasThemes: false,
  hasInitiative: false,
};

/**
 * Foundation progress with vision and characters (heroes + villains)
 */
const CHARACTERS_PROGRESS: FoundationProgress = {
  hasVision: true,
  hasHeroes: true,
  hasVillains: true,
  hasPillars: false,
  hasOutcomes: false,
  hasThemes: false,
  hasInitiative: false,
};

/**
 * Foundation progress with vision, characters, and strategy (pillars + outcomes)
 */
const STRATEGY_PROGRESS: FoundationProgress = {
  hasVision: true,
  hasHeroes: true,
  hasVillains: true,
  hasPillars: true,
  hasOutcomes: true,
  hasThemes: false,
  hasInitiative: false,
};

/**
 * Foundation progress with everything except initiative
 */
const THEME_PROGRESS: FoundationProgress = {
  hasVision: true,
  hasHeroes: true,
  hasVillains: true,
  hasPillars: true,
  hasOutcomes: true,
  hasThemes: true,
  hasInitiative: false,
};

/**
 * Complete foundation progress
 */
const COMPLETE_PROGRESS: FoundationProgress = {
  hasVision: true,
  hasHeroes: true,
  hasVillains: true,
  hasPillars: true,
  hasOutcomes: true,
  hasThemes: true,
  hasInitiative: true,
};

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
    workspaceId: null,
    foundationProgress: EMPTY_FOUNDATION_PROGRESS,
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
  workspaceId: null,
  foundationProgress: EMPTY_FOUNDATION_PROGRESS,
};

/**
 * Mock for polling foundation - just started (no entities yet)
 */
export const mockPollingFoundationStart: OnboardingPollingState = {
  status: 'polling-foundation',
  hasWorkspace: true,
  hasInitiatives: false,
  workspaceCount: 1,
  initiativeCount: 0,
  workspaceId: 'mock-workspace-id',
  foundationProgress: EMPTY_FOUNDATION_PROGRESS,
};

/**
 * Mock for polling foundation - vision defined
 */
export const mockPollingFoundationVision: OnboardingPollingState = {
  status: 'polling-foundation',
  hasWorkspace: true,
  hasInitiatives: false,
  workspaceCount: 1,
  initiativeCount: 0,
  workspaceId: 'mock-workspace-id',
  foundationProgress: VISION_PROGRESS,
};

/**
 * Mock for polling foundation - characters created
 */
export const mockPollingFoundationCharacters: OnboardingPollingState = {
  status: 'polling-foundation',
  hasWorkspace: true,
  hasInitiatives: false,
  workspaceCount: 1,
  initiativeCount: 0,
  workspaceId: 'mock-workspace-id',
  foundationProgress: CHARACTERS_PROGRESS,
};

/**
 * Mock for polling foundation - strategy defined
 */
export const mockPollingFoundationStrategy: OnboardingPollingState = {
  status: 'polling-foundation',
  hasWorkspace: true,
  hasInitiatives: false,
  workspaceCount: 1,
  initiativeCount: 0,
  workspaceId: 'mock-workspace-id',
  foundationProgress: STRATEGY_PROGRESS,
};

/**
 * Mock for polling foundation - theme set
 */
export const mockPollingFoundationTheme: OnboardingPollingState = {
  status: 'polling-foundation',
  hasWorkspace: true,
  hasInitiatives: false,
  workspaceCount: 1,
  initiativeCount: 0,
  workspaceId: 'mock-workspace-id',
  foundationProgress: THEME_PROGRESS,
};

/**
 * Mock for polling initiatives stage (legacy - maps to polling-foundation)
 * @deprecated Use mockPollingFoundationStart instead
 */
export const mockPollingInitiatives: OnboardingPollingState = {
  status: 'polling-foundation',
  hasWorkspace: true,
  hasInitiatives: false,
  workspaceCount: 1,
  initiativeCount: 0,
  workspaceId: 'mock-workspace-id',
  foundationProgress: EMPTY_FOUNDATION_PROGRESS,
};

/**
 * Mock for complete stage
 */
export const mockComplete: OnboardingPollingState = {
  status: 'complete',
  hasWorkspace: true,
  hasInitiatives: true,
  workspaceCount: 1,
  initiativeCount: 1,
  workspaceId: 'mock-workspace-id',
  foundationProgress: COMPLETE_PROGRESS,
};
