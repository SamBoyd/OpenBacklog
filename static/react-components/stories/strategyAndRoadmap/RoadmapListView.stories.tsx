import type { Meta, StoryObj } from '@storybook/react';
import { RoadmapListView } from '#components/strategyAndRoadmap/RoadmapListView';
import { mockStoryArcs } from '#hooks/strategyAndRoadmap/useStoryArcs.mock';

const meta: Meta<typeof RoadmapListView> = {
  component: RoadmapListView,
  title: 'Components/StrategyAndRoadmap/RoadmapListView',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof RoadmapListView>;

/**
 * List view with multiple arcs grouped by quarter.
 */
export const Default: Story = {
  args: {
    arcs: mockStoryArcs,
    isLoading: false,
    onViewArc: (arcId) => console.log('View Arc:', arcId),
    onViewBeats: (arcId) => console.log('View Beats:', arcId),
    onEdit: (arcId) => console.log('Edit:', arcId),
    onMoreOptions: (arcId) => console.log('More Options:', arcId),
  },
};

/**
 * Loading state of the list view.
 */
export const Loading: Story = {
  args: {
    arcs: [],
    isLoading: true,
  },
};

/**
 * Empty state with no arcs.
 */
export const Empty: Story = {
  args: {
    arcs: [],
    isLoading: false,
  },
};

/**
 * Single arc in the list.
 */
export const SingleArc: Story = {
  args: {
    arcs: [mockStoryArcs[0]],
    isLoading: false,
    onViewArc: (arcId) => console.log('View Arc:', arcId),
    onViewBeats: (arcId) => console.log('View Beats:', arcId),
    onEdit: (arcId) => console.log('Edit:', arcId),
    onMoreOptions: (arcId) => console.log('More Options:', arcId),
  },
};
