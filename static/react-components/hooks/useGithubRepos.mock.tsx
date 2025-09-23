// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useGithubRepos';

export const useGithubRepos = fn(actual.useGithubRepos).mockName('useGithubRepos');
export const useRepositoryData = fn(actual.useRepositoryData).mockName('useRepositoryData');

const mockRepositoriesData = [
    {
        repository_full_name: 'user/frontend-app',
        file_search_string: [
            'src/components/Button.tsx',
            'src/components/ButtonGroup.tsx',
            'src/components/Modal.tsx',
            'src/components/Navigation.tsx',
            'src/hooks/useAuth.tsx',
            'src/hooks/useLocalStorage.tsx',
            'src/pages/Dashboard.tsx',
            'src/pages/Login.tsx',
            'src/utils/api.ts',
            'src/utils/validation.ts',
            'README.md',
            'package.json'
        ].join('\n'),
        updated_at: '2023-01-01T00:00:00Z',
    },
    {
        repository_full_name: 'user/backend-api',
        file_search_string: [
            'src/controllers/auth.ts',
            'src/controllers/users.ts',
            'src/models/User.ts',
            'src/models/Task.ts',
            'src/routes/api.ts',
            'src/middleware/auth.ts',
            'tests/auth.test.ts',
            'tests/users.test.ts',
            'config/database.ts',
            'README.md'
        ].join('\n'),
        updated_at: '2023-01-01T00:00:00Z',
    },
    {
        repository_full_name: 'user/shared-lib',
        file_search_string: [
            'src/types/common.ts',
            'src/types/api.ts',
            'src/utils/helpers.ts',
            'src/utils/constants.ts',
            'dist/index.js',
            'package.json'
        ].join('\n'),
        updated_at: '2023-01-01T00:00:00Z',
    },
];

export const mockUseGithubReposReturn = {
    repositories: mockRepositoriesData,
    isLoading: false,
    error: null,
    getRepositoryByName: (name: string) => mockRepositoriesData.find(repo => repo.repository_full_name === name) || null,
    refresh: () => {},
    totalRepositories: mockRepositoriesData.length,
    isCacheValid: true,
    cacheTimestamp: Date.now(),
    lastRepoCheck: Date.now(),
    forceRefresh: () => {},
    invalidateCache: () => {},
};