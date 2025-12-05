import type { Meta, StoryObj } from '@storybook/react';
import { RoadmapOverview } from '#pages/RoadmapOverview';
import { mockPrioritizedThemes, mockUnprioritizedThemes, useRoadmapThemes } from '#hooks/strategyAndRoadmap/useRoadmapThemes.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { mockWorkspacesReturn } from '#stories/example_data';
import { mockStrategicPillarsReturn, useStrategicPillars } from '#hooks/useStrategicPillars.mock';
import { mockProductOutcomesReturn, useProductOutcomes } from '#hooks/useProductOutcomes.mock';

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
    useRoadmapThemes.mockReturnValue({
      prioritizedThemes: mockPrioritizedThemes,
      unprioritizedThemes: mockUnprioritizedThemes,
      isLoading: false,
      error: null,
      isLoadingPrioritized: false,
      isLoadingUnprioritized: false
    })

    useStrategicPillars.mockReturnValue(mockStrategicPillarsReturn);
    useProductOutcomes.mockReturnValue(mockProductOutcomesReturn);
  },
};

/**
 * Roadmap overview with loading state.
 */
export const Loading: Story = {
  beforeEach: () => {
    useRoadmapThemes.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
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
    useRoadmapThemes.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
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
    useRoadmapThemes.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
      isLoadingPrioritized: false,
      isLoadingUnprioritized: false,
      error: new Error('Failed to load roadmap'),
      isLoading: false
    });
  },
};
