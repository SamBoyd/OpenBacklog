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
    metrics: mockMetrics,
    isLoading: false,
    error: null,
    onViewBeat: fn((initiativeId: string) => console.log('View Beat:', initiativeId)),
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
    metrics: mockMetrics,
    isLoading: false,
    error: null,
    onViewBeat: fn((initiativeId: string) => console.log('View Beat:', initiativeId)),
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
    metrics: mockHighProgressMetrics,
    isLoading: false,
    error: null,
    onViewBeat: fn((initiativeId: string) => console.log('View Beat:', initiativeId)),
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
    metrics: mockMetrics,
    isLoading: true,
    error: null,
    onViewBeat: fn((initiativeId: string) => console.log('View Beat:', initiativeId)),
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
    metrics: mockMetrics,
    isLoading: false,
    error: 'Failed to load roadmap theme. Please check your connection and try again.',
    onViewBeat: fn((initiativeId: string) => console.log('View Beat:', initiativeId)),
  },
};
