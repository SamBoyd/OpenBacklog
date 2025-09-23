// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { TaskDto, TaskStatus } from '#types';
import InitiativeTasksDiffView from '#components/diffs/InitiativeTasksDiffView';
import { SuggestionsToBeResolvedContextProvider } from '#contexts/SuggestionsToBeResolvedContext';
import { mockInitiatives, mockInitiativesContextReturn } from '#stories/example_data';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';

const meta: Meta<typeof InitiativeTasksDiffView> = {
    title: 'Components/Diffs/Components/InitiativeTasksDiffView',
    component: InitiativeTasksDiffView,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof InitiativeTasksDiffView>;

// Mock original tasks
const mockOriginalTasks: Partial<TaskDto>[] = [
    {
        id: 'task-1',
        identifier: 'T-1001',
        title: 'Setup authentication system',
        description: 'Implement basic user authentication functionality',
        status: TaskStatus.TO_DO,
        type: 'FEATURE',
    },
    {
        id: 'task-2',
        identifier: 'T-1002',
        title: 'Create user dashboard',
        description: 'Build a comprehensive user dashboard with widgets',
        status: TaskStatus.IN_PROGRESS,
        type: 'FEATURE',
    },
    {
        id: 'task-3',
        identifier: 'T-1003',
        title: 'Fix login bug',
        description: 'Resolve issue with login form validation',
        status: TaskStatus.DONE,
        type: 'BUG',
    },
];

// Mock changed tasks with modifications, additions, and removals
const mockChangedTasks: Partial<TaskDto>[] = [
    {
        id: 'task-1',
        identifier: 'T-1001',
        title: 'Setup enhanced authentication system',
        description: 'Implement comprehensive user authentication with multi-factor support',
        status: TaskStatus.IN_PROGRESS,
        type: 'FEATURE',
    },
    {
        id: 'task-2',
        identifier: 'T-1002',
        title: 'Create user dashboard',
        description: 'Build a comprehensive user dashboard with widgets',
        status: TaskStatus.IN_PROGRESS,
        type: 'FEATURE',
    },
    // task-3 removed (deleted)
    {
        id: 'task-4',
        identifier: 'T-1004',
        title: 'Implement API rate limiting',
        description: 'Add rate limiting to prevent API abuse',
        status: TaskStatus.TO_DO,
        type: 'FEATURE',
    },
    // New task without ID (will be treated as addition)
    {
        title: 'Setup monitoring dashboard',
        description: 'Create comprehensive monitoring and alerting system',
        status: TaskStatus.TO_DO,
        type: 'FEATURE',
    },
];

// Mock tasks with only additions
const mockOnlyAdditionTasks: Partial<TaskDto>[] = [
    {
        title: 'New feature development',
        description: 'Develop new feature from scratch',
        status: TaskStatus.TO_DO,
        type: 'FEATURE',
    },
    {
        title: 'Performance optimization',
        description: 'Optimize application performance',
        status: TaskStatus.TO_DO,
        type: 'CHORE',
    },
];

// Mock tasks with only removals
const mockOnlyRemovalOriginal: Partial<TaskDto>[] = [
    {
        id: 'task-remove-1',
        identifier: 'T-2001',
        title: 'Deprecated feature cleanup',
        description: 'Remove old deprecated features',
        status: TaskStatus.DONE,
        type: 'CHORE',
    },
    {
        id: 'task-remove-2',
        identifier: 'T-2002',
        title: 'Legacy code removal',
        description: 'Clean up legacy codebase',
        status: TaskStatus.TO_DO,
        type: 'CHORE',
    },
];

// Mock complex scenario with various changes
const mockComplexOriginalTasks: Partial<TaskDto>[] = [
    {
        id: 'task-complex-1',
        identifier: 'T-3001',
        title: 'User registration',
        description: 'Basic user registration flow',
        status: TaskStatus.TO_DO,
        type: 'FEATURE',
    },
    {
        id: 'task-complex-2',
        identifier: 'T-3002',
        title: 'Email notifications',
        description: 'Send email notifications to users',
        status: TaskStatus.IN_PROGRESS,
        type: 'FEATURE',
    },
    {
        id: 'task-complex-3',
        identifier: 'T-3003',
        title: 'Data backup',
        description: 'Automated data backup system',
        status: TaskStatus.DONE,
        type: 'CHORE',
    },
    {
        id: 'task-complex-4',
        identifier: 'T-3004',
        title: 'Security audit',
        description: 'Perform security audit',
        status: TaskStatus.TO_DO,
        type: 'CHORE',
    },
];

const mockComplexChangedTasks: Partial<TaskDto>[] = [
    // Modified task
    {
        id: 'task-complex-1',
        identifier: 'T-3001',
        title: 'Advanced user registration',
        description: 'Enhanced user registration with social login options',
        status: TaskStatus.IN_PROGRESS,
        type: 'FEATURE',
    },
    // Unchanged task
    {
        id: 'task-complex-2',
        identifier: 'T-3002',
        title: 'Email notifications',
        description: 'Send email notifications to users',
        status: TaskStatus.IN_PROGRESS,
        type: 'FEATURE',
    },
    // task-complex-3 removed (deleted)
    // task-complex-4 stays the same (unchanged)
    {
        id: 'task-complex-4',
        identifier: 'T-3004',
        title: 'Security audit',
        description: 'Perform security audit',
        status: TaskStatus.TO_DO,
        type: 'CHORE',
    },
    // New tasks added
    {
        id: 'task-complex-5',
        identifier: 'T-3005',
        title: 'API documentation',
        description: 'Create comprehensive API documentation',
        status: TaskStatus.TO_DO,
        type: 'FEATURE',
    },
    // New task without ID
    {
        title: 'Mobile app development',
        description: 'Develop mobile application',
        status: TaskStatus.TO_DO,
        type: 'FEATURE',
    },
];

export const Primary: Story = {
    args: {
        initiative: mockInitiatives[0],
    },
    decorators: [
        (Story) => {
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        }
    ]

};

export const NoChanges: Story = {
    args: {
        initiative: mockInitiatives[0],
    },
    decorators: [
        (Story) => {
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        }
    ]
};

export const OnlyAdditions: Story = {
    args: {
        initiative: mockInitiatives[0],
    },
    decorators: [
        (Story) => {
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        }
    ]
};

export const OnlyRemovals: Story = {
    args: {
        initiative: mockInitiatives[0],
    },
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

export const EmptyToEmpty: Story = {
    args: {
        initiative: mockInitiatives[0],
    },
    decorators: [
        (Story) => {
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        }
    ]
};

export const ComplexScenario: Story = {
    args: {
        initiative: mockInitiatives[0],
    },
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

export const ResolvedAccepted: Story = {
    args: {
initiative: mockInitiatives[0],
    },
    decorators: [
        (Story) => {
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        }
    ]
};

export const ResolvedRejected: Story = {
    args: {
        initiative: mockInitiatives[0],
    },
    decorators: [
        (Story) => {
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        }
    ]
};

export const ResolvedEmpty: Story = {
    args: {
        initiative: mockInitiatives[0],
    },
    decorators: [
        (Story) => {
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            
            return (
                <SuggestionsToBeResolvedContextProvider>
                    <Story />
                </SuggestionsToBeResolvedContextProvider>
            );
        }
    ]
};