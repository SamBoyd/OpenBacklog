import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { useTasksContext } from '#contexts/TasksContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import ViewTask from '#components/ViewTask';

import { AgentMode, AiImprovementJobStatus, LENS, ManagedEntityAction, TaskDto, TaskStatus } from '#types';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';

import {
    mockDeleteJob,
    mockRequestImprovement,
    mockResetError,
    mockUseTasksContext,
    mockWorkspace,
    mockTasks,
    mockReloadTask,
    mockDeleteTask,
    mockAiImprovementsContextReturn,
    mockUpdateTask,
    mockTasksAiJobResultPending,
    mockFieldDefinitionsReturn,
    mockInitiativeImprovements
} from '../example_data';
import { within } from '@storybook/test';
import { mockUseGithubReposReturn, useGithubRepos } from '#hooks/useGithubRepos.mock';

const meta: Meta<typeof ViewTask> = {
    title: 'Components/ViewTask',
    component: ViewTask,
    parameters: {
        layout: 'fullscreen',
    },
    decorators: [
        (Story, context) => {
            useGithubRepos.mockReturnValue(mockUseGithubReposReturn);
            return <Story />
        },
        (Story) => (
            <div style={{ padding: '20px' }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;

type Story = StoryObj<typeof ViewTask>;

export const EmptyChecklistWithOverlay: Story = {
    args: {},
    decorators: [
        (Story) => {
            useTasksContext.mockReturnValue({
                ...mockUseTasksContext,
                tasks: [{ ...mockTasks[0], checklist: [] }],
            });
            useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

            return <Story />
        }],
    parameters: {
        docs: {
            description: {
                story: 'Shows the new Claude Code integration overlay that appears when a task has no checklist items. Displays educational content about automatic checklist management.'
            }
        }
    }
};

export const EmptyChecklistManualEdit: Story = {
    args: {},
    decorators: [
        (Story) => {
            useTasksContext.mockReturnValue({
                ...mockUseTasksContext,
                tasks: [{ ...mockTasks[0], checklist: [] }]
            });
            useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

            return <Story />
        }
    ],
    parameters: {
        docs: {
            description: {
                story: 'Shows the task view with empty checklist. Click "Edit Manually" in the overlay to bypass it and see the manual input mode.'
            }
        }
    },
    play: async ({ canvasElement, step }) => {
        // This story demonstrates the interactive overlay behavior
        // Users can click "Edit Manually" to bypass the overlay
        await step('Initial state shows overlay', () => {
            // The overlay should be visible initially
            const canvas = within(canvasElement);
            expect(canvas.getByText('Edit Manually')).toBeInTheDocument();
            canvas.getByText('Edit Manually').click();
        });
    }
};

export const WithChecklist: Story = {
    args: {
        workspace: mockWorkspace,
        tasks: [mockTasks[1]], // This task has checklist items
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [mockTasks[1]],
        })

        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        return () => {
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
        }
    }
};

export const PendingJob: Story = {
    args: {
        workspace: mockWorkspace,
        task: { ...mockTasks[0], has_pending_job: true },
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,
        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [{ ...mockTasks[0], has_pending_job: true }]
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,

            jobResult: mockTasksAiJobResultPending,
            loading: false,
            error: null,
            isEntityLocked: true,
        });

        return () => {
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
        }
    }
};

export const Loading: Story = {
    args: {
        workspace: mockWorkspace,
        task: null,
        loading: true,
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [],
            shouldShowSkeleton: true
        });

        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        return () => {
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
        }
    }
};

export const NotFound404: Story = {
    args: {
        workspace: mockWorkspace,
        task: null,
        error: 'Error loading task',
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,
        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: []
        });

        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        return () => {
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
        }
    }
};

