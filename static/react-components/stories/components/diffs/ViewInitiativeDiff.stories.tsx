import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import ViewInitiativeDiff from '#components/ViewInitiativeDiff';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useActiveEntity } from '#hooks/useActiveEntity.mock';
import { useUserPreferences } from '#hooks/useUserPreferences.mock';
import { SuggestionsToBeResolvedContextProvider } from '#contexts/SuggestionsToBeResolvedContext';

import {
    mockInitiatives,
    mockUseTasksContext,
    mockInitiativesContextReturn,
    mockAiImprovementsContextReturn,
    mockActiveEntityReturn,
    mockUserPreferencesReturn,
    mockInitiativeAiJobResult,
    mockInitiativeAiJobResultError,
    mockTasks,
    mockWorkspace
} from '../../example_data';

import {
    ManagedEntityAction,
} from '#types';

const meta: Meta<typeof ViewInitiativeDiff> = {
    title: 'Components/Diffs/ViewInitiativeDiff',
    component: ViewInitiativeDiff,
    parameters: {
        layout: 'fullscreen',
    },
};

export default meta;

type Story = StoryObj<typeof ViewInitiativeDiff>;

export const WithTitleAndDescriptionDiff: Story = {
    args: {
        initiativeId: mockInitiatives[0].id,
    },
    decorators: [
        (Story) => {
            useActiveEntity.mockReturnValue({
                ...mockActiveEntityReturn,
                activeInitiativeId: mockInitiatives[0].id,
            });

            useUserPreferences.mockReturnValue(mockUserPreferencesReturn);

            useAiImprovementsContext.mockReturnValue({
                ...mockAiImprovementsContextReturn,
                jobResult: {
                    ...mockInitiativeAiJobResult,
                    result_data: {
                        message: "Here's your mock update to the initiative",
                        managed_initiatives: [
                            {
                                action: ManagedEntityAction.UPDATE,
                                identifier: mockInitiatives[0].identifier,
                                title: 'Implement CI/CD pipeline',
                                description: 'Set up continuous integration and deployment pipeline to automate testing and deployment processes.',
                                tasks: []
                            }
                        ]
                    }
                },
                initiativeImprovements: {
                    [mockInitiatives[0].identifier]: {
                        action: ManagedEntityAction.UPDATE,
                        identifier: mockInitiatives[0].identifier,
                        title: 'Implement CI/CD pipeline',
                        description: 'Set up continuous integration and deployment pipeline to automate testing and deployment processes.',
                        tasks: [],
                    }
                },
                loading: false,
                error: null,
                isEntityLocked: false,
            });

            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useTasksContext.mockReturnValue(mockUseTasksContext);

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [
                {
                    ...mockInitiatives[0],
                    tasks: mockTasks.slice(0, 5),
                }
            ]
        });
    }
}

export const withOnlyTitleDiff: Story = {
    args: {
        initiativeId: mockInitiatives[0].id,
    },
    decorators: [
        (Story) => {
            // Set up all mocks for this story


            useActiveEntity.mockReturnValue({
                ...mockActiveEntityReturn,
                activeInitiativeId: mockInitiatives[0].id,
            });

            useUserPreferences.mockReturnValue(mockUserPreferencesReturn);

            useAiImprovementsContext.mockReturnValue({
                ...mockAiImprovementsContextReturn,
                jobResult: {
                    ...mockInitiativeAiJobResult,
                    result_data: {
                        message: 'Updated the initiative title only.',
                        managed_initiatives: [
                            {
                                action: ManagedEntityAction.UPDATE,
                                identifier: mockInitiatives[0].identifier,
                                title: 'Updated Initiative Title - New Version',
                                description: null,
                                tasks: [],
                            }
                        ]
                    }
                },
                initiativeImprovements: {
                    [mockInitiatives[0].identifier]: {
                        action: ManagedEntityAction.UPDATE,
                        identifier: mockInitiatives[0].identifier,
                        title: 'Updated Initiative Title - New Version',
                        description: null,
                        tasks: [],
                    }
                },
                loading: false,
                error: null,
                isEntityLocked: false,
            });

            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockTasks.slice(0, 5)
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [
                {
                    ...mockInitiatives[0],
                    tasks: mockTasks.slice(0, 5),
                }
            ]
        });
    }
}

export const withOnlyDescriptionDiff: Story = {
    args: {
        initiativeId: mockInitiatives[0].id,
    },
    decorators: [
        (Story) => {
            // Set up all mocks for this story


            useActiveEntity.mockReturnValue({
                ...mockActiveEntityReturn,
                activeInitiativeId: mockInitiatives[0].id,
            });

            useUserPreferences.mockReturnValue(mockUserPreferencesReturn);


            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockTasks.slice(0, 5)
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [
                {
                    ...mockInitiatives[0],
                    tasks: mockTasks.slice(0, 5),
                }
            ]
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: {
                ...mockInitiativeAiJobResult,
                result_data: {
                    message: 'Updated the initiative description with more detailed information.',
                    managed_initiatives: [
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockInitiatives[0].identifier,
                            title: null,
                            description: 'This initiative has been enhanced with additional context and clearer objectives to better align with our strategic goals.',
                            tasks: [],
                        }
                    ]
                }
            },
            initiativeImprovements: {
                [mockInitiatives[0].identifier]: {
                    action: ManagedEntityAction.UPDATE,
                    identifier: mockInitiatives[0].identifier,
                    title: null,
                    description: 'This initiative has been enhanced with additional context and clearer objectives to better align with our strategic goals.',
                    tasks: [],
                }
            },
            loading: false,
            error: null,
            isEntityLocked: false,
        });
    }
}

