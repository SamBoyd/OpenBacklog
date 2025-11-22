// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import { ArcDto } from '#api/productStrategy';
import * as actual from './useStoryArcs';

export const useStoryArcs = fn(actual.useStoryArcs).mockName('useStoryArcs');

/**
 * Mock data for story arcs in the roadmap overview.
 */
export const mockStoryArcs: ArcDto[] = [
  {
    id: 'arc-1',
    workspace_id: 'workspace-1',
    name: 'AI-First Product Management',
    description: 'Helping Sarah achieve flow by fighting Context Switching',
    outcome_ids: ['outcome-1'],
    hero_ids: ['hero-1'],
    villain_ids: ['villain-1', 'villain-2'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    heroes: [{ id: 'hero-1', name: 'Sarah, The Solo Builder' }],
    villains: [
      { id: 'villain-1', name: 'Context Switching' },
      { id: 'villain-2', name: 'AI Ignorance' },
    ],
    status: 'in_progress',
    progress_percentage: 60,
    scenes_completed: 12,
    scenes_total: 28,
    started_quarter: 'Q1 2024',
    expected_quarter: 'Q2 2024',
  },
  {
    id: 'arc-2',
    workspace_id: 'workspace-1',
    name: 'Performance Optimization',
    description: 'Improving speed for power users by fighting Slowness',
    outcome_ids: ['outcome-2'],
    hero_ids: ['hero-2'],
    villain_ids: ['villain-3'],
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-01-05T00:00:00Z',
    heroes: [{ id: 'hero-2', name: 'Power User' }],
    villains: [{ id: 'villain-3', name: 'Slow Response Times' }],
    status: 'complete',
    progress_percentage: 100,
    scenes_completed: 18,
    scenes_total: 18,
    started_quarter: 'Q1 2024',
    expected_quarter: 'Q2 2024',
  },
  {
    id: 'arc-3',
    workspace_id: 'workspace-1',
    name: 'Onboarding Experience Redesign',
    description: 'Helping new users succeed by fighting Confusion',
    outcome_ids: ['outcome-3'],
    hero_ids: ['hero-3'],
    villain_ids: ['villain-4'],
    created_at: '2024-04-01T00:00:00Z',
    updated_at: '2024-04-01T00:00:00Z',
    heroes: [{ id: 'hero-3', name: 'New User' }],
    villains: [{ id: 'villain-4', name: 'Unclear First Steps' }],
    status: 'planned',
    progress_percentage: 0,
    scenes_completed: 0,
    scenes_total: 20,
    started_quarter: 'Q2 2024',
    expected_quarter: 'Q3 2024',
  },
  {
    id: 'arc-4',
    workspace_id: 'workspace-1',
    name: 'Mobile App Launch',
    description: 'Helping power users stay productive on-the-go by fighting Limited Access',
    outcome_ids: ['outcome-4'],
    hero_ids: ['hero-2'],
    villain_ids: ['villain-5', 'villain-6'],
    created_at: '2024-10-01T00:00:00Z',
    updated_at: '2024-10-01T00:00:00Z',
    heroes: [{ id: 'hero-2', name: 'Power User' }],
    villains: [
      { id: 'villain-5', name: 'Limited Access' },
      { id: 'villain-6', name: 'Platform Constraints' },
    ],
    status: 'planned',
    progress_percentage: 0,
    scenes_completed: 0,
    scenes_total: 24,
    started_quarter: 'Q4 2024',
    expected_quarter: 'Q1 2025',
  },
];


