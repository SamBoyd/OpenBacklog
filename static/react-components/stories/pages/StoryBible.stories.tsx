import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import StoryBiblePage from '#pages/Narrative/StoryBible';
import { useHeroes } from '#hooks/useHeroes.mock';
import { useVillains } from '#hooks/useVillains.mock';
import { useStrategicPillars } from '#hooks/useStrategicPillars.mock';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes.mock';
import { HeroDto } from '#types';
import { VillainDto, VillainType } from '#types';
import { PillarDto } from '#api/productStrategy';
import { ThemeDto } from '#api/productStrategy';
import { mockWorkspace } from '#stories/example_data';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';

const mockNarrativeSummary = `OpenBacklog is pioneering a new category: the AI-native product management layer. We're building for solo developers and small teams who work alongside AI coding assistants like Claude Code, who need their product context to be immediately accessible to both humans and AI without breaking flow state.

Our hero, Sarah the Solo Builder, is trapped in a constant cycle of context switching between her IDE, planning tools, and documentation—preventing her AI assistant from understanding what to build and why. We're fighting against the fragmentation villain by transforming product management into a narrative format that AI can query and understand natively through MCP integration.

By treating product development as storytelling—with Heroes (users), Villains (problems), Story Arcs (strategic directions), and Beats (milestones)—we're creating a coherent, AI-accessible knowledge base that maintains narrative consistency over time. This isn't just another task manager; it's the canonical story bible for your product's universe.`;

const mockHeroes: HeroDto[] = [
    {
        id: '550e8400-e29b-41d4-a716-446655440001',
        identifier: 'H-2003',
        workspace_id: 'ws-001',
        name: 'Sarah, The Solo Builder',
        description: 'A solo developer who juggles multiple projects alongside an AI coding assistant. She needs to keep product context accessible without breaking flow state.',
        is_primary: true,
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: '550e8400-e29b-41d4-a716-446655440002',
        identifier: 'H-2004',
        workspace_id: 'ws-001',
        name: 'Alex, The AI-Augmented PM',
        description: 'Product Manager leveraging AI for documentation and decision support.',
        is_primary: false,
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
    {
        id: '550e8400-e29b-41d4-a716-446655440003',
        identifier: 'H-2005',
        workspace_id: 'ws-001',
        name: 'Morgan, The Indie Hacker',
        description: 'Entrepreneur bootstrapping a startup. Needs product management without the overhead.',
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
        description: 'Product information scattered across multiple tools, making it hard for AI to understand what to build.',
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
        description: 'Traditional PM tools require constant manual updates, distracting from actual product work.',
        villain_type: VillainType.WORKFLOW,
        severity: 4,
        is_defeated: false,
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
];

const mockPillars: PillarDto[] = [
    {
        id: '750e8400-e29b-41d4-a716-446655440001',
        workspace_id: 'ws-001',
        name: 'AI-Native Product Management',
        description: 'Build product management tools designed from the ground up for AI collaboration.',
        display_order: 1,
        outcome_ids: ['outcome-1', 'outcome-2'],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: '750e8400-e29b-41d4-a716-446655440002',
        workspace_id: 'ws-001',
        name: 'Developer Experience First',
        description: 'Prioritize the needs of developers over administrative overhead.',
        display_order: 2,
        outcome_ids: ['outcome-3'],
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
];

const mockThemes: ThemeDto[] = [
    {
        id: '850e8400-e29b-41d4-a716-446655440001',
        workspace_id: 'ws-001',
        name: 'MCP Integration for AI Context',
        description: 'Enable AI assistants to query product context natively through MCP server integration.',
        outcome_ids: ['outcome-1', 'outcome-2'],
        hero_ids: [],
        villain_ids: [],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: '850e8400-e29b-41d4-a716-446655440002',
        workspace_id: 'ws-001',
        name: 'Narrative Health Monitoring',
        description: 'Provide visibility into narrative consistency over time with health metrics and coverage scores.',
        outcome_ids: ['outcome-3'],
        hero_ids: [],
        villain_ids: [],
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
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
        onEditNarrative: {
            action: 'edit narrative clicked',
            description: 'Callback when Edit is clicked',
        },
        onRegenerateNarrative: {
            action: 'regenerate narrative clicked',
            description: 'Callback when Regenerate is clicked',
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

            useRoadmapThemes.mockReturnValue({
                themes: mockThemes,
                isLoading: false,
                error: null,
                createTheme: fn(),
                isCreating: false,
                createError: null,
                updateTheme: fn(),
                isUpdating: false,
                updateError: null,
                deleteTheme: fn(),
                isDeleting: false,
                deleteError: null,
                reorderThemes: fn(),
                isReordering: false,
                reorderError: null,
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
 * Story Bible page with callbacks.
 */
export const WithCallbacks: Story = {
    args: {
        narrativeSummary: mockNarrativeSummary,
        healthPercentage: 72,
        onEditNarrative: () => console.log('Edit narrative clicked'),
        onRegenerateNarrative: () => console.log('Regenerate narrative clicked'),
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
