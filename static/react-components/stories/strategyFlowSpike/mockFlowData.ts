/**
 * Mock data for Strategy Flow Canvas Storybook stories.
 * Provides realistic strategic entities with proper connections.
 */

import {
  VisionNodeData,
  PillarNodeData,
  OutcomeNodeData,
  ThemeNodeData,
  InitiativeNodeData,
  StrategyFlowCanvasProps,
} from '../../components/strategyFlowSpike/types';

/**
 * Mock product vision.
 */
const mockVision: VisionNodeData = {
  name: 'OpenBacklog Product Vision',
  description:
    'Empower development teams to seamlessly connect daily work with strategic objectives, enabling faster delivery and better alignment across the organization.',
};

/**
 * Mock strategic pillars.
 */
const mockPillars: PillarNodeData[] = [
  {
    identifier: 'P-001',
    name: 'Developer Velocity',
    description:
      'Maximize developer productivity by reducing friction in daily workflows and enabling faster iteration cycles.',
  },
  {
    identifier: 'P-002',
    name: 'Strategic Clarity',
    description:
      'Provide clear visibility into product strategy and roadmap alignment for all stakeholders.',
  },
  {
    identifier: 'P-003',
    name: 'Developer Experience',
    description:
      'Create a seamless experience where developers can manage tasks, view context, and track progress in one place.',
  }
];

/**
 * Mock product outcomes.
 */
const mockOutcomes: OutcomeNodeData[] = [
  {
    identifier: 'O-001',
    name: 'Reduce Context Switching',
    description:
      'Decrease time spent switching between tools by 50% through integrated workflows.',
    pillar_identifiers: ['P-001'],
  },
  {
    identifier: 'O-002',
    name: 'Improve Planning Efficiency',
    description:
      'Enable teams to complete sprint planning in half the time with better outcome alignment.',
    pillar_identifiers: ['P-002'],
  },
  {
    identifier: 'O-003',
    name: 'Increase Roadmap Visibility',
    description:
      'Give stakeholders real-time visibility into roadmap progress and strategic alignment.',
    pillar_identifiers: ['P-002'],
  },
];

/**
 * Mock roadmap themes.
 */
const mockThemes: ThemeNodeData[] = [
  {
    identifier: 'T-001',
    name: 'Unified Developer Experience',
    description:
      'Create a seamless experience where developers can manage tasks, view context, and track progress in one place.',
    outcome_identifiers: ['O-001'],
  },
  {
    identifier: 'T-002',
    name: 'Strategic Visualization',
    description:
      'Build interactive visualizations that connect daily work to strategic objectives.',
    outcome_identifiers: ['O-002'],
  },
  {
    identifier: 'T-003',
    name: 'Intelligent Automation',
    description:
      'Leverage AI and automation to reduce manual overhead and accelerate developer workflows.',
    outcome_identifiers: ['O-003'],
  },
  {
    identifier: 'T-004',
    name: 'Real-time Collaboration',
    description:
      'Enable seamless team collaboration with live updates and shared context across workstreams.',
    outcome_identifiers: ['O-003'],
  },
];

const mockOnNavigate = () => {
  alert('Navigating to initiative');
};
/**
 * Mock strategic initiatives.
 * Large set to test wide layout scenarios.
 */
