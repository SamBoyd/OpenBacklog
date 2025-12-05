import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { ThemeCard } from '#components/strategyAndRoadmap/ThemeCard';
import {
  mockPrioritizedThemes,
  mockUnprioritizedThemes,
} from '#hooks/strategyAndRoadmap/useRoadmapThemes.mock';

const meta: Meta<typeof ThemeCard> = {
  component: ThemeCard,
  title: 'Components/StrategyAndRoadmap/ThemeCard',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ThemeCard>;

const defaultHandlers = {
  onViewTheme: fn(),
  onViewInitiatives: fn(),
  onEdit: fn(),
  onMoreOptions: fn(),
};

/**
 * Prioritized theme with full narrative context (hero and multiple villains).
 * This represents a typical active roadmap theme with clear narrative elements.
 */
export const WithNarrativeContext: Story = {
  args: {
    theme: mockPrioritizedThemes[0],
    ...defaultHandlers,
  },
};

/**
 * Theme with multiple narrative elements showing complex hero/villain relationships.
 * Demonstrates how the card handles multiple heroes and villains.
 */
export const MultipleNarratives: Story = {
  args: {
    theme: mockPrioritizedThemes[1],
    ...defaultHandlers,
  },
};

/**
 * Backlog theme with no heroes or villains assigned yet.
 * Shows the card's appearance when narrative context hasn't been defined.
 */
export const NoNarratives: Story = {
  args: {
    theme: mockUnprioritizedThemes[1],
    ...defaultHandlers,
  },
};

/**
 * Theme with a long description to show text truncation behavior.
 * Description is limited to 2 lines with line-clamp-2.
 */
export const LongDescription: Story = {
  args: {
    theme: {
      ...mockPrioritizedThemes[0],
      description:
        'This is a very long description that demonstrates how the ArcCard component handles text overflow. The description will be truncated to two lines using the line-clamp-2 utility class, ensuring the card maintains a consistent height and clean appearance even when theme descriptions are verbose. This helps maintain visual consistency across the roadmap.',
    },
    ...defaultHandlers,
  },
};

/**
 * Theme with minimal data - just name and description.
 * Shows the simplest possible card state.
 */
export const Minimal: Story = {
  args: {
    theme: {
      id: 'minimal-1',
      workspace_id: 'workspace-1',
      name: 'Simple Theme',
      description: 'A basic theme with no additional context',
      outcome_ids: [],
      hero_ids: [],
      villain_ids: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      heroes: [],
      villains: [],
    },
    ...defaultHandlers,
  },
};

/**
 * Card with no action handlers provided.
 * Buttons will not be rendered when handlers are undefined.
 */
export const NoActions: Story = {
  args: {
    theme: mockPrioritizedThemes[2],
  },
};
