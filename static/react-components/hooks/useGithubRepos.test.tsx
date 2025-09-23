import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useGithubRepos, GithubReposProvider, useRepositoryData } from './useGithubRepos';
import type {
    RepositoryFileData,
    AllFileSearchStringsResponse,
    RepositoryNamesResponse
} from '#api/githubRepos';

// Mock the GitHub repos API
vi.mock('#api/githubRepos', () => ({
    getAllFileSearchStrings: vi.fn(),
    getRepositoryNames: vi.fn(),
    GitHubApiError: class GitHubApiError extends Error {
        public status: number;
        constructor(message: string, status: number) {
            super(message);
            this.name = 'GitHubApiError';
            this.status = status;
        }
    },
}));

// Mock JWT API for user ID retrieval
vi.mock('#api/jwt', () => ({
    getCurrentUserId: vi.fn(),
}));

// Mock SafeStorage from useUserPreferences
vi.mock('./useUserPreferences', () => ({
    SafeStorage: {
        safeGetUserScoped: vi.fn(),
        safeSetUserScoped: vi.fn(),
    },
}));

import * as mockGithubReposApi from '#api/githubRepos';
import * as mockJwtApi from '#api/jwt';
import { SafeStorage } from './useUserPreferences';

/**
 * Helper function to create a test wrapper with QueryClient and GithubReposProvider
 */
const createTestWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
                gcTime: 0,
                staleTime: 0,
            },
            mutations: {
                retry: false,
            },
        },
    });

    const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
        <QueryClientProvider client={queryClient}>
            <GithubReposProvider>
                {children}
            </GithubReposProvider>
        </QueryClientProvider>
    );

    return { TestWrapper, queryClient };
};

describe('useGithubRepos', () => {
    const mockRepository1: RepositoryFileData = {
        repository_full_name: 'owner/repo1',
        file_search_string: 'src/**/*.{ts,tsx,js,jsx}',
        updated_at: '2024-01-15T10:30:00Z',
    };

    const mockRepository2: RepositoryFileData = {
        repository_full_name: 'owner/repo2',
        file_search_string: 'app/**/*.{py,pyx}',
        updated_at: '2024-01-16T14:22:00Z',
    };

    const mockRepositories = [mockRepository1, mockRepository2];

    const mockAllRepositoriesResponse: AllFileSearchStringsResponse = {
        repositories: mockRepositories,
        total_repositories: 2,
        success: true,
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.resetAllMocks();
    });

    describe('Context Provider', () => {
        it('should throw error when used outside of GithubReposProvider', () => {
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => { });

            expect(() => {
                renderHook(() => useGithubRepos());
            }).toThrow('useGithubRepos must be used within a GithubReposProvider');

            consoleError.mockRestore();
        });

        it('should work with GithubReposProvider', async () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            expect(result.current.repositories).toEqual(mockRepositories);
            expect(result.current.totalRepositories).toBe(2);
        });
    });

    describe('Initial Loading', () => {
        it('should initialize with loading state', () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() => new Promise(() => { }));

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            expect(result.current.isLoading).toBe(true);
            expect(result.current.repositories).toEqual([]);
            expect(result.current.totalRepositories).toBe(0);
            expect(result.current.error).toBe(null);
        });

        it('should load repositories successfully', async () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            expect(result.current.repositories).toEqual(mockRepositories);
            expect(result.current.totalRepositories).toBe(2);
            expect(result.current.error).toBe(null);
        });

        it('should handle empty repositories list', async () => {
            const emptyResponse: AllFileSearchStringsResponse = {
                repositories: [],
                total_repositories: 0,
                success: true,
            };

            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(emptyResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            expect(result.current.repositories).toEqual([]);
            expect(result.current.totalRepositories).toBe(0);
            expect(result.current.error).toBe(null);
        });
    });

    describe('Error Handling', () => {
        it('should handle errors gracefully and provide default values', async () => {
            const error = new Error('Failed to fetch repositories');
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockRejectedValue(error);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Just verify the hook doesn't crash and provides safe defaults
            expect(result.current).toBeDefined();
            expect(result.current.repositories).toEqual([]);
            expect(result.current.totalRepositories).toBe(0);
        });
    });

    describe('getRepositoryByName', () => {
        it('should return repository data when repository exists', async () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            const repositoryData = result.current.getRepositoryByName('owner/repo1');
            expect(repositoryData).toEqual(mockRepository1);
        });

        it('should return null when repository does not exist', async () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            const repositoryData = result.current.getRepositoryByName('nonexistent/repo');
            expect(repositoryData).toBeNull();
        });

        it('should return null when no repositories are loaded', () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() => new Promise(() => { }));

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            const repositoryData = result.current.getRepositoryByName('owner/repo1');
            expect(repositoryData).toBeNull();
        });
    });

    describe('refresh', () => {
        it('should refresh repository data', async () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            vi.clearAllMocks();

            act(() => {
                result.current.refresh();
            });

            // After refresh, the query should be triggered again
            await waitFor(() => {
                expect(mockGithubReposApi.getAllFileSearchStrings).toHaveBeenCalled();
            });
        });
    });

    describe('Loading States', () => {
        it('should show loading when fetching initial data', () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() => new Promise(() => { }));

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            expect(result.current).toBeDefined();
            expect(result.current.isLoading).toBe(true);
        });

        it('should not be loading after data is fetched', async () => {
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Initially loading
            expect(result.current.isLoading).toBe(true);

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            // After loading, should be false
            expect(result.current.isLoading).toBe(false);
        });
    });
});

