import type { Meta, StoryObj } from '@storybook/react';
import StoryArcDetail from '../../pages/Narrative/StoryArcDetail/StoryArcDetail';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useStoryArcDetail } from '#hooks/useStoryArcDetail.mock';
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import { mockWorkspace, mockWorkspacesReturn } from '#stories/example_data';
import {
  mockArc,
  mockHero,
  mockVillains,
  mockThemes,
  mockBeats,
  mockConflicts,
  mockMetrics,
} from './mockData';

const meta: Meta<typeof StoryArcDetail> = {
  title: 'Pages/StrategyAndRoadmap/StoryArcDetail',
  component: StoryArcDetail,
  parameters: {
    layout: 'fullscreen',
    reactRouter: reactRouterParameters({
      location: {
        pathParams: { arcId: 'arc-1' },
      },
      routing: { path: '/workspace/story-bible/arc/:arcId' },
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
      useStoryArcDetail.mockReturnValue({
        arc: mockArc,
        hero: mockHero,
        villains: mockVillains,
        themes: mockThemes,
        beats: mockBeats,
        conflicts: mockConflicts,
        metrics: mockMetrics,
        isLoading: false,
        error: null,
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
      useStoryArcDetail.mockReturnValue({
        arc: null,
        hero: null,
        villains: [],
        themes: [],
        beats: [],
        conflicts: [],
        metrics: mockMetrics,
        isLoading: true,
        error: null,
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
      useStoryArcDetail.mockReturnValue({
        arc: null,
        hero: null,
        villains: [],
        themes: [],
        beats: [],
        conflicts: [],
        metrics: mockMetrics,
        isLoading: false,
        error: 'Failed to load story arc. The server is not responding.',
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
      useStoryArcDetail.mockReturnValue({
        arc: null,
        hero: null,
        villains: [],
        themes: [],
        beats: [],
        conflicts: [],
        metrics: mockMetrics,
        isLoading: false,
        error: null,
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

      useStoryArcDetail.mockReturnValue({
        arc: null,
        hero: null,
        villains: [],
        themes: [],
        beats: [],
        conflicts: [],
        metrics: mockMetrics,
        isLoading: false,
        error: null,
      });
      return <Story />;
    },
  ],
};
