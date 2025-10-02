// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useGithubInstallation';

export const useGithubInstallation = fn(actual.useGithubInstallation).mockName('useGithubInstallation');

/**
 * Default mock return value for useGithubInstallation hook (not connected state)
 */
export const mockUseGithubInstallationReturn = {
    hasInstallation: false,
    repositoryCount: 0,
    isLoading: false,
    error: null,
    refresh: () => {},
};

/**
 * Mock return value for loading state
 */
export const mockUseGithubInstallationLoadingReturn = {
    hasInstallation: false,
    repositoryCount: 0,
    isLoading: true,
    error: null,
    refresh: () => {},
};

/**
 * Mock return value for connected state with repositories
 */
export const mockUseGithubInstallationConnectedReturn = {
    hasInstallation: true,
    repositoryCount: 3,
    isLoading: false,
    error: null,
    refresh: () => {},
};

/**
 * Mock return value for connected state with no repositories
 */
export const mockUseGithubInstallationConnectedNoReposReturn = {
    hasInstallation: true,
    repositoryCount: 0,
    isLoading: false,
    error: null,
    refresh: () => {},
};

/**
 * Mock return value for error state
 */
export const mockUseGithubInstallationErrorReturn = {
    hasInstallation: false,
    repositoryCount: 0,
    isLoading: false,
    error: new Error('Failed to fetch installation status'),
    refresh: () => {},
};
