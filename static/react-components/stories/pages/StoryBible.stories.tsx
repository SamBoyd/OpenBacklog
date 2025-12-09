import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import StoryBiblePage from '#pages/Narrative/StoryBible';
import { useHeroes } from '#hooks/useHeroes.mock';
import { useVillains } from '#hooks/useVillains.mock';
import { useStrategicPillars } from '#hooks/useStrategicPillars.mock';
import { useRoadmapThemes } from '#hooks/strategyAndRoadmap/useRoadmapThemes.mock';
import { HeroDto } from '#types';
import { VillainDto, VillainType } from '#types';
import { OutcomeReorderRequest, PillarDto } from '#api/productStrategy';
import { ThemeDto } from '#api/productStrategy';
import { mockWorkspace } from '#stories/example_data';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { mockOutcomes } from '#stories/strategyAndRoadmap/mockData';
import { useProductOutcomes } from '#hooks/useProductOutcomes.mock';

const mockNarrativeSummary = `OpenBacklog is pioneering a new category: the AI-native product management layer. We're building for solo developers and small teams who work alongside AI coding assistants like Claude Code, who need their product context to be immediately accessible to both humans and AI without breaking flow state.

Our hero, Sarah the Solo Builder, is trapped in a constant cycle of context switching between her IDE, planning tools, and documentation—preventing her AI assistant from understanding what to build and why. We're fighting against the fragmentation villain by transforming product management into a narrative format that AI can query and understand natively through MCP integration.

By treating product development as storytelling—with Heroes (users), Villains (problems), Story Arcs (strategic directions), and Beats (milestones)—we're creating a coherent, AI-accessible knowledge base that maintains narrative consistency over time. This isn't just another task manager; it's the canonical story bible for your product's universe.`;

