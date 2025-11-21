import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import NarrativeHeroCard from '#components/Narrative/NarrativeHeroCard';
import { HeroDto } from '#types';

const mockHero: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440001',
    identifier: 'H-2003',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Sarah, The Solo Builder',
    description: 'A solo developer who juggles multiple projects alongside an AI coding assistant. She needs to keep product context accessible without breaking flow state. Her core promise is to never leave the IDE to give AI the context it needs.',
    is_primary: true,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockHeroShort: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440002',
    identifier: 'H-2004',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Alex, The AI-Augmented PM',
    description: 'Product Manager leveraging AI for documentation.',
    is_primary: false,
    created_at: '2025-01-16T14:30:00Z',
    updated_at: '2025-01-16T14:30:00Z',
};

const meta: Meta<typeof NarrativeHeroCard> = {
    title: 'Components/Narrative/NarrativeHeroCard',
    component: NarrativeHeroCard,
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
        hero: {
            description: 'The hero object to display',
        },
        arcCount: {
            control: { type: 'number', min: 0, max: 10 },
            description: 'Number of story arcs featuring this hero',
        },
        villainCount: {
            control: { type: 'number', min: 0, max: 10 },
            description: 'Number of villains opposing this hero',
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
type Story = StoryObj<typeof NarrativeHeroCard>;

/**
 * Default hero card with full description.
 */
export const Default: Story = {
    args: {
        hero: mockHero,
        arcCount: 2,
        villainCount: 2,
        isExpanded: false,
    },
};

/**
 * Expanded hero card showing full description.
 */
export const Expanded: Story = {
    args: {
        hero: mockHero,
        arcCount: 2,
        villainCount: 2,
        isExpanded: true,
    },
};

/**
 * Hero card with short description.
 */
export const ShortDescription: Story = {
    args: {
        hero: mockHeroShort,
        arcCount: 1,
        villainCount: 1,
        isExpanded: false,
    },
};

/**
 * Hero card with no opposing villains.
 */
export const NoVillains: Story = {
    args: {
        hero: mockHero,
        arcCount: 2,
        villainCount: 0,
        isExpanded: false,
    },
};

/**
 * Hero card with high arc count.
 */
export const HighArcCount: Story = {
    args: {
        hero: mockHero,
        arcCount: 5,
        villainCount: 3,
        isExpanded: false,
    },
};

/**
 * Interactive hero card with expand functionality.
 */
export const Interactive: Story = {
    render: (args) => {
        const [isExpanded, setIsExpanded] = useState(false);
        return (
            <NarrativeHeroCard
                {...args}
                isExpanded={isExpanded}
                onToggleExpand={setIsExpanded}
            />
        );
    },
    args: {
        hero: mockHero,
        arcCount: 2,
        villainCount: 2,
    },
};

/**
 * Multiple hero cards together.
 */
export const MultipleCards: Story = {
    render: () => (
        <div className="flex flex-col gap-4 max-w-2xl">
            <NarrativeHeroCard
                hero={mockHero}
                arcCount={2}
                villainCount={2}
                isExpanded={false}
            />
            <NarrativeHeroCard
                hero={mockHeroShort}
                arcCount={1}
                villainCount={1}
                isExpanded={false}
            />
        </div>
    ),
};
