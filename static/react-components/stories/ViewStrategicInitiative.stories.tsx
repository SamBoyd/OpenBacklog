import { Meta, StoryObj } from '@storybook/react';
import ViewStrategicInitiative from '#components/ViewStrategicInitiative';
import { useStrategicInitiative } from '#hooks/useStrategicInitiative.mock';
import { useParams } from '#hooks/useParams.mock';
import { StrategicInitiativeDto, HeroDto, VillainDto, ConflictDto, ConflictStatus, VillainType, InitiativeDto, TaskStatus, TaskDto } from '#types';
import { useTasksContext } from '#contexts/TasksContext.mock';
import { mockUseTasksContext, mockWorkspace } from '#stories/example_data';
import { LexoRank } from 'lexorank';
import { OrderedEntity } from '#hooks/useOrderings';

const meta: Meta<typeof ViewStrategicInitiative> = {
  title: 'Pages/StrategyAndRoadmap/ViewStrategicInitiative',
  component: ViewStrategicInitiative,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

// Mock data
const mockHero: HeroDto = {
  id: '1',
  identifier: 'HERO-001',
  workspace_id: 'ws-1',
  name: 'Product Manager',
  description: 'The visionary leader driving product strategy',
  is_primary: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockVillain: VillainDto = {
  id: '1',
  identifier: 'VILLAIN-001',
  user_id: 'user-1',
  workspace_id: 'ws-1',
  name: 'Technical Debt',
  villain_type: VillainType.TECHNICAL,
  description: 'Accumulated technical debt blocking feature development',
  severity: 4,
  is_defeated: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockConflict: ConflictDto = {
  id: '1',
  identifier: 'CONFLICT-001',
  workspace_id: 'ws-1',
  hero_id: mockHero.id,
  villain_id: mockVillain.id,
  description: 'Product Manager needs to refactor code to enable faster feature delivery',
  status: ConflictStatus.OPEN,
  story_arc_id: 'arc-1',
  resolved_at: null,
  resolved_by_initiative_id: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  hero: mockHero,
  villain: mockVillain,
};

const mockTheme: any = {
  id: 'theme-1',
  workspace_id: 'ws-1',
  name: 'Platform Excellence',
  description: 'Building a robust, scalable foundation for product success',
  outcome_ids: [],
  hero_ids: [mockHero.id],
  villain_ids: [mockVillain.id],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  heroes: [mockHero],
  villains: [mockVillain],
};

const mockPillar: any = {
  id: 'pillar-1',
  workspace_id: 'ws-1',
  name: 'Stability',
  description: 'Core infrastructure and reliability',
  display_order: 1,
  outcome_ids: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockInitiative: InitiativeDto = {
  id: 'init-1',
  identifier: 'BEAT-001',
  user_id: 'user-1',
  workspace: mockWorkspace,
  title: 'Refactor Payment System',
  description: 'Complete rewrite of payment processing',
  type: 'FEATURE',
  status: 'IN_PROGRESS',
  properties: {},
  tasks: [
    {
      id: 'task-1',
      identifier: 'TASK-001',
      user_id: 'user-1',
      workspace: mockWorkspace,
      initiative_id: 'init-1',
      title: 'Design new payment flow',
      description: 'Create UX mockups',
      status: TaskStatus.DONE,
      type: 'FEATURE',
      properties: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      checklist: [],
    },
    {
      id: 'task-2',
      identifier: 'TASK-002',
      user_id: 'user-1',
      workspace: mockWorkspace,
      initiative_id: 'init-1',
      title: 'Implement payment gateway integration',
      description: 'Connect to Stripe API',
      status: TaskStatus.IN_PROGRESS,
      type: 'FEATURE',
      properties: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      checklist: [],
    },
    {
      id: 'task-3',
      identifier: 'TASK-003',
      user_id: 'user-1',
      workspace: mockWorkspace,
      initiative_id: 'init-1',
      title: 'Add error handling and validation',
      description: 'Handle edge cases',
      status: TaskStatus.TO_DO,
      type: 'FEATURE',
      properties: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      checklist: [],
    },
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  has_pending_job: null
};

const mockStrategicInitiative: StrategicInitiativeDto = {
  id: 'strat-init-1',
  initiative_id: 'init-1',
  workspace_id: 'ws-1',
  pillar_id: 'pillar-1',
  theme_id: 'theme-1',
  description: 'This beat represents the critical refactoring work needed to unblock feature velocity',
  narrative_intent: 'We must defeat technical debt to empower our product team',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  initiative: mockInitiative,
  pillar: mockPillar,
  theme: mockTheme,
  heroes: [mockHero],
  villains: [mockVillain],
  conflicts: [mockConflict],
};

let rank = LexoRank.middle()
const mockTasks = mockInitiative.tasks.map((task) => {
  rank = rank.genNext()

  return {
    ...task,
    position: rank.genNext().toString(),
    orderingId: task.id
  }
})

/**
 * Default story showing a fully populated strategic initiative
 */
export const Default: Story = {
  render: () => {
    useParams.mockReturnValue({
      initiativeId: 'init-1',
    });

    useTasksContext.mockReturnValue({
      ...mockUseTasksContext,
      tasks: mockTasks as OrderedEntity<TaskDto>[]
    });

    useStrategicInitiative.mockReturnValue({
      strategicInitiative: mockStrategicInitiative,
      isLoading: false,
      error: null,
      createStrategicInitiative: () => { },
      isCreating: false,
      createError: null,
      updateStrategicInitiative: () => { },
      isUpdating: false,
      updateError: null,
    });

    return <ViewStrategicInitiative />;
  },
};

/**
 * Loading state
 */
export const Loading: Story = {
  render: () => {
    useParams.mockReturnValue({
      initiativeId: 'init-1',
    } as any);

    useStrategicInitiative.mockReturnValue({
      strategicInitiative: null,
      isLoading: true,
      error: null,
      createStrategicInitiative: () => { },
      isCreating: false,
      createError: null,
      updateStrategicInitiative: () => { },
      isUpdating: false,
      updateError: null,
    });

    return <ViewStrategicInitiative />;
  },
};

/**
 * Error state
 */
export const Error: Story = {
  render: () => {
    useParams.mockReturnValue({
      initiativeId: 'init-1',
    } as any);

    useStrategicInitiative.mockReturnValue({
      strategicInitiative: null,
      isLoading: false,
      error: { message: 'Failed to fetch strategic initiative' } as any,
      createStrategicInitiative: () => { },
      isCreating: false,
      createError: null,
      updateStrategicInitiative: () => { },
      isUpdating: false,
      updateError: null,
    });

    return <ViewStrategicInitiative />;
  },
};

/**
 * Minimal data - no narrative context
 */
export const MinimalContext: Story = {
  render: () => {
    const minimalStrategicInitiative: StrategicInitiativeDto = {
      ...mockStrategicInitiative,
      description: null,
      narrative_intent: null,
      heroes: [],
      villains: [],
      conflicts: [],
      pillar: undefined,
    };

    useParams.mockReturnValue({
      initiativeId: 'init-1',
    } as any);

    useStrategicInitiative.mockReturnValue({
      strategicInitiative: minimalStrategicInitiative,
      isLoading: false,
      error: null,
      createStrategicInitiative: () => { },
      isCreating: false,
      createError: null,
      updateStrategicInitiative: () => { },
      isUpdating: false,
      updateError: null,
    } as any);

    return <ViewStrategicInitiative />;
  },
};

/**
 * Multiple heroes and villains
 */
export const MultipleNarrativeElements: Story = {
  render: () => {
    const hero2: HeroDto = {
      ...mockHero,
      id: '2',
      identifier: 'HERO-002',
      name: 'Engineering Lead',
      is_primary: false,
    };

    const villain2: VillainDto = {
      ...mockVillain,
      id: '2',
      identifier: 'VILLAIN-002',
      name: 'Performance Issues',
      villain_type: VillainType.TECHNICAL,
      severity: 3,
    };

    const enrichedInitiative: StrategicInitiativeDto = {
      ...mockStrategicInitiative,
      heroes: [mockHero, hero2],
      villains: [mockVillain, villain2],
    };

    useParams.mockReturnValue({
      initiativeId: 'init-1',
    } as any);

    useStrategicInitiative.mockReturnValue({
      strategicInitiative: enrichedInitiative,
      isLoading: false,
      error: null,
      createStrategicInitiative: () => { },
      isCreating: false,
      createError: null,
      updateStrategicInitiative: () => { },
      isUpdating: false,
      updateError: null,
    });

    return <ViewStrategicInitiative />;
  },
};

/**
 * No tasks defined
 */
export const NoTasks: Story = {
  render: () => {
    const noTasksInitiative: StrategicInitiativeDto = {
      ...mockStrategicInitiative,
      initiative: { ...mockInitiative, tasks: [] },
    };

    useParams.mockReturnValue({
      initiativeId: 'init-1',
    });

    useStrategicInitiative.mockReturnValue({
      strategicInitiative: noTasksInitiative,
      isLoading: false,
      error: null,
      createStrategicInitiative: () => { },
      isCreating: false,
      createError: null,
      updateStrategicInitiative: () => { },
      isUpdating: false,
      updateError: null,
    });

    return <ViewStrategicInitiative />;
  },
};
