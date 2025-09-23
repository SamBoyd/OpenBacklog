// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import WorkspaceSwitcher from '#components/WorkspaceSwitcher/WorkspaceSwitcher';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { mockAddWorkspace, mockChangeWorkspace, mockWorkspacesReturn } from '../example_data';

const meta: Meta<typeof WorkspaceSwitcher> = {
    component: WorkspaceSwitcher,
    async beforeEach() {
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);

        return () => {
            useWorkspaces.mockReset();
        }
    }
};

export default meta;
type Story = StoryObj<typeof WorkspaceSwitcher>;

export const Default: Story = {
    args: {
        workspaceLimit: 3
    },
};


export const NoWorkspace: Story = {
    args: {
        workspaceLimit: 1
    },
    async beforeEach() {
        useWorkspaces.mockReturnValue({
            workspaces: [],
            currentWorkspace: null,
            isLoading: false,
            isProcessing: false,
            changeWorkspace: mockChangeWorkspace,
            addWorkspace: mockAddWorkspace,
            error: null,
            refresh: () => { }
        });
    }
};

export const Loading: Story = {
    args: {
        workspaceLimit: 1
    },
    async beforeEach() {
        useWorkspaces.mockReturnValue({
            workspaces: [],
            currentWorkspace: null,
            isLoading: true,
            isProcessing: false,
            changeWorkspace: mockChangeWorkspace,
            addWorkspace: mockAddWorkspace,
            error: null,
            refresh: () => { }
        });
    }
};

export const Error: Story = {
    args: {
        workspaceLimit: 1
    },
    async beforeEach() {
        useWorkspaces.mockReturnValue({
            workspaces: [],
            currentWorkspace: null,
            isLoading: false,
            isProcessing: false,
            changeWorkspace: mockChangeWorkspace,
            addWorkspace: mockAddWorkspace,
            error: { name: 'test error', message: 'Failed to fetch workspaces' },
            refresh: () => { }
        });
    }
};
