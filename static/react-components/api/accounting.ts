import { z } from 'zod';
import { withApiCall } from './api-utils';
import { UserAccountStatus } from '#constants/userAccountStatus';

/**
 * Schema for billing onboard response
 */
const BillingOnboardResponseSchema = z.object({
    customerId: z.string(),
    stripeCustomerId: z.string(),
    sessionId: z.string(),
    setupIntentId: z.string(),
    url: z.string(),
    mode: z.string(),
    cancelURL: z.string().nullable(),
    successURL: z.string(),
    returnURL: z.string().nullable()
});

/**
 * Schema for transaction data from the ledger
 */
const TransactionSchema = z.object({
    id: z.string().uuid(),
    userId: z.string().uuid(),
    amountCents: z.number(),
    source: z.enum([
        'CREDIT_USAGE',
        'BALANCE_USAGE',
        'STATE_TRANSITION',
        'BALANCE_TOPUP',
        'MONTHLY_CREDITS_RESET',
        'BALANCE_REFUND',
        'SUBSCRIPTION_SIGNUP',
        'SUBSCRIPTION_CANCEL',
        'CHARGEBACK_DETECTED',
    ]),
    externalId: z.string().nullable(),
    createdAt: z.string(),
});

/**
 * Schema for the API response containing transactions
 */
const TransactionsResponseSchema = z.object({
    transactions: z.array(TransactionSchema),
    total_count: z.number(),
    page: z.number(),
    page_size: z.number(),
    has_next: z.boolean()
});

/**
 * Schema for user account details
 */
const UserAccountDetailsSchema = z.object({
    balanceCents: z.number(),
    status: z.nativeEnum(UserAccountStatus),
    onboardingCompleted: z.boolean(),
    monthlyCreditsTotal: z.number().optional(),
    monthlyCreditsUsed: z.number().optional(),
    subscriptionCancelAt: z.string().nullable().optional(),
    subscriptionCanceledAt: z.string().nullable().optional(),
    subscriptionCancelAtPeriodEnd: z.boolean().nullable().optional()
});

/**
 * Schema for open meter token
 */
const OpenMeterTokenResponseSchema = z.object({
    id: z.string(),
    subject: z.string(),
    expiresAt: z.string(),
    token: z.string(),
    allowedMeterSlugs: z.array(z.string())
});

/**
 * Schema for refund request
 */
const RefundRequestSchema = z.object({
    amountCents: z.number().positive()
});

/**
 * Schema for refund result
 */
const RefundResultSchema = z.object({
    success: z.boolean(),
    details: z.string().nullable()
});

/**
 * Schema for pending topup status
 */
const PendingTopupStatusSchema = z.object({
    id: z.string().uuid(),
    userId: z.string().uuid(),
    sessionId: z.string(),
    amountCents: z.number(),
    status: z.enum(['PENDING', 'COMPLETED', 'FAILED', 'CANCELLED']),
    createdAt: z.string(),
    completedAt: z.string().nullable()
});

/**
 * Schema for payment method data
 */
const PaymentMethodDataSchema = z.object({
    id: z.string(),
    type: z.string(),
    cardBrand: z.string().nullable().optional(),
    cardLast4: z.string().nullable().optional(),
    cardExpMonth: z.number().nullable().optional(),
    cardExpYear: z.number().nullable().optional(),
    isDefault: z.boolean()
});

/**
 * Schema for payment methods response
 */
const PaymentMethodsResponseSchema = z.object({
    paymentMethods: z.array(PaymentMethodDataSchema),
    defaultPaymentMethodId: z.string().nullable().optional()
});

/**
 * Schema for customer portal session response
 */
const CustomerPortalSessionResponseSchema = z.object({
    url: z.string()
});

/**
 * Schema for billing details data
 */
const BillingDetailsDataSchema = z.object({
    email: z.string().nullable(),
    name: z.string().nullable(),
    phone: z.string().nullable(),
    addressLine1: z.string().nullable(),
    addressLine2: z.string().nullable(),
    addressCity: z.string().nullable(),
    addressState: z.string().nullable(),
    addressPostalCode: z.string().nullable(),
    addressCountry: z.string().nullable(),
    taxId: z.string().nullable()
});

/**
 * Schema for billing details response
 */
const BillingDetailsResponseSchema = z.object({
    billingDetails: BillingDetailsDataSchema
});

/**
 * Schema for OpenMeter query data point
 */
