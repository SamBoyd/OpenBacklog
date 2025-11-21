// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import Conflicts from '#pages/Narrative/Conflicts';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useConflicts } from '#hooks/useConflicts.mock';
import { ConflictDto, ConflictStatus } from '#types';

const meta: Meta<typeof Conflicts> = {
  title: 'Pages/Narrative/Conflicts',
  component: Conflicts,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Conflicts>;

const mockWorkspace = {
  id: 'workspace-123',
  name: 'Test Workspace',
  description: 'Test',
  icon: 'test.png',
  user_id: 'user-123',
  created_at: '2025-11-15T10:00:00Z',
  updated_at: '2025-11-15T10:00:00Z',
};

const mockConflicts: ConflictDto[] = [
  {
    id: 'conflict-1',
    identifier: 'C-2001',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    hero_id: 'hero-1',
    villain_id: 'villain-1',
    description:
      'Sarah cannot access product context from IDE. This forces her to switch between tools constantly.',
    status: ConflictStatus.OPEN,
    story_arc_id: null,
    resolved_at: null,
    resolved_by_initiative_id: null,
    created_at: '2025-11-15T10:00:00Z',
    updated_at: '2025-11-15T10:00:00Z',
  },
  {
    id: 'conflict-2',
    identifier: 'C-2002',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    hero_id: 'hero-1',
    villain_id: 'villain-2',
    description:
      'Legacy monolith makes it hard to add new features without breaking existing functionality.',
    status: ConflictStatus.ESCALATING,
    story_arc_id: null,
    resolved_at: null,
    resolved_by_initiative_id: null,
    created_at: '2025-11-15T10:30:00Z',
    updated_at: '2025-11-15T10:30:00Z',
  },
  {
    id: 'conflict-3',
    identifier: 'C-2003',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    hero_id: 'hero-2',
    villain_id: 'villain-3',
    description: 'Team needs better alignment on priorities and requirements.',
    status: ConflictStatus.RESOLVING,
    story_arc_id: 'arc-1',
    resolved_at: null,
    resolved_by_initiative_id: null,
    created_at: '2025-11-15T11:00:00Z',
    updated_at: '2025-11-15T11:00:00Z',
  },
  {
    id: 'conflict-4',
    identifier: 'C-2004',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    hero_id: 'hero-1',
    villain_id: 'villain-4',
    description: 'Need to ship competitive features to retain market share.',
    status: ConflictStatus.RESOLVED,
    story_arc_id: null,
    resolved_at: '2025-11-10T15:00:00Z',
    resolved_by_initiative_id: 'initiative-1',
    created_at: '2025-11-15T11:30:00Z',
    updated_at: '2025-11-15T11:30:00Z',
  },
];

const manyConflicts: ConflictDto[] = Array.from({ length: 12 }, (_, i) => ({
  id: `conflict-${i}`,
  identifier: `C-${2000 + i}`,
  user_id: 'user-123',
  workspace_id: 'workspace-123',
  hero_id: `hero-${i % 3}`,
  villain_id: `villain-${i % 4}`,
  description: `Conflict ${i + 1}: This is a detailed description about the conflict.`,
  status: Object.values(ConflictStatus)[i % Object.values(ConflictStatus).length],
  story_arc_id: i % 2 === 0 ? 'arc-1' : null,
  resolved_at: i % 3 === 0 ? '2025-11-10T15:00:00Z' : null,
  resolved_by_initiative_id: i % 3 === 0 ? 'initiative-1' : null,
  created_at: '2025-11-15T10:00:00Z',
  updated_at: '2025-11-15T10:00:00Z',
}));

/**
 * Empty state - no conflicts created yet
 */
export const Empty: Story = {
  render: () => <Conflicts />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useConflicts.mockReturnValue({
        conflicts: [],
        isLoading: false,
        error: null,
        isFetching: false,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * Loading state - data is being fetched
 */
export const Loading: Story = {
  render: () => <Conflicts />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useConflicts.mockReturnValue({
        conflicts: null,
        isLoading: true,
        error: null,
        isFetching: true,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * With data - displays conflicts in list with various statuses
 */
export const WithData: Story = {
  render: () => <Conflicts />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useConflicts.mockReturnValue({
        conflicts: mockConflicts,
        isLoading: false,
        error: null,
        isFetching: false,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * With many conflicts - tests layout with many items
 */
export const ManyConflicts: Story = {
  render: () => <Conflicts />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useConflicts.mockReturnValue({
        conflicts: manyConflicts,
        isLoading: false,
        error: null,
        isFetching: false,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * Grouped by status - shows conflicts organized by their status
 */
export const GroupedByStatus: Story = {
  render: () => <Conflicts />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useConflicts.mockReturnValue({
        conflicts: mockConflicts,
        isLoading: false,
        error: null,
        isFetching: false,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
  play: async ({ canvasElement }) => {
    // Simulate clicking the group by status button
    const button = canvasElement.querySelector('[data-testid="group-by-status-toggle"]');
    if (button) {
      button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }
  },
};

/**
 * Error state - failed to load conflicts
 */
export const Error: Story = {
  render: () => <Conflicts />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useConflicts.mockReturnValue({
        conflicts: null,
        isLoading: false,
        error: 'Failed to fetch conflicts',
        isFetching: false,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};
