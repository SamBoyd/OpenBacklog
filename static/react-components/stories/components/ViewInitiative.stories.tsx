import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';
import { useParams } from '#hooks/useParams.mock';
import { useActiveEntity } from '#hooks/useActiveEntity.mock';
import { mockUseGithubReposReturn, useGithubRepos } from '#hooks/useGithubRepos.mock';


import {
    mockDeleteJob,
    mockRequestImprovement,
    mockResetError,
    mockUpdateTask,
    mockWorkspace,
    mockInitiatives,
    mockTasks,
    mockUpdateInitiatives,
    mockReloadInitiatives,
    mockDeleteInitiative_Initiative,
    mockDeleteTask,
    mockReloadTask,
    mockInitiativesContextReturn,
    mockUseTasksContext,
    mockAiImprovementsContextReturn,
    mockUpdateTaskVoid,
    mockTasksData,
    mockCreateInitiativeDiff,
    mockInitiativeAiJobResult,
    mockInitiativeAiJobResultError,
    mockAllFieldDefinitions,
    mockActiveEntityReturn,
    mockInitiativeImprovements
} from '../example_data';

import {
    AiImprovementJobStatus,
    InitiativeDto,
    InitiativeLLMResponse,
    LENS,
    ManagedEntityAction,
    TaskDto,
    EntityType,
    FieldType,
    ManagedTaskModel,
    AgentMode
} from '#types';

import ViewInitiative from '#components/ViewInitiative';
import { userEvent, within, expect } from '@storybook/test';
import { initiativeTypeFieldDefinition } from '#constants/coreFieldDefinitions';
import { initiativeStatusFieldDefinition } from '#constants/coreFieldDefinitions';
import { taskStatusFieldDefinition } from '#constants/coreFieldDefinitions';
import { taskTypeFieldDefinition } from '#constants/coreFieldDefinitions';
import { delay, HttpResponse } from 'msw';
import { http } from 'msw';
import { OrderedEntity } from '#hooks/useOrderings';


