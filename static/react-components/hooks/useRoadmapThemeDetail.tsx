import { useMemo } from 'react';
import { useRoadmapThemeById } from '#hooks/useRoadmapThemeById';
import { useInitiativesByTheme, BeatItem } from '#hooks/initiatives/useInitiativesByTheme';
import { useConflicts } from '#hooks/useConflicts';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes';
import { useProductVision } from '#hooks/useProductVision';
import { useProductOutcomes } from '#hooks/useProductOutcomes';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { ThemeDto, HeroRef, VillainRef, PillarDto } from '#api/productStrategy';
import { OutcomeDto } from '#api/productOutcomes';
import { ConflictDto } from '#types';

/**
 * Metrics data derived from the roadmap theme's beats and tasks.
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
 * Complete roadmap theme detail data for the detail page.
 */
export interface RoadmapThemeDetailData {
  arc: ThemeDto | null;
  hero: HeroRef | null; // Primary hero from the theme
  villains: VillainRef[]; // Villains associated with the theme
  beats: BeatItem[]; // Strategic initiatives as story beats
  conflicts: ConflictDto[]; // Conflicts filtered by arc ID
  outcomes: OutcomeDto[]; // Outcomes linked to this theme
  pillars: PillarDto[]; // Strategic pillars linked to this theme
  visionText: string | null; // Product vision text
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
 * Main composition hook for the Roadmap theme Detail Page.
 * Combines data from multiple sources to provide complete context for a roadmap theme.
 * @param {string} workspaceId - The workspace ID
 * @param {string} arcId - The arc/theme ID
 * @returns {RoadmapThemeDetailData} Complete roadmap theme detail data
 */
export function useRoadmapThemeDetail(workspaceId: string, arcId: string): RoadmapThemeDetailData {
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

  // Fetch workspace vision
  const {
    vision,
    isLoading: isLoadingVision,
    error: visionError,
  } = useProductVision(workspaceId);

  // Fetch all product outcomes
  const {
    outcomes: allOutcomes,
    isLoading: isLoadingOutcomes,
    error: outcomesError,
  } = useProductOutcomes(workspaceId);

  // Fetch all strategic pillars
  const {
    pillars: allPillars,
    isLoading: isLoadingPillars,
    error: pillarsError,
  } = useStrategicPillars(workspaceId);

  // Filter conflicts by arc ID
  const conflicts = useMemo(() => {
    if (!allConflicts) return [];
    return allConflicts.filter(conflict => conflict.story_arc_id === arcId);
  }, [allConflicts, arcId]);

  // Get outcomes linked to this theme
  const outcomes = useMemo(() => {
    if (!arc || !allOutcomes) return [];
    // Filter outcomes by theme's outcome_ids
    return allOutcomes.filter(outcome => outcome.theme_ids.includes(arc.id));
  }, [allOutcomes, arc]);

  // Get pillars linked to this theme (derived through outcomes)
  const pillars = useMemo(() => {
    if (!arc || !allPillars || !outcomes) return [];
    // Collect unique pillar IDs from all outcomes linked to this theme
    const derivedPillarIds = new Set<string>();
    outcomes.forEach((outcome) => {
      outcome.pillar_ids?.forEach((pillarId) => derivedPillarIds.add(pillarId));
    });
    return allPillars.filter(pillar => derivedPillarIds.has(pillar.id));
  }, [arc, allPillars, outcomes]);

  // Get vision text
  const visionText = useMemo(() => {
    return vision?.vision_text || null;
  }, [vision]);

  // Get primary hero (first one in the list, or null if none)
  const hero = useMemo(() => {
    return arcHeroes.length > 0 ? arcHeroes[0] : null;
  }, [arcHeroes]);

  // Calculate metrics
  const metrics = useMemo(() => {
    return calculateMetrics(beats, arc);
  }, [beats, arc]);

  // Aggregate loading and error states
  const isLoading = isLoadingArc || isLoadingBeats || isLoadingConflicts || isLoadingVision || isLoadingOutcomes;

  // Combine errors - convert string errors to Error objects
  let combinedError: string | null = null;
  if (arcError) {
    combinedError = arcError instanceof Error ? String(arcError) : arcError;
  } else if (beatsError) {
    combinedError = beatsError instanceof Error ? String(beatsError) : beatsError;
  } else if (conflictsError) {
    combinedError = conflictsError;
  } else if (visionError) {
    combinedError = visionError instanceof Error ? String(visionError) : visionError;
  } else if (outcomesError) {
    combinedError = outcomesError instanceof Error ? String(outcomesError) : outcomesError;
  }

  return {
    arc,
    hero,
    villains: arcVillains,
    beats,
    conflicts,
    outcomes,
    pillars,
    visionText,
    metrics,
    isLoading,
    error: combinedError,
  };
}
