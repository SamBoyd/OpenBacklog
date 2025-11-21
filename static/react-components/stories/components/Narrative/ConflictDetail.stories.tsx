import type { Meta, StoryObj } from '@storybook/react';
import ConflictDetail from '#components/Narrative/ConflictDetail';
import { ConflictDto, ConflictStatus, HeroDto, VillainDto, VillainType } from '#types';

// Mock data
const mockHero: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440001',
    identifier: 'H-2003',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Sarah Chen',
    description: 'Senior Product Manager at a fast-growing SaaS company. Manages a team of 5 and oversees product strategy for the core platform.',
    is_primary: true,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockVillain: VillainDto = {
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

const mockConflictOpen: ConflictDto = {
    id: '750e8400-e29b-41d4-a716-446655440001',
    identifier: 'C-2001',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    hero_id: mockHero.id,
    villain_id: mockVillain.id,
    description: 'Sarah cannot access her product context (roadmap, initiatives, tasks) from within her IDE. This forces her to switch between VS Code and a web browser constantly, which breaks her flow state. The impact is severe: she loses focus, forgets what she was working on, and shipping slows down. The stakes are high: if this conflict isn\'t resolved, Sarah will abandon OpenBacklog and go back to fragmented tools.',
    status: ConflictStatus.OPEN,
    story_arc_id: null,
    resolved_at: null,
    resolved_by_initiative_id: null,
    created_at: '2025-01-18T10:00:00Z',
    updated_at: '2025-01-18T10:00:00Z',
    hero: mockHero,
    villain: mockVillain,
};

const mockConflictResolving: ConflictDto = {
    ...mockConflictOpen,
    identifier: 'C-2002',
    status: ConflictStatus.RESOLVING,
    story_arc_id: '850e8400-e29b-41d4-a716-446655440001',
};

const mockConflictResolved: ConflictDto = {
    ...mockConflictOpen,
    identifier: 'C-2003',
    status: ConflictStatus.RESOLVED,
    resolved_at: '2025-01-25T14:00:00Z',
    resolved_by_initiative_id: '950e8400-e29b-41d4-a716-446655440001',
    resolved_by_initiative: {
        id: '950e8400-e29b-41d4-a716-446655440001',
        identifier: 'I-1001',
        title: 'Add MCP Commands for Product Context Access',
        description: 'Create new MCP endpoints that expose product roadmap, initiatives, and tasks to Claude Code',
        status: 'COMPLETED',
        created_at: '2025-01-18T11:00:00Z',
        updated_at: '2025-01-25T14:00:00Z',
    },
};

const mockConflictEscalating: ConflictDto = {
    ...mockConflictOpen,
    identifier: 'C-2004',
    status: ConflictStatus.ESCALATING,
    description: 'The situation is deteriorating. More team members are reporting that context switching is hurting productivity even more than before.',
};

const meta: Meta<typeof ConflictDetail> = {
    title: 'Components/Narrative/ConflictDetail',
    component: ConflictDetail,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        conflict: {
            description: 'The conflict object to display',
        },
        hero: {
            description: 'The hero involved in the conflict',
        },
        villain: {
            description: 'The villain in the conflict',
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
            <div className="w-full max-w-4xl">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof ConflictDetail>;

/**
 * Open conflict (initial state).
 */
export const OpenConflict: Story = {
    args: {
        conflict: mockConflictOpen,
        hero: mockHero,
        villain: mockVillain,
        loading: false,
        error: null,
        dataTestId: 'conflict-detail-open',
    },
};

/**
 * Escalating conflict (getting worse).
 */
export const EscalatingConflict: Story = {
    args: {
        conflict: mockConflictEscalating,
        hero: mockHero,
        villain: mockVillain,
        loading: false,
        error: null,
        dataTestId: 'conflict-detail-escalating',
    },
};

/**
 * Resolving conflict (being actively worked on).
 */
export const ResolvingConflict: Story = {
    args: {
        conflict: mockConflictResolving,
        hero: mockHero,
        villain: mockVillain,
        loading: false,
        error: null,
        dataTestId: 'conflict-detail-resolving',
    },
};

/**
 * Resolved conflict (successfully resolved).
 */
export const ResolvedConflict: Story = {
    args: {
        conflict: mockConflictResolved,
        hero: mockHero,
        villain: mockVillain,
        loading: false,
        error: null,
        dataTestId: 'conflict-detail-resolved',
    },
};

/**
 * Loading state.
 */
export const Loading: Story = {
    args: {
        conflict: null,
        loading: true,
        error: null,
        dataTestId: 'conflict-detail-loading',
    },
};

/**
 * Empty state (no conflict data).
 */
export const Empty: Story = {
    args: {
        conflict: null,
        loading: false,
        error: null,
        dataTestId: 'conflict-detail-empty',
    },
};

/**
 * Error state.
 */
export const Error: Story = {
    args: {
        conflict: null,
        loading: false,
        error: 'Failed to load conflict data. Please try again.',
        dataTestId: 'conflict-detail-error',
    },
};

/**
 * With interactive callbacks.
 */
export const Interactive: Story = {
    args: {
        conflict: mockConflictOpen,
        hero: mockHero,
        villain: mockVillain,
        loading: false,
        error: null,
        onDelete: () => console.log('Delete conflict'),
        onRefresh: () => console.log('Refresh conflict'),
        dataTestId: 'conflict-detail-interactive',
    },
};

/**
 * All conflict statuses displayed together.
 */
export const AllStatuses: Story = {
    render: () => (
        <div className="space-y-8">
            <div>
                <h3 className="text-sm font-semibold text-foreground mb-2">OPEN Status</h3>
                <ConflictDetail
                    conflict={mockConflictOpen}
                    hero={mockHero}
                    villain={mockVillain}
                    loading={false}
                    error={null}
                    dataTestId="conflict-detail-open"
                />
            </div>
            <div>
                <h3 className="text-sm font-semibold text-foreground mb-2">RESOLVING Status</h3>
                <ConflictDetail
                    conflict={mockConflictResolving}
                    hero={mockHero}
                    villain={mockVillain}
                    loading={false}
                    error={null}
                    dataTestId="conflict-detail-resolving"
                />
            </div>
            <div>
                <h3 className="text-sm font-semibold text-foreground mb-2">RESOLVED Status</h3>
                <ConflictDetail
                    conflict={mockConflictResolved}
                    hero={mockHero}
                    villain={mockVillain}
                    loading={false}
                    error={null}
                    dataTestId="conflict-detail-resolved"
                />
            </div>
        </div>
    ),
    decorators: [
        (Story) => (
            <div className="w-full max-w-4xl">
                <Story />
            </div>
        ),
    ],
};
