import { useMemo } from 'react';
import { useSuggestedImprovements } from '#hooks/diffs/useSuggestedImprovements';
import { useTasksContext } from '#contexts/TasksContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { ManagedEntityAction, ManagedTaskModel } from '#types';

// Re-export types from context for convenience
export interface UnifiedSuggestion {
  /** Unique path identifier for this suggestion */
  path: string;
  /** Type of suggestion */
  type: 'field' | 'entity';
  /** Entity action */
  action: ManagedEntityAction;
  /** Original value (for field changes) */
  originalValue?: any;
  /** Suggested value */
  suggestedValue: any;
  /** Initiative identifier */
  entityIdentifier: string;
  /** Field name for field-level changes ('title', 'description', 'tasks') */
  fieldName?: string;
}

/**
 * Helper function to process embedded tasks into individual entity and field suggestions.
 * Creates granular suggestions for each task within an initiative.
 * 
 * @param tasks Array of ManagedTaskModel from initiative
 * @param initiativeId The parent initiative identifier  
 * @param action The action for this initiative (CREATE or UPDATE)
 * @param tasksData Array of current tasks from TasksContext for originalValue lookup
 * @returns Record of path-keyed suggestions for individual tasks
 */
function processEmbeddedTasks(
  tasks: ManagedTaskModel[],
  initiativeId: string,
  tasksData?: any[]
): Record<string, UnifiedSuggestion> {
  const result: Record<string, UnifiedSuggestion> = {};

  /**
   * Helper function to find the original value for a task field from TasksContext
   * @param {string} identifier - The task identifier to look up
   * @param {string} fieldName - The field name ('title' or 'description')
   * @returns {any} The original value or undefined if not found
   */
  const findTaskOriginalValue = (identifier: string, fieldName: string): any => {
    const task = tasksData?.find(t => t.identifier === identifier);
    return task ? (task as any)[fieldName] : undefined;
  };

  tasks.forEach((task, index) => {
    // Determine task identifier
    const taskIdentifier = (task as any).identifier || `new-task-${index}`;
    const taskBasePath = `initiative.${initiativeId}.tasks.${taskIdentifier}`;

    // Create entity-level suggestion for the task
    result[taskBasePath] = {
      path: taskBasePath,
      type: 'entity',
      action: task.action,
      originalValue: tasksData?.find(t => t.identifier === taskIdentifier),
      suggestedValue: task,
      entityIdentifier: initiativeId // Initiative remains the main entity
    };

    if (task.action === ManagedEntityAction.DELETE) {
      return
    }

    // Create field-level suggestions for task fields
    if ((task as any).title !== undefined && (task as any).title !== null) {
      const originalTitleValue = task.action === ManagedEntityAction.UPDATE && (task as any).identifier
        ? findTaskOriginalValue((task as any).identifier, 'title')
        : undefined;

      result[`${taskBasePath}.title`] = {
        path: `${taskBasePath}.title`,
        type: 'field',
        action: task.action,
        originalValue: originalTitleValue,
        suggestedValue: (task as any).title,
        entityIdentifier: initiativeId,
        fieldName: 'title'
      };
    }

    if ((task as any).description !== undefined && (task as any).description !== null) {
      const originalDescriptionValue = task.action === ManagedEntityAction.UPDATE && (task as any).identifier
        ? findTaskOriginalValue((task as any).identifier, 'description')
        : undefined;

      result[`${taskBasePath}.description`] = {
        path: `${taskBasePath}.description`,
        type: 'field',
        action: task.action,
        originalValue: originalDescriptionValue,
        suggestedValue: (task as any).description,
        entityIdentifier: initiativeId,
        fieldName: 'description'
      };
    }
  });

  return result;
}

/**
 * Hook that transforms raw AI improvements into unified suggestions with path-based keys.
 * Normalizes both initiative and task improvements into initiative-centric suggestions.
 * 
 * @returns {Record<string, UnifiedSuggestion>} Map of path-keyed unified suggestions
 */
export function useUnifiedSuggestions(): Record<string, UnifiedSuggestion> {
  const { initiativeImprovements, taskImprovements } = useSuggestedImprovements();
  const { tasks } = useTasksContext();
  const { initiativesData } = useInitiativesContext();

  return useMemo(() => {
    const result: Record<string, UnifiedSuggestion> = {};

    /**
     * Helper function to find the original value for a field from InitiativesContext
     * @param {string} identifier - The initiative identifier to look up
     * @param {string} fieldName - The field name ('title' or 'description')
     * @returns {any} The original value or undefined if not found
     */
    const findInitiativeOriginalValue = (identifier: string, fieldName: string): any => {
      const initiative = initiativesData?.find(i => i.identifier === identifier);
      return initiative ? (initiative as any)[fieldName] : undefined;
    };

    // Process initiative improvements
    Object.entries(initiativeImprovements).forEach(([key, improvement]) => {
      const basePath = `initiative.${key}`;

      if (improvement.action === ManagedEntityAction.CREATE) {
        // New initiative creation - entity-level suggestion
        const createImprovement = improvement as any;

        result[basePath] = {
          path: basePath,
          type: 'entity',
          action: ManagedEntityAction.CREATE,
          suggestedValue: improvement,
          entityIdentifier: key
        };

        // Process embedded tasks if present
        if (createImprovement.tasks && Array.isArray(createImprovement.tasks) && createImprovement.tasks.length > 0) {
          const embeddedTaskSuggestions = processEmbeddedTasks(
            createImprovement.tasks,
            key,
            tasks
          );
          Object.assign(result, embeddedTaskSuggestions);
        }
      } else if (improvement.action === ManagedEntityAction.UPDATE) {
        // Initiative update - create both entity-level and field-level suggestions
        const updateImprovement = improvement as any; // TODO: Proper typing needed

        // Create entity-level suggestion
        result[basePath] = {
          path: basePath,
          type: 'entity',
          action: ManagedEntityAction.UPDATE,
          suggestedValue: improvement,
          originalValue: initiativesData?.find(i => i.identifier === key),
          entityIdentifier: key
        };

        // Create field-level suggestions for title and description
        if (updateImprovement.title !== undefined && updateImprovement.title !== null) {
          result[`${basePath}.title`] = {
            path: `${basePath}.title`,
            type: 'field',
            action: ManagedEntityAction.UPDATE,
            originalValue: findInitiativeOriginalValue(key, 'title'),
            suggestedValue: updateImprovement.title,
            entityIdentifier: key,
            fieldName: 'title'
          };
        }

        if (updateImprovement.description !== undefined && updateImprovement.description !== null) {
          result[`${basePath}.description`] = {
            path: `${basePath}.description`,
            type: 'field',
            action: ManagedEntityAction.UPDATE,
            originalValue: findInitiativeOriginalValue(key, 'description'),
            suggestedValue: updateImprovement.description,
            entityIdentifier: key,
            fieldName: 'description'
          };
        }

        // Process embedded tasks if present
        if (updateImprovement.tasks && Array.isArray(updateImprovement.tasks) && updateImprovement.tasks.length > 0) {
          const embeddedTaskSuggestions = processEmbeddedTasks(
            updateImprovement.tasks,
            key,
            tasks
          );
          Object.assign(result, embeddedTaskSuggestions);
        }

      } else if (improvement.action === ManagedEntityAction.DELETE) {
        // Initiative deletion - entity-level suggestion
        result[basePath] = {
          path: basePath,
          type: 'entity',
          action: ManagedEntityAction.DELETE,
          suggestedValue: improvement,
          originalValue: initiativesData?.find(i => i.identifier === key),
          entityIdentifier: key
        };
      }
    });

    // Process task improvements - normalize into initiative updates
    const tasksByInitiative: Record<string, { tasks: ManagedTaskModel[], taskKeys: string[] }> = {};
    let newInitiativeCounter = 0;

    Object.entries(taskImprovements).forEach(([taskKey, taskImprovement]) => {
      let targetInitiativeId: string;

      if (taskImprovement.action === ManagedEntityAction.CREATE) {
        // For CREATE tasks, use initiative_identifier or generate new one
        const createTask = taskImprovement as any;
        if (createTask.initiative_identifier) {
          // Validate the initiative exists in InitiativesContext
          const existingInitiative = initiativesData?.find(i => i.identifier === createTask.initiative_identifier);
          if (existingInitiative) {
            targetInitiativeId = createTask.initiative_identifier;
          } else {
            throw new Error(`Initiative ${createTask.initiative_identifier} not found in InitiativesContext`);
          }
        } else {
          throw new Error('CREATE task without initiative_identifier');
        }
      } else {
        // For UPDATE/DELETE, find the task in TasksContext
        const updateOrDeleteTask = taskImprovement as any;
        const existingTask = tasks.find(t => t.identifier === updateOrDeleteTask.identifier);
        const existingInitiative = initiativesData?.find(i => i.id === existingTask?.initiative_id);
        if (existingTask && existingInitiative) {
          targetInitiativeId = existingInitiative.identifier;
        } else {
          throw new Error(`Task ${updateOrDeleteTask.identifier} not found in TasksContext`);
        }
      }

      if (!tasksByInitiative[targetInitiativeId]) {
        tasksByInitiative[targetInitiativeId] = {
          tasks: [],
          taskKeys: []
        };
      }
      tasksByInitiative[targetInitiativeId].tasks.push(taskImprovement);
      tasksByInitiative[targetInitiativeId].taskKeys.push(taskKey);
    });

    // Convert aggregated task operations into initiative suggestions
    Object.entries(tasksByInitiative).forEach(([initiativeId, { tasks: taskOperations, taskKeys }]) => {
      const pathSuffix = taskKeys.join(',');
      const basePath = `initiative.${initiativeId}`;

      // Determine if this should be CREATE or UPDATE initiative
      const isNewInitiative = initiativeId.startsWith('new-initiative-');

      const suggestionValue = isNewInitiative ? {
        action: ManagedEntityAction.CREATE,
        title: `New Initiative for ${(taskOperations[0] as any).title || 'tasks'}`,
        description: 'Auto-generated initiative for task operations',
        workspace_identifier: null,
        tasks: taskOperations
      } : {
        action: ManagedEntityAction.UPDATE,
        identifier: initiativeId,
        tasks: taskOperations
      };

      result[basePath] = {
        path: basePath,
        type: 'entity',
        action: isNewInitiative ? ManagedEntityAction.CREATE : ManagedEntityAction.UPDATE,
        suggestedValue: suggestionValue,
        originalValue: initiativesData?.find(i => i.identifier === initiativeId),
        entityIdentifier: initiativeId
      };

      const embeddedTaskSuggestions = processEmbeddedTasks(
        taskOperations,
        initiativeId,
        tasks
      )
      Object.assign(result, embeddedTaskSuggestions);
    });

    return result;
  }, [initiativeImprovements, taskImprovements, tasks, initiativesData]);
}