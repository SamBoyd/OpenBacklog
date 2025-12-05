import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import {  useRoadmapThemes } from './useRoadmapThemes';
import * as useThemePrioritizationModule from '#hooks/useThemePrioritization';
import * as useHeroesModule from '#hooks/useHeroes';
import * as useVillainsModule from '#hooks/useVillains';
import { ThemeDto } from '#api/productStrategy';

// Mock the dependencies
vi.mock('#hooks/useThemePrioritization');
vi.mock('#hooks/useHeroes');
vi.mock('#hooks/useVillains');

describe(' useRoadmapThemes', () => {
  const mockWorkspaceId = 'workspace-1';

  const mockPrioritizedThemes: ThemeDto[] = [
    {
      id: 'theme-1',
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
