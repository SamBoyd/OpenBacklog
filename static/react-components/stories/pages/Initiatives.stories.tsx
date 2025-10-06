import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import Initiatives from '#pages/Initiatives';
import NavBar from '#components/reusable/NavBar';
import ChatDialog from '#components/ChatDialog/ChatDialog';

import { useTasksContext } from '#contexts/TasksContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useLocation } from '#hooks/useLocation.mock';
import { useUserPreferences } from '#hooks/useUserPreferences.mock';
import useChatMessages from '#hooks/useChatMessages.mock';
import { useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext.mock';

import {
    mockInitiativesAiJobResult,
    mockUseTasksContext,
    mockAiImprovementsContextReturn,
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockWorkspacesReturn,
    mockInitiativeAiJobResultError,
    mockInitiativeImprovements,
    mockUserPreferencesReturn,
    mockChatMessages,
    mockSuggestionsToBeResolvedContextReturn
} from '../example_data';

import { AiImprovementJobStatus, LENS } from '#types';
import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';
import { localStorageForStorybook } from '@alexgorbatchev/storybook-addon-localstorage';

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
                <ResponsiveLayout
                    leftColumnComponent={<ChatDialog />}
                    rightColumnComponent={<Initiatives />}
                />
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
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);
        
        useChatMessages.mockReturnValue({
                threadId: 'test-thread-id',
                messages: mockChatMessages.map(msg => ({
                    id: msg.id,
                    text: msg.text,
                    sender: msg.sender,
                    timestamp: msg.timestamp,
                    entityId: msg.entityId,
                    entityTitle: msg.entityTitle,
                    entityIdentifier: msg.entityIdentifier,
                    lens: LENS.INITIATIVES
                })),
                addMessage: (message: any) => {
                    console.log('Adding message:', message);
                },
                addUserMessage: (messageText: string, lens: any, entity: any) => {
                    console.log('Adding user message:', messageText);
                },
                startNewThread: () => {
                    console.log('Starting new thread');
                }
            });
            
        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
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
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
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
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        useChatMessages.mockReturnValue({
                threadId: 'test-thread-id',
                messages: mockChatMessages.map(msg => ({
                    id: msg.id,
                    text: msg.text,
                    sender: msg.sender,
                    timestamp: msg.timestamp,
                    entityId: msg.entityId,
                    entityTitle: msg.entityTitle,
                    entityIdentifier: msg.entityIdentifier,
                    lens: LENS.INITIATIVES
                })),
                addMessage: (message: any) => {
                    console.log('Adding message:', message);
                },
                addUserMessage: (messageText: string, lens: any, entity: any) => {
                    console.log('Adding user message:', messageText);
                },
                startNewThread: () => {
                    console.log('Starting new thread');
                }
            });
            
        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
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
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
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
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);

        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
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
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);

        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: { ...mockInitiativesAiJobResult, status: AiImprovementJobStatus.PENDING, result_data: null },
            isEntityLocked: true,
        });
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);
        
        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
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
        useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);

        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: mockInitiativesAiJobResult
        });
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);
        
        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
        };
    }
};

export const WithAiResultError: Story = {
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
        useTasksContext.mockReturnValue(mockUseTasksContext);

        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: mockInitiativeAiJobResultError
        });
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);
        
        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
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
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            loading: true
        });
        useSuggestionsToBeResolved.mockReturnValue(mockSuggestionsToBeResolvedContextReturn);
        
        return () => {
            useTasksContext.mockReset();
            useUserPreferences.mockReset();
            useInitiativesContext.mockReset();
            useWorkspaces.mockReset();
            useAiImprovementsContext.mockReset();
            useSuggestionsToBeResolved.mockReset();
        };
    }
};
