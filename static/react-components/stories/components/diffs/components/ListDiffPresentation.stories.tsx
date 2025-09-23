// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { InitiativeDto, ManagedEntityAction, ManagedInitiativeModel, ManagedTaskModel, TaskDto, TaskStatus, UpdateInitiativeModel, WorkspaceDto } from '#types';
import ListDiffPresentation from '#components/diffs/ListDiffPresentation';
import { UnifiedSuggestion, ResolutionMap, ResolutionState } from '#contexts/SuggestionsToBeResolvedContext';

const meta: Meta<typeof ListDiffPresentation> = {
    title: 'Components/Diffs/Components/ListDiffPresentation',
    component: ListDiffPresentation,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof ListDiffPresentation>;

// Mock workspace
const mockWorkspace: WorkspaceDto = {
    id: 'workspace-1',
    name: 'Development Workspace',
    description: null,
    icon: null
};

// Mock unified suggestions
const mockInitiativeSuggestions: UnifiedSuggestion[] = [
    {
        path: 'initiative.I-NEW-1',
        type: 'entity',
        action: ManagedEntityAction.CREATE,
        suggestedValue: {
            action: ManagedEntityAction.CREATE,
            title: 'Implement user notification system',
            description: 'Design and implement a comprehensive user notification system that supports email, in-app notifications, and push notifications.',
            type: 'FEATURE',
            workspace_identifier: 'workspace-1',
        },
        entityIdentifier: 'I-NEW-1',
    },
    {
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
            description: 'Migrate the legacy system to the new architecture. This includes database migration, API updates, and frontend component updates.',
            type: 'CHORE',
        },
        entityIdentifier: 'I-245',
    },
    {
        path: 'initiative.I-245.title',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Legacy system migration',
        suggestedValue: 'Complete legacy system migration',
        entityIdentifier: 'I-245',
        fieldName: 'title',
    },
    {
        path: 'initiative.I-245.description',
        type: 'field',
        action: ManagedEntityAction.UPDATE,
        originalValue: 'Migrate the legacy system to the new architecture.',
        suggestedValue: 'Migrate the legacy system to the new architecture. This includes database migration, API updates, and frontend component updates.',
        entityIdentifier: 'I-245',
        fieldName: 'description',
    },
    {
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
    },
];

// Mock task suggestions with embedded tasks
const mockTaskSuggestions: UnifiedSuggestion[] = [
    {
        path: 'initiative.I-NEW-TASKS',
        type: 'entity',
        action: ManagedEntityAction.CREATE,
        suggestedValue: {
            action: ManagedEntityAction.CREATE,
            title: 'Implement component notification system',
            description: 'Design and implement a comprehensive component notification system that supports email, in-app notifications, and push notifications.',
            type: 'FEATURE',
            workspace_identifier: 'workspace-1',
            tasks: [
                {
                    action: ManagedEntityAction.CREATE,
                    title: 'Create notification component',
                    description: 'Build the core notification component',
                    checklist: [
                        { title: 'First checklist item', is_complete: false },
                        { title: 'Second checklist item', is_complete: true },
                    ],
                }
            ],
        },
        entityIdentifier: 'I-NEW-TASKS',
    },
    {
        path: 'initiative.I-NEW-TASKS.tasks.new-task-0',
        type: 'entity',
        action: ManagedEntityAction.CREATE,
        suggestedValue: {
            action: ManagedEntityAction.CREATE,
            title: 'Create notification component',
            description: 'Build the core notification component',
            checklist: [
                { title: 'First checklist item', is_complete: false },
                { title: 'Second checklist item', is_complete: true },
            ],
        },
        entityIdentifier: 'I-NEW-TASKS',
    },
    {
        path: 'initiative.I-NEW-TASKS.tasks.new-task-0.title',
        type: 'field',
        action: ManagedEntityAction.CREATE,
        suggestedValue: 'Create notification component',
        entityIdentifier: 'I-NEW-TASKS',
        fieldName: 'title',
    },
    {
        path: 'initiative.I-NEW-TASKS.tasks.new-task-0.description',
        type: 'field',
        action: ManagedEntityAction.CREATE,
        suggestedValue: 'Build the core notification component',
        entityIdentifier: 'I-NEW-TASKS',
        fieldName: 'description',
    },
];

// Mock resolution state helpers
const createEmptyResolutions = (suggestions: UnifiedSuggestion[]): ResolutionMap => {
    const resolutions: ResolutionMap = {};
    suggestions.forEach(suggestion => {
        resolutions[suggestion.path] = {
            isResolved: false,
            isAccepted: false,
            resolvedValue: undefined,
        };
    });
    return resolutions;
};

const createResolvedResolutions = (suggestions: UnifiedSuggestion[]): ResolutionMap => {
    const resolutions: ResolutionMap = {};
    suggestions.forEach((suggestion, index) => {
        resolutions[suggestion.path] = {
            isResolved: true,
            isAccepted: index % 2 === 0, // Alternate between accepted/rejected
            resolvedValue: index % 2 === 0 ? suggestion.suggestedValue : suggestion.originalValue,
        };
    });
    return resolutions;
};

const createMixedResolutions = (suggestions: UnifiedSuggestion[]): ResolutionMap => {
    const resolutions: ResolutionMap = {};
    suggestions.forEach((suggestion, index) => {
        if (index === 0) {
            // First one accepted
            resolutions[suggestion.path] = {
                isResolved: true,
                isAccepted: true,
                resolvedValue: suggestion.suggestedValue,
            };
        } else if (index === 1) {
            // Second one rejected
            resolutions[suggestion.path] = {
                isResolved: true,
                isAccepted: false,
                resolvedValue: suggestion.originalValue,
            };
        } else {
            // Rest pending
            resolutions[suggestion.path] = {
                isResolved: false,
                isAccepted: false,
                resolvedValue: undefined,
            };
        }
    });
    return resolutions;
};

// Mock handlers
const mockHandlers = {
    resolve: (path: string, accepted: boolean, value?: any) =>
        console.log('Resolve:', path, accepted, value),
    rollback: (path: string) =>
        console.log('Rollback:', path),
    acceptAll: (pathPrefix?: string) =>
        console.log('Accept all:', pathPrefix),
    rejectAll: (pathPrefix?: string) =>
        console.log('Reject all:', pathPrefix),
    rollbackAll: (pathPrefix?: string) =>
        console.log('Rollback all:', pathPrefix),
    getResolutionState: (path: string) => ({
        isResolved: false,
        isAccepted: false,
        resolvedValue: undefined,
    }) as ResolutionState,
};

export const Primary: Story = {
    args: {
        entityType: 'initiative',
        error: null,
        suggestions: mockInitiativeSuggestions,
        resolutions: createEmptyResolutions(mockInitiativeSuggestions),
        allResolved: false,
        ...mockHandlers,
    },
};

export const ErrorState: Story = {
    args: {
        entityType: 'initiative',
        error: 'Failed to load suggestions. Please try again.',
        suggestions: [],
        resolutions: {},
        allResolved: false,
        ...mockHandlers,
    },
};

export const AllResolved: Story = {
    args: {
        entityType: 'initiative',
        error: null,
        suggestions: mockInitiativeSuggestions,
        resolutions: createResolvedResolutions(mockInitiativeSuggestions),
        allResolved: true,
        ...mockHandlers,
    },
};

export const MixedResolutions: Story = {
    args: {
        entityType: 'initiative',
        error: null,
        suggestions: mockInitiativeSuggestions,
        resolutions: createMixedResolutions(mockInitiativeSuggestions),
        allResolved: false,
        ...mockHandlers,
    },
};

export const TaskSuggestions: Story = {
    args: {
        entityType: 'task',
        error: null,
        suggestions: mockTaskSuggestions,
        resolutions: createEmptyResolutions(mockTaskSuggestions),
        allResolved: false,
        ...mockHandlers,
    },
};
