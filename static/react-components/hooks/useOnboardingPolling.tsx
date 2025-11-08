import { useState, useEffect } from 'react';
import { getAllWorkspaces } from '#api/workspaces';
import { getAllInitiatives } from '#api/initiatives';

/**
 * Polling status types for onboarding flow
 */
export type OnboardingPollingStatus = 'polling-workspace' | 'polling-initiatives' | 'complete';

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
}

/**
 * Hook that polls for workspace and initiative creation during onboarding.
 *
 * Implements a two-stage polling flow:
 * 1. Poll for workspace creation every 3 seconds
 * 2. Once workspace exists, poll for initiative creation every 3 seconds
 * 3. Complete when initiatives are detected
 *
 * Polling continues indefinitely until completion or component unmount.
 *
 * @returns {OnboardingPollingState} Current onboarding polling state
 *
 * @example
 * ```tsx
 * const { status, hasWorkspace, hasInitiatives } = useOnboardingPolling();
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

  // Stage 1: Poll for workspace creation
  useEffect(() => {
    let isActive = true;

    const pollWorkspaces = async () => {
      if (!isActive) return;

      try {
        const workspaces = await getAllWorkspaces();

        if (!isActive) return; // Check again after async call

        setWorkspaceCount(workspaces.length);

        if (workspaces.length > 0) {
          // Workspace detected - move to stage 2
          setHasWorkspace(true);
          setStatus('polling-initiatives');
        } else {
          // Continue polling for workspace
          setTimeout(pollWorkspaces, 3000);
        }
      } catch (error) {
        // Log error but continue polling
        console.error('Error polling workspaces:', error);
        if (isActive) {
          setTimeout(pollWorkspaces, 3000);
        }
      }
    };

    // Start polling
    pollWorkspaces();

    // Cleanup function
    return () => {
      isActive = false;
    };
  }, []); // Only run once on mount

  // Stage 2: Poll for initiative creation (only after workspace exists)
  useEffect(() => {
    if (status !== 'polling-initiatives') return;

    let isActive = true;

    const pollInitiatives = async () => {
      if (!isActive) return;

      try {
        const initiatives = await getAllInitiatives();

        if (!isActive) return; // Check again after async call

        setInitiativeCount(initiatives.length);

        if (initiatives.length > 0) {
          // Initiatives detected - complete onboarding
          setHasInitiatives(true);
          setStatus('complete');
        } else {
          // Continue polling for initiatives
          setTimeout(pollInitiatives, 3000);
        }
      } catch (error) {
        // Log error but continue polling
        console.error('Error polling initiatives:', error);
        if (isActive) {
          setTimeout(pollInitiatives, 3000);
        }
      }
    };

    // Start polling
    pollInitiatives();

    // Cleanup function
    return () => {
      isActive = false;
    };
  }, [status]); // Re-run when status changes to 'polling-initiatives'

  return {
    status,
    hasWorkspace,
    hasInitiatives,
    workspaceCount,
    initiativeCount,
  };
}
