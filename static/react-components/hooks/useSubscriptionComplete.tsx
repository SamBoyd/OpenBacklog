import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';
import {
  checkSessionStatus,
  type SessionStatusResponse,
  type SubscriptionOnboardingResponse
} from '#api/accounting';


/**
 * State interface for the subscription completion flow
 */
interface SubscriptionCompleteState {
  isLoading: boolean;
  hasError: boolean;
  errorMessage: string | null;
  onboardingComplete: boolean;
}

/**
 * Hook return type
 */
interface UseSubscriptionCompleteReturn extends SubscriptionCompleteState {
  sessionId: string | null;
}

/**
 * Custom hook to handle subscription completion flow.
 * 
 * This hook manages the entire post-subscription process:
 * 1. Extracts session ID from URL parameters
 * 2. Polls session status until completion
 * 3. Automatically triggers OpenMeter onboarding after successful subscription
 * 4. Manages loading, error, and success states
 * 
 * @returns {UseSubscriptionCompleteReturn} State and session information
 */
export const useSubscriptionComplete = (): UseSubscriptionCompleteReturn => {
  const [searchParams] = useSearchParams();
  const [state, setState] = useState<SubscriptionCompleteState>({
    isLoading: true,
    hasError: false,
    errorMessage: null,
    onboardingComplete: false,
  });

  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    if (!sessionId) {
      setState({
        isLoading: false,
        hasError: true,
        errorMessage: "No session ID found in URL",
        onboardingComplete: false,
      });
      return;
    }

    let pollCount = 0;
    const maxPollAttempts = 30; // 30 attempts × 3 seconds = 90 seconds timeout
    let isActive = true; // Flag to prevent state updates after unmount

    const pollSessionStatus = async (): Promise<void> => {
      if (!isActive) return;

      try {
        const data = await checkSessionStatus(sessionId);
        const status = data.status;

        if (status === 'complete') {
          if (isActive) {
            setState({
              isLoading: false,
              hasError: false,
              errorMessage: null,
              onboardingComplete: true,
            });
          }
          return; // Exit polling
        } else if (status === 'expired') {
          // Session expired - stop polling and show error
          if (isActive) {
            setState({
              isLoading: false,
              hasError: true,
              errorMessage: "Payment session has expired. Please try setting up your subscription again.",
              onboardingComplete: false,
            });
          }
          return; // Exit polling
        } else if (status === 'open') {
          // Still processing - continue polling
          pollCount++;
          if (pollCount >= maxPollAttempts) {
            // Timeout - stop polling and show error
            if (isActive) {
              setState({
                isLoading: false,
                hasError: true,
                errorMessage: "Payment processing is taking longer than expected. Please check your billing page or try again.",
                onboardingComplete: false,
              });
            }
            return; // Exit polling
          }
          // Continue polling after 3 seconds
          setTimeout(pollSessionStatus, 3000);
        } else {
          // Unknown status - treat as error
          if (isActive) {
            setState({
              isLoading: false,
              hasError: true,
              errorMessage: `Unexpected session status: ${status}`,
              onboardingComplete: false,
            });
          }
          return; // Exit polling
        }
      } catch (err) {
        // Network or other error
        if (isActive) {
          setState({
            isLoading: false,
            hasError: true,
            errorMessage: "Failed to check payment status. Please check your connection and try again.",
            onboardingComplete: false,
          });
        }
        console.error('Session status polling error:', err);
        return; // Exit polling
      }
    };

    // Start polling immediately
    pollSessionStatus();

    // Cleanup function to prevent state updates after unmount
    return () => {
      isActive = false;
    };
  }, [sessionId]);

  return {
    ...state,
    sessionId,
  };
};

export default useSubscriptionComplete;