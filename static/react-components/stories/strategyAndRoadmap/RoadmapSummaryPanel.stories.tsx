import type { Meta, StoryObj } from '@storybook/react';
import { RoadmapSummaryPanel } from '#components/strategyAndRoadmap/RoadmapSummaryPanel';
import { mockStoryArcs } from '#hooks/strategyAndRoadmap/useStoryArcs.mock';

const meta: Meta<typeof RoadmapSummaryPanel> = {
  component: RoadmapSummaryPanel,
  title: 'strategyAndRoadmap/RoadmapSummaryPanel',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof RoadmapSummaryPanel>;

/**
 * Summary panel in expanded state showing all statistics.
 */
export const Expanded: Story = {
  args: {
    arcs: mockStoryArcs,
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
    arcs: mockStoryArcs,
    onViewAllHeroes: () => console.log('View All Heroes clicked'),
    onViewAllVillains: () => console.log('View All Villains clicked'),
    onRunConsistencyCheck: () => console.log('Run Consistency Check clicked'),
  },
  render: (args) => {
    return (
      <div>
        <div className="text-xs text-neutral-500 mb-2">
          Click the Collapse button to see the collapsed state
        </div>
        <RoadmapSummaryPanel {...args} />
      </div>
    );
  },
};

/**
 * Summary panel with no arcs (empty state).
 */
export const Empty: Story = {
  args: {
    arcs: [],
    onViewAllHeroes: () => console.log('View All Heroes clicked'),
    onViewAllVillains: () => console.log('View All Villains clicked'),
    onRunConsistencyCheck: () => console.log('Run Consistency Check clicked'),
  },
};
