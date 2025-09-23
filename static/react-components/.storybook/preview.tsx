import React from 'react';

import type { Preview } from '@storybook/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { initialize, mswLoader } from 'msw-storybook-addon';
import { withRouter } from 'storybook-addon-remix-react-router';

import { ActiveEntityProvider } from '#hooks/useActiveEntity';
import { UserPreferencesProvider } from '#hooks/useUserPreferences';
import { AiImprovementsContextProvider } from '#contexts/AiImprovementsContext.mock';
import { fetchCurrentWorkspace } from '#services/workspaceApi.mock'
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';

import '../styles/output.css';

import {
  mockFieldDefinitionsReturn,
  mockUseTasksContext,
  mockWorkspace
} from '#stories/example_data';

/*
 * Initializes MSW
 * See https://github.com/mswjs/msw-storybook-addon#configuring-msw
 * to learn how to customize it
 */
initialize();

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
  loaders: [mswLoader],
  decorators: [
    withRouter,
    // 👇 Defining the decorator in the preview file applies it to all stories
    (Story) => {
      useTasksContext.mockReturnValue(mockUseTasksContext);
      fetchCurrentWorkspace.mockResolvedValue(mockWorkspace);
      useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);

      return (
        <QueryClientProvider client={queryClient}>
          <ActiveEntityProvider>
            <UserPreferencesProvider>
              <AiImprovementsContextProvider>
                  <Story />
              </AiImprovementsContextProvider>
            </UserPreferencesProvider>
          </ActiveEntityProvider>
        </QueryClientProvider>
      );
    },
    (Story) => {
      return <Story />;
    },
  ],
};

export default preview;
