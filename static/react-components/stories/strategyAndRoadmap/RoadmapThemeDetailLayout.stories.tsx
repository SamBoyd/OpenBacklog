import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';

import RoadmapThemeDetailLayout from '#pages/Narrative/StoryArcDetail/RoadmapThemeDetailLayout';

import {
  mockArc,
  mockShortArc,
  mockHero,
  mockVillains,
  mockThemes,
  mockBeats,
  mockConflicts,
  mockMetrics,
  mockHighProgressMetrics,
  mockOutcomes,
  mockPillars,
  mockVisionText,
} from './mockData';

const meta: Meta<typeof RoadmapThemeDetailLayout> = {
  title: 'Components/Narrative/RoadmapThemeDetail/RoadmapThemeDetailLayout',
  component: RoadmapThemeDetailLayout,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Full layout with all sections rendered and complete data.
 * Demonstrates the complete roadmap theme detail page.
 */
export const FullLayout: Story = {
  args: {
    arc: mockArc,
    hero: mockHero,
    villains: mockVillains,
    themes: mockThemes,
    beats: mockBeats,
    conflicts: mockConflicts,
    outcomes: mockOutcomes,
    pillars: mockPillars,
    visionText: mockVisionText,
    metrics: mockMetrics,
    isLoading: false,
    error: null,
    onViewOutcome: fn((outcomeId: string) => console.log('View Outcome:', outcomeId)),
    onViewHero: fn((heroId: string) => console.log('View Hero:', heroId)),
    onViewVillain: fn((villainId: string) => console.log('View Villain:', villainId)),
  },
};

/**
 * Mobile/tablet responsive layout.
 * Tests stacked layout on smaller screens.
 */
export const MobileLayout: Story = {
  args: {
    arc: mockShortArc,
    hero: mockHero,
    villains: mockVillains.slice(0, 2),
    themes: mockThemes.slice(0, 2),
    beats: mockBeats.slice(0, 2),
    conflicts: mockConflicts.slice(0, 1),
    outcomes: mockOutcomes.slice(0, 2),
    pillars: mockPillars,
    visionText: mockVisionText,
    metrics: mockMetrics,
    isLoading: false,
    error: null,
    onViewOutcome: fn((outcomeId: string) => console.log('View Outcome:', outcomeId)),
    onViewHero: fn((heroId: string) => console.log('View Hero:', heroId)),
    onViewVillain: fn((villainId: string) => console.log('View Villain:', villainId)),
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};

/**
 * Tablet layout with medium-width responsive design.
 * Tests layout behavior at tablet breakpoints.
 */
export const TabletLayout: Story = {
  args: {
    arc: mockArc,
    hero: mockHero,
    villains: mockVillains.slice(0, 3),
    themes: mockThemes.slice(0, 2),
    beats: mockBeats.slice(0, 3),
    conflicts: mockConflicts.slice(0, 2),
    outcomes: mockOutcomes,
    pillars: mockPillars,
    visionText: mockVisionText,
    metrics: mockHighProgressMetrics,
    isLoading: false,
    error: null,
    onViewOutcome: fn((outcomeId: string) => console.log('View Outcome:', outcomeId)),
    onViewHero: fn((heroId: string) => console.log('View Hero:', heroId)),
    onViewVillain: fn((villainId: string) => console.log('View Villain:', villainId)),
  },
  parameters: {
    viewport: {
      defaultViewport: 'tablet',
    },
  },
};

/**
 * Loading state with skeleton loaders in all sections.
 * Shows loading placeholders across the entire page.
 */
export const LoadingState: Story = {
  args: {
    arc: null,
    hero: null,
    villains: [],
    themes: [],
    beats: [],
    conflicts: [],
    outcomes: [],
    pillars: [],
    visionText: null,
    metrics: mockMetrics,
    isLoading: true,
    error: null,
    onViewOutcome: fn((outcomeId: string) => console.log('View Outcome:', outcomeId)),
    onViewHero: fn((heroId: string) => console.log('View Hero:', heroId)),
    onViewVillain: fn((villainId: string) => console.log('View Villain:', villainId)),
  },
};

/**
 * Error state with error message and retry button.
 * Shows error handling for failed data fetch.
 */
export const ErrorState: Story = {
  args: {
    arc: null,
    hero: null,
    villains: [],
    themes: [],
    beats: [],
    conflicts: [],
    outcomes: [],
    pillars: [],
    visionText: null,
    metrics: mockMetrics,
    isLoading: false,
    error: 'Failed to load roadmap theme. Please check your connection and try again.',
    onViewOutcome: fn((outcomeId: string) => console.log('View Outcome:', outcomeId)),
    onViewHero: fn((heroId: string) => console.log('View Hero:', heroId)),
    onViewVillain: fn((villainId: string) => console.log('View Villain:', villainId)),
  },
};
