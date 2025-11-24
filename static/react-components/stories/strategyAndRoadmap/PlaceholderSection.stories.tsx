import type { Meta, StoryObj } from '@storybook/react';
import PlaceholderSection from '../../pages/Narrative/StoryArcDetail/PlaceholderSection';

const meta: Meta<typeof PlaceholderSection> = {
  title: 'Components/Narrative/StoryArcDetail/PlaceholderSection',
  component: PlaceholderSection,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default placeholder with an action button.
 * Shows empty state with a call-to-action for adding content.
 */
export const Default: Story = {
  args: {
    title: 'Foreshadowing',
    emptyMessage: 'No foreshadowing elements defined yet. Add hints about future developments in this arc.',
    actionButton: {
      label: 'Add Foreshadowing',
      onClick: () => console.log('Add Foreshadowing clicked'),
    },
  },
};

/**
 * Placeholder without an action button.
 * Used when the section is informational only.
 */
export const NoAction: Story = {
  args: {
    title: 'Related Lore',
    emptyMessage: 'No related lore defined yet. This section will show background information and world-building context.',
  },
};

/**
 * Placeholder with a long multi-line message.
 * Tests layout with verbose empty state messaging.
 */
export const LongMessage: Story = {
  args: {
    title: 'Turning Points',
    emptyMessage: 'No turning points defined yet. Turning points are critical moments in the story arc where the direction changes dramatically. They represent major decisions, discoveries, or events that alter the trajectory of the narrative and push the story toward its climax.',
    actionButton: {
      label: 'Define Turning Point',
      onClick: () => console.log('Define Turning Point clicked'),
    },
  },
};
