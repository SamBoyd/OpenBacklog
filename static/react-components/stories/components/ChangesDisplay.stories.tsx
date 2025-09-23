// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { AgentMode, AiImprovementJobStatus, CreateInitiativeModel, DeleteInitiativeModel, LENS, ManagedEntityAction, UpdateInitiativeModel } from '#types';

import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';

import ChangesDisplay from '#components/diffs/ChangesDisplay';

import {
    mockAiImprovementsContextReturn,
    mockInitiativeImprovements,
    mockInitiatives,
    mockInitiativesContextReturn,
    mockTasks,
    mockUseTasksContext,
    mockWorkspacesReturn,
} from '#stories/example_data';

const meta: Meta<typeof ChangesDisplay> = {
    component: ChangesDisplay,
    async beforeEach() {
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            updateTask: (task) => {
                console.log('updateTask called with:', task);
                return Promise.resolve(mockTasks[0]);
            },
            deleteTask: (id) => {
                console.log('inline deleteTask called with id:', id);
                return Promise.resolve();
            }
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            loading: false,
            isEntityLocked: false,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: {
                id: '123',
                thread_id: 'thread1',
                lens: LENS.INITIATIVE,
                status: AiImprovementJobStatus.COMPLETED,
                mode: AgentMode.EDIT,
                input_data: mockInitiatives,
                result_data: {
                    message: 'Some random summary of changes',
                    managed_initiatives: [
                        {
                            action: ManagedEntityAction.CREATE,
                            title: 'This is a test initiative',
                            description: 'Updated initiative description',
                            order: 0,
                            workspace_identifier: '123'
                        } as CreateInitiativeModel,
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockInitiatives[0].identifier,
                            title: 'Updated initiative title',
                            description: 'Updated initiative description',
                            order: 1,
                        } as UpdateInitiativeModel,
                        {
                            action: ManagedEntityAction.CREATE,
                            title: 'New initiative title',
                            description: 'New initiative description',
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
        });

        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset();
            useAiImprovementsContext.mockReset();
        }
    },
};

export default meta;
type Story = StoryObj<typeof ChangesDisplay>;

export const Primary: Story = {
    args: {},
};


export const NoChanges: Story = {
    args: {
    },
    async beforeEach() {
        useWorkspaces.mockReturnValue(mockWorkspacesReturn);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);

        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            updateTask: (task) => {
                console.log('updateTask called with:', task);
                return Promise.resolve(mockTasks[0]);
            },
            deleteTask: (id) => {
                console.log('inline deleteTask called with id:', id);
                return Promise.resolve();
            }
        });

        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            loading: false,
            isEntityLocked: false,
        });

        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset();
            useAiImprovementsContext.mockReset();
        }
    }
};