export const WithDiff: Story = {
    args: {
        workspace: mockWorkspace,
        tasks: [mockTasks[0]],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [{ ...mockTasks[0], identifier: 'TM-001' }],
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            taskImprovements: {
                "TM-001": {
                    "title": "Refine Task Description and Checklist",
                    "action": ManagedEntityAction.UPDATE,
                    "checklist": [
                        {
                            "title": "Refine Task Description and Checklist",
                            "is_complete": false,
                            "order": 0,
                        },
                        {
                            "title": "Refine Task Description and Checklist",
                            "is_complete": false,
                            "order": 1,
                        }
                    ],
                    "identifier": "TM-001",
                    "description": "Rewrite, rephrase, and restructure the task description to enhance readability, actionability, and relevance to the codebase. Additionally, improve the checklist to ensure each item focuses on a single change that requires updating/adding at least one unit test.",
                }
            },
            jobResult: {
                "id": "51ec34b8-b9cd-4a15-82aa-2e1f936ac2d2",
                "lens": LENS.TASK,
                "thread_id": 'thread1',
                "status": AiImprovementJobStatus.COMPLETED,
                "mode": AgentMode.EDIT,
                "input_data": [{
                    "id": "d101110c-5a56-4600-be37-04325644a8d6",
                    "type": null,
                    "title": "Create a login page",
                    "status": "TO_DO",
                    "user_id": "b59a6ef7-c88c-47f7-b30e-9df1f999624f",
                    "created_at": "2025-04-13T13:52:19.846",
                    "identifier": "TM-001",
                    "updated_at": "2025-04-13T14:05:24.236",
                    "description": "I'd like the user to be able to log in with a username and password",
                    "initiative_id": "6d06edbc-1fc5-4b65-9d3a-ee54c10026bf",
                    "checklist": [],
                    "has_pending_job": true,
                    "workspace": mockWorkspace
                }],
                "result_data": {
                    "managed_tasks": [
                        {
                            "title": "Refine Task Description and Checklist",
                            "action": ManagedEntityAction.UPDATE,
                            "checklist": [
                                {
                                    "title": "Refine Task Description and Checklist",
                                    "is_complete": false,
                                    "order": 0,
                                },
                                {
                                    "title": "Refine Task Description and Checklist",
                                    "is_complete": false,
                                    "order": 1,
                                }
                            ],
                            "identifier": "TM-001",
                            "description": "Rewrite, rephrase, and restructure the task description to enhance readability, actionability, and relevance to the codebase. Additionally, improve the checklist to ensure each item focuses on a single change that requires updating/adding at least one unit test.",
                        }
                    ],
                    "message": "Rewritten task description for improved readability, actionability, and alignment with the codebase."
                },
                "error_message": null,
                "created_at": "2025-04-13T14:05:26.685648",
                "updated_at": "2025-04-13T14:05:34.935483",
                "user_id": "b59a6ef7-c88c-47f7-b30e-9df1f999624f",
                "messages": [
                    { role: 'user', content: 'Rewritten task description for improved readability, actionability, and alignment with the codebase.', suggested_changes: [] }
                ]
            }
        })

        return () => {
            useTasksContext.mockReset()
        }
    },
};

export const WithCreateNewTaskDiff: Story = {
    args: {
        workspace: mockWorkspace,
        tasks: [mockTasks[0]],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [{ ...mockTasks[0] }],
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult:
            {
                "id": "34b0dd01-c344-4448-9a35-784e6f27efcd",
                "lens": LENS.TASK,
                "thread_id": 'thread1',
                "status": AiImprovementJobStatus.COMPLETED,
                "mode": AgentMode.EDIT,
                "input_data": [
                    {
                        "id": mockTasks[0].id,
                        "type": null,
                        "title": "Implement Google Analytics tracking",
                        "status": TaskStatus.TO_DO,
                        "user_id": mockTasks[0].user_id,
                        "checklist": [],
                        "created_at": "2025-04-20T11:07:25.743483",
                        "identifier": mockTasks[0].identifier,
                        "updated_at": "2025-04-20T11:07:25.743483",
                        "description": "Implement tracking code to monitor user interactions using Google Analytics.",
                        "initiative_id": "27071b67-d167-42bb-aa85-ed44c4136ab8",
                        "has_pending_job": false,
                        "workspace": mockWorkspace
                    }
                ],
                "result_data": {
                    "managed_tasks": [
                        {
                            "title": "Implement Google Analytics tracking",
                            "action": ManagedEntityAction.UPDATE,
                            "checklist": [],
                            "identifier": mockTasks[0].identifier,
                            "description": "Implement tracking code to monitor user interactions using Google Analytics."
                        },
                        {
                            "title": "Implement Hotjar heatmaps",
                            "action": ManagedEntityAction.CREATE,
                            "checklist": [],
                            "description": "Implement Hotjar to visualize user behavior through heatmaps."
                        }
                    ],
                    "message": "Refined the task to provide clear guidance on implementing Google Analytics tracking for user interactions."
                },
                "error_message": "",
                "created_at": "2025-04-20T11:42:52.666463",
                "updated_at": "2025-04-20T11:43:07.650827",
                "user_id": mockTasks[0].user_id,
                "messages": [{ role: 'user', content: 'What steps should be take to achieve this task?', suggested_changes: [] }]
            }
        })

        return () => {
            useTasksContext.mockReset()
        }
    },
};

