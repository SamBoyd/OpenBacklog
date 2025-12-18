import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import {
    mockContextDocumentReturn,
    mockInitiativesContextReturn,
    mockUseTasksContext,
    mockWorkspacesReturn
} from '../example_data';

import { useTasksContext } from '#contexts/TasksContext.mock';
import { useContextDocument } from '#hooks/useContextDocument.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import NavBar from '#components/reusable/NavBar';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import ContextDocument from '#pages/ContextDocument';
import { ContextDocumentDto } from '#types';
import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';

const meta: Meta<typeof ContextDocument> = {
    component: ContextDocument,
    decorators: [],
    async beforeEach() {
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);

        return () => {
            useWorkspaces.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof ContextDocument>;

// Create the wrapper structure that matches how Initiatives is rendered in Main.tsx
const getInitiativesWithWrappers = () => {
    return reactRouterNestedAncestors([
        {
            element: <div className="inset-0 flex flex-col h-screen w-screen">
                <NavBar />
                <div className="relative w-full">
                    <ResponsiveLayout>
                        <ContextDocument />
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
            routing: getInitiativesWithWrappers()
        })
    },
    async beforeEach() {
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useContextDocument.mockReturnValue(mockContextDocumentReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);


        return () => {
            useTasksContext.mockReset();
            useContextDocument.mockReset();
            useWorkspaces.mockReset();
            useInitiativesContext.mockReset();
        };
    },
};


export const Placeholder: Story = {
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
        useContextDocument.mockReturnValue({
            ...mockContextDocumentReturn,
            contextDocument: {
                ...mockContextDocumentReturn.contextDocument,
                content: ''
            } as ContextDocumentDto
        });
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);


        return () => {
            useTasksContext.mockReset();
            useContextDocument.mockReset();
            useWorkspaces.mockReset();
            useInitiativesContext.mockReset();
        };

    },
};
