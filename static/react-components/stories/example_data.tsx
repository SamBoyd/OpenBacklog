import { LexoRank } from 'lexorank';

import {
    TaskDto,
    InitiativeDto,
    TaskStatus,
    WorkspaceDto,
    LENS,
    AiImprovementJobResult,
    ManagedEntityAction,
    AiImprovementJobStatus,
    ManagedTaskModel,
    CreateInitiativeModel,
    ChatMessage,
    AiJobChatMessage,
    ContextDocumentDto,
    FieldDefinitionDto,
    FieldType,
    EntityType,
    GroupType,
    GroupDto,
    InitiativeStatus,
    ManagedInitiativeModel,
    DeleteInitiativeModel,
    UpdateInitiativeModel,
    AgentMode,
    ContextType,
    OrderingDto,
} from '#types';

import { taskTypeFieldDefinition, taskStatusFieldDefinition, initiativeTypeFieldDefinition, initiativeStatusFieldDefinition } from '#constants/coreFieldDefinitions';
import { InitiativesContextType } from '#contexts/InitiativesContext';
import { TasksContextType } from '#contexts/TasksContext';
import { useAiImprovementsContextReturn } from '#contexts/AiImprovementsContext';

import { UseContextDocumentReturn } from '#hooks/useContextDocument';
import { UseInitiativeGroupsReturn } from '#hooks/useInitiativeGroups';
import { OrderedEntity } from '#hooks/useOrderings';
import { UserPreferencesContextType } from '#hooks/useUserPreferences';
import { UseActiveEntityReturn } from '#hooks/useActiveEntity';
import { useEntityFromUrlReturn } from '#hooks/useEntityFromUrl';
import { BillingUsageData, UseBillingUsageReturn } from '#hooks/useBillingUsage';
import { useAiChatReturn } from '#hooks/useAiChat';

import { UserAccountStatus } from '#constants/userAccountStatus';
import { UseSuggestionsToBeResolvedReturn } from '#contexts/SuggestionsToBeResolvedContext';
import { loremIpsum } from 'lorem-ipsum';

function sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

export enum Theme {
    LIGHT = 'light',
    DARK = 'dark',
}

export interface UserPreferences {
    theme: Theme;
    filterTasksToInitiative: string | null;
    selectedGroupIds: string[];
    selectedInitiativeStatuses: InitiativeStatus[];
    selectedTaskStatuses: TaskStatus[];
    isRewriteEnabled: boolean;
    initiativesShowListView: boolean;
}


export interface UseUserPreferencesReturn {
    preferences: UserPreferences;
    toggleTheme: () => void;
    updateFilterTasksToInitiative: (initiativeId: string | null) => void;
}


// --- Common Mock Data ---

export const mockToggleTheme = () => {
    console.log('mockToggleTheme');
};

export const mockUpdateFilterTasksToInitiative = () => {
    console.log('mockUpdateFilterTasksToInitiative');
};

export const mockUpdateSelectedGroups = () => {
    console.log('mockUpdateSelectedGroups');
};

export const mockUpdateSelectedInitiativeStatuses = () => {
    console.log('mockUpdateSelectedInitiativeStatuses');
};

export const mockUpdateSelectedTaskStatuses = () => {
    console.log('mockUpdateSelectedTaskStatuses');
};

export const mockUpdateCompactnessLevel = () => {
    console.log('mockUpdateCompactnessLevel');
};

export const mockUpdateIsRewriteEnabled = () => {
    console.log('mockUpdateIsRewriteEnabled');
};

export const mockUpdateInitiativesShowListView = () => {
    console.log('mockUpdateInitiativesShowListView');
};

export const mockUpdateTasksShowListView = () => {
    console.log('mockUpdateTasksShowListView');
};

export const mockUpdateViewInitiativeShowListView = () => {
    console.log('mockUpdateViewInitiativeShowListView');
};

export const mockUpdateChatLayoutMode = () => {
    console.log('mockUpdateChatLayoutMode');
};

export const mockUserPreferencesReturn: UserPreferencesContextType = {
    preferences: {
        theme: Theme.DARK,
        filterTasksToInitiative: null,
        selectedGroupIds: ['all-pseudo-group'],
        selectedInitiativeStatuses: [InitiativeStatus.TO_DO, InitiativeStatus.IN_PROGRESS],
        selectedTaskStatuses: [TaskStatus.TO_DO, TaskStatus.IN_PROGRESS],
        compactnessLevel: 'normal',
        isRewriteEnabled: true,
        initiativesShowListView: false,
        tasksShowListView: false,
        viewInitiativeShowListView: false,
        chatLayoutMode: 'normal'
    },
    toggleTheme: mockToggleTheme,
    updateFilterTasksToInitiative: mockUpdateFilterTasksToInitiative,
    updateSelectedGroups: mockUpdateSelectedGroups,
    updateSelectedInitiativeStatuses: mockUpdateSelectedInitiativeStatuses,
    updateSelectedTaskStatuses: mockUpdateSelectedTaskStatuses,
    updateCompactnessLevel: mockUpdateCompactnessLevel,
    updateIsRewriteEnabled: mockUpdateIsRewriteEnabled,
    updateInitiativesShowListView: mockUpdateInitiativesShowListView,
    updateTasksShowListView: mockUpdateTasksShowListView,
    updateViewInitiativeShowListView: mockUpdateViewInitiativeShowListView,
    updateChatLayoutMode: mockUpdateChatLayoutMode,
};

export const mockWorkspace: WorkspaceDto = {
    id: '1',
    name: 'Engineering',
    description: null,
    icon: null
};

export const mockWorkspaces: WorkspaceDto[] = [
    {
        id: 'Test Workspace',
        name: 'Frontend Team',
        description: 'Frontend development workspace',
        icon: null,
    },
    {
        id: '1', name: 'Engineering',
        icon: null,
        description: null
    },
    {
        id: '2', name: 'Product',
        icon: null,
        description: null
    },
    {
        id: '3', name: 'DevOps',
        icon: null,
        description: null
    }
];

export const mockTasks__unordered: TaskDto[] = [
    {
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747000',
        identifier: 'T-1024',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747579',
        title: 'Implement user authentication flow so that it is compliant with GDPR and CCPA',
        description: 'Create a secure authentication flow including login, registration, and password reset functionality. Use JWT for session management.',
        status: TaskStatus.TO_DO,

        created_at: '2025-01-09T17:50:48.340652',
        updated_at: '2025-01-09T17:50:48.340653',




        type: 'CODING',
        checklist: [
            {
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747581',
                task_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
                title: 'Create login page UI components',
                is_complete: false,
                order: 0,
            },
            {
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747582',
                task_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
                title: 'Implement JWT token generation',
                is_complete: false,
                order: 1,
            },
            {
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747583',
                task_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
                title: 'Add email verification process',
                is_complete: false,
                order: 2,
            },
            {
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584',
                task_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
                title: 'Test authentication flows',
                is_complete: false,
                order: 3,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
        identifier: 'T-1032',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747579',
        title: 'Fix responsive layout issues in dashboard',
        description: 'The dashboard layout breaks on mobile devices and tablets. Implement responsive design fixes to ensure proper rendering across all device sizes.',

        status: TaskStatus.IN_PROGRESS,


        created_at: '2025-01-15T10:30:00.000000',
        updated_at: '2025-01-15T10:30:00.000001',



        type: 'CODING',
        checklist: [
            {
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747581',
                task_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
                title: 'Fix chart component overflow',
                is_complete: true,
                order: 0,
            },
            {
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747582',
                task_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
                title: 'Update media queries for tablet view',
                is_complete: true,
                order: 1,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747581',
        identifier: 'T-1033',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747579',
        title: 'Optimize API endpoint performance',
        description: 'Several API endpoints have slow response times impacting user experience. Profile and optimize database queries and API logic to improve performance.',

        status: TaskStatus.DONE,


        created_at: '2025-01-20T14:00:00.000000',
        updated_at: '2025-01-20T14:00:00.000001',




        type: 'CODING',
        checklist: [
            {
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747581',
                task_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
                title: 'Identify bottlenecks using performance tools',
                is_complete: false,
                order: 0,
            },
            {
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747582',
                task_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
                title: 'Optimize database queries',
                is_complete: false,
                order: 1,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747583',
        identifier: 'T-1087',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747583',
        title: 'Implement JWT auto-renewal mechanism in the authentication service so that it is compliant with GDPR and CCPA',
        description: 'The JWT used for API authorization needs to automatically renew before expiration to prevent user session interruptions.',

        status: TaskStatus.TO_DO,


        created_at: '2025-01-09T17:50:48.340652',
        updated_at: '2025-01-09T17:50:48.340653',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584',
        identifier: 'T-1093',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747583',
        title: 'Design JWT refresh token service',
        description: 'Create a service to handle JWT token refreshing with proper error handling and security considerations.',

        status: TaskStatus.IN_PROGRESS,


        created_at: '2025-01-15T10:30:00.000000',
        updated_at: '2025-01-15T10:30:00.000001',




        type: 'CODING',
        checklist: [
            {
                id: '1',
                title: 'Create token validation function',

                is_complete: true,
                order: 0,
            },
            {
                id: '2',
                title: 'Implement refresh token storage',

                is_complete: true,
                order: 1,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // New tasks - User Notification System (INIT-251)
    {
        id: 'task-notification-001',
        identifier: 'T-1100',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747585',
        title: 'Design notification system architecture',
        description: 'Create a detailed technical architecture for the notification system, including database schema, message queuing, and delivery mechanisms.',

        status: TaskStatus.DONE,


        created_at: '2025-01-26T10:00:00.000000',
        updated_at: '2025-01-26T10:00:00.000001',




        type: 'PLANNING',
        checklist: [
            {
                id: 'checklist-001',
                task_id: 'task-notification-001',
                title: 'Diagram database schema',
                is_complete: true,
                order: 0,
            },
            {
                id: 'checklist-002',
                task_id: 'task-notification-001',
                title: 'Document API endpoints',
                is_complete: true,
                order: 1,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-notification-002',
        identifier: 'T-1101',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747585',
        title: 'Implement notification database models',
        description: 'Create database models and migrations for storing notification templates, user preferences, and notification history.',

        status: TaskStatus.DONE,


        created_at: '2025-02-01T11:30:00.000000',
        updated_at: '2025-02-01T11:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-notification-003',
        identifier: 'T-1102',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747585',
        title: 'Set up WebSocket server for real-time notifications',
        description: 'Implement WebSocket server to push real-time notifications to connected clients with proper authentication and error handling.',

        status: TaskStatus.IN_PROGRESS,


        created_at: '2025-02-10T14:00:00.000000',
        updated_at: '2025-02-10T14:00:00.000001',




        type: 'CODING',
        checklist: [
            {
                id: 'checklist-003',
                task_id: 'task-notification-003',
                title: 'Implement authentication middleware',
                is_complete: true,
                order: 0,
            },
            {
                id: 'checklist-004',
                task_id: 'task-notification-003',
                title: 'Create channel subscription mechanism',
                is_complete: false,
                order: 1,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-notification-004',
        identifier: 'T-1103',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747585',
        title: 'Create notification preferences UI',
        description: 'Design and implement UI components for users to manage their notification preferences across different channels.',

        status: TaskStatus.TO_DO,


        created_at: '2025-02-20T15:30:00.000000',
        updated_at: '2025-02-20T15:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-notification-005',
        identifier: 'T-1104',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747585',
        title: 'Implement email notification delivery service',
        description: 'Create a service to format and deliver email notifications with proper templating, tracking, and retry mechanisms.',

        status: TaskStatus.TO_DO,


        created_at: '2025-03-01T09:00:00.000000',
        updated_at: '2025-03-01T09:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // Mobile App Development (INIT-252)
    {
        id: 'task-mobile-001',
        identifier: 'T-1105',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747586',
        title: 'Research and select React Native architecture',
        description: 'Evaluate different React Native architecture approaches (Expo vs bare workflow) and select the most appropriate for our requirements.',

        status: TaskStatus.TO_DO,


        created_at: '2025-02-10T10:00:00.000000',
        updated_at: '2025-02-10T10:00:00.000001',




        type: 'RESEARCH',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-mobile-002',
        identifier: 'T-1106',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747586',
        title: 'Set up mobile CI/CD pipeline',
        description: 'Establish continuous integration and deployment pipeline for mobile app builds, including code signing and app store distribution.',

        status: TaskStatus.TO_DO,


        created_at: '2025-02-15T13:30:00.000000',
        updated_at: '2025-02-15T13:30:00.000001',




        type: 'DEVOPS',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-mobile-003',
        identifier: 'T-1107',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747586',
        title: 'Design mobile app UI/UX',
        description: 'Create comprehensive UI/UX designs for the mobile application, optimized for mobile device interaction patterns.',

        status: TaskStatus.TO_DO,


        created_at: '2025-03-01T11:00:00.000000',
        updated_at: '2025-03-01T11:00:00.000001',




        type: 'DESIGN',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-mobile-004',
        identifier: 'T-1108',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747586',
        title: 'Implement offline mode support',
        description: 'Add capability for the mobile app to function with limited functionality when offline, with data synchronization when back online.',

        status: TaskStatus.TO_DO,


        created_at: '2025-04-15T16:45:00.000000',
        updated_at: '2025-04-15T16:45:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-mobile-005',
        identifier: 'T-1109',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747586',
        title: 'Implement push notification handling',
        description: 'Add support for receiving and processing push notifications on iOS and Android platforms with proper permission handling.',

        status: TaskStatus.TO_DO,


        created_at: '2025-05-01T14:00:00.000000',
        updated_at: '2025-05-01T14:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // Collaborative Editing (INIT-253)
    {
        id: 'task-collab-001',
        identifier: 'T-1110',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747587',
        title: 'Research CRDT algorithms for collaborative editing',
        description: 'Evaluate different Conflict-free Replicated Data Type (CRDT) algorithms for implementing collaborative editing with proper conflict resolution.',

        status: TaskStatus.DONE,


        created_at: '2025-02-12T09:30:00.000000',
        updated_at: '2025-02-12T09:30:00.000001',




        type: 'RESEARCH',
        checklist: [
            {
                id: 'checklist-005',
                task_id: 'task-collab-001',
                title: 'Evaluate Yjs library',
                is_complete: true,
            },
            {
                id: 'checklist-006',
                task_id: 'task-collab-001',
                title: 'Evaluate Automerge library',
                is_complete: true,
            },
            {
                id: 'checklist-007',
                task_id: 'task-collab-001',
                title: 'Compare performance characteristics',
                is_complete: true,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-collab-002',
        identifier: 'T-1111',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747587',
        title: 'Implement real-time collaboration server',
        description: 'Create server-side infrastructure for handling collaborative editing sessions, including authentication, authorization, and data persistence.',

        status: TaskStatus.DONE,


        created_at: '2025-02-18T14:15:00.000000',
        updated_at: '2025-02-18T14:15:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-collab-003',
        identifier: 'T-1112',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747587',
        title: 'Create collaborative text editor component',
        description: 'Develop a React component for collaborative text editing using the selected CRDT library with proper cursors and presence indicators.',

        status: TaskStatus.IN_PROGRESS,


        created_at: '2025-02-25T11:30:00.000000',
        updated_at: '2025-02-25T11:30:00.000001',




        type: 'CODING',
        checklist: [
            {
                id: 'checklist-008',
                task_id: 'task-collab-003',
                title: 'Implement text synchronization',
                is_complete: true,
            },
            {
                id: 'checklist-009',
                task_id: 'task-collab-003',
                title: 'Add cursor positions',
                is_complete: false,
            },
            {
                id: 'checklist-010',
                task_id: 'task-collab-003',
                title: 'Implement user presence indicators',
                is_complete: false,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-collab-004',
        identifier: 'T-1113',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747587',
        title: 'Implement conflict resolution for structured data',
        description: 'Implement conflict resolution strategies for structured data (lists, maps, etc.) in collaborative editing sessions.',

        status: TaskStatus.TO_DO,


        created_at: '2025-03-01T09:45:00.000000',
        updated_at: '2025-03-01T09:45:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-collab-005',
        identifier: 'T-1114',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747587',
        title: 'Add history and versioning support',
        description: 'Implement document history tracking and version management for collaborative documents with ability to view and restore previous versions.',

        status: TaskStatus.TO_DO,


        created_at: '2025-03-15T10:00:00.000000',
        updated_at: '2025-03-15T10:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // React 19 Upgrade (INIT-254)
    {
        id: 'task-react19-001',
        identifier: 'T-1115',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747588',
        title: 'Evaluate React 19 breaking changes',
        description: 'Analyze React 19 release notes and documentation to identify all breaking changes and deprecated features that will affect our codebase.',

        status: TaskStatus.DONE,


        created_at: '2025-02-16T09:00:00.000000',
        updated_at: '2025-02-16T09:00:00.000001',




        type: 'RESEARCH',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-react19-002',
        identifier: 'T-1116',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747588',
        title: 'Update React and React DOM dependencies',
        description: 'Update package.json dependencies to React 19 versions and resolve any peer dependency conflicts.',

        status: TaskStatus.DONE,


        created_at: '2025-02-18T10:30:00.000000',
        updated_at: '2025-02-18T10:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-react19-003',
        identifier: 'T-1117',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747588',
        title: 'Update component code to React 19 patterns',
        description: 'Refactor components to use React 19 patterns and APIs, removing deprecated patterns and implementing recommended alternatives.',

        status: TaskStatus.DONE,


        created_at: '2025-02-20T14:00:00.000000',
        updated_at: '2025-02-20T14:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-react19-004',
        identifier: 'T-1118',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747588',
        title: 'Update testing infrastructure for React 19',
        description: 'Update testing libraries and test code to be compatible with React 19, including React Testing Library and test utilities.',

        status: TaskStatus.DONE,


        created_at: '2025-02-22T11:00:00.000000',
        updated_at: '2025-02-22T11:00:00.000001',




        type: 'TESTING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-react19-005',
        identifier: 'T-1119',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747588',
        title: 'Implement new React 19 features',
        description: 'Identify and implement new React 19 features and optimizations that can benefit our application.',

        status: TaskStatus.DONE,


        created_at: '2025-02-24T13:30:00.000000',
        updated_at: '2025-02-24T13:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // E2E Testing Suite (INIT-255)
    {
        id: 'task-e2e-001',
        identifier: 'T-1120',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747589',
        title: 'Set up Cypress testing framework',
        description: 'Install and configure Cypress testing framework with TypeScript support, including folder structure and base configuration.',

        status: TaskStatus.BLOCKED,


        created_at: '2025-03-03T10:00:00.000000',
        updated_at: '2025-03-03T10:00:00.000001',




        type: 'DEVOPS',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-e2e-002',
        identifier: 'T-1121',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747589',
        title: 'Create test utilities and fixtures',
        description: 'Develop reusable test utilities, fixtures, and commands for Cypress tests to ensure consistency and reduce duplication.',

        status: TaskStatus.BLOCKED,


        created_at: '2025-03-10T11:15:00.000000',
        updated_at: '2025-03-10T11:15:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // AI Recommendations (INIT-256)
    {
        id: 'task-ai-001',
        identifier: 'T-1122',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747590',
        title: 'Design recommendation engine architecture',
        description: 'Create technical architecture for the AI recommendation engine, including data flow, model training and serving components.',

        status: TaskStatus.DONE,


        created_at: '2025-03-16T09:30:00.000000',
        updated_at: '2025-03-16T09:30:00.000001',




        type: 'PLANNING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-ai-002',
        identifier: 'T-1123',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747590',
        title: 'Implement data collection and processing pipeline',
        description: 'Create data pipeline to collect, process, and store user behavior data for training recommendation models.',

        status: TaskStatus.DONE,


        created_at: '2025-03-25T14:45:00.000000',
        updated_at: '2025-03-25T14:45:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-ai-003',
        identifier: 'T-1124',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747590',
        title: 'Develop collaborative filtering algorithm',
        description: 'Implement collaborative filtering recommendation algorithm using user behavior data to generate personalized content recommendations.',

        status: TaskStatus.IN_PROGRESS,


        created_at: '2025-04-05T13:00:00.000000',
        updated_at: '2025-04-05T13:00:00.000001',




        type: 'CODING',
        checklist: [
            {
                id: 'checklist-011',
                task_id: 'task-ai-003',
                title: 'Implement matrix factorization',
                is_complete: true,
            },
            {
                id: 'checklist-012',
                task_id: 'task-ai-003',
                title: 'Add item similarity calculation',
                is_complete: false,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-ai-004',
        identifier: 'T-1125',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747590',
        title: 'Create recommendation API endpoints',
        description: 'Implement API endpoints for serving personalized recommendations to users with proper caching and performance optimizations.',

        status: TaskStatus.TO_DO,


        created_at: '2025-04-15T11:30:00.000000',
        updated_at: '2025-04-15T11:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-ai-005',
        identifier: 'T-1126',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747590',
        title: 'Implement recommendation UI components',
        description: 'Design and implement UI components for displaying personalized recommendations to users in various contexts.',

        status: TaskStatus.TO_DO,


        created_at: '2025-04-20T15:00:00.000000',
        updated_at: '2025-04-20T15:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // Database Optimization (INIT-257)
    {
        id: 'task-db-001',
        identifier: 'T-1127',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747591',
        title: 'Perform database query performance audit',
        description: 'Analyze database query performance using monitoring tools to identify slow queries and optimization opportunities.',

        status: TaskStatus.TO_DO,


        created_at: '2025-04-02T09:00:00.000000',
        updated_at: '2025-04-02T09:00:00.000001',




        type: 'ANALYSIS',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-db-002',
        identifier: 'T-1128',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747591',
        title: 'Optimize database indexes',
        description: 'Add, modify, or remove database indexes based on query analysis to improve query performance.',

        status: TaskStatus.TO_DO,


        created_at: '2025-04-05T11:30:00.000000',
        updated_at: '2025-04-05T11:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-db-003',
        identifier: 'T-1129',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747591',
        title: 'Implement database query caching',
        description: 'Add caching layer for frequent database queries to reduce database load and improve response times.',

        status: TaskStatus.TO_DO,


        created_at: '2025-04-10T14:00:00.000000',
        updated_at: '2025-04-10T14:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // Analytics Dashboard (INIT-258)
    {
        id: 'task-analytics-001',
        identifier: 'T-1130',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747592',
        title: 'Design analytics dashboard wireframes',
        description: 'Create detailed wireframes for the analytics dashboard UI, including charts, filters, and report configurations.',

        status: TaskStatus.DONE,


        created_at: '2025-04-16T10:00:00.000000',
        updated_at: '2025-04-16T10:00:00.000001',




        type: 'DESIGN',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-analytics-002',
        identifier: 'T-1131',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747592',
        title: 'Implement data aggregation API endpoints',
        description: 'Create API endpoints for aggregating and serving analytics data to the dashboard with proper filtering and time range options.',

        status: TaskStatus.IN_PROGRESS,


        created_at: '2025-04-20T13:30:00.000000',
        updated_at: '2025-04-20T13:30:00.000001',




        type: 'CODING',
        checklist: [
            {
                id: 'checklist-013',
                task_id: 'task-analytics-002',
                title: 'Implement time range filtering',
                is_complete: true,
            },
            {
                id: 'checklist-014',
                task_id: 'task-analytics-002',
                title: 'Add data aggregation logic',
                is_complete: true,
            },
            {
                id: 'checklist-015',
                task_id: 'task-analytics-002',
                title: 'Implement caching layer',
                is_complete: false,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-analytics-003',
        identifier: 'T-1132',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747592',
        title: 'Develop chart visualization components',
        description: 'Create reusable chart components using D3.js for visualizing different types of analytics data.',

        status: TaskStatus.TO_DO,


        created_at: '2025-05-01T11:00:00.000000',
        updated_at: '2025-05-01T11:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // Multi-language Support (INIT-259)
    {
        id: 'task-i18n-001',
        identifier: 'T-1133',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747593',
        title: 'Set up i18n framework and translation workflow',
        description: 'Select and implement internationalization framework with translation management workflow for maintaining multiple language translations.',

        status: TaskStatus.TO_DO,


        created_at: '2025-05-02T10:00:00.000000',
        updated_at: '2025-05-02T10:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-i18n-002',
        identifier: 'T-1134',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747593',
        title: 'Refactor UI components for localization',
        description: 'Update UI components to use i18n translation functions instead of hardcoded text, with proper handling of pluralization and formatting.',

        status: TaskStatus.TO_DO,


        created_at: '2025-05-15T14:30:00.000000',
        updated_at: '2025-05-15T14:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // Kubernetes Migration (INIT-260)
    {
        id: 'task-k8s-001',
        identifier: 'T-1135',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747594',
        title: 'Design Kubernetes cluster architecture',
        description: 'Create detailed architecture for Kubernetes cluster, including node types, networking, storage, and security configurations.',

        status: TaskStatus.DONE,


        created_at: '2025-05-16T09:45:00.000000',
        updated_at: '2025-05-16T09:45:00.000001',




        type: 'PLANNING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-k8s-002',
        identifier: 'T-1136',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747594',
        title: 'Containerize application services',
        description: 'Create Docker containers for all application services with optimized configurations for Kubernetes deployment.',

        status: TaskStatus.IN_PROGRESS,


        created_at: '2025-05-25T13:15:00.000000',
        updated_at: '2025-05-25T13:15:00.000001',




        type: 'DEVOPS',
        checklist: [
            {
                id: 'checklist-016',
                task_id: 'task-k8s-002',
                title: 'Containerize frontend application',
                is_complete: true,
            },
            {
                id: 'checklist-017',
                task_id: 'task-k8s-002',
                title: 'Containerize API services',
                is_complete: false,
            },
            {
                id: 'checklist-018',
                task_id: 'task-k8s-002',
                title: 'Containerize worker services',
                is_complete: false,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // Add tasks to previous initiatives that had empty task arrays
    {
        id: 'task-dashboard-001',
        identifier: 'T-1137',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580', // Dashboard performance initiative
        title: 'Profile dashboard component rendering',
        description: 'Use React profiler to identify slow-rendering components in the dashboard and document optimization opportunities.',

        status: TaskStatus.DONE,


        created_at: '2025-01-16T09:00:00.000000',
        updated_at: '2025-01-16T09:00:00.000001',




        type: 'ANALYSIS',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-dashboard-002',
        identifier: 'T-1138',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580', // Dashboard performance initiative
        title: 'Implement virtualized lists for large datasets',
        description: 'Replace standard list rendering with virtualized lists to improve performance when displaying large datasets.',

        status: TaskStatus.IN_PROGRESS,


        created_at: '2025-01-25T11:30:00.000000',
        updated_at: '2025-01-25T11:30:00.000001',




        type: 'CODING',
        checklist: [
            {
                id: 'checklist-019',
                task_id: 'task-dashboard-002',
                title: 'Research virtualization libraries',
                is_complete: true,
            },
            {
                id: 'checklist-020',
                task_id: 'task-dashboard-002',
                title: 'Implement in main data table',
                is_complete: true,
            },
            {
                id: 'checklist-021',
                task_id: 'task-dashboard-002',
                title: 'Implement in sidebar lists',
                is_complete: false,
            },
        ],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-export-001',
        identifier: 'T-1139',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747581', // Data export initiative
        title: 'Implement CSV export functionality',
        description: 'Create backend service and API endpoint for exporting data in CSV format with proper formatting and character encoding.',

        status: TaskStatus.DONE,


        created_at: '2025-01-21T10:00:00.000000',
        updated_at: '2025-01-21T10:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-export-002',
        identifier: 'T-1140',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747581', // Data export initiative
        title: 'Implement Excel export functionality',
        description: 'Create backend service and API endpoint for exporting data in Excel format with proper formatting, styling, and multiple sheets.',

        status: TaskStatus.DONE,


        created_at: '2025-02-01T13:30:00.000000',
        updated_at: '2025-02-01T13:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-export-003',
        identifier: 'T-1141',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747581', // Data export initiative
        title: 'Implement PDF export functionality',
        description: 'Create backend service and API endpoint for exporting data in PDF format with proper formatting, pagination, and header/footer.',

        status: TaskStatus.DONE,


        created_at: '2025-02-20T11:00:00.000000',
        updated_at: '2025-02-20T11:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-microservices-001',
        identifier: 'T-1142',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747582', // Microservices initiative
        title: 'Design microservices architecture',
        description: 'Create detailed architecture for breaking monolithic application into microservices, including service boundaries and communication patterns.',

        status: TaskStatus.TO_DO,


        created_at: '2025-01-10T09:30:00.000000',
        updated_at: '2025-01-10T09:30:00.000001',




        type: 'PLANNING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-microservices-002',
        identifier: 'T-1143',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747582', // Microservices initiative
        title: 'Implement service discovery mechanism',
        description: 'Set up service discovery infrastructure to allow microservices to locate and communicate with each other dynamically.',

        status: TaskStatus.TO_DO,


        created_at: '2025-01-30T13:00:00.000000',
        updated_at: '2025-01-30T13:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-a11y-001',
        identifier: 'T-1144',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584', // Accessibility initiative
        title: 'Perform accessibility audit',
        description: 'Conduct comprehensive accessibility audit using automated tools and manual testing to identify WCAG 2.1 AA compliance issues.',

        status: TaskStatus.DONE,


        created_at: '2025-01-21T10:00:00.000000',
        updated_at: '2025-01-21T10:00:00.000001',




        type: 'TESTING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-a11y-002',
        identifier: 'T-1145',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584', // Accessibility initiative
        title: 'Fix keyboard navigation issues',
        description: 'Improve keyboard navigation throughout the application to ensure all functionality is accessible without using a mouse.',

        status: TaskStatus.DONE,


        created_at: '2025-02-01T11:30:00.000000',
        updated_at: '2025-02-01T11:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-a11y-003',
        identifier: 'T-1146',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584', // Accessibility initiative
        title: 'Improve screen reader compatibility',
        description: 'Update components to provide appropriate ARIA attributes and ensure proper screen reader announcements for dynamic content changes.',

        status: TaskStatus.DONE,


        created_at: '2025-02-20T13:00:00.000000',
        updated_at: '2025-02-20T13:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // Add remaining tasks to reach 50
    {
        id: 'task-extra-001',
        identifier: 'T-1147',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747579', // Authentication initiative
        title: 'Implement OAuth provider integration',
        description: 'Add support for authenticating with Google, GitHub, and Facebook OAuth providers with proper account linking.',

        status: TaskStatus.TO_DO,


        created_at: '2025-02-01T11:00:00.000000',
        updated_at: '2025-02-01T11:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-extra-002',
        identifier: 'T-1148',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747579', // Authentication initiative
        title: 'Implement multi-factor authentication',
        description: 'Add support for multi-factor authentication using app-based TOTP and/or SMS verification with proper recovery mechanisms.',

        status: TaskStatus.TO_DO,


        created_at: '2025-02-15T13:30:00.000000',
        updated_at: '2025-02-15T13:30:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-extra-003',
        identifier: 'T-1149',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747590', // AI initiative
        title: 'Implement content-based filtering algorithm',
        description: 'Develop content-based filtering algorithm to complement collaborative filtering for more accurate recommendations.',

        status: TaskStatus.TO_DO,


        created_at: '2025-05-01T10:00:00.000000',
        updated_at: '2025-05-01T10:00:00.000001',




        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-extra-004',
        identifier: 'T-1150',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747588', // React 19 initiative
        title: 'Document React 19 migration lessons',
        description: 'Create comprehensive documentation on the React 19 migration process, including challenges, solutions, and best practices.',

        status: TaskStatus.TO_DO,


        created_at: '2025-02-28T09:00:00.000000',
        updated_at: '2025-02-28T09:00:00.000001',




        type: 'DOCUMENTATION',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        id: 'task-extra-005',
        identifier: 'T-1151',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        initiative_id: 'cd441dc5-1bf8-423f-9f88-f47e1c747586', // Mobile app initiative
        title: 'Implement mobile app authentication',
        description: 'Create secure authentication flow for mobile application with biometric authentication support and secure token storage.',
        status: TaskStatus.TO_DO,
        created_at: '2025-05-20T11:30:00.000000',
        updated_at: '2025-05-20T11:30:00.000001',
        type: 'CODING',
        checklist: [],
        has_pending_job: null,
        workspace: mockWorkspace
    }
];

let rank = LexoRank.middle()

export const mockTasks = mockTasks__unordered.map((task) => {
    rank = rank.genNext()

    return {
        ...task,
        position: rank.genNext().toString(),
        orderingId: task.id
    }
})

export const mockInitiatives__unordered: InitiativeDto[] = [
    {
        type: "CHORE",
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747579',
        identifier: 'I-245',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Revamp authentication system so that it is compliant with GDPR and CCPA',
        description: `Our current authentication system needs significant updates to improve security and user experience:

- Migrate from cookie-based authentication to JWT tokens
- Implement refresh token mechanism to prevent frequent logouts
- Add multi-factor authentication support
- Integrate with OAuth providers (Google, GitHub, Facebook)
- Improve password recovery workflow
- Update user profile management

This initiative will cover all aspects of the authentication system overhaul, including backend services, API endpoints, and frontend components.`,



        created_at: '2025-01-09T17:50:48.340652',
        updated_at: '2025-01-09T17:50:48.340653',
        status: TaskStatus.TO_DO,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747579' ||
            task.identifier === 'T-1147' ||
            task.identifier === 'T-1148'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747580',
        identifier: 'I-246',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Dashboard performance optimization',
        description: 'Improve dashboard loading and rendering performance to enhance user experience, especially for users with large datasets.',



        created_at: '2025-01-15T10:30:00.000000',
        updated_at: '2025-01-15T10:30:00.000001',

        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747580'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747581',
        identifier: 'I-247',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Implement data export functionality',
        description: 'Add ability to export project data in multiple formats (CSV, Excel, PDF) for reporting and backup purposes.',



        created_at: '2025-01-20T14:00:00.000000',
        updated_at: '2025-01-20T14:00:00.000001',

        status: TaskStatus.DONE,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747581'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747582',
        identifier: 'I-248',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Migrate backend to microservices architecture',
        description: 'Refactor the monolithic backend into microservices to improve scalability and maintenance.',



        created_at: '2025-01-09T17:50:48.340652',
        updated_at: '2025-01-09T17:50:48.340653',

        status: TaskStatus.TO_DO,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747582'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747583',
        identifier: 'I-249',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Implement advanced search and filtering',
        description: 'Add comprehensive search functionality across all data with advanced filtering options for better user experience.',



        created_at: '2025-01-15T10:30:00.000000',
        updated_at: '2025-01-15T10:30:00.000001',

        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747583'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584',
        identifier: 'I-250',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Accessibility compliance improvements',
        description: 'Update application to meet WCAG 2.1 AA compliance standards for accessibility across all features.',



        created_at: '2025-01-20T14:00:00.000000',
        updated_at: '2025-01-20T14:00:00.000001',

        status: TaskStatus.DONE,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747584'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    // New initiatives
    {
        type: "FEATURE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747585',
        identifier: 'I-251',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Implement user notification system built on top of the new notification service so that it is compliant with GDPR and CCPA',
        description: 'Create a comprehensive notification system that alerts users about important events, updates, and actions needed. Include in-app notifications, email digests, and push notifications for mobile users.',



        created_at: '2025-01-25T09:00:00.000000',
        updated_at: '2025-01-25T09:00:00.000001',

        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747585'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "FEATURE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747586',
        identifier: 'I-252',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Mobile app development',
        description: 'Develop native mobile applications for iOS and Android platforms to provide users with a seamless mobile experience.',



        created_at: '2025-02-01T15:00:00.000000',
        updated_at: '2025-02-01T15:00:00.000001',

        status: TaskStatus.TO_DO,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747586' ||
            task.identifier === 'T-1151'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "FEATURE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747587',
        identifier: 'I-253',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Implement collaborative editing',
        description: 'Add real-time collaborative editing features to allow multiple users to work on the same content simultaneously without conflicts.',



        created_at: '2025-02-10T11:00:00.000000',
        updated_at: '2025-02-10T11:00:00.000001',

        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747587'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747588',
        identifier: 'I-254',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Upgrade to React 19',
        description: 'Migrate the frontend application from React 18 to React 19 to leverage new features and performance improvements.',



        created_at: '2025-02-15T13:30:00.000000',
        updated_at: '2025-02-15T13:30:00.000001',

        status: TaskStatus.DONE,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747588' ||
            task.identifier === 'T-1150'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747589',
        identifier: 'I-255',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Implement end-to-end testing suite using Cypress for the frontend and backend testing via Jest',
        description: 'Develop comprehensive end-to-end test suite using Cypress to ensure all critical user flows work correctly.',



        created_at: '2025-03-01T10:15:00.000000',
        updated_at: '2025-03-01T10:15:00.000001',

        status: TaskStatus.BLOCKED,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747589'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "FEATURE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747590',
        identifier: 'I-256',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Implement AI-powered content recommendations',
        description: 'Integrate machine learning algorithms to provide personalized content recommendations based on user behavior and preferences.',



        created_at: '2025-03-15T16:45:00.000000',
        updated_at: '2025-03-15T16:45:00.000001',

        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747590' ||
            task.identifier === 'T-1149'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747591',
        identifier: 'I-257',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Database optimization and scaling',
        description: 'Optimize database performance and implement sharding strategy to handle increasing data volumes and user traffic.',



        created_at: '2025-04-01T14:20:00.000000',
        updated_at: '2025-04-01T14:20:00.000001',

        status: TaskStatus.TO_DO,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747591'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "FEATURE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747592',
        identifier: 'I-258',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Implement advanced analytics dashboard',
        description: 'Create a comprehensive analytics dashboard with visualizations and reports for users to track performance metrics and KPIs.',



        created_at: '2025-04-15T11:30:00.000000',
        updated_at: '2025-04-15T11:30:00.000001',

        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747592'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "FEATURE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747593',
        identifier: 'I-259',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Multi-language support implementation',
        description: 'Add internationalization and localization support to make the application available in multiple languages.',



        created_at: '2025-05-01T09:45:00.000000',
        updated_at: '2025-05-01T09:45:00.000001',

        status: TaskStatus.TO_DO,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747593'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "CHORE",

        id: 'cd441dc5-1bf8-423f-9f88-f47e1c747594',
        identifier: 'I-260',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Infrastructure migration to Kubernetes',
        description: 'Migrate application hosting from traditional VMs to a Kubernetes-based infrastructure for improved scalability and resilience.',



        created_at: '2025-05-15T13:15:00.000000',
        updated_at: '2025-05-15T13:15:00.000001',

        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747594'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "BUGFIX",
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c749384',
        identifier: 'I-260',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Fix migration to Kubernetes',
        description: 'Migrate application hosting from traditional VMs to a Kubernetes-based infrastructure for improved scalability and resilience.',

        created_at: '2025-05-15T13:15:00.000000',
        updated_at: '2025-05-15T13:15:00.000001',

        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.initiative_id === 'cd441dc5-1bf8-423f-9f88-f47e1c747594'
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "BUGFIX",
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c749385',
        identifier: 'I-261',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Fix critical login bug',
        description: 'Users are reporting intermittent login failures. This initiative aims to identify and resolve the root cause of the login issues.',

        created_at: '2025-06-01T10:00:00.000000',
        updated_at: '2025-06-01T10:00:00.000001',
        status: TaskStatus.TO_DO,
        tasks: mockTasks.filter(task =>
            task.identifier === 'T-1024' // "Implement user authentication flow"
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    },
    {
        type: "BUGFIX",
        id: 'cd441dc5-1bf8-423f-9f88-f47e1c749386',
        identifier: 'I-262',
        user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        title: 'Address data export errors',
        description: 'Fix errors occurring during data export to CSV and PDF formats. Ensure all data is correctly formatted and exported without loss.',

        created_at: '2025-06-05T14:30:00.000000',
        updated_at: '2025-06-05T14:30:00.000001',
        status: TaskStatus.IN_PROGRESS,
        tasks: mockTasks.filter(task =>
            task.identifier === 'T-1139' || // "Implement CSV export functionality"
            task.identifier === 'T-1141'    // "Implement PDF export functionality"
        ),
        has_pending_job: null,
        workspace: mockWorkspace
    }
];

export const mockInitiatives: OrderedEntity<InitiativeDto>[] = mockInitiatives__unordered.map((initiative) => {
    rank = rank.genNext()
    let tasksRank = LexoRank.middle()
    return {
        ...initiative,
        tasks: initiative.tasks.map((task) => {
            tasksRank = tasksRank.genNext()
            return {
                ...task,
                position: tasksRank.genNext().toString(),
                orderingId: task.id
            }
        }),
        position: rank.genNext().toString(),
        orderingId: initiative.id
    }
})

export const testInitiativeDto: InitiativeDto = {
    type: "CHORE",

    id: 'cd441dc5-1bf8-423f-9f88-f47e1c747579',
    identifier: 'I-251',
    user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
    title: 'Implement CI/CD pipeline',
    description: 'Set up continuous integration and deployment pipeline to automate testing and deployment processes.',



    created_at: '2025-01-09T17:50:48.340652',
    updated_at: '2025-01-09T17:50:48.340653',

    status: TaskStatus.TO_DO,
    tasks: [],
    has_pending_job: null,
    workspace: mockWorkspace
};

// --- Common Mock Functions ---

export const mockRequestImprovement = (inputData: (InitiativeDto | TaskDto)[], lens: LENS, threadId: string, mode?: AgentMode, messages?: AiJobChatMessage[]): Promise<void> => {
    console.log('Mock request improvement', lens, inputData, messages, mode);
    return Promise.resolve();
};

export const mockUpdateImprovement = (job: AiImprovementJobResult): Promise<void> => {
    console.log('Mock update improvement', job);
    return Promise.resolve();
};

export const mockUpdateInitiatives = (initiatives: Partial<InitiativeDto>[]): Promise<InitiativeDto[]> => {
    console.log('Mock update initiatives', initiatives);
    return Promise.resolve(initiatives.map(init => ({ ...testInitiativeDto, ...init })));
};

export const mockUpdateInitiative = (initiative: Partial<InitiativeDto>): Promise<InitiativeDto> => {
    console.log('Mock update initiative', initiative);
    return Promise.resolve({ ...testInitiativeDto, ...initiative });
};

export const mockReloadInitiatives = () => {
    console.log('Mock reload initiatives');
};

export const mockDeleteInitiative = (initiativeId: string): Promise<void> => {
    console.log('Mock delete initiative', initiativeId);
    return Promise.resolve();
};

export const mockDeleteTask = (taskId: string): Promise<void> => {
    console.log('Mock delete task', taskId);
    return Promise.resolve();
};

export const mockChecklistItem = (checklistItemId: string): Promise<void> => {
    console.log('Mock delete checklist item', checklistItemId);
    return Promise.resolve();
};

export const mockUpdateTasks = (tasks: Partial<TaskDto>[]): Promise<TaskDto[]> => {
    console.log('Mock update tasks', tasks);
    return Promise.resolve(tasks.map(task => ({ ...mockTasks[0], ...task })));
};

export const mockUpdateTask = (task: Partial<TaskDto>): Promise<TaskDto> => {
    console.log('Mock update task', task);
    return Promise.resolve({ ...mockTasks[0], ...task });
};

export const mockCreateTask = async (task: Partial<TaskDto>): Promise<TaskDto> => {
    console.log('Mock create task', task);
    await sleep(1000)
    return Promise.resolve({
        ...task,
    } as TaskDto);
};

export const mockReloadTasks = () => {
    console.log('Mock reload tasks');
};

export const mockReloadTask = () => {
    console.log('Mock reload task');
};

export const mockUpdateInitiative_Initiative = (initiative: Partial<InitiativeDto>): Promise<void> => {
    console.log('Mock update initiative (void return)', initiative);
    return Promise.resolve();
};

export const mockReloadInitiative = () => {
    console.log('Mock reload initiative');
};

export const mockDeleteInitiative_Initiative = (): Promise<void> => {
    console.log('Mock delete initiative (void return)');
    return Promise.resolve();
};

export const mockChangeWorkspace = (workspace: WorkspaceDto): Promise<void> => {
    console.log('Mock change workspace', workspace);
    return Promise.resolve();
};

export const mockAddWorkspace = (workspace: Omit<WorkspaceDto, 'id'>): Promise<WorkspaceDto> => {
    console.log('Mock add workspace', workspace);
    const newWorkspace: WorkspaceDto = {
        id: `new-${Date.now()}`,
        ...workspace
    };
    return Promise.resolve(newWorkspace);
};

export const mockRefresh = (): Promise<void> => {
    console.log('Mock refresh');
    return Promise.resolve();
};

export const mockDeleteChecklistItem = (checklistItemId: string): Promise<void> => {
    console.log('Mock delete checklist item', checklistItemId);
    return Promise.resolve();
};

export const mockGetInitiatives = (): Promise<InitiativeDto[]> => {
    console.log('Mock get initiatives');
    return Promise.resolve(mockInitiatives);
};

export const mockCreateInitiative = async (initiative: Partial<InitiativeDto>): Promise<InitiativeDto> => {
    console.log('Mock create initiative', initiative);
    await sleep(1000)
    return Promise.resolve({ ...mockInitiatives[0], ...initiative });
};

export const mockSetThreadId = (threadId: string): void => {
    console.log('Mock set thread id called', threadId)
}

export const mockDeleteJob = (jobId: string): void => {
    console.log('Mock delete job called', jobId)
}

export const mockResetError = (): void => {
    console.log('Mock reset error called')
}

export const mockInvalidateTasks = (): void => {
    console.log('Mock invalidate tasks called')
}

// Mock tasks data used in stories
export const mockTasksData: ManagedTaskModel[] = [
    {
        action: ManagedEntityAction.UPDATE,
        identifier: 'TM-001',
        title: 'Setup project infrastructure and CI/CD pipeline',
        description: 'Configure development environment, setup automated testing, and implement continuous integration and deployment pipeline for the project.',
        checklist: [
            {
                title: 'Initialize project repository',
                completed: false,
                order: 1
            },
            {
                title: 'Configure CI/CD pipeline',
                completed: false,
                order: 2
            },
            {
                title: 'Setup testing framework',
                completed: true,
                order: 3
            }
        ]
    },
    {
        action: ManagedEntityAction.CREATE,
        title: 'Implement user authentication system',
        description: 'Create secure user registration, login, and session management functionality with proper error handling and validation.',
        checklist: [
            {
                title: 'Design authentication flow',
                completed: false,
                order: 1
            },
            {
                title: 'Implement login component',
                completed: false,
                order: 2
            },
            {
                title: 'Add password validation',
                completed: false,
                order: 3
            },
            {
                title: 'Setup JWT token handling',
                completed: false,
                order: 4
            },
            {
                title: 'Add logout functionality',
                completed: false,
                order: 5
            },
            {
                title: 'Implement session persistence',
                completed: false,
                order: 6
            },
            {
                title: 'Add error handling',
                completed: false,
                order: 7
            },
            {
                title: 'Write authentication tests',
                completed: false,
                order: 8
            }
        ]
    }
];

export const mockCreateInitiativeDiff: CreateInitiativeModel = {
    action: ManagedEntityAction.CREATE,
    title: 'AI-Suggested Initiative: Security Enhancement',
    description: 'Comprehensive security audit and implementation of enhanced security measures across the application, including authentication improvements, data encryption, and vulnerability assessments.',
    type: 'SECURITY',
    workspace_identifier: '123',
    tasks: [
        {
            action: ManagedEntityAction.CREATE,
            title: 'Conduct security audit',
            description: 'Perform comprehensive security assessment of current system',
            checklist: [
                {
                    title: 'Review authentication mechanisms',
                    completed: false,
                    order: 1
                },
                {
                    title: 'Analyze data encryption practices',
                    completed: false,
                    order: 2
                }
            ]
        },
        {
            action: ManagedEntityAction.CREATE,
            title: 'Implement two-factor authentication',
            description: 'Add 2FA support for enhanced user account security',
            checklist: [
                {
                    title: 'Research 2FA providers',
                    completed: false,
                    order: 1
                },
                {
                    title: 'Implement TOTP support',
                    completed: false,
                    order: 2
                }
            ]
        }
    ]
};

export const mockUpdateTaskVoid = (task: Partial<TaskDto>): Promise<void> => {
    console.log('Mock update task void called', task);
    return Promise.resolve();
};

export const mockSetInitiativeId = (initiativeId: string | null | undefined): void => {
    console.log('Mock set initiative id called', initiativeId);
};

export const mockSetTaskId = (taskId: string | null | undefined): void => {
    console.log('Mock set task id called', taskId);
};

export const mockStartPolling = (intervalMs: number | undefined) => {
    console.log("Starting polling in TaskContext")
}

export const mockStopPolling = () => {
    console.log("Stopping polling in TaskContext")
}

export const mockReorderTask = (taskId: string, afterId: string | null, beforeId: string | null): Promise<void> => {
    console.log("Mock reorder task")
    return Promise.resolve()
}

export const mockMoveTaskToStatus = (taskId: string, newStatus: TaskStatus, afterId: string | null, beforeId: string | null): Promise<void> => {
    console.log("Mock move task to status")
    return Promise.resolve()
}

// --- Standard Hook Return Values ---

export const mockLocationReturn = {
    pathname: '/workspace',
    search: '',
    hash: '',
    state: null,
    key: 'default'
};

export const mockWorkspacesReturn = {
    workspaces: [
        {
            id: '1', name: 'Personal',
            icon: null,
            description: null
        },
        {
            id: '2', name: 'Work',
            icon: null,
            description: null
        },
        {
            id: '3', name: 'Team Project',
            icon: null,
            description: null
        }
    ],
    currentWorkspace: {
        id: '1', name: 'Personal',
        icon: null,
        description: null
    },
    isLoading: false,
    isProcessing: false,
    changeWorkspace: mockChangeWorkspace,
    addWorkspace: mockAddWorkspace,
    error: null,
    refresh: mockRefresh
};


export const mockUseTasksContext: TasksContextType = {
    tasks: mockTasks,
    shouldShowSkeleton: false,
    isQueryFetching: false,
    isCreatingTask: false,
    isUpdatingTask: false,
    isDeletingTask: false,
    error: null,
    isPolling: false,
    updateTask: mockUpdateTask,
    reloadTasks: mockReloadTasks,
    deleteTask: mockDeleteTask,
    createTask: mockCreateTask,
    invalidateTasks: mockInvalidateTasks,
    setInitiativeId: mockSetInitiativeId,
    setTaskId: mockSetTaskId,
    startPolling: mockStartPolling,
    stopPolling: mockStopPolling,
    reorderTask: mockReorderTask,
    moveTaskToStatus: mockMoveTaskToStatus,
    updateChecklistItem: async () => ({ id: 'updated', title: 'Updated Item', order: 0, task_id: 'task-1', is_complete: false }),
    updateChecklistItemDebounced: async () => ({ id: 'updated', title: 'Updated Item', order: 0, task_id: 'task-1', is_complete: false }),
    addChecklistItem: async () => ({ id: 'new-item', title: 'New Item', order: 0, task_id: 'task-1', is_complete: false }),
    removeChecklistItem: async () => {},
    reorderChecklistItems: async () => []
};


export const mockInvalidateInitiative = () => {
    console.log('Mock invalidate initiative called');
};

export const mockInvalidateAllInitiatives = () => {
    console.log('Mock invalidate all initiatives called');
};

export const mockInvalidateInitiativesByStatus = () => {
    console.log('Mock invalidate initiatives by status called');
};

export const mockReorderInitiative = (initiativeId: string, afterId: string | null, beforeId: string | null): Promise<void> => {
    console.log('Mock reorder initiative')
    return Promise.resolve()
}

export const moveInitiativeToStatus = (initiativeId: string, newStatus: InitiativeStatus, afterId: string | null, beforeId: string | null): Promise<void> => {
    console.log('Mock move initiative to status')
    return Promise.resolve()
}

export const moveInitiativeInGroup = (initiativeId: string, groupId: string, afterId: string | null, beforeId: string | null): Promise<void> => {
    console.log('Mock moveInitiativeInGroup');
    return Promise.resolve()
}

export const mockUpdateInitiativeInCache = (initiative: InitiativeDto, oldStatus?: string): void => {
    console.log('Mock update initiative in cache')
}

export const mockInitiativesContextReturn: InitiativesContextType = {
    initiativesData: mockInitiatives,
    error: null,
    isQueryFetching: false,
    isCreatingInitiative: false,
    isUpdatingInitiative: false,
    isDeletingInitiative: false,
    isBatchUpdatingInitiatives: false,
    isDeletingTask: false,
    isDeletingChecklistItem: false,
    shouldShowSkeleton: false,
    createInitiative: mockCreateInitiative,
    updateInitiatives: mockUpdateInitiatives,
    updateInitiative: mockUpdateInitiative,
    reloadInitiatives: mockReloadInitiatives,
    deleteInitiative: mockDeleteInitiative,
    deleteTask: mockDeleteTask,
    deleteChecklistItem: mockDeleteChecklistItem,
    invalidateInitiative: mockInvalidateInitiative,
    invalidateAllInitiatives: mockInvalidateAllInitiatives,
    invalidateInitiativesByStatus: mockInvalidateInitiativesByStatus,
    reorderInitiative: mockReorderInitiative,
    moveInitiativeToStatus: moveInitiativeToStatus,
    moveInitiativeInGroup: moveInitiativeInGroup,
    updateInitiativeInCache: mockUpdateInitiativeInCache,
};

export const mockInitiativeReturn = {
    initiativeData: mockInitiatives[0],
    loading: false,
    error: null,
    updateInitiative: mockUpdateInitiative_Initiative,
    deleteInitiative: mockDeleteInitiative_Initiative,
    reloadInitiative: mockReloadInitiative,
};


export const mockInitiativeImprovements_from_mockInitiativeJobResult: Record<string, ManagedInitiativeModel> = {
    [mockInitiatives[0].identifier]: {
        action: ManagedEntityAction.UPDATE,
        identifier: mockInitiatives[0].identifier,
        title: 'Updated initiative title',
        description: 'Updated initiative description',

    } as UpdateInitiativeModel,
    [mockInitiatives[1].identifier]: {
        action: ManagedEntityAction.CREATE,
        title: 'New initiative title',
        description: 'New initiative description',

        workspace_identifier: '123'
    } as CreateInitiativeModel,
    [mockInitiatives[2].identifier]: {
        action: ManagedEntityAction.DELETE,
        identifier: mockInitiatives[1].identifier,
    } as DeleteInitiativeModel
}


export const mockInitiativeImprovements: Record<string, ManagedInitiativeModel> = {
    [mockInitiatives[0].identifier]: {
        action: ManagedEntityAction.UPDATE,
        identifier: mockInitiatives[0].identifier,
        title: 'Implement CI/CD pipeline',
        description: 'Set up continuous integration and deployment pipeline to automate testing and deployment processes.',

        type: "CHORE",

        tasks: [
            {
                action: ManagedEntityAction.CREATE,
                title: 'Create a new task',
                description: 'This is a new task',
                checklist: []
            },
            {
                action: ManagedEntityAction.CREATE,
                title: 'Create a new task',
                description: 'This is a new task',
                checklist: []
            },
            {
                action: ManagedEntityAction.UPDATE,
                identifier: mockInitiatives[0].tasks[0].identifier || '',
                title: 'Update the first task',
                description: 'This is an updated task',
                checklist: []
            },
            {
                action: ManagedEntityAction.DELETE,
                identifier: mockInitiatives[0].tasks[1].identifier || '',
            },
            {
                action: ManagedEntityAction.UPDATE,
                identifier: mockInitiatives[0].tasks[2].identifier || '',
                title: 'Update the second task',
                description: 'This is an updated task',
                checklist: []
            },
        ],
    },
    [mockInitiatives[1].identifier]: {
        action: ManagedEntityAction.UPDATE,
        identifier: mockInitiatives[1].identifier, // INIT-246
        title: 'Optimize Dashboard Rendering Speed',
        description: 'Focus on reducing initial load time and improving interaction responsiveness.',

    },
    [mockInitiatives[2].identifier]: {
        action: ManagedEntityAction.DELETE,
        identifier: mockInitiatives[2].identifier, // INIT-247 (Data export)
    },
    'NEW-0': {
        action: ManagedEntityAction.CREATE,
        title: 'New Security Audit Initiative',
        description: 'Perform a full security audit of the backend services and authentication flows.',

        type: "CHORE",

        workspace_identifier: mockWorkspace.id,
        tasks: [
            {
                action: ManagedEntityAction.CREATE,
                title: 'Conduct vulnerability scan',
                description: 'Use automated tools to scan for common vulnerabilities.',
                checklist: []
            },
            {
                action: ManagedEntityAction.CREATE,
                title: 'Manual code review (Auth)',
                description: 'Review authentication and authorization code for potential flaws.',
                checklist: []
            },
        ]
    },
    [mockInitiatives[3].identifier]: {
        action: ManagedEntityAction.UPDATE,
        identifier: mockInitiatives[3].identifier, // INIT-248 (Microservices)
        title: 'Refactor the monolithic backend into microservices focusing on user and auth services first.',
        description: 'Update: Refactor the monolithic backend into microservices focusing on user and auth services first.',
        tasks: [
            {
                action: ManagedEntityAction.DELETE,
                identifier: mockInitiatives[3].tasks[0].identifier || '', // TASK-1142
            },
            {
                action: ManagedEntityAction.UPDATE,
                identifier: mockInitiatives[3].tasks[1].identifier || '', // TASK-1143
                title: 'Implement Service Discovery (Consul)',
                description: 'Implement Service Discovery (Consul)',
                checklist: []
            },
            {
                action: ManagedEntityAction.CREATE,
                title: 'Extract User Service',
                description: 'Create a separate microservice for user management.',
                checklist: []
            }
        ]
    },
}

export const mockTaskImprovements: Record<string, ManagedTaskModel> = {
    [mockTasks[0].identifier]: {
        action: ManagedEntityAction.UPDATE,
        identifier: mockTasks[0].identifier,
        title: mockTasks[0].title + ' some update',
        description: mockTasks[0].description + ' some update',
        checklist: [
            {
                id: 'checklist_id_3o42o42',
                title: 'New checklist item',
                completed: false,
                order: 1,
                task_id: mockTasks[0].id
            },
            ...mockTasks[0].checklist
        ]
    }
}

export const mockAiImprovementsContextReturn: useAiImprovementsContextReturn = {
    setThreadId: mockSetThreadId,
    jobResult: null,
    initiativeImprovements: {},
    taskImprovements: {},
    loading: false,
    error: null,
    isEntityLocked: false,
    deleteJob: mockDeleteJob,
    requestImprovement: mockRequestImprovement,
    updateImprovement: mockUpdateImprovement,
    resetError: mockResetError,
};


export const mockChatMessages: ChatMessage[] = [
    {
        id: '1',
        text: 'I need help planning out the mobile app redesign initiative. Could you help me structure this?',
        sender: 'user',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '2',
        text: 'I\'d be happy to help with planning your mobile app redesign initiative. What are the key objectives you want to achieve with this redesign?',
        sender: 'assistant',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '3',
        text: 'We need to improve user engagement, modernize the UI, and reduce the bounce rate on the checkout flow. Our target is to increase conversions by 15%.',
        sender: 'user',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '4',
        text: 'Great objectives. I recommend breaking this initiative into 4 main phases: Research, Design, Implementation, and Testing. Would you like me to outline the key tasks for each phase?',
        sender: 'assistant',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '5',
        text: 'Yes, please outline the key tasks and also suggest timeframes for each phase.',
        sender: 'user',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '6',
        text: 'Here\'s my proposed breakdown:\n\n**Phase 1: Research (2 weeks)**\n- User surveys and interviews\n- Competitor analysis\n- Analytics review\n- Pain point identification\n\n**Phase 2: Design (3 weeks)**\n- Wireframing\n- Prototyping\n- User testing\n- Design system updates\n\n**Phase 3: Implementation (4 weeks)**\n- Frontend development\n- Backend integration\n- New feature development\n- Performance optimization\n\n**Phase 4: Testing & Launch (3 weeks)**\n- QA testing\n- Beta testing\n- Bug fixes\n- Phased rollout\n\nDoes this timeline work with your Q3 goals?',
        sender: 'assistant',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '7',
        text: 'This is great. We might need to compress the design phase to 2 weeks to meet our deadline. Which tasks would you prioritize if we had to cut some scope?',
        sender: 'user',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '8',
        text: 'If you need to compress the design phase to 2 weeks, I recommend prioritizing:\n\n1. Wireframing the checkout flow specifically (highest impact on conversions)\n2. Rapid prototyping of key screens\n3. Focused user testing on the new checkout experience\n\nYou could streamline the design system updates to cover only components needed for this redesign, and consider a follow-up initiative for a more comprehensive design system overhaul later.',
        sender: 'assistant',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '9',
        text: 'Makes sense. Can you also suggest some key metrics we should track to measure the success of this initiative?',
        sender: 'user',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    },
    {
        id: '10',
        text: (
            '# This is a markdown heading\n\n' + 
            loremIpsum({ count: 6, units: 'sentences' }) +
            '\n\n' +
            '## This is a subheading\n\n' +
            loremIpsum({ count: 6, units: 'sentences' }) +
            '\n\n' +
            '### This is a subsubheading + list\n\n' +
            ' - ' + loremIpsum({ count: 1, units: 'sentences' }) + '\n' +
            ' - ' + loremIpsum({ count: 1, units: 'sentences' }) + '\n' +
            ' - ' + loremIpsum({ count: 1, units: 'sentences' })
        ),
        sender: 'assistant',
        timestamp: new Date(),
        entityId: '101',
        entityTitle: 'Mobile App Redesign Q3',
        entityIdentifier: 'I-201',
        entityType: 'initiative'
    }
]


export const mockTasksAiJobResult: AiImprovementJobResult = {
    id: '1',
    lens: LENS.TASK,
    thread_id: 'thread1',
    status: AiImprovementJobStatus.COMPLETED,
    mode: AgentMode.EDIT,
    input_data: mockTasks,
    error_message: '',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'user-1',
    result_data: {
        message: 'The task has been updated with the new details.',
        managed_tasks: [
            {
                action: ManagedEntityAction.UPDATE,
                identifier: mockTasks[0].identifier,
                title: 'Updated task title',
                description: 'Updated task description',
                checklist: []
            },
            {
                action: ManagedEntityAction.CREATE,
                title: 'New task title',
                description: 'New task description',
                initiative_identifier: mockInitiatives[0].identifier,
                checklist: []
            },
        ]
    },
    messages: [{ role: 'user', content: 'This is the users message', suggested_changes: [] }],
}

export const mockTasksAiJobResultWithError: AiImprovementJobResult = {
    id: '1',
    lens: LENS.TASK,
    thread_id: 'thread1',
    status: AiImprovementJobStatus.FAILED,
    mode: AgentMode.EDIT,
    input_data: mockTasks,
    error_message: 'This is an error message',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'user-1',
    result_data: null,
    messages: [{ role: 'user', content: 'This is the users message', suggested_changes: [] }],
}


export const mockTasksAiJobResultPending: AiImprovementJobResult = {
    id: '1',
    lens: LENS.TASK,
    thread_id: 'thread1',
    status: AiImprovementJobStatus.PENDING,
    mode: AgentMode.EDIT,
    input_data: mockTasks,
    error_message: '',
    result_data: null,
    messages: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'user-1'
}

export const mockInitiativeAiJobResult: AiImprovementJobResult = {
    id: '1',
    lens: LENS.INITIATIVE,
    thread_id: 'thread1',
    status: AiImprovementJobStatus.COMPLETED,
    mode: AgentMode.EDIT,
    input_data: [mockInitiatives[0]],
    error_message: '',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'user-1',
    result_data: {
        message: 'The initiative has been updated with the new details.',
        managed_initiatives: [
            {
                action: ManagedEntityAction.UPDATE,
                identifier: mockInitiatives[0].identifier,
                title: 'Implement CI/CD pipeline',
                description: 'Set up continuous integration and deployment pipeline to automate testing and deployment processes.',

                type: "CHORE",

                tasks: [
                    {
                        action: ManagedEntityAction.CREATE,
                        title: 'Create a new task',
                        description: 'This is a new task',
                        checklist: []
                    },
                    {
                        action: ManagedEntityAction.CREATE,
                        title: 'Create a new task',
                        description: 'This is a new task',
                        checklist: []
                    },
                    {
                        action: ManagedEntityAction.UPDATE,
                        identifier: mockInitiatives[0].tasks[0].identifier || '',
                        title: 'Update the first task',
                        description: 'This is an updated task',
                        checklist: []
                    },
                    {
                        action: ManagedEntityAction.DELETE,
                        identifier: mockInitiatives[0].tasks[1].identifier || '',
                    },
                    {
                        action: ManagedEntityAction.UPDATE,
                        identifier: mockInitiatives[0].tasks[2].identifier || '',
                        title: 'Update the second task',
                        description: 'This is an updated task',
                        checklist: []
                    },
                ],
            }
        ]
    },
    messages: [{ role: 'user', content: 'This is the users message', suggested_changes: [] }],
}

export const mockInitiativesAiJobResult: AiImprovementJobResult = {
    id: '1',
    lens: LENS.INITIATIVE,
    thread_id: 'thread1',
    status: AiImprovementJobStatus.COMPLETED,
    mode: AgentMode.EDIT,
    input_data: mockInitiatives.slice(0, 4),
    error_message: '',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'user-1',
    result_data: {
        message: 'The initiative has been updated with the new details.',
        managed_initiatives: [
            {
                action: ManagedEntityAction.UPDATE,
                identifier: mockInitiatives[0].identifier,
                title: 'Implement CI/CD pipeline',
                description: 'Set up continuous integration and deployment pipeline to automate testing and deployment processes.',

                type: "CHORE",

                tasks: [
                    {
                        action: ManagedEntityAction.CREATE,
                        title: 'Create a new task',
                        description: 'This is a new task',
                        checklist: []
                    },
                    {
                        action: ManagedEntityAction.CREATE,
                        title: 'Create a new task',
                        description: 'This is a new task',
                        checklist: []
                    },
                    {
                        action: ManagedEntityAction.UPDATE,
                        identifier: mockInitiatives[0].tasks[0].identifier || '',
                        title: 'Update the first task',
                        description: 'This is an updated task',
                        checklist: []
                    },
                    {
                        action: ManagedEntityAction.DELETE,
                        identifier: mockInitiatives[0].tasks[1].identifier || '',
                    },
                    {
                        action: ManagedEntityAction.UPDATE,
                        identifier: mockInitiatives[0].tasks[2].identifier || '',
                        title: 'Update the second task',
                        description: 'This is an updated task',
                        checklist: []
                    },
                ],
            },
            {
                action: ManagedEntityAction.UPDATE,
                identifier: mockInitiatives[1].identifier, // INIT-246
                title: 'Optimize Dashboard Rendering Speed',
                description: 'Focus on reducing initial load time and improving interaction responsiveness.',

            },
            {
                action: ManagedEntityAction.DELETE,
                identifier: mockInitiatives[2].identifier, // INIT-247 (Data export)
            },
            {
                action: ManagedEntityAction.CREATE,
                title: 'New Security Audit Initiative',
                description: 'Perform a full security audit of the backend services and authentication flows.',

                type: "CHORE",

                workspace_identifier: mockWorkspace.id,
                tasks: [
                    {
                        action: ManagedEntityAction.CREATE,
                        title: 'Conduct vulnerability scan',
                        description: 'Use automated tools to scan for common vulnerabilities.',
                        checklist: []
                    },
                    {
                        action: ManagedEntityAction.CREATE,
                        title: 'Manual code review (Auth)',
                        description: 'Review authentication and authorization code for potential flaws.',
                        checklist: []
                    },
                ]
            },
            {
                action: ManagedEntityAction.UPDATE,
                identifier: mockInitiatives[3].identifier, // INIT-248 (Microservices)
                description: 'Update: Refactor the monolithic backend into microservices focusing on user and auth services first.',
                tasks: [
                    {
                        action: ManagedEntityAction.DELETE,
                        identifier: mockInitiatives[3].tasks[0].identifier || '', // TASK-1142
                    },
                    {
                        action: ManagedEntityAction.UPDATE,
                        identifier: mockInitiatives[3].tasks[1].identifier || '', // TASK-1143
                        title: 'Implement Service Discovery (Consul)',
                        description: 'Implement Service Discovery (Consul)',
                        checklist: []
                    },
                    {
                        action: ManagedEntityAction.CREATE,
                        title: 'Extract User Service',
                        description: 'Create a separate microservice for user management.',
                        checklist: []
                    }
                ]
            }
        ]
    },
    messages: [{ role: 'user', content: 'This is the users message', suggested_changes: [] }],
}

export const mockInitiativeAiJobResultError: AiImprovementJobResult = {
    id: '1',
    lens: LENS.INITIATIVE,
    thread_id: 'thread1',
    status: AiImprovementJobStatus.FAILED,
    mode: AgentMode.EDIT,
    input_data: [mockInitiatives[0]],
    error_message: 'This is an error message',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'user-1',
    result_data: null,
    messages: [{ role: 'user', content: 'This is the users message', suggested_changes: [] }],
}

export const mockPostInitiative: InitiativeDto = {
    id: '1',
    title: 'Test Initiative',
    description: 'This is a test initiative',
    type: 'FEATURE',
    status: 'TO_DO',

    tasks: [
        {
            id: '1',
            title: 'Test Task',
            description: 'This is a test task',
            status: 'TO_DO',
            checklist: [
                {
                    id: '1',
                    title: 'Test Checklist Item',
                    is_complete: false,
                }
            ]
        }
    ],
    identifier: '',
    user_id: '',



    created_at: '',
    updated_at: '',

    has_pending_job: null,
    workspace: mockWorkspace
}

export const mockPostTask: TaskDto = {
    id: '1',
    title: 'Test Task',
    description: 'This is a test task',
    status: 'TO_DO',
    checklist: [
        {
            id: '1',
            title: 'Test Checklist Item',
            is_complete: false,
        },
    ],
    identifier: 'T-001',
    user_id: mockTasks[0].user_id,


    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),

    initiative_id: mockInitiatives[0].id,
    workspace: mockWorkspace,


    type: 'CODING',


    has_pending_job: null,
}

export const MockContextDocument: ContextDocumentDto = {
    id: '1',
    title: 'ChronoFlow',
    content: `# Project Documentation: ChronoFlow

## 1. Introduction

ChronoFlow is an innovative, AI-enhanced project management platform designed specifically for the unique needs of modern agile software development teams. Traditional project management tools often struggle to adapt to the dynamic nature of agile methodologies, leading to inefficiencies in task prioritization, resource allocation, and overall workflow management. ChronoFlow aims to bridge this gap by leveraging artificial intelligence to provide intelligent insights and automation, empowering teams to deliver high-quality software faster and more reliably. Our core mission is to streamline the development lifecycle, reduce administrative overhead, and foster better collaboration within and across teams.

## 2. Problem Statement

Agile teams face several persistent challenges:
*   **Prioritization Paralysis:** Difficulty in objectively prioritizing tasks based on changing requirements, dependencies, and business value.
*   **Resource Bottlenecks:** Inefficient allocation of developers, designers, and testers, leading to delays and burnout.
*   **Visibility Gaps:** Lack of real-time, holistic views of project progress, potential risks, and team velocity.
*   **Tool Sprawl:** Reliance on multiple disconnected tools for planning, tracking, communication, and reporting, causing context switching and data silos.
*   **Estimation Inaccuracy:** Struggling with accurate effort estimation for tasks, impacting sprint planning and delivery forecasts.

ChronoFlow directly addresses these issues by providing a unified, intelligent platform that learns from project data and team interactions.

## 3. Target Audience

ChronoFlow is primarily targeted at:
*   Agile Software Development Teams (Scrum, Kanban, Scrumban)
*   Project Managers and Scrum Masters
*   Product Owners and Managers
*   Engineering Leads and Managers
*   Software Development Organizations seeking to optimize their agile processes

## 4. Key Features

*   **AI-Powered Task Prioritization:** Analyzes task descriptions, dependencies, historical data, team capacity, and stated business goals to suggest an optimal task order within sprints or backlogs.
*   **Smart Resource Allocation:** Recommends the best-suited team members for specific tasks based on skills, availability, current workload, and past performance on similar tasks. Helps identify potential bottlenecks proactively.
*   **Real-time Progress Tracking:** Visual dashboards (Burndown charts, Cumulative Flow Diagrams, Velocity charts) automatically updated based on task status changes, providing instant insights into sprint and project health.
*   **Integrated Communication Hub:** Centralized discussion threads linked directly to tasks, epics, or sprints, reducing the need for external chat applications for context-specific communication. Includes automated notifications for important updates.
*   **Customizable Workflows:** Allows teams to define and adapt their specific agile workflows (e.g., custom stages in a Kanban board, unique sprint ceremonies checklists).
*   **Predictive Analytics & Reporting:** Generates reports on team velocity, cycle time, lead time, and provides AI-driven forecasts for project completion dates based on current progress and historical trends. Identifies potential risks and suggests mitigation strategies.

## 5. Technology Stack (Planned)

*   **Frontend:** React, TypeScript, Tailwind CSS
*   **Backend:** Node.js (Express.js), Python (for AI services - Flask/FastAPI)
*   **Database:** PostgreSQL (for structured data), Redis (for caching)
*   **AI/ML:** Scikit-learn, TensorFlow/PyTorch (for predictive models)
*   **Infrastructure:** Docker, Kubernetes, AWS/GCP/Azure

## 6. Architecture Overview

ChronoFlow utilizes a microservices architecture. Core services include: User Management, Project Service, Task Service, AI Prioritization Service, Reporting Service, and Notification Service. Communication between services happens via REST APIs and potentially an event bus (like Kafka or RabbitMQ) for asynchronous operations. This allows for scalability, resilience, and independent development/deployment of features.

## 7. Future Enhancements

*   **CI/CD Integration:** Direct integration with popular CI/CD tools (Jenkins, GitLab CI, GitHub Actions) to link deployments to tasks and releases.
*   **Advanced Risk Assessment:** More sophisticated AI models to identify complex inter-dependency risks and resource conflicts earlier.
*   **Cross-Project Portfolio Management:** Features for managing dependencies and resources across multiple related projects.
*   **Automated Meeting Facilitation:** AI assistance in scheduling and summarizing key agile ceremonies like stand-ups and retrospectives.
`,
    created_at: '2021-01-01',
    updated_at: '2021-01-01'
};

const mockUpdateContextDocument = async (contextDocument: ContextDocumentDto) => {
    console.log('updateContextDocument', contextDocument);
    await sleep(1000);
    return Promise.resolve(contextDocument);
}

export const mockContextDocumentReturn: UseContextDocumentReturn = {
    contextDocument: MockContextDocument,
    updateContextDocument: mockUpdateContextDocument,
    isLoadingContextDocument: false,
    errorContextDocument: null,
};

export const mockCreateFieldDefinition = async () => {
    console.log('mockCreateFieldDefinition');
    await sleep(1000);
    return Promise.resolve(mockAllFieldDefinitions[0]);
}
export const mockUpdateFieldDefinition = async () => {
    console.log('mockUpdateFieldDefinition');
    await sleep(1000);
    return Promise.resolve(mockAllFieldDefinitions[0]);
}
export const mockDeleteFieldDefinition = async () => {
    console.log('mockDeleteFieldDefinition');
    await sleep(1000);
    return Promise.resolve();
}
export const mockInvalidateQuery = async () => {
    console.log('mockInvalidateQuery');
    await sleep(1000);
}

export const mockAllFieldDefinitions: FieldDefinitionDto[] = [
    { ...initiativeStatusFieldDefinition, id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a9', workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0' },
    { ...initiativeTypeFieldDefinition, id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a2', workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0' },
    { ...taskStatusFieldDefinition, id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a3', workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0' },
    { ...taskTypeFieldDefinition, id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a4', workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0' },
    {
        field_type: FieldType.TEXT,
        id: '8f7d7d5d-d940-4b12-a85a-7c11c3e3b8a1',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'description_field',
        name: 'Description Field',
        is_core: false,
        column_name: 'description_field',
        config: { maxLength: 1000, addToAllInitiatives: true },
        created_at: '2024-03-20T10:00:00.000Z',
        updated_at: '2024-03-20T10:00:00.000Z'
    },
    {
        field_type: FieldType.NUMBER,
        id: '9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'story_points',
        name: 'Story Points',
        is_core: false,
        column_name: 'story_points',
        config: { precision: 0, min: 0, max: 100 },
        created_at: '2024-03-20T10:01:00.000Z',
        updated_at: '2024-03-20T10:01:00.000Z'
    },
    {
        field_type: FieldType.SELECT,
        id: 'b1c2d3e4-f5g6-7h8i-9j0k-l1m2n3o4p5q6',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'priority',
        name: 'Priority',
        is_core: false,
        column_name: 'priority',
        config: {
            options: [
                'Low',
                'Medium',
                'High'
            ],
            addToAllInitiatives: true
        },
        created_at: '2024-03-20T10:02:00.000Z',
        updated_at: '2024-03-20T10:02:00.000Z'
    },
    {
        field_type: FieldType.MULTI_SELECT,
        id: 'c2d3e4f5-g6h7-i8j9-k0l1-m2n3o4p5q6r7',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'tags',
        name: 'Tags',
        is_core: false,
        column_name: 'tags',
        config: {
            options: [
                'Frontend',
                'Backend',
                'Design',
                'Testing'
            ]
        },
        created_at: '2024-03-20T10:03:00.000Z',
        updated_at: '2024-03-20T10:03:00.000Z'
    },
    {
        field_type: FieldType.DATE,
        id: 'e4f5g6h7-i8j9-k0l1-m2n3-o4p5q6r7s8t9',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'due_date',
        name: 'Due Date',
        is_core: false,
        column_name: 'due_date',
        config: { includeTime: true },
        created_at: '2024-03-20T10:05:00.000Z',
        updated_at: '2024-03-20T10:05:00.000Z'
    },
    {
        field_type: FieldType.CHECKBOX,
        id: 'f5g6h7i8-j9k0-l1m2-n3o4-p5q6r7s8t9u0',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'is_blocked',
        name: 'Is Blocked',
        is_core: false,
        column_name: 'is_blocked',
        config: { defaultValue: false },
        created_at: '2024-03-20T10:06:00.000Z',
        updated_at: '2024-03-20T10:06:00.000Z'
    },
    {
        field_type: FieldType.URL,
        id: 'g6h7i8j9-k0l1-m2n3-o4p5-q6r7s8t9u0v1',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'documentation_link',
        name: 'Documentation Link',
        is_core: false,
        column_name: 'documentation_link',
        config: { validateUrl: true },
        created_at: '2024-03-20T10:07:00.000Z',
        updated_at: '2024-03-20T10:07:00.000Z'
    },
    {
        field_type: FieldType.EMAIL,
        id: 'h7i8j9k0-l1m2-n3o4-p5q6-r7s8t9u0v1w2',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'contact_email',
        name: 'Contact Email',
        is_core: false,
        column_name: 'contact_email',
        config: { validateEmail: true },
        created_at: '2024-03-20T10:08:00.000Z',
        updated_at: '2024-03-20T10:08:00.000Z'
    },
    {
        field_type: FieldType.PHONE,
        id: 'i8j9k0l1-m2n3-o4p5-q6r7-s8t9u0v1w2x3',
        workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
        entity_type: EntityType.INITIATIVE,
        key: 'contact_phone',
        name: 'Contact Phone',
        is_core: false,
        column_name: 'contact_phone',
        config: { format: '+1 (###) ###-####' },
        created_at: '2024-03-20T10:09:00.000Z',
        updated_at: '2024-03-20T10:09:00.000Z'
    }
];

export const mockFieldDefinitionsReturn = {
    fieldDefinitions: mockAllFieldDefinitions,
    loading: false,
    error: null,
    createFieldDefinition: mockCreateFieldDefinition,
    updateFieldDefinition: mockUpdateFieldDefinition,
    deleteFieldDefinition: mockDeleteFieldDefinition,
    invalidateQuery: mockInvalidateQuery
};

export const mockGroups: GroupDto[] = [
    {
        id: '1',
        name: 'Getting to Launch',
        description: 'The minimum set of initiatives to get to launch',
        group_type: GroupType.EXPLICIT,
        user_id: '1',
        query_criteria: null,
        initiatives: mockInitiatives.slice(0, 2),
        workspace_id: 'workspace-1',
        group_metadata: {},
        parent_group_id: null
    },
    {
        id: '2',
        group_type: GroupType.SMART,
        user_id: '1',
        workspace_id: 'workspace-1',
        name: 'All Bugs',
        description: '',
        query_criteria: {
            type: "BUGFIX"
        },
        initiatives: mockInitiatives.slice(3, 6),
        group_metadata: null,
        parent_group_id: null
    }
];

export const mockRefetchInitiativeGroups = async () => {
    console.log('refetching initiative groups');
    await sleep(1000);
};

export const mockDeleteGroup = async () => {
    console.log(`Deleting group ${mockGroups[0].id}`);
    await sleep(1000);
    return Promise.resolve();
};

export const mockUpdateGroup = async () => {
    console.log(`Updating group ${mockGroups[0].id}`);
    await sleep(1000);
    return Promise.resolve(mockGroups[0]);
};

export const mockCreateExplicitGroup = async () => {
    console.log(`Creating explicit group ${mockGroups[0].id}`);
    await sleep(1000);
    return Promise.resolve(mockGroups[0]);
};

export const mockAddInitiativeToExplicitGroup = async () => {
    console.log(`Adding initiative to explicit group ${mockGroups[0].id}`);
    await sleep(1000);
    return Promise.resolve(mockGroups[0]);
};

export const mockRemoveInitiativeFromExplicitGroup = async () => {
    console.log(`Removing initiative from explicit group ${mockGroups[0].id}`);
    await sleep(1000);
    return Promise.resolve(mockGroups[0]);
};

export const mockCreateNewSmartGroup = async () => {
    console.log(`Creating new smart group ${mockGroups[0].id}`);
    await sleep(1000);
    return Promise.resolve(mockGroups[0]);
};

export const mockUpdateSmartGroup = async () => {
    console.log(`Updating smart group ${mockGroups[0].id}`);
    await sleep(1000);
    return Promise.resolve({ ...mockGroups[0], initiatives: [] });
};

export const mockFindGroupsByIds = (ids: string[]) => {
    console.log(`Finding groups by ids ${ids.join(', ')}`);
    return mockGroups.filter(group => ids.includes(group.id)).map(group => ({
        ...group,
        initiatives: []
    }));
}

export const mockRefetchGroups = () => {
    console.log('mock refetch groups')
    return Promise.resolve()
}
export const mockInitiativeGroupsReturn: UseInitiativeGroupsReturn = {
    allGroupsInWorkspace: mockGroups.map(group => ({
        ...group,
        initiatives: [] as OrderedEntity<InitiativeDto>[]
    })),
    loading: false,
    error: null,
    deleteGroup: mockDeleteGroup,
    updateGroup: mockUpdateGroup,
    createNewExplicitGroup: mockCreateExplicitGroup,
    addInitiativeToExplicitGroup: mockAddInitiativeToExplicitGroup,
    removeInitiativeFromExplicitGroup: mockRemoveInitiativeFromExplicitGroup,
    createNewSmartGroup: mockCreateNewSmartGroup,
    updateSmartGroup: mockUpdateSmartGroup,
    findGroupsByIds: mockFindGroupsByIds,
    refetchGroups: mockRefetchGroups,
};

export const mockSetActiveInitiative = (initiativeId: string | null) => {
    console.log('setting active initiative', initiativeId);
}
export const mockSetActiveTask = (taskId: string | null) => {
    console.log('setting active task', taskId);
}
export const mockClearActiveEntity = () => {
    console.log('clearing active entity');
}

export const mockActiveEntityReturn: UseActiveEntityReturn = {
    activeInitiativeId: mockInitiatives[0].id,
    activeTaskId: null,
    recentInitiatives: [],
    setActiveInitiative: mockSetActiveInitiative,
    setActiveTask: mockSetActiveTask,
    clearActiveEntity: mockClearActiveEntity
};


export const mockUseEntityFromUrlReturn: useEntityFromUrlReturn = {
    lens: LENS.INITIATIVE,
    initiativeId: mockInitiatives[0].id,
    taskId: null,
    initiativeData: mockInitiatives[0],
    taskData: null,
    currentEntity: mockInitiatives[0]
}

export const mockUpdateOrderingPosition = async (ordering: { orderingId: string; position: string; contextType?: ContextType }) => {
    console.log(`Updating ordering position ${ordering.orderingId} to ${ordering.position} for context type ${ordering.contextType}`);
    await sleep(1000);
    return Promise.resolve({
        id: ordering.orderingId,
        position: ordering.position,
        contextType: ordering.contextType,
        entityType: EntityType.INITIATIVE,
    } as OrderingDto);
}

export const mockBillingUsageReturn: BillingUsageData = {
    currentBalance: 25.50,
    transactions: [
        { id: 1, date: '2024-01-15', type: 'Top-up', amount: 50 },
        { id: 2, date: '2024-01-14', type: 'Usage', amount: -0.00532 },
        { id: 3, date: '2024-01-13', type: 'Usage', amount: -0.00421 },
        { id: 4, date: '2024-01-12', type: 'Usage', amount: -0.00789 },
        { id: 5, date: '2024-01-11', type: 'Top-up', amount: 25 },
        { id: 6, date: '2024-01-10', type: 'Usage', amount: -0.00334 },
        { id: 7, date: '2024-01-09', type: 'Usage', amount: -0.00567 },
        { id: 8, date: '2024-01-08', type: 'Usage', amount: -0.00234 },
        { id: 9, date: '2024-01-07', type: 'Usage', amount: -0.00678 },
        { id: 10, date: '2024-01-06', type: 'Top-up', amount: 100 },
        { id: 11, date: '2024-01-05', type: 'Usage', amount: -0.00445 },
        { id: 12, date: '2024-01-04', type: 'Usage', amount: -0.00556 },
        { id: 13, date: '2024-01-03', type: 'Usage', amount: -0.00323 },
        { id: 14, date: '2024-01-02', type: 'Usage', amount: -0.00789 },
        { id: 15, date: '2024-01-01', type: 'Top-up', amount: 75 },
        { id: 16, date: '2023-12-31', type: 'Usage', amount: -0.00234 },
        { id: 17, date: '2023-12-30', type: 'Usage', amount: -0.00567 },
        { id: 18, date: '2023-12-29', type: 'Usage', amount: -0.00345 },
        { id: 19, date: '2023-12-28', type: 'Refund', amount: 10 },
        { id: 20, date: '2023-12-27', type: 'Usage', amount: -0.00678 }
    ],
    transactionsPagination: {
        totalCount: 45,
        page: 1,
        pageSize: 20,
        hasNext: true
    },
    subscriptionStatus: UserAccountStatus.ACTIVE_SUBSCRIPTION,
    monthlyCreditsTotal: 500,
    monthlyCreditsUsed: 200
};

const mockSetAutoTopUp = (v: boolean) => {
    console.log(`setAutoTopUp: ${v}`);
};

const mockHandleAddCredit = async () => {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    console.log(`handleAddCredit`);
};

const mockFormatCurrency = (amount: number) => `$${amount}`;
const mockFormatNumber = (num: number) => `${num}`;

const mockOnboardCustomer = () => {
    console.log(`onboardCustomer`);
};

const mockSetupMonthlySubscription = async () => {
    console.log(`setupMonthlySubscription`);
    return Promise.resolve();
};

const mockHandleOpenCustomerPortal = async () => {
    console.log(`handleOpenCustomerPortal`);
    await new Promise((resolve) => setTimeout(resolve, 3000));
    return Promise.resolve();
};

export const mockUseBillingUsageReturn: UseBillingUsageReturn = {
    data: mockBillingUsageReturn,
    userAccountDetails: {
        balanceCents: 1500,
        status: UserAccountStatus.ACTIVE_SUBSCRIPTION,
        onboardingCompleted: true,
        monthlyCreditsTotal: 500,
        monthlyCreditsUsed: 200
    },
    userIsOnboarded: true,
    autoTopUp: false,
    isLoading: false,
    isAccountDetailsLoading: false,
    error: null,
    setAutoTopUp: mockSetAutoTopUp,
    handleAddCredit: mockHandleAddCredit,
    formatCurrency: mockFormatCurrency,
    formatNumber: mockFormatNumber,
    onboardCustomer: mockOnboardCustomer,
    setupMonthlySubscription: mockSetupMonthlySubscription,
    // Payment dialog states
    showErrorDialog: false,
    showPendingDialog: false,
    showCancelledDialog: false,
    closeErrorDialog: () => console.log('closeErrorDialog'),
    closePendingDialog: () => console.log('closePendingDialog'),
    closeCancelledDialog: () => console.log('closeCancelledDialog'),
    handlePaymentRetry: () => console.log('handlePaymentRetry'),
    handlePaymentSuccess: () => console.log('handlePaymentSuccess'),
    handlePaymentFailure: () => console.log('handlePaymentFailure'),
    handleRefundRequest: () => {
        console.log('handleRefundRequest');
        return Promise.resolve({ success: true, details: null });
    },
    handleOpenCustomerPortal: mockHandleOpenCustomerPortal,
    loadTransactionsPage: () => {
        console.log('loadMoreTransactions');
    },
    resetTransactionsPagination: () => {
        console.log('resetTransactionsPagination');
    },
    invalidateUserAccountDetails: async () => {
        console.log('invalidateUserAccountDetails')
        return Promise.resolve();
    }
};

export const mockUseBillingUsageReturnNewUser: UseBillingUsageReturn = {
    ...mockUseBillingUsageReturn,
    userIsOnboarded: true,
    data: {
        currentBalance: 0,
        transactions: [],
        transactionsPagination: null,
        subscriptionStatus: UserAccountStatus.ACTIVE_SUBSCRIPTION,
        monthlyCreditsTotal: 500,
        monthlyCreditsUsed: 0
    },
    userAccountDetails: {
        balanceCents: 0,
        status: UserAccountStatus.NEW,
        onboardingCompleted: true,
        monthlyCreditsTotal: 500,
        monthlyCreditsUsed: 0
    }
};


const mockSendMessage = (threadId: string, messages: AiJobChatMessage[], lens: LENS, mode: AgentMode) => {
    console.log('mock send message')
}

export const mockUseAiChatReturn: useAiChatReturn = {
    jobResult: null,
    error: null,
    chatDisabled: false,
    sendMessage: mockSendMessage,
    clearChat: () => { },
    currentContext: [],
    setCurrentContext: (context: any) => { },
    removeEntityFromContext: (entityId: string) => { },
}

export const mockSuggestionsToBeResolvedContextReturn: UseSuggestionsToBeResolvedReturn = {
    suggestions: [],
    fieldSuggestions: [],
    entitySuggestions: [],
    resolutions: {},
    allResolved: false,
    resolve: () => {},
    rollback: () => {},
    acceptAll: () => {},
    rejectAll: () => {},
    rollbackAll: () => {},
    getResolutionState: () => ({
        isResolved: false,
        isAccepted: false,
        resolvedValue: null
    }),
    isFullyResolved: () => false,
    getAcceptedChanges: () => [],
    saveSuggestions: () => Promise.resolve(),
}
