import type { Meta, StoryObj } from '@storybook/react';
import { RoadmapHeader } from '#components/strategyAndRoadmap/RoadmapHeader';

const meta: Meta<typeof RoadmapHeader> = {
  component: RoadmapHeader,
  title: 'strategyAndRoadmap/RoadmapHeader',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof RoadmapHeader>;

/**
 * Default header with list view selected.
 */
export const Default: Story = {
  args: {
    workspaceName: 'My Workspace',
    activeView: 'list',
    onViewToggle: (view) => console.log('View toggled to:', view),
  },
};

/**
 * Header with timeline view selected.
 */
export const TimelineView: Story = {
  args: {
    workspaceName: 'Engineering Team',
    activeView: 'timeline',
    onViewToggle: (view) => console.log('View toggled to:', view),
  },
};

/**
 * Header with board view selected.
 */
export const BoardView: Story = {
  args: {
    workspaceName: 'Product Roadmap',
    activeView: 'board',
    onViewToggle: (view) => console.log('View toggled to:', view),
  },
};