export const withOnlyTasksDiff: Story = {
    args: {
        initiativeId: mockInitiatives[0].id,
    },
    decorators: [
        (Story) => {
            // Set up all mocks for this story
            useActiveEntity.mockReturnValue({
                ...mockActiveEntityReturn,
                activeInitiativeId: mockInitiatives[0].id,
            });

            useUserPreferences.mockReturnValue(mockUserPreferencesReturn);

            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockTasks.slice(0, 5)
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [
                {
                    ...mockInitiatives[0],
                    tasks: mockTasks.slice(0, 5),
                }
            ]
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: {
                ...mockInitiativeAiJobResult,
                result_data: {
                    message: 'Updated the tasks within this initiative.',
                    managed_initiatives: [
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockInitiatives[0].identifier,
                            title: null,
                            description: null,
                            tasks: [
                                {
                                    action: ManagedEntityAction.UPDATE,
                                    identifier: mockTasks[0].identifier,
                                    title: 'Updated Task Title from Initiative Context',
                                    description: 'Updated task description from initiative improvement',
                                    checklist: mockTasks[0].checklist,
                                },
                                {
                                    action: ManagedEntityAction.CREATE,
                                    title: 'New Task Created from Initiative',
                                    description: 'This task was created as part of the initiative improvement',
                                    initiative_identifier: mockInitiatives[0].identifier,
                                    checklist: [],
                                }
                            ],
                        }
                    ]
                }
            },
            initiativeImprovements: {
                [mockInitiatives[0].identifier]: {
                    action: ManagedEntityAction.UPDATE,
                    identifier: mockInitiatives[0].identifier,
                    title: null,
                    description: null,
                    tasks: [
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockTasks[0].identifier,
                            title: 'Updated Task Title from Initiative Context',
                            description: 'Updated task description from initiative improvement',
                            checklist: mockTasks[0].checklist,
                        },
                        {
                            action: ManagedEntityAction.CREATE,
                            title: 'New Task Created from Initiative',
                            description: 'This task was created as part of the initiative improvement',
                            initiative_identifier: mockInitiatives[0].identifier,
                            checklist: [],
                        }
                    ],
                }
            },
            loading: false,
            error: null,
            isEntityLocked: false,
        });
    }
}

export const DeleteInitiative: Story = {
    args: {
        initiativeId: mockInitiatives[0].id,
    },
    decorators: [
        (Story) => {
            // Set up all mocks for this story
            useActiveEntity.mockReturnValue({
                ...mockActiveEntityReturn,
                activeInitiativeId: mockInitiatives[0].id,
            });

            useUserPreferences.mockReturnValue(mockUserPreferencesReturn);

            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockTasks.slice(0, 5)
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [
                {
                    ...mockInitiatives[0],
                    tasks: mockTasks.slice(0, 5),
                }
            ]
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: {
                ...mockInitiativeAiJobResult,
                result_data: {
                    message: 'Marked initiative for deletion and created a replacement.',
                    managed_initiatives: [
                        {
                            action: ManagedEntityAction.DELETE,
                            identifier: mockInitiatives[0].identifier,
                        }
                    ]
                }
            },
            initiativeImprovements: {
                [mockInitiatives[0].identifier]: {
                    action: ManagedEntityAction.DELETE,
                    identifier: mockInitiatives[0].identifier,
                }
            },
            loading: false,
            error: null,
            isEntityLocked: false,
        });
    }
}

export const AiJobLoading: Story = {
    args: {
        initiativeId: mockInitiatives[0].id,
    },
    decorators: [
        (Story) => {
            // Set up all mocks for this story
            useActiveEntity.mockReturnValue({
                ...mockActiveEntityReturn,
                activeInitiativeId: mockInitiatives[0].id,
            });

            useUserPreferences.mockReturnValue(mockUserPreferencesReturn);

            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [
                {
                    ...mockInitiatives[0],
                    tasks: mockTasks.slice(0, 5),
                }
            ]
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: null,
            initiativeImprovements: {},
            loading: true,
            error: null,
            isEntityLocked: true,
        });
    }
}

export const WithError: Story = {
    args: {
        initiativeId: mockInitiatives[0].id,
    },
    decorators: [
        (Story) => {
            // Set up all mocks for this story
            useTasksContext.mockReturnValue({
                ...mockUseTasksContext,
                tasks: mockTasks.slice(0, 5)
            });

            useActiveEntity.mockReturnValue({
                ...mockActiveEntityReturn,
                activeInitiativeId: mockInitiatives[0].id,
            });

            useUserPreferences.mockReturnValue(mockUserPreferencesReturn);

            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        },
    ],
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockTasks.slice(0, 5)
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [
                {
                    ...mockInitiatives[0],
                    tasks: mockTasks.slice(0, 5),
                }
            ]
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: mockInitiativeAiJobResultError,
            initiativeImprovements: {},
            loading: false,
            error: 'Failed to process AI improvement for initiative',
            isEntityLocked: false,
        });
    }
}