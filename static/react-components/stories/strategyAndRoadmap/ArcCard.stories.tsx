import type { Meta, StoryObj } from '@storybook/react';
import { ArcCard } from '#components/strategyAndRoadmap/ArcCard';
import { mockStoryArcs } from '#hooks/strategyAndRoadmap/useStoryArcs.mock';

const meta: Meta<typeof ArcCard> = {
  component: ArcCard,
  title: 'strategyAndRoadmap/ArcCard',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ArcCard>;

/**
 * Arc card in "In Progress" status with partial completion.
 */
export const InProgress: Story = {
  args: {
    arc: mockStoryArcs[0],
    onViewArc: () => console.log('View Arc clicked'),
    onViewBeats: () => console.log('View Beats clicked'),
    onEdit: () => console.log('Edit clicked'),
    onMoreOptions: () => console.log('More Options clicked'),
  },
};

/**
 * Arc card in "Complete" status showing full progress.
 */
export const Complete: Story = {
  args: {
    arc: mockStoryArcs[1],
    onViewArc: () => console.log('View Arc clicked'),
    onViewBeats: () => console.log('View Retrospective clicked'),
    onEdit: () => console.log('Edit clicked'),
    onMoreOptions: () => console.log('More Options clicked'),
  },
};

/**
 * Arc card in "Planned" status with no progress.
 */
export const Planned: Story = {
  args: {
    arc: mockStoryArcs[2],
    onViewArc: () => console.log('View Arc clicked'),
    onViewBeats: () => console.log('View Beats clicked'),
    onEdit: () => console.log('Edit clicked'),
    onMoreOptions: () => console.log('More Options clicked'),
  },
};

/**
 * Arc card with multiple heroes and villains.
 */
export const MultipleNarratives: Story = {
  args: {
    arc: mockStoryArcs[3],
    onViewArc: () => console.log('View Arc clicked'),
    onViewBeats: () => console.log('View Beats clicked'),
    onEdit: () => console.log('Edit clicked'),
    onMoreOptions: () => console.log('More Options clicked'),
  },
};
