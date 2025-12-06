// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useVillains';
import { VillainDto, VillainType } from '#types';

export const useVillains = fn(actual.useVillains).mockName('useVillains');

/**
 * Mock villains data for Storybook stories.
 */
export const mockVillains: VillainDto[] = [
  {
    id: 'villain-1',
    identifier: 'V-001',
    user_id: 'user-1',
    workspace_id: 'workspace-1',
    name: 'Context Switching',
    description: 'Constant interruptions breaking flow state and reducing productivity',
    villain_type: VillainType.WORKFLOW,
    severity: 4,
    is_defeated: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'villain-2',
    identifier: 'V-002',
    user_id: 'user-1',
    workspace_id: 'workspace-1',
    name: 'AI Tool Ignorance',
    description: 'Lack of knowledge about effective AI tool usage',
    villain_type: VillainType.INTERNAL,
    severity: 3,
    is_defeated: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'villain-3',
    identifier: 'V-003',
    user_id: 'user-1',
    workspace_id: 'workspace-1',
    name: 'Slow Response Times',
    description: 'Application performance issues causing frustration and delays',
    villain_type: VillainType.TECHNICAL,
    severity: 5,
    is_defeated: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'villain-4',
    identifier: 'V-004',
    user_id: 'user-1',
    workspace_id: 'workspace-1',
    name: 'Unclear First Steps',
    description: 'Confusing onboarding flow leading to early abandonment',
    villain_type: VillainType.WORKFLOW,
    severity: 3,
    is_defeated: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'villain-5',
    identifier: 'V-005',
    user_id: 'user-1',
    workspace_id: 'workspace-1',
    name: 'Limited Mobile Access',
    description: 'Inability to access critical features on mobile devices',
    villain_type: VillainType.TECHNICAL,
    severity: 4,
    is_defeated: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'villain-6',
    identifier: 'V-006',
    user_id: 'user-1',
    workspace_id: 'workspace-1',
    name: 'Platform Constraints',
    description: 'Mobile platform limitations and API restrictions',
    villain_type: VillainType.EXTERNAL,
    severity: 3,
    is_defeated: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

/**
 * Default mock return value for useVillains hook.
 */
export const mockVillainsReturn = {
  villains: mockVillains,
  isLoading: false,
  error: null,
  refetch: fn(),
};
