// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useHeroes';
import { HeroDto } from '#types';

export const useHeroes = fn(actual.useHeroes).mockName('useHeroes');

/**
 * Mock heroes data for Storybook stories.
 */
export const mockHeroes: HeroDto[] = [
  {
    id: 'hero-1',
    identifier: 'H-001',
    workspace_id: 'workspace-1',
    name: 'Sarah, The Solo Builder',
    description: 'A solo developer juggling multiple projects who needs to stay in flow',
    is_primary: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'hero-2',
    identifier: 'H-002',
    workspace_id: 'workspace-1',
    name: 'Alex, The Power User',
    description: 'An advanced user managing large-scale projects with complex dependencies',
    is_primary: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'hero-3',
    identifier: 'H-003',
    workspace_id: 'workspace-1',
    name: 'Jordan, The New User',
    description: 'A first-time user exploring the product for their startup',
    is_primary: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

/**
 * Default mock return value for useHeroes hook.
 */
export const mockHeroesReturn = {
  heroes: mockHeroes,
  isLoading: false,
  error: null,
  refetch: fn(),
};
