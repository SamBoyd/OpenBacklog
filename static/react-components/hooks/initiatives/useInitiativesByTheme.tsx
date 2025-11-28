import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStrategicInitiativesByTheme } from '#api/productStrategy';
import { TaskDto, InitiativeDto, StrategicInitiativeDto } from '#types';

/**
 * Flattened beat item combining strategic initiative context with full initiative data.
 */
export interface BeatItem {
  id: string; // Strategic initiative ID
  initiativeId: string; // Actual initiative ID
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done';
  identifier: string;
  narrativeIntent: string | null;
  strategicDescription: string | null;
  tasks: Partial<TaskDto>[];
  createdAt: string;
  updatedAt: string;
  progressPercent: number; // Calculated from tasks
}

/**
 * Calculates the progress percentage based on task completion.
 * @param {Partial<TaskDto>[]} tasks - Array of tasks
 * @returns {number} Progress percentage (0-100)
 */
function calculateTaskProgress(tasks: Partial<TaskDto>[]): number {
  if (!tasks || tasks.length === 0) {
    return 0;
  }

  const completedTasks = tasks.filter(task => task.status === 'DONE').length;
  return Math.round((completedTasks / tasks.length) * 100);
}

/**
 * Maps initiative status to simplified beat status.
 * @param {string} status - Initiative status
 * @returns {'todo' | 'in_progress' | 'done'} Simplified status
 */
function mapToBeatStatus(status: string): 'todo' | 'in_progress' | 'done' {
  switch (status) {
    case 'DONE':
    case 'ARCHIVED':
      return 'done';
    case 'IN_PROGRESS':
    case 'BLOCKED':
      return 'in_progress';
    case 'TO_DO':
    case 'BACKLOG':
    default:
      return 'todo';
  }
}

/**
 * Custom hook for fetching strategic initiatives by theme, flattened into beat items.
 * Each beat combines the strategic context with the full initiative data including tasks.
 * @param {string} workspaceId - The workspace ID
 * @param {string} themeId - The theme ID
 * @returns {object} Object containing beats array, loading state, error, and refetch function
 */
export function useInitiativesByTheme(workspaceId: string, themeId: string) {
  const {
    data: strategicInitiatives,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['strategic-initiatives', 'theme', workspaceId, themeId],
    queryFn: () => getStrategicInitiativesByTheme(workspaceId, themeId),
    enabled: !!workspaceId && !!themeId,
  });

  // Transform strategic initiatives into beat items
  const beats = useMemo<BeatItem[]>(() => {
    if (!strategicInitiatives || strategicInitiatives.length === 0) {
      return [];
    }

    return strategicInitiatives
      .filter((si: StrategicInitiativeDto) => si.initiative) // Only include if initiative data is present
      .map((si: StrategicInitiativeDto) => {
        const initiative = si.initiative as InitiativeDto;
        const tasks = initiative.tasks || [];

        return {
          id: si.id,
          initiativeId: si.initiative_id,
          title: initiative.title,
          description: initiative.description,
          status: mapToBeatStatus(initiative.status),
          identifier: initiative.identifier,
          narrativeIntent: si.narrative_intent,
          strategicDescription: si.description,
          tasks: tasks,
          createdAt: initiative.created_at,
          updatedAt: initiative.updated_at,
          progressPercent: calculateTaskProgress(tasks),
        };
      });
  }, [strategicInitiatives]);

  return {
    beats,
    isLoading,
    error,
    refetch,
  };
}
