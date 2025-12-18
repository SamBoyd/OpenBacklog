import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';
import { useParams } from '#hooks/useParams.mock';
import { useActiveEntity } from '#hooks/useActiveEntity.mock';
import { mockUseGithubReposReturn, useGithubRepos } from '#hooks/useGithubRepos.mock';
import { useStrategicInitiative } from '#hooks/useStrategicInitiative.mock';
import { useStrategicPillars } from '#hooks/useStrategicPillars.mock';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';

import {
    mockUpdateTask,
    mockInitiatives,
    mockTasks,
    mockUpdateInitiatives,
    mockReloadInitiatives,
    mockDeleteInitiative_Initiative,
    mockDeleteTask,
    mockReloadTask,
    mockInitiativesContextReturn,
    mockUseTasksContext,
    mockUpdateTaskVoid,
    mockAllFieldDefinitions,
    mockActiveEntityReturn,
    mockWorkspacesReturn,
    mockWorkspace
} from '../example_data';

import {
    InitiativeDto,
    TaskDto,
    EntityType,
    FieldType,
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

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        useWorkspaces.mockReturnValue(mockWorkspacesReturn);

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useActiveEntity.mockReset()
            useWorkspaces.mockReset()
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

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        useWorkspaces.mockReturnValue(mockWorkspacesReturn);

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useActiveEntity.mockReset()
            useWorkspaces.mockReset()
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

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        useWorkspaces.mockReturnValue(mockWorkspacesReturn);

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useActiveEntity.mockReset()
            useWorkspaces.mockReset()
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

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        useWorkspaces.mockReturnValue(mockWorkspacesReturn);

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useActiveEntity.mockReset()
            useWorkspaces.mockReset()
        }
    },
};

export const WithStrategicContext: Story = {
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
                    "04e4c955-b341-4070-bbf3-13cb3c4650f2": "High",
                    "eee09a42-fa2a-4567-bd9b-e7e06286ef52": "2024-06-01",
                    "55d48178-68d2-4172-9b0e-81b51eddc2d4": true
                }
            }]
        });

        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: []
        });

        useActiveEntity.mockReturnValue({ ...mockActiveEntityReturn, activeInitiativeId: mockInitiatives[0].id });

        useStrategicInitiative.mockReturnValue({
            strategicInitiative: {
                id: 'strategic-init-1',
                initiative_id: mockInitiatives[0].id,
                workspace_id: 'workspace-1',
                pillar_id: 'pillar-1',
                theme_id: 'theme-1',
                description: 'Solo developers need assistance to help them stay productive and organized when working alone.',
                narrative_intent: 'This initiative directly enables our vision of being the best task management tool for solo developers.',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
            isLoading: false,
            error: null,
            createStrategicInitiative: () => {},
            isCreating: false,
            createError: null,
            updateStrategicInitiative: () => {},
            isUpdating: false,
            updateError: null,
        });

        useStrategicPillars.mockReturnValue({
            pillars: [
                {
                    id: 'pillar-1',
                    identifier: 'P-001',
                    workspace_id: 'workspace-1',
                    name: 'Developer Productivity',
                    description: 'Make productivity a natural and essential part of the development workflow for solo developers.',
                    display_order: 0,
                    outcome_ids: ['outcome-1'],
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                },
                {
                    id: 'pillar-2',
                    identifier: 'P-002',
                    workspace_id: 'workspace-1',
                    name: 'Developer Experience',
                    description: 'Create a delightful, intuitive interface that developers love to use.',
                    display_order: 1,
                    outcome_ids: [],
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                }
            ],
            isLoading: false,
            error: null,
            createPillar: () => {},
            isCreating: false,
            createError: null,
            updatePillar: () => {},
            isUpdating: false,
            updateError: null,
            deletePillar: () => {},
            isDeleting: false,
            deleteError: null,
            reorderPillars: () => {},
            isReordering: false,
            reorderError: null,
        });

        useRoadmapThemes.mockReturnValue({
            themes: [
                {
                    id: 'theme-1',
                    identifier: 'T-001',
                    workspace_id: 'workspace-1',
                    name: 'First Week Magic',
                    description: 'New users struggle to see value in the first week and often abandon the product before experiencing its key benefits.',
                    outcome_ids: ['outcome-1'],
                    hero_ids: [],
                    villain_ids: [],
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                },
                {
                    id: 'theme-2',
                    identifier: 'T-002',
                    workspace_id: 'workspace-1',
                    name: 'Weekly Habit',
                    description: 'Users who try features once often forget to use them again.',
                    outcome_ids: [],
                    hero_ids: [],
                    villain_ids: [],
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                }
            ],
            isLoading: false,
            error: null,
            createTheme: () => {},
            isCreating: false,
            createError: null,
            updateTheme: () => {},
            isUpdating: false,
            updateError: null,
            deleteTheme: () => {},
            isDeleting: false,
            deleteError: null,
            reorderThemes: () => {},
            isReordering: false,
            reorderError: null,
        });

        useWorkspaces.mockReturnValue(mockWorkspacesReturn);

        return () => {
            useInitiativesContext.mockReset()
            useTasksContext.mockReset()
            useActiveEntity.mockReset()
            useStrategicInitiative.mockReset()
            useStrategicPillars.mockReset()
            useRoadmapThemes.mockReset()
            useWorkspaces.mockReset()
        }
    },
};
