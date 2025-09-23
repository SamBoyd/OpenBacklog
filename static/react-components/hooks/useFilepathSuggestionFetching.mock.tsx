import type { UseFilepathSuggestionFetchingResult } from './useFilepathSuggestionFetching';

/**
 * Mock implementation of useFilepathSuggestionFetching hook for Storybook stories
 *
 * This mock provides realistic file path suggestions that can be used in Storybook
 * to demonstrate components that use the file path suggestion functionality.
 */

// Sample file paths that represent a typical repository structure
const MOCK_FILE_SUGGESTIONS = [
    '@user/frontend-app/src/components/Button.tsx',
    '@user/frontend-app/src/components/ButtonGroup.tsx',
    '@user/frontend-app/src/components/Modal.tsx',
    '@user/frontend-app/src/hooks/useAuth.tsx',
    '@user/frontend-app/src/hooks/useLocalStorage.tsx',
    '@user/frontend-app/src/pages/Dashboard.tsx',
    '@user/frontend-app/src/pages/Login.tsx',
    '@user/frontend-app/src/utils/api.ts',
    '@user/frontend-app/src/utils/validation.ts',
    '@user/backend-api/src/controllers/auth.ts',
    '@user/backend-api/src/controllers/users.ts',
    '@user/backend-api/src/models/User.ts',
    '@user/backend-api/src/routes/api.ts',
    '@user/backend-api/tests/auth.test.ts',
    '@user/shared-lib/src/types/common.ts',
    '@user/shared-lib/src/utils/helpers.ts',
];

/**
 * Filters mock suggestions based on search query to simulate real behavior
 */
function filterMockSuggestions(searchQuery: string): string[] {
    if (!searchQuery.trim()) {
        return [];
    }

    const lowercaseQuery = searchQuery.toLowerCase();

    return MOCK_FILE_SUGGESTIONS
        .filter(path => path.toLowerCase().includes(lowercaseQuery))
        .slice(0, 10)
        .sort((a, b) => {
            // Prioritize exact matches, then prefix matches
            const aStarts = a.toLowerCase().startsWith(`@${lowercaseQuery}`) ||
                           a.toLowerCase().includes(`/${lowercaseQuery}`);
            const bStarts = b.toLowerCase().startsWith(`@${lowercaseQuery}`) ||
                           b.toLowerCase().includes(`/${lowercaseQuery}`);
            if (aStarts && !bStarts) return -1;
            if (!aStarts && bStarts) return 1;
            return a.localeCompare(b);
        });
}

/**
 * Mock hook that returns predefined file path suggestions for Storybook
 */
export const useFilepathSuggestionFetching = ({
    searchQuery
}: {
    searchQuery: string
}): UseFilepathSuggestionFetchingResult => {
    return {
        suggestions: filterMockSuggestions(searchQuery),
        isLoading: false,
        error: null,
    };
};

/**
 * Mock hook that simulates loading state
 */
export const useFilepathSuggestionFetchingLoading = ({
    searchQuery
}: {
    searchQuery: string
}): UseFilepathSuggestionFetchingResult => {
    return {
        suggestions: [],
        isLoading: true,
        error: null,
    };
};

/**
 * Mock hook that simulates error state
 */
export const useFilepathSuggestionFetchingError = ({
    searchQuery
}: {
    searchQuery: string
}): UseFilepathSuggestionFetchingResult => {
    return {
        suggestions: [],
        isLoading: false,
        error: new Error('Failed to fetch repository data'),
    };
};

/**
 * Mock hook that simulates empty repository state
 */
export const useFilepathSuggestionFetchingEmpty = ({
    searchQuery
}: {
    searchQuery: string
}): UseFilepathSuggestionFetchingResult => {
    return {
        suggestions: [],
        isLoading: false,
        error: null,
    };
};

// Export the type for consistency
export type { UseFilepathSuggestionFetchingResult };