// Create a list of realistic field definitions
const mockFieldDefinitions = [
    { ...initiativeStatusFieldDefinition, id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a9', workspace_id: 'workspace-1' },
    { ...initiativeTypeFieldDefinition, id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a2', workspace_id: 'workspace-1' },
    { ...taskStatusFieldDefinition, id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a3', workspace_id: 'workspace-1' },
    { ...taskTypeFieldDefinition, id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a4', workspace_id: 'workspace-1' },
    {
        id: "04e4c955-b341-4070-bbf3-13cb3c4650f2",
        workspace_id: "workspace-1",
        entity_type: EntityType.INITIATIVE,
        key: "priority",
        name: "Priority",
        field_type: FieldType.SELECT,
        is_core: false,
        column_name: null,
        config: {
            options: [
                "Low",
                "Medium",
                "High",
            ]
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "eee09a42-fa2a-4567-bd9b-e7e06286ef52",
        workspace_id: "workspace-1",
        entity_type: EntityType.INITIATIVE,
        key: "deadline",
        name: "Deadline",
        field_type: FieldType.DATE,
        is_core: false,
        column_name: null,
        config: {
            format: "YYYY-MM-DD"
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "55d48178-68d2-4172-9b0e-81b51eddc2d4",
        workspace_id: "workspace-1",
        entity_type: EntityType.INITIATIVE,
        key: "is_important",
        name: "Important",
        field_type: FieldType.CHECKBOX,
        is_core: false,
        column_name: null,
        config: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "55d48178-68d2-4172-9b0e-81b51eddc2203",
        workspace_id: "workspace-1",
        entity_type: EntityType.INITIATIVE,
        key: "unset_text_field",
        name: "Unset Text Field",
        field_type: FieldType.TEXT,
        is_core: false,
        column_name: null,
        config: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    },
    {
        id: "55d48178-68d2-4172-9b0e-81b51eddc2204",
        workspace_id: "workspace-1",
        entity_type: EntityType.INITIATIVE,
        key: "unset_number_field",
        name: "Unset Number Field",
        field_type: FieldType.NUMBER,
        is_core: false,
        column_name: null,
        config: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    }
];

const mockCreateFieldDefinition = () => {
    console.log('mockCreateFieldDefinition');
    return Promise.resolve(mockFieldDefinitions[0]);
}
const mockUpdateFieldDefinition = () => {
    console.log('mockUpdateFieldDefinition');
    return Promise.resolve(mockFieldDefinitions[0]);
}
const mockDeleteFieldDefinition = () => {
    console.log('mockDeleteFieldDefinition');
    return Promise.resolve();
}
const mockInvalidateQuery = () => {
    console.log('mockInvalidateQuery');
}

const mockFieldDefinitionsReturn = {
    fieldDefinitions: mockFieldDefinitions,
    loading: false,
    error: null,
    createFieldDefinition: mockCreateFieldDefinition,
    updateFieldDefinition: mockUpdateFieldDefinition,
    deleteFieldDefinition: mockDeleteFieldDefinition,
    invalidateQuery: mockInvalidateQuery
};
const meta: Meta<typeof ViewInitiative> = {
    title: 'Components/ViewInitiative',
    component: ViewInitiative,
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

type Story = StoryObj<typeof ViewInitiative>;

// 'cd441dc5-1bf8-423f-9f88-f47e1c747579'
export const Default: Story = {
    args: {
        workspace: mockWorkspace,
        initiative: mockInitiatives[0],
        tasks: mockTasks,
        updateInitiatives: mockUpdateInitiatives,
        reloadInitiatives: mockReloadInitiatives,
        deleteInitiative: mockDeleteInitiative_Initiative,
    },
    parameters: {
        msw: {
            handlers: [
                http.post('/api/text-completion', async () => {
                    const sampleText = "this is a sample of the kind of text that will be returned from the text completion api";
                    const words = sampleText.split(" "); // Split into words to simulate chunks

                    const stream = new ReadableStream({
                        async start(controller) {
                            const encoder = new TextEncoder();
                            for (let i = 0; i < words.length; i++) {
                                const word = words[i];
                                // Send word with a trailing space, unless it's the last word.
                                const contentToSend = word + (i < words.length - 1 ? " " : "");
                                const message = `data: ${contentToSend}\n\n`;
                                controller.enqueue(encoder.encode(message));
                                await delay(150); // Simulate a small delay between chunks
                            }
                            controller.close();
                        },
                    });

                    return new HttpResponse(stream, {
                        headers: {
                            'Content-Type': 'text/event-stream',
                            'Cache-Control': 'no-cache', // Recommended for SSE
                        },
                    });
                })
            ]
        },
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [{
                ...mockInitiatives[0],
                tasks: [],
                properties: {
                    "04e4c955-b341-4070-bbf3-13cb3c4650f2": "p1",
                    "eee09a42-fa2a-4567-bd9b-e7e06286ef52": "2024-01-01",
                    "55d48178-68d2-4172-9b0e-81b51eddc2d4": true
                }
            }]
        });

        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockInitiatives[0].tasks as OrderedEntity<TaskDto>[],
        })

        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};

export const WithTasks: Story = {


    args: {
        workspace: mockWorkspace,
        initiative: mockInitiatives[4], // This initiative has tasks
        tasks: mockTasks,
        updateInitiatives: mockUpdateInitiatives,
        reloadInitiatives: mockReloadInitiatives,
        deleteInitiative: mockDeleteInitiative_Initiative,
    },

    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [{ ...mockInitiatives[0], tasks: mockTasks }]
        })

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockInitiatives[0].tasks as OrderedEntity<TaskDto>[],
        })

        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
            useActiveEntity.mockReset()
        }
    }
};

export const Loading: Story = {
    args: {
        workspace: mockWorkspace,
        initiative: mockInitiatives[0],
        tasks: mockTasks,
        updateInitiatives: mockUpdateInitiatives,
        reloadInitiatives: mockReloadInitiatives,
        deleteInitiative: mockDeleteInitiative_Initiative,
    },
    parameters: {
        msw: {
            handlers: [
                http.post('/api/text-completion', async () => {
                    const sampleText = "this is a sample of the kind of text that will be returned from the text completion api";
                    const words = sampleText.split(" "); // Split into words to simulate chunks

                    const stream = new ReadableStream({
                        async start(controller) {
                            const encoder = new TextEncoder();
                            for (let i = 0; i < words.length; i++) {
                                const word = words[i];
                                // Send word with a trailing space, unless it's the last word.
                                const contentToSend = word + (i < words.length - 1 ? " " : "");
                                const message = `data: ${contentToSend}\n\n`;
                                controller.enqueue(encoder.encode(message));
                                await delay(150); // Simulate a small delay between chunks
                            }
                            controller.close();
                        },
                    });

                    return new HttpResponse(stream, {
                        headers: {
                            'Content-Type': 'text/event-stream',
                            'Cache-Control': 'no-cache', // Recommended for SSE
                        },
                    });
                })
            ]
        },
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [],
            shouldShowSkeleton: true,
        });

        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: []
        })

        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};

export const WithDiff: Story = {
    args: {
        workspace: mockWorkspace,
        task: mockTasks[0],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTaskVoid,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,
        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn
        });

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockInitiatives[0].tasks as OrderedEntity<TaskDto>[],
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: mockInitiativeAiJobResult,
        });

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });


        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};


export const WithDiffLoading: Story = {

    args: {
        workspace: mockWorkspace,
        task: mockTasks[0],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTaskVoid,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,
        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn
        });

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockInitiatives[0].tasks as OrderedEntity<TaskDto>[],
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            jobResult: null,
            loading: true,
            isEntityLocked: true,

        });

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};


export const WithTaskDiff: Story = {

    args: {
        workspace: mockWorkspace,
        task: mockTasks[0],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTaskVoid,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,
        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [mockInitiatives[0]],
        })

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockInitiatives[0].tasks as OrderedEntity<TaskDto>[],
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: {
                id: '123',
                lens: LENS.INITIATIVE,
                thread_id: 'thread1',
                status: AiImprovementJobStatus.COMPLETED,
                mode: AgentMode.EDIT,
                input_data: [mockInitiatives[0]],
                result_data: {
                    message: 'Some random summary of changes',
                    managed_initiatives: [
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockInitiatives[0].identifier,
                            type: mockInitiatives[0].type,
                            status: mockInitiatives[0].status,
                            title: 'Updated initiative title',
                            description: 'Updated initiative description',
                            tasks: mockTasks.slice(0, 3).map((task, index) => ({
                                action: ManagedEntityAction.UPDATE,
                                identifier: task.identifier,
                                title: `Updated task title ${index}`,
                                description: `Updated task description ${index}`,
                                checklist: task.checklist,
                            }) as ManagedTaskModel)
                        }
                    ]
                },
                messages: [{ role: 'user', content: 'Let me explain the changes I made to the task - I\'ve updated the title and description with some placeholder text', suggested_changes: [] }],
                error_message: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                user_id: mockTasks[0].user_id
            },
        })

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};

export const WithCreateInitiativeDiff: Story = {

    args: {
        workspace: mockWorkspace,
        task: mockTasks[0],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTaskVoid,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [mockInitiatives[0]]
        })

        useTasksContext.mockReturnValue(mockUseTasksContext);

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: {
                ...mockInitiativeAiJobResult,
                result_data: {
                    ...mockInitiativeAiJobResult.result_data,
                    managed_initiatives: [
                        {
                            action: ManagedEntityAction.UPDATE,
                            ...mockInitiatives[0],
                            title: 'Updated initiative title',
                            description: 'Updated initiative description',
                            tasks: mockTasksData
                        },
                        mockCreateInitiativeDiff
                    ]
                } as InitiativeLLMResponse
            },
        })

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useAiImprovementsContext.mockReset()
            useTasksContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};


export const WithDiffError: Story = {

    args: {
        workspace: mockWorkspace,
        task: mockTasks[0],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTaskVoid,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,
        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn
        });

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: []
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: mockInitiativeAiJobResultError,
        });

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};


export const WithDeleteInitiativeDiff: Story = {

    args: {
        workspace: mockWorkspace,
        task: mockTasks[0],
        updateTask: mockUpdateTask,
        updateTaskVoid: mockUpdateTaskVoid,
        reloadTask: mockReloadTask,
        deleteTask: mockDeleteTask,

        requestImprovement: mockRequestImprovement,
        deleteJob: mockDeleteJob,
        resetError: mockResetError
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [mockInitiatives[0]]
        })

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: mockInitiatives[0].tasks as OrderedEntity<TaskDto>[]
        })

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: {
                ...mockInitiativeAiJobResult,
                result_data: {
                    ...mockInitiativeAiJobResult.result_data,
                    managed_initiatives: [
                        {
                            action: ManagedEntityAction.DELETE,
                            identifier: mockInitiatives[0].identifier,
                        },
                        {
                            action: ManagedEntityAction.CREATE,
                            title: 'Created initiative title',
                            description: 'Created initiative description',
                            tasks: mockTasksData
                        },
                    ]
                } as InitiativeLLMResponse
            },
        })

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useAiImprovementsContext.mockReset()
            useTasksContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};

export const WithAllFieldTypes: Story = {

    args: {
        workspace: mockWorkspace,
        initiative: mockInitiatives[0],
        tasks: mockTasks,
        updateInitiatives: mockUpdateInitiatives,
        reloadInitiatives: mockReloadInitiatives,
        deleteInitiative: mockDeleteInitiative_Initiative,
    },
    beforeEach: () => {
        useParams.mockReturnValue({
            initiativeId: mockInitiatives[0].id
        });

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [{
                ...mockInitiatives[0],
                tasks: [],
                properties: {
                    "04e4c955-b341-4070-bbf3-13cb3c4650f2": "p1",
                    "eee09a42-fa2a-4567-bd9b-e7e06286ef52": "2024-01-01",
                    "55d48178-68d2-4172-9b0e-81b51eddc2d4": true
                }
            }]
        });

        useFieldDefinitions.mockReturnValue({
            ...mockFieldDefinitionsReturn,
            fieldDefinitions: mockAllFieldDefinitions
        });

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: []
        });

        useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
            useActiveEntity.mockReset()
        }
    },
};