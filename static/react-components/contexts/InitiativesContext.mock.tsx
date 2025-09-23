// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import { InitiativeDto, InitiativeStatus } from '#types';
import { OrderedEntity } from '#hooks/useOrderings';
import { InitiativesContextType } from '#hooks/initiatives';
import * as actual from './InitiativesContext';

/**
 * Mock data for testing and stories
 */
export const mockInitiatives: OrderedEntity<InitiativeDto>[] = [
  {
    id: 'test-initiative-1',
    title: 'Test Initiative 1',
    description: 'Test Description 1',
    status: InitiativeStatus.TO_DO,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    identifier: 'I-001',
    user_id: 'test-user-1',
    type: null,
    tasks: [],
    has_pending_job: null,
    orderings: [],
    orderingId: 'ordering-1',
    position: 'aa'
  },
  {
    id: 'test-initiative-2',
    title: 'Test Initiative 2',
    description: 'Test Description 2',
    status: InitiativeStatus.IN_PROGRESS,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    identifier: 'I-002',
    user_id: 'test-user-1',
    type: 'FEATURE',
    tasks: [],
    has_pending_job: null,
    orderings: [],
    orderingId: 'ordering-2',
    position: 'bb'
  }
];

/**
 * Default mock return value for useInitiativesContext
 */
export const mockInitiativesContextValue: InitiativesContextType = {
  // Query data
  initiativesData: mockInitiatives,
  error: null,
  shouldShowSkeleton: false,
  isQueryFetching: false,
  reloadInitiatives: fn(),

  // Cache operations
  invalidateInitiative: fn(),
  invalidateAllInitiatives: fn(),
  invalidateInitiativesByStatus: fn(),
  updateInitiativeInCache: fn(),

  // Mutation loading states
  isCreatingInitiative: false,
  isUpdatingInitiative: false,
  isDeletingInitiative: false,
  isBatchUpdatingInitiatives: false,
  isDeletingTask: false,
  isDeletingChecklistItem: false,

  // Mutation operations
  createInitiative: fn().mockResolvedValue(mockInitiatives[0]),
  updateInitiative: fn().mockResolvedValue(mockInitiatives[0]),
  updateInitiatives: fn().mockResolvedValue(mockInitiatives),
  deleteInitiative: fn().mockResolvedValue(undefined),
  deleteTask: fn().mockResolvedValue(undefined),
  deleteChecklistItem: fn().mockResolvedValue(undefined),

  // Reordering operations
  reorderInitiative: fn().mockResolvedValue(undefined),
  moveInitiativeToStatus: fn().mockResolvedValue(undefined),
  moveInitiativeInGroup: fn().mockResolvedValue(undefined),
};

/**
 * Mock hook that returns configurable mock data
 */
export const useInitiativesContext = fn(actual.useInitiativesContext)
  .mockName('useInitiativesContext')
  .mockReturnValue(mockInitiativesContextValue);

/**
 * Mock provider component
 */
export const InitiativesProvider = fn(actual.InitiativesProvider).mockName('InitiativesProvider');

/**
 * Helper function to create custom mock return values
 * @param overrides - Partial overrides for the mock context value
 * @returns Complete mock context value with overrides applied
 */
export const createMockInitiativesContext = (
  overrides: Partial<InitiativesContextType> = {}
): InitiativesContextType => ({
  ...mockInitiativesContextValue,
  ...overrides,
});

/**
 * Helper function to create mock initiatives with custom data
 * @param overrides - Array of partial initiative overrides
 * @returns Array of complete mock initiatives
 */
export const createMockInitiatives = (
  overrides: Partial<InitiativeDto>[] = []
): OrderedEntity<InitiativeDto>[] => {
  return overrides.map((override, index) => ({
    ...mockInitiatives[0],
    id: `test-initiative-${index + 1}`,
    identifier: `I-${String(index + 1).padStart(3, '0')}`,
    orderingId: `ordering-${index + 1}`,
    position: String.fromCharCode(97 + index).repeat(2), // aa, bb, cc, etc.
    ...override,
  }));
};
