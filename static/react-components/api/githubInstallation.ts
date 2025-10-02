import { z } from 'zod';
import { withApiCall } from './api-utils';

// Zod schema for validation
const GitHubInstallationStatusSchema = z.object({
    has_installation: z.boolean(),
    repository_count: z.number(),
});

// TypeScript interface
export interface GitHubInstallationStatus {
    has_installation: boolean;
    repository_count: number;
}

/**
 * Custom error class for GitHub installation API errors
 */
export class GitHubInstallationApiError extends Error {
    public status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = 'GitHubInstallationApiError';
        this.status = status;
    }
}

/**
 * Fetches the GitHub installation status for the current user
 *
 * @returns Promise<GitHubInstallationStatus> - Installation status with has_installation and repository_count
 * @throws {GitHubInstallationApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getInstallationStatus = async (): Promise<GitHubInstallationStatus> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/github/installation-status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new GitHubInstallationApiError(
                    `Failed to fetch GitHub installation status: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = GitHubInstallationStatusSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof GitHubInstallationApiError) {
                throw error;
            }
            throw new Error(`Unexpected error fetching installation status: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    });
};
