/**
 * Storybook stories for the Strategy Flow Canvas spike.
 * Demonstrates the React Flow visualization with various data sets.
 */

import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import StrategyFlowCanvas from '../../components/strategyFlowSpike/StrategyFlowCanvas';
import { fullData, simpleData, emptyData, disconnectedData, manyInitiativesData } from './mockFlowData';

const meta: Meta<typeof StrategyFlowCanvas> = {
  title: 'Spikes/StrategyFlowCanvas',
  component: StrategyFlowCanvas,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component:
          'React Flow spike for visualizing strategic entities: Pillars → Outcomes → Themes → Initiatives.',
      },
    },
  },
  decorators: [
    (Story) => (
      <div style={{ width: '100vw', height: 'calc(100vh - 2rem)' }}>
        <Story />
      </div>
    ),
  ],
  argTypes: {
    onNodeClick: { action: 'nodeClicked' },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Full visualization with all entity types and connections.
 * Shows 2 pillars, 3 outcomes, 2 themes, and 3 initiatives.
 */
export const FullVisualization: Story = {
  args: {
    ...fullData,
    onNodeClick: fn(),
  },
};

/**
 * Simplified visualization with minimal entities.
 * Good for testing basic rendering and interactions.
 */
export const SimpleVisualization: Story = {
  args: {
    ...simpleData,
    onNodeClick: fn(),
  },
};

/**
 * Empty state when no entities are provided.
 * Shows a helpful message to the user.
 */
export const EmptyState: Story = {
  args: {
    ...emptyData,
    onNodeClick: fn(),
  },
};

/**
 * Data with disconnected initiatives (not linked to any theme).
 * Tests handling of null theme_identifier.
 */
export const WithDisconnectedInitiatives: Story = {
  args: {
    ...disconnectedData,
    onNodeClick: fn(),
  },
};

/**
 * Dark mode visualization.
 * Uses Storybook's theme switcher to test dark mode styling.
 */
export const DarkMode: Story = {
  args: {
    ...fullData,
    onNodeClick: fn(),
  },
  parameters: {
    backgrounds: { default: 'dark' },
  },
  decorators: [
    (Story) => (
      <div className="dark" style={{ width: '100vw', height: 'calc(100vh - 2rem)' }}>
        <Story />
      </div>
    ),
  ],
};

/**
 * Many initiatives distributed across themes.
 * Tests the wide layout problem when many initiatives exist.
 * Use this to experiment with alternative initiative tier layouts.
 */
export const ManyInitiatives: Story = {
  args: {
    ...manyInitiativesData,
    onNodeClick: fn(),
  },
};
