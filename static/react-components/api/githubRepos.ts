import { z } from 'zod';
import { withApiCall } from './api-utils';

// Zod schemas for validation
const RepositoryFileDataSchema = z.object({
    repository_full_name: z.string(),
    file_search_string: z.string(),
    updated_at: z.string(),
});

const FileSearchStringResponseSchema = z.object({
    repository_full_name: z.string(),
    file_search_string: z.string(),
    updated_at: z.string(),
    success: z.boolean(),
});

const AllFileSearchStringsResponseSchema = z.object({
    repositories: z.array(RepositoryFileDataSchema),
    total_repositories: z.number(),
    success: z.boolean(),
});

const RepositoryNamesResponseSchema = z.object({
    repository_names: z.array(z.string()),
    repository_timestamps: z.record(z.string(), z.string()), // repo_name -> ISO timestamp
    total_repositories: z.number(),
    success: z.boolean(),
});

// TypeScript interfaces
export interface RepositoryFileData {
    repository_full_name: string;
    file_search_string: string;
    updated_at: string;
}

export interface FileSearchStringResponse {
    repository_full_name: string;
    file_search_string: string;
    updated_at: string;
    success: boolean;
}

export interface AllFileSearchStringsResponse {
    repositories: RepositoryFileData[];
    total_repositories: number;
    success: boolean;
}

export interface RepositoryNamesResponse {
    repository_names: string[];
    repository_timestamps: Record<string, string>; // repo_name -> ISO timestamp
    total_repositories: number;
    success: boolean;
}

/**
 * Custom error class for GitHub API errors
 */
export class GitHubApiError extends Error {
    public status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = 'GitHubApiError';
        this.status = status;
    }
}

/**
 * Fetches the file search string for a specific GitHub repository
 *
 * @param repositoryFullName - The full name of the repository (e.g., "owner/repo")
 * @returns Promise<FileSearchStringResponse> - The repository's file search string data
 * @throws {GitHubApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getFileSearchString = async (repositoryFullName: string): Promise<FileSearchStringResponse> => {
    return withApiCall(async () => {
        try {
            const response = await fetch(`/api/github/file-search-string?repository_full_name=${encodeURIComponent(repositoryFullName)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new GitHubApiError(
                    `Failed to fetch file search string for repository ${repositoryFullName}: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = FileSearchStringResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof GitHubApiError) {
                throw error;
            }
            throw new Error(`Unexpected error fetching file search string: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    });
};

/**
 * Fetches file search strings for all GitHub repositories accessible to the user
 *
 * @returns Promise<AllFileSearchStringsResponse> - All repositories' file search string data
 * @throws {GitHubApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getAllFileSearchStrings = async (): Promise<AllFileSearchStringsResponse> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/github/file-search-strings', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new GitHubApiError(
                    `Failed to fetch all file search strings: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = AllFileSearchStringsResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof GitHubApiError) {
                throw error;
            }
            throw new Error(`Unexpected error fetching all file search strings: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    });
};

/**
 * Fetches lightweight list of repository names for cache validation
 *
 * Returns only repository names (~1KB) instead of full file search strings (~100KB+)
 * for efficient cache invalidation detection.
 *
 * @returns Promise<RepositoryNamesResponse> - Repository names only (minimal payload)
 * @throws {GitHubApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getRepositoryNames = async (): Promise<RepositoryNamesResponse> => {
    return withApiCall(async () => {
        try {
            const response = await fetch('/api/github/repository-names', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new GitHubApiError(
                    `Failed to fetch repository names: ${errorText}`,
                    response.status
                );
            }

            const data = await response.json();
            const validatedData = RepositoryNamesResponseSchema.parse(data);

            return validatedData;
        } catch (error) {
            if (error instanceof GitHubApiError) {
                throw error;
            }
            throw new Error(`Unexpected error fetching repository names: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    });
};
