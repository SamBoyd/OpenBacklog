import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { reactRouterParameters } = require('storybook-addon-remix-react-router');

import Onboarding from '#pages/Onboarding';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { UserAccountStatus } from '#constants/userAccountStatus';
import { mockWorkspace, mockWorkspacesReturn } from '#stories/example_data';
import { WorkspaceDto } from '#types';
import { useOpenbacklogToken, mockUseOpenbacklogTokenGeneratedReturn } from '#hooks/useOpenbacklogToken.mock';
import { useOnboardingPolling } from '#hooks/useOnboardingPolling.mock';
import {
    mockPollingWorkspace,
    mockPollingFoundationStart,
    mockPollingFoundationVision,
    mockPollingFoundationCharacters,
    mockPollingFoundationStrategy,
    mockPollingFoundationTheme,
    mockComplete
} from '#hooks/useOnboardingPolling.mock';

const mockOnboardCustomer = async () => {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    alert('Page will now navigate away from onboarding')
}

// Note: This story file is primarily for Pro features.
// Community Edition onboarding is simplified.

const mockAddWorkspace = async (workspace: Omit<WorkspaceDto, 'id'>): Promise<WorkspaceDto> => {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    return mockWorkspace
}

const meta = {
    title: 'Pages/Onboarding',
    component: Onboarding,
    parameters: {
        layout: 'fullscreen',
        docs: {
            description: {
                component: 'Carousel-style onboarding flow for new users. Guides users through product introduction, features, and pricing.',
            },
        },
        reactRouter: reactRouterParameters({
            routing: { path: '/onboarding' },
        }),
    },
    decorators: [
        (Story) => {
            // Mock the hooks
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockPollingWorkspace);
            return <Story />;
        }
    ],
    argTypes: {
        step: {
            control: 'select',
            options: ['planning', 'ai-assistants', 'coding-context', 'pricing'],
            description: 'Which step of onboarding to show',
        },
    },
} satisfies Meta<typeof Onboarding>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * The default onboarding carousel showing all steps.
 * Users can navigate through the carousel to see planning, AI assistants, coding context, and pricing.
 */
export const Default: Story = {
};

export const ExistingWorkspace: Story = {
    decorators: [
        (Story) => {
            useWorkspaces.mockReturnValue(mockWorkspacesReturn)
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockPollingWorkspace);
            return <Story />;
        }
    ],
};

/**
 * MCP Setup page - Polling for workspace creation
 * Shows the initial state where the user hasn't created a workspace yet via MCP.
 */
export const MCPSetupPollingWorkspace: Story = {
    decorators: [
        (Story) => {
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockPollingWorkspace);
            return <Story />;
        }
    ],
};

/**
 * MCP Setup page - Foundation polling just started
 * Workspace exists but no strategic entities have been created yet.
 */
export const MCPSetupFoundationStart: Story = {
    decorators: [
        (Story) => {
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockPollingFoundationStart);
            return <Story />;
        }
    ],
};

/**
 * MCP Setup page - Vision defined
 * Shows progress after the user's product vision has been captured.
 */
export const MCPSetupFoundationVision: Story = {
    decorators: [
        (Story) => {
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockPollingFoundationVision);
            return <Story />;
        }
    ],
};

/**
 * MCP Setup page - Characters created (heroes & villains)
 * Shows progress after heroes and villains have been defined.
 */
export const MCPSetupFoundationCharacters: Story = {
    decorators: [
        (Story) => {
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockPollingFoundationCharacters);
            return <Story />;
        }
    ],
};

/**
 * MCP Setup page - Strategy defined (pillars & outcomes)
 * Shows progress after strategic pillars and outcomes have been set.
 */
export const MCPSetupFoundationStrategy: Story = {
    decorators: [
        (Story) => {
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockPollingFoundationStrategy);
            return <Story />;
        }
    ],
};

/**
 * MCP Setup page - Theme selected
 * Shows progress after the roadmap theme (focus area) has been defined.
 * Only missing the final initiative creation.
 */
export const MCPSetupFoundationTheme: Story = {
    decorators: [
        (Story) => {
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockPollingFoundationTheme);
            return <Story />;
        }
    ],
};

/**
 * MCP Setup page - Complete
 * Shows the success state when initiatives have been detected and user will be redirected.
 */
export const MCPSetupComplete: Story = {
    decorators: [
        (Story) => {
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            useOpenbacklogToken.mockReturnValue(mockUseOpenbacklogTokenGeneratedReturn);
            useOnboardingPolling.mockReturnValue(mockComplete);
            return <Story />;
        }
    ],
};
