import type { Meta, StoryObj } from '@storybook/react';
import { localStorageForStorybook } from '@alexgorbatchev/storybook-addon-localstorage';
import { delay, http, HttpResponse } from 'msw';

import { AiImprovementJobStatus, LENS, AgentMode, InitiativeDto, TaskDto } from '#types';
import { UserAccountStatus } from '#constants/userAccountStatus';

import ChatDialog from '#components/ChatDialog/ChatDialog';

import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';

import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { UserPreferencesProvider } from '#hooks/useUserPreferences';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useEntityFromUrl } from '#hooks/useEntityFromUrl.mock';
import { useActiveEntity } from '#hooks/useActiveEntity.mock';
import useChatMessages from '#hooks/useChatMessages.mock';
import { useAiChat } from '#hooks/useAiChat.mock';
import { useIsDeviceMobile } from '#hooks/isDeviceMobile.mock';
import { useBillingUsage } from '#hooks/useBillingUsage.mock';

import {
    mockAiImprovementsContextReturn,
    mockChatMessages,
    mockInitiativeAiJobResult,
    mockInitiativesContextReturn,
    mockUseTasksContext,
    mockUserPreferencesReturn,
    mockWorkspacesReturn,
    mockUseEntityFromUrlReturn,
    mockActiveEntityReturn,
    mockInitiatives,
    mockUseBillingUsageReturn,
    mockUseBillingUsageReturnNewUser,

} from '#stories/example_data';
import { SetStateAction, useState } from 'react';

// Mock localStorage
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

const meta: Meta<typeof ChatDialog> = {
    component: ChatDialog,
    parameters: {
        msw: {
            handlers: [
                http.post('/api/transcribe', async () => {
                    await delay(800);
                    return HttpResponse.json({ "transcript": "I guess this is a test.\n" });
                }),
            ],
        },
        localStorage: localStorageForStorybook({
            'chatDialog_currentContext': [],
            'chat_messages': [],
            'thread_id': 'test-thread-id'
        }),
    },
    globals: {
        // 👇 Set viewport for all component stories
        viewport: { value: 'mobile2', isRotated: false },
    },
    decorators: [
        (Story) => {
            const [context, setContext] = useState<(InitiativeDto | TaskDto)[]>([])

            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useActiveEntity.mockReturnValue(mockActiveEntityReturn);
            useEntityFromUrl.mockReturnValue(mockUseEntityFromUrlReturn);
            useBillingUsage.mockReturnValue(mockUseBillingUsageReturn)

            // Mock useChatMessages hook
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

            // Mock useAiChat hook
            useAiChat.mockReturnValue({
                jobResult: null,
                error: null,
                chatDisabled: false,
                sendMessage: (threadId: string, messages: any[], lens: any, mode: AgentMode) => {
                    console.log('Sending message:', { threadId, messages, lens, mode });
                },
                clearChat: () => {
                    console.log('Clearing chat');
                },
                currentContext: context,
                setCurrentContext: setContext,
                removeEntityFromContext: (function (entityId: string): void {
                    setContext(context.filter(e => e.id != entityId))
                })
            });

            // Mock useIsDeviceMobile hook
            useIsDeviceMobile.mockReturnValue(false);

            return <UserPreferencesProvider initialPreferences={mockUserPreferencesReturn.preferences}>
                <Story />
            </UserPreferencesProvider>
        },
    ],
};

export default meta;
type Story = StoryObj<typeof ChatDialog>;

export const Primary: Story = {
    args: {},
};

export const Error: Story = {
    args: {},
    decorators: [
        (Story) => {

            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useActiveEntity.mockReturnValue(mockActiveEntityReturn);
            useEntityFromUrl.mockReturnValue(mockUseEntityFromUrlReturn);

            // Mock with error state
            useAiImprovementsContext.mockReturnValue({
                ...mockAiImprovementsContextReturn,
                error: 'Failed to connect to AI service. Please check your internet connection and try again.',
                jobResult: {
                    ...mockInitiativeAiJobResult,
                    status: AiImprovementJobStatus.FAILED,
                    error_message: 'Request timeout after 30 seconds'
                }
            });

            // Mock useChatMessages hook
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

            // Mock useAiChat hook with error
            useAiChat.mockReturnValue({
                jobResult: {
                    ...mockInitiativeAiJobResult,
                    status: AiImprovementJobStatus.FAILED,
                    error_message: 'Request timeout after 30 seconds'
                },
                error: 'Failed to connect to AI service. Please check your internet connection and try again.',
                chatDisabled: false,
                sendMessage: (threadId: string, messages: any[], lens: any, mode: AgentMode) => {
                    console.log('Sending message (error scenario):', { threadId, messages, lens, mode });
                },
                clearChat: () => {
                    console.log('Clearing chat');
                },
                currentContext: [],
                setCurrentContext: function (value: SetStateAction<(InitiativeDto | TaskDto)[]>): void { },
                removeEntityFromContext: function (entityId: string): void { }
            });

            // Mock useIsDeviceMobile hook
            useIsDeviceMobile.mockReturnValue(false);

            return <UserPreferencesProvider initialPreferences={mockUserPreferencesReturn.preferences}>
                <Story />
            </UserPreferencesProvider>
        },
    ],
};


export const withCurrentEntity: Story = {
    args: {},
    decorators: [
        (Story) => {
            const [context, setContext] = useState<(InitiativeDto | TaskDto)[]>([])

            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);

            // Mock with current entity
            useActiveEntity.mockReturnValue({
                ...mockActiveEntityReturn,
                recentInitiatives: mockInitiatives.sort(() => 0.5 - Math.random()).map(i => i.id)
            });

            useEntityFromUrl.mockReturnValue({
                ...mockUseEntityFromUrlReturn,
                currentEntity: mockInitiatives[0]
            });

            // Mock useChatMessages hook
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

            // Mock useAiChat hook
            useAiChat.mockReturnValue({
                jobResult: null,
                error: null,
                chatDisabled: false,
                sendMessage: (threadId: string, messages: any[], lens: any, mode: AgentMode) => {
                    console.log('Sending message:', { threadId, messages, lens, mode });
                },
                clearChat: () => {
                    console.log('Clearing chat');
                },
                currentContext: context,
                setCurrentContext: setContext,
                removeEntityFromContext: (function (entityId: string): void {
                    setContext(context.filter(e => e.id != entityId))
                })
            });

            // Mock useIsDeviceMobile hook
            useIsDeviceMobile.mockReturnValue(false);

            return <UserPreferencesProvider initialPreferences={mockUserPreferencesReturn.preferences}>
                <Story />
            </UserPreferencesProvider>
        },
    ],
};

export const withoutSubscription: Story = {
    args: {},
    decorators: [
        (Story) => {
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                userIsOnboarded: true,
                data: {
                    currentBalance: 0,
                    transactions: [],
                    transactionsPagination: null,
                    subscriptionStatus: UserAccountStatus.NO_SUBSCRIPTION,
                    monthlyCreditsTotal: 500,
                    monthlyCreditsUsed: 0
                },
                userAccountDetails: {
                    balanceCents: 0,
                    status: UserAccountStatus.NO_SUBSCRIPTION,
                    onboardingCompleted: true,
                    monthlyCreditsTotal: 500,
                    monthlyCreditsUsed: 0
                }
            });

            return <UserPreferencesProvider initialPreferences={mockUserPreferencesReturn.preferences}>
                <Story />
            </UserPreferencesProvider>
        },
    ],
};