/**
 * Enum representing the status of a user's account
 * Matches the backend UserAccountStatus enum
 */
export enum UserAccountStatus {
    NEW = "NEW",
    ACTIVE_SUBSCRIPTION = "ACTIVE_SUBSCRIPTION",
    NO_SUBSCRIPTION = "NO_SUBSCRIPTION",
    METERED_BILLING = "METERED_BILLING",
    SUSPENDED = "SUSPENDED",
    CLOSED = "CLOSED"
}

/**
 * Helper function to check if a user is onboarded
 * A user is considered onboarded if their status is not NEW OR if they have completed onboarding
 * @param status - The user's account status
 * @param onboardingCompleted - Whether the user has completed the onboarding process
 * @returns True if the user is onboarded, false otherwise
 */
export const isUserOnboarded = (status: UserAccountStatus, onboardingCompleted?: boolean): boolean => {
    return status !== UserAccountStatus.NEW || (onboardingCompleted === true);
};
