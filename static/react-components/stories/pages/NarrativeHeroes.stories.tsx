// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import Heroes from '#pages/Narrative/Heroes';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useHeroes } from '#hooks/useHeroes.mock';
import { HeroDto } from '#types';

const meta: Meta<typeof Heroes> = {
  title: 'Pages/Narrative/Heroes',
  component: Heroes,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Heroes>;

const mockWorkspace = {
  id: 'workspace-123',
  name: 'Test Workspace',
  description: 'Test',
  icon: 'test.png',
  user_id: 'user-123',
  created_at: '2025-11-15T10:00:00Z',
  updated_at: '2025-11-15T10:00:00Z',
};

const mockHeroes: HeroDto[] = [
  {
    id: 'hero-1',
    identifier: 'H-2001',
    workspace_id: 'workspace-123',
    name: 'Sarah, The Solo Builder',
    description:
      'Sarah is a solo developer building a SaaS product. She is driven by wanting to ship quality products without needing a team.',
    is_primary: true,
    created_at: '2025-11-15T10:00:00Z',
    updated_at: '2025-11-15T10:00:00Z',
  },
  {
    id: 'hero-2',
    identifier: 'H-2002',
    workspace_id: 'workspace-123',
    name: 'Marcus, The Enterprise Lead',
    description:
      'Marcus leads a team at a Fortune 500 company and needs to balance speed with governance.',
    is_primary: false,
    created_at: '2025-11-15T10:30:00Z',
    updated_at: '2025-11-15T10:30:00Z',
  },
  {
    id: 'hero-3',
    identifier: 'H-2003',
    workspace_id: 'workspace-123',
    name: 'Elena, The Startup Founder',
    description: null,
    is_primary: false,
    created_at: '2025-11-15T11:00:00Z',
    updated_at: '2025-11-15T11:00:00Z',
  },
];

const manyHeroes: HeroDto[] = Array.from({ length: 12 }, (_, i) => ({
  id: `hero-${i}`,
  identifier: `H-${2000 + i}`,
  workspace_id: 'workspace-123',
  name: `Hero ${i + 1}`,
  description:
    i % 2 === 0
      ? 'This is a detailed description about this hero and what drives them.'
      : null,
  is_primary: i === 0,
  created_at: '2025-11-15T10:00:00Z',
  updated_at: '2025-11-15T10:00:00Z',
}));

/**
 * Empty state - no heroes defined yet
 */
export const Empty: Story = {
  render: () => <Heroes />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useHeroes.mockReturnValue({
        heroes: [],
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
  render: () => <Heroes />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useHeroes.mockReturnValue({
        heroes: [],
        isLoading: true,
        error: null,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * With data - displays heroes in grid
 */
export const WithData: Story = {
  render: () => <Heroes />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useHeroes.mockReturnValue({
        heroes: mockHeroes,
        isLoading: false,
        error: null,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * With many heroes - tests grid layout with many items
 */
export const ManyHeroes: Story = {
  render: () => <Heroes />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useHeroes.mockReturnValue({
        heroes: manyHeroes,
        isLoading: false,
        error: null,
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};

/**
 * Error state - failed to load heroes
 */
export const Error: Story = {
  render: () => <Heroes />,
  decorators: [
    (Story) => {
      useWorkspaces.mockReturnValue({
        currentWorkspace: mockWorkspace,
        workspaces: [mockWorkspace],
        isLoading: false,
        error: null,
      });
      useHeroes.mockReturnValue({
        heroes: [],
        isLoading: false,
        error: 'Failed to fetch heroes',
        refetch: () => {},
      });
      return <Story />;
    },
  ],
};
