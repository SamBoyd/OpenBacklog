// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { ManagedEntityAction, TaskStatus, WorkspaceDto } from '#types';
import { ListItem, LoadingListItem } from '#components/diffs/ListDiffListItem';
import type { UnifiedSuggestion, ResolutionState } from '#contexts/SuggestionsToBeResolvedContext';

const meta: Meta<typeof ListItem> = {
    title: 'Components/Diffs/Components/ListDiffListItem',
    component: ListItem,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof ListItem>;

// Mock workspace
const mockWorkspace: WorkspaceDto = {
    id: 'workspace-1',
    name: 'Development Workspace',
    description: null,
    icon: null
};

const defaultResolution: ResolutionState = {
    isResolved: false,
    isAccepted: false,
    resolvedValue: null,
};

// Mock initiative suggestion for CREATE
const mockCreateInitiativeSuggestion: UnifiedSuggestion = {
    path: 'initiative.I-NEW',
    type: 'entity',
    action: ManagedEntityAction.CREATE,
    originalValue: undefined,
    suggestedValue: {
        action: ManagedEntityAction.CREATE,
        title: 'Implement user notification system',
        description: 'Design and implement a comprehensive user notification system that supports email, in-app notifications, and push notifications. This system will handle user preferences, delivery scheduling, and notification history tracking.',
        type: 'FEATURE',
        workspace_identifier: 'workspace-1',
    },
    entityIdentifier: 'I-NEW',
};

// Mock task suggestion for CREATE
const mockCreateTaskSuggestion: UnifiedSuggestion = {
    path: 'initiative.I-NEW.tasks.new-task-1',
    type: 'entity',
    action: ManagedEntityAction.CREATE,
    originalValue: undefined,
    suggestedValue: {
        action: ManagedEntityAction.CREATE,
        title: 'Implement user authentication',
        description: 'Create a secure user authentication system with login, logout, and password reset functionality.',
        type: 'FEATURE',
        checklist: [
            { title: 'Design login form', is_complete: false },
            { title: 'Implement backend authentication logic', is_complete: false },
            { title: 'Add password reset functionality', is_complete: false },
            { title: 'Write unit tests', is_complete: false },
        ],
        order: 0,
    },
    entityIdentifier: 'I-NEW',
};

// Mock initiative suggestion for UPDATE
const mockUpdateInitiativeSuggestion: UnifiedSuggestion = {
    path: 'initiative.I-245',
    type: 'entity',
    action: ManagedEntityAction.UPDATE,
    originalValue: {
        id: 'initiative-1',
        identifier: 'I-245',
        user_id: 'user-1',
        title: 'Legacy system migration',
        description: 'Migrate the legacy system to the new architecture.',
        type: 'CHORE',
        status: TaskStatus.TO_DO,
        created_at: '2025-01-15T10:30:00.000000',
        updated_at: '2025-01-15T10:30:00.000001',
        tasks: [],
        has_pending_job: null,
        workspace: mockWorkspace,
    },
    suggestedValue: {
        action: ManagedEntityAction.UPDATE,
        identifier: 'I-245',
        title: 'Complete legacy system migration',
        description: 'Migrate the legacy system to the new architecture. This includes database migration, API updates, and frontend component updates. The project involves significant refactoring and testing.',
        type: 'CHORE',
    },
    entityIdentifier: 'I-245',
};

// Mock initiative suggestion for DELETE
const mockDeleteInitiativeSuggestion: UnifiedSuggestion = {
    path: 'initiative.I-246',
    type: 'entity',
    action: ManagedEntityAction.DELETE,
    originalValue: {
        id: 'initiative-2',
        identifier: 'I-246',
        user_id: 'user-1',
        title: 'Deprecated feature cleanup',
        description: 'Remove deprecated features that are no longer needed.',
        type: 'CHORE',
        status: TaskStatus.DONE,
        created_at: '2025-01-10T10:30:00.000000',
        updated_at: '2025-01-20T10:30:00.000001',
        tasks: [],
        has_pending_job: null,
        workspace: mockWorkspace,
    },
    suggestedValue: {
        action: ManagedEntityAction.DELETE,
        identifier: 'I-246',
    },
    entityIdentifier: 'I-246',
};

// Resolved suggestions
const resolvedAcceptedResolution: ResolutionState = {
    isResolved: true,
    isAccepted: true,
    resolvedValue: mockCreateInitiativeSuggestion.suggestedValue,
};

const resolvedRejectedResolution: ResolutionState = {
    isResolved: true,
    isAccepted: false,
    resolvedValue: null,
};

export const CreateInitiative: Story = {
    args: {
        suggestion: mockCreateInitiativeSuggestion,
        resolution: defaultResolution,
        accept: () => console.log('Create initiative accepted'),
        reject: () => console.log('Create initiative rejected'),
        rollback: () => console.log('Create initiative rolled back'),
        entityType: 'initiative',
    },
};

export const CreateTask: Story = {
    args: {
        suggestion: mockCreateTaskSuggestion,
        resolution: defaultResolution,
        accept: () => console.log('Create task accepted'),
        reject: () => console.log('Create task rejected'),
        rollback: () => console.log('Create task rolled back'),
        entityType: 'task',
    },
};

export const UpdateInitiative: Story = {
    args: {
        suggestion: mockUpdateInitiativeSuggestion,
        resolution: defaultResolution,
        accept: () => console.log('Update initiative accepted'),
        reject: () => console.log('Update initiative rejected'),
        rollback: () => console.log('Update initiative rolled back'),
        entityType: 'initiative',
    },
};

export const DeleteInitiative: Story = {
    args: {
        suggestion: mockDeleteInitiativeSuggestion,
        resolution: defaultResolution,
        accept: () => console.log('Delete initiative accepted'),
        reject: () => console.log('Delete initiative rejected'),
        rollback: () => console.log('Delete initiative rolled back'),
        entityType: 'initiative',
    },
};

export const ResolvedAccepted: Story = {
    args: {
        suggestion: mockCreateInitiativeSuggestion,
        resolution: resolvedAcceptedResolution,
        accept: () => console.log('Accepted'),
        reject: () => console.log('Rejected'),
        rollback: () => console.log('Rolled back'),
        entityType: 'initiative',
    },
};

export const ResolvedRejected: Story = {
    args: {
        suggestion: mockCreateInitiativeSuggestion,
        resolution: resolvedRejectedResolution,
        accept: () => console.log('Accepted'),
        reject: () => console.log('Rejected'),
        rollback: () => console.log('Rolled back'),
        entityType: 'initiative',
    },
};

export const Loading: Story = {
    render: () => <LoadingListItem />,
    parameters: {
        docs: {
            description: {
                story: 'Loading state for list items while suggestions are being generated.',
            },
        },
    },
};
