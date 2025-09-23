import React, {
    createContext,
    useContext,
    useCallback,
    useMemo,
    useState,
    useEffect,
    ReactNode
} from 'react';
import {
    useQuery,
    useQueryClient,
    UseQueryResult
} from '@tanstack/react-query';
import {
    getAllFileSearchStrings,
    getRepositoryNames
} from '#api/githubRepos';
import {
    RepositoryFileData,
    AllFileSearchStringsResponse
} from '#api/githubRepos';
import { SafeStorage } from './useUserPreferences';
import { getCurrentUserId } from '#api/jwt';

/**
 * Interface for the return value of useGithubRepos hook
 */
export interface GithubReposHookResult {
    /** List of all available repositories with file search strings */
    repositories: RepositoryFileData[];
    /** Whether repositories data is being loaded */
    isLoading: boolean;
    /** Error that occurred during repository operations, if any */
    error: Error | null;
    /** Function to get repository data by name from cached results */
    getRepositoryByName: (repositoryFullName: string) => RepositoryFileData | null;
    /** Function to manually refresh repository data */
    refresh: () => void;
    /** Total number of repositories available */
    totalRepositories: number;
    /** Whether current cache is valid and up-to-date */
    isCacheValid: boolean;
    /** Timestamp when cache was last updated (null if no cache) */
    cacheTimestamp: number | null;
    /** Timestamp when repository list was last checked */
    lastRepoCheck: number | null;
    /** Force refresh bypassing cache */
    forceRefresh: () => void;
    /** Invalidate cache and trigger fresh fetch */
    invalidateCache: () => void;
}

/**
 * Query keys for GitHub repository-related queries
 */
const QUERY_KEYS = {
    allRepositories: ['github', 'repositories'] as const,
    repositoryNames: ['github', 'repository-names'] as const,
} as const;

/**
 * Type validator for cached repository data
 * @param value - The value to validate
 * @returns True if value is a valid array of RepositoryFileData
 */
const repositoriesValidator = (value: unknown): value is RepositoryFileData[] => {
    return Array.isArray(value) && value.every(item =>
        typeof item === 'object' &&
        item !== null &&
        typeof (item as any).repository_full_name === 'string' &&
        typeof (item as any).file_search_string === 'string' &&
        typeof (item as any).updated_at === 'string'
    );
};

/**
 * Cache configuration constants
 */
const CACHE_CONFIG = {
    baseKey: 'github-repos',
    ttlMs: 60 * 60 * 1000, // 1 hour TTL as specified in requirements
} as const;

/**
 * Check if cached repository list matches current available repositories (legacy function)
 * @param cachedRepos - Cached repository data
 * @param currentNames - Current repository names from server
 * @returns True if repository lists match
 */
const areRepositoryListsEqual = (
    cachedRepos: RepositoryFileData[],
    currentNames: string[]
): boolean => {
    const cachedNames = cachedRepos.map(repo => repo.repository_full_name).sort();
    const sortedCurrentNames = [...currentNames].sort();

    if (cachedNames.length !== sortedCurrentNames.length) {
        return false;
    }

    return cachedNames.every((name, index) => name === sortedCurrentNames[index]);
};

/**
 * Check if cached repositories are unchanged (names and timestamps)
 * @param cachedRepos - Cached repository data with timestamps
 * @param currentNames - Current repository names from server
 * @param currentTimestamps - Current repository timestamps from server
 * @returns True if repositories are unchanged
 */
const areRepositoriesUnchanged = (
    cachedRepos: RepositoryFileData[],
    currentNames: string[] | undefined,
    currentTimestamps: Record<string, string> | undefined
): boolean => {
    // If no current data, can't validate
    if (!currentNames || !currentTimestamps) {
        return false;
    }

    // First check if repository lists match (names)
    if (!areRepositoryListsEqual(cachedRepos, currentNames)) {
        return false;
    }

    // Then check if any repository has been updated (timestamps)
    for (const repo of cachedRepos) {
        const repoName = repo.repository_full_name;
        const currentTimestamp = currentTimestamps[repoName];

        if (!currentTimestamp) {
            // Repository no longer exists
            return false;
        }

        // Compare timestamps - if current is newer than cached, cache is stale
        const cachedTime = new Date(repo.updated_at).getTime();
        const currentTime = new Date(currentTimestamp).getTime();

        if (currentTime > cachedTime) {
            return false;
        }
    }

    return true;
};

/**
 * Check if cache has expired based on TTL
 * @param userId - User ID for cache lookup
 * @returns True if cache has expired or doesn't exist
 */
const isCacheExpired = (userId: string | null): boolean => {
    if (!userId) return true;

    try {
        const cacheKey = `${CACHE_CONFIG.baseKey}-${userId}`;
        const storedValue = localStorage.getItem(cacheKey);
        if (!storedValue) return true;

        const cachedData = JSON.parse(storedValue);
        if (!cachedData.timestamp || !cachedData.ttl) return true;

        return (Date.now() - cachedData.timestamp) > cachedData.ttl;
    } catch {
        return true;
    }
};

/**
 * Check if current cache is valid (not expired + repositories unchanged)
 * @param hasCachedData - Whether cached data exists
 * @param cachedData - Current cached repository data
 * @param currentRepoNames - Current repository names from server (optional)
 * @param currentTimestamps - Current repository timestamps from server (optional)
 * @param userId - User ID for cache validation
 * @returns True if cache is valid and current
 */
const isCacheValid = (
    hasCachedData: boolean,
    cachedData: RepositoryFileData[],
    currentRepoNames: string[] | undefined,
    currentTimestamps: Record<string, string> | undefined,
    userId: string | null
): boolean => {
    if (!hasCachedData || cachedData.length === 0) return false;
    if (isCacheExpired(userId)) return false;

    // If we have current repo data, check if repositories have changed
    if (currentRepoNames && currentTimestamps) {
        return areRepositoriesUnchanged(cachedData, currentRepoNames, currentTimestamps);
    }

    // If we only have repo names (no timestamps), use legacy validation
    if (currentRepoNames) {
        return areRepositoryListsEqual(cachedData, currentRepoNames);
    }

    // If no current data provided, assume valid (TTL-only check)
    return true;
};

/**
 * Interface for the GitHub repositories context type
 */
export interface GithubReposContextType {
    /** List of all available repositories with file search strings */
    repositories: RepositoryFileData[];
    /** Whether repositories data is being loaded */
    isLoading: boolean;
    /** Error that occurred during repository operations, if any */
    error: Error | null;
    /** Function to get repository data by name from cached results */
    getRepositoryByName: (repositoryFullName: string) => RepositoryFileData | null;
    /** Function to manually refresh repository data */
    refresh: () => void;
    /** Total number of repositories available */
    totalRepositories: number;
    /** TanStack Query result for all repositories (for advanced usage) */
    allRepositoriesQuery: UseQueryResult<AllFileSearchStringsResponse, Error>;
    /** Whether current cache is valid and up-to-date */
    isCacheValid: boolean;
    /** Timestamp when cache was last updated (null if no cache) */
    cacheTimestamp: number | null;
    /** Timestamp when repository list was last checked */
    lastRepoCheck: number | null;
    /** Force refresh bypassing cache */
    forceRefresh: () => void;
    /** Invalidate cache and trigger fresh fetch */
    invalidateCache: () => void;
}

/**
 * Default context value with warning functions
 */
const defaultContextValue: GithubReposContextType = {
    repositories: [],
    isLoading: false,
    error: null,
    getRepositoryByName: () => {
        console.warn('GithubReposProvider not found');
        return null;
    },
    refresh: () => { console.warn('GithubReposProvider not found'); },
    totalRepositories: 0,
    allRepositoriesQuery: {} as UseQueryResult<AllFileSearchStringsResponse, Error>,
    isCacheValid: false,
    cacheTimestamp: null,
    lastRepoCheck: null,
    forceRefresh: () => { console.warn('GithubReposProvider not found'); },
    invalidateCache: () => { console.warn('GithubReposProvider not found'); },
};

/**
 * Create the GitHub repositories context
 */
const GithubReposContext = createContext<GithubReposContextType | undefined>(
    undefined
);

/**
 * Props for the GithubReposProvider component
 */
export interface GithubReposProviderProps {
    /** Child components to be wrapped by the provider */
    children: ReactNode;
}

/**
 * Provider component that manages and distributes GitHub repositories state using TanStack Query.
 * @param {GithubReposProviderProps} props - Component props.
 * @returns {React.ReactElement} The provider component.
 */