describe('useRepositoryData', () => {
    const mockRepository1: RepositoryFileData = {
        repository_full_name: 'owner/repo1',
        file_search_string: 'src/**/*.{ts,tsx,js,jsx}',
        updated_at: '2024-01-15T10:30:00Z',
    };

    const mockRepository2: RepositoryFileData = {
        repository_full_name: 'owner/repo2',
        file_search_string: 'app/**/*.{py,pyx}',
        updated_at: '2024-01-16T14:22:00Z',
    };

    const mockRepositories = [mockRepository1, mockRepository2];

    const mockAllRepositoriesResponse: AllFileSearchStringsResponse = {
        repositories: mockRepositories,
        total_repositories: 2,
        success: true,
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.resetAllMocks();
    });

    it('should return repository data when repository name is provided and exists', async () => {
        vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

        const { TestWrapper } = createTestWrapper();
        const { result } = renderHook(
            () => useRepositoryData('owner/repo1'),
            { wrapper: TestWrapper }
        );

        await waitFor(() => {
            expect(result.current).toEqual(mockRepository1);
        });
    });

    it('should return null when repository name is null', async () => {
        vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

        const { TestWrapper } = createTestWrapper();
        const { result } = renderHook(
            () => useRepositoryData(null),
            { wrapper: TestWrapper }
        );

        expect(result.current).toBeNull();
    });

    it('should return null when repository does not exist', async () => {
        vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

        const { TestWrapper } = createTestWrapper();
        const { result } = renderHook(
            () => useRepositoryData('nonexistent/repo'),
            { wrapper: TestWrapper }
        );

        await waitFor(() => {
            expect(result.current).toBeNull();
        });
    });

    it('should return null when repositories are still loading', () => {
        vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() => new Promise(() => { }));

        const { TestWrapper } = createTestWrapper();
        const { result } = renderHook(
            () => useRepositoryData('owner/repo1'),
            { wrapper: TestWrapper }
        );

        expect(result.current).toBeNull();
    });
});

