import { InitiativeDto, InitiativeStatus, ContextType, EntityType } from '#types';
import { OrderedEntity } from '#hooks/useOrderings';

/**
 * Filter type for initiatives queries
 */
export type InitiativeFilters = {
  id?: string;
  ids?: string[];
  status?: string[];
};

/**
 * Core initiatives data and loading states
 */
export interface InitiativesQueryResult {
  initiativesData: OrderedEntity<InitiativeDto>[] | null;
  error: string | null;
  shouldShowSkeleton: boolean;
  isQueryFetching: boolean;
  reloadInitiatives: () => void;
}

/**
 * Cache management operations
 */
export interface InitiativesCacheOperations {
  invalidateInitiative: (initiativeId: string) => void;
  invalidateAllInitiatives: () => void;
  invalidateInitiativesByStatus: (status: InitiativeStatus | InitiativeStatus[]) => void;
  updateInitiativeInCache: (initiative: InitiativeDto, oldStatus?: string) => void;
}

/**
 * All mutation operations and their loading states
 */
export interface InitiativesMutationOperations {
  isCreatingInitiative: boolean;
  isUpdatingInitiative: boolean;
  isDeletingInitiative: boolean;
  isBatchUpdatingInitiatives: boolean;
  isDeletingTask: boolean;
  isDeletingChecklistItem: boolean;

  createInitiative: (
    initiative: Partial<InitiativeDto>,
    orderingContext?: {
      contextType?: ContextType;
      contextId?: string | null;
      entityType?: EntityType;
    }
  ) => Promise<InitiativeDto>;
  updateInitiative: (initiative: Partial<InitiativeDto>) => Promise<InitiativeDto>;
  updateInitiatives: (initiatives: Partial<InitiativeDto>[]) => Promise<InitiativeDto[]>;
  deleteInitiative: (initiativeId: string) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
  deleteChecklistItem: (checklistItemId: string) => Promise<void>;

  // Reordering operations
  reorderInitiative: (initiativeId: string, afterId: string | null, beforeId: string | null) => Promise<void>;
  moveInitiativeToStatus: (initiativeId: string, newStatus: InitiativeStatus, afterId: string | null, beforeId: string | null) => Promise<void>;
  moveInitiativeInGroup: (initiativeId: string, groupId: string, afterId: string | null, beforeId: string | null) => Promise<void>;
}

/**
 * Complete initiatives context interface - matches the original for backward compatibility
 */
export interface InitiativesContextType extends
  InitiativesQueryResult,
  InitiativesCacheOperations,
  InitiativesMutationOperations {}

/**
 * Context for optimistic mutations
 */
export interface InitiativeMutationContext {
  previousInitiatives: InitiativeDto[] | undefined;
  queryKey: any[];
  previousStatus?: string;
  deletedInitiative?: InitiativeDto;
  oldStatus?: string;
}