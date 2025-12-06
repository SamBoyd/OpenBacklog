/**
 * Type definitions for Story Arc Detail Page.
 *
 * This module centralizes all TypeScript interfaces and types needed for the
 * Story Arc Detail page components, hooks, and data transformations.
 */

// Import types from other modules
import type { ThemeDto, HeroRef, VillainRef } from '#api/productStrategy';
import type { ConflictDto, TaskDto, InitiativeDto } from '#types';

// Re-export commonly used types for convenience
export type { ThemeDto, HeroRef, VillainRef } from '#api/productStrategy';
export type { ConflictDto, TaskDto, InitiativeDto } from '#types';

/**
 * Represents a beat (initiative) in a story arc with narrative context.
 * This is the core data structure for displaying initiatives as narrative beats.
 */
export interface BeatItem {
  id: string;
  initiativeId: string;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'done';
  narrativeIntent: string | null;
  tasks: Partial<TaskDto>[];
  createdAt: string;
  updatedAt: string;
}

/**
 * Aggregated metrics data for a story arc.
 * Provides quantitative insights into arc progress and health.
 */
export interface MetricsData {
  completionPercent: number;
  progressPercent: number;
  healthPercent: number;
  scenesComplete: number;
  scenesTotal: number;
  startDate: string;
  lastActivityDate: string;
  beatsComplete: number;
  beatsInProgress: number;
  beatsPlanned: number;
}

/**
 * Complete data structure for a story arc detail view.
 * Combines arc metadata, narrative context, beats, and metrics.
 */
export interface RoadmapThemeDetailData {
  arc: ThemeDto;
  hero: HeroRef | null;
  villains: VillainRef[];
  themes: ThemeDto[];
  beats: BeatItem[];
  conflicts: ConflictDto[];
  metrics: MetricsData;
}

/**
 * Props for the header section of the story arc detail page.
 * Includes arc metadata and action handlers.
 */
export interface HeaderSectionProps {
  arcTitle: string;
  arcSubtitle?: string;
  arcStatus?: 'planning' | 'in_progress' | 'climax' | 'complete' | 'archived';
  onEditMode: () => void;
  onViewRoadmap: () => void;
  onShare: () => void;
  onLinkEntity: () => void;
  onDelete: () => void;
}

/**
 * Props for the narrative context bar component.
 * Displays hero, villains, themes, and progress indicators.
 */
export interface NarrativeContextBarProps {
  hero: HeroRef | null;
  villains: VillainRef[];
  themes: ThemeDto[];
  progressPercent: number;
  healthPercent: number;
  onHeroClick?: (heroId: string) => void;
  onVillainClick?: (villainId: string) => void;
  onThemeClick?: (themeId: string) => void;
}

/**
 * Props for the story section component.
 * Displays the narrative description of the story arc.
 */
export interface StorySectionProps {
  storyText: string;
  isLoading?: boolean;
  onRegenerateClick?: () => void;
  onEditClick?: () => void;
}

/**
 * Props for the beats (initiatives) section component.
 * Displays the list of story beats with filtering and actions.
 */
export interface BeatsSectionProps {
  beats: BeatItem[];
  arcId: string;
  isLoading?: boolean;
  onViewBeat: (initiativeId: string) => void;
  onAddBeat?: () => void;
}

/**
 * Props for the narrative connections section.
 * Shows relationships between hero, villains, and themes.
 */
export interface NarrativeConnectionsSectionProps {
  hero: HeroRef | null;
  villains: VillainRef[];
  themes: ThemeDto[];
  onEditLinks?: () => void;
}

/**
 * Props for the conflicts and stakes section.
 * Displays active conflicts and their resolution status.
 */
export interface ConflictsStakesSectionProps {
  conflicts: ConflictDto[];
  arcId: string;
  onAddConflict?: () => void;
}

/**
 * Props for placeholder/empty state sections.
 * Used when a section has no data to display.
 */
export interface PlaceholderSectionProps {
  title: string;
  emptyMessage: string;
  actionButton?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Props for the metrics section component.
 * Displays quantitative progress and health metrics.
 */
export interface MetricsSectionProps {
  completionPercent: number;
  scenesComplete: number;
  scenesTotal: number;
  beatsComplete: number;
  beatsInProgress: number;
  beatsPlanned: number;
  startDate: string;
  lastActivityDate: string;
}

/**
 * Props for the main roadmap theme detail layout component.
 * Orchestrates all section components and manages overall page state.
 */
export interface RoadmapThemeDetailLayoutProps {
  arc: ThemeDto;
  hero: HeroRef | null;
  villains: VillainRef[];
  themes: ThemeDto[];
  beats: BeatItem[];
  conflicts: ConflictDto[];
  metrics: MetricsData;
  isLoading: boolean;
  error: String | null;
  onViewBeat: (initiativeId: string) => void;
}
