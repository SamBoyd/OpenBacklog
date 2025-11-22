import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { RoadmapFilterControls } from '#components/strategyAndRoadmap/RoadmapFilterControls';

const meta: Meta<typeof RoadmapFilterControls> = {
  component: RoadmapFilterControls,
  title: 'Components/StrategyAndRoadmap/RoadmapFilterControls',
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof RoadmapFilterControls>;

/**
 * Default filter controls with quarters zoom selected.
 */
export const Default: Story = {
  args: {
    onZoomChange: (zoom) => console.log('Zoom changed to:', zoom),
  },
};

/**
 * Filter controls with years zoom selected.
 */
export const YearsZoom: Story = {
  args: {
    onZoomChange: (zoom) => console.log('Zoom changed to:', zoom),
  },
  render: (args) => {
    const [zoom, setZoom] = React.useState<'years' | 'quarters' | 'months' | 'weeks'>('years');
    return <RoadmapFilterControls {...args} onZoomChange={(z) => setZoom(z)} />;
  },
};
