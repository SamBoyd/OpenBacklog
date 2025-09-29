import * as Sentry from '@sentry/react';
import { ManagedInitiativeModel, ManagedTaskModel } from '#types';

/**
 * Analytics and logging functions for the useSaveSuggestions hook.
 * Centralizes all Sentry breadcrumb logging to keep the main hook clean.
 */

/**
 * Log validation failure when suggestions are not fully resolved
 */
export const logSuggestionsNotFullyResolved = (): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.process',
    message: 'Suggestions save failed - not fully resolved',
    level: 'warning',
    data: {
      error: 'Suggestions are not fully resolved'
    }
  });
};

/**
 * Log the start of the suggestions save process
 */
export const logSuggestionsSaveStarted = (
  acceptedChanges: ManagedInitiativeModel[],
  hasJobResult: boolean
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.process',
    message: 'Suggestions save started',
    level: 'info',
    data: {
      totalChanges: acceptedChanges.length,
      initiativeIds: acceptedChanges.map(change =>
        'identifier' in change ? change.identifier : `NEW_${change.action}`
      ),
      hasJobResult
    }
  });
};

/**
 * Log successful completion of the suggestions save process
 */
export const logSuggestionsSaveCompleted = (
  totalChanges: number,
  jobMarkedResolved: boolean
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.process',
    message: 'Suggestions save completed successfully',
    level: 'info',
    data: {
      totalChanges,
      jobMarkedResolved
    }
  });
};

/**
 * Log error during the suggestions save process
 */
export const logSuggestionsSaveError = (
  error: unknown,
  totalInitiativeData: number,
  totalTaskData: number,
  hasJobResult: boolean
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.process',
    message: 'Suggestions save failed with error',
    level: 'error',
    data: {
      error: error instanceof Error ? error.message : String(error),
      errorType: error instanceof Error ? error.constructor.name : typeof error,
      stackTrace: error instanceof Error ? error.stack?.slice(0, 500) : undefined,
      totalInitiativeData,
      totalTaskData,
      hasJobResult
    }
  });
};

/**
 * Log attempt to resolve an entity identifier
 */
export const logEntityResolutionAttempt = (
  identifier: string,
  entityType: string,
  availableIds: string[],
  totalAvailable: number
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.resolution',
    message: `Resolving ${entityType} identifier`,
    level: 'info',
    data: {
      identifier,
      entityType,
      availableIds,
      totalAvailable
    }
  });
};

/**
 * Log failed entity identifier resolution
 */
export const logEntityResolutionFailure = (
  identifier: string,
  entityType: string,
  availableIds: string[]
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.resolution',
    message: `Failed to resolve ${entityType} identifier`,
    level: 'warning',
    data: {
      identifier,
      entityType,
      availableIds
    }
  });
};

/**
 * Log successful entity identifier resolution
 */
export const logEntityResolutionSuccess = (
  identifier: string,
  entityType: string,
  resolvedId: string
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.resolution',
    message: `Successfully resolved ${entityType} identifier`,
    level: 'info',
    data: {
      identifier,
      entityType,
      resolvedId
    }
  });
};

/**
 * Log initiative CREATE operation
 */
export const logInitiativeCreateStarted = (managedInitiative: ManagedInitiativeModel): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.entity',
    message: 'Initiative CREATE started',
    level: 'info',
    data: {
      action: 'CREATE',
      entityType: 'initiative',
      title: 'title' in managedInitiative ? managedInitiative.title?.slice(0, 50) : undefined,
      hasDescription: 'description' in managedInitiative ? !!managedInitiative.description : undefined,
      taskCount: 'tasks' in managedInitiative ? (managedInitiative.tasks?.length || 0) : undefined
    }
  });
};

/**
 * Log initiative UPDATE operation
 */
export const logInitiativeUpdateStarted = (managedInitiative: ManagedInitiativeModel): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.entity',
    message: 'Initiative UPDATE started',
    level: 'info',
    data: {
      action: 'UPDATE',
      entityType: 'initiative',
      identifier: 'identifier' in managedInitiative ? managedInitiative.identifier : undefined,
      title: 'title' in managedInitiative ? managedInitiative.title?.slice(0, 50) : undefined,
      hasDescription: 'description' in managedInitiative ? !!managedInitiative.description : undefined,
      taskCount: 'tasks' in managedInitiative ? (managedInitiative.tasks?.length || 0) : undefined
    }
  });
};

/**
 * Log initiative DELETE operation
 */
export const logInitiativeDeleteStarted = (managedInitiative: ManagedInitiativeModel): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.entity',
    message: 'Initiative DELETE started',
    level: 'info',
    data: {
      action: 'DELETE',
      entityType: 'initiative',
      identifier: 'identifier' in managedInitiative ? managedInitiative.identifier : undefined
    }
  });
};

/**
 * Log task CREATE operation
 */
export const logTaskCreateStarted = (
  task: ManagedTaskModel,
  managedInitiative: ManagedInitiativeModel
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.entity',
    message: 'Task CREATE started',
    level: 'info',
    data: {
      action: 'CREATE',
      entityType: 'task',
      title: 'title' in task ? task.title?.slice(0, 50) : undefined,
      hasDescription: 'description' in task ? !!task.description : undefined,
      initiativeIdentifier: 'identifier' in managedInitiative ? managedInitiative.identifier : 'NEW_INITIATIVE'
    }
  });
};

/**
 * Log task UPDATE operation
 */
export const logTaskUpdateStarted = (
  task: ManagedTaskModel,
  managedInitiative: ManagedInitiativeModel
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.entity',
    message: 'Task UPDATE started',
    level: 'info',
    data: {
      action: 'UPDATE',
      entityType: 'task',
      identifier: 'identifier' in task ? task.identifier : undefined,
      title: 'title' in task ? task.title?.slice(0, 50) : undefined,
      hasDescription: 'description' in task ? !!task.description : undefined,
      initiativeIdentifier: 'identifier' in managedInitiative ? managedInitiative.identifier : undefined
    }
  });
};

/**
 * Log task DELETE operation
 */
export const logTaskDeleteStarted = (
  task: ManagedTaskModel,
  managedInitiative: ManagedInitiativeModel
): void => {
  Sentry.addBreadcrumb({
    category: 'suggestions_save.entity',
    message: 'Task DELETE started',
    level: 'info',
    data: {
      action: 'DELETE',
      entityType: 'task',
      identifier: 'identifier' in task ? task.identifier : undefined,
      initiativeIdentifier: 'identifier' in managedInitiative ? managedInitiative.identifier : undefined
    }
  });
};