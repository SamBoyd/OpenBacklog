import type { Meta, StoryObj } from '@storybook/react';
import VillainCard from '#components/Narrative/VillainCard';
import { VillainDto, VillainType } from '#types';

// Mock villain data
const mockVillainExternal: VillainDto = {
    id: '650e8400-e29b-41d4-a716-446655440001',
    identifier: 'V-2001',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Competing AI Agents',
    villain_type: VillainType.EXTERNAL,
    description: 'Third-party AI agents that are rapidly improving and gaining market share, threatening our competitive advantage in product context awareness.',
    severity: 4,
    is_defeated: false,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockVillainTechnical: VillainDto = {
    id: '650e8400-e29b-41d4-a716-446655440002',
    identifier: 'V-2002',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Database Performance Bottleneck',
    villain_type: VillainType.TECHNICAL,
    description: 'Slow database queries on large workspaces are causing timeouts and poor user experience. Affects real-time narrative retrieval.',
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

const mockVillainInternal: VillainDto = {
    id: '650e8400-e29b-41d4-a716-446655440004',
    identifier: 'V-2004',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Lack of Context Awareness',
    villain_type: VillainType.INTERNAL,
    description: 'AI assistants lack sufficient product context to make informed decisions, leading to irrelevant suggestions and manual corrections.',
    severity: 4,
    is_defeated: false,
    created_at: '2025-01-18T11:00:00Z',
    updated_at: '2025-01-18T11:00:00Z',
};

const mockVillainDefeated: VillainDto = {
    id: '650e8400-e29b-41d4-a716-446655440005',
    identifier: 'V-2005',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Manual Task Tracking',
    villain_type: VillainType.WORKFLOW,
    description: 'The old system required manual tracking of task progress across multiple spreadsheets, causing errors and delays.',
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
    description: 'Small visual inconsistencies in the UI that are minor but could be polished.',
    severity: 1,
    is_defeated: false,
    created_at: '2025-01-20T15:00:00Z',
    updated_at: '2025-01-20T15:00:00Z',
};

const meta: Meta<typeof VillainCard> = {
    title: 'Components/Narrative/VillainCard',
    component: VillainCard,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        villain: {
            description: 'The villain object to display',
        },
        onClick: {
            action: 'clicked',
            description: 'Callback when card is clicked',
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
            <div className="w-96 p-4">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof VillainCard>;

/**
 * Critical severity villain (TECHNICAL type).
 */
export const CriticalVillain: Story = {
    args: {
        villain: mockVillainTechnical,
        dataTestId: 'villain-card-critical',
    },
};

/**
 * High severity villain (WORKFLOW type).
 */
export const HighSeverityVillain: Story = {
    args: {
        villain: mockVillainWorkflow,
        dataTestId: 'villain-card-high',
    },
};

/**
 * External villain (EXTERNAL type).
 */
export const ExternalVillain: Story = {
    args: {
        villain: mockVillainExternal,
        dataTestId: 'villain-card-external',
    },
};

/**
 * Internal villain (INTERNAL type).
 */
export const InternalVillain: Story = {
    args: {
        villain: mockVillainInternal,
        dataTestId: 'villain-card-internal',
    },
};

/**
 * Defeated villain with DEFEATED badge.
 */
export const DefeatedVillain: Story = {
    args: {
        villain: mockVillainDefeated,
        dataTestId: 'villain-card-defeated',
    },
};

/**
 * Low severity villain.
 */
export const LowSeverityVillain: Story = {
    args: {
        villain: mockVillainLow,
        dataTestId: 'villain-card-low',
    },
};

/**
 * Clickable villain card.
 */
export const Clickable: Story = {
    args: {
        villain: mockVillainWorkflow,
        onClick: () => console.log('Villain card clicked!'),
        dataTestId: 'villain-card-clickable',
    },
};

/**
 * Multiple villain cards with different types and severities.
 */
export const AllVillainTypes: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <div>
                <h3 className="text-sm font-semibold text-foreground mb-2">EXTERNAL</h3>
                <VillainCard villain={mockVillainExternal} />
            </div>
            <div>
                <h3 className="text-sm font-semibold text-foreground mb-2">INTERNAL</h3>
                <VillainCard villain={mockVillainInternal} />
            </div>
            <div>
                <h3 className="text-sm font-semibold text-foreground mb-2">TECHNICAL</h3>
                <VillainCard villain={mockVillainTechnical} />
            </div>
            <div>
                <h3 className="text-sm font-semibold text-foreground mb-2">WORKFLOW</h3>
                <VillainCard villain={mockVillainWorkflow} />
            </div>
            <div>
                <h3 className="text-sm font-semibold text-foreground mb-2">DEFEATED</h3>
                <VillainCard villain={mockVillainDefeated} />
            </div>
        </div>
    ),
    decorators: [
        (Story) => (
            <div className="w-96 p-4">
                <Story />
            </div>
        ),
    ],
};
