import { useMemo } from 'react';
import { useRoadmapThemeById } from '#hooks/useRoadmapThemeById';
import { useInitiativesByTheme, BeatItem } from '#hooks/initiatives/useInitiativesByTheme';
import { useConflicts } from '#hooks/useConflicts';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes';
import { ThemeDto, HeroRef, VillainRef } from '#api/productStrategy';
import { ConflictDto } from '#types';

/**
 * Metrics data derived from the story arc's beats and tasks.
 */
export interface MetricsData {
  completionPercent: number; // (completed beats / total beats) * 100
  progressPercent: number; // (completed tasks / total tasks) * 100
  healthPercent: number; // Hardcoded 85% for MVP
  scenesComplete: number; // Sum of completed tasks
  scenesTotal: number; // Sum of all tasks
  startDate: string; // From theme created_at or first beat
  lastActivityDate: string; // From theme updated_at or last beat
  beatsComplete: number; // Count of 'done' beats
  beatsInProgress: number; // Count of 'in_progress' beats
  beatsPlanned: number; // Count of 'todo' beats
}

/**
 * Complete story arc detail data for the detail page.
 */
export interface StoryArcDetailData {
  arc: ThemeDto | null;
  hero: HeroRef | null; // Primary hero from the theme
  villains: VillainRef[]; // Villains associated with the theme
  themes: ThemeDto[]; // All other themes in the workspace
  beats: BeatItem[]; // Strategic initiatives as story beats
  conflicts: ConflictDto[]; // Conflicts filtered by arc ID
  metrics: MetricsData;
  isLoading: boolean;
  error: string | null;
}

/**
 * Calculates metrics data from beats.
 * @param {BeatItem[]} beats - Array of beat items
 * @param {ThemeDto | null} theme - The theme/arc
 * @returns {MetricsData} Calculated metrics
 */
function calculateMetrics(beats: BeatItem[], theme: ThemeDto | null): MetricsData {
  const beatsComplete = beats.filter(beat => beat.status === 'done').length;
  const beatsInProgress = beats.filter(beat => beat.status === 'in_progress').length;
  const beatsPlanned = beats.filter(beat => beat.status === 'todo').length;
  const totalBeats = beats.length;

  // Calculate completion percentage
  const completionPercent = totalBeats > 0 ? Math.round((beatsComplete / totalBeats) * 100) : 0;

  // Calculate progress from tasks
  const allTasks = beats.flatMap(beat => beat.tasks);
  const completedTasks = allTasks.filter(task => task?.status === 'DONE').length;
  const totalTasks = allTasks.length;
  const progressPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  // Find start date and last activity date
  let startDate = theme?.created_at || new Date().toISOString();
  let lastActivityDate = theme?.updated_at || new Date().toISOString();

  if (beats.length > 0) {
    // Use earliest beat created_at as start date if available
    const beatDates = beats.map(beat => new Date(beat.createdAt).getTime());
    const earliestBeatDate = new Date(Math.min(...beatDates)).toISOString();
    if (new Date(earliestBeatDate) < new Date(startDate)) {
      startDate = earliestBeatDate;
    }

    // Use latest beat updated_at as last activity
    const beatUpdateDates = beats.map(beat => new Date(beat.updatedAt).getTime());
    const latestBeatDate = new Date(Math.max(...beatUpdateDates)).toISOString();
    if (new Date(latestBeatDate) > new Date(lastActivityDate)) {
      lastActivityDate = latestBeatDate;
    }
  }

  return {
    completionPercent,
    progressPercent,
    healthPercent: 85, // Hardcoded for MVP
    scenesComplete: completedTasks,
    scenesTotal: totalTasks,
    startDate,
    lastActivityDate,
    beatsComplete,
    beatsInProgress,
    beatsPlanned,
  };
}

/**
 * Main composition hook for the Story Arc Detail Page.
 * Combines data from multiple sources to provide complete context for a story arc.
 * @param {string} workspaceId - The workspace ID
 * @param {string} arcId - The arc/theme ID
 * @returns {StoryArcDetailData} Complete story arc detail data
 */
export function useStoryArcDetail(workspaceId: string, arcId: string): StoryArcDetailData {
  // Fetch the specific theme/arc with heroes and villains
  const {
    theme: arc,
    heroes: arcHeroes,
    villains: arcVillains,
    isLoading: isLoadingArc,
    error: arcError,
  } = useRoadmapThemeById(workspaceId, arcId);

  // Fetch beats (strategic initiatives) for this theme
  const {
    beats,
    isLoading: isLoadingBeats,
    error: beatsError,
  } = useInitiativesByTheme(workspaceId, arcId);

  // Fetch all conflicts and filter by arc ID
  const {
    conflicts: allConflicts,
    isLoading: isLoadingConflicts,
    error: conflictsError,
  } = useConflicts();

  // Fetch all themes to provide context (other arcs)
  const {
    themes: allThemes,
    isLoading: isLoadingThemes,
    error: themesError,
  } = useRoadmapThemes(workspaceId);

  // Filter conflicts by arc ID
  const conflicts = useMemo(() => {
    if (!allConflicts) return [];
    return allConflicts.filter(conflict => conflict.story_arc_id === arcId);
  }, [allConflicts, arcId]);

  // Filter out current arc from themes list
  const otherThemes = useMemo(() => {
    if (!allThemes) return [];
    return allThemes.filter(theme => theme.id !== arcId);
  }, [allThemes, arcId]);

  // Get primary hero (first one in the list, or null if none)
  const hero = useMemo(() => {
    return arcHeroes.length > 0 ? arcHeroes[0] : null;
  }, [arcHeroes]);

  // Calculate metrics
  const metrics = useMemo(() => {
    return calculateMetrics(beats, arc);
  }, [beats, arc]);

  // Aggregate loading and error states
  const isLoading = isLoadingArc || isLoadingBeats || isLoadingConflicts || isLoadingThemes;

  // Combine errors - convert string errors to Error objects
  let combinedError: string | null = null;
  if (arcError) {
    combinedError = arcError instanceof Error ? String(arcError) : arcError;
  } else if (beatsError) {
    combinedError = beatsError instanceof Error ? String(beatsError) : beatsError;
  } else if (conflictsError) {
    combinedError = conflictsError;
  } else if (themesError) {
    combinedError = themesError instanceof Error ? String(themesError) : themesError;
  }

  return {
    arc,
    hero,
    villains: arcVillains,
    themes: otherThemes,
    beats,
    conflicts,
    metrics,
    isLoading,
    error: combinedError,
  };
}
