// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import TasksKanbanBoard from '../../components/TasksKanbanBoard';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { mockUseTasksContext } from '#stories/example_data';
import { TaskStatus } from '#types';

const meta: Meta<typeof TasksKanbanBoard> = {
    component: TasksKanbanBoard,
    async beforeEach() {
        useTasksContext.mockReturnValue(mockUseTasksContext);

        return () => {
            useTasksContext.mockReset();
        };
    },
};

const mockReloadCounter = 0;
const mockOnUpdate = () => {
    console.log('[TasksKanbanBoard] onUpdate called');
};

const componentArgs = {
    reloadCounter: mockReloadCounter,
    onUpdate: mockOnUpdate,
    filterToInitiativeId: mockUseTasksContext.tasks[0].initiative_id,
    filterToStatus: [TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]
};

export default meta;
type Story = StoryObj<typeof TasksKanbanBoard>;

export const Primary: Story = {
    args: componentArgs
};

export const shouldShowSkeleton: Story = {
    args: componentArgs,

    async beforeEach() {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [],
            shouldShowSkeleton: true
        });

        return () => {
            useTasksContext.mockReset();
        };
    },
};

export const Error: Story = {
    args: componentArgs,

    async beforeEach() {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [],
            error: 'Aaaahhhh!!'
        });

        return () => {
            useTasksContext.mockReset();
        };
    },
};
