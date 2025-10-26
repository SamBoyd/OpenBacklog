import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import ThemeSidebar from '#components/ThemeSidebar';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { mockUseThemePrioritizationReturn, useThemePrioritization } from '#hooks/useThemePrioritization.mock';
import { mockWorkspacesReturn } from '#stories/example_data';
import { ThemeDto } from '#api/productStrategy';

const mockPrioritizedThemes: ThemeDto[] = [
  {
    id: 'theme-1',
    workspace_id: 'workspace-1',
    name: 'Onboarding Experience Redesign',
    problem_statement: 'New users struggle to start quickly.',
    hypothesis: 'Guided onboarding reduces time to first value.',
    indicative_metrics: 'Onboarding completion, time to first plan',
    time_horizon_months: 3,
    outcome_ids: ['outcome-1'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
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
  },
];

const mockUnprioritizedThemes: ThemeDto[] = [
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
  },
  {
    id: 'theme-4',
    workspace_id: 'workspace-1',
    name: 'API Rate Limiting',
    problem_statement: 'Need to protect API from abuse.',
    hypothesis: 'Rate limiting prevents service degradation.',
    indicative_metrics: 'API uptime',
    time_horizon_months: 6,
    outcome_ids: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'theme-5',
    workspace_id: 'workspace-1',
    name: 'Internationalization',
    problem_statement: 'Global users need localized experience.',
    hypothesis: 'i18n increases international adoption.',
    indicative_metrics: 'Users by region',
    time_horizon_months: 9,
    outcome_ids: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const meta: Meta<typeof ThemeSidebar> = {
  component: ThemeSidebar,
  decorators: [
    (Story) => {
      return (
        <div className="flex h-screen">
          <Story />
          <div className="flex-1 bg-background p-8">
            <p className="text-muted-foreground">Main content area</p>
          </div>
        </div>
      );
    },
  ],
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
  },
};

export default meta;
type Story = StoryObj<typeof ThemeSidebar>;

export const WithPrioritizedAndUnprioritized: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',
  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useThemePrioritization.mockReturnValue(mockUseThemePrioritizationReturn);

    return () => {
      useWorkspaces.mockReset();
      useThemePrioritization.mockReset();
    };
  },
};

export const OnlyPrioritized: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',
  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useThemePrioritization.mockReturnValue({
      prioritizedThemes: mockPrioritizedThemes,
      unprioritizedThemes: [],
      isLoadingPrioritized: false,
      prioritizedError: null,
      isLoadingUnprioritized: false,
      unprioritizedError: null,
      isLoading: false,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      prioritizeError: null,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      deprioritizeError: null,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
      reorderError: null,
    });

    return () => {
      useWorkspaces.mockReset();
      useThemePrioritization.mockReset();
    };
  },
};

export const OnlyUnprioritized: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',
  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useThemePrioritization.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: mockUnprioritizedThemes,
      isLoadingPrioritized: false,
      prioritizedError: null,
      isLoadingUnprioritized: false,
      unprioritizedError: null,
      isLoading: false,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      prioritizeError: null,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      deprioritizeError: null,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
      reorderError: null,
    });

    return () => {
      useWorkspaces.mockReset();
      useThemePrioritization.mockReset();
    };
  },
};

export const Empty: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',
  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useThemePrioritization.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
      isLoadingPrioritized: false,
      prioritizedError: null,
      isLoadingUnprioritized: false,
      unprioritizedError: null,
      isLoading: false,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      prioritizeError: null,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      deprioritizeError: null,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
      reorderError: null,
    });

    return () => {
      useWorkspaces.mockReset();
      useThemePrioritization.mockReset();
    };
  },
};

export const LoadingState: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',
  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useThemePrioritization.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
      isLoadingPrioritized: true,
      prioritizedError: null,
      isLoadingUnprioritized: true,
      unprioritizedError: null,
      isLoading: true,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      prioritizeError: null,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      deprioritizeError: null,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
      reorderError: null,
    });

    return () => {
      useWorkspaces.mockReset();
      useThemePrioritization.mockReset();
    };
  },
};

export const ErrorState: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',
  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useThemePrioritization.mockReturnValue({
      prioritizedThemes: [],
      unprioritizedThemes: [],
      isLoadingPrioritized: false,
      prioritizedError: new Error('Failed to fetch prioritized themes'),
      isLoadingUnprioritized: false,
      unprioritizedError: new Error('Failed to fetch unprioritized themes'),
      isLoading: false,
      prioritizeTheme: ({ themeId, position }: { themeId: string; position: number }) => {
        console.log(`Prioritizing theme ${themeId} at position ${position}`);
      },
      isPrioritizing: false,
      prioritizeError: null,
      deprioritizeTheme: (themeId: string) => {
        console.log(`Deprioritizing theme ${themeId}`);
      },
      isDeprioritizing: false,
      deprioritizeError: null,
      reorderPrioritizedThemes: (request: any) => {
        console.log('Reordering prioritized themes:', request);
      },
      isReordering: false,
      reorderError: null,
    });

    return () => {
      useWorkspaces.mockReset();
      useThemePrioritization.mockReset();
    };
  },
};
