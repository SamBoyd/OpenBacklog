import { PostgrestClient, PostgrestResponse } from '@supabase/postgrest-js';
import { loadAndValidateJWT, checkJwtAndRenew, renewJWT } from './jwt';

export const REST_URL = process.env.POSTGREST_URL || '';

/**
 * Wraps a function that may encounter JWT expiration issues
 * @param operation Function to execute that may need JWT renewal
 * @returns Result of the operation after handling any JWT issues
 */
export async function withJwtHandling<T>(operation: () => Promise<T>): Promise<T> {
    try {
        // Check and renew JWT if needed before the operation
        await checkJwtAndRenew();

        // Execute the operation
        return await operation();
    } catch (error) {
        // If we get a JWT-related error, try to renew the token and retry
        if (error instanceof Error &&
            (error.message.includes('JWT') ||
                error.message.includes('401') ||
                error.message.includes('auth'))) {
            try {
                await renewJWT();
                // Retry the operation with a fresh token
                return await operation();
            } catch (renewError) {
                throw new Error('Session expired. Please log in again.');
            }
        }
        throw error;
    }
}

/**
 * Creates a PostgrestClient with the current JWT token
 */
export const createPostgrestClient = () => {
    return new PostgrestClient(REST_URL, {
        headers: {
            'Prefer': 'resolution=merge-duplicates',
            Authorization: `Bearer ${loadAndValidateJWT()}`,
            schema: 'dev',
        },
    });
};

/**
 * Gets a PostgrestClient with the current JWT
 * Use this when you want to make direct calls to the API
 */
export const getPostgrestClient = () => {
    return createPostgrestClient();
};

/**
 * Helper function to wrap API calls with JWT handling
 * Use this for all API operations that require authentication
 * 
 * Example usage:
 * ```
 * export async function getAllWorkspaces(): Promise<WorkspaceDto[]> {
 *     return withApiCall(async () => {
 *         const response = await getPostgrestClient()
 *             .from('workspace')
 *             .select('*');
 *         
 *         // Process response...
 *         return processedData;
 *     });
 * }
 * ```
 */
export async function withApiCall<T>(apiCall: () => Promise<T>): Promise<T> {
    return withJwtHandling(apiCall);
}
