// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import { loremIpsum } from "lorem-ipsum";

import { AgentMode, AiImprovementJobStatus, CreateInitiativeModel, DeleteInitiativeModel, LENS, ManagedEntityAction, UpdateInitiativeModel } from '#types';

import { SuggestionsToBeResolvedContextProvider } from '#contexts/SuggestionsToBeResolvedContext';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';

import InitiativeListDiff from '#components/diffs/InitiativesListDiff';

import {
    mockAiImprovementsContextReturn,
    mockInitiatives,
    mockInitiativesContextReturn,
    mockTasks,
    mockUseTasksContext,
    mockWorkspacesReturn,
    mockInitiativeImprovements,
    mockTasksData,
} from '#stories/example_data';

const meta: Meta<typeof InitiativeListDiff> = {
    title: 'Components/Diffs/Components/InitiativeListDiff',
    component: InitiativeListDiff,
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
        });

        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset();
            useAiImprovementsContext.mockReset();
        }
    },
};

export default meta;
type Story = StoryObj<typeof InitiativeListDiff>;

export const Primary: Story = {
    args: {},
    decorators: [
        (Story) => {
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        }
    ]
};
