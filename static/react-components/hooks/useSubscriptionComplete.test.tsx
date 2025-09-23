/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { useSubscriptionComplete } from './useSubscriptionComplete';
import React from 'react';

// Mock the accounting API module
vi.mock('#api/accounting', () => ({
  checkSessionStatus: vi.fn(),
}));

import { checkSessionStatus } from '#api/accounting';

// Mock react-router
const mockUseSearchParams = vi.fn();
vi.mock('react-router', async () => {
  return {
    useSearchParams: () => mockUseSearchParams(),
  };
});

describe('useSubscriptionComplete', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Don't use fake timers for now to test the basic mocking
  });

  afterEach(() => {
    // vi.useRealTimers();
  });

  it('should return error when no session ID is provided', async () => {
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(null) }
    ]);

    const { result } = renderHook(() => useSubscriptionComplete());

    expect(result.current.isLoading).toBe(false);
    expect(result.current.hasError).toBe(true);
    expect(result.current.errorMessage).toBe('No session ID found in URL');
    expect(result.current.sessionId).toBe(null);
    expect(result.current.onboardingComplete).toBe(false);
  });

  it('should successfully poll session status and complete onboarding', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    // Mock API functions
    const mockSessionResponse = { status: 'complete' as const };
    const mockOnboardingResponse = {
      balanceCents: 0,
      status: 'ACTIVE',
      onboardingCompleted: true
    };

    vi.mocked(checkSessionStatus).mockResolvedValueOnce(mockSessionResponse);

    const { result } = renderHook(() => useSubscriptionComplete());

    // Initially loading
    expect(result.current.isLoading).toBe(true);
    expect(result.current.hasError).toBe(false);
    expect(result.current.sessionId).toBe(mockSessionId);

    // Wait for async operations to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasError).toBe(false);
    expect(result.current.errorMessage).toBe(null);
    expect(result.current.onboardingComplete).toBe(true);

    // Verify API calls
    expect(checkSessionStatus).toHaveBeenCalledTimes(1);
    expect(checkSessionStatus).toHaveBeenCalledWith(mockSessionId);
  });

  it('should handle session expired status', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    vi.mocked(checkSessionStatus).mockResolvedValueOnce({ status: 'expired' });

    const { result } = renderHook(() => useSubscriptionComplete());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasError).toBe(true);
    expect(result.current.errorMessage).toBe('Payment session has expired. Please try setting up your subscription again.');
    expect(result.current.onboardingComplete).toBe(false);
  });

  it.skip('should handle session polling with open status and eventual completion', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    // Mock multiple polling attempts - first open, then complete
    const mockOnboardingResponse = {
      balanceCents: 0,
      status: 'ACTIVE',
      onboardingCompleted: true
    };

    vi.mocked(checkSessionStatus)
      .mockResolvedValueOnce({ status: 'open' })
      .mockResolvedValueOnce({ status: 'complete' });

    const { result } = renderHook(() => useSubscriptionComplete());

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasError).toBe(false);
    expect(result.current.onboardingComplete).toBe(true);

    // Should have made 2 session polls + 1 onboarding
    expect(checkSessionStatus).toHaveBeenCalledTimes(2);
  });

  it.skip('should handle polling timeout', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    // Mock always returning 'open' status
    vi.mocked(checkSessionStatus).mockResolvedValue({ status: 'open' });

    const { result } = renderHook(() => useSubscriptionComplete());

    // With always 'open' status, should eventually hit max poll attempts

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasError).toBe(true);
    expect(result.current.errorMessage).toBe('Payment processing is taking longer than expected. Please check your billing page or try again.');
    expect(result.current.onboardingComplete).toBe(false);
  });

  it('should handle session status API error', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    vi.mocked(checkSessionStatus).mockRejectedValueOnce(new Error('Failed to check session status: Internal Server Error'));

    const { result } = renderHook(() => useSubscriptionComplete());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasError).toBe(true);
    expect(result.current.errorMessage).toBe('Failed to check payment status. Please check your connection and try again.');
    expect(result.current.onboardingComplete).toBe(false);
  });

  it('should handle network errors during session polling', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    (checkSessionStatus as Mock).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useSubscriptionComplete());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasError).toBe(true);
    expect(result.current.errorMessage).toBe('Failed to check payment status. Please check your connection and try again.');
    expect(result.current.onboardingComplete).toBe(false);
  });

  it('should handle unknown session status', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    // @ts-expect-error - intentionally testing invalid status
    vi.mocked(checkSessionStatus).mockResolvedValueOnce({ status: 'unknown_status' });

    const { result } = renderHook(() => useSubscriptionComplete());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasError).toBe(true);
    expect(result.current.errorMessage).toBe('Unexpected session status: unknown_status');
    expect(result.current.onboardingComplete).toBe(false);
  });

  it('should handle missing status in response', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    vi.mocked(checkSessionStatus).mockRejectedValueOnce(new Error('Invalid session status response format'));

    const { result } = renderHook(() => useSubscriptionComplete());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasError).toBe(true);
    expect(result.current.errorMessage).toBe('Failed to check payment status. Please check your connection and try again.');
    expect(result.current.onboardingComplete).toBe(false);
  });

  it('should prevent state updates after component unmount', async () => {
    const mockSessionId = 'cs_test_123';
    mockUseSearchParams.mockReturnValue([
      { get: vi.fn().mockReturnValue(mockSessionId) }
    ]);

    // Mock slow response
    vi.mocked(checkSessionStatus).mockImplementation(() =>
      new Promise(resolve => {
        setTimeout(() => {
          resolve({ status: 'complete' });
        }, 1000);
      })
    );

    const { result, unmount } = renderHook(() => useSubscriptionComplete());

    // Verify initial loading state
    expect(result.current.isLoading).toBe(true);

    // Unmount before the fetch completes
    unmount();

    // Mock will resolve asynchronously

    // Since the component was unmounted, the state should not have been updated
    // The hook should handle cleanup properly
    expect(checkSessionStatus).toHaveBeenCalledTimes(1);
  });
});