const mockInitiatives: InitiativeNodeData[] = [
  {
    identifier: 'I-001',
    title: 'Integrated Code Review',
    description:
      'Embed code review workflows directly into the task management interface.',
    status: 'IN_PROGRESS',
    theme_identifier: 'T-001',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-002',
    title: 'AI Task Decomposition',
    description:
      'Use AI to automatically break down large initiatives into actionable tasks.',
    status: 'TO_DO',
    theme_identifier: 'T-001',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-003',
    title: 'Strategy Canvas View',
    description:
      'Interactive canvas showing strategic pillars, outcomes, themes, and initiatives.',
    status: 'IN_PROGRESS',
    theme_identifier: 'T-002',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-004',
    title: 'MCP Server Integration',
    description:
      'Enable AI coding agents to interact with backlog through Model Context Protocol.',
    status: 'IN_PROGRESS',
    theme_identifier: 'T-001',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-005',
    title: 'Smart Commit Linking',
    description:
      'Automatically link git commits to tasks based on branch naming and commit messages.',
    status: 'TO_DO',
    theme_identifier: 'T-001',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-006',
    title: 'Context-Aware Task Suggestions',
    description:
      'Suggest relevant tasks based on current file and code context.',
    status: 'BACKLOG',
    theme_identifier: 'T-001',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-007',
    title: 'Roadmap Timeline View',
    description:
      'Gantt-style visualization showing initiative timelines and dependencies.',
    status: 'TO_DO',
    theme_identifier: 'T-002',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-008',
    title: 'Progress Dashboard',
    description:
      'Executive dashboard showing strategic progress across all pillars.',
    status: 'BACKLOG',
    theme_identifier: 'T-002',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-009',
    title: 'Dependency Mapping',
    description:
      'Visualize and manage dependencies between initiatives and tasks.',
    status: 'TO_DO',
    theme_identifier: 'T-002',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-010',
    title: 'Auto Sprint Planning',
    description:
      'AI-powered sprint planning that optimizes for velocity and strategic alignment.',
    status: 'IN_PROGRESS',
    theme_identifier: 'T-003',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-011',
    title: 'Smart Task Prioritization',
    description:
      'Automatically prioritize tasks based on strategic impact and dependencies.',
    status: 'TO_DO',
    theme_identifier: 'T-003',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-012',
    title: 'Automated Status Updates',
    description:
      'Generate status updates from git activity and task progress.',
    status: 'BACKLOG',
    theme_identifier: 'T-003',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-013',
    title: 'Predictive Delivery Dates',
    description:
      'Use historical data to predict realistic delivery dates for initiatives.',
    status: 'TO_DO',
    theme_identifier: 'T-003',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-014',
    title: 'Live Cursor Collaboration',
    description:
      'See teammate cursors and selections in real-time on boards and documents.',
    status: 'BACKLOG',
    theme_identifier: 'T-004',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-015',
    title: 'Shared Context Sidebar',
    description:
      'Team sidebar showing who is working on what with live status.',
    status: 'TO_DO',
    theme_identifier: 'T-004',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-016',
    title: 'Async Video Updates',
    description:
      'Record and attach quick video updates to tasks and initiatives.',
    status: 'BACKLOG',
    theme_identifier: 'T-004',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-017',
    title: 'Comment Threading',
    description:
      'Threaded discussions on tasks with mentions and notifications.',
    status: 'IN_PROGRESS',
    theme_identifier: 'T-004',
    onNavigate: mockOnNavigate,
  },
  {
    identifier: 'I-018',
    title: 'IDE Task Panel',
    description:
      'Native task panel embedded in VS Code and JetBrains IDEs.',
    status: 'TO_DO',
    theme_identifier: 'T-001',
    onNavigate: mockOnNavigate,
  },
];

/**
 * Full mock data set with all entity types and connections.
 */
export const fullData: StrategyFlowCanvasProps = {
  vision: mockVision,
  pillars: mockPillars,
  outcomes: mockOutcomes,
  themes: mockThemes,
  initiatives: mockInitiatives,
};

/**
 * Simplified mock data with fewer entities.
 */
export const simpleData: StrategyFlowCanvasProps = {
  vision: mockVision,
  pillars: [mockPillars[0]],
  outcomes: [mockOutcomes[0]],
  themes: [mockThemes[0]],
  initiatives: [mockInitiatives[0]],
};

/**
 * Empty data set for testing empty state.
 */
export const emptyData: StrategyFlowCanvasProps = {
  pillars: [],
  outcomes: [],
  themes: [],
  initiatives: [],
};

/**
 * Data with unconnected initiatives (no theme_identifier).
 */
export const disconnectedData: StrategyFlowCanvasProps = {
  vision: mockVision,
  pillars: mockPillars,
  outcomes: mockOutcomes,
  themes: mockThemes,
  initiatives: [
    ...mockInitiatives,
    {
      identifier: 'I-019',
      title: 'Backlog Initiative',
      description: 'An initiative not yet assigned to a theme.',
      status: 'BACKLOG',
      theme_identifier: null,
      onNavigate: mockOnNavigate,
    },
  ],
};

/**
 * Data set specifically for testing wide layout scenarios.
 * Uses all 18 initiatives distributed across 4 themes.
 * Distribution: T-001 (7), T-002 (4), T-003 (4), T-004 (4)
 */
export const manyInitiativesData: StrategyFlowCanvasProps = {
  vision: mockVision,
  pillars: mockPillars,
  outcomes: mockOutcomes,
  themes: mockThemes,
  initiatives: mockInitiatives,
};