export const WithNoChangesTaskDiff: Story = {
    args: {
        workspace: mockWorkspace,
        tasks: [mockTasks[0]],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [{ ...mockTasks[0] }],
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult:
            {
                "id": "34b0dd01-c344-4448-9a35-784e6f27efcd",
                "lens": LENS.TASK,
                "thread_id": 'thread1',
                "status": AiImprovementJobStatus.COMPLETED,
                "mode": AgentMode.EDIT,
                "input_data": [
                    {
                        "id": mockTasks[0].id,
                        "type": null,
                        "title": mockTasks[0].title,
                        "status": mockTasks[0].status,
                        "user_id": mockTasks[0].user_id,
                        "checklist": mockTasks[0].checklist,
                        "created_at": "2025-04-20T11:07:25.743483",
                        "identifier": mockTasks[0].identifier,
                        "updated_at": mockTasks[0].updated_at,
                        "description": mockTasks[0].description,
                        "initiative_id": mockTasks[0].initiative_id,
                        "has_pending_job": mockTasks[0].has_pending_job,
                        "workspace": mockWorkspace
                    }
                ],
                "result_data": {
                    "managed_tasks": [
                        {
                            "title": mockTasks[0].title,
                            "action": ManagedEntityAction.UPDATE,
                            "checklist": mockTasks[0].checklist,
                            "identifier": mockTasks[0].identifier,
                            "description": mockTasks[0].description
                        }
                    ],
                    "message": "No changes to the task."
                },
                "error_message": "",
                "created_at": "2025-04-20T11:42:52.666463",
                "updated_at": "2025-04-20T11:43:07.650827",
                "user_id": mockTasks[0].user_id,
                "messages": [{ role: 'user', content: 'What steps should be take to achieve this task?', suggested_changes: [] }]
            }
        })

        return () => {
            useTasksContext.mockReset()
        }
    },
};


export const WithDiffError: Story = {
    args: {
        workspace: mockWorkspace,
        tasks: [mockTasks[0]],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [{ ...mockTasks[0], identifier: 'TM-001' }],
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: {
                "id": "51ec34b8-b9cd-4a15-82aa-2e1f936ac2d2",
                "lens": LENS.TASK,
                "thread_id": 'thread1',
                "status": AiImprovementJobStatus.FAILED,
                "mode": AgentMode.EDIT,
                "input_data": [mockTasks[0]],
                "result_data": null,
                "error_message": "This is an error message",
                "created_at": "2025-04-13T14:05:26.685648",
                "updated_at": "2025-04-13T14:05:34.935483",
                "user_id": "b59a6ef7-c88c-47f7-b30e-9df1f999624f",
                "messages": [{ role: 'user', content: 'What steps should be take to achieve this task?', suggested_changes: [] }]
            },
        })

        return () => {
            useTasksContext.mockReset()
        }
    },
};

export const WithDeleteTaskDiff: Story = {
    args: {
        workspace: mockWorkspace,
        tasks: [mockTasks[0]],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTask,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [{ ...mockTasks[0] }],
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            taskImprovements: {
                [mockTasks[0].identifier]: {
                    "action": ManagedEntityAction.DELETE,
                    "identifier": mockTasks[0].identifier,
                }
            },
            jobResult:
            {
                "id": "34b0dd01-c344-4448-9a35-784e6f27efcd",
                "lens": LENS.TASK,
                "thread_id": 'thread1',
                "status": AiImprovementJobStatus.COMPLETED,
                "mode": AgentMode.EDIT,
                "input_data": [mockTasks[0]],
                "result_data": {
                    "managed_tasks": [
                        {
                            "action": ManagedEntityAction.DELETE,
                            "identifier": mockTasks[0].identifier,
                        },
                        {
                            "title": "Implement Hotjar heatmaps",
                            "action": ManagedEntityAction.CREATE,
                            "checklist": [],
                            "description": "Implement Hotjar to visualize user behavior through heatmaps."
                        }
                    ],
                    "message": "Refined the task to provide clear guidance on implementing Google Analytics tracking for user interactions."
                },
                "error_message": "",
                "created_at": "2025-04-20T11:42:52.666463",
                "updated_at": "2025-04-20T11:43:07.650827",
                "user_id": mockTasks[0].user_id,
                "messages": [{ role: 'user', content: "I've replaced the task with a new one.", suggested_changes: [] }]
            }
        })

        return () => {
            useTasksContext.mockReset()
        }
    },
};