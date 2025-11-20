import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import ConflictCard from '#components/Narrative/ConflictCard';
import { ConflictDto, ConflictStatus, HeroDto, VillainDto, VillainType } from '#types';

const meta: Meta<typeof ConflictCard> = {
    title: 'Components/Narrative/ConflictCard',
    component: ConflictCard,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        conflict: {
            description: 'Conflict data object',
        },
        hero: {
            description: 'Optional hero data (will use conflict.hero if not provided)',
        },
        villain: {
            description: 'Optional villain data (will use conflict.villain if not provided)',
        },
        onClick: {
            action: 'clicked',
            description: 'Click handler for the card',
        },
    },
};

export default meta;
type Story = StoryObj<typeof ConflictCard>;

// Mock data
const mockWorkspaceId = 'workspace-123';

const mockHero: HeroDto = {
    id: 'hero-1',
    identifier: 'H-2003',
    workspace_id: mockWorkspaceId,
    name: 'Sarah, The Solo Builder',
    description: 'A solo developer building side projects while managing a full-time job.',
    is_primary: true,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockVillain: VillainDto = {
    id: 'villain-1',
    identifier: 'V-2003',
    user_id: 'user-123',
    workspace_id: mockWorkspaceId,
    name: 'Context Switching',
    villain_type: VillainType.WORKFLOW,
    description: 'Jumping between multiple tools and platforms breaks flow state and wastes time.',
    severity: 5,
    is_defeated: false,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockVillainFragmentedKnowledge: VillainDto = {
    id: 'villain-2',
    identifier: 'V-2004',
    user_id: 'user-123',
    workspace_id: mockWorkspaceId,
    name: 'Fragmented Knowledge',
    villain_type: VillainType.WORKFLOW,
    description: 'Important project context is scattered across different files and locations.',
    severity: 4,
    is_defeated: false,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockConflictOpen: ConflictDto = {
    id: 'conflict-1',
    identifier: 'C-2003',
    workspace_id: mockWorkspaceId,
    hero_id: mockHero.id,
    villain_id: mockVillain.id,
    description:
        'Sarah cannot access project context from her IDE. She has to switch between her editor, browser tabs, and notes app to gather requirements and technical details, breaking her flow state repeatedly.',
    status: ConflictStatus.OPEN,
    story_arc_id: null,
    resolved_at: null,
    resolved_by_initiative_id: null,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
    hero: mockHero,
    villain: mockVillain,
};

const mockConflictEscalating: ConflictDto = {
    id: 'conflict-2',
    identifier: 'C-2004',
    workspace_id: mockWorkspaceId,
    hero_id: mockHero.id,
    villain_id: mockVillainFragmentedKnowledge.id,
    description:
        'As Sarah adds more features, she loses track of design decisions. She finds herself re-reading old code and notes to remember why certain choices were made, leading to inconsistent implementation.',
    status: ConflictStatus.ESCALATING,
    story_arc_id: null,
    resolved_at: null,
    resolved_by_initiative_id: null,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
    hero: mockHero,
    villain: mockVillainFragmentedKnowledge,
};

const mockConflictResolving: ConflictDto = {
    id: 'conflict-3',
    identifier: 'C-2005',
    workspace_id: mockWorkspaceId,
    hero_id: mockHero.id,
    villain_id: mockVillain.id,
    description:
        'Sarah is testing a unified context management system that brings all project information into one place.',
    status: ConflictStatus.RESOLVING,
    story_arc_id: null,
    resolved_at: null,
    resolved_by_initiative_id: null,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
    hero: mockHero,
    villain: mockVillain,
};

const mockConflictResolved: ConflictDto = {
    id: 'conflict-4',
    identifier: 'C-2006',
    workspace_id: mockWorkspaceId,
    hero_id: mockHero.id,
    villain_id: mockVillain.id,
    description:
        'Sarah successfully implemented an AI-powered IDE extension that brings context directly into her editor.',
    status: ConflictStatus.RESOLVED,
    story_arc_id: null,
    resolved_at: '2025-01-20T15:30:00Z',
    resolved_by_initiative_id: 'init-1',
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-20T15:30:00Z',
    hero: mockHero,
    villain: mockVillain,
    resolved_by_initiative: {
        id: 'init-1',
        identifier: 'I-100',
        title: 'Build IDE Context Extension',
        status: 'DONE',
    },
};

const mockConflictWithoutRelatedData: ConflictDto = {
    id: 'conflict-5',
    identifier: 'C-2007',
    workspace_id: mockWorkspaceId,
    hero_id: mockHero.id,
    villain_id: mockVillain.id,
    description: 'This conflict has no hero or villain data loaded.',
    status: ConflictStatus.OPEN,
    story_arc_id: null,
    resolved_at: null,
    resolved_by_initiative_id: null,
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
};

const mockLongDescription: ConflictDto = {
    ...mockConflictOpen,
    id: 'conflict-6',
    identifier: 'C-2008',
    description:
        'This is a very long description that should be truncated in the card view. ' +
        'Sarah faces multiple challenges when trying to maintain focus during development. ' +
        'She constantly switches between her code editor, browser documentation, Slack messages, ' +
        'Jira tickets, and her notes app. Each context switch takes mental energy and time to reload ' +
        'the mental model of what she was working on. This cumulative effect results in hours of lost ' +
        'productivity each week and increasing frustration with the development workflow.',
};

// Stories
export const OpenStatus: Story = {
    args: {
        conflict: mockConflictOpen,
    },
};

export const EscalatingStatus: Story = {
    args: {
        conflict: mockConflictEscalating,
    },
};

export const ResolvingStatus: Story = {
    args: {
        conflict: mockConflictResolving,
    },
};

export const ResolvedStatus: Story = {
    args: {
        conflict: mockConflictResolved,
    },
};

export const WithoutRelatedData: Story = {
    args: {
        conflict: mockConflictWithoutRelatedData,
    },
};

export const LongDescriptionTruncated: Story = {
    args: {
        conflict: mockLongDescription,
    },
};

export const WithClickHandler: Story = {
    args: {
        conflict: mockConflictOpen,
        onClick: () => alert('Conflict card clicked!'),
    },
};

export const AllStatuses: Story = {
    render: () => (
        <div className="flex flex-col gap-4 p-6 max-w-2xl">
            <ConflictCard conflict={mockConflictOpen} />
            <ConflictCard conflict={mockConflictEscalating} />
            <ConflictCard conflict={mockConflictResolving} />
            <ConflictCard conflict={mockConflictResolved} />
        </div>
    ),
};
