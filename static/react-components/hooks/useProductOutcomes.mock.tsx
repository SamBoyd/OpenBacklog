// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useProductOutcomes';
import { OutcomeDto, OutcomeReorderRequest } from '#api/productOutcomes';
import { UseProductOutcomesReturn } from './useProductOutcomes';

export const useProductOutcomes = fn(actual.useProductOutcomes).mockName('useProductOutcomes');

export const mockProductOutcomes: OutcomeDto[] = [
    {
        id: 'outcome-1',
        workspace_id: 'ws-001',
        identifier: 'O-001',
        name: '80% AI feature adoption',
        description: 'Users actively use AI features weekly',
        display_order: 1,
        pillar_ids: ['pillar-1', 'pillar-2'],
        theme_ids: ['theme-1'],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: 'outcome-2',
        workspace_id: 'ws-001',
        identifier: 'O-002',
        name: 'Faster onboarding',
        description: 'Users complete onboarding in under 5 minutes',
        display_order: 2,
        pillar_ids: ['pillar-1'],
        theme_ids: ['theme-1', 'theme-2'],
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
    {
        id: 'outcome-3',
        workspace_id: 'ws-001',
        identifier: 'O-003',
        name: 'Improved customer support',
        description: 'Customers receive help faster with AI-powered support',
        display_order: 3,
        pillar_ids: ['pillar-2'],
        theme_ids: [],
        created_at: '2025-01-17T10:00:00Z',
        updated_at: '2025-01-17T10:00:00Z',
    },
];

export const mockProductOutcomesReturn: UseProductOutcomesReturn = {
    outcomes: mockProductOutcomes,
    isLoading: false,
    error: null,
    createOutcome: () => Promise.resolve(mockProductOutcomes[0]),
    isCreating: false,
    createError: null,
    updateOutcome: () => Promise.resolve(mockProductOutcomes[0]),
    isUpdating: false,
    updateError: null,
    deleteOutcome: function (outcomeId: string): void {
        throw new Error('Function not implemented.');
    },
    isDeleting: false,
    deleteError: null,
    reorderOutcomes: function (request: OutcomeReorderRequest): void {
        throw new Error('Function not implemented.');
    },
    isReordering: false,
    reorderError: null
};
