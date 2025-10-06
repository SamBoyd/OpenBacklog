import React, { useState } from 'react';
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
import { useBillingUsage } from '#hooks/useBillingUsage.mock';
import { useAiChat } from '#hooks/useAiChat.mock';

import {
    mockUseTasksContext,
    mockAiImprovementsContextReturn,
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockWorkspacesReturn,
    mockUserPreferencesReturn,
    mockUseBillingUsageReturn,
    mockUseAiChatReturn
} from '../example_data';

import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';
import { localStorageForStorybook } from '@alexgorbatchev/storybook-addon-localstorage';
import { ChatLayoutMode } from '#hooks/useUserPreferences';

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
    decorators: [
        (Story) => {

            return <Story />
        }
    ],
    parameters: {
        localStorage: localStorageForStorybook({
            'chatDialog_currentContext': [],
            'chat_messages': [],
            'thread_id': 'test-thread-id'
        }),
        layout: 'fullscreen',
        reactRouter: reactRouterParameters({
            location: {
                path: '/'
            },
            routing: reactRouterNestedAncestors([
                {
                    element: <div className="inset-0 flex flex-col h-screen w-screen">
                        <NavBar />
                        <ResponsiveLayout
                            leftColumnComponent={<ChatDialog />}
                            rightColumnComponent={<Initiatives />}
                        />
                    </div>
                }])
        })
    }
};

export default meta;
type Story = StoryObj<typeof Initiatives>;

export const Primary: Story = {
    args: {},
    decorators: [
        (Story) => {
            const [layoutMode, setLayoutMode] = useState<ChatLayoutMode>('normal')
            useUserPreferences.mockReturnValue({
                ...mockUserPreferencesReturn,
                preferences: {
                    ...mockUserPreferencesReturn.preferences,
                    chatLayoutMode: layoutMode
                },
                updateChatLayoutMode: setLayoutMode
            })

            return <Story />
        }
    ],
    beforeEach: () => {
        useLocation.mockReturnValue(mockLocationReturn);
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
        useBillingUsage.mockReturnValue(mockUseBillingUsageReturn)
        useAiChat.mockReturnValue(mockUseAiChatReturn)
    }
};