const mockHeroes: HeroDto[] = [
    {
        id: '550e8400-e29b-41d4-a716-446655440001',
        identifier: 'H-2003',
        workspace_id: 'ws-001',
        name: 'Sarah, The Solo Builder',
        description: 'A solo developer who juggles multiple projects alongside an AI coding assistant. She needs to keep product context accessible without breaking flow state. Sarah works best in deep focus sessions and needs tools that respect her flow rather than interrupt it.',
        is_primary: true,
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: '550e8400-e29b-41d4-a716-446655440002',
        identifier: 'H-2004',
        workspace_id: 'ws-001',
        name: 'Alex, The AI-Augmented PM',
        description: 'Product Manager leveraging AI for documentation and decision support. Alex bridges the gap between technical teams and stakeholders, using AI to accelerate documentation and maintain alignment.',
        is_primary: false,
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
    {
        id: '550e8400-e29b-41d4-a716-446655440003',
        identifier: 'H-2005',
        workspace_id: 'ws-001',
        name: 'Morgan, The Indie Hacker',
        description: 'Entrepreneur bootstrapping a startup. Needs product management without the overhead. Morgan wears many hats and values simplicity and speed over process.',
        is_primary: false,
        created_at: '2025-01-17T09:00:00Z',
        updated_at: '2025-01-17T09:00:00Z',
    },
];

const mockVillains: VillainDto[] = [
    {
        id: '650e8400-e29b-41d4-a716-446655440001',
        identifier: 'V-2001',
        user_id: 'user-001',
        workspace_id: 'ws-001',
        name: 'Context Fragmentation',
        description: 'Product information scattered across multiple tools, making it hard for AI to understand what to build. This villain causes repeated context loss and forces developers to re-explain decisions.',
        villain_type: VillainType.EXTERNAL,
        severity: 5,
        is_defeated: false,
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: '650e8400-e29b-41d4-a716-446655440002',
        identifier: 'V-2002',
        user_id: 'user-001',
        workspace_id: 'ws-001',
        name: 'Manual Documentation Overhead',
        description: 'Traditional PM tools require constant manual updates, distracting from actual product work. Documentation becomes stale quickly, creating a vicious cycle of outdated information.',
        villain_type: VillainType.WORKFLOW,
        severity: 4,
        is_defeated: false,
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
    {
        id: '650e8400-e29b-41d4-a716-446655440003',
        identifier: 'V-2003',
        user_id: 'user-001',
        workspace_id: 'ws-001',
        name: 'Tool Sprawl',
        description: 'The proliferation of specialized tools that each solve one problem but create integration headaches. Every new tool adds cognitive overhead and context switching costs.',
        villain_type: VillainType.TECHNICAL,
        severity: 3,
        is_defeated: false,
        created_at: '2025-01-17T09:00:00Z',
        updated_at: '2025-01-17T09:00:00Z',
    },
];

const mockPillars: PillarDto[] = [
    {
        id: '750e8400-e29b-41d4-a716-446655440001',
        workspace_id: 'ws-001',
        name: 'AI-Native Product Management',
        description: 'Build product management tools designed from the ground up for AI collaboration. Every feature should be queryable and understandable by AI assistants.',
        display_order: 1,
        outcome_ids: ['outcome-1', 'outcome-2'],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: '750e8400-e29b-41d4-a716-446655440002',
        workspace_id: 'ws-001',
        name: 'Developer Experience First',
        description: 'Prioritize the needs of developers over administrative overhead. Minimize clicks, maximize keyboard shortcuts, and respect flow state.',
        display_order: 2,
        outcome_ids: ['outcome-3'],
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
    {
        id: '750e8400-e29b-41d4-a716-446655440003',
        workspace_id: 'ws-001',
        name: 'Narrative Coherence',
        description: 'Maintain a consistent product story that evolves over time. Every decision should connect back to the core narrative of who we serve and why.',
        display_order: 3,
        outcome_ids: [],
        created_at: '2025-01-17T09:00:00Z',
        updated_at: '2025-01-17T09:00:00Z',
    },
];

const mockThemes: ThemeDto[] = [
    {
        id: '850e8400-e29b-41d4-a716-446655440001',
        workspace_id: 'ws-001',
        name: 'MCP Integration for AI Context',
        description: 'Enable AI assistants to query product context natively through MCP server integration. This allows tools like Claude Code to understand the product roadmap, user personas, and technical decisions without manual context sharing.',
        outcome_ids: ['outcome-1', 'outcome-2'],
        hero_ids: [mockHeroes[0].id, mockHeroes[1].id],
        villain_ids: [mockVillains[0].id, mockVillains[1].id],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: '850e8400-e29b-41d4-a716-446655440002',
        workspace_id: 'ws-001',
        name: 'Narrative Health Monitoring',
        description: 'Provide visibility into narrative consistency over time with health metrics and coverage scores. Track how well the product story is maintained as the team builds new features.',
        outcome_ids: ['outcome-3'],
        hero_ids: [mockHeroes[0].id],
        villain_ids: [mockVillains[0].id],
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
    {
        id: '850e8400-e29b-41d4-a716-446655440003',
        workspace_id: 'ws-001',
        name: 'Story-Driven Backlog Management',
        description: 'Transform traditional backlog items into narrative beats that connect to the larger product story. Each task becomes part of a coherent arc rather than an isolated ticket.',
        outcome_ids: [],
        hero_ids: [mockHeroes[2].id],
        villain_ids: [mockVillains[2].id],
        created_at: '2025-01-17T09:00:00Z',
        updated_at: '2025-01-17T09:00:00Z',
    },
];

const meta: Meta<typeof StoryBiblePage> = {
    title: 'Pages/StoryBible',
    component: StoryBiblePage,
    parameters: {
        layout: 'fullscreen',
    },
    argTypes: {
        narrativeSummary: {
            control: 'text',
            description: 'Product narrative summary',
        },
        healthPercentage: {
            control: { type: 'number', min: 0, max: 100 },
            description: 'Narrative health percentage',
        },
    },
    decorators: [
        (Story) => {
            // Mock all hooks with data
            useWorkspaces.mockReturnValue({
                currentWorkspace: mockWorkspace,
                workspaces: [mockWorkspace],
                isLoading: false,
                error: null,
                changeWorkspace: async () => { },
                addWorkspace: async () => mockWorkspace,
                refresh: () => { },
                isProcessing: false
            });
            
            useHeroes.mockReturnValue({
                heroes: mockHeroes,
                isLoading: false,
                error: null,
                refetch: fn(),
            });

            useVillains.mockReturnValue({
                villains: mockVillains,
                isLoading: false,
                error: null,
                refetch: fn(),
            });

            useStrategicPillars.mockReturnValue({
                pillars: mockPillars,
                isLoading: false,
                error: null,
                createPillar: fn(),
                isCreating: false,
                createError: null,
                updatePillar: fn(),
                isUpdating: false,
                updateError: null,
                deletePillar: fn(),
                isDeleting: false,
                deleteError: null,
                reorderPillars: fn(),
                isReordering: false,
                reorderError: null,
            });

            useProductOutcomes.mockReturnValue({
                outcomes: mockOutcomes,
                isLoading: false,
                error: null,
                createOutcome: fn(),
                isCreating: false,
                createError: null,
                updateOutcome: fn(),
                isUpdating: false,
                updateError: null,
                deleteOutcome: function (outcomeId: string): void {
                    throw new Error('Function not implemented.');
                },
                isDeleting: false,
                deleteError: null,
                reorderOutcomes: function (request: OutcomeReorderRequest): void {
                    throw new Error('Function not implemented.');
                },
                isReordering: false,
                reorderError: null
            });

            useRoadmapThemes.mockReturnValue({
                prioritizedThemes: [mockThemes[0], mockThemes[1]],
                unprioritizedThemes: [mockThemes[2]],
                isLoadingPrioritized: false,
                isLoadingUnprioritized: false,
                isLoading: false,
                error: null,
            });

            return <Story />;
        },
    ],
};

export default meta;
type Story = StoryObj<typeof StoryBiblePage>;

/**
 * Default Story Bible page showing Heroes tab.
 * Data is fetched via hooks from the workspace.
 */
export const Default: Story = {
    args: {
        narrativeSummary: mockNarrativeSummary,
        healthPercentage: 72,
    },
};

/**
 * Story Bible page with good health status.
 */
export const GoodHealth: Story = {
    args: {
        narrativeSummary: mockNarrativeSummary,
        healthPercentage: 95,
    },
};

/**
 * Story Bible page with poor health status.
 */
export const PoorHealth: Story = {
    args: {
        narrativeSummary: mockNarrativeSummary,
        healthPercentage: 40,
    },
};

/**
 * Story Bible page with short narrative.
 */
export const ShortNarrative: Story = {
    args: {
        narrativeSummary: 'Build the best AI-native product management tool for developers.',
        healthPercentage: 85,
    },
};

/**
 * Story Bible page with no narrative.
 */
export const NoNarrative: Story = {
    args: {
        narrativeSummary: '',
        healthPercentage: 50,
    },
};
