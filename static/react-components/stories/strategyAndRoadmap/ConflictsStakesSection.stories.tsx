import type { Meta, StoryObj } from '@storybook/react';
import ConflictsStakesSection from '../../pages/Narrative/StoryArcDetail/ConflictsStakesSection';
import { mockConflicts } from './mockData';
import { ConflictStatus } from '#types';

const meta: Meta<typeof ConflictsStakesSection> = {
  title: 'Components/Narrative/StoryArcDetail/ConflictsStakesSection',
  component: ConflictsStakesSection,
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
 * Default state with multiple conflicts of different statuses.
 * Shows active, emerging, and resolved conflicts with stakes section.
 */
export const WithConflicts: Story = {
  args: {
    conflicts: mockConflicts,
    arcId: 'arc-1',
    onAddConflict: () => console.log('Add Conflict clicked'),
  },
};

/**
 * Empty state with no conflicts defined.
 * Displays placeholder messaging.
 */
export const NoConflicts: Story = {
  args: {
    conflicts: [],
    arcId: 'arc-1',
    onAddConflict: () => console.log('Add Conflict clicked'),
  },
};

/**
 * Shows conflicts and stakes together.
 * Full section with active conflicts.
 */
export const ConflictsAndStakes: Story = {
  args: {
    conflicts: mockConflicts.filter((c) => c.status === ConflictStatus.OPEN || c.status === ConflictStatus.ESCALATING),
    arcId: 'arc-1',
    onAddConflict: () => console.log('Add Conflict clicked'),
  },
};

/**
 * Shows only resolved conflicts.
 * Tests display when stakes data is not yet implemented.
 */
export const NoStakesData: Story = {
  args: {
    conflicts: mockConflicts.filter((c) => c.status === ConflictStatus.RESOLVED),
    arcId: 'arc-1',
    onAddConflict: () => console.log('Add Conflict clicked'),
  },
};
