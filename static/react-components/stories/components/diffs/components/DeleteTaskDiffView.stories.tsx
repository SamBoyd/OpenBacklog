// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { TaskDto, TaskStatus } from '#types';
import { DeleteTaskDiffView } from '#components/diffs/DeleteTaskDiffView';
import { mockWorkspace } from '#stories/example_data';

const meta: Meta<typeof DeleteTaskDiffView> = {
    title: 'Components/Diffs/Components/DeleteTaskDiffView',
    component: DeleteTaskDiffView,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof DeleteTaskDiffView>;

// Mock task data for deletion
const mockDeleteTaskData: TaskDto = {
    id: 'task-1',
    identifier: 'T-1001',
    user_id: 'user-1',
    initiative_id: 'initiative-1',
    title: 'Implement user authentication',
    description: 'Create a secure user authentication system with login, logout, and password reset functionality. This should include proper error handling and user feedback.',
    status: TaskStatus.TO_DO,
    type: 'FEATURE',
    created_at: '2025-01-15T10:30:00.000000',
    updated_at: '2025-01-15T10:30:00.000001',
    checklist: [
        {
            id: 'checklist-1',
            title: 'Design login form',
            order: 0,
            task_id: 'task-1',
            is_complete: false,
        },
        {
            id: 'checklist-2',
            title: 'Implement backend authentication logic',
            order: 1,
            task_id: 'task-1',
            is_complete: false,
        },
    ],
    has_pending_job: null,
    workspace: mockWorkspace,
};

const mockSimpleTask: TaskDto = {
    id: 'task-2',
    identifier: 'T-1002',
    user_id: 'user-1',
    initiative_id: 'initiative-1',
    title: 'Fix button styling issue',
    description: 'The submit button appears misaligned on the login form.',
    status: TaskStatus.IN_PROGRESS,
    type: 'BUG',
    created_at: '2025-01-16T10:30:00.000000',
    updated_at: '2025-01-16T10:30:00.000001',
    checklist: [],
    has_pending_job: null,
    workspace: mockWorkspace,
};

const mockComplexTask: TaskDto = {
    id: 'task-3',
    identifier: 'T-1003',
    user_id: 'user-1',
    initiative_id: 'initiative-1',
    title: 'Implement comprehensive data visualization dashboard',
    description: `Create a sophisticated dashboard for data visualization with the following requirements:

## Core Features
- Interactive charts and graphs
- Real-time data updates
- Customizable layouts
- Export functionality

## Technical Requirements
- Use D3.js for visualizations
- Implement WebSocket connections for real-time updates
- Support for multiple data formats (CSV, JSON, API)
- Mobile-responsive design

## Performance Considerations
- Lazy loading for large datasets
- Efficient data caching
- Optimized rendering for smooth interactions

This is a complex task that will require careful planning and execution.`,
    status: TaskStatus.DONE,
    type: 'FEATURE',
    created_at: '2025-01-10T10:30:00.000000',
    updated_at: '2025-01-20T10:30:00.000001',
    checklist: [
        {
            id: 'checklist-3',
            title: 'Research visualization libraries',
            order: 0,
            task_id: 'task-3',
            is_complete: true,
        },
        {
            id: 'checklist-4',
            title: 'Design dashboard layout wireframes',
            order: 1,
            task_id: 'task-3',
            is_complete: false,
        },
    ],
    has_pending_job: null,
    workspace: mockWorkspace,
};

const mockEmptyDescriptionTask: TaskDto = {
    id: 'task-4',
    identifier: 'T-1004',
    user_id: 'user-1',
    initiative_id: 'initiative-1',
    title: 'Task with no description',
    description: '',
    status: TaskStatus.TO_DO,
    type: 'CHORE',
    created_at: '2025-01-17T10:30:00.000000',
    updated_at: '2025-01-17T10:30:00.000001',
    checklist: [],
    has_pending_job: null,
    workspace: mockWorkspace,
};

export const Primary: Story = {
    args: {
        taskData: mockDeleteTaskData,
        onAccept: () => console.log('Delete task accepted'),
        onReject: () => console.log('Delete task rejected'),
        onRollback: () => console.log('Delete task rolled back'),
        isResolved: false,
        accepted: null,
    },
};

export const SimpleTask: Story = {
    args: {
        taskData: mockSimpleTask,
        onAccept: () => console.log('Delete simple task accepted'),
        onReject: () => console.log('Delete simple task rejected'),
        onRollback: () => console.log('Delete simple task rolled back'),
        isResolved: false,
        accepted: null,
    },
};

export const ComplexTask: Story = {
    args: {
        taskData: mockComplexTask,
        onAccept: () => console.log('Delete complex task accepted'),
        onReject: () => console.log('Delete complex task rejected'),
        onRollback: () => console.log('Delete complex task rolled back'),
        isResolved: false,
        accepted: null,
    },
};

export const EmptyDescription: Story = {
    args: {
        taskData: mockEmptyDescriptionTask,
        onAccept: () => console.log('Delete empty description task accepted'),
        onReject: () => console.log('Delete empty description task rejected'),
        onRollback: () => console.log('Delete empty description task rolled back'),
        isResolved: false,
        accepted: null,
    },
};

export const ResolvedAccepted: Story = {
    args: {
        taskData: mockDeleteTaskData,
        onAccept: () => console.log('Resolved delete accepted'),
        onReject: () => console.log('Resolved delete rejected'),
        onRollback: () => console.log('Resolved delete rolled back'),
        isResolved: true,
        accepted: true,
    },
};

export const ResolvedRejected: Story = {
    args: {
        taskData: mockDeleteTaskData,
        onAccept: () => console.log('Resolved delete accepted'),
        onReject: () => console.log('Resolved delete rejected'),
        onRollback: () => console.log('Resolved delete rolled back'),
        isResolved: true,
        accepted: false,
    },
};