describe('LocalStorage Caching', () => {
    const mockUserId = 'test-user-123';
    const mockRepository1: RepositoryFileData = {
        repository_full_name: 'owner/repo1',
        file_search_string: 'src/main.py\nsrc/utils.py\nREADME.md',
        updated_at: '2024-01-15T10:30:00Z',
    };

    const mockRepository2: RepositoryFileData = {
        repository_full_name: 'owner/repo2',
        file_search_string: 'app/server.js\napp/client.js\npackage.json',
        updated_at: '2024-01-16T14:22:00Z',
    };

    const mockRepositories = [mockRepository1, mockRepository2];

    const mockAllRepositoriesResponse: AllFileSearchStringsResponse = {
        repositories: mockRepositories,
        total_repositories: 2,
        success: true,
    };

    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(mockJwtApi.getCurrentUserId).mockReturnValue(mockUserId);
        vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([]);
        vi.mocked(SafeStorage.safeSetUserScoped).mockImplementation(() => {});
    });

    afterEach(() => {
        vi.resetAllMocks();
    });

    describe('Cache Loading on Initialization', () => {
        it('should load cached data immediately when available', async () => {
            // Mock cached data available
            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(mockRepositories);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() =>
                new Promise(() => {}) // Never resolves to test cache-first behavior
            );

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Should immediately show cached data
            expect(result.current.repositories).toEqual(mockRepositories);
            expect(result.current.totalRepositories).toBe(2);
            expect(result.current.isLoading).toBe(false); // Not loading because we have cached data
            expect(result.current.error).toBe(null);

            // Verify cache was accessed correctly
            expect(SafeStorage.safeGetUserScoped).toHaveBeenCalledWith(
                'github-repos',
                mockUserId,
                expect.any(Function), // repositoriesValidator
                []
            );
        });

        it('should show loading state when no cached data is available', () => {
            // Mock no cached data
            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([]);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() =>
                new Promise(() => {}) // Never resolves
            );

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Should show loading state when no cache
            expect(result.current.repositories).toEqual([]);
            expect(result.current.totalRepositories).toBe(0);
            expect(result.current.isLoading).toBe(true);
            expect(result.current.error).toBe(null);
        });

        it('should handle cache retrieval when user ID is null', () => {
            vi.mocked(mockJwtApi.getCurrentUserId).mockReturnValue(null);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() =>
                new Promise(() => {})
            );

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Should not attempt to load cache when no user ID
            expect(SafeStorage.safeGetUserScoped).not.toHaveBeenCalled();
            expect(result.current.isLoading).toBe(true);
        });
    });

    describe('Cache Storage on Fresh Data', () => {
        it('should store fresh data to cache when API responds', async () => {
            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([]);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            // Verify fresh data is displayed
            expect(result.current.repositories).toEqual(mockRepositories);

            // Verify cache was updated with fresh data
            expect(SafeStorage.safeSetUserScoped).toHaveBeenCalledWith(
                'github-repos',
                mockUserId,
                mockRepositories,
                60 * 60 * 1000 // 1 hour TTL
            );
        });

        it('should not store to cache when user ID is null', async () => {
            vi.mocked(mockJwtApi.getCurrentUserId).mockReturnValue(null);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(mockGithubReposApi.getAllFileSearchStrings).toHaveBeenCalled();
            });

            // Should not attempt to store cache when no user ID
            expect(SafeStorage.safeSetUserScoped).not.toHaveBeenCalled();
        });
    });

    describe('Fresh Data Prioritization', () => {
        it('should prioritize fresh data over cached data when both available', async () => {
            const cachedData = [mockRepository1]; // Only one repository in cache
            const freshData = mockRepositories; // Two repositories from API

            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Initially should show cached data
            expect(result.current.repositories).toEqual(cachedData);
            expect(result.current.isLoading).toBe(false);

            await waitFor(() => {
                expect(result.current.repositories).toEqual(freshData);
            });

            // After fresh data arrives, should show fresh data
            expect(result.current.repositories).toEqual(freshData);
            expect(result.current.totalRepositories).toBe(2);
            expect(result.current.isLoading).toBe(false);
        });

        it('should update total repositories count correctly with cache vs fresh data', async () => {
            const cachedData = [mockRepository1]; // 1 repository
            const freshResponse = { ...mockAllRepositoriesResponse, total_repositories: 5 }; // API says 5 total

            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(freshResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Initially should use cached data length
            expect(result.current.totalRepositories).toBe(1);

            await waitFor(() => {
                expect(result.current.totalRepositories).toBe(5);
            });

            // After fresh data, should use API total count
            expect(result.current.totalRepositories).toBe(5);
        });
    });

    describe('User Isolation', () => {
        it('should use different cache keys for different users', async () => {
            const user1Id = 'user-1';
            const user2Id = 'user-2';

            // Test with first user
            vi.mocked(mockJwtApi.getCurrentUserId).mockReturnValue(user1Id);
            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([mockRepository1]);

            const { TestWrapper: TestWrapper1 } = createTestWrapper();
            const { result: result1 } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper1 });

            expect(SafeStorage.safeGetUserScoped).toHaveBeenCalledWith(
                'github-repos',
                user1Id,
                expect.any(Function),
                []
            );

            // Test with second user
            vi.mocked(mockJwtApi.getCurrentUserId).mockReturnValue(user2Id);
            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([mockRepository2]);

            const { TestWrapper: TestWrapper2 } = createTestWrapper();
            const { result: result2 } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper2 });

            expect(SafeStorage.safeGetUserScoped).toHaveBeenCalledWith(
                'github-repos',
                user2Id,
                expect.any(Function),
                []
            );

            // Users should have different cached data
            expect(result1.current.repositories).toEqual([mockRepository1]);
            expect(result2.current.repositories).toEqual([mockRepository2]);
        });
    });

    describe('Cache Validation', () => {
        it('should validate cached data with repositoriesValidator', () => {
            const invalidCachedData = [
                { repository_full_name: 'test', invalid_field: 'bad' } // Missing required fields
            ];

            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(invalidCachedData);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() =>
                new Promise(() => {})
            );

            const { TestWrapper } = createTestWrapper();
            renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Should call validator function
            expect(SafeStorage.safeGetUserScoped).toHaveBeenCalledWith(
                'github-repos',
                mockUserId,
                expect.any(Function),
                []
            );

            // Validator function should be passed
            const validatorCall = vi.mocked(SafeStorage.safeGetUserScoped).mock.calls[0];
            const validator = validatorCall[2];

            // Test validator with valid data
            expect(validator(mockRepositories)).toBe(true);

            // Test validator with invalid data
            expect(validator(invalidCachedData)).toBe(false);
            expect(validator(null)).toBe(false);
            expect(validator({})).toBe(false);
            expect(validator('string')).toBe(false);
        });
    });

    describe('Error Scenarios', () => {
        it('should handle cache storage errors gracefully', async () => {
            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([]);
            vi.mocked(SafeStorage.safeSetUserScoped).mockImplementation(() => {
                throw new Error('localStorage quota exceeded');
            });
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(result.current.isLoading).toBe(false);
            });

            // Should still work despite cache storage error
            expect(result.current.repositories).toEqual(mockRepositories);
            expect(result.current.error).toBe(null);

            // Should have attempted to store to cache
            expect(SafeStorage.safeSetUserScoped).toHaveBeenCalled();
        });

        it('should handle cache retrieval errors gracefully', () => {
            vi.mocked(SafeStorage.safeGetUserScoped).mockImplementation(() => {
                throw new Error('localStorage access denied');
            });
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockImplementation(() =>
                new Promise(() => {})
            );

            const { TestWrapper } = createTestWrapper();
            const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            // Should still work despite cache retrieval error
            expect(result.current.repositories).toEqual([]);
            expect(result.current.isLoading).toBe(true);
            expect(result.current.error).toBe(null);
        });
    });

    describe('TTL Configuration', () => {
        it('should use correct TTL when storing cache', async () => {
            vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([]);
            vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

            const { TestWrapper } = createTestWrapper();
            renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

            await waitFor(() => {
                expect(SafeStorage.safeSetUserScoped).toHaveBeenCalled();
            });

            // Verify correct TTL (1 hour = 3,600,000 milliseconds)
            expect(SafeStorage.safeSetUserScoped).toHaveBeenCalledWith(
                'github-repos',
                mockUserId,
                mockRepositories,
                60 * 60 * 1000
            );
        });
    });

    describe('Enhanced Caching with Repository Names Polling', () => {
        const mockRepositoryNamesResponse: RepositoryNamesResponse = {
            repository_names: ['owner/repo1', 'owner/repo2'],
            repository_timestamps: {
                'owner/repo1': '2024-01-15T10:30:00Z',
                'owner/repo2': '2024-01-16T14:22:00Z',
            },
            total_repositories: 2,
            success: true,
        };

        beforeEach(() => {
            vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue(mockRepositoryNamesResponse);
        });

        describe('Conditional Fetching', () => {
            it('should not fetch full data when cache is valid and repo list matches', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);

                // Mock localStorage for cache timestamp validation
                const mockCacheData = {
                    value: cachedData,
                    timestamp: Date.now() - 30 * 60 * 1000, // 30 minutes ago (within 1 hour TTL)
                    ttl: 60 * 60 * 1000,
                };
                vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(JSON.stringify(mockCacheData));

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                // Wait for the system to stabilize and cache validation to complete
                await waitFor(() => {
                    expect(result.current.repositories).toEqual(cachedData);
                    expect(result.current.isCacheValid).toBe(true);
                });

                // Since cache is valid and repo lists match, the query should be disabled
                // We allow for an initial call but no subsequent calls
                const initialCalls = vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mock.calls.length;

                // Wait a bit more to ensure no additional calls are made
                await new Promise(resolve => setTimeout(resolve, 100));

                const finalCalls = vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mock.calls.length;

                // Should not make additional calls beyond the initial
                expect(finalCalls).toBeLessThanOrEqual(1);
                expect(result.current.isCacheValid).toBe(true);
            });

            it('should fetch full data when cache is expired', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);
                vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

                // Mock expired cache
                const mockCacheData = {
                    value: cachedData,
                    timestamp: Date.now() - 2 * 60 * 60 * 1000, // 2 hours ago (expired)
                    ttl: 60 * 60 * 1000,
                };
                vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(JSON.stringify(mockCacheData));

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(mockGithubReposApi.getAllFileSearchStrings).toHaveBeenCalled();
                });

                // Cache should be invalid due to expiry
                expect(result.current.isCacheValid).toBe(false);
                expect(result.current.repositories).toEqual(mockRepositories);
            });

            it('should fetch full data when repository list has changed', async () => {
                const cachedData = [mockRepository1]; // Only repo1 in cache
                const changedRepoNames = ['user/repo1', 'user/repo2', 'user/repo3']; // Added repo3

                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);
                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue({
                    repository_names: changedRepoNames,
                    repository_timestamps: {
                        'user/repo1': '2024-01-15T10:30:00Z',
                        'user/repo2': '2024-01-16T14:22:00Z',
                        'user/repo3': '2024-01-17T09:15:00Z',
                    },
                    total_repositories: 3,
                    success: true,
                });
                vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

                // Mock valid cache timestamp but different repo list
                const mockCacheData = {
                    value: cachedData,
                    timestamp: Date.now() - 10 * 60 * 1000, // 10 minutes ago (valid)
                    ttl: 60 * 60 * 1000,
                };
                vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(JSON.stringify(mockCacheData));

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(mockGithubReposApi.getAllFileSearchStrings).toHaveBeenCalled();
                });

                // Cache should be invalid due to repo list change
                expect(result.current.isCacheValid).toBe(false);
            });
        });

        describe('Cache Invalidation Detection', () => {
            it('should not make duplicate requests when using forceRefresh', async () => {
                const initialCachedData = [mockRepository1];
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(initialCachedData);
                vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

                // Start with matching repo names
                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue({
                    repository_names: ['owner/repo1'],
                    repository_timestamps: {
                        'owner/repo1': '2024-01-15T10:30:00Z',
                    },
                    total_repositories: 1,
                    success: true,
                });

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                // Wait for initial load
                await waitFor(() => {
                    expect(result.current.repositories).toEqual(initialCachedData);
                });

                // Clear mock history to track only invalidation-triggered calls
                vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockClear();

                // Force refresh to trigger cache invalidation
                await act(async () => {
                    result.current.forceRefresh();
                });

                // Wait for the API call to complete
                await waitFor(() => {
                    expect(mockGithubReposApi.getAllFileSearchStrings).toHaveBeenCalled();
                });

                // Allow extra time for potential duplicate calls
                await new Promise(resolve => setTimeout(resolve, 200));

                // Critical assertion: Should make exactly 1 call, not 2
                expect(mockGithubReposApi.getAllFileSearchStrings).toHaveBeenCalledTimes(1);
            });

            it('should invalidate cache when repository list changes', async () => {
                const initialCachedData = [mockRepository1];
                const newRepoNames = ['user/repo1', 'user/repo2']; // Added a new repo

                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(initialCachedData);
                vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

                // Start with initial repo list
                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue({
                    repository_names: ['user/repo1'],
                    repository_timestamps: {
                        'user/repo1': '2024-01-15T10:30:00Z',
                    },
                    total_repositories: 1,
                    success: true,
                });

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.repositories).toEqual(initialCachedData);
                });

                // Simulate repository list change
                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue({
                    repository_names: newRepoNames,
                    repository_timestamps: {
                        'user/repo1': '2024-01-15T10:30:00Z',
                        'user/repo2': '2024-01-16T14:22:00Z',
                    },
                    total_repositories: 2,
                    success: true,
                });

                // Wait for the polling interval to detect the change
                await waitFor(() => {
                    expect(SafeStorage.safeSetUserScoped).toHaveBeenCalledWith(
                        'github-repos',
                        mockUserId,
                        [],
                        0
                    );
                }, { timeout: 35000 }); // Account for 30-second polling interval

                // Should invalidate cache and fetch fresh data
                await waitFor(() => {
                    expect(mockGithubReposApi.getAllFileSearchStrings).toHaveBeenCalled();
                });
            });

            it('should not invalidate cache when repository list is unchanged', async () => {
                const cachedData = mockRepositories;
                const unchangedRepoNames = ['owner/repo1', 'owner/repo2'];

                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);
                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue({
                    repository_names: unchangedRepoNames,
                    repository_timestamps: {
                        'owner/repo1': '2024-01-15T10:30:00Z',
                        'owner/repo2': '2024-01-16T14:22:00Z',
                    },
                    total_repositories: 2,
                    success: true,
                });

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.repositories).toEqual(cachedData);
                });

                // Should not clear cache when repo list is the same
                expect(SafeStorage.safeSetUserScoped).not.toHaveBeenCalledWith(
                    'github-repos',
                    mockUserId,
                    [],
                    0
                );
            });
        });

        describe('Repository Names Polling', () => {
            it('should call repository names API immediately on mount', async () => {
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([]);
                vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);
                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue(mockRepositoryNamesResponse);

                const { TestWrapper } = createTestWrapper();
                renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                // Should call repository names API immediately
                await waitFor(() => {
                    expect(mockGithubReposApi.getRepositoryNames).toHaveBeenCalled();
                });

                // Verify it was called at least once
                expect(mockGithubReposApi.getRepositoryNames).toHaveBeenCalledTimes(1);
            });
        });

        describe('Enhanced Hook Interface', () => {
            it('should provide new cache control properties', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);
                vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.repositories).toEqual(cachedData);
                });

                // Should have new cache control properties
                expect(result.current).toHaveProperty('isCacheValid');
                expect(result.current).toHaveProperty('cacheTimestamp');
                expect(result.current).toHaveProperty('lastRepoCheck');
                expect(result.current).toHaveProperty('forceRefresh');
                expect(result.current).toHaveProperty('invalidateCache');

                // Should be functions
                expect(typeof result.current.forceRefresh).toBe('function');
                expect(typeof result.current.invalidateCache).toBe('function');
            });

            it('should force refresh when forceRefresh is called', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);
                vi.mocked(mockGithubReposApi.getAllFileSearchStrings).mockResolvedValue(mockAllRepositoriesResponse);

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.repositories).toEqual(cachedData);
                });

                // Call forceRefresh
                act(() => {
                    result.current.forceRefresh();
                });

                // Should clear cache and trigger fresh fetch
                expect(SafeStorage.safeSetUserScoped).toHaveBeenCalledWith(
                    'github-repos',
                    mockUserId,
                    [],
                    0
                );

                await waitFor(() => {
                    expect(mockGithubReposApi.getAllFileSearchStrings).toHaveBeenCalled();
                });
            });

            it('should invalidate cache when invalidateCache is called', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.repositories).toEqual(cachedData);
                });

                // Call invalidateCache
                act(() => {
                    result.current.invalidateCache();
                });

                // Should clear cache (same as forceRefresh)
                expect(SafeStorage.safeSetUserScoped).toHaveBeenCalledWith(
                    'github-repos',
                    mockUserId,
                    [],
                    0
                );
            });
        });

        describe('Cache Timestamp Tracking', () => {
            it('should track cache timestamp correctly', async () => {
                const now = Date.now();
                const mockCacheData = {
                    value: mockRepositories,
                    timestamp: now,
                    ttl: 60 * 60 * 1000,
                };

                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(mockRepositories);
                vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(JSON.stringify(mockCacheData));

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.cacheTimestamp).toBe(now);
                });
            });

            it('should return null cache timestamp when no cache exists', async () => {
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue([]);
                vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.cacheTimestamp).toBe(null);
                });
            });
        });

        describe('Timestamp-Based Cache Invalidation', () => {
            it('should invalidate cache when repository timestamps are newer', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);

                // Mock repository names response with newer timestamps
                const newerTimestampsResponse: RepositoryNamesResponse = {
                    repository_names: ['owner/repo1', 'owner/repo2'],
                    repository_timestamps: {
                        'owner/repo1': '2024-01-15T11:00:00Z', // 30 minutes newer
                        'owner/repo2': '2024-01-16T15:00:00Z', // 38 minutes newer
                    },
                    total_repositories: 2,
                    success: true,
                };

                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue(newerTimestampsResponse);

                const { TestWrapper } = createTestWrapper();
                renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                // Should detect timestamp changes and invalidate cache
                await waitFor(() => {
                    expect(SafeStorage.safeSetUserScoped).toHaveBeenCalledWith(
                        'github-repos',
                        mockUserId,
                        [],
                        0
                    );
                });
            });

            it('should not invalidate cache when timestamps are unchanged', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);

                // Mock repository names response with same timestamps as cached data
                const sameTimestampsResponse: RepositoryNamesResponse = {
                    repository_names: ['owner/repo1', 'owner/repo2'],
                    repository_timestamps: {
                        'owner/repo1': '2024-01-15T10:30:00Z', // Same as mockRepository1
                        'owner/repo2': '2024-01-16T14:22:00Z', // Same as mockRepository2
                    },
                    total_repositories: 2,
                    success: true,
                };

                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue(sameTimestampsResponse);

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.repositories).toEqual(cachedData);
                });

                // Should not clear cache when timestamps are the same
                expect(SafeStorage.safeSetUserScoped).not.toHaveBeenCalledWith(
                    'github-repos',
                    mockUserId,
                    [],
                    0
                );
            });

            it('should invalidate cache when one repository has newer timestamp', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);

                // Mock response with one repository having newer timestamp
                const partiallyUpdatedResponse: RepositoryNamesResponse = {
                    repository_names: ['owner/repo1', 'owner/repo2'],
                    repository_timestamps: {
                        'owner/repo1': '2024-01-15T10:30:00Z', // Same as cached
                        'owner/repo2': '2024-01-16T15:30:00Z', // Newer than cached
                    },
                    total_repositories: 2,
                    success: true,
                };

                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue(partiallyUpdatedResponse);

                const { TestWrapper } = createTestWrapper();
                renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                // Should detect the newer timestamp and invalidate cache
                await waitFor(() => {
                    expect(SafeStorage.safeSetUserScoped).toHaveBeenCalledWith(
                        'github-repos',
                        mockUserId,
                        [],
                        0
                    );
                });
            });

            it('should handle missing repository in timestamps (invalidate cache)', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);

                // Mock response missing one repository timestamp
                const missingRepoResponse: RepositoryNamesResponse = {
                    repository_names: ['owner/repo1', 'owner/repo2'],
                    repository_timestamps: {
                        'owner/repo1': '2024-01-15T10:30:00Z',
                        // Missing 'owner/repo2'
                    },
                    total_repositories: 2,
                    success: true,
                };

                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue(missingRepoResponse);

                const { TestWrapper } = createTestWrapper();
                renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                // Should invalidate cache when repository timestamp is missing
                await waitFor(() => {
                    expect(SafeStorage.safeSetUserScoped).toHaveBeenCalledWith(
                        'github-repos',
                        mockUserId,
                        [],
                        0
                    );
                });
            });

            it('should use legacy validation when timestamps are unavailable', async () => {
                const cachedData = mockRepositories;
                vi.mocked(SafeStorage.safeGetUserScoped).mockReturnValue(cachedData);

                // Mock response without timestamps (legacy API)
                const legacyResponse = {
                    repository_names: ['owner/repo1', 'owner/repo2'],
                    total_repositories: 2,
                    success: true,
                    // No repository_timestamps field
                };

                vi.mocked(mockGithubReposApi.getRepositoryNames).mockResolvedValue(legacyResponse as any);

                const { TestWrapper } = createTestWrapper();
                const { result } = renderHook(() => useGithubRepos(), { wrapper: TestWrapper });

                await waitFor(() => {
                    expect(result.current.repositories).toEqual(cachedData);
                });

                // Should fall back to name-only validation (not invalidate for same names)
                expect(SafeStorage.safeSetUserScoped).not.toHaveBeenCalledWith(
                    'github-repos',
                    mockUserId,
                    [],
                    0
                );
            });
        });
    });
});