export const GithubReposProvider: React.FC<GithubReposProviderProps> = ({ children }) => {
    const queryClient = useQueryClient();

    // State for cached data management
    const [cachedData, setCachedData] = useState<RepositoryFileData[]>([]);
    const [hasCachedData, setHasCachedData] = useState(false);

    // Load cache immediately on mount for instant data display
    useEffect(() => {
        const userId = getCurrentUserId();
        if (userId) {
            try {
                const cached = SafeStorage.safeGetUserScoped(
                    CACHE_CONFIG.baseKey,
                    userId,
                    repositoriesValidator,
                    []
                );
                if (cached.length > 0) {
                    setCachedData(cached);
                    setHasCachedData(true);
                }
            } catch (error) {
                // Handle cache retrieval errors gracefully - continue without cache
                console.warn('Failed to retrieve cache:', error);
            }
        }
    }, []);

    // Lightweight repository names query for cache validation
    const repositoryNamesQuery = useQuery({
        queryKey: QUERY_KEYS.repositoryNames,
        queryFn: getRepositoryNames,
        refetchInterval: 30 * 1000, // Poll every 30 seconds for cache invalidation detection
        staleTime: 0, // Always fetch fresh names for comparison
        retry: 2,
        throwOnError: false,
    });

    // Query for all repositories with file search strings - only fetch when cache is invalid
    const allRepositoriesQuery = useQuery({
        queryKey: QUERY_KEYS.allRepositories,
        queryFn: getAllFileSearchStrings,
        enabled: !isCacheValid(
            hasCachedData,
            cachedData,
            repositoryNamesQuery.data?.repository_names,
            repositoryNamesQuery.data?.repository_timestamps,
            getCurrentUserId()
        ), // Only fetch when cache is invalid/missing/stale
        staleTime: 10 * 60 * 1000, // 10 minutes - repositories don't change frequently
        retry: 2,
        throwOnError: false, // Ensure errors are captured in error state
    });

    // Update cache when fresh data arrives from API
    useEffect(() => {
        if (allRepositoriesQuery.data?.repositories) {
            const userId = getCurrentUserId();
            if (userId) {
                try {
                    SafeStorage.safeSetUserScoped(
                        CACHE_CONFIG.baseKey,
                        userId,
                        allRepositoriesQuery.data.repositories,
                        CACHE_CONFIG.ttlMs
                    );
                } catch (error) {
                    console.warn('Failed to set cache:', error);
                }
                // Update cached data state for consistency
                setCachedData(allRepositoriesQuery.data.repositories);
                setHasCachedData(true);
            }
        }
    }, [allRepositoriesQuery.data]);

    // Monitor repository changes and invalidate cache when needed
    useEffect(() => {
        if (repositoryNamesQuery.data?.repository_names && hasCachedData) {
            const currentRepoNames = repositoryNamesQuery.data.repository_names;
            const currentTimestamps = repositoryNamesQuery.data.repository_timestamps;

            // Use validation logic with fallback for legacy compatibility
            let repositoriesChanged = false;
            if (currentTimestamps) {
                // Enhanced validation with timestamps
                repositoriesChanged = !areRepositoriesUnchanged(cachedData, currentRepoNames, currentTimestamps);
            } else {
                // Legacy validation (names only)
                repositoriesChanged = !areRepositoryListsEqual(cachedData, currentRepoNames);
            }

            if (repositoriesChanged) {
                console.info('Repositories changed (names or timestamps), invalidating cache');
                // Clear cache and force refresh
                const userId = getCurrentUserId();
                if (userId) {
                    try {
                        SafeStorage.safeSetUserScoped(CACHE_CONFIG.baseKey, userId, [], 0); // Clear cache
                    } catch (error) {
                        console.warn('Failed to clear cache:', error);
                    }
                    // Force refetch of full data using query invalidation only
                    // Let TanStack Query handle the state updates to avoid duplicate requests
                    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.allRepositories });
                }
            }
        }
    }, [repositoryNamesQuery.data, cachedData, hasCachedData, queryClient]);

    // Helper function to find repository by name from cached results
    const getRepositoryByName = useCallback((repositoryFullName: string): RepositoryFileData | null => {
        const repositories = allRepositoriesQuery.data?.repositories || [];
        return repositories.find(repo => repo.repository_full_name === repositoryFullName) || null;
    }, [allRepositoriesQuery.data?.repositories]);

    const refresh = useCallback(() => {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.allRepositories });
    }, [queryClient]);

    // Cache control functions
    const forceRefresh = useCallback(() => {
        const userId = getCurrentUserId();
        if (userId) {
            // Clear cache
            try {
                SafeStorage.safeSetUserScoped(CACHE_CONFIG.baseKey, userId, [], 0);
            } catch (error) {
                console.warn('Failed to clear cache:', error);
            }
            setCachedData([]);
            setHasCachedData(false);
            // Force refetch both queries
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.allRepositories });
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.repositoryNames });
        }
    }, [queryClient]);

    const invalidateCache = useCallback(() => {
        forceRefresh();
    }, [forceRefresh]);

    const getCacheTimestamp = useCallback((): number | null => {
        const userId = getCurrentUserId();
        if (!userId) return null;

        try {
            const cacheKey = `${CACHE_CONFIG.baseKey}-${userId}`;
            const storedValue = localStorage.getItem(cacheKey);
            if (!storedValue) return null;

            const cachedData = JSON.parse(storedValue);
            return cachedData.timestamp || null;
        } catch {
            return null;
        }
    }, []);

    // Compute derived state with cache-first approach
    // Prioritize fresh data when available, fall back to cached data
    const repositories = allRepositoriesQuery.data?.repositories || cachedData;
    const totalRepositories = allRepositoriesQuery.data?.total_repositories || cachedData.length;
    // Only show loading state if we don't have cached data to display
    const isLoading = allRepositoriesQuery.isLoading && !hasCachedData;
    const error = allRepositoriesQuery.error;

    // Memoize the context value to prevent unnecessary re-renders
    const contextValue = useMemo(() => ({
        repositories,
        isLoading,
        error,
        getRepositoryByName,
        refresh,
        totalRepositories,
        allRepositoriesQuery,
        // New cache control properties
        isCacheValid: isCacheValid(
            hasCachedData,
            cachedData,
            repositoryNamesQuery.data?.repository_names,
            repositoryNamesQuery.data?.repository_timestamps,
            getCurrentUserId()
        ),
        cacheTimestamp: getCacheTimestamp(),
        lastRepoCheck: repositoryNamesQuery.dataUpdatedAt || null,
        forceRefresh,
        invalidateCache,
    }), [
        repositories,
        isLoading,
        error,
        getRepositoryByName,
        refresh,
        totalRepositories,
        allRepositoriesQuery,
        hasCachedData,
        cachedData,
        repositoryNamesQuery.data?.repository_names,
        getCacheTimestamp,
        repositoryNamesQuery.dataUpdatedAt,
        forceRefresh,
        invalidateCache,
    ]);

    return (
        <GithubReposContext.Provider value={contextValue}>
            {children}
        </GithubReposContext.Provider>
    );
};

