import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { RoadmapListView } from '#components/strategyAndRoadmap/RoadmapListView';
import {
  mockPrioritizedThemes,
  mockUnprioritizedThemes,
} from '#hooks/strategyAndRoadmap/useRoadmapThemes.mock';

const meta: Meta<typeof RoadmapListView> = {
  component: RoadmapListView,
  title: 'Components/StrategyAndRoadmap/RoadmapListView',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof RoadmapListView>;

const defaultHandlers = {
  onViewTheme: fn(),
  onViewInitiatives: fn(),
  onEdit: fn(),
  onMoreOptions: fn(),
};

/**
 * Default view with both prioritized and unprioritized themes.
 * Shows the typical state with an active roadmap and backlog.
 */
export const Default: Story = {
  args: {
    prioritizedThemes: mockPrioritizedThemes,
    unprioritizedThemes: mockUnprioritizedThemes,
    isLoading: false,
    ...defaultHandlers,
  },
};

/**
 * Only prioritized themes are present, backlog is empty.
 * This shows the state when all themes have been prioritized.
 */
export const OnlyPrioritized: Story = {
  args: {
    prioritizedThemes: mockPrioritizedThemes,
    unprioritizedThemes: [],
    isLoading: false,
    ...defaultHandlers,
  },
};

/**
 * Only backlog themes exist, no themes are prioritized yet.
 * This shows the initial state before prioritization.
 */
export const OnlyBacklog: Story = {
  args: {
    prioritizedThemes: [],
    unprioritizedThemes: mockUnprioritizedThemes,
    isLoading: false,
    ...defaultHandlers,
  },
};

/**
 * Empty state with no themes at all.
 * User needs to create their first roadmap theme.
 */
export const Empty: Story = {
  args: {
    prioritizedThemes: [],
    unprioritizedThemes: [],
    isLoading: false,
    ...defaultHandlers,
  },
};

/**
 * Loading state while fetching themes.
 */
export const Loading: Story = {
  args: {
    prioritizedThemes: [],
    unprioritizedThemes: [],
    isLoading: true,
  },
};

/**
 * Single prioritized theme with no backlog.
 * Minimal viable roadmap state.
 */
export const SingleTheme: Story = {
  args: {
    prioritizedThemes: [mockPrioritizedThemes[0]],
    unprioritizedThemes: [],
    isLoading: false,
    ...defaultHandlers,
  },
};

/**
 * Maximum prioritized themes (5) with additional themes in backlog.
 * Shows the prioritization limit in action.
 */
export const MaxPrioritized: Story = {
  args: {
    prioritizedThemes: [
      ...mockPrioritizedThemes,
      { ...mockUnprioritizedThemes[0], id: 'extra-1' },
      { ...mockUnprioritizedThemes[1], id: 'extra-2' },
    ],
    unprioritizedThemes: [mockUnprioritizedThemes[2]],
    isLoading: false,
    ...defaultHandlers,
  },
};
