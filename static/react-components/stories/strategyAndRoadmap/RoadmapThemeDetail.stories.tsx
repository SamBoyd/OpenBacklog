import type { Meta, StoryObj } from '@storybook/react';
import RoadmapThemeDetail from '../../pages/Narrative/StoryArcDetail/RoadmapThemeDetail';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useRoadmapThemeDetail } from '#hooks/useRoadmapThemeDetail.mock';

const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import { mockWorkspace, mockWorkspacesReturn } from '#stories/example_data';
import {
  mockArc,
  mockHero,
  mockVillains,
  mockBeats,
  mockConflicts,
  mockMetrics,
  mockOutcomes,
  mockVisionText,
  mockPillars,
} from './mockData';

const meta: Meta<typeof RoadmapThemeDetail> = {
  title: 'Pages/StrategyAndRoadmap/RoadmapThemeDetail',
  component: RoadmapThemeDetail,
  parameters: {
    layout: 'fullscreen',
    reactRouter: reactRouterParameters({
      location: {
        pathParams: { themeId: 'theme-1' },
      },
      routing: { path: '/workspace/story-bible/theme/:themeId' },
    }),
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => {
      // Mock workspace context
      useWorkspaces.mockReturnValue(mockWorkspacesReturn);

      return <Story />;
    },
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Loaded state with full arc data displayed.
 * Shows complete story arc detail with all sections populated.
 */
export const Loaded: Story = {
  decorators: [
    (Story) => {
      useRoadmapThemeDetail.mockReturnValue({
        arc: mockArc,
        hero: mockHero,
        villains: mockVillains,
        beats: mockBeats,
        conflicts: mockConflicts,
        metrics: mockMetrics,
        isLoading: false,
        error: null,
        outcomes: mockOutcomes,
        pillars: mockPillars,
        visionText: mockVisionText,
      });
      return <Story />;
    },
  ],
};

/**
 * Loading state with skeleton loaders.
 * Shows loading placeholders while data is being fetched.
 */
export const Loading: Story = {
  decorators: [
    (Story) => {
      useRoadmapThemeDetail.mockReturnValue({
        arc: null,
        hero: null,
        villains: [],
        beats: [],
        conflicts: [],
        metrics: mockMetrics,
        isLoading: true,
        error: null,
        outcomes: [],
        visionText: null,
        pillars: [],
      });
      return <Story />;
    },
  ],
};

/**
 * Error state with retry button.
 * Shows error message when data fetch fails.
 */
export const Error: Story = {
  decorators: [
    (Story) => {
      useRoadmapThemeDetail.mockReturnValue({
        arc: null,
        hero: null,
        villains: [],
        beats: [],
        conflicts: [],
        metrics: mockMetrics,
        isLoading: false,
        error: 'Failed to load story arc. The server is not responding.',
        outcomes: [],
        visionText: null,
        pillars: [],
      });
      return <Story />;
    },
  ],
};

/**
 * Arc not found state.
 * Shows message when the requested arc doesn't exist.
 */
export const NoArc: Story = {
  decorators: [
    (Story) => {
      useRoadmapThemeDetail.mockReturnValue({
        arc: null,
        hero: null,
        villains: [],
        beats: [],
        conflicts: [],
        metrics: mockMetrics,
        isLoading: false,
        error: null,
        outcomes: [],
        visionText: null,
        pillars: [],
      });
      return <Story />;
    },
  ],
};

/**
 * No workspace selected state.
 * Shows error when workspace context is missing.
 */
export const NoWorkspace: Story = {
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: null,
        workspaces: [],
        isLoading: false,
        error: null,
        changeWorkspace: async () => { },
        addWorkspace: async () => mockWorkspace,
        refresh: () => { },
        isProcessing: false,
      });

      useRoadmapThemeDetail.mockReturnValue({
        arc: null,
        hero: null,
        villains: [],
        beats: [],
        conflicts: [],
        metrics: mockMetrics,
        isLoading: false,
        error: null,
        outcomes: [],
        visionText: null,
        pillars: [],
      });
      return <Story />;
    },
  ],
};
