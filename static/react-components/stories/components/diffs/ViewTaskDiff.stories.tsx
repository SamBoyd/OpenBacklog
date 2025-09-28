import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';

import ViewTask from '#components/ViewTask';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { SuggestionsToBeResolvedContextProvider } from '#contexts/SuggestionsToBeResolvedContext';

import {
    mockTasks,
    mockUseTasksContext,
    mockTasksAiJobResult,
    mockTasksAiJobResultWithError,
    mockTaskImprovements,
    mockInitiativesContextReturn,
} from '../../example_data';

import {
    ManagedEntityAction,
} from '#types';


const meta: Meta<typeof ViewTask> = {
    title: 'Components/Diffs/ViewTask',
    component: ViewTask,
    parameters: {
        layout: 'fullscreen',
        nextRouter: {
            router: {
                route: '/initiatives/init-123/tasks/task-123/diff',
                pathname: '/initiatives/[initiativeId]/tasks/[taskId]/diff',
                query: { initiativeId: 'init-123', taskId: 'task-123' },
                asPath: '/initiatives/init-123/tasks/task-123/diff',
            },
        },
    },
};

export default meta;

type Story = StoryObj<typeof ViewTask>;


const mockTask = mockTasks[0];

/**
 * Story showing task with title and description changes from AI
 */
export const WithTitleAndDescriptionDiff: Story = {
    args: {},
    decorators: [
        (Story) => {
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [mockTask],
        });

        useAiImprovementsContext.mockReturnValue({
            ...useAiImprovementsContext,
            jobResult: mockTasksAiJobResult,
            taskImprovements: mockTaskImprovements,
            loading: false,
            error: null,
            isEntityLocked: false,
            markJobAsResolved: fn().mockName('deleteJob'),
            resetError: fn().mockName('resetError'),
            setThreadId: fn().mockName('setThreadId'),
            requestImprovement: fn().mockName('requestImprovement'),
            updateImprovement: fn().mockName('updateImprovement'),
            initiativeImprovements: {},
        });
    }
};

export const withOnlyTitleDiff: Story = {
    args: {},
    decorators: [
        (Story) => (
            <SuggestionsToBeResolvedContextProvider>
                <Story />
            </SuggestionsToBeResolvedContextProvider>
        ),
    ],
    beforeEach: () => {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [mockTask],
        });

        useAiImprovementsContext.mockReturnValue({
            ...useAiImprovementsContext,
            jobResult: {
                ...mockTasksAiJobResult,
                result_data: {
                    message: 'The task has been updated with the new details.',
                    managed_tasks: [
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockTasks[0].identifier,
                            title: 'Updated task title - 2323',
                            description: null,
                            checklist: []
                        }
                    ]
                }
            },
            taskImprovements: {
                [mockTasks[0].identifier]: {
                    action: ManagedEntityAction.UPDATE,
                    identifier: mockTasks[0].identifier,
                    title: 'Updated task title - 2323',
                    description: null,
                    checklist: []
                }
            },
            loading: false,
            error: null,
            isEntityLocked: false,
            markJobAsResolved: fn().mockName('deleteJob'),
            resetError: fn().mockName('resetError'),
            setThreadId: fn().mockName('setThreadId'),
            requestImprovement: fn().mockName('requestImprovement'),
            updateImprovement: fn().mockName('updateImprovement'),
            initiativeImprovements: {},
        });
    }
};


export const withOnlyDescriptionDiff: Story = {
    args: {},
    decorators: [
        (Story) => (
            <SuggestionsToBeResolvedContextProvider>
                <Story />
            </SuggestionsToBeResolvedContextProvider>
        ),
    ],
    beforeEach: () => {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [mockTask],
        });

        useAiImprovementsContext.mockReturnValue({
            ...useAiImprovementsContext,
            jobResult: {
                ...mockTasksAiJobResult,
                result_data: {
                    message: 'The task has been updated with the new details.',
                    managed_tasks: [
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockTasks[0].identifier,
                            title: null,
                            description: 'Updated task description',
                            checklist: []
                        }
                    ]
                }
            },
            taskImprovements: {
                [mockTasks[0].identifier]: {
                    action: ManagedEntityAction.UPDATE,
                    identifier: mockTasks[0].identifier,
                    title: null,
                    description: mockTasks[0].description + ' some update',
                    checklist: []
                }
            },
            loading: false,
            error: null,
            isEntityLocked: false,
            markJobAsResolved: fn().mockName('deleteJob'),
            resetError: fn().mockName('resetError'),
            setThreadId: fn().mockName('setThreadId'),
            requestImprovement: fn().mockName('requestImprovement'),
            updateImprovement: fn().mockName('updateImprovement'),
            initiativeImprovements: {},
        });
    }
};


/**
 * Story showing task marked for deletion by AI
 */
export const DeleteTask: Story = {
    args: {},
    decorators: [
        (Story) => (
            <SuggestionsToBeResolvedContextProvider>
                <Story />
            </SuggestionsToBeResolvedContextProvider>
        ),
    ],
    beforeEach: () => {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [mockTask],
        });

        

        useAiImprovementsContext.mockReturnValue({
            jobResult: {
                ...mockTasksAiJobResult,
                result_data: {
                    message: 'The task has been updated with the new details.',
                    managed_tasks: [
                        {
                            action: ManagedEntityAction.DELETE,
                            identifier: mockTasks[0].identifier,
                        }
                    ]
                }
            },
            initiativeImprovements: {},
            taskImprovements: {
                [mockTask.identifier]: {
                    action: ManagedEntityAction.DELETE,
                    identifier: mockTask.identifier
                },
            },
            loading: false,
            error: null,
            isEntityLocked: false,
            markJobAsResolved: fn(),
            resetError: fn(),
            setThreadId: fn(),
            requestImprovement: fn(),
            updateImprovement: fn(),
        });
    }
};

/**
 * Story showing loading state while aiJob are being fetched
 */
export const AiJobLoading: Story = {
    args: {},
    decorators: [
        (Story) => {

            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [mockTask],
        });

        useAiImprovementsContext.mockReturnValue({
            jobResult: null,
            taskImprovements: {},
            loading: true,
            error: null,
            isEntityLocked: false,
            markJobAsResolved: fn(),
            resetError: fn(),
            setThreadId: fn(),
            requestImprovement: fn(),
            updateImprovement: fn(),
            initiativeImprovements: {}
        });

    }
};

/**
 * Story showing error state when AI improvement fails
 */
export const WithError: Story = {
    args: {},
    decorators: [
        (Story) => {
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [mockTask],
            error: 'Failed to load task data',
        });

        useAiImprovementsContext.mockReturnValue({
            jobResult: mockTasksAiJobResultWithError,
            taskImprovements: {},
            loading: false,
            error: 'Failed to process AI improvement',
            isEntityLocked: false,
            markJobAsResolved: fn(),
            resetError: fn(),
            setThreadId: fn(),
            requestImprovement: fn(),
            updateImprovement: fn(),
            initiativeImprovements: {},
        });
    }
};
