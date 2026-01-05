/**
 * Storybook stories for the Strategy Flow Canvas spike.
 * Demonstrates the React Flow visualization with various data sets.
 */

import type { Meta, StoryObj } from '@storybook/react';
const { reactRouterParameters, reactRouterNestedAncestors } = require('storybook-addon-remix-react-router');


import StrategyFlowPage from '#pages/StrategyFlowPage';
import { mockLocationReturn, mockInitiativesContextReturn, mockUserPreferencesReturn, mockUseTasksContext, mockWorkspacesReturn, mockWorkspace } from '#stories/example_data';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import NavBar from '#components/reusable/NavBar';
import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';
import { mockUseThemePrioritizationReturn, useThemePrioritization } from '#hooks/useThemePrioritization.mock';
import { useLocation } from '#hooks/useLocation.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { useUserPreferences } from '#hooks/useUserPreferences.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useProductVision } from '#hooks/useProductVision.mock';
import { mockStrategicPillarsReturn, useStrategicPillars } from '#hooks/useStrategicPillars.mock';
import { mockProductOutcomesReturn, useProductOutcomes } from '#hooks/useProductOutcomes.mock';
import { useRoadmapWithInitiatives } from '#hooks/useRoadmapWithInitiatives.mock';
import { mockThemes } from '#stories/strategyAndRoadmap/mockData';
import { ThemeReorderRequest, VisionUpdateRequest } from '#api/productStrategy';
import AppBackground from '#components/AppBackground';

// Create the wrapper structure that matches how StrategyFlowPage is rendered in Main.tsx
const getStrategyFlowPageWithWrappers = () => {
  return reactRouterNestedAncestors([
    {
      element: <div className="inset-0 flex flex-col h-screen w-screen">
        <NavBar />
        <AppBackground>

          <ResponsiveLayout>
            <StrategyFlowPage />
          </ResponsiveLayout>
        </AppBackground>
      </div>
    }
  ]);
};

const meta: Meta<typeof StrategyFlowPage> = {
  title: 'Pages/StrategyFlowPage',
  component: StrategyFlowPage,
  parameters: {
    layout: 'fullscreen',
    reactRouter: reactRouterParameters({
      location: {
        path: '/'
      },
      routing: getStrategyFlowPageWithWrappers()
    })
  },
  decorators: [
    (Story) => (
      <div style={{ width: '100vw', height: 'calc(100vh - 2rem)' }}>
        <Story />
      </div>
    ),
  ],
  argTypes: {
    onNodeClick: { action: 'nodeClicked' },
  },
  async beforeEach() {
    useLocation.mockReturnValue(mockLocationReturn);
    useWorkspaces.mockReturnValue(mockWorkspacesReturn);
    useUserPreferences.mockReturnValue(mockUserPreferencesReturn);
    useThemePrioritization.mockReturnValue(mockUseThemePrioritizationReturn);

    useProductVision.mockReturnValue({
      vision: {
        id: 'vision_id',
        workspace_id: mockWorkspace.id,
        vision_text: "To create something truely awesome",
        created_at: (new Date()).toLocaleString(),
        updated_at: (new Date()).toLocaleString()
      },
      isLoading: false,
      error: null,
      upsertVision: (request: VisionUpdateRequest) => { },
      isUpserting: false,
      upsertError: null
    })
    useStrategicPillars.mockReturnValue(mockStrategicPillarsReturn)
    useProductOutcomes.mockReturnValue(mockProductOutcomesReturn)
    useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
    useRoadmapWithInitiatives.mockReturnValue({
      prioritizedThemes: [
        { ...mockThemes[0], strategicInitiatives: [], isLoadingInitiatives: false },
        { ...mockThemes[1], strategicInitiatives: [], isLoadingInitiatives: false }
      ],
      unprioritizedThemes: [
        { ...mockThemes[2], strategicInitiatives: [], isLoadingInitiatives: false }
      ],
      isLoading: false,
      isLoadingInitiatives: false,
      error: null,
      prioritizeTheme: (request: any) => { },
      isPrioritizing: false,
      deprioritizeTheme: (themeId: string) => { },
      isDeprioritizing: false,
      reorderPrioritizedThemes: (request: ThemeReorderRequest) => { },
      isReordering: false,
    })
    useTasksContext.mockReturnValue(mockUseTasksContext);

    return () => {
      useTasksContext.mockReset();
      useUserPreferences.mockReset();
      useInitiativesContext.mockReset();
      useWorkspaces.mockReset();
    };
  }
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Full visualization with all entity types and connections.
 * Shows 2 pillars, 3 outcomes, 2 themes, and 3 initiatives.
 */
export const FullVisualization: Story = {
  args: {},
};