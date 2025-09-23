import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { withRouter, reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import { MainContent } from '#pages/Main';
import InitiativesBacklog from '#pages/InitiativesBacklog';
import AppBackground from '#components/AppBackground';
import NavBar from '#components/reusable/NavBar';
import ChatDialog from '#components/ChatDialog/ChatDialog';
import ResizableTwoColumns from '#components/resizableTwoColumns';

import { useTasksContext } from '#contexts/TasksContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useLocation } from '#hooks/useLocation.mock';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';
import { useUserPreferences } from '#hooks/useUserPreferences.mock';

import {
    mockInitiativesAiJobResult,
    mockUseTasksContext,
    mockAiImprovementsContextReturn,
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockWorkspacesReturn,
    mockInitiativeAiJobResultError,
    mockInitiatives,
    mockFieldDefinitionsReturn,
    mockInitiativeGroupsReturn,
    mockUserPreferencesReturn,
    mockGroups,
    mockInitiativeImprovements,
} from '../example_data';

import { AiImprovementJobStatus, GroupDto, InitiativeStatus } from '#types';
import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';

const meta: Meta<typeof InitiativesBacklog> = {
    component: InitiativesBacklog,
    decorators: [withRouter],
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: mockInitiatives.map(initiative => ({
                ...initiative,
                status: InitiativeStatus.BACKLOG
            }))
        });
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useInitiativeGroups.mockReset();
            useFieldDefinitions.mockReset();
            useUserPreferences.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof InitiativesBacklog>;

// Create the wrapper structure that matches how Initiatives is rendered in Main.tsx
const getInitiativesWithWrappers = () => {
    return reactRouterNestedAncestors([
        {
            element: <div className="inset-0 flex flex-col h-screen w-screen">
                <NavBar />
                <div className="relative w-full">
                    <ResponsiveLayout
                        leftColumnComponent={<ChatDialog />}
                        rightColumnComponent={<InitiativesBacklog />}
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
            routing: getInitiativesWithWrappers()
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
            routing: getInitiativesWithWrappers()
        })
    },
    async beforeEach() {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue({ ...mockUseTasksContext, tasks: [] });
        useInitiativesContext.mockReturnValue({ ...mockInitiativesContextReturn, initiativesData: [] });
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useInitiativeGroups.mockReset();
            useFieldDefinitions.mockReset();
        };
    }
};

export const WithPendingAiResult: Story = {
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
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: { ...mockInitiativesAiJobResult, status: AiImprovementJobStatus.PENDING, result_data: null },
            isEntityLocked: true,
        });
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useInitiativeGroups.mockReset();
            useFieldDefinitions.mockReset();
        };
    }
};

export const WithAiResult: Story = {
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
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: mockInitiativesAiJobResult
        });
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useInitiativeGroups.mockReset();
            useFieldDefinitions.mockReset();
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
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            loading: true
        });
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useInitiativeGroups.mockReset();
            useFieldDefinitions.mockReset();
        };
    }
};


export const withGrouping: Story = {
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
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: mockInitiatives.map(initiative => ({
                ...initiative,
                status: InitiativeStatus.BACKLOG
            }))
        });
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useUserPreferences.mockReturnValue({
            ...mockUserPreferencesReturn,
            preferences: {
                ...mockUserPreferencesReturn.preferences,
                selectedGroupIds: ['all-pseudo-group', ...mockGroups.map((group: GroupDto) => group.id)]
            }
        });

        return () => {
            useTasksContext.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useInitiativeGroups.mockReset();
            useFieldDefinitions.mockReset();
            useUserPreferences.mockReset();
        };
    },
}