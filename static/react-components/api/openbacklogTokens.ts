import { z } from 'zod';
import { withApiCall } from './api-utils';

/**
 * Zod schema for OpenBacklog token creation response validation
 */
const OpenBacklogTokenResponseSchema = z.object({
    message: z.string(),
    token: z.string(),
    token_id: z.string(),
    redacted_key: z.string(),
    created_at: z.string(),
});

/**
 * TypeScript interface for OpenBacklog token creation response
 */
export interface OpenBacklogTokenResponse {
    message: string;
    token: string;
    token_id: string;
    redacted_key: string;
    created_at: string;
}

/**
 * Custom error class for OpenBacklog token API errors
 */
export class OpenBacklogTokenApiError extends Error {
    public status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = 'OpenBacklogTokenApiError';
        this.status = status;
    }
}

/**
 * Creates a new OpenBacklog Personal Access Token
 *
 * @returns Promise<OpenBacklogTokenResponse> - The created token with full value (only returned once)
 * @throws {OpenBacklogTokenApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const createOpenBacklogToken = async (): Promise<OpenBacklogTokenResponse> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/openbacklog/tokens', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new OpenBacklogTokenApiError(
                    `Failed to create OpenBacklog token: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = OpenBacklogTokenResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof OpenBacklogTokenApiError) {
                throw error;
            }
            throw new Error(`Unexpected error creating token: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    });
};
