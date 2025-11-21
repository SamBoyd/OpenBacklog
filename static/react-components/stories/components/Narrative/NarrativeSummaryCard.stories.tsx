import type { Meta, StoryObj } from '@storybook/react';
import NarrativeSummaryCard from '#components/Narrative/NarrativeSummaryCard';

const mockNarrativeSummary = `OpenBacklog is pioneering a new category: the AI-native product management layer. We're building for solo developers and small teams who work alongside AI coding assistants like Claude Code, who need their product context to be immediately accessible to both humans and AI without breaking flow state.

Our hero, Sarah the Solo Builder, is trapped in a constant cycle of context switching between her IDE, planning tools, and documentation—preventing her AI assistant from understanding what to build and why. We're fighting against the fragmentation villain by transforming product management into a narrative format that AI can query and understand natively through MCP integration.

By treating product development as storytelling—with Heroes (users), Villains (problems), Story Arcs (strategic directions), and Beats (milestones)—we're creating a coherent, AI-accessible knowledge base that maintains narrative consistency over time. This isn't just another task manager; it's the canonical story bible for your product's universe.`;

const meta: Meta<typeof NarrativeSummaryCard> = {
    title: 'Components/Narrative/NarrativeSummaryCard',
    component: NarrativeSummaryCard,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    decorators: [
        (Story) => (
            <div className="w-full max-w-4xl p-4">
                <Story />
            </div>
        ),
    ],
    argTypes: {
        summary: {
            control: 'text',
            description: 'The narrative summary text',
        },
        healthPercentage: {
            control: { type: 'number', min: 0, max: 100 },
            description: 'Narrative health percentage',
        },
        needsAttention: {
            control: 'boolean',
            description: 'Whether narrative needs attention',
        },
        onEdit: {
            action: 'edit clicked',
            description: 'Callback when Edit is clicked',
        },
        onRegenerate: {
            action: 'regenerate clicked',
            description: 'Callback when Regenerate is clicked',
        },
    },
};

export default meta;
type Story = StoryObj<typeof NarrativeSummaryCard>;

/**
 * Default narrative summary card with good health.
 */
export const Default: Story = {
    args: {
        summary: mockNarrativeSummary,
        healthPercentage: 72,
        needsAttention: true,
    },
};

/**
 * Narrative summary with excellent health.
 */
export const GoodHealth: Story = {
    args: {
        summary: mockNarrativeSummary,
        healthPercentage: 95,
        needsAttention: false,
    },
};

/**
 * Narrative summary with poor health.
 */
export const PoorHealth: Story = {
    args: {
        summary: mockNarrativeSummary,
        healthPercentage: 40,
        needsAttention: true,
    },
};

/**
 * Narrative summary with short text.
 */
export const ShortSummary: Story = {
    args: {
        summary: 'Build the best product management tool for AI-native teams.',
        healthPercentage: 85,
        needsAttention: false,
    },
};

/**
 * Narrative summary with callbacks.
 */
export const WithCallbacks: Story = {
    args: {
        summary: mockNarrativeSummary,
        healthPercentage: 72,
        needsAttention: true,
        onEdit: () => console.log('Edit clicked'),
        onRegenerate: () => console.log('Regenerate clicked'),
    },
};
