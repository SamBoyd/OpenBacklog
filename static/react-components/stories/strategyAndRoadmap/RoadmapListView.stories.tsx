import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { RoadmapListView } from '#components/strategyAndRoadmap/RoadmapListView';
import {
  mockPrioritizedArcs,
  mockUnprioritizedArcs,
} from '#hooks/strategyAndRoadmap/useStoryArcs.mock';

const meta: Meta<typeof RoadmapListView> = {
  component: RoadmapListView,
  title: 'Components/StrategyAndRoadmap/RoadmapListView',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof RoadmapListView>;

const defaultHandlers = {
  onViewArc: fn(),
  onViewBeats: fn(),
  onEdit: fn(),
  onMoreOptions: fn(),
};

/**
 * Default view with both prioritized and unprioritized themes.
 * Shows the typical state with an active roadmap and backlog.
 */
export const Default: Story = {
  args: {
    prioritizedArcs: mockPrioritizedArcs,
    unprioritizedArcs: mockUnprioritizedArcs,
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
    prioritizedArcs: mockPrioritizedArcs,
    unprioritizedArcs: [],
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
    prioritizedArcs: [],
    unprioritizedArcs: mockUnprioritizedArcs,
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
    prioritizedArcs: [],
    unprioritizedArcs: [],
    isLoading: false,
    ...defaultHandlers,
  },
};

/**
 * Loading state while fetching themes.
 */
export const Loading: Story = {
  args: {
    prioritizedArcs: [],
    unprioritizedArcs: [],
    isLoading: true,
  },
};

/**
 * Single prioritized theme with no backlog.
 * Minimal viable roadmap state.
 */
export const SingleTheme: Story = {
  args: {
    prioritizedArcs: [mockPrioritizedArcs[0]],
    unprioritizedArcs: [],
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
    prioritizedArcs: [
      ...mockPrioritizedArcs,
      { ...mockUnprioritizedArcs[0], id: 'extra-1' },
      { ...mockUnprioritizedArcs[1], id: 'extra-2' },
    ],
    unprioritizedArcs: [mockUnprioritizedArcs[2]],
    isLoading: false,
    ...defaultHandlers,
  },
};
