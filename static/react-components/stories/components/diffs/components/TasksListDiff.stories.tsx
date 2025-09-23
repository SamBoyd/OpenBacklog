// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { AgentMode, AiImprovementJobStatus, CreateTaskModel, DeleteTaskModel, LENS, ManagedEntityAction, UpdateTaskModel } from '#types';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';

import TasksListDiff from '#components/diffs/TasksListDiff';

import { mockAiImprovementsContextReturn, mockInitiativeImprovements, mockInitiativeReturn, mockTasks, mockTasksData, mockUseTasksContext } from '#stories/example_data';

const meta: Meta<typeof TasksListDiff> = {
    title: 'Components/Diffs/Components/TasksListDiff',
    component: TasksListDiff,
    async beforeEach() {
        useTasksContext.mockReturnValue(mockUseTasksContext);

        // We need a custom configuration for the AI improvements hook
        // specific to the task diff use case
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            isEntityLocked: false,
            initiativeImprovements: mockInitiativeImprovements,
            jobResult: {
                id: '123',
                lens: LENS.TASK,
                status: AiImprovementJobStatus.COMPLETED,
                mode: AgentMode.EDIT,
                input_data: mockTasks,
                result_data: {
                    message: 'Some random summary of changes',
                    managed_tasks: [
                        {
                            action: ManagedEntityAction.CREATE,
                            title: 'This is a test initiative',
                            description: 'Updated initiative description',
                            order: 0,
                            checklist: []
                        } as CreateTaskModel,
                        {
                            action: ManagedEntityAction.UPDATE,
                            identifier: mockTasks[0].identifier,
                            title: 'Updated initiative title',
                            description: 'Updated initiative description',
                            order: 1,
                            checklist: []
                        } as UpdateTaskModel,
                        {
                            action: ManagedEntityAction.CREATE,
                            title: 'New initiative title',
                            description: 'New initiative description',
                            task: mockTasksData,
                            order: 2,
                            checklist: []
                        } as CreateTaskModel,
                        {
                            action: ManagedEntityAction.DELETE,
                            identifier: mockTasks[1].identifier,
                            checklist: []
                        } as DeleteTaskModel
                    ]
                },
                thread_id: 'thread1',
                messages: [{ role: 'user', content: 'Let me explain the changes I made to the task - I\'ve updated the title and description with some placeholder text', suggested_changes: [] }],
                error_message: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                user_id: mockTasks[0].user_id
            }
        })

        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset()
            useAiImprovementsContext.mockReset()
        }
    },
};

export default meta;
type Story = StoryObj<typeof TasksListDiff>;

export const Primary: Story = {
    args: {},
};

export const Loading: Story = {
    args: {},
    async beforeEach() {
        useTasksContext.mockReturnValue(mockUseTasksContext);

        // We need a custom configuration for the AI improvements hook
        // specific to the task diff use case
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            isEntityLocked: true,
            jobResult: null,
        });

        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset();
            useAiImprovementsContext.mockReset();
        };
    },
};
