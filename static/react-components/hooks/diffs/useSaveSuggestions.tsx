import React, { useCallback, useState } from 'react';

import { useSuggestionsToBeResolvedContext } from '#contexts/SuggestionsToBeResolvedContext';
import { ManagedInitiativeModel, ManagedEntityAction } from '#types';
import { useTasksContext } from '#contexts/TasksContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';
import {
  logSuggestionsNotFullyResolved,
  logSuggestionsSaveStarted,
  logSuggestionsSaveCompleted,
  logSuggestionsSaveError,
  logEntityResolutionAttempt,
  logEntityResolutionFailure,
  logEntityResolutionSuccess,
  logInitiativeCreateStarted,
  logInitiativeUpdateStarted,
  logInitiativeDeleteStarted,
  logTaskCreateStarted,
  logTaskUpdateStarted,
  logTaskDeleteStarted
} from './useSaveSuggestionsAnalytics';


export interface useSaveSuggestionsReturn {
  saveSuggestions: () => Promise<void>;
  isSaving: boolean;
}


export const useSaveSuggestions = (): useSaveSuggestionsReturn => {
  const { isFullyResolved, getAcceptedChanges } = useSuggestionsToBeResolvedContext();
  const { createInitiative, updateInitiative, deleteInitiative, initiativesData } = useInitiativesContext();
  const { createTask, updateTask, deleteTask, tasks } = useTasksContext();
  const { jobResult, markJobAsResolved } = useAiImprovementsContext();
  const [isSaving, setIsSaving] = useState(false);

  const saveSuggestions = useCallback(async () => {
    setIsSaving(true);
    // Declare variables outside try block for error context access
    let acceptedChanges: ManagedInitiativeModel[] = [];
    let initiativeIdentifierToId = new Map<string, string>();
    let taskIdentifierToId = new Map<string, string>();

    try {
      if (!isFullyResolved()) {
        logSuggestionsNotFullyResolved();
        throw new Error('Suggestions are not fully resolved');
      }

      acceptedChanges = getAcceptedChanges();

      logSuggestionsSaveStarted(acceptedChanges, !!jobResult?.id);

      // Build initiative identifier-to-id lookup map
      if (initiativesData) {
        for (const initiative of initiativesData) {
          initiativeIdentifierToId.set(initiative.identifier, initiative.id);
        }
      }

      // Build task identifier-to-id lookup map
      if (tasks) {
        for (const task of tasks) {
          taskIdentifierToId.set(task.identifier, task.id);
        }
      }

      /**
       * Helper function to resolve identifier to id for UPDATE/DELETE operations
       * @param {string} identifier - The entity identifier (e.g., "INIT-123")
       * @param {Map<string, string>} lookupMap - Map from identifier to id
       * @param {string} entityType - Type of entity for error reporting
       * @returns {string} The entity id (UUID)
       * @throws {Error} If identifier cannot be resolved
       */
      const resolveEntityId = (identifier: string, lookupMap: Map<string, string>, entityType: string): string => {
        const availableIds = Array.from(lookupMap.keys());
        logEntityResolutionAttempt(identifier, entityType, availableIds, lookupMap.size);

        const id = lookupMap.get(identifier);
        if (!id) {
          logEntityResolutionFailure(identifier, entityType, availableIds);
          throw new Error(`Cannot find ${entityType} with identifier "${identifier}". Entity may not exist or may not be loaded.`);
        }

        logEntityResolutionSuccess(identifier, entityType, id);
        return id;
      };

      // Process each initiative and its tasks
      for (const managedInitiative of acceptedChanges) {

        // Process initiative actions
        if (managedInitiative.action === ManagedEntityAction.CREATE) {
          logInitiativeCreateStarted(managedInitiative);

          // For CREATE: include tasks in initiative payload - API handles task creation automatically
          const { action, tasks: managedTasks, ...initiativeData } = managedInitiative;

          // Clean up initiative data (convert null values to undefined)
          const cleanedInitiativeData = Object.fromEntries(
            Object.entries(initiativeData).map(([key, value]) => [key, value === null ? undefined : value])
          );

          // Clean up tasks data if present (remove action and convert null to undefined)
          const cleanedTasks = managedTasks?.map(task => {
            const { action, ...taskData } = task;
            return Object.fromEntries(
              Object.entries(taskData).map(([key, value]) => [key, value === null ? undefined : value])
            );
          });

          console.log('[useSaveSuggestions] createInitiative', managedInitiative.title.slice(0, 20));
          await createInitiative({
            ...cleanedInitiativeData,
            ...(cleanedTasks && { tasks: cleanedTasks })
          });

        } else if (managedInitiative.action === ManagedEntityAction.UPDATE) {
          logInitiativeUpdateStarted(managedInitiative);

          // For UPDATE: handle initiative and tasks separately
          const { action, tasks: managedTasks, ...initiativeData } = managedInitiative;

          // Resolve identifier to id for UPDATE operation
          const initiativeId = resolveEntityId(managedInitiative.identifier, initiativeIdentifierToId, 'initiative');

          // Convert null values to undefined for the API and add the resolved ID
          const cleanedData = Object.fromEntries(
            Object.entries({ ...initiativeData, id: initiativeId }).map(([key, value]) => [key, value === null ? undefined : value])
          );

          console.log('[useSaveSuggestions] updateInitiative', managedInitiative.identifier);
          if (cleanedData.title || cleanedData.description) {
            await updateInitiative(cleanedData);
          }

          // Process task operations separately for UPDATE initiatives
          if (managedTasks) {
            for (const task of managedTasks) {
              if (task.action === ManagedEntityAction.CREATE) {
                logTaskCreateStarted(task, managedInitiative);

                const { action, ...taskData } = task;

                // Start with the base task data
                let cleanedTaskData: any = { ...taskData };

                // Resolve initiative_identifier to initiative_id if present
                cleanedTaskData.initiative_id = initiativeId;
                // Remove initiative_identifier since we've resolved it to initiative_id
                delete cleanedTaskData.initiative_identifier;

                // Convert null values to undefined for the API
                const finalTaskData = Object.fromEntries(
                  Object.entries(cleanedTaskData).map(([key, value]) => [key, value === null ? undefined : value])
                );

                console.log('[useSaveSuggestions] createTask', finalTaskData);
                await createTask(finalTaskData);
              } else if (task.action === ManagedEntityAction.UPDATE) {
                logTaskUpdateStarted(task, managedInitiative);

                const { action, ...taskData } = task;

                // Resolve identifier to id for UPDATE operation
                const taskId = resolveEntityId(task.identifier, taskIdentifierToId, 'task');

                // Convert null values to undefined for the API and add the resolved ID
                const cleanedTaskData = Object.fromEntries(
                  Object.entries({ ...taskData, id: taskId }).map(([key, value]) => [key, value === null ? undefined : value])
                );

                console.log('[useSaveSuggestions] updateTask', task.identifier);
                await updateTask(cleanedTaskData);
              } else if (task.action === ManagedEntityAction.DELETE) {
                logTaskDeleteStarted(task, managedInitiative);

                // Resolve identifier to id for DELETE operation
                const taskId = resolveEntityId(task.identifier, taskIdentifierToId, 'task');

                console.log('[useSaveSuggestions] deleteTask', task.identifier);
                await deleteTask(taskId);
              }
            }
          }
        } else if (managedInitiative.action === ManagedEntityAction.DELETE) {
          logInitiativeDeleteStarted(managedInitiative);

          // Resolve identifier to id for DELETE operation
          const initiativeId = resolveEntityId(managedInitiative.identifier, initiativeIdentifierToId, 'initiative');

          console.log('[useSaveSuggestions] deleteInitiative', managedInitiative.identifier);
          await deleteInitiative(initiativeId);
        }
      }

      if (jobResult?.id) {
        console.log('[useSaveSuggestions] Job marked as resolved', jobResult.id);
        markJobAsResolved(jobResult.id);
      }

      logSuggestionsSaveCompleted(acceptedChanges.length, !!jobResult?.id);

    } catch (error) {
      logSuggestionsSaveError(
        error,
        initiativesData?.length || 0,
        tasks?.length || 0,
        !!jobResult?.id
      );

      // Re-throw the error to maintain the hook's error handling behavior
      throw error;
    } finally {
      setIsSaving(false);
    }

  }, [getAcceptedChanges, isFullyResolved, createInitiative, updateInitiative, deleteInitiative, createTask, updateTask, deleteTask, jobResult, markJobAsResolved, initiativesData, tasks]);

  return {
    saveSuggestions,
    isSaving
  }
};
