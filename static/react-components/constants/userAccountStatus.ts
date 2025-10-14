/**
 * Enum representing the status of a user's account
 * Matches the backend UserAccountStatus enum
 */
export enum UserAccountStatus {
    NEW = "NEW", // User has not completed onboarding
    ACTIVE_SUBSCRIPTION = "ACTIVE_SUBSCRIPTION", // User has an active subscription
    NO_SUBSCRIPTION = "NO_SUBSCRIPTION", // User has not signed up for a subscription
    METERED_BILLING = "METERED_BILLING", // User has signed up for a subscription but is using metered billing
    SUSPENDED = "SUSPENDED", // User has a subscription but has zero balance
    CLOSED = "CLOSED" // Users account has been closed (usually due to a chargeback)
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

/**
 * Helper function to check if a user has an active subscription
 * Only users with ACTIVE_SUBSCRIPTION status can access AI features
 * @param status - The user's account status
 * @returns True if the user has an active subscription, false otherwise
 */
export const hasActiveSubscription = (status: UserAccountStatus): boolean => {
    return (
        status === UserAccountStatus.ACTIVE_SUBSCRIPTION
        || status === UserAccountStatus.METERED_BILLING
        || status === UserAccountStatus.SUSPENDED
    );
};
