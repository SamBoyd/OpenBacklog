import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import {  useRoadmapThemes } from './useRoadmapThemes';
import * as useThemePrioritizationModule from '#hooks/useThemePrioritization';
import * as useHeroesModule from '#hooks/useHeroes';
import * as useVillainsModule from '#hooks/useVillains';
import * as useProductOutcomesModule from '#hooks/useProductOutcomes';
import * as useStrategicPillarsModule from '#hooks/useStrategicPillars';
import { ThemeDto } from '#api/productStrategy';
import { UseProductOutcomesReturn } from '#hooks/useProductOutcomes';
import { UseStrategicPillarsReturn } from '#hooks/useStrategicPillars';

// Mock the dependencies
vi.mock('#hooks/useThemePrioritization');
vi.mock('#hooks/useHeroes');
vi.mock('#hooks/useVillains');
vi.mock('#hooks/useProductOutcomes');
vi.mock('#hooks/useStrategicPillars');

describe(' useRoadmapThemes', () => {
  const mockWorkspaceId = 'workspace-1';

  const mockPrioritizedThemes: ThemeDto[] = [
    {
      id: 'theme-1',
      identifier: 'T-001',
      workspace_id: mockWorkspaceId,
      name: 'AI-First Product Management',
      description: 'Helping Sarah achieve flow',
      outcome_ids: ['outcome-1'],
      hero_ids: ['hero-1'],
      villain_ids: ['villain-1', 'villain-2'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'theme-2',
      identifier: 'T-002',
      workspace_id: mockWorkspaceId,
      name: 'Performance Optimization',
      description: 'Improving speed',
      outcome_ids: ['outcome-2'],
      hero_ids: ['hero-2'],
      villain_ids: [],
      created_at: '2024-01-05T00:00:00Z',
      updated_at: '2024-01-05T00:00:00Z',
    },
  ];

  const mockUnprioritizedThemes: ThemeDto[] = [
    {
      id: 'theme-3',
      identifier: 'T-003',
      workspace_id: mockWorkspaceId,
      name: 'Mobile App Launch',
      description: 'Native mobile apps',
      outcome_ids: [],
      hero_ids: [],
      villain_ids: [],
      created_at: '2024-03-01T00:00:00Z',
      updated_at: '2024-03-01T00:00:00Z',
    },
  ];

  const mockHeroes = [
    {
      id: 'hero-1',
      workspace_id: mockWorkspaceId,
      name: 'Sarah, The Solo Builder',
      identifier: 'H-001',
      description: 'A solo developer',
      is_primary: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'hero-2',
      workspace_id: mockWorkspaceId,
      name: 'Alex, The Power User',
      identifier: 'H-002',
      description: 'An advanced user',
      is_primary: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ];

  const mockVillains = [
    {
      id: 'villain-1',
      user_id: 'user-1',
      workspace_id: mockWorkspaceId,
      name: 'Context Switching',
      identifier: 'V-001',
      description: 'Constant interruptions',
      villain_type: 'WORKFLOW' as const,
      severity: 4,
      is_defeated: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'villain-2',
      user_id: 'user-1',
      workspace_id: mockWorkspaceId,
      name: 'AI Tool Ignorance',
      identifier: 'V-002',
      description: 'Lack of AI knowledge',
      villain_type: 'INTERNAL' as const,
      severity: 3,
      is_defeated: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ];

  const mockOutcomes = [
    {
      id: 'outcome-1',
      workspace_id: mockWorkspaceId,
      name: '80% AI feature adoption',
      description: 'Users actively use AI features weekly',
      display_order: 0,
      pillar_ids: ['pillar-1', 'pillar-2'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'outcome-2',
      workspace_id: mockWorkspaceId,
      name: 'Faster onboarding',
      description: 'Users complete onboarding in under 5 minutes',
      display_order: 1,
      pillar_ids: ['pillar-1'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ];

  const mockPillars = [
    {
      id: 'pillar-1',
      workspace_id: mockWorkspaceId,
      name: 'Developer Experience',
      description: 'Make developers love our product',
      display_order: 0,
      outcome_ids: ['outcome-1', 'outcome-2'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'pillar-2',
      workspace_id: mockWorkspaceId,
      name: 'AI-Native Product',
      description: 'AI at the core',
      display_order: 1,
      outcome_ids: ['outcome-1'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockRefetch = vi.fn();

  // Helper function to create complete mock return values
  const createMockThemePrioritization = (overrides = {}) => ({
    prioritizedThemes: [],
    unprioritizedThemes: [],
    isLoadingPrioritized: false,
    isLoadingUnprioritized: false,
    isLoading: false,
    prioritizedError: null,
    unprioritizedError: null,
    prioritizeTheme: vi.fn(),
    isPrioritizing: false,
    prioritizeError: null,
    deprioritizeTheme: vi.fn(),
    isDeprioritizing: false,
    deprioritizeError: null,
    reorderPrioritizedThemes: vi.fn(),
    isReordering: false,
    reorderError: null,
    ...overrides,
  });

  const createMockHeroes = (overrides = {}) => ({
    heroes: [],
    isLoading: false,
    error: null,
    refetch: mockRefetch as any,
    ...overrides,
  });

  const createMockVillains = (overrides = {}) => ({
    villains: [],
    isLoading: false,
    error: null,
    refetch: mockRefetch as any,
    ...overrides,
  });

  const createMockOutcomes = (overrides = {}): UseProductOutcomesReturn => ({
    outcomes: [],
    isLoading: false,
    error: null,
    createOutcome: vi.fn(),
    isCreating: false,
    createError: null,
    updateOutcome: vi.fn(),
    isUpdating: false,
    updateError: null,
    deleteOutcome: vi.fn(),
    isDeleting: false,
    deleteError: null,
    reorderOutcomes: vi.fn(),
    isReordering: false,
    reorderError: null,
    ...overrides,
  });

  const createMockPillars = (overrides = {}): UseStrategicPillarsReturn => ({
    pillars: [],
    isLoading: false,
    error: null,
    createPillar: vi.fn(),
    isCreating: false,
    createError: null,
    updatePillar: vi.fn(),
    isUpdating: false,
    updateError: null,
    deletePillar: vi.fn(),
    isDeleting: false,
    deleteError: null,
    reorderPillars: vi.fn(),
    isReordering: false,
    reorderError: null,
    ...overrides,
  });

  it('should separate prioritized and unprioritized themes', async () => {
    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization({
        prioritizedThemes: mockPrioritizedThemes,
        unprioritizedThemes: mockUnprioritizedThemes,
      })
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes({ heroes: mockHeroes })
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains({ villains: mockVillains })
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes()
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars()
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    await waitFor(() => {
      expect(result.current.prioritizedThemes).toHaveLength(2);
      expect(result.current.unprioritizedThemes).toHaveLength(1);
    });

    expect(result.current.prioritizedThemes[0].id).toBe('theme-1');
    expect(result.current.prioritizedThemes[1].id).toBe('theme-2');
    expect(result.current.unprioritizedThemes[0].id).toBe('theme-3');
  });

  it('should enrich themes with heroes and villains', async () => {
    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization({
        prioritizedThemes: mockPrioritizedThemes,
        unprioritizedThemes: [],
      })
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes({ heroes: mockHeroes })
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains({ villains: mockVillains })
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    await waitFor(() => {
      expect(result.current.prioritizedThemes).toHaveLength(2);
    });

    // First theme should have enriched heroes and villains
    const firstTheme = result.current.prioritizedThemes[0];
    expect(firstTheme.heroes).toHaveLength(1);
    expect(firstTheme.heroes?.[0].name).toBe('Sarah, The Solo Builder');
    expect(firstTheme.villains).toHaveLength(2);
    expect(firstTheme.villains?.[0].name).toBe('Context Switching');
    expect(firstTheme.villains?.[1].name).toBe('AI Tool Ignorance');

    // Second theme should have enriched hero, no villains
    const secondTheme = result.current.prioritizedThemes[1];
    expect(secondTheme.heroes).toHaveLength(1);
    expect(secondTheme.heroes?.[0].name).toBe('Alex, The Power User');
    expect(secondTheme.villains).toHaveLength(0);
  });

  it('should enrich themes with outcomes and derived pillars', async () => {
    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization({
        prioritizedThemes: mockPrioritizedThemes,
        unprioritizedThemes: [],
      })
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes()
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains()
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes({ outcomes: mockOutcomes })
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars({ pillars: mockPillars })
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    await waitFor(() => {
      expect(result.current.prioritizedThemes).toHaveLength(2);
    });

    // First theme (outcome-1) should have 1 outcome and 2 pillars
    const firstTheme = result.current.prioritizedThemes[0];
    expect(firstTheme.outcomes).toHaveLength(1);
    expect(firstTheme.outcomes?.[0].name).toBe('80% AI feature adoption');
    expect(firstTheme.pillars).toHaveLength(2);
    expect(firstTheme.pillars?.map(p => p.name).sort()).toEqual([
      'AI-Native Product',
      'Developer Experience',
    ]);

    // Second theme (outcome-2) should have 1 outcome and 1 pillar
    const secondTheme = result.current.prioritizedThemes[1];
    expect(secondTheme.outcomes).toHaveLength(1);
    expect(secondTheme.outcomes?.[0].name).toBe('Faster onboarding');
    expect(secondTheme.pillars).toHaveLength(1);
    expect(secondTheme.pillars?.[0].name).toBe('Developer Experience');
  });

  it('should derive unique pillars when outcomes share pillars', async () => {
    const themesWithSharedPillars: ThemeDto[] = [
      {
        id: 'theme-shared',
        identifier: 'T-004',
        workspace_id: mockWorkspaceId,
        name: 'Multi-Outcome Theme',
        description: 'Has multiple outcomes with overlapping pillars',
        outcome_ids: ['outcome-1', 'outcome-2'],
        hero_ids: [],
        villain_ids: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ];

    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization({
        prioritizedThemes: themesWithSharedPillars,
        unprioritizedThemes: [],
      })
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes()
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains()
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes({ outcomes: mockOutcomes })
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars({ pillars: mockPillars })
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    await waitFor(() => {
      expect(result.current.prioritizedThemes).toHaveLength(1);
    });

    const theme = result.current.prioritizedThemes[0];
    // outcome-1 has [pillar-1, pillar-2], outcome-2 has [pillar-1]
    // Should deduplicate to [pillar-1, pillar-2]
    expect(theme.pillars).toHaveLength(2);
    expect(theme.pillars?.map(p => p.name).sort()).toEqual([
      'AI-Native Product',
      'Developer Experience',
    ]);
  });

  it('should handle combined loading states correctly', async () => {
    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization({
        isLoadingPrioritized: true,
        isLoadingUnprioritized: false,
      })
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes({ isLoading: false })
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains({ isLoading: false })
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes({ isLoading: false })
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars({ isLoading: false })
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isLoadingPrioritized).toBe(true);
    expect(result.current.isLoadingUnprioritized).toBe(false);
  });

  it('should handle all data sources loading', async () => {
    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization({
        isLoadingPrioritized: true,
        isLoadingUnprioritized: true,
      })
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes({ isLoading: true })
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains({ isLoading: true })
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes({ isLoading: true })
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars({ isLoading: true })
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    expect(result.current.isLoading).toBe(true);
  });

  it('should propagate errors from theme prioritization', async () => {
    const prioritizedError = new Error('Failed to load prioritized themes');

    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization({
        prioritizedError,
      })
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes()
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains()
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes()
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars()
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    expect(result.current.error).toBe(prioritizedError);
  });

  it('should propagate errors from heroes', async () => {
    const heroesError = new Error('Failed to load heroes');

    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization()
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes({ error: heroesError })
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains()
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes()
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars()
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    expect(result.current.error).toBe(heroesError);
  });

  it('should handle empty state correctly', async () => {
    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization()
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes()
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains()
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes()
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars()
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    await waitFor(() => {
      expect(result.current.prioritizedThemes).toEqual([]);
      expect(result.current.unprioritizedThemes).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  it('should handle themes with non-existent hero/villain IDs gracefully', async () => {
    const themesWithBadIds: ThemeDto[] = [
      {
        id: 'theme-bad',
        identifier: 'T-005',
        workspace_id: mockWorkspaceId,
        name: 'Theme with missing references',
        description: 'Has IDs that dont exist',
        outcome_ids: [],
        hero_ids: ['non-existent-hero'],
        villain_ids: ['non-existent-villain-1', 'non-existent-villain-2'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ];

    vi.spyOn(useThemePrioritizationModule, 'useThemePrioritization').mockReturnValue(
      createMockThemePrioritization({
        prioritizedThemes: themesWithBadIds,
        unprioritizedThemes: [],
      })
    );

    vi.spyOn(useHeroesModule, 'useHeroes').mockReturnValue(
      createMockHeroes({ heroes: mockHeroes })
    );

    vi.spyOn(useVillainsModule, 'useVillains').mockReturnValue(
      createMockVillains({ villains: mockVillains })
    );

    vi.spyOn(useProductOutcomesModule, 'useProductOutcomes').mockReturnValue(
      createMockOutcomes()
    );

    vi.spyOn(useStrategicPillarsModule, 'useStrategicPillars').mockReturnValue(
      createMockPillars()
    );

    const { result } = renderHook(() =>  useRoadmapThemes(mockWorkspaceId));

    await waitFor(() => {
      expect(result.current.prioritizedThemes).toHaveLength(1);
    });

    // Should filter out non-existent references
    const theme = result.current.prioritizedThemes[0];
    expect(theme.heroes).toEqual([]);
    expect(theme.villains).toEqual([]);
  });
});
