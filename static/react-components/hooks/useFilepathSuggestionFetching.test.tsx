import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useFilepathSuggestionFetching } from './useFilepathSuggestionFetching';
import { useGithubRepos } from './useGithubRepos';
import type { RepositoryFileData } from '#api/githubRepos';

// Mock the useGithubRepos hook
vi.mock('./useGithubRepos');

const mockUseGithubRepos = vi.mocked(useGithubRepos);

describe('useFilepathSuggestionFetching', () => {
    const mockRepositories: RepositoryFileData[] = [
        {
            repository_full_name: 'user/repo1',
            file_search_string: 'src/components/Button.tsx\nsrc/components/ButtonGroup.tsx\nsrc/utils/auth.ts\nREADME.md',
            updated_at: '2023-01-01T00:00:00Z',
        },
        {
            repository_full_name: 'user/repo2',
            file_search_string: 'lib/components/Modal.tsx\nlib/utils/validation.ts\npackage.json',
            updated_at: '2023-01-01T00:00:00Z',
        },
        {
            repository_full_name: 'user/empty-repo',
            file_search_string: '',
            updated_at: '2023-01-01T00:00:00Z',
        },
    ];

    beforeEach(() => {
        vi.clearAllMocks();
    });

    // Helper function to create complete mock return value with all required properties
    const createMockGithubReposResult = (overrides = {}) => ({
        repositories: mockRepositories,
        isLoading: false,
        error: null,
        getRepositoryByName: vi.fn(),
        refresh: vi.fn(),
        totalRepositories: 3,
        isCacheValid: true,
        cacheTimestamp: Date.now(),
        lastRepoCheck: Date.now(),
        forceRefresh: vi.fn(),
        invalidateCache: vi.fn(),
        ...overrides,
    });

    it('returns empty suggestions for empty search query', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult());

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: '' })
        );

        expect(result.current.suggestions).toEqual([]);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).toBe(null);
    });

    it('returns empty suggestions for whitespace-only search query', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult());

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: '   ' })
        );

        expect(result.current.suggestions).toEqual([]);
    });

    it('filters file paths based on search query', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult());

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'components' })
        );

        expect(result.current.suggestions).toEqual([
            'lib/components/Modal.tsx',
            'src/components/Button.tsx',
            'src/components/ButtonGroup.tsx',
        ]);
    });

    it('returns suggestions with repository prefixes', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult());

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'Button' })
        );

        expect(result.current.suggestions).toEqual([
            'src/components/Button.tsx',
            'src/components/ButtonGroup.tsx',
        ]);
    });

    it('prioritizes exact prefix matches over partial matches', () => {
        const repoWithPrefixMatches: RepositoryFileData[] = [
            {
                repository_full_name: 'user/test-repo',
                file_search_string: 'auth/login.ts\nsrc/auth/middleware.ts\nutils/auth-helper.ts',
                updated_at: '2023-01-01T00:00:00Z',
            },
        ];

        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult({
            repositories: repoWithPrefixMatches,
            totalRepositories: 1,
        }));

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'auth' })
        );

        // Should prioritize files that start with 'auth' over those that contain 'auth'
        expect(result.current.suggestions[0]).toBe('auth/login.ts');
        expect(result.current.suggestions[1]).toBe('src/auth/middleware.ts');
        expect(result.current.suggestions[2]).toBe('utils/auth-helper.ts');
    });

    it('performs case-insensitive search', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult());

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'BUTTON' })
        );

        expect(result.current.suggestions).toEqual([
            'src/components/Button.tsx',
            'src/components/ButtonGroup.tsx',
        ]);
    });

    it('limits results to 10 suggestions', () => {
        const repoWithManyFiles: RepositoryFileData[] = [
            {
                repository_full_name: 'user/large-repo',
                file_search_string: Array.from({ length: 15 }, (_, i) => `file${i}.ts`).join('\n'),
                updated_at: '2023-01-01T00:00:00Z',
            },
        ];

        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult({
            repositories: repoWithManyFiles,
            totalRepositories: 1,
        }));

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'file' })
        );

        expect(result.current.suggestions).toHaveLength(10);
    });

    it('handles repositories with empty file search strings', () => {
        const emptyRepo: RepositoryFileData[] = [
            {
                repository_full_name: 'user/empty-repo',
                file_search_string: '',
                updated_at: '2023-01-01T00:00:00Z',
            },
        ];

        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult({
            repositories: emptyRepo,
            totalRepositories: 1,
        }));

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'any' })
        );

        expect(result.current.suggestions).toEqual([]);
    });

    it('handles repositories with only newlines in file search strings', () => {
        const newlineOnlyRepo: RepositoryFileData[] = [
            {
                repository_full_name: 'user/newline-repo',
                file_search_string: '\n\n\n',
                updated_at: '2023-01-01T00:00:00Z',
            },
        ];

        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult({
            repositories: newlineOnlyRepo,
            totalRepositories: 1,
        }));

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'any' })
        );

        expect(result.current.suggestions).toEqual([]);
    });

    it('passes through loading state from useGithubRepos', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult({
            repositories: [],
            isLoading: true,
            totalRepositories: 0,
        }));

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'test' })
        );

        expect(result.current.isLoading).toBe(true);
        expect(result.current.suggestions).toEqual([]);
    });

    it('passes through error state from useGithubRepos', () => {
        const testError = new Error('Failed to fetch repositories');
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult({
            repositories: [],
            error: testError,
            totalRepositories: 0,
        }));

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'test' })
        );

        expect(result.current.error).toBe(testError);
        expect(result.current.suggestions).toEqual([]);
    });

    it('returns no suggestions when no repositories are available', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult({
            repositories: [],
            totalRepositories: 0,
        }));

        const { result } = renderHook(() =>
            useFilepathSuggestionFetching({ searchQuery: 'test' })
        );

        expect(result.current.suggestions).toEqual([]);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).toBe(null);
    });

    it('memoizes suggestions when searchQuery and repositories remain the same', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult());

        const { result, rerender } = renderHook(
            (props) => useFilepathSuggestionFetching(props),
            { initialProps: { searchQuery: 'components' } }
        );

        const firstResult = result.current.suggestions;

        // Rerender with same props
        rerender({ searchQuery: 'components' });

        // Should return the same reference due to memoization
        expect(result.current.suggestions).toBe(firstResult);
    });

    it('updates suggestions when searchQuery changes', () => {
        mockUseGithubRepos.mockReturnValue(createMockGithubReposResult());

        const { result, rerender } = renderHook(
            (props) => useFilepathSuggestionFetching(props),
            { initialProps: { searchQuery: 'components' } }
        );

        const firstResult = result.current.suggestions;
        expect(firstResult).toHaveLength(3);

        // Change search query
        rerender({ searchQuery: 'Button' });

        expect(result.current.suggestions).not.toBe(firstResult);
        expect(result.current.suggestions).toHaveLength(2);
        expect(result.current.suggestions).toEqual([
            'src/components/Button.tsx',
            'src/components/ButtonGroup.tsx',
        ]);
    });
});