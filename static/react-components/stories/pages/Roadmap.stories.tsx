import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import Roadmap from '#pages/Roadmap';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useRoadmapWithInitiatives } from '#hooks/useRoadmapWithInitiatives.mock';
import { mockWorkspacesReturn } from '#stories/example_data';
import { ThemeWithInitiatives } from '#hooks/useRoadmapWithInitiatives';
import { StrategicInitiativeDto } from '#types';
import AppBackground from '#components/AppBackground';

// Mock strategic initiatives
const mockStrategicInitiatives: StrategicInitiativeDto[] = [
  {
    id: 'si-1',
    initiative_id: 'init-1',
    workspace_id: 'workspace-1',
    pillar_id: 'pillar-1',
    theme_id: 'theme-1',
    description: 'Users need quick guidance to get started with the platform',
    narrative_intent: 'Aligns with ease of use and reduces onboarding friction',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    initiative: {
      id: 'init-1',
      identifier: 'I-001',
      title: 'Build onboarding wizard',
    },
  },
  {
    id: 'si-2',
    initiative_id: 'init-2',
    workspace_id: 'workspace-1',
    pillar_id: null,
    theme_id: 'theme-1',
    description: 'Users need help getting started with core features',
    narrative_intent: 'Reduces time to value and improves user retention',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    initiative: {
      id: 'init-2',
      identifier: 'I-002',
      title: 'Add contextual help tooltips',
    },
  },
  {
    id: 'si-3',
    initiative_id: 'init-3',
    workspace_id: 'workspace-1',
    pillar_id: 'pillar-2',
    theme_id: 'theme-2',
    description: 'Teams need visibility into progress and outcomes',
    narrative_intent: 'Enables data-driven decisions and improves team alignment',
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
    initiative: {
      id: 'init-3',
      identifier: 'I-003',
      title: 'Create real-time metrics dashboard',
    },
  },
];

// Mock themes with initiatives
const mockPrioritizedThemes: ThemeWithInitiatives[] = [
  {
    id: 'theme-1',
    workspace_id: 'workspace-1',
    name: 'Onboarding Experience Redesign',
    description: 'New users struggle to start quickly and often abandon before creating their first plan. User research shows confusion about core features and workflow. Guided onboarding reduces time to first value.',
    outcome_ids: ['outcome-1'],
    hero_ids: [],
    villain_ids: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    strategicInitiatives: mockStrategicInitiatives.filter(si => si.theme_id === 'theme-1'),
    isLoadingInitiatives: false,
  },
  {
    id: 'theme-2',
    workspace_id: 'workspace-1',
    name: 'Advanced Analytics Dashboard',
    description: 'Teams lack visibility into progress and outcomes. Customizable real-time dashboards improve decision-making and enable data-driven choices.',
    outcome_ids: ['outcome-2', 'outcome-3'],
    hero_ids: [],
    villain_ids: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    strategicInitiatives: mockStrategicInitiatives.filter(si => si.theme_id === 'theme-2'),
    isLoadingInitiatives: false,
  },
];

const mockUnprioritizedThemes: ThemeWithInitiatives[] = [
  {
    id: 'theme-3',
    workspace_id: 'workspace-1',
    name: 'Mobile App Development',
    description: 'Users need access on mobile devices. A mobile app would increase engagement and allow users to stay connected on the go.',
    outcome_ids: [],
    hero_ids: [],
    villain_ids: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    strategicInitiatives: [],
    isLoadingInitiatives: false,
  },
  {
    id: 'theme-4',
    workspace_id: 'workspace-1',
    name: 'API Rate Limiting',
    description: 'Need to protect API from abuse and ensure fair usage across all customers.',
    outcome_ids: [],
    hero_ids: [],
    villain_ids: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    strategicInitiatives: [],
    isLoadingInitiatives: false,
  },
];

const meta: Meta<typeof Roadmap> = {
  component: Roadmap,
  parameters: {
    layout: 'fullscreen',
  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
  },
  decorators: [
    (Story) => {
      return (
        <AppBackground>
          <Story />
        </AppBackground>
      );
    },
  ],
};

export default meta;
type Story = StoryObj<typeof Roadmap>;

export const WithThemesAndInitiatives: Story = {
  args: {},
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useRoadmapWithInitiatives.mockReturnValue({
      prioritizedThemes: mockPrioritizedThemes,
      unprioritizedThemes: mockUnprioritizedThemes,
      isLoading: false,
      isLoadingInitiatives: false,
      error: null,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
    });

    return () => {
      useWorkspaces.mockReset();
      useRoadmapWithInitiatives.mockReset();
    };
  },
};

export const LoadingInitiatives: Story = {
  args: {},
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useRoadmapWithInitiatives.mockReturnValue({
      prioritizedThemes: mockPrioritizedThemes.map(theme => ({
        ...theme,
        isLoadingInitiatives: true,
        strategicInitiatives: [],
      })),
      unprioritizedThemes: mockUnprioritizedThemes,
      isLoading: false,
      isLoadingInitiatives: true,
      error: null,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
    });

    return () => {
      useWorkspaces.mockReset();
      useRoadmapWithInitiatives.mockReset();
    };
  },
};

export const EmptyRoadmap: Story = {
  args: {},
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useRoadmapWithInitiatives.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
      isLoading: false,
      isLoadingInitiatives: false,
      error: null,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
    });

    return () => {
      useWorkspaces.mockReset();
      useRoadmapWithInitiatives.mockReset();
    };
  },
};

export const LoadingState: Story = {
  args: {},
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useRoadmapWithInitiatives.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
      isLoading: true,
      isLoadingInitiatives: false,
      error: null,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
    });

    return () => {
      useWorkspaces.mockReset();
      useRoadmapWithInitiatives.mockReset();
    };
  },
};

export const ErrorState: Story = {
  args: {},
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useRoadmapWithInitiatives.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
      isLoading: false,
      isLoadingInitiatives: false,
      error: new Error('Failed to load roadmap themes'),
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
    });

    return () => {
      useWorkspaces.mockReset();
      useRoadmapWithInitiatives.mockReset();
    };
  },
};
