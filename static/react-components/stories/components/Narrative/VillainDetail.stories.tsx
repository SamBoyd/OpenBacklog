import type { Meta, StoryObj } from '@storybook/react';
import VillainDetail from '#components/Narrative/VillainDetail';
import { VillainDto, VillainType } from '#types';

// Mock villain data
const mockVillainTechnical: VillainDto = {
    id: '650e8400-e29b-41d4-a716-446655440002',
    identifier: 'V-2002',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Database Performance Bottleneck',
    villain_type: VillainType.TECHNICAL,
    description: 'Slow database queries on large workspaces are causing timeouts and poor user experience. Affects real-time narrative retrieval. The issue stems from inefficient joins and missing indexes on the conflicts and heroes tables. This impacts both API response times and MCP tool latency.',
    severity: 5,
    is_defeated: false,
    created_at: '2025-01-16T14:30:00Z',
    updated_at: '2025-01-16T14:30:00Z',
};

const mockVillainWorkflow: VillainDto = {
    id: '650e8400-e29b-41d4-a716-446655440003',
    identifier: 'V-2003',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Context Switching Between Tools',
    villain_type: VillainType.WORKFLOW,
    description: 'Users must constantly jump between IDE, planning tools, and documentation, breaking their flow state and reducing productivity.',
    severity: 5,
    is_defeated: false,
    created_at: '2025-01-17T09:00:00Z',
    updated_at: '2025-01-17T09:00:00Z',
};

const mockVillainDefeated: VillainDto = {
    id: '650e8400-e29b-41d4-a716-446655440005',
    identifier: 'V-2005',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Manual Task Tracking',
    villain_type: VillainType.WORKFLOW,
    description: 'The old system required manual tracking of task progress across multiple spreadsheets, causing errors and delays. This was defeated by implementing automated status tracking and real-time synchronization.',
    severity: 3,
    is_defeated: true,
    created_at: '2025-01-19T08:00:00Z',
    updated_at: '2025-01-19T08:00:00Z',
};

const mockVillainLow: VillainDto = {
    id: '650e8400-e29b-41d4-a716-446655440006',
    identifier: 'V-2006',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Minor UI Inconsistencies',
    villain_type: VillainType.OTHER,
    description: 'Small visual inconsistencies in the UI that are minor but could be polished for a better user experience.',
    severity: 1,
    is_defeated: false,
    created_at: '2025-01-20T15:00:00Z',
    updated_at: '2025-01-20T15:00:00Z',
};

const meta: Meta<typeof VillainDetail> = {
    title: 'Components/Narrative/VillainDetail',
    component: VillainDetail,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        villain: {
            description: 'The villain object to display',
        },
        loading: {
            control: 'boolean',
            description: 'Loading state',
        },
        error: {
            control: 'text',
            description: 'Error message if any',
        },
        onDelete: {
            action: 'deleted',
            description: 'Callback when delete is clicked',
        },
        onRefresh: {
            action: 'refreshed',
            description: 'Callback when refresh is clicked',
        },
        className: {
            control: 'text',
            description: 'Additional CSS classes',
        },
        dataTestId: {
            control: 'text',
            description: 'Test ID for testing',
        },
    },
    decorators: [
        (Story) => (
            <div className="w-full max-w-2xl">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof VillainDetail>;

/**
 * Critical severity villain (TECHNICAL type) - fully populated.
 */
export const CriticalVillain: Story = {
    args: {
        villain: mockVillainTechnical,
        loading: false,
        error: null,
        dataTestId: 'villain-detail-critical',
    },
};

/**
 * High severity villain (WORKFLOW type).
 */
export const HighSeverityVillain: Story = {
    args: {
        villain: mockVillainWorkflow,
        loading: false,
        error: null,
        dataTestId: 'villain-detail-high',
    },
};

/**
 * Defeated villain showing success state.
 */
export const DefeatedVillain: Story = {
    args: {
        villain: mockVillainDefeated,
        loading: false,
        error: null,
        dataTestId: 'villain-detail-defeated',
    },
};

/**
 * Low severity villain.
 */
export const LowSeverityVillain: Story = {
    args: {
        villain: mockVillainLow,
        loading: false,
        error: null,
        dataTestId: 'villain-detail-low',
    },
};

/**
 * Loading state.
 */
export const Loading: Story = {
    args: {
        villain: null,
        loading: true,
        error: null,
        dataTestId: 'villain-detail-loading',
    },
};

/**
 * Empty state (no villain data).
 */
export const Empty: Story = {
    args: {
        villain: null,
        loading: false,
        error: null,
        dataTestId: 'villain-detail-empty',
    },
};

/**
 * Error state.
 */
export const Error: Story = {
    args: {
        villain: null,
        loading: false,
        error: 'Failed to load villain data. Please try again.',
        dataTestId: 'villain-detail-error',
    },
};

/**
 * With interactive callbacks.
 */
export const Interactive: Story = {
    args: {
        villain: mockVillainTechnical,
        loading: false,
        error: null,
        onDelete: () => console.log('Delete villain'),
        onRefresh: () => console.log('Refresh villain'),
        dataTestId: 'villain-detail-interactive',
    },
};
