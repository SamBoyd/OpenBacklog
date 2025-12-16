/**
 * Mock data for Story Arc Detail Page Storybook stories.
 * Provides realistic test data covering various states and edge cases.
 */

import { LoremIpsum } from "lorem-ipsum";

import { MetricsData, OutcomeRef } from '#types/storyArc';
import { ThemeDto, HeroRef, VillainRef, PillarDto } from '#api/productStrategy';
import { OutcomeDto } from '#api/productOutcomes';
import { ConflictDto, VillainType, ConflictStatus, HeroDto, VillainDto } from '#types';
import { BeatItem } from '#hooks/initiatives/useInitiativesByTheme';

const lorem = new LoremIpsum({
  sentencesPerParagraph: {
    max: 8,
    min: 4
  },
  wordsPerSentence: {
    max: 16,
    min: 4
  }
});

// Mock Vision Text
export const mockVisionText = 'Build the AI-native product management layer that enables developers and AI assistants to maintain shared context without breaking flow state.';

// Mock Outcome Data
export const mockOutcomes: OutcomeDto[] = [
  {
    id: 'outcome-1',
    identifier: 'O-001',
    name: 'AI assistants can query product context natively',
    description: 'Enable Claude Code and other AI tools to access product decisions, user stories, and technical context through MCP integration.',
    workspace_id: 'workspace-1',
    display_order: 0,
    pillar_ids: ['pillar-1', 'pillar-2'],
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
    theme_ids: []
  },
  {
    id: 'outcome-2',
    identifier: 'O-002',
    name: 'Narrative consistency maintained over time',
    description: 'Product story remains coherent as features evolve, with health metrics tracking alignment between vision and implementation.',
    workspace_id: 'workspace-1',
    display_order: 1,
    pillar_ids: ['pillar-1'],
    created_at: '2025-01-16T10:00:00Z',
    updated_at: '2025-01-16T10:00:00Z',
    theme_ids: []
  },
  {
    id: 'outcome-3',
    identifier: 'O-003',
    name: 'Zero context-switching for developers',
    description: 'Developers stay in flow state by having all product context accessible within their IDE environment.',
    workspace_id: 'workspace-1',
    display_order: 0,
    pillar_ids: ['pillar-3'],
    created_at: '2025-01-17T10:00:00Z',
    updated_at: '2025-01-17T10:00:00Z',
    theme_ids: []
  },
];

// Mock Pillar Data
export const mockPillars: PillarDto[] = [
  {
    id: 'pillar-1',
    identifier: 'P-001',
    name: 'AI-Native Product Management',
    description: 'Build product management tools designed from the ground up for AI collaboration.',
    workspace_id: 'workspace-1',
    display_order: 0,
    outcome_ids: ['outcome-1', 'outcome-2'],
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
  },
  {
    id: 'pillar-3',
    identifier: 'P-003',
    name: 'Developer Experience First',
    description: 'Prioritize the needs of developers over administrative overhead.',
    workspace_id: 'workspace-1',
    display_order: 2,
    outcome_ids: ['outcome-3'],
    created_at: '2025-01-18T10:00:00Z',
    updated_at: '2025-01-18T10:00:00Z',
  },
];


// Mock Hero Data
export const mockHero: HeroRef = {
  id: 'hero-1',
  name: 'Sarah, The Solo Builder',
  identifier: 'HERO-1',
  description: 'A solo developer who juggles multiple projects alongside an AI coding assistant. She needs to keep product context accessible without breaking flow state.',
  is_primary: true,
};

export const mockSecondaryHero: HeroRef = {
  id: 'hero-2',
  name: 'Alex, The AI-Augmented PM',
  identifier: 'HERO-2',
  description: 'Product Manager leveraging AI for documentation and decision support.',
  is_primary: false,
};

// Mock Villain Data
export const mockVillains: VillainRef[] = [
  {
    id: 'villain-1',
    name: 'Context Fragmentation',
    identifier: 'VILLAIN-1',
    description: 'Product information scattered across multiple tools, making it hard for AI to understand what to build.',
    villain_type: VillainType.EXTERNAL,
    severity: 8,
    is_defeated: false,
  },
  {
    id: 'villain-2',
    name: 'Manual Documentation Overhead',
    identifier: 'VILLAIN-2',
    description: 'Traditional PM tools require constant manual updates, distracting from actual product work.',
    villain_type: VillainType.WORKFLOW,
    severity: 6,
    is_defeated: false,
  },
  {
    id: 'villain-3',
    name: 'Technical Debt',
    identifier: 'VILLAIN-3',
    description: 'Legacy code and architecture slowing down development.',
    villain_type: VillainType.TECHNICAL,
    severity: 7,
    is_defeated: false,
  },
  {
    id: 'villain-4',
    name: 'Performance Bottlenecks',
    identifier: 'VILLAIN-4',
    description: 'Slow response times affecting user experience.',
    villain_type: VillainType.TECHNICAL,
    severity: 5,
    is_defeated: false,
  },
];

// Mock Theme Data
export const mockThemes: ThemeDto[] = [
  {
    id: 'theme-1',
    identifier: 'T-001',
    workspace_id: 'workspace-1',
    name: 'MCP Integration for AI Context',
    description: 'Enable AI assistants to query product context natively through MCP server integration.',
    outcome_ids: ['outcome-1'],
    hero_ids: ['hero-1'],
    villain_ids: ['villain-1'],
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
  },
  {
    id: 'theme-2',
    identifier: 'T-002',
    workspace_id: 'workspace-1',
    name: 'Narrative Health Monitoring',
    description: 'Provide visibility into narrative consistency over time with health metrics and coverage scores.',
    outcome_ids: ['outcome-2'],
    hero_ids: ['hero-1'],
    villain_ids: ['villain-2'],
    created_at: '2025-01-16T10:00:00Z',
    updated_at: '2025-01-16T10:00:00Z',
  },
  {
    id: 'theme-3',
    identifier: 'T-003',
    workspace_id: 'workspace-1',
    name: 'Developer Experience First',
    description: 'Prioritize the needs of developers over administrative overhead.',
    outcome_ids: ['outcome-3'],
    hero_ids: [],
    villain_ids: [],
    created_at: '2025-01-17T10:00:00Z',
    updated_at: '2025-01-17T10:00:00Z',
  },
];

// Mock Arc Data
export const mockArc: ThemeDto = {
  id: 'arc-1',
  identifier: 'T-004',
  workspace_id: 'workspace-1',
  name: 'AI-Native Product Management',
  description: `OpenBacklog is pioneering a new category: the AI-native product management layer. We're building for solo developers and small teams who work alongside AI coding assistants like Claude Code, who need their product context to be immediately accessible to both humans and AI without breaking flow state.

Our hero, Sarah the Solo Builder, is trapped in a constant cycle of context switching between her IDE, planning tools, and documentation—preventing her AI assistant from understanding what to build and why. We're fighting against the fragmentation villain by transforming product management into a narrative format that AI can query and understand natively through MCP integration.

By treating product development as storytelling—with Heroes (users), Villains (problems), Story Arcs (strategic directions), and Beats (milestones)—we're creating a coherent, AI-accessible knowledge base that maintains narrative consistency over time.`,
  outcome_ids: ['outcome-1', 'outcome-2'],
  hero_ids: ['hero-1'],
  villain_ids: ['villain-1', 'villain-2'],
  created_at: '2025-01-15T10:00:00Z',
  updated_at: '2025-01-20T14:30:00Z',
};

export const mockShortArc: ThemeDto = {
  ...mockArc,
  id: 'arc-2',
  identifier: 'T-005',
  name: 'Performance Optimization',
  description: 'Improve application performance for power users.',
};

// Mock Beat Data
export const mockBeats: BeatItem[] = [
  {
    id: 'beat-1',
    initiativeId: 'initiative-1',
    identifier: 'BEAT-1',
    title: 'MCP Server Foundation',
    description: `Build the core MCP server infrastructure. ${lorem.generateParagraphs(7)}`,
    status: 'done',
    narrativeIntent: 'Establish the technical foundation for AI integration',
    strategicDescription: 'Core infrastructure enabling AI integration',
    progressPercent: 100,
    tasks: [
      { id: 'task-1', title: 'Setup MCP protocol', status: 'DONE' },
      { id: 'task-2', title: 'Create server endpoints', status: 'DONE' },
      { id: 'task-3', title: 'Write integration tests', status: 'DONE' },
    ],
    createdAt: '2025-01-10T10:00:00Z',
    updatedAt: '2025-01-15T10:00:00Z',
  },
  {
    id: 'beat-2',
    initiativeId: 'initiative-2',
    identifier: 'BEAT-2',
    title: 'Context Query API',
    description: `Enable AI to query product context. ${lorem.generateParagraphs(7)}`,
    status: 'in_progress',
    narrativeIntent: 'Allow AI assistants to understand product decisions',
    strategicDescription: 'Query interface for AI context access',
    progressPercent: 50,
    tasks: [
      { id: 'task-4', title: 'Design query interface', status: 'DONE' },
      { id: 'task-5', title: 'Implement query handlers', status: 'IN_PROGRESS' },
      { id: 'task-6', title: 'Add caching layer', status: 'TODO' },
      { id: 'task-7', title: 'Performance optimization', status: 'TODO' },
    ],
    createdAt: '2025-01-12T10:00:00Z',
    updatedAt: '2025-01-20T14:30:00Z',
  },
  {
    id: 'beat-3',
    initiativeId: 'initiative-3',
    identifier: 'BEAT-3',
    title: 'Narrative Health Metrics',
    description: `Track narrative consistency over time. ${lorem.generateParagraphs(7)}`,
    status: 'in_progress',
    narrativeIntent: 'Provide visibility into story coherence',
    strategicDescription: 'Health monitoring and analytics',
    progressPercent: 33,
    tasks: [
      { id: 'task-8', title: 'Define health metrics', status: 'DONE' },
      { id: 'task-9', title: 'Build analytics dashboard', status: 'IN_PROGRESS' },
      { id: 'task-10', title: 'Create alerts system', status: 'TODO' },
    ],
    createdAt: '2025-01-14T10:00:00Z',
    updatedAt: '2025-01-20T16:00:00Z',
  },
  {
    id: 'beat-4',
    initiativeId: 'initiative-4',
    identifier: 'BEAT-4',
    title: 'Claude Code Integration',
    description: `Deep integration with Claude Code IDE. ${lorem.generateParagraphs(7)}`,
    status: 'todo',
    narrativeIntent: 'Seamless workflow for developers using AI assistants',
    strategicDescription: 'IDE integration for developer workflow',
    progressPercent: 0,
    tasks: [
      { id: 'task-11', title: 'Research integration points', status: 'TODO' },
      { id: 'task-12', title: 'Design plugin architecture', status: 'TODO' },
      { id: 'task-13', title: 'Build prototype', status: 'TODO' },
    ],
    createdAt: '2025-01-18T10:00:00Z',
    updatedAt: '2025-01-18T10:00:00Z',
  },
];

// Mock Conflict Data
export const mockConflicts: ConflictDto[] = [
  {
    id: 'conflict-1',
    identifier: 'CONF-001',
    description: 'How do we balance AI automation with human control in product decisions?',
    status: ConflictStatus.OPEN,
    workspace_id: 'workspace-1',
    hero_id: 'hero-1',
    villain_id: 'villain-1',
    story_arc_id: 'arc-1',
    resolved_at: null,
    resolved_by_initiative_id: null,
    hero: {
      id: 'hero-1',
      name: 'Sarah, The Solo Builder',
      identifier: 'HERO-1',
      workspace_id: 'workspace-1',
      description: 'A solo developer who juggles multiple projects',
      is_primary: true,
      created_at: '2025-01-15T10:00:00Z',
      updated_at: '2025-01-15T10:00:00Z',
    },
    villain: {
      id: 'villain-1',
      name: 'Context Fragmentation',
      identifier: 'VILLAIN-1',
      user_id: 'user-1',
      workspace_id: 'workspace-1',
      description: 'Product information scattered across multiple tools',
      villain_type: VillainType.EXTERNAL,
      severity: 8,
      is_defeated: false,
      created_at: '2025-01-15T10:00:00Z',
      updated_at: '2025-01-15T10:00:00Z',
    },
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-20T14:30:00Z',
  },
  {
    id: 'conflict-2',
    identifier: 'CONF-002',
    description: 'Should we optimize for AI readability or human readability first?',
    status: ConflictStatus.ESCALATING,
    workspace_id: 'workspace-1',
    hero_id: 'hero-1',
    villain_id: 'villain-2',
    story_arc_id: 'arc-1',
    resolved_at: null,
    resolved_by_initiative_id: null,
    hero: {
      id: 'hero-1',
      name: 'Sarah, The Solo Builder',
      identifier: 'HERO-1',
      workspace_id: 'workspace-1',
      description: 'A solo developer who juggles multiple projects',
      is_primary: true,
      created_at: '2025-01-15T10:00:00Z',
      updated_at: '2025-01-15T10:00:00Z',
    },
    villain: {
      id: 'villain-2',
      name: 'Manual Documentation Overhead',
      identifier: 'VILLAIN-2',
      user_id: 'user-1',
      workspace_id: 'workspace-1',
      description: 'Traditional PM tools require constant manual updates',
      villain_type: VillainType.WORKFLOW,
      severity: 6,
      is_defeated: false,
      created_at: '2025-01-16T10:00:00Z',
      updated_at: '2025-01-16T10:00:00Z',
    },
    created_at: '2025-01-18T10:00:00Z',
    updated_at: '2025-01-18T10:00:00Z',
  },
  {
    id: 'conflict-3',
    identifier: 'CONF-003',
    description: 'How can we maintain narrative consistency as the product evolves?',
    status: ConflictStatus.RESOLVED,
    workspace_id: 'workspace-1',
    hero_id: 'hero-2',
    villain_id: 'villain-3',
    story_arc_id: 'arc-1',
    resolved_at: '2025-01-16T10:00:00Z',
    resolved_by_initiative_id: 'initiative-1',
    hero: {
      id: 'hero-2',
      name: 'Alex, The AI-Augmented PM',
      identifier: 'HERO-2',
      workspace_id: 'workspace-1',
      description: 'Product Manager leveraging AI',
      is_primary: false,
      created_at: '2025-01-15T10:00:00Z',
      updated_at: '2025-01-15T10:00:00Z',
    },
    villain: {
      id: 'villain-3',
      name: 'Technical Debt',
      identifier: 'VILLAIN-3',
      user_id: 'user-1',
      workspace_id: 'workspace-1',
      description: 'Legacy code and architecture slowing down development',
      villain_type: VillainType.TECHNICAL,
      severity: 7,
      is_defeated: false,
      created_at: '2025-01-17T10:00:00Z',
      updated_at: '2025-01-17T10:00:00Z',
    },
    created_at: '2025-01-10T10:00:00Z',
    updated_at: '2025-01-16T10:00:00Z',
  },
];

