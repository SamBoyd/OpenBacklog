import type { Meta, StoryObj } from '@storybook/react';
import { RoadmapSummaryPanel } from '#components/strategyAndRoadmap/RoadmapSummaryPanel';
import { mockPrioritizedThemes, mockUnprioritizedThemes } from '#hooks/strategyAndRoadmap/useRoadmapThemes.mock';

const meta: Meta<typeof RoadmapSummaryPanel> = {
  component: RoadmapSummaryPanel,
  title: 'Components/StrategyAndRoadmap/RoadmapSummaryPanel',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof RoadmapSummaryPanel>;

/**
 * Summary panel in expanded state showing all statistics.
 */
export const Expanded: Story = {
  args: {
    themes: mockPrioritizedThemes,
    onViewAllHeroes: () => console.log('View All Heroes clicked'),
    onViewAllVillains: () => console.log('View All Villains clicked'),
    onRunConsistencyCheck: () => console.log('Run Consistency Check clicked'),
  },
};

/**
 * Summary panel in collapsed state.
 */
export const Collapsed: Story = {
  args: {
    themes: mockPrioritizedThemes,
    onViewAllHeroes: () => console.log('View All Heroes clicked'),
    onViewAllVillains: () => console.log('View All Villains clicked'),
    onRunConsistencyCheck: () => console.log('Run Consistency Check clicked'),
  },
  render: (args) => {
    return (
      <div>
        <div className="text-xs text-foreground mb-2">
          Click the Collapse button to see the collapsed state
        </div>
        <RoadmapSummaryPanel {...args} />
      </div>
    );
  },
};

/**
 * Summary panel with no themes (empty state).
 */
export const Empty: Story = {
  args: {
    themes: [],
    onViewAllHeroes: () => console.log('View All Heroes clicked'),
    onViewAllVillains: () => console.log('View All Villains clicked'),
    onRunConsistencyCheck: () => console.log('Run Consistency Check clicked'),
  },
};
