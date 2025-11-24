import type { Meta, StoryObj } from '@storybook/react';
import NarrativeConnectionsSection from '../../pages/Narrative/StoryArcDetail/NarrativeConnectionsSection';
import { mockHero, mockSecondaryHero, mockVillains, mockThemes } from './mockData';

const meta: Meta<typeof NarrativeConnectionsSection> = {
  title: 'Components/Narrative/StoryArcDetail/NarrativeConnectionsSection',
  component: NarrativeConnectionsSection,
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
 * Full data with hero, multiple villains, and themes.
 * Demonstrates complete narrative connections.
 */
export const FullData: Story = {
  args: {
    hero: mockHero,
    villains: mockVillains,
    themes: mockThemes,
    onEditLinks: () => console.log('Edit Links clicked'),
  },
};

/**
 * Hero only, no villains or themes.
 * Tests partial data display.
 */
export const HeroOnly: Story = {
  args: {
    hero: mockHero,
    villains: [],
    themes: [],
    onEditLinks: () => console.log('Edit Links clicked'),
  },
};

/**
 * No hero defined for this arc.
 * Shows empty state for hero section.
 */
export const NoHero: Story = {
  args: {
    hero: null,
    villains: mockVillains.slice(0, 2),
    themes: mockThemes.slice(0, 1),
    onEditLinks: () => console.log('Edit Links clicked'),
  },
};

/**
 * Many villains to test display overflow.
 * Shows how component handles more than 3 villains.
 */
export const ManyVillains: Story = {
  args: {
    hero: mockSecondaryHero,
    villains: mockVillains,
    themes: mockThemes.slice(0, 2),
    onEditLinks: () => console.log('Edit Links clicked'),
  },
};

/**
 * All empty states - no connections defined.
 * Tests completely empty narrative connections.
 */
export const NoData: Story = {
  args: {
    hero: null,
    villains: [],
    themes: [],
    onEditLinks: () => console.log('Edit Links clicked'),
  },
};
