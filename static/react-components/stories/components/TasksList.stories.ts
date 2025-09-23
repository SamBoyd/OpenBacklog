import type { Meta, StoryObj } from '@storybook/react';

import TasksList from '../../components/TasksList';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { mockUseTasksContext } from '#stories/example_data';
import { TaskStatus } from '#types';

const meta: Meta<typeof TasksList> = {
    component: TasksList,
    async beforeEach() {
        useTasksContext.mockReturnValue(mockUseTasksContext);
        
        return () => {
            useTasksContext.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof TasksList>;

export const Primary: Story = {
    args: {
        initiativeId: 'dd7e819d-7355-4146-bac4-7045dfa3f25d',
        filterToStatus: [TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.DONE],
    },
};

export const NoTasks: Story = {
    args: {
        initiativeId: 'dd7e819d-7355-4146-bac4-7045dfa3f25d',
    },

    async beforeEach() {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [],
        });


        return () => {
            useTasksContext.mockReset();
        };
    },
};

export const shouldShowSkeleton: Story = {
    args: {
        initiativeId: 'dd7e819d-7355-4146-bac4-7045dfa3f25d',
    },

    async beforeEach() {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            shouldShowSkeleton: true
        });

        return () => {
            useTasksContext.mockReset();
        };
    },
};

export const Error: Story = {
    args: {
        initiativeId: 'dd7e819d-7355-4146-bac4-7045dfa3f25d',
    },

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

export const FilteredToInitiative: Story = {
    args: {
        initiativeId: 'dd7e819d-7355-4146-bac4-7045dfa3f25d',
    },

    async beforeEach() {
        useTasksContext.mockReturnValue(mockUseTasksContext);

        return () => {
            useTasksContext.mockReset();
        };
    },
};
