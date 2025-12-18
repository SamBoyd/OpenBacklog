import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import Initiatives from '#pages/Initiatives';
import NavBar from '#components/reusable/NavBar';

import { useTasksContext } from '#contexts/TasksContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useLocation } from '#hooks/useLocation.mock';
import { useUserPreferences } from '#hooks/useUserPreferences.mock';

import {
    mockUseTasksContext,
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockWorkspacesReturn,
    mockUserPreferencesReturn,
} from '../example_data';

import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';
import { localStorageForStorybook } from '@alexgorbatchev/storybook-addon-localstorage';
import { mockUseThemePrioritizationReturn, useThemePrioritization } from '#hooks/useThemePrioritization.mock';

const mockLocalStorage = {
    storage: new Map<string, string>([
        ['chatDialog_currentContext', JSON.stringify([])],
        ['chat_messages', JSON.stringify([])],
        ['thread_id', 'test-thread-id']
    ]),
    getItem: function(key: string) {
        return this.storage.get(key) || null;
    },
    setItem: function(key: string, value: string) {
        this.storage.set(key, value);
    },
    removeItem: function(key: string) {
        this.storage.delete(key);
    },
    clear: function() {
        this.storage.clear();
    }
};

// Set up global localStorage mock before any stories run
Object.defineProperty(window, 'localStorage', {
    value: mockLocalStorage,
    writable: true
});

const meta: Meta<typeof Initiatives> = {
    component: Initiatives,
    decorators: [],
    parameters: {
        localStorage: localStorageForStorybook({
            'chatDialog_currentContext': [],
            'chat_messages': [],
            'thread_id': 'test-thread-id'
        }),
    }
};

export default meta;
type Story = StoryObj<typeof Initiatives>;

// Create the wrapper structure that matches how Initiatives is rendered in Main.tsx
const getInitiativesWithWrappers = () => {
    return reactRouterNestedAncestors([
        {
            element: <div className="inset-0 flex flex-col h-screen w-screen">
                <NavBar />
                <ResponsiveLayout>
                    <Initiatives />
                </ResponsiveLayout>
            </div>
        }
    ]);
};

export const Primary: Story = {
    args: {},
    parameters: {
        layout: 'fullscreen',
        reactRouter: reactRouterParameters({
            location: {
                path: '/'
            },
            routing: getInitiativesWithWrappers()
        })
    },
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useThemePrioritization.mockReturnValue(mockUseThemePrioritizationReturn);

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
        };
    }
};

export const WithNoData: Story = {
    args: {},
    parameters: {
        layout: 'fullscreen',
        reactRouter: reactRouterParameters({
            location: {
                path: '/'
            },
            routing: getInitiativesWithWrappers()
        })
    },
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue({ ...mockUseTasksContext, tasks: [] });
        useInitiativesContext.mockReturnValue({ ...mockInitiativesContextReturn, initiativesData: [] });

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
        };
    }
};

export const WithSmallData: Story = {
    args: {},
    parameters: {
        layout: 'fullscreen',
        reactRouter: reactRouterParameters({
            location: {
                path: '/'
            },
            routing: getInitiativesWithWrappers()
        })
    },
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: mockInitiativesContextReturn.initiativesData?.slice(0,3) || [],
        });

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
        };
    }
};

export const WithDataError: Story = {
    args: {},
    parameters: {
        layout: 'fullscreen',
        reactRouter: reactRouterParameters({
            location: {
                path: '/'
            },
            routing: getInitiativesWithWrappers()
        })
    },
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue({ ...mockUseTasksContext, tasks: [] });
        useInitiativesContext.mockReturnValue({ ...mockInitiativesContextReturn, error: 'This is a test error', initiativesData: [] });

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
        };
    }
};

export const WithoutWorkspaces: Story = {
    args: {},
    parameters: {
        layout: 'fullscreen',
        reactRouter: reactRouterParameters({
            location: {
                path: '/'
            },
            routing: getInitiativesWithWrappers()
        })
    },
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useWorkspaces.mockReturnValue({
            ...mockWorkspacesReturn,
            workspaces: [],
            currentWorkspace: null
        });
        useTasksContext.mockReturnValue(mockUseTasksContext);

        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
        };
    }
};

export const Loading: Story = {
    args: {},
    parameters: {
        layout: 'fullscreen',
        reactRouter: reactRouterParameters({
            location: {
                path: '/'
            },
            routing: getInitiativesWithWrappers()
        })
    },
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useWorkspaces.mockReturnValue({
            ...mockWorkspacesReturn,
        });
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            shouldShowSkeleton: true
        });
        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            shouldShowSkeleton: true
        });

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
        };
    }
};
