// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useStrategicPillars';
import { PillarDto, PillarReorderRequest } from '#api/productStrategy';
import { UseStrategicPillarsReturn } from './useStrategicPillars';

export const useStrategicPillars = fn(actual.useStrategicPillars).mockName('useStrategicPillars');

export const mockStrategicPillars: PillarDto[] = [
    {
        id: 'pillar-1',
        workspace_id: 'ws-001',
        identifier: 'P-001',
        name: 'AI-Native Product Management',
        description: 'Build product management tools designed from the ground up for AI collaboration.',
        display_order: 1,
        outcome_ids: ['outcome-1'],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
    },
    {
        id: 'pillar-2',
        workspace_id: 'ws-001',
        identifier: 'P-002',
        name: 'Developer Experience First',
        description: 'Prioritize the needs of developers over administrative overhead.',
        display_order: 2,
        outcome_ids: ['outcome-3'],
        created_at: '2025-01-16T14:30:00Z',
        updated_at: '2025-01-16T14:30:00Z',
    },
];

export const mockStrategicPillarsReturn: UseStrategicPillarsReturn = {
    pillars: mockStrategicPillars,
    isLoading: false,
    error: null,
    createPillar: () => Promise.resolve(mockStrategicPillars[0]),
    isCreating: false,
    createError: null,
    updatePillar: () => Promise.resolve(mockStrategicPillars[0]),
    isUpdating: false,
    updateError: null,
    deletePillar: function (pillarId: string): void {
        throw new Error('Function not implemented.');
    },
    isDeleting: false,
    deleteError: null,
    reorderPillars: function (request: PillarReorderRequest): void {
        throw new Error('Function not implemented.');
    },
    isReordering: false,
    reorderError: null
};
