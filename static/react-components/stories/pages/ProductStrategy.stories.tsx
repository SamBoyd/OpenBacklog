import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// @ts-ignore
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');

import ProductStrategy from '#pages/ProductStrategy';
import NavBar from '#components/reusable/NavBar';

import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useStrategicPillars } from '#hooks/useStrategicPillars.mock';
import { useProductVision } from '#hooks/useProductVision.mock';
import { useProductOutcomes } from '#hooks/useProductOutcomes.mock';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes.mock';
import { mockWorkspacesReturn } from '#stories/example_data';
import AppBackground from '#components/AppBackground';

const mockVision = {
  id: 'vision-1',
  workspace_id: 'workspace-1',
  vision_text: 'To become the leading platform for product strategy and roadmap planning.',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockPillars = [
  {
    id: 'pillar-1',
    workspace_id: 'workspace-1',
    name: 'User Experience Excellence',
    description: 'Deliver intuitive, accessible, and delightful user experiences across all touchpoints.',
    anti_strategy: 'Complex interfaces that require extensive training or documentation.',
    display_order: 1,
    outcome_ids: ['outcome-1', 'outcome-2'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'pillar-2',
    workspace_id: 'workspace-1',
    name: 'Data-Driven Decision Making',
    description: 'Enable teams to make informed decisions through comprehensive analytics and insights.',
    anti_strategy: 'Gut-feeling based decisions without supporting data or metrics.',
    display_order: 2,
    outcome_ids: ['outcome-3'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockOutcomes = [
  {
    id: 'outcome-1',
    workspace_id: 'workspace-1',
    name: 'Reduce Time to Value',
    description: 'New users create their first strategic plan within 15 minutes of signup.',
    metrics: 'Time to first strategic plan < 15m',
    time_horizon_months: 6,
    display_order: 1,
    pillar_ids: ['pillar-1'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'outcome-2',
    workspace_id: 'workspace-1',
    name: 'Increase User Engagement',
    description: 'Users actively use the platform weekly.',
    metrics: 'WAU/MAU > 0.8',
    time_horizon_months: 12,
    display_order: 2,
    pillar_ids: ['pillar-1'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'outcome-3',
    workspace_id: 'workspace-1',
    name: 'Enable Data-Driven Insights',
    description: 'Track progress against strategic goals with clear metrics.',
    metrics: '90% initiatives have measurable success criteria',
    time_horizon_months: 9,
    display_order: 3,
    pillar_ids: ['pillar-2'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockThemes = [
  {
    id: 'theme-1',
    workspace_id: 'workspace-1',
    name: 'Onboarding Experience Redesign',
    problem_statement: 'New users struggle to start quickly.',
    hypothesis: 'Guided onboarding reduces time to first value.',
    indicative_metrics: 'Onboarding completion, time to first plan',
    time_horizon_months: 3,
    display_order: 1,
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
    display_order: 2,
    outcome_ids: ['outcome-2', 'outcome-3'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockWorkspace = {
  id: 'workspace-1',
  name: 'Product Strategy Workspace',
  icon: null,
  description: 'Main workspace for product strategy planning',
};

const meta: Meta<typeof ProductStrategy> = {
  component: ProductStrategy,
  decorators: [
    (Story) => {
      return (
        <div className="inset-0 flex flex-col h-screen w-screen">
          <NavBar />
          <div className="relative w-screen min-h-screen">
            <AppBackground>
              <Story />
            </AppBackground>
          </div>
        </div>
      )
    }
  ],
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
  },
};

export default meta;
type Story = StoryObj<typeof ProductStrategy>;

export const WithValidData: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',
  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useProductVision.mockReturnValue({
      vision: mockVision,
      isLoading: false,
      error: null,
      upsertVision: () => { },
      isUpserting: false,
      upsertError: null,
    });
    useStrategicPillars.mockReturnValue({
      pillars: mockPillars,
      isLoading: false,
      error: null,
      createPillar: () => { },
      isCreating: false,
      createError: null,
      updatePillar: () => { },
      isUpdating: false,
      updateError: null,
      deletePillar: () => { },
      isDeleting: false,
      deleteError: null,
      reorderPillars: () => { },
      isReordering: false,
      reorderError: null,
    });
    useProductOutcomes.mockReturnValue({
      outcomes: mockOutcomes,
      isLoading: false,
      error: null,
      createOutcome: () => { },
      isCreating: false,
      createError: null,
      updateOutcome: () => { },
      isUpdating: false,
      updateError: null,
      deleteOutcome: () => { },
      isDeleting: false,
      deleteError: null,
      reorderOutcomes: () => { },
      isReordering: false,
      reorderError: null,
    });
    useRoadmapThemes.mockReturnValue({
      themes: mockThemes,
      isLoading: false,
      error: null,
      createTheme: () => { },
      isCreating: false,
      createError: null,
      updateTheme: () => { },
      isUpdating: false,
      updateError: null,
      deleteTheme: () => { },
      isDeleting: false,
      deleteError: null,
      reorderThemes: () => { },
      isReordering: false,
      reorderError: null,
    });

    return () => {
      useWorkspaces.mockReset();
      useProductVision.mockReset();
      useStrategicPillars.mockReset();
      useProductOutcomes.mockReset();
      useRoadmapThemes.mockReset();
    };
  },
};

export const WithNoData: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',

  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useProductVision.mockReturnValue({
      vision: null,
      isLoading: false,
      error: null,
      upsertVision: () => { },
      isUpserting: false,
      upsertError: null,
    });
    useStrategicPillars.mockReturnValue({
      pillars: [],
      isLoading: false,
      error: null,
      createPillar: () => { },
      isCreating: false,
      createError: null,
      updatePillar: () => { },
      isUpdating: false,
      updateError: null,
      deletePillar: () => { },
      isDeleting: false,
      deleteError: null,
      reorderPillars: () => { },
      isReordering: false,
      reorderError: null,
    });
    useProductOutcomes.mockReturnValue({
      outcomes: [],
      isLoading: false,
      error: null,
      createOutcome: () => { },
      isCreating: false,
      createError: null,
      updateOutcome: () => { },
      isUpdating: false,
      updateError: null,
      deleteOutcome: () => { },
      isDeleting: false,
      deleteError: null,
      reorderOutcomes: () => { },
      isReordering: false,
      reorderError: null,
    });
    useRoadmapThemes.mockReturnValue({
      themes: [],
      isLoading: false,
      error: null,
      createTheme: () => { },
      isCreating: false,
      createError: null,
      updateTheme: () => { },
      isUpdating: false,
      updateError: null,
      deleteTheme: () => { },
      isDeleting: false,
      deleteError: null,
      reorderThemes: () => { },
      isReordering: false,
      reorderError: null,
    });

    return () => {
      useWorkspaces.mockReset();
      useProductVision.mockReset();
      useStrategicPillars.mockReset();
      useProductOutcomes.mockReset();
      useRoadmapThemes.mockReset();
    };
  },
};

export const WithLoadingStates: Story = {
  args: {},
  parameters: {
    layout: 'fullscreen',

  },
  async beforeEach() {
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useProductVision.mockReturnValue({
      vision: null,
      isLoading: true,
      error: null,
      upsertVision: () => { },
      isUpserting: false,
      upsertError: null,
    });
    useStrategicPillars.mockReturnValue({
      pillars: [],
      isLoading: true,
      error: null,
      createPillar: () => { },
      isCreating: false,
      createError: null,
      updatePillar: () => { },
      isUpdating: false,
      updateError: null,
      deletePillar: () => { },
      isDeleting: false,
      deleteError: null,
      reorderPillars: () => { },
      isReordering: false,
      reorderError: null,
    });
    useProductOutcomes.mockReturnValue({
      outcomes: [],
      isLoading: true,
      error: null,
      createOutcome: () => { },
      isCreating: false,
      createError: null,
      updateOutcome: () => { },
      isUpdating: false,
      updateError: null,
      deleteOutcome: () => { },
      isDeleting: false,
      deleteError: null,
      reorderOutcomes: () => { },
      isReordering: false,
      reorderError: null,
    });
    useRoadmapThemes.mockReturnValue({
      themes: [],
      isLoading: true,
      error: null,
      createTheme: () => { },
      isCreating: false,
      createError: null,
      updateTheme: () => { },
      isUpdating: false,
      updateError: null,
      deleteTheme: () => { },
      isDeleting: false,
      deleteError: null,
      reorderThemes: () => { },
      isReordering: false,
      reorderError: null,
    });

    return () => {
      useWorkspaces.mockReset();
      useProductVision.mockReset();
      useStrategicPillars.mockReset();
      useProductOutcomes.mockReset();
      useRoadmapThemes.mockReset();
    };
  },
};


