import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getUserTransactions, getUserAccountDetails, Transaction as ApiTransaction, topupAccount, processRefund, RefundResult, getCustomerPortalSession, queryOpenMeterData, OpenMeterQueryResponse, UserAccountDetails } from '#api/accounting';
import { getCurrentUserId } from '#api/jwt';
import { SafeStorage } from './useUserPreferences';


/**
 * Interface for transaction data
 */
interface Transaction {
    id: number;
    date: string;
    type: string;
    amount: number;
}

/**
 * Interface for billing usage data
 */
export interface BillingUsageData {
    currentBalance: number;
    transactions: Transaction[];
    transactionsPagination: {
        totalCount: number;
        page: number;
        pageSize: number;
        hasNext: boolean;
    } | null;
    subscriptionStatus: string;
    monthlyCreditsTotal: number;
    monthlyCreditsUsed: number;
}

export interface UseBillingUsageReturn {
    data: BillingUsageData;
    userAccountDetails: UserAccountDetails | undefined;
    userIsOnboarded: boolean;
    autoTopUp: boolean;
    setAutoTopUp: (autoTopUp: boolean) => void;
    onboardCustomer: () => void;
    setupMonthlySubscription: () => Promise<void>;
    handleAddCredit: (amount_cents: number) => void;
    formatCurrency: (amount: number) => string;
    formatNumber: (num: number) => string;
    isLoading: boolean;
    isAccountDetailsLoading: boolean;
    error: Error | null;
    // Payment dialog states
    showErrorDialog: boolean;
    showPendingDialog: boolean;
    showCancelledDialog: boolean;
    closeErrorDialog: () => void;
    closePendingDialog: () => void;
    closeCancelledDialog: () => void;
    handlePaymentRetry: () => void;
    handlePaymentSuccess: () => void;
    handlePaymentFailure: () => void;
    handleRefundRequest: () => Promise<RefundResult>;
    handleOpenCustomerPortal: () => Promise<void>;
    // Pagination functions
    loadTransactionsPage: (page: number) => void;
    resetTransactionsPagination: () => void;
    invalidateUserAccountDetails: () => Promise<void>;
}

/**
 * Converts API transaction data to UI transaction format
 * @param {ApiTransaction} apiTransaction - Transaction from API
 * @returns {Transaction} Transaction in UI format
 */
const convertApiTransactionToUI = (apiTransaction: ApiTransaction): Transaction => {
    const amount = apiTransaction.amountCents / 100; // Convert cents to dollars

    // Created at given in form: "2025-07-01T13:36:40.745496"
    const date = new Date(apiTransaction.createdAt.split('T')[0]).toDateString();

    // Determine transaction type and method based on source
    let type: string;

    switch (apiTransaction.source) {
        case 'CREDIT_USAGE':
            type = 'Usage (included in monthly credits)';
            break;
        case 'BALANCE_USAGE':
            type = 'Usage (deducted from balance)';
            break;
        case 'BALANCE_TOPUP':
            type = 'Balance topup';
            break;
        case 'MONTHLY_CREDITS_RESET':
            type = 'Monthly credit reset';
            break;
        case 'BALANCE_REFUND':
            type = 'Balance refund';
            break;
        case 'SUBSCRIPTION_SIGNUP':
            type = 'Subscription signup';
            break;
        case 'SUBSCRIPTION_CANCEL':
            type = 'Subscription cancel';
            break;
        case 'CHARGEBACK_DETECTED':
            type = 'Chargeback';
            break;
        default:
            type = 'Transaction';
            break;
    }

    return {
        id: parseInt(apiTransaction.id.replace(/-/g, '').substring(0, 8), 16), // Convert UUID to number
        date,
        type,
        amount,
    };
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
        'balanceCents' in value &&
        'status' in value &&
        'onboardingCompleted' in value &&
        typeof (value as UserAccountDetails).balanceCents === 'number' &&
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

/**
 * Custom hook for managing billing and usage data with user-scoped caching
 * @returns {useBillingUsageReturn} Billing usage data and state management functions
 */
export const useBillingUsage = (): UseBillingUsageReturn => {
    const queryClient = useQueryClient();
    const [autoTopUp, setAutoTopUp] = useState(false);
    const [showErrorDialog, setShowErrorDialog] = useState(false);
    const [showPendingDialog, setShowPendingDialog] = useState(false);
    const [showCancelledDialog, setShowCancelledDialog] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [allTransactions, setAllTransactions] = useState<Transaction[]>([]);
    const [transactionsPagination, setTransactionsPagination] = useState<{
        totalCount: number;
        page: number;
        pageSize: number;
        hasNext: boolean;
    } | null>(null);

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

    // Billing details URL parameter handling will be added after queries are defined

    // Fetch real transaction data using TanStack Query with pagination
    const {
        data: transactionsResponse,
        isLoading: transactionsLoading,
        error: transactionsError,
        refetch: refetchTransactions
    } = useQuery({
        queryKey: ['userTransactions', currentPage],
        queryFn: () => getUserTransactions(currentPage, 20),
        staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
        refetchOnWindowFocus: false,
    });

    // Update local state when new transaction data is fetched
    useEffect(() => {
        if (transactionsResponse) {
            const newTransactions = transactionsResponse.transactions.map(convertApiTransactionToUI);
            
            setAllTransactions(newTransactions);

            setTransactionsPagination({
                totalCount: transactionsResponse.total_count,
                page: transactionsResponse.page,
                pageSize: transactionsResponse.page_size,
                hasNext: transactionsResponse.has_next
            });
        }
    }, [transactionsResponse, currentPage]);

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
        queryKey: ['userAccountDetails', currentUserId],
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

    /**
     * Handles URL parameters for payment redirects and customer portal returns
     */
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        const pending = urlParams.get('pending');
        const cancelled = urlParams.get('cancelled');

        if (error) {
            setShowErrorDialog(true);
            // Clear the URL parameters
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('error');
            window.history.replaceState({}, '', newUrl.toString());
        } else if (pending) {
            setShowPendingDialog(true);
            // Clear the URL parameters
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('pending');
            window.history.replaceState({}, '', newUrl.toString());
        } else if (cancelled === 'true') {
            setShowCancelledDialog(true);
            // Clear the URL parameters
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('cancelled');
            window.history.replaceState({}, '', newUrl.toString());
        }
    }, []);

    // Calculate current balance from transactions
    const currentBalance = userAccountDetails?.balanceCents ? userAccountDetails.balanceCents / 100 : 0;

    // Determine if user is onboarded based on account status and onboarding completion using the helper function
    const userIsOnboarded = userAccountDetails ? userAccountDetails.onboardingCompleted : false;

    /**
     * Handles adding credit to the account by creating a billing onboarding session
     * and redirecting to the Stripe checkout URL
     */
    const handleAddCredit = async (amount_cents: number) => {
        try {
            const response = await topupAccount(amount_cents);
            if (response) {
                window.location.href = response.redirect_url;
            } else {
                alert('Failed to top up account. Please try again.');
            }
        } catch (error) {
            console.error('Failed to top up account:', error);
            alert('Failed to top up account. Please try again.');
        }
    };

    /**
     * Handles onboarding a customer by creating a billing onboarding session
     * and redirecting to the Stripe checkout URL
     */
    const onboardCustomer = async () => {
        // TODO: Deprecated - remove this function
        console.warn('onboardCustomer is deprecated and will be removed in the future');
        return Promise.reject(new Error('onboardCustomer is deprecated and will be removed in the future'));
    }

    /**
     * Handles setting up a monthly subscription by creating a subscription onboarding session
     * and redirecting to the Stripe checkout URL
     */
    const setupMonthlySubscription = async () => {
        // TODO: Deprecated - remove this function
        return Promise.reject(new Error('setupMonthlySubscription is deprecated and will be removed in the future'));
    }

    /**
     * Formats currency values
     * @param {number} amount - The amount to format
     * @returns {string} Formatted currency string
     */
    const formatCurrency = (amount: number): string => {
        if (amount < 1) {
            // format to at most 7 decimal places with no trailing zeros
            return amount.toFixed(7).replace(/\.?0+$/, '');
        }
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    /**
     * Formats number values with commas
     * @param {number} num - The number to format
     * @returns {string} Formatted number string
     */
    const formatNumber = (num: number): string => {
        return new Intl.NumberFormat('en-US').format(num);
    };

    const data: BillingUsageData = {
        currentBalance,
        transactions: allTransactions,
        transactionsPagination,
        subscriptionStatus: userAccountDetails?.status || 'NEW',
        monthlyCreditsTotal: userAccountDetails?.monthlyCreditsTotal || 500,
        monthlyCreditsUsed: userAccountDetails?.monthlyCreditsUsed || 0,
    };

    const closeErrorDialog = () => setShowErrorDialog(false);
    const closePendingDialog = () => setShowPendingDialog(false);
    const closeCancelledDialog = () => setShowCancelledDialog(false);

    const handlePaymentRetry = () => {
        closeErrorDialog();
        closeCancelledDialog();
        // The user can retry by clicking the "Add Credit" button again
    };

    const handlePaymentSuccess = () => {
        closePendingDialog();
        // Refresh the data to show updated balance
        window.location.reload();
    };

    const handlePaymentFailure = () => {
        closePendingDialog();
        setShowErrorDialog(true);
    };

    const handleRefundRequest = async (): Promise<RefundResult> => {
        if (!currentBalance) {
            return { success: false, details: 'No balance available to refund.' } as RefundResult;
        }

        const payload = {
            amountCents: currentBalance * 100
        };

        try {
            const response = await processRefund(payload);
            // Refetch data regardless of success to keep UI in sync
            setCurrentPage(1); // Reset to first page
            refetchTransactions();
            refetchAccountDetails();
            return response;
        } catch (error) {
            console.error('Failed to refund account:', error);
            return { success: false, details: 'Failed to process refund. Please try again.' } as RefundResult;
        }
    };

    const loadTransactionsPage = (page: number) => {
        setCurrentPage(page);
    };

    const resetTransactionsPagination = () => {
        setCurrentPage(1);
        setAllTransactions([]);
        setTransactionsPagination(null);
    };

    const handleOpenCustomerPortal = async () => {
        try {
            // Create customer portal session
            const response = await getCustomerPortalSession();

            // Redirect to customer portal URL
            window.location.href = response.url;
        } catch (error) {
            // Remove the flag if there's an error
            console.error('Failed to create customer portal session:', error);
            // In a real implementation, you might want to show a toast notification here
            alert('Failed to create customer portal session. Please try again.');
        }
    };

    return {
        data,
        userAccountDetails,
        userIsOnboarded,
        autoTopUp,
        setAutoTopUp,
        onboardCustomer,
        setupMonthlySubscription,
        handleAddCredit,
        formatCurrency,
        formatNumber,
        isLoading: (accountDetailsLoading && !cachedUserAccountDetails) || transactionsLoading,
        isAccountDetailsLoading: accountDetailsLoading && !cachedUserAccountDetails,
        error: transactionsError || accountDetailsError,
        showErrorDialog,
        showPendingDialog,
        showCancelledDialog,
        closeErrorDialog,
        closePendingDialog,
        closeCancelledDialog,
        handlePaymentRetry,
        handlePaymentSuccess,
        handlePaymentFailure,
        handleRefundRequest,
        handleOpenCustomerPortal,
        loadTransactionsPage,
        resetTransactionsPagination,
        invalidateUserAccountDetails,
    };
}; 