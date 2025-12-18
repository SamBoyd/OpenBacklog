import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import Tasks from '#pages/Tasks';
import NavBar from '#components/reusable/NavBar';
import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';

import { useTasksContext } from '#contexts/TasksContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useLocation } from '#hooks/useLocation.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';

import {
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockUseTasksContext,
    mockWorkspacesReturn,
    mockFieldDefinitionsReturn,
} from '../example_data';


const meta: Meta<typeof Tasks> = {
    component: Tasks,
    decorators: [],
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useFieldDefinitions.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof Tasks>;

// Create the wrapper structure that matches how Tasks is rendered in Main.tsx
const getTasksWithWrappers = () => {
    return reactRouterNestedAncestors([
        {
            element: <div className="inset-0 flex flex-col h-screen w-screen">
                <NavBar />
                <div className="relative w-full">
                    <ResponsiveLayout>
                        <Tasks />
                    </ResponsiveLayout>
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
            routing: getTasksWithWrappers()
        })
    },
};

export const WithNoData: Story = {
    args: {},
    parameters: {
        layout: 'fullscreen',
        reactRouter: reactRouterParameters({
            location: {
                path: '/'
            },
            routing: getTasksWithWrappers()
        })
    },
    async beforeEach() {
        useTasksContext.mockReturnValue({ ...mockUseTasksContext, tasks: [] });
        useInitiativesContext.mockReturnValue({ ...mockInitiativesContextReturn, initiativesData: [] });
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useFieldDefinitions.mockReset();
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
            routing: getTasksWithWrappers()
        })
    },
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue({
            ...mockWorkspacesReturn,
            workspaces: [],
            currentWorkspace: null
        });
        useTasksContext.mockReturnValue(mockUseTasksContext);

        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
        };
    }
};
