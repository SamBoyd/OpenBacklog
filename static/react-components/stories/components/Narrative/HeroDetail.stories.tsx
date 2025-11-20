import type { Meta, StoryObj } from '@storybook/react';
import HeroDetail from '#components/Narrative/HeroDetail';
import { HeroDto } from '#types';

// Mock hero data
const mockPrimaryHero: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440001',
    identifier: 'H-2003',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Sarah Chen',
    description: 'Senior Product Manager at a fast-growing SaaS company. Manages a team of 5 and oversees product strategy for the core platform. Values clear communication and data-driven decision making.\n\nKey Characteristics:\n- 5+ years of product management experience\n- Strong analytical skills\n- Prefers async communication\n- Uses Slack and Linear daily\n\nGoals:\n- Ship features faster\n- Reduce team coordination overhead\n- Improve product quality',
    is_primary: true,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T12:30:00Z',
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

const mockHeroVeryLongDescription: HeroDto = {
    id: '550e8400-e29b-41d4-a716-446655440004',
    identifier: 'H-2006',
    workspace_id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Dr. Emily Watson',
    description: `Chief Technology Officer with 15+ years of experience in enterprise software development. Leads engineering teams across multiple time zones and is responsible for technical architecture decisions.

Background:
- Ph.D. in Computer Science from MIT
- Previously CTO at two successful startups
- Published author on distributed systems
- Conference speaker and industry thought leader

Leadership Style:
- Believes in servant leadership
- Encourages experimentation and learning from failures
- Strong advocate for work-life balance
- Regular 1-on-1s with all direct reports

Technical Expertise:
- Scalable systems architecture
- Cloud infrastructure (AWS, GCP, Azure)
- Microservices and event-driven architecture
- Performance optimization
- Security best practices

Current Challenges:
- Scaling engineering team from 20 to 100
- Modernizing legacy systems
- Implementing better observability
- Reducing technical debt

Goals for Next Quarter:
- Hire 15 senior engineers
- Launch new platform architecture
- Improve deployment frequency
- Reduce incident response time by 50%`,
    is_primary: true,
    created_at: '2025-01-18T11:00:00Z',
    updated_at: '2025-01-19T16:45:00Z',
};

const meta: Meta<typeof HeroDetail> = {
    title: 'Components/Narrative/HeroDetail',
    component: HeroDetail,
    parameters: {
        layout: 'padded',
    },
    tags: ['autodocs'],
    argTypes: {
        hero: {
            description: 'The hero object to display',
        },
        loading: {
            control: 'boolean',
            description: 'Loading state',
        },
        error: {
            control: 'text',
            description: 'Error message',
        },
        onDelete: {
            action: 'delete clicked',
            description: 'Callback when delete button is clicked',
        },
        onRefresh: {
            action: 'refresh clicked',
            description: 'Callback when refresh button is clicked',
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
            <div className="max-w-4xl mx-auto">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof HeroDetail>;

/**
 * Primary hero detail view with full description.
 */
export const PrimaryHero: Story = {
    args: {
        hero: mockPrimaryHero,
        loading: false,
        error: null,
        dataTestId: 'hero-detail-primary',
    },
};

/**
 * Secondary hero detail view.
 */
export const SecondaryHero: Story = {
    args: {
        hero: mockSecondaryHero,
        loading: false,
        error: null,
        dataTestId: 'hero-detail-secondary',
    },
};

/**
 * Hero detail without description.
 */
export const NoDescription: Story = {
    args: {
        hero: mockHeroNoDescription,
        loading: false,
        error: null,
        dataTestId: 'hero-detail-no-description',
    },
};

/**
 * Hero detail with very long description.
 */
export const LongDescription: Story = {
    args: {
        hero: mockHeroVeryLongDescription,
        loading: false,
        error: null,
        dataTestId: 'hero-detail-long-description',
    },
};

/**
 * Loading state.
 */
export const Loading: Story = {
    args: {
        hero: null,
        loading: true,
        error: null,
        dataTestId: 'hero-detail-loading',
    },
};

/**
 * Empty state with no hero data.
 */
export const Empty: Story = {
    args: {
        hero: null,
        loading: false,
        error: null,
        dataTestId: 'hero-detail-empty',
    },
};

/**
 * Error state.
 */
export const WithError: Story = {
    args: {
        hero: mockPrimaryHero,
        loading: false,
        error: 'Failed to load hero data. Please try again.',
        dataTestId: 'hero-detail-error',
    },
};

/**
 * Hero detail with callback handlers.
 */
export const WithCallbacks: Story = {
    args: {
        hero: mockPrimaryHero,
        loading: false,
        error: null,
        onDelete: () => console.log('Delete hero clicked!'),
        onRefresh: () => console.log('Refresh hero clicked!'),
        dataTestId: 'hero-detail-callbacks',
    },
};
