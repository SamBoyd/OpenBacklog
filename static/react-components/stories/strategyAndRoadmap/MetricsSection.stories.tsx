import type { Meta, StoryObj } from '@storybook/react';
import MetricsSection from '../../pages/Narrative/StoryArcDetail/MetricsSection';
import { mockMetrics, mockHighProgressMetrics, mockLowProgressMetrics, mockZeroMetrics } from './mockData';

const meta: Meta<typeof MetricsSection> = {
  title: 'Components/Narrative/StoryArcDetail/MetricsSection',
  component: MetricsSection,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div className="max-w-4xl w-full">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default metrics showing moderate progress (70% completion).
 * Demonstrates a healthy in-progress story arc.
 */
export const Default: Story = {
  args: {
    completionPercent: mockMetrics.completionPercent,
    scenesComplete: mockMetrics.scenesComplete,
    scenesTotal: mockMetrics.scenesTotal,
    beatsComplete: mockMetrics.beatsComplete,
    beatsInProgress: mockMetrics.beatsInProgress,
    beatsPlanned: mockMetrics.beatsPlanned,
    startDate: mockMetrics.startDate,
    lastActivityDate: mockMetrics.lastActivityDate,
  },
};

/**
 * High progress metrics showing near completion (95%).
 * Arc is almost finished with most beats complete.
 */
export const HighProgress: Story = {
  args: {
    completionPercent: mockHighProgressMetrics.completionPercent,
    scenesComplete: mockHighProgressMetrics.scenesComplete,
    scenesTotal: mockHighProgressMetrics.scenesTotal,
    beatsComplete: mockHighProgressMetrics.beatsComplete,
    beatsInProgress: mockHighProgressMetrics.beatsInProgress,
    beatsPlanned: mockHighProgressMetrics.beatsPlanned,
    startDate: mockHighProgressMetrics.startDate,
    lastActivityDate: mockHighProgressMetrics.lastActivityDate,
  },
};

/**
 * Low progress metrics showing early stage (20%).
 * Arc is just getting started with minimal completion.
 */
export const LowProgress: Story = {
  args: {
    completionPercent: mockLowProgressMetrics.completionPercent,
    scenesComplete: mockLowProgressMetrics.scenesComplete,
    scenesTotal: mockLowProgressMetrics.scenesTotal,
    beatsComplete: mockLowProgressMetrics.beatsComplete,
    beatsInProgress: mockLowProgressMetrics.beatsInProgress,
    beatsPlanned: mockLowProgressMetrics.beatsPlanned,
    startDate: mockLowProgressMetrics.startDate,
    lastActivityDate: mockLowProgressMetrics.lastActivityDate,
  },
};

/**
 * Edge case with all metrics at zero.
 * Tests layout when no progress has been made.
 */
export const AllZeros: Story = {
  args: {
    completionPercent: mockZeroMetrics.completionPercent,
    scenesComplete: mockZeroMetrics.scenesComplete,
    scenesTotal: mockZeroMetrics.scenesTotal,
    beatsComplete: mockZeroMetrics.beatsComplete,
    beatsInProgress: mockZeroMetrics.beatsInProgress,
    beatsPlanned: mockZeroMetrics.beatsPlanned,
    startDate: mockZeroMetrics.startDate,
    lastActivityDate: mockZeroMetrics.lastActivityDate,
  },
};
