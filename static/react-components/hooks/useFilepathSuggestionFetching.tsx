import { useMemo } from 'react';
import { useGithubRepos } from '#hooks/useGithubRepos';

/**
 * Properties for the useFilepathSuggestionFetching hook
 */
interface UseFilepathSuggestionFetchingProps {
    /** The search query to filter file paths with */
    searchQuery: string;
}

/**
 * Return type for the useFilepathSuggestionFetching hook
 */
export interface UseFilepathSuggestionFetchingResult {
    /** Array of file path suggestions formatted as @repo/path/file.ext */
    suggestions: string[];
    /** Whether the underlying repository data is still loading */
    isLoading: boolean;
    /** Error from the repository data fetch, if any */
    error: Error | null;
}

/**
 * Filters file paths based on a search query with intelligent ranking
 * @param allPaths - Array of all file paths to search through
 * @param query - The search query to filter by
 * @returns Filtered and sorted array of file paths (limited to 10 results)
 */
function filterFilePaths(allPaths: string[], query: string): string[] {
    if (!query.trim()) {
        return [];
    }

    const lowercaseQuery = query.toLowerCase();

    return allPaths
        .filter(path => path.toLowerCase().includes(lowercaseQuery))
        .slice(0, 10) // Limit to 10 suggestions
        .sort((a, b) => {
            // Prioritize exact matches, then prefix matches
            const aStarts = a.toLowerCase().startsWith(lowercaseQuery);
            const bStarts = b.toLowerCase().startsWith(lowercaseQuery);
            if (aStarts && !bStarts) return -1;
            if (!aStarts && bStarts) return 1;
            return a.localeCompare(b);
        });
}

/**
 * Custom hook for fetching file path suggestions across all user repositories
 *
 * This hook searches through all connected GitHub repositories to provide
 * autocomplete suggestions for file paths. It formats results with repository
 * prefixes (@repo/path/file.ext) and provides intelligent ranking.
 *
 * @param {UseFilepathSuggestionFetchingProps} props - Hook configuration
 * @returns {UseFilepathSuggestionFetchingResult} Suggestions, loading state, and error
 *
 * @example
 * ```tsx
 * const { suggestions, isLoading, error } = useFilepathSuggestionFetching({
 *     searchQuery: 'components/But'
 * });
 * // Returns: ['@myrepo/src/components/Button.tsx', '@myrepo/src/components/ButtonGroup.tsx']
 * ```
 */
export const useFilepathSuggestionFetching = ({
    searchQuery
}: UseFilepathSuggestionFetchingProps): UseFilepathSuggestionFetchingResult => {
    const { repositories, isLoading, error } = useGithubRepos();

    // Combine all file paths from all repositories
    const allFilePaths = useMemo(() => {
        return repositories.flatMap(repo =>
            repo.file_search_string
                .split('\n')
                .filter(path => path.trim())
        );
    }, [repositories]);

    // Filter file paths based on search query
    const suggestions = useMemo(() => {
        return filterFilePaths(allFilePaths, searchQuery);
    }, [allFilePaths, searchQuery]);

    return {
        suggestions,
        isLoading,
        error,
    };
};