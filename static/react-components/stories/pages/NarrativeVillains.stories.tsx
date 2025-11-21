// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import Villains from '#pages/Narrative/Villains';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useVillains } from '#hooks/useVillains.mock';
import { VillainDto, VillainType } from '#types';

const meta: Meta<typeof Villains> = {
  title: 'Pages/Narrative/Villains',
  component: Villains,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Villains>;

const mockWorkspace = {
  id: 'workspace-123',
  name: 'Test Workspace',
  description: 'Test',
  icon: 'test.png',
  user_id: 'user-123',
  created_at: '2025-11-15T10:00:00Z',
  updated_at: '2025-11-15T10:00:00Z',
};

const mockVillains: VillainDto[] = [
  {
    id: 'villain-1',
    identifier: 'V-2001',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    name: 'Context Switching',
    villain_type: VillainType.WORKFLOW,
    description:
      'Jumping between IDE, planning tool, and documentation breaks flow state and reduces productivity.',
    severity: 5,
    is_defeated: false,
    created_at: '2025-11-15T10:00:00Z',
    updated_at: '2025-11-15T10:00:00Z',
  },
  {
    id: 'villain-2',
    identifier: 'V-2002',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    name: 'Legacy Monolith',
    villain_type: VillainType.TECHNICAL,
    description: 'Difficult to understand and modify codebase slows development and increases bugs.',
    severity: 4,
    is_defeated: false,
    created_at: '2025-11-15T10:30:00Z',
    updated_at: '2025-11-15T10:30:00Z',
  },
  {
    id: 'villain-3',
    identifier: 'V-2003',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    name: 'Lack of Team Communication',
    villain_type: VillainType.INTERNAL,
    description: 'Misaligned goals and unclear requirements lead to rework.',
    severity: 3,
    is_defeated: false,
    created_at: '2025-11-15T11:00:00Z',
    updated_at: '2025-11-15T11:00:00Z',
  },
  {
    id: 'villain-4',
    identifier: 'V-2004',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    name: 'Competitor Features',
    villain_type: VillainType.EXTERNAL,
    description: 'Competitors are shipping features faster and capturing market share.',
    severity: 4,
    is_defeated: false,
    created_at: '2025-11-15T11:30:00Z',
    updated_at: '2025-11-15T11:30:00Z',
  },
  {
    id: 'villain-5',
    identifier: 'V-2005',
    user_id: 'user-123',
    workspace_id: 'workspace-123',
    name: 'Slow Build Pipeline',
    villain_type: VillainType.TECHNICAL,
    description: 'CI/CD pipeline takes too long, reducing feedback loop.',
    severity: 2,
    is_defeated: true,
    created_at: '2025-11-15T12:00:00Z',
    updated_at: '2025-11-15T12:00:00Z',
  },
];

const manyVillains: VillainDto[] = Array.from({ length: 12 }, (_, i) => ({
  id: `villain-${i}`,
  identifier: `V-${2000 + i}`,
  user_id: 'user-123',
  workspace_id: 'workspace-123',
  name: `Villain ${i + 1}`,
  villain_type: Object.values(VillainType)[i % Object.values(VillainType).length],
  description: `This is a detailed description about villain ${i + 1} and its impact.`,
  severity: ((i % 5) + 1) as 1 | 2 | 3 | 4 | 5,
  is_defeated: i % 3 === 0,
  created_at: '2025-11-15T10:00:00Z',
  updated_at: '2025-11-15T10:00:00Z',
}));

/**
 * Empty state - no villains defined yet
 */
export const Empty: Story = {
  render: () => <Villains />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useVillains.mockReturnValue({
        villains: [],
        isLoading: false,
        error: null,
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
  render: () => <Villains />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useVillains.mockReturnValue({
        villains: [],
        isLoading: true,
        error: null,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * With data - displays villains in grid with various types and severities
 */
export const WithData: Story = {
  render: () => <Villains />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useVillains.mockReturnValue({
        villains: mockVillains,
        isLoading: false,
        error: null,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * With many villains - tests grid layout with many items
 */
export const ManyVillains: Story = {
  render: () => <Villains />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useVillains.mockReturnValue({
        villains: manyVillains,
        isLoading: false,
        error: null,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * Error state - failed to load villains
 */
export const Error: Story = {
  render: () => <Villains />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useVillains.mockReturnValue({
        villains: [],
        isLoading: false,
        error: 'Failed to fetch villains',
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};
