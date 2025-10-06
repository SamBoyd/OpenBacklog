import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import { Dashboard } from '#pages/Dashboard';
import NavBar from '#components/reusable/NavBar';

import { useTasksContext } from '#contexts/TasksContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useLocation } from '#hooks/useLocation.mock';

import {
    mockAiImprovementsContextReturn,
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockUseTasksContext,
    mockWorkspacesReturn,
} from '../example_data';

const meta: Meta<typeof Dashboard> = {
    component: Dashboard,
    decorators: [],
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof Dashboard>;

// Create the wrapper structure that matches how Dashboard is rendered in Main.tsx
const getDashboardWithWrappers = () => {
    return reactRouterNestedAncestors([
        {
            element: <div className="inset-0 flex flex-col h-screen w-screen">
                <NavBar />
                <div className="relative w-full">
                    <Dashboard />
                </div>
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
            routing: getDashboardWithWrappers()
        })
    },
};

