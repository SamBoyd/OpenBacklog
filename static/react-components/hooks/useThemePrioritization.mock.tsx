// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useThemePrioritization';
import { ThemeDto } from '#api/productStrategy';

export const useThemePrioritization = fn(actual.useThemePrioritization).mockName('useThemePrioritization');


export const mockPrioritizedThemes: ThemeDto[] = [
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

export const mockUnprioritizedThemes: ThemeDto[] = [
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

export const mockUseThemePrioritizationReturn = {
    prioritizedThemes: mockPrioritizedThemes,
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
}