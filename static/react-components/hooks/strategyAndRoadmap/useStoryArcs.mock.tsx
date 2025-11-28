// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import { ArcDto } from '#api/productStrategy';
import * as actual from './useStoryArcs';

export const useStoryArcs = fn(actual.useStoryArcs).mockName('useStoryArcs');

/**
 * Mock data for prioritized story arcs (active roadmap themes).
 */
export const mockPrioritizedArcs: ArcDto[] = [
  {
    id: 'arc-1',
    workspace_id: 'workspace-1',
    name: 'AI-First Product Management',
    description: 'Helping Sarah achieve flow by eliminating context switching with intelligent task automation',
    outcome_ids: ['outcome-1'],
    hero_ids: ['hero-1'],
    villain_ids: ['villain-1', 'villain-2'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
    heroes: [
      {
        id: 'hero-1',
        name: 'Sarah, The Solo Builder',
        identifier: 'H-001',
        description: 'A solo developer juggling multiple projects who needs to stay in flow',
        is_primary: true,
      },
    ],
    villains: [
      {
        id: 'villain-1',
        name: 'Context Switching',
        identifier: 'V-001',
        description: 'Constant interruptions breaking flow state and reducing productivity',
        villain_type: 'WORKFLOW',
        severity: 4,
        is_defeated: false,
      },
      {
        id: 'villain-2',
        name: 'AI Tool Ignorance',
        identifier: 'V-002',
        description: 'Lack of knowledge about effective AI tool usage',
        villain_type: 'INTERNAL',
        severity: 3,
        is_defeated: false,
      },
    ],
  },
  {
    id: 'arc-2',
    workspace_id: 'workspace-1',
    name: 'Performance Optimization',
    description: 'Improving application speed and responsiveness for power users who work with large datasets',
    outcome_ids: ['outcome-2'],
    hero_ids: ['hero-2'],
    villain_ids: ['villain-3'],
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-02-20T00:00:00Z',
    heroes: [
      {
        id: 'hero-2',
        name: 'Alex, The Power User',
        identifier: 'H-002',
        description: 'An advanced user managing large-scale projects with complex dependencies',
        is_primary: false,
      },
    ],
    villains: [
      {
        id: 'villain-3',
        name: 'Slow Response Times',
        identifier: 'V-003',
        description: 'Application performance issues causing frustration and delays',
        villain_type: 'TECHNICAL',
        severity: 5,
        is_defeated: true,
      },
    ],
  },
  {
    id: 'arc-3',
    workspace_id: 'workspace-1',
    name: 'Onboarding Experience Redesign',
    description: 'Helping new users succeed in their first week by providing clear guidance and quick wins',
    outcome_ids: ['outcome-3'],
    hero_ids: ['hero-3'],
    villain_ids: ['villain-4'],
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-02-15T00:00:00Z',
    heroes: [
      {
        id: 'hero-3',
        name: 'Jordan, The New User',
        identifier: 'H-003',
        description: 'A first-time user exploring the product for their startup',
        is_primary: false,
      },
    ],
    villains: [
      {
        id: 'villain-4',
        name: 'Unclear First Steps',
        identifier: 'V-004',
        description: 'Confusing onboarding flow leading to early abandonment',
        villain_type: 'WORKFLOW',
        severity: 3,
        is_defeated: false,
      },
    ],
  },
];

/**
 * Mock data for unprioritized story arcs (backlog themes).
 */
export const mockUnprioritizedArcs: ArcDto[] = [
  {
    id: 'arc-4',
    workspace_id: 'workspace-1',
    name: 'Mobile App Launch',
    description: 'Native mobile applications for iOS and Android to enable on-the-go productivity',
    outcome_ids: ['outcome-4'],
    hero_ids: ['hero-2'],
    villain_ids: ['villain-5', 'villain-6'],
    created_at: '2024-03-01T00:00:00Z',
    updated_at: '2024-03-01T00:00:00Z',
    heroes: [
      {
        id: 'hero-2',
        name: 'Alex, The Power User',
        identifier: 'H-002',
        description: 'An advanced user managing large-scale projects',
        is_primary: false,
      },
    ],
    villains: [
      {
        id: 'villain-5',
        name: 'Limited Mobile Access',
        identifier: 'V-005',
        description: 'Inability to access critical features on mobile devices',
        villain_type: 'TECHNICAL',
        severity: 4,
        is_defeated: false,
      },
      {
        id: 'villain-6',
        name: 'Platform Constraints',
        identifier: 'V-006',
        description: 'Mobile platform limitations and API restrictions',
        villain_type: 'EXTERNAL',
        severity: 3,
        is_defeated: false,
      },
    ],
  },
  {
    id: 'arc-5',
    workspace_id: 'workspace-1',
    name: 'Advanced Analytics Dashboard',
    description: 'Comprehensive analytics and insights for data-driven product decisions',
    outcome_ids: ['outcome-5'],
    hero_ids: [],
    villain_ids: [],
    created_at: '2024-03-15T00:00:00Z',
    updated_at: '2024-03-15T00:00:00Z',
    heroes: [],
    villains: [],
  },
  {
    id: 'arc-6',
    workspace_id: 'workspace-1',
    name: 'Collaboration Features',
    description: 'Real-time collaboration tools for distributed teams working asynchronously',
    outcome_ids: [],
    hero_ids: [],
    villain_ids: [],
    created_at: '2024-03-20T00:00:00Z',
    updated_at: '2024-03-20T00:00:00Z',
    heroes: [],
    villains: [],
  },
];

/**
 * Legacy export for backward compatibility.
 * @deprecated Use mockPrioritizedArcs and mockUnprioritizedArcs instead.
 */
export const mockStoryArcs: ArcDto[] = [
  ...mockPrioritizedArcs,
  ...mockUnprioritizedArcs,
];