// Mock Metrics Data
export const mockMetrics: MetricsData = {
  completionPercent: 70,
  progressPercent: 65,
  healthPercent: 85,
  scenesComplete: 12,
  scenesTotal: 28,
  startDate: '2025-01-10T00:00:00Z',
  lastActivityDate: '2025-01-20T14:30:00Z',
  beatsComplete: 1,
  beatsInProgress: 2,
  beatsPlanned: 1,
};

export const mockHighProgressMetrics: MetricsData = {
  completionPercent: 95,
  progressPercent: 98,
  healthPercent: 92,
  scenesComplete: 27,
  scenesTotal: 28,
  startDate: '2025-01-10T00:00:00Z',
  lastActivityDate: '2025-01-22T10:00:00Z',
  beatsComplete: 3,
  beatsInProgress: 1,
  beatsPlanned: 0,
};

export const mockLowProgressMetrics: MetricsData = {
  completionPercent: 20,
  progressPercent: 15,
  healthPercent: 45,
  scenesComplete: 3,
  scenesTotal: 28,
  startDate: '2025-01-18T00:00:00Z',
  lastActivityDate: '2025-01-19T10:00:00Z',
  beatsComplete: 0,
  beatsInProgress: 1,
  beatsPlanned: 3,
};

export const mockZeroMetrics: MetricsData = {
  completionPercent: 0,
  progressPercent: 0,
  healthPercent: 50,
  scenesComplete: 0,
  scenesTotal: 0,
  startDate: '2025-01-20T00:00:00Z',
  lastActivityDate: '2025-01-20T00:00:00Z',
  beatsComplete: 0,
  beatsInProgress: 0,
  beatsPlanned: 0,
};

// Long text for testing
export const longStoryText = `OpenBacklog is pioneering a new category: the AI-native product management layer. We're building for solo developers and small teams who work alongside AI coding assistants like Claude Code, who need their product context to be immediately accessible to both humans and AI without breaking flow state.

Our hero, Sarah the Solo Builder, is trapped in a constant cycle of context switching between her IDE, planning tools, and documentation—preventing her AI assistant from understanding what to build and why. She loses hours every week re-explaining context to AI, copying information between tools, and maintaining documentation that quickly becomes stale.

We're fighting against the fragmentation villain by transforming product management into a narrative format that AI can query and understand natively through MCP integration. Instead of scattered Notion docs, Linear issues, and Slack threads, everything lives in one canonical story bible that both humans and AI can reference.

By treating product development as storytelling—with Heroes (users), Villains (problems), Story Arcs (strategic directions), and Beats (milestones)—we're creating a coherent, AI-accessible knowledge base that maintains narrative consistency over time. This isn't just another task manager; it's the canonical story bible for your product's universe.

The key insight is that narrative structure provides the semantic richness AI needs to understand not just what you're building, but why you're building it. When Claude Code can query "What problem does the current sprint solve?" or "Which hero will this feature serve?", it can generate better code and make smarter decisions.

This is a fundamental shift from document-driven to story-driven product management—where the narrative isn't documentation, it's the source of truth.`;

export const shortStoryText = 'Build the best AI-native product management tool for developers.';
