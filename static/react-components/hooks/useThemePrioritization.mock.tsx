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
        description: 'New users struggle to start quickly. Guided onboarding reduces time to first value. We will measure success through onboarding completion and time to first plan over a 3-month horizon.',
        outcome_ids: ['outcome-1'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
    },
    {
        id: 'theme-2',
        workspace_id: 'workspace-1',
        name: 'Advanced Analytics Dashboard',
        description: 'Teams lack visibility into progress and outcomes. Customizable real-time dashboards improve decision-making. We will measure success through dashboard usage and outcome completion rate over a 6-month horizon.',
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
        description: 'Users need access on mobile devices. Mobile app increases engagement. We will measure success through Mobile DAU over a 12-month horizon.',
        outcome_ids: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
    },
    {
        id: 'theme-4',
        workspace_id: 'workspace-1',
        name: 'API Rate Limiting',
        description: 'Need to protect API from abuse. Rate limiting prevents service degradation. We will measure success through API uptime over a 6-month horizon.',
        outcome_ids: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
    },
    {
        id: 'theme-5',
        workspace_id: 'workspace-1',
        name: 'Internationalization',
        description: 'Global users need localized experience. i18n increases international adoption. We will measure success through users by region over a 9-month horizon.',
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