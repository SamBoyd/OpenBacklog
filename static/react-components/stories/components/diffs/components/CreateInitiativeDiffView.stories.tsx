// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { CreateInitiativeModel, ManagedEntityAction } from '#types';
import CreateInitiativeDiffView from '#components/diffs/CreateInitiativeDiffView';

const meta: Meta<typeof CreateInitiativeDiffView> = {
    title: 'Components/Diffs/Components/CreateInitiativeDiffView',
    component: CreateInitiativeDiffView,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof CreateInitiativeDiffView>;

// Mock initiative data for creation
const mockCreateInitiativeData: CreateInitiativeModel = {
    action: ManagedEntityAction.CREATE,
    title: 'Implement user notification system',
    description: 'Design and implement a comprehensive user notification system that supports email, in-app notifications, and push notifications. This system will handle user preferences, delivery scheduling, and notification history tracking.',
    type: 'FEATURE',
    workspace_identifier: 'workspace-1',
};

const mockSimpleInitiative: CreateInitiativeModel = {
    action: ManagedEntityAction.CREATE,
    title: 'Fix login bug',
    description: 'Users are experiencing issues with the login process.',
    type: 'BUG',
    workspace_identifier: 'workspace-1',
};

const mockComplexInitiative: CreateInitiativeModel = {
    action: ManagedEntityAction.CREATE,
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
    type: 'CHORE',
    workspace_identifier: 'workspace-1',
};

const mockEmptyDescription: CreateInitiativeModel = {
    action: ManagedEntityAction.CREATE,
    title: 'Initiative without description',
    description: '',
    type: 'FEATURE',
    workspace_identifier: 'workspace-1',
};

export const Primary: Story = {
    args: {
        initiativeData: mockCreateInitiativeData,
        onAccept: () => console.log('Create initiative accepted'),
        onReject: () => console.log('Create initiative rejected'),
        onRollback: () => console.log('Create initiative rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const SimpleInitiative: Story = {
    args: {
        initiativeData: mockSimpleInitiative,
        onAccept: () => console.log('Simple initiative accepted'),
        onReject: () => console.log('Simple initiative rejected'),
        onRollback: () => console.log('Simple initiative rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const ComplexInitiative: Story = {
    args: {
        initiativeData: mockComplexInitiative,
        onAccept: () => console.log('Complex initiative accepted'),
        onReject: () => console.log('Complex initiative rejected'),
        onRollback: () => console.log('Complex initiative rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const EmptyDescription: Story = {
    args: {
        initiativeData: mockEmptyDescription,
        onAccept: () => console.log('Empty description accepted'),
        onReject: () => console.log('Empty description rejected'),
        onRollback: () => console.log('Empty description rolled back'),
        isResolved: false,
        accepted: false,
    },
};

export const ResolvedAccepted: Story = {
    args: {
        initiativeData: mockCreateInitiativeData,
        onAccept: () => console.log('Resolved initiative accepted'),
        onReject: () => console.log('Resolved initiative rejected'),
        onRollback: () => console.log('Resolved initiative rolled back'),
        isResolved: true,
        accepted: true,
    },
};

export const ResolvedRejected: Story = {
    args: {
        initiativeData: mockCreateInitiativeData,
        onAccept: () => console.log('Resolved initiative accepted'),
        onReject: () => console.log('Resolved initiative rejected'),
        onRollback: () => console.log('Resolved initiative rolled back'),
        isResolved: true,
        accepted: false,
    },
};