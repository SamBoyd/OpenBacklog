// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import CompactCreateTask from '#components/CompactCreateTask';

import { mockFieldDefinitionsReturn, mockInitiativesContextReturn, mockPostTask, mockUseTasksContext } from '#stories/example_data';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';
import { postTask } from '#api/tasks.mock';

const meta: Meta<typeof CompactCreateTask> = {
    component: CompactCreateTask,
    async beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset();
            useFieldDefinitions.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof CompactCreateTask>;

export const Primary: Story = {
    args: {
        focus: true,
        startExpanded: true,
    },
};

export const ApiError: Story = {
    args: {},
    async beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);

        return () => {
            useInitiativesContext.mockReset();
        };
    },
};
