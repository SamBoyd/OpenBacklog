import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import RoadmapThemeCard from '#components/Narrative/RoadmapThemeCard';
import { ThemeDto } from '#api/productStrategy';

const mockTheme: ThemeDto = {
    id: '750e8400-e29b-41d4-a716-446655440001',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'MCP Integration for AI Context',
    description: 'AI assistants lack native access to product context, forcing developers to manually context-switch between tools. If we expose product management data through an MCP server, AI assistants can query it natively and make better decisions without breaking developer flow. Success will be measured by reduction in context switches, faster feature implementation, and improved AI decision quality over a 6-month horizon.',
    outcome_ids: ['outcome-1', 'outcome-2'],
    hero_ids: [],
    villain_ids: [],
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockThemeMinimal: ThemeDto = {
    id: '750e8400-e29b-41d4-a716-446655440002',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Narrative Health Monitoring',
    description: 'Teams need visibility into how consistent their product narrative is over time.',
    outcome_ids: ['outcome-3'],
    hero_ids: [],
    villain_ids: [],
    created_at: '2025-01-16T14:30:00Z',
    updated_at: '2025-01-16T14:30:00Z',
};

const meta: Meta<typeof RoadmapThemeCard> = {
    title: 'Components/Narrative/RoadmapThemeCard',
    component: RoadmapThemeCard,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    decorators: [
        (Story) => (
            <div className="w-full max-w-2xl">
                <Story />
            </div>
        ),
    ],
    argTypes: {
        theme: {
            description: 'The theme object to display',
        },
        outcomeCount: {
            control: { type: 'number', min: 0, max: 10 },
            description: 'Number of linked outcomes',
        },
        isExpanded: {
            control: 'boolean',
            description: 'Whether card is expanded',
        },
        onToggleExpand: {
            action: 'expand toggled',
            description: 'Callback when expand is toggled',
        },
        onClick: {
            action: 'card clicked',
            description: 'Callback when card is clicked',
        },
    },
};

export default meta;
type Story = StoryObj<typeof RoadmapThemeCard>;

/**
 * Default theme card with full details.
 */
export const Default: Story = {
    args: {
        theme: mockTheme,
        outcomeCount: 2,
        isExpanded: false,
    },
};

/**
 * Expanded theme card showing all content.
 */
export const Expanded: Story = {
    args: {
        theme: mockTheme,
        outcomeCount: 2,
        isExpanded: true,
    },
};

/**
 * Theme card with minimal information.
 */
export const MinimalInfo: Story = {
    args: {
        theme: mockThemeMinimal,
        outcomeCount: 1,
        isExpanded: false,
    },
};

/**
 * Theme card with no linked outcomes.
 */
export const NoOutcomes: Story = {
    args: {
        theme: mockTheme,
        outcomeCount: 0,
        isExpanded: false,
    },
};

/**
 * Theme card with high outcome count.
 */
export const ManyOutcomes: Story = {
    args: {
        theme: mockTheme,
        outcomeCount: 7,
        isExpanded: false,
    },
};

/**
 * Interactive theme card with expand functionality.
 */
export const Interactive: Story = {
    render: (args) => {
        const [isExpanded, setIsExpanded] = useState(false);
        return (
            <RoadmapThemeCard
                {...args}
                isExpanded={isExpanded}
                onToggleExpand={setIsExpanded}
            />
        );
    },
    args: {
        theme: mockTheme,
        outcomeCount: 2,
    },
};

/**
 * Multiple theme cards together.
 */
export const MultipleCards: Story = {
    render: () => (
        <div className="flex flex-col gap-4 max-w-2xl">
            <RoadmapThemeCard
                theme={mockTheme}
                outcomeCount={2}
                isExpanded={false}
            />
            <RoadmapThemeCard
                theme={mockThemeMinimal}
                outcomeCount={1}
                isExpanded={false}
            />
        </div>
    ),
};
