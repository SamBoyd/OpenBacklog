import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { useTasksContext } from '#contexts/TasksContext.mock';
import ViewTask from '#components/ViewTask';

import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';

import {
    mockUseTasksContext,
    mockWorkspace,
    mockTasks,
    mockReloadTask,
    mockDeleteTask,
    mockUpdateTask,
    mockFieldDefinitionsReturn,
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
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [mockTasks[1]],
        })

        return () => {
            useTasksContext.mockReset()
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
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: [],
            shouldShowSkeleton: true
        });

        return () => {
            useTasksContext.mockReset()
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
    },
    beforeEach: () => {
        useTasksContext.mockReturnValue({
            ...mockUseTasksContext,
            tasks: []
        });

        return () => {
            useTasksContext.mockReset()
        }
    }
};