/**
 * Custom hook for managing GitHub repositories data and operations
 * @returns {GithubReposHookResult} Object containing repositories data and operations
 */
export const useGithubRepos = (): GithubReposHookResult => {
    const context = useContext(GithubReposContext);

    if (context === undefined) {
        throw new Error('useGithubRepos must be used within a GithubReposProvider');
    }

    // Return only the public interface, hiding TanStack Query internals
    return {
        repositories: context.repositories,
        isLoading: context.isLoading,
        error: context.error,
        getRepositoryByName: context.getRepositoryByName,
        refresh: context.refresh,
        totalRepositories: context.totalRepositories,
        isCacheValid: context.isCacheValid,
        cacheTimestamp: context.cacheTimestamp,
        lastRepoCheck: context.lastRepoCheck,
        forceRefresh: context.forceRefresh,
        invalidateCache: context.invalidateCache,
    };
};

/**
 * Hook for getting a specific repository's data from cached results
 * @param repositoryFullName - The full name of the repository (e.g., "owner/repo")
 * @returns Repository data if found, null otherwise
 */
export const useRepositoryData = (repositoryFullName: string | null): RepositoryFileData | null => {
    const { getRepositoryByName } = useGithubRepos();

    return useMemo(() => {
        if (!repositoryFullName) return null;
        return getRepositoryByName(repositoryFullName);
    }, [repositoryFullName, getRepositoryByName]);
};