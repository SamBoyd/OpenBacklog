import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { withRouter, reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import { SuggestionsToBeResolvedContextProvider } from '#contexts/SuggestionsToBeResolvedContext';
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

import {
    mockUseTasksContext,
    mockAiImprovementsContextReturn,
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockWorkspacesReturn,
    mockInitiativeImprovements,
    mockUserPreferencesReturn,
    mockChatMessages,
    mockInitiatives,
    mockTasks,
    mockTasksData
} from '../../example_data';

import { AgentMode, AiImprovementJobStatus, CreateInitiativeModel, DeleteInitiativeModel, LENS, ManagedEntityAction, UpdateInitiativeModel } from '#types';
import { localStorageForStorybook } from '@alexgorbatchev/storybook-addon-localstorage';
import { loremIpsum } from 'lorem-ipsum';

const mockLocalStorage = {
    storage: new Map<string, string>([
        ['chatDialog_currentContext', JSON.stringify([])],
        ['chat_messages', JSON.stringify([])],
        ['thread_id', 'test-thread-id']
    ]),
    getItem: function (key: string) {
        return this.storage.get(key) || null;
    },
    setItem: function (key: string, value: string) {
        this.storage.set(key, value);
    },
    removeItem: function (key: string) {
        this.storage.delete(key);
    },
    clear: function () {
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
    parameters: {
        localStorage: localStorageForStorybook({
            'chatDialog_currentContext': [],
            'chat_messages': [],
            'thread_id': 'test-thread-id'
        }),
    },
    decorators: [
        (Story) => {
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ]
};

export default meta;
type Story = StoryObj<typeof Initiatives>;

export const Primary: Story = {
    args: {},
    parameters: {
        layout: 'fullscreen',
    },
    decorators: [
        (Story) => {
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
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

            return <Story />;
        }
    ],
    beforeEach: () => {
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            loading: false,
            isEntityLocked: false,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: {
                id: '123',
                lens: LENS.INITIATIVE,
                thread_id: 'thread1',
                status: AiImprovementJobStatus.COMPLETED,
                mode: AgentMode.EDIT,
                input_data: mockInitiatives,
                result_data: {
                    message: 'Some random summary of changes',
                    managed_initiatives: [
                        {
                            action: ManagedEntityAction.CREATE,
                            title: loremIpsum({ count: 1, format: 'plain' }),
                            description: loremIpsum({ count: 3, format: 'plain', units: 'paragraphs' }),
                            order: 0,
                            workspace_identifier: '123',
                            tasks: mockTasksData,
                        } as CreateInitiativeModel,
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockInitiatives[0].identifier,
                            title: loremIpsum({ count: 1, format: 'plain' }),
                            description: loremIpsum({ count: 3, format: 'plain', units: 'paragraphs' }),
                            order: 1,
                        } as UpdateInitiativeModel,
                        {
                            action: ManagedEntityAction.CREATE,
                            title: loremIpsum({ count: 1, format: 'plain' }),
                            description: loremIpsum({ count: 3, format: 'plain', units: 'paragraphs' }),
                            order: 2,
                            workspace_identifier: '123'
                        } as CreateInitiativeModel,
                        {
                            action: ManagedEntityAction.DELETE,
                            identifier: mockInitiatives[1].identifier,
                        } as DeleteInitiativeModel
                    ]
                },
                messages: [{ role: 'user', content: 'Let me explain the changes I made to the task - I\'ve updated the title and description with some placeholder text', suggested_changes: [] }],
                error_message: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                user_id: mockTasks[0].user_id
            },
        })
    }
};
