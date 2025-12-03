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
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Mock data - Updated to match Figma design examples
const mockHero: HeroDto = {
  id: '1',
  identifier: 'HERO-001',
  workspace_id: 'ws-1',
  name: 'Sarah, The Solo Builder',
  description: 'Never leave your IDE to give AI the context it needs',
  is_primary: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockVillain: VillainDto = {
  id: '1',
  identifier: 'VILLAIN-001',
  user_id: 'user-1',
  workspace_id: 'ws-1',
  name: 'Context Switching',
  villain_type: VillainType.WORKFLOW,
  description: 'Constant jumping between IDE and planning tools',
  severity: 4,
  is_defeated: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockVillain2: VillainDto = {
  id: '2',
  identifier: 'VILLAIN-002',
  user_id: 'user-1',
  workspace_id: 'ws-1',
  name: 'AI Ignorance',
  villain_type: VillainType.TECHNICAL,
  description: 'AI agents lack product context and strategic intent',
  severity: 5,
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
  description: 'Sarah wastes time context switching between tools, and AI can\'t help because it lacks product context.',
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
  name: 'AI-First Product Management',
  description: 'Enabling AI agents to understand and contribute to product development',
  status: 'In Progress - Act 2 (60%)',
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
  name: 'Developer-First Simplicity',
  description: 'Eliminate complexity found in enterprise tools. Focus on intuitive, developer-centered workflows that keep users in flow state.',
  display_order: 1,
  outcome_ids: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockInitiative: InitiativeDto = {
  id: 'init-1',
  identifier: 'I-0039',
  user_id: 'user-1',
  workspace: mockWorkspace,
  title: 'Enable ClaudeCode to read product context via MCP',
  description: 'This initiative implements the technical foundation for AI agents to access product context directly from OpenBacklog. By creating an MCP (Model Context Protocol) server, we enable tools like ClaudeCode to query initiatives, tasks, and strategic context without requiring manual copy-paste or context switching. This is the first step toward true AI-assisted product development.',
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
      title: 'Add /get_project_vision MCP command',
      description: 'Implement the MCP command to retrieve project vision',
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
      title: 'Add /get_initiatives MCP command',
      description: 'Implement the MCP command to list all initiatives',
      status: TaskStatus.DONE,
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
      title: 'Add /get_task_details MCP command',
      description: 'Implement the MCP command to get task details',
      status: TaskStatus.IN_PROGRESS,
      type: 'FEATURE',
      properties: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      checklist: [],
    },
    {
      id: 'task-4',
      identifier: 'TASK-004',
      user_id: 'user-1',
      workspace: mockWorkspace,
      initiative_id: 'init-1',
      title: 'Add /get_lore MCP command',
      description: 'Implement the MCP command to retrieve lore entries',
      status: TaskStatus.TO_DO,
      type: 'FEATURE',
      properties: {},
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      checklist: [],
    },
    {
      id: 'task-5',
      identifier: 'TASK-005',
      user_id: 'user-1',
      workspace: mockWorkspace,
      initiative_id: 'init-1',
      title: 'Implement MCP authentication layer',
      description: 'Add authentication for secure MCP access',
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
  description: 'Sarah is constantly breaking flow state to switch between her IDE and separate task management tools. The AI agent doesn\'t have access to the product context it needs—what to build, why, or how it fits into the broader roadmap—forcing her to manually relay this information repeatedly. By enabling ClaudeCode to read product context directly from OpenBacklog via MCP, we eliminate this context switching and empower the AI to propose better, more aligned suggestions.',
  narrative_intent: 'This beat is the first step in the "AI-First Product Management" arc, establishing the read-only foundation before we enable write capabilities.',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  initiative: mockInitiative,
  pillar: mockPillar,
  theme: mockTheme,
  heroes: [mockHero],
  villains: [mockVillain, mockVillain2],
  conflicts: [mockConflict],
};

let rank = LexoRank.middle();
const mockTasks = mockInitiative.tasks.map((task) => {
  rank = rank.genNext();

  return {
    ...task,
    position: rank.genNext().toString(),
    orderingId: task.id
  };
});

/**
 * Default story showing a fully populated strategic initiative
 * Demonstrates the new layout with initiative title as primary heading,
 * "What This Initiative Does" section, and restructured narrative connections sidebar.
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
 * Shows how the page looks when only the initiative data exists without
 * strategic context, heroes, villains, or conflicts.
 */
export const MinimalContext: Story = {
  render: () => {
    const minimalInitiative: InitiativeDto = {
      ...mockInitiative,
      title: 'Simple Bug Fix',
      description: 'Fix the login button alignment issue on mobile devices.',
    };

    const minimalStrategicInitiative: StrategicInitiativeDto = {
      ...mockStrategicInitiative,
      initiative: minimalInitiative,
      description: null,
      narrative_intent: null,
      heroes: [],
      villains: [],
      conflicts: [],
      pillar: undefined,
      theme: undefined,
    };

    useParams.mockReturnValue({
      initiativeId: 'init-1',
    } as any);

    useTasksContext.mockReturnValue({
      ...mockUseTasksContext,
      tasks: mockTasks as OrderedEntity<TaskDto>[]
    });

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
 * Demonstrates the sidebar display when there are multiple narrative elements.
 * Shows the Hero card (blue styling) and multiple Villain cards (amber styling).
 */
export const MultipleNarrativeElements: Story = {
  render: () => {
    const hero2: HeroDto = {
      ...mockHero,
      id: '2',
      identifier: 'HERO-002',
      name: 'Engineering Lead',
      description: 'Ensure code quality and architectural consistency',
      is_primary: false,
    };

    const enrichedInitiative: StrategicInitiativeDto = {
      ...mockStrategicInitiative,
      heroes: [mockHero, hero2],
      villains: [mockVillain, mockVillain2],
    };

    useParams.mockReturnValue({
      initiativeId: 'init-1',
    } as any);

    useTasksContext.mockReturnValue({
      ...mockUseTasksContext,
      tasks: mockTasks as OrderedEntity<TaskDto>[]
    });

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
 * Shows the empty state for the Scenes section with the "Add Scene" and "Decompose" buttons.
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

    useTasksContext.mockReturnValue({
      ...mockUseTasksContext,
      tasks: []
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

/**
 * Completed Initiative
 * Shows how the page looks when all tasks are complete and the initiative is done.
 */
export const CompletedInitiative: Story = {
  render: () => {
    const completedTasks = mockInitiative.tasks.map(task => ({
      ...task,
      status: TaskStatus.DONE,
    }));

    const completedInitiative: InitiativeDto = {
      ...mockInitiative,
      status: 'DONE',
      tasks: completedTasks,
    };

    const completedStrategicInitiative: StrategicInitiativeDto = {
      ...mockStrategicInitiative,
      initiative: completedInitiative,
    };

    let completedRank = LexoRank.middle();
    const completedMockTasks = completedTasks.map((task) => {
      completedRank = completedRank.genNext();
      return {
        ...task,
        position: completedRank.genNext().toString(),
        orderingId: task.id
      };
    });

    useParams.mockReturnValue({
      initiativeId: 'init-1',
    });

    useTasksContext.mockReturnValue({
      ...mockUseTasksContext,
      tasks: completedMockTasks as OrderedEntity<TaskDto>[]
    });

    useStrategicInitiative.mockReturnValue({
      strategicInitiative: completedStrategicInitiative,
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
