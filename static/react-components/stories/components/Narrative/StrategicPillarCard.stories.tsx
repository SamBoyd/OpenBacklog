import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import StrategicPillarCard from '#components/Narrative/StrategicPillarCard';
import { PillarDto } from '#api/productStrategy';

const mockPillar: PillarDto = {
    id: '650e8400-e29b-41d4-a716-446655440001',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'AI-Native Product Management',
    description: 'Build product management tools that are designed from the ground up for AI collaboration. These tools should make it easy for AI systems to understand product context and make better decisions.',
    anti_strategy: 'We will not build traditional project management tools that ignore AI. We will not create tools that require context switching.',
    display_order: 1,
    outcome_ids: ['outcome-1', 'outcome-2'],
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockPillarMinimal: PillarDto = {
    id: '650e8400-e29b-41d4-a716-446655440002',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Developer Experience First',
    description: null,
    anti_strategy: null,
    display_order: 2,
    outcome_ids: ['outcome-3'],
    created_at: '2025-01-16T14:30:00Z',
    updated_at: '2025-01-16T14:30:00Z',
};

const meta: Meta<typeof StrategicPillarCard> = {
    title: 'Components/Narrative/StrategicPillarCard',
    component: StrategicPillarCard,
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
        pillar: {
            description: 'The pillar object to display',
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
type Story = StoryObj<typeof StrategicPillarCard>;

/**
 * Default pillar card with full details.
 */
export const Default: Story = {
    args: {
        pillar: mockPillar,
        outcomeCount: 2,
        isExpanded: false,
    },
};

/**
 * Expanded pillar card showing full content.
 */
export const Expanded: Story = {
    args: {
        pillar: mockPillar,
        outcomeCount: 2,
        isExpanded: true,
    },
};

/**
 * Pillar card with minimal information.
 */
export const MinimalInfo: Story = {
    args: {
        pillar: mockPillarMinimal,
        outcomeCount: 1,
        isExpanded: false,
    },
};

/**
 * Pillar card with no linked outcomes.
 */
export const NoOutcomes: Story = {
    args: {
        pillar: mockPillar,
        outcomeCount: 0,
        isExpanded: false,
    },
};

/**
 * Pillar card with high outcome count.
 */
export const ManyOutcomes: Story = {
    args: {
        pillar: mockPillar,
        outcomeCount: 8,
        isExpanded: false,
    },
};

/**
 * Interactive pillar card with expand functionality.
 */
export const Interactive: Story = {
    render: (args) => {
        const [isExpanded, setIsExpanded] = useState(false);
        return (
            <StrategicPillarCard
                {...args}
                isExpanded={isExpanded}
                onToggleExpand={setIsExpanded}
            />
        );
    },
    args: {
        pillar: mockPillar,
        outcomeCount: 2,
    },
};

/**
 * Multiple pillar cards together.
 */
export const MultipleCards: Story = {
    render: () => (
        <div className="flex flex-col gap-4 max-w-2xl">
            <StrategicPillarCard
                pillar={mockPillar}
                outcomeCount={2}
                isExpanded={false}
            />
            <StrategicPillarCard
                pillar={mockPillarMinimal}
                outcomeCount={1}
                isExpanded={false}
            />
        </div>
    ),
};
