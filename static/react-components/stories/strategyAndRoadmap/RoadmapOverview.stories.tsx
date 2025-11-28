import type { Meta, StoryObj } from '@storybook/react';
import { RoadmapOverview } from '#pages/RoadmapOverview';
import { mockPrioritizedArcs, mockUnprioritizedArcs, useStoryArcs } from '#hooks/strategyAndRoadmap/useStoryArcs.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { mockWorkspacesReturn } from '#stories/example_data';

const meta: Meta<typeof RoadmapOverview> = {
  component: RoadmapOverview,
  title: 'Pages/StrategyAndRoadmap/RoadmapOverview',
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue(mockWorkspacesReturn);
      return <Story />;
    },
  ],
};

export default meta;
type Story = StoryObj<typeof RoadmapOverview>;

/**
 * Full Roadmap Overview page with multiple arcs.
 */
export const Default: Story = {
  parameters: {
    layout: 'fullscreen',
  },
  beforeEach: () => {
    useStoryArcs.mockReturnValue({
      prioritizedArcs: mockPrioritizedArcs,
      unprioritizedArcs: mockUnprioritizedArcs,
      isLoading: false,
      error: null,
      isLoadingPrioritized: false,
      isLoadingUnprioritized: false
    })
  },
};

/**
 * Roadmap overview with loading state.
 */
export const Loading: Story = {
  beforeEach: () => {
    useStoryArcs.mockReturnValue({
      prioritizedArcs: [],
      unprioritizedArcs: [],
      isLoading: true,
      error: null,
      isLoadingPrioritized: false,
      isLoadingUnprioritized: false
    });
  },
};

/**
 * Roadmap overview with empty state (no arcs).
 */
export const Empty: Story = {
  beforeEach: () => {
    useStoryArcs.mockReturnValue({
      prioritizedArcs: [],
      unprioritizedArcs: [],
      isLoading: false,
      error: null,
      isLoadingPrioritized: false,
      isLoadingUnprioritized: false
    });
  },
};

/**
 * Roadmap overview with error state.
 */
export const WithError: Story = {
  beforeEach: () => {
    useStoryArcs.mockReturnValue({
      prioritizedArcs: [],
      unprioritizedArcs: [],
      isLoadingPrioritized: false,
      isLoadingUnprioritized: false,
      error: new Error('Failed to load roadmap'),
      isLoading: false
    });
  },
};
