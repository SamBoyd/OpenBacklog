import { useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { getInstallationStatus } from '#api/githubInstallation';
import { GitHubInstallationStatus } from '#api/githubInstallation';

/**
 * Interface for the return value of useGithubInstallation hook
 */
export interface GithubInstallationHookResult {
    /** Whether the user has a GitHub installation */
    hasInstallation: boolean;
    /** Number of repositories connected */
    repositoryCount: number;
    /** Whether installation status is being loaded */
    isLoading: boolean;
    /** Error that occurred during fetch, if any */
    error: Error | null;
    /** Function to manually refresh installation status */
    refresh: () => void;
}

/**
 * Query keys for GitHub installation-related queries
 */
const QUERY_KEYS = {
    installationStatus: ['github', 'installation-status'] as const,
} as const;

/**
 * Custom hook for fetching GitHub installation status
 * @returns {GithubInstallationHookResult} Object containing installation status and operations
 */
export const useGithubInstallation = (): GithubInstallationHookResult => {
    const queryClient = useQueryClient();

    // Query for installation status
    const installationQuery: UseQueryResult<GitHubInstallationStatus, Error> = useQuery({
        queryKey: QUERY_KEYS.installationStatus,
        queryFn: getInstallationStatus,
        refetchInterval: 30 * 1000, // Poll every 30 seconds (consistent with useGithubRepos)
        staleTime: 10 * 1000, // Consider data stale after 10 seconds
        retry: 2,
        throwOnError: false, // Ensure errors are captured in error state
    });

    const refresh = useCallback(() => {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.installationStatus });
    }, [queryClient]);

    // Memoize the return value to prevent unnecessary re-renders
    return useMemo(() => ({
        hasInstallation: installationQuery.data?.has_installation ?? false,
        repositoryCount: installationQuery.data?.repository_count ?? 0,
        isLoading: installationQuery.isLoading,
        error: installationQuery.error,
        refresh,
    }), [
        installationQuery.data?.has_installation,
        installationQuery.data?.repository_count,
        installationQuery.isLoading,
        installationQuery.error,
        refresh,
    ]);
};
