import type { Meta, StoryObj } from '@storybook/react';
import HeroCard from '#components/Narrative/HeroCard';
import { HeroDto } from '#types';

// Mock hero data
const mockPrimaryHero: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440001',
    identifier: 'H-2003',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Sarah Chen',
    description: 'Senior Product Manager at a fast-growing SaaS company. Manages a team of 5 and oversees product strategy for the core platform. Values clear communication and data-driven decision making.',
    is_primary: true,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockSecondaryHero: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440002',
    identifier: 'H-2004',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Marcus Johnson',
    description: 'Junior Developer new to the team. Learning the codebase and eager to contribute. Prefers clear documentation and pair programming.',
    is_primary: false,
    created_at: '2025-01-16T14:30:00Z',
    updated_at: '2025-01-16T14:30:00Z',
};

const mockHeroNoDescription: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440003',
    identifier: 'H-2005',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Alex Rivera',
    description: null,
    is_primary: false,
    created_at: '2025-01-17T09:00:00Z',
    updated_at: '2025-01-17T09:00:00Z',
};

const mockHeroLongDescription: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440004',
    identifier: 'H-2006',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Dr. Emily Watson',
    description: 'Chief Technology Officer with 15+ years of experience in enterprise software development. Leads engineering teams across multiple time zones and is responsible for technical architecture decisions. Has deep expertise in scalable systems, cloud infrastructure, and team leadership. Known for mentoring junior engineers and fostering a culture of innovation and continuous improvement.',
    is_primary: true,
    created_at: '2025-01-18T11:00:00Z',
    updated_at: '2025-01-18T11:00:00Z',
};

const meta: Meta<typeof HeroCard> = {
    title: 'Components/Narrative/HeroCard',
    component: HeroCard,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        hero: {
            description: 'The hero object to display',
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
type Story = StoryObj<typeof HeroCard>;

/**
 * Primary hero card with full description.
 */
export const PrimaryHero: Story = {
    args: {
        hero: mockPrimaryHero,
        dataTestId: 'hero-card-primary',
    },
};

/**
 * Secondary hero card.
 */
export const SecondaryHero: Story = {
    args: {
        hero: mockSecondaryHero,
        dataTestId: 'hero-card-secondary',
    },
};

/**
 * Hero card without description.
 */
export const NoDescription: Story = {
    args: {
        hero: mockHeroNoDescription,
        dataTestId: 'hero-card-no-description',
    },
};

/**
 * Hero card with long description that gets truncated.
 */
export const LongDescription: Story = {
    args: {
        hero: mockHeroLongDescription,
        dataTestId: 'hero-card-long-description',
    },
};

/**
 * Clickable hero card.
 */
export const Clickable: Story = {
    args: {
        hero: mockPrimaryHero,
        onClick: () => console.log('Hero card clicked!'),
        dataTestId: 'hero-card-clickable',
    },
};

/**
 * Multiple hero cards displayed together.
 */
export const MultipleCards: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <HeroCard hero={mockPrimaryHero} />
            <HeroCard hero={mockSecondaryHero} />
            <HeroCard hero={mockHeroNoDescription} />
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
