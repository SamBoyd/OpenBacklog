import type { Meta, StoryObj } from '@storybook/react';
import NarrativeContextBar from '../../pages/Narrative/StoryArcDetail/NarrativeContextBar';
import { mockHero, mockSecondaryHero, mockVillains, mockThemes } from './mockData';

const meta: Meta<typeof NarrativeContextBar> = {
  title: 'Components/Narrative/StoryArcDetail/NarrativeContextBar',
  component: NarrativeContextBar,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Full context with hero, villains, themes, and high progress.
 * Shows complete narrative context at a glance.
 */
export const FullContext: Story = {
  args: {
    hero: mockHero,
    villains: mockVillains,
    themes: mockThemes,
    progressPercent: 75,
    healthPercent: 85,
    onHeroClick: (heroId: string) => console.log('Hero clicked:', heroId),
    onVillainClick: (villainId: string) => console.log('Villain clicked:', villainId),
    onThemeClick: (themeId: string) => console.log('Theme clicked:', themeId),
  },
};

/**
 * Minimal context with few entities and low progress.
 * Tests compact display with limited data.
 */
export const MinimalContext: Story = {
  args: {
    hero: mockSecondaryHero,
    villains: [mockVillains[0]],
    themes: [mockThemes[0]],
    progressPercent: 25,
    healthPercent: 60,
    onHeroClick: (heroId: string) => console.log('Hero clicked:', heroId),
    onVillainClick: (villainId: string) => console.log('Villain clicked:', villainId),
    onThemeClick: (themeId: string) => console.log('Theme clicked:', themeId),
  },
};

/**
 * Many villains to test overflow display (shows +X indicator).
 * Tests how component handles more than 3 villains.
 */
export const ManyVillains: Story = {
  args: {
    hero: mockHero,
    villains: mockVillains,
    themes: mockThemes.slice(0, 2),
    progressPercent: 60,
    healthPercent: 70,
    onHeroClick: (heroId: string) => console.log('Hero clicked:', heroId),
    onVillainClick: (villainId: string) => console.log('Villain clicked:', villainId),
    onThemeClick: (themeId: string) => console.log('Theme clicked:', themeId),
  },
};

/**
 * High health indicator (green, 95%).
 * Shows healthy arc status.
 */
export const HighHealth: Story = {
  args: {
    hero: mockHero,
    villains: mockVillains.slice(0, 2),
    themes: mockThemes.slice(0, 2),
    progressPercent: 90,
    healthPercent: 95,
    onHeroClick: (heroId: string) => console.log('Hero clicked:', heroId),
    onVillainClick: (villainId: string) => console.log('Villain clicked:', villainId),
    onThemeClick: (themeId: string) => console.log('Theme clicked:', themeId),
  },
};

/**
 * Low health indicator (red, 40%).
 * Shows arc requiring attention.
 */
export const LowHealth: Story = {
  args: {
    hero: mockHero,
    villains: mockVillains.slice(0, 2),
    themes: mockThemes.slice(0, 1),
    progressPercent: 45,
    healthPercent: 40,
    onHeroClick: (heroId: string) => console.log('Hero clicked:', heroId),
    onVillainClick: (villainId: string) => console.log('Villain clicked:', villainId),
    onThemeClick: (themeId: string) => console.log('Theme clicked:', themeId),
  },
};
