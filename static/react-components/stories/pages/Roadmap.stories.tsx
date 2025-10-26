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
    user_need: 'Users need quick guidance',
    connection_to_vision: 'Aligns with ease of use',
    success_criteria: 'Completion rate > 80%',
    out_of_scope: 'Advanced features',
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
    user_need: 'Users need help getting started',
    connection_to_vision: 'Reduces time to value',
    success_criteria: 'Time to first plan < 5 min',
    out_of_scope: 'Video tutorials',
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
    user_need: 'Teams need visibility',
    connection_to_vision: 'Enables data-driven decisions',
    success_criteria: 'Dashboard adoption > 70%',
    out_of_scope: 'Predictive analytics',
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
    problem_statement: 'New users struggle to start quickly and often abandon before creating their first plan. User research shows confusion about core features and workflow.',
    hypothesis: 'Guided onboarding reduces time to first value.',
    indicative_metrics: 'Onboarding completion rate, time to first plan',
    time_horizon_months: 3,
    outcome_ids: ['outcome-1'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    strategicInitiatives: mockStrategicInitiatives.filter(si => si.theme_id === 'theme-1'),
    isLoadingInitiatives: false,
  },
  {
    id: 'theme-2',
    workspace_id: 'workspace-1',
    name: 'Advanced Analytics Dashboard',
    problem_statement: 'Teams lack visibility into progress and outcomes.',
    hypothesis: 'Customizable real-time dashboards improve decision-making.',
    indicative_metrics: 'Dashboard usage, outcome completion rate',
    time_horizon_months: 6,
    outcome_ids: ['outcome-2', 'outcome-3'],
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
    problem_statement: 'Users need access on mobile devices.',
    hypothesis: 'Mobile app increases engagement.',
    indicative_metrics: 'Mobile DAU',
    time_horizon_months: 12,
    outcome_ids: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    strategicInitiatives: [],
    isLoadingInitiatives: false,
  },
  {
    id: 'theme-4',
    workspace_id: 'workspace-1',
    name: 'API Rate Limiting',
    problem_statement: 'Need to protect API from abuse.',
    hypothesis: null,
    indicative_metrics: null,
    time_horizon_months: null,
    outcome_ids: [],
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
