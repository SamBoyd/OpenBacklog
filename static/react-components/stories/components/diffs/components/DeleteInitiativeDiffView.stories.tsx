// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { InitiativeDto, TaskStatus } from '#types';
import { DeleteInitiativeDiffView } from '#components/diffs/DeleteInitiativeDiffView';
import { mockWorkspace } from '#stories/example_data';

const meta: Meta<typeof DeleteInitiativeDiffView> = {
    title: 'Components/Diffs/Components/DeleteInitiativeDiffView',
    component: DeleteInitiativeDiffView,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof DeleteInitiativeDiffView>;


// Mock initiative data for deletion
const mockDeleteInitiativeData: InitiativeDto = {
    id: 'initiative-1',
    identifier: 'I-245',
    user_id: 'user-1',
    title: 'Legacy system migration',
    description: 'Migrate the legacy system to the new architecture. This includes database migration, API updates, and frontend component updates. The project involves significant refactoring and testing.',
    type: 'CHORE',
    status: TaskStatus.TO_DO,
    created_at: '2025-01-15T10:30:00.000000',
    updated_at: '2025-01-15T10:30:00.000001',
    tasks: [],
    has_pending_job: null,
    workspace: mockWorkspace,
};

const mockSimpleInitiative: InitiativeDto = {
    id: 'initiative-2',
    identifier: 'I-246',
    user_id: 'user-1',
    title: 'Fix login bug',
    description: 'Simple bug fix for login issues.',
    type: 'BUG',
    status: TaskStatus.IN_PROGRESS,
    created_at: '2025-01-16T10:30:00.000000',
    updated_at: '2025-01-16T10:30:00.000001',
    tasks: [],
    has_pending_job: null,
    workspace: mockWorkspace,
};

const mockComplexInitiative: InitiativeDto = {
    id: 'initiative-3',
    identifier: 'I-247',
    user_id: 'user-1',
    title: 'Complete system architecture overhaul',
    description: `This is a comprehensive initiative that involves:

## Phase 1: Planning and Analysis
- Assess current system architecture
- Identify bottlenecks and pain points  
- Create migration strategy

## Phase 2: Core Infrastructure
- Migrate database to new schema
- Implement caching layers
- Update API architecture

## Phase 3: Frontend Modernization
- Upgrade React components
- Implement responsive design
- Add accessibility features

## Phase 4: Testing and Deployment
- Comprehensive testing suite
- Gradual rollout strategy
- Performance monitoring

This initiative is expected to take 6 months and will significantly improve system performance and maintainability.`,
    type: 'FEATURE',
    status: TaskStatus.DONE,
    created_at: '2025-01-10T10:30:00.000000',
    updated_at: '2025-01-20T10:30:00.000001',
    tasks: [],
    has_pending_job: null,
    workspace: mockWorkspace,
};

const mockEmptyDescriptionInitiative: InitiativeDto = {
    id: 'initiative-4',
    identifier: 'I-248',
    user_id: 'user-1',
    title: 'Initiative without description',
    description: '',
    type: 'CHORE',
    status: TaskStatus.TO_DO,
    created_at: '2025-01-17T10:30:00.000000',
    updated_at: '2025-01-17T10:30:00.000001',
    tasks: [],
    has_pending_job: null,
    workspace: mockWorkspace,
};

export const Primary: Story = {
    args: {
        initiativeData: mockDeleteInitiativeData,
        onAccept: () => console.log('Delete initiative accepted'),
        onReject: () => console.log('Delete initiative rejected'),
        onRollback: () => console.log('Delete initiative rolled back'),
        isResolved: false,
        accepted: null,
    },
};

export const SimpleInitiative: Story = {
    args: {
        initiativeData: mockSimpleInitiative,
        onAccept: () => console.log('Delete simple initiative accepted'),
        onReject: () => console.log('Delete simple initiative rejected'),
        onRollback: () => console.log('Delete simple initiative rolled back'),
        isResolved: false,
        accepted: null,
    },
};

export const ComplexInitiative: Story = {
    args: {
        initiativeData: mockComplexInitiative,
        onAccept: () => console.log('Delete complex initiative accepted'),
        onReject: () => console.log('Delete complex initiative rejected'),
        onRollback: () => console.log('Delete complex initiative rolled back'),
        isResolved: false,
        accepted: null,
    },
};

export const EmptyDescription: Story = {
    args: {
        initiativeData: mockEmptyDescriptionInitiative,
        onAccept: () => console.log('Delete empty description initiative accepted'),
        onReject: () => console.log('Delete empty description initiative rejected'),
        onRollback: () => console.log('Delete empty description initiative rolled back'),
        isResolved: false,
        accepted: null,
    },
};

export const ResolvedAccepted: Story = {
    args: {
        initiativeData: mockDeleteInitiativeData,
        onAccept: () => console.log('Resolved delete accepted'),
        onReject: () => console.log('Resolved delete rejected'),
        onRollback: () => console.log('Resolved delete rolled back'),
        isResolved: true,
        accepted: true,
    },
};

export const ResolvedRejected: Story = {
    args: {
        initiativeData: mockDeleteInitiativeData,
        onAccept: () => console.log('Resolved delete accepted'),
        onReject: () => console.log('Resolved delete rejected'),
        onRollback: () => console.log('Resolved delete rolled back'),
        isResolved: true,
        accepted: false,
    },
};