const OpenMeterQueryDataPointSchema = z.object({
    value: z.number(),
    windowStart: z.string(),
    windowEnd: z.string(),
    subject: z.string().optional(),
    groupBy: z.object({
        model: z.string().optional(),
        direction: z.enum(['input', 'output']).optional(),
    }).optional()
});

/**
 * Schema for OpenMeter query response
 */
const OpenMeterQueryResponseSchema = z.object({
    from: z.string(),
    to: z.string(),
    windowSize: z.string(),
    data: z.array(OpenMeterQueryDataPointSchema)
});

/**
 * Schema for session status response
 */
const SessionStatusResponseSchema = z.object({
    status: z.enum(['complete', 'expired', 'open'])
});

/**
 * Schema for subscription onboarding response
 */
const SubscriptionOnboardingResponseSchema = z.object({
    balanceCents: z.number(),
    status: z.string(),
    onboardingCompleted: z.boolean()
});


/**
 * Type definitions for transaction data
 */
export type Transaction = z.infer<typeof TransactionSchema>;
export type TransactionsResponse = z.infer<typeof TransactionsResponseSchema>;
export type UserAccountDetails = z.infer<typeof UserAccountDetailsSchema>;
export type BillingOnboardResponse = z.infer<typeof BillingOnboardResponseSchema>;
export type OpenMeterTokenResponse = z.infer<typeof OpenMeterTokenResponseSchema>;
export type RefundRequest = z.infer<typeof RefundRequestSchema>;
export type RefundResult = z.infer<typeof RefundResultSchema>;
export type PendingTopupStatus = z.infer<typeof PendingTopupStatusSchema>;
export type PaymentMethodData = z.infer<typeof PaymentMethodDataSchema>;
export type PaymentMethodsResponse = z.infer<typeof PaymentMethodsResponseSchema>;
export type CustomerPortalSessionResponse = z.infer<typeof CustomerPortalSessionResponseSchema>;
export type BillingDetailsData = z.infer<typeof BillingDetailsDataSchema>;
export type BillingDetailsResponse = z.infer<typeof BillingDetailsResponseSchema>;
export type OpenMeterQueryDataPoint = z.infer<typeof OpenMeterQueryDataPointSchema>;
export type OpenMeterQueryResponse = z.infer<typeof OpenMeterQueryResponseSchema>;
export type SessionStatusResponse = z.infer<typeof SessionStatusResponseSchema>;
export type SubscriptionOnboardingResponse = z.infer<typeof SubscriptionOnboardingResponseSchema>;

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
 * Fetches the user's transaction history from the ledger with pagination
 * 
 * @param page - Page number (1-based, defaults to 1)
 * @param pageSize - Number of transactions per page (defaults to 20)
 * @returns {Promise<TransactionsResponse>} Paginated transactions response
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getUserTransactions = async (page: number = 1, pageSize: number = 20): Promise<TransactionsResponse> => {
    return withApiCall(async () => {
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                page_size: pageSize.toString()
            });

            const response = await fetch(`/api/accounting/transactions?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new AccountingApiError(
                    `Failed to fetch transactions: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = TransactionsResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error fetching transactions: ${(error as Error).message}`);
        }
    });
};

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
            const response = await fetch('/api/accounting/user-account-details', {
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


export const getOpenMeterTokenData = async (): Promise<OpenMeterTokenResponse> => {
    return withApiCall(async () => {
        const response = await fetch(
            '/api/accounting/openmeter-token', {
            method: 'POST',
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new AccountingApiError(
                `Failed to fetch open meter token: ${errorText}`,
                response.status
            );
        }

        const data = await response.json();
        const validatedData = OpenMeterTokenResponseSchema.parse(data);

        return validatedData;
    });
};

/**
 * Process a refund for the current user
 * 
 * @param request - The refund request
 * @returns {Promise<RefundResult>} The refund result
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const processRefund = async (request: RefundRequest): Promise<RefundResult> => {
    return withApiCall(async () => {
        const response = await fetch('/api/accounting/refund', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount_cents: request.amountCents
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new AccountingApiError(
                `Failed to process refund: ${errorText}`,
                response.status
            );
        }

        const data = await response.json();
        const validatedData = RefundResultSchema.parse(data);

        return validatedData;
    });
};

/**
 * Schema for topup request
 */
const TopupRequestSchema = z.object({
    amount_cents: z.number()
});

/**
 * Schema for topup response
 */
const TopupResponseSchema = z.object({
    ok: z.boolean(),
    redirect_url: z.string()
});

export type TopupResponse = z.infer<typeof TopupResponseSchema>;

/**
 * Top up the user's account with the amount of the checkout session
 * 
 * @param amount_cents - The amount to top up in cents
 * @returns {Promise<TopupResponse | undefined>} - The response from the API
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const topupAccount = async (amount_cents: number): Promise<TopupResponse | undefined> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/billing/topup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ amount_cents }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new AccountingApiError(
                    `Failed to top up account: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = TopupResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error topping up account: ${(error as Error).message}`);
        }
    });
};

/**
 * Get the current user's pending topup status
 * 
 * @returns {Promise<PendingTopupStatus | null>} The pending topup status or null if none exists
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getPendingTopupStatus = async (): Promise<PendingTopupStatus | null> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/accounting/pending-topup', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.status === 404) {
                return null;
            }

            if (!response.ok) {
                const errorText = await response.text();
                throw new AccountingApiError(
                    `Failed to fetch pending topup status: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = PendingTopupStatusSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error fetching pending topup status: ${(error as Error).message}`);
        }
    });
};

/**
 * Fetches the user's payment methods from Stripe
 * 
 * @returns {Promise<PaymentMethodsResponse>} User payment methods
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getPaymentMethods = async (): Promise<PaymentMethodsResponse> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/billing/payment-methods', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new AccountingApiError(
                    `Failed to fetch payment methods: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = PaymentMethodsResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error fetching payment methods: ${(error as Error).message}`);
        }
    });
};

/**
 * Creates a Stripe customer portal session for the current user
 * 
 * @returns {Promise<CustomerPortalSessionResponse>} Customer portal session with URL
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getCustomerPortalSession = async (): Promise<CustomerPortalSessionResponse> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/billing/customer-portal-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new AccountingApiError(
                    `Failed to create customer portal session: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = CustomerPortalSessionResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error creating customer portal session: ${(error as Error).message}`);
        }
    });
};

/**
 * Fetches the user's billing details from Stripe
 * 
 * @returns {Promise<BillingDetailsResponse>} User billing details
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getBillingDetails = async (): Promise<BillingDetailsResponse> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/billing/billing-details', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new AccountingApiError(
                    `Failed to fetch billing details: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = BillingDetailsResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error fetching billing details: ${(error as Error).message}`);
        }
    });
};

/**
 * Queries the OpenMeter customer portal API for tokens data
 * 
 * @param meterSlug - The meter slug to query (e.g., 'tokens_total')
 * @param windowSize - The window size for data aggregation (e.g., 'DAY', 'HOUR')
 * @param from - The start date for the query (ISO string)
 * @param to - The end date for the query (ISO string)
 * @param openMeterToken - The OpenMeter API token
 * @returns {Promise<OpenMeterQueryResponse>} The query response data
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const queryOpenMeterData = async (
    meterSlug: string,
    windowSize: string,
    from: string,
    to: string,
    openMeterToken: string
): Promise<OpenMeterQueryResponse> => {
    return withApiCall(async () => {
        try {
            const queryParams = new URLSearchParams({
                windowSize,
                from,
                to,
            });

            const response = await fetch(`https://openmeter.cloud/api/v1/portal/meters/${meterSlug}/query?${queryParams.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${openMeterToken}`,
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new AccountingApiError(
                    `Failed to query OpenMeter data: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = OpenMeterQueryResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid OpenMeter response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error querying OpenMeter data: ${(error as Error).message}`);
        }
    });
};

/**
 * Check the status of a Stripe checkout session
 * 
 * @param sessionId - The Stripe session ID to check
 * @returns {Promise<SessionStatusResponse>} The session status
 * @throws {AccountingApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const checkSessionStatus = async (sessionId: string): Promise<SessionStatusResponse> => {
    return withApiCall(async () => {
        try {
            const response = await fetch(`/api/session-status?session_id=${sessionId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new AccountingApiError(
                    `Failed to check session status: ${response.statusText}`,
                    response.status
                );
            }

            const data = await response.json();

            if (!data.status) {
                throw new Error('No status found in response');
            }

            const validatedData = SessionStatusResponseSchema.parse(data);
            return validatedData;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid session status response format: ${error.message}`);
            }
            if (error instanceof AccountingApiError) {
                throw error;
            }
            throw new Error(`Error checking session status: ${(error as Error).message}`);
        }
    });
};
