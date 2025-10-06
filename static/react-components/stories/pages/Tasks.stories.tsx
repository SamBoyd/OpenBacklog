import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import Tasks from '#pages/Tasks';
import NavBar from '#components/reusable/NavBar';
import ChatDialog from '#components/ChatDialog/ChatDialog';
import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';

import { AiImprovementJobStatus } from '#types';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useLocation } from '#hooks/useLocation.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';
import { useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext.mock';

import {
    mockTasksAiJobResult,
    mockAiImprovementsContextReturn,
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockUseTasksContext,
    mockWorkspacesReturn,
    mockTasksAiJobResultWithError,
    mockFieldDefinitionsReturn,
    mockInitiativeImprovements,
    mockSuggestionsToBeResolvedContextReturn,
} from '../example_data';


const meta: Meta<typeof Tasks> = {
    component: Tasks,
    decorators: [],
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useAiImprovementsContext.mockReset();
            useWorkspaces.mockReset();
            useFieldDefinitions.mockReset();
            useSuggestionsToBeResolved.mockReset();
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
                    <ResponsiveLayout
                        leftColumnComponent={<ChatDialog />}
                        rightColumnComponent={<Tasks />}
                    />
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
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);
        
        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useFieldDefinitions.mockReset();
            useSuggestionsToBeResolved.mockReset();
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
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useAiImprovementsContext.mockReset();
            useWorkspaces.mockReset();
            useSuggestionsToBeResolved.mockReset();
        };
    }
};


export const withPendingAiJob: Story = {
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
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);

        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: { ...mockTasksAiJobResult, status: AiImprovementJobStatus.PENDING, result_data: null },
            isEntityLocked: true,
        });

        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
        };
    }
};


export const withAiJob: Story = {
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
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);

        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: mockTasksAiJobResult
        });

        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
        };
    }
};

export const withAiJobError: Story = {
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
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: mockTasksAiJobResultWithError
        });

        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
        };
    }
};
