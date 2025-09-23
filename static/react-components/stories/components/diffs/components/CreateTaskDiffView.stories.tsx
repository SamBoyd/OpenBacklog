// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { CreateTaskModel, ManagedEntityAction } from '#types';
import CreateTaskDiffView from '#components/diffs/CreateTaskDiffView';

const meta: Meta<typeof CreateTaskDiffView> = {
    title: 'Components/Diffs/Components/CreateTaskDiffView',
    component: CreateTaskDiffView,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof CreateTaskDiffView>;

// Mock task data for creation
const mockCreateTaskData: CreateTaskModel = {
    action: ManagedEntityAction.CREATE,
    title: 'Implement user authentication',
    description: 'Create a secure user authentication system with login, logout, and password reset functionality. This should include proper error handling and user feedback.',
    checklist: [
        {
            title: 'Design login form',
            is_complete: false,
        },
        {
            title: 'Implement backend authentication logic',
            is_complete: false,
        },
        {
            title: 'Add password reset functionality',
            is_complete: false,
        },
        {
            title: 'Write unit tests',
            is_complete: false,
        },
    ],
};

const mockSimpleTask: CreateTaskModel = {
    action: ManagedEntityAction.CREATE,
    title: 'Fix button styling issue',
    description: 'The submit button appears misaligned on the login form.',
    checklist: [],
};

const mockComplexTask: CreateTaskModel = {
    action: ManagedEntityAction.CREATE,
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
    checklist: [
        {
            title: 'Research visualization libraries',
            is_complete: true,
        },
        {
            title: 'Design dashboard layout wireframes',
            is_complete: false,
        },
        {
            title: 'Implement basic chart components',
            is_complete: false,
        },
        {
            title: 'Add real-time data connections',
            is_complete: false,
        },
        {
            title: 'Implement export functionality',
            is_complete: false,
        },
        {
            title: 'Optimize performance',
            is_complete: false,
        },
        {
            title: 'Add responsive design',
            is_complete: false,
        },
        {
            title: 'Write comprehensive tests',
            is_complete: false,
        },
    ],
};

const mockEmptyDescriptionTask: CreateTaskModel = {
    action: ManagedEntityAction.CREATE,
    title: 'Task with no description',
    description: '',
    checklist: [
        {
            title: 'Only checklist item',
            is_complete: false,
        },
    ],
};

const mockNoChecklistTask: CreateTaskModel = {
    action: ManagedEntityAction.CREATE,
    title: 'Simple task without checklist',
    description: 'This task has a description but no checklist items.',
    checklist: [],
};

export const Primary: Story = {
    args: {
        taskData: mockCreateTaskData,
        onAccept: () => console.log('Create task accepted'),
        onReject: () => console.log('Create task rejected'),
        onRollback: () => console.log('Create task rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const SimpleTask: Story = {
    args: {
        taskData: mockSimpleTask,
        onAccept: () => console.log('Simple task accepted'),
        onReject: () => console.log('Simple task rejected'),
        onRollback: () => console.log('Simple task rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const ComplexTask: Story = {
    args: {
        taskData: mockComplexTask,
        onAccept: () => console.log('Complex task accepted'),
        onReject: () => console.log('Complex task rejected'),
        onRollback: () => console.log('Complex task rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const EmptyDescription: Story = {
    args: {
        taskData: mockEmptyDescriptionTask,
        onAccept: () => console.log('Empty description task accepted'),
        onReject: () => console.log('Empty description task rejected'),
        onRollback: () => console.log('Empty description task rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const NoChecklist: Story = {
    args: {
        taskData: mockNoChecklistTask,
        onAccept: () => console.log('No checklist task accepted'),
        onReject: () => console.log('No checklist task rejected'),
        onRollback: () => console.log('No checklist task rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const ResolvedAccepted: Story = {
    args: {
        taskData: mockCreateTaskData,
        onAccept: () => console.log('Resolved task accepted'),
        onReject: () => console.log('Resolved task rejected'),
        onRollback: () => console.log('Resolved task rolled back'),
        isResolved: true,
        accepted: true,
    },
};

export const ResolvedRejected: Story = {
    args: {
        taskData: mockCreateTaskData,
        onAccept: () => console.log('Resolved task accepted'),
        onReject: () => console.log('Resolved task rejected'),
        onRollback: () => console.log('Resolved task rolled back'),
        isResolved: true,
        accepted: false,
    },
};