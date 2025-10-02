import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import GitHubInstallStep from '#components/onboarding/steps/GitHubInstallStep';
import { useGithubInstallation } from '#hooks/useGithubInstallation.mock';

const meta: Meta<typeof GitHubInstallStep> = {
  title: 'Components/Onboarding/GitHubInstallStep',
  component: GitHubInstallStep,
  parameters: {
    layout: 'centered',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#f8fafc' },
        { name: 'dark', value: '#0f172a' },
      ],
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Loading state - checking GitHub connection status
 */
export const Loading: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Shows loading spinner while checking if GitHub app is installed.',
      },
    },
  },
  beforeEach: () => {
    useGithubInstallation.mockImplementation(() => ({
      hasInstallation: false,
      repositoryCount: 0,
      isLoading: true,
      error: null,
      refresh: () => {},
    }));
  },
};

/**
 * Not connected state - shows benefits and connect button
 */
export const NotConnected: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Default state when GitHub app is not yet installed. Shows benefits and call-to-action.',
      },
    },
  },
  beforeEach: () => {
    useGithubInstallation.mockImplementation(() => ({
      hasInstallation: false,
      repositoryCount: 0,
      isLoading: false,
      error: null,
      refresh: () => {},
    }));
  },
};

/**
 * Connected with no repositories
 */
export const ConnectedNoRepos: Story = {
  parameters: {
    docs: {
      description: {
        story: 'GitHub app is installed but no repositories have been granted access yet.',
      },
    },
  },
  beforeEach: () => {
    useGithubInstallation.mockImplementation(() => ({
      hasInstallation: true,
      repositoryCount: 0,
      isLoading: false,
      error: null,
      refresh: () => {},
    }));
  },
};

/**
 * Connected with 1 repository
 */
export const ConnectedOneRepo: Story = {
  parameters: {
    docs: {
      description: {
        story: 'GitHub app is installed with access to 1 repository.',
      },
    },
  },
  beforeEach: () => {
    useGithubInstallation.mockImplementation(() => ({
      hasInstallation: true,
      repositoryCount: 1,
      isLoading: false,
      error: null,
      refresh: () => {},
    }));
  },
};

/**
 * Connected with 3 repositories
 */
export const ConnectedThreeRepos: Story = {
  parameters: {
    docs: {
      description: {
        story: 'GitHub app is installed with access to 3 repositories.',
      },
    },
  },
  beforeEach: () => {
    useGithubInstallation.mockImplementation(() => ({
      hasInstallation: true,
      repositoryCount: 3,
      isLoading: false,
      error: null,
      refresh: () => {},
    }));
  },
};

/**
 * Connected with 10 repositories
 */
export const ConnectedTenRepos: Story = {
  parameters: {
    docs: {
      description: {
        story: 'GitHub app is installed with access to 10 repositories.',
      },
    },
  },
  beforeEach: () => {
    useGithubInstallation.mockImplementation(() => ({
      hasInstallation: true,
      repositoryCount: 10,
      isLoading: false,
      error: null,
      refresh: () => {},
    }));
  },
};

/**
 * Error state - failed to fetch installation status
 */
export const Error: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Shows error state when API call fails to fetch installation status.',
      },
    },
  },
  beforeEach: () => {
    useGithubInstallation.mockImplementation(() => ({
      hasInstallation: false,
      repositoryCount: 0,
      isLoading: false,
      error: new Error('Failed to fetch installation status'),
      refresh: () => {},
    }));
  },
};
