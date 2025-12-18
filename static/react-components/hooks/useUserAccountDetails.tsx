import React, { useEffect, useRef, useState } from 'react';
import { z } from 'zod';
import { useQuery, useQueryClient } from '@tanstack/react-query';

import { UserAccountStatus } from '#constants/userAccountStatus';
import { withApiCall } from '#api/api-utils';
import { getCurrentUserId } from '#api/jwt';
import { SafeStorage } from './useUserPreferences';

/**
 * Schema for user account details
 */
const UserAccountDetailsSchema = z.object({
    status: z.nativeEnum(UserAccountStatus),
    onboardingCompleted: z.boolean()
})

export type UserAccountDetails = z.infer<typeof UserAccountDetailsSchema>;

/**
 * Error class for accounting API related errors
 */
export class AccountingApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = 'AccountingApiError';
        this.status = status;
    }
}


/**
 * Fetches the user's account details
 * 
 * @returns {Promise<UserAccountDetails>} User account details
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getUserAccountDetails = async (): Promise<UserAccountDetails> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/user-account-details', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new AccountingApiError(
                    `Failed to fetch user account details: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = UserAccountDetailsSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error fetching user account details: ${(error as Error).message}`);
        }
    });
};

/**
 * Type validator for UserAccountDetails
 * @param value - Value to validate
 * @returns True if value is a valid UserAccountDetails object
 */
const isUserAccountDetails = (value: unknown): value is UserAccountDetails => {
    return (
        typeof value === 'object' &&
        value !== null &&
        'status' in value &&
        'onboardingCompleted' in value &&
        typeof (value as UserAccountDetails).status === 'string' &&
        typeof (value as UserAccountDetails).onboardingCompleted === 'boolean'
    );
};

/**
 * Cache TTL constants
 */
const CACHE_TTL = {
    USER_ACCOUNT_DETAILS: 24 * 60 * 60 * 1000, // 24 hours
} as const;


export interface UserAccountDetailsReturn {
    userIsOnboarded: boolean;
    isLoading: boolean;
    error: string | null;
    refetch: () => void;
    invalidateUserAccountDetails: () => Promise<void>;
}


export const useUserAccountDetails = (): UserAccountDetailsReturn => {
    const queryClient = useQueryClient();

    // Track current user ID for cache invalidation
    const currentUserId = getCurrentUserId();
    const previousUserIdRef = useRef<string | null>(currentUserId);

    // Check for user changes and clear cache if needed
    useEffect(() => {
        const previousUserId = previousUserIdRef.current;

        if (previousUserId && currentUserId && previousUserId !== currentUserId) {
            // User changed, clear cache for the previous user
            SafeStorage.clearUserCache(previousUserId);
            console.debug('User changed, cleared cache for previous user:', previousUserId);
        }

        previousUserIdRef.current = currentUserId;
    }, [currentUserId]);

    // Clear expired cache on hook initialization
    useEffect(() => {
        SafeStorage.clearExpiredCache();
    }, []);

    // Get cached user account details immediately
    const cachedUserAccountDetails = currentUserId
        ? SafeStorage.safeGetUserScoped(
            'userAccountDetails',
            currentUserId,
            isUserAccountDetails,
            null
        )
        : null;

    // Fetch user account details using TanStack Query with cached initial data
    const {
        data: userAccountDetails,
        isLoading: accountDetailsLoading,
        error: accountDetailsError,
        refetch: refetchAccountDetails
    } = useQuery({
        queryKey: ['userAccountDetails'],
        queryFn: getUserAccountDetails,
        // staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
        refetchOnWindowFocus: false,
        initialData: cachedUserAccountDetails || undefined,
        enabled: !!currentUserId, // Only fetch if we have a user ID
    });

    // Update cache when fresh data is received
    useEffect(() => {
        if (userAccountDetails && currentUserId) {
            SafeStorage.safeSetUserScoped(
                'userAccountDetails',
                currentUserId,
                userAccountDetails,
                CACHE_TTL.USER_ACCOUNT_DETAILS
            );
        }
    }, [userAccountDetails, currentUserId]);
    
    const invalidateUserAccountDetails = async () => {
        // Invalidate query cache
        await queryClient.invalidateQueries({ queryKey: ['userAccountDetails', currentUserId] });

        // Also clear localStorage cache for immediate effect
        if (currentUserId) {
            SafeStorage.safeSetUserScoped(
                'userAccountDetails',
                currentUserId,
                null,
                0 // Immediate expiry to force refetch
            );
        }
    }

    return {
        userIsOnboarded: userAccountDetails?.onboardingCompleted || false,
        isLoading: accountDetailsLoading,
        error: accountDetailsError?.message || null,
        refetch: refetchAccountDetails,
        invalidateUserAccountDetails: invalidateUserAccountDetails,
    };
};