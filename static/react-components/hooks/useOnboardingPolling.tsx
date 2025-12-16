import { useState, useEffect, useCallback } from 'react';
import { getAllWorkspaces } from '#api/workspaces';
import { getAllInitiatives } from '#api/initiatives';
import { getWorkspaceVision } from '#api/productStrategy';
import { getAllHeroes } from '#api/heroes';
import { getAllVillains } from '#api/villains';
import { getStrategicPillars, getRoadmapThemes } from '#api/productStrategy';
import { getProductOutcomes } from '#api/productOutcomes';

/**
 * Polling status types for onboarding flow
 */
export type OnboardingPollingStatus = 'polling-workspace' | 'polling-foundation' | 'complete';

/**
 * Progress state for strategic foundation entities
 */
export interface FoundationProgress {
  hasVision: boolean;
  hasHeroes: boolean;
  hasVillains: boolean;
  hasPillars: boolean;
  hasOutcomes: boolean;
  hasThemes: boolean;
  hasInitiative: boolean;
}

/**
 * State interface for onboarding polling
 */
export interface OnboardingPollingState {
  /** Current polling status */
  status: OnboardingPollingStatus;
  /** Whether a workspace has been detected */
  hasWorkspace: boolean;
  /** Whether initiatives have been detected */
  hasInitiatives: boolean;
  /** Number of workspaces found */
  workspaceCount: number;
  /** Number of initiatives found */
  initiativeCount: number;
  /** Current workspace ID (for foundation polling) */
  workspaceId: string | null;
  /** Progress tracking for strategic foundation entities */
  foundationProgress: FoundationProgress;
}

const INITIAL_FOUNDATION_PROGRESS: FoundationProgress = {
  hasVision: false,
  hasHeroes: false,
  hasVillains: false,
  hasPillars: false,
  hasOutcomes: false,
  hasThemes: false,
  hasInitiative: false,
};

/**
 * Hook that polls for workspace and strategic foundation creation during onboarding.
 *
 * Implements a three-stage polling flow:
 * 1. Poll for workspace creation every 3 seconds
 * 2. Once workspace exists, poll for strategic foundation entities every 3 seconds
 * 3. Complete when initiative is detected
 *
 * Strategic foundation entities tracked:
 * - Vision
 * - Heroes (at least 1)
 * - Villains (at least 1)
 * - Pillars (at least 2)
 * - Outcomes (at least 2)
 * - Themes (at least 1)
 * - Initiative (triggers completion)
 *
 * Polling continues indefinitely until completion or component unmount.
 *
 * @returns {OnboardingPollingState} Current onboarding polling state
 *
 * @example
 * ```tsx
 * const { status, hasWorkspace, foundationProgress } = useOnboardingPolling();
 *
 * if (status === 'complete') {
 *   navigate('/workspace/initiatives');
 * }
 * ```
 */
export function useOnboardingPolling(): OnboardingPollingState {
  const [status, setStatus] = useState<OnboardingPollingStatus>('polling-workspace');
  const [hasWorkspace, setHasWorkspace] = useState(false);
  const [hasInitiatives, setHasInitiatives] = useState(false);
  const [workspaceCount, setWorkspaceCount] = useState(0);
  const [initiativeCount, setInitiativeCount] = useState(0);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [foundationProgress, setFoundationProgress] = useState<FoundationProgress>(INITIAL_FOUNDATION_PROGRESS);

  /**
   * Polls all strategic foundation entities in parallel
   */
  const pollFoundation = useCallback(async (wsId: string): Promise<FoundationProgress> => {
    const results = await Promise.allSettled([
      getWorkspaceVision(wsId),
      getAllHeroes(wsId),
      getAllVillains(wsId),
      getStrategicPillars(wsId),
      getProductOutcomes(wsId),
      getRoadmapThemes(wsId),
      getAllInitiatives(),
    ]);

    const [visionResult, heroesResult, villainsResult, pillarsResult, outcomesResult, themesResult, initiativesResult] = results;

    return {
      hasVision: visionResult.status === 'fulfilled' && visionResult.value !== null,
      hasHeroes: heroesResult.status === 'fulfilled' && heroesResult.value.length >= 1,
      hasVillains: villainsResult.status === 'fulfilled' && villainsResult.value.length >= 1,
      hasPillars: pillarsResult.status === 'fulfilled' && pillarsResult.value.length >= 1,
      hasOutcomes: outcomesResult.status === 'fulfilled' && outcomesResult.value.length >= 1,
      hasThemes: themesResult.status === 'fulfilled' && themesResult.value.length >= 1,
      hasInitiative: initiativesResult.status === 'fulfilled' && initiativesResult.value.length >= 1,
    };
  }, []);

  // Stage 1: Poll for workspace creation
  useEffect(() => {
    let isActive = true;

    const pollWorkspaces = async () => {
      if (!isActive) return;

      try {
        const workspaces = await getAllWorkspaces();

        if (!isActive) return;

        setWorkspaceCount(workspaces.length);

        if (workspaces.length > 0) {
          setHasWorkspace(true);
          setWorkspaceId(workspaces[0].id);
          setStatus('polling-foundation');
        } else {
          setTimeout(pollWorkspaces, 3000);
        }
      } catch (error) {
        console.error('Error polling workspaces:', error);
        if (isActive) {
          setTimeout(pollWorkspaces, 3000);
        }
      }
    };

    pollWorkspaces();

    return () => {
      isActive = false;
    };
  }, []);

  // Stage 2: Poll for strategic foundation entities
  useEffect(() => {
    if (status !== 'polling-foundation' || !workspaceId) return;

    let isActive = true;

    const pollFoundationEntities = async () => {
      if (!isActive) return;

      try {
        const progress = await pollFoundation(workspaceId);

        if (!isActive) return;

        setFoundationProgress(progress);

        if (progress.hasInitiative) {
          setHasInitiatives(true);
          setInitiativeCount(1);
          setStatus('complete');
        } else {
          setTimeout(pollFoundationEntities, 3000);
        }
      } catch (error) {
        console.error('Error polling foundation:', error);
        if (isActive) {
          setTimeout(pollFoundationEntities, 3000);
        }
      }
    };

    pollFoundationEntities();

    return () => {
      isActive = false;
    };
  }, [status, workspaceId, pollFoundation]);

  return {
    status,
    hasWorkspace,
    hasInitiatives,
    workspaceCount,
    initiativeCount,
    workspaceId,
    foundationProgress,
  };
}
