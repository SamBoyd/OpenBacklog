import { useState, useCallback } from 'react';
import { ManagedEntityAction, ManagedInitiativeModel, ManagedTaskModel, UpdateTaskModel } from '#types';
import { UnifiedSuggestion } from './useUnifiedSuggestions';

// Re-export types from context for convenience
export interface ResolutionState {
  /** Whether this suggestion has been resolved (accepted or rejected) */
  isResolved: boolean;
  /** Whether the suggestion was accepted (true) or rejected (false) */
  isAccepted: boolean;
  /** The resolved value if accepted, null if rejected or unresolved */
  resolvedValue: any;
}

export type ResolutionMap = Record<string, ResolutionState>;

export interface UseResolutionOperationsReturn {
  /** Resolution state for all paths */
  resolutions: ResolutionMap;
  /** Core resolution operation */
  resolve: (path: string, accepted: boolean, value?: any) => void;
  /** Rollback a specific resolution */
  rollback: (path: string) => void;
  /** Accept all suggestions at path or globally */
  acceptAll: (pathPrefix?: string) => void;
  /** Reject all suggestions at path or globally */
  rejectAll: (pathPrefix?: string) => void;
  /** Rollback all resolutions at path or globally */
  rollbackAll: (pathPrefix?: string) => void;
  /** Get resolution state for a specific path */
  getResolutionState: (path: string) => ResolutionState;
  /** Check if a path or all paths are fully resolved */
  isFullyResolved: (pathPrefix?: string) => boolean;
  /** Get all accepted changes for saving */
  getAcceptedChanges: () => ManagedInitiativeModel[];
}

/**
 * Hook that manages resolution state and operations for path-based suggestions.
 * Provides all resolution operations including bulk accept/reject/rollback functionality.
 * 
 * @param {Record<string, UnifiedSuggestion>} suggestions - Map of suggestions by path
 * @returns {UseResolutionOperationsReturn} Resolution state and operations
 */
export function useResolutionOperations(
  suggestions: Record<string, UnifiedSuggestion>
): UseResolutionOperationsReturn {
  const [resolutions, setResolutions] = useState<ResolutionMap>({});

  // Core resolution operation
  const resolve = useCallback((path: string, accepted: boolean, value?: any) => {
    const newValue = value ?? suggestions[path]?.suggestedValue

    setResolutions(prev => ({
      ...prev,
      [path]: {
        isResolved: true,
        isAccepted: accepted,
        resolvedValue: accepted ? newValue : suggestions[path]?.originalValue
      }
    }));
  }, [suggestions]);

  // Rollback a specific resolution
  const rollback = useCallback((path: string) => {
    setResolutions(prev => {
      const newResolutions = { ...prev };
      delete newResolutions[path];
      return newResolutions;
    });
  }, []);

  // Get resolution state for a specific path
  const getResolutionState = useCallback((path: string): ResolutionState => {
    return resolutions[path] || {
      isResolved: false,
      isAccepted: false,
      resolvedValue: null
    };
  }, [resolutions]);

  /**
   * Validates the pathPrefix parameter to ensure it follows allowed patterns
   */
  const validatePathPrefix = useCallback((pathPrefix?: string): void => {
    if (pathPrefix === undefined) return; // undefined is always valid

    // Check if it's a field-level path (not allowed)
    if (pathPrefix.includes('.title') || pathPrefix.includes('.description')) {
      throw new Error(`Invalid pathPrefix: "${pathPrefix}". Field-level paths are not allowed as prefixes.`);
    }

    // Check if it's a multiple tasks path (not allowed)
    if (pathPrefix.endsWith('.tasks') && !pathPrefix.includes('.tasks.')) {
      throw new Error(`Invalid pathPrefix: "${pathPrefix}". Multiple tasks prefix paths are not allowed.`);
    }

    // Validate that it matches allowed patterns
    const initiativePattern = /^initiative\.[^.]+$/;
    const taskPattern = /^initiative\.[^.]+\.tasks\.[^.]+$/;

    if (!initiativePattern.test(pathPrefix) && !taskPattern.test(pathPrefix)) {
      throw new Error(`Invalid pathPrefix: "${pathPrefix}". Must be initiative entity or task entity path.`);
    }
  }, []);

  /**
   * Identifies the type of path: initiative, task, or undefined (multiple initiatives)
   */
  const identifyPathType = useCallback((pathPrefix?: string): 'initiative' | 'task' | 'multiple' => {
    if (pathPrefix === undefined) return 'multiple';

    const taskPattern = /^initiative\.[^.]+\.tasks\.[^.]+$/;
    if (taskPattern.test(pathPrefix)) return 'task';

    return 'initiative';
  }, []);

  /**
   * Checks if a specific task is resolved (entity accepted OR all fields resolved)
   */
  const isTaskResolved = useCallback((taskPath: string): boolean => {
    const taskEntityPath = taskPath;
    const taskTitlePath = `${taskPath}.title`;
    const taskDescriptionPath = `${taskPath}.description`;

    // Check if task entity-level suggestion exists and is accepted
    const hasEntitySuggestion = !!suggestions[taskEntityPath];
    const entityResolution = resolutions[taskEntityPath];
    if (hasEntitySuggestion && entityResolution?.isResolved === true) {
      return true;
    }

    // Check if all field-level suggestions are resolved
    const fieldPaths = [taskTitlePath, taskDescriptionPath].filter(path => suggestions[path]);
    if (fieldPaths.length > 0) {
      return fieldPaths.every(path => resolutions[path]?.isResolved === true);
    }

    // If only entity suggestion exists, check if it's resolved (accepted or rejected)
    if (hasEntitySuggestion) {
      return resolutions[taskEntityPath]?.isResolved === true;
    }

    // If no suggestions exist for this task, consider it resolved
    return true;
  }, [suggestions, resolutions]);

  /**
   * Checks if a specific initiative is resolved (entity accepted OR (all fields + all tasks) resolved)
   */
  const isInitiativeResolved = useCallback((initiativePath: string): boolean => {
    const initiativeEntityPath = initiativePath;
    const initiativeTitlePath = `${initiativePath}.title`;
    const initiativeDescriptionPath = `${initiativePath}.description`;

    // Check if initiative entity-level suggestion exists and is accepted
    const hasEntitySuggestion = !!suggestions[initiativeEntityPath];
    const entityResolution = resolutions[initiativeEntityPath];
    if (hasEntitySuggestion && entityResolution?.isResolved === true) {
      return true;
    }

    // For non-entity resolution, check if all field-level AND all contained tasks are resolved
    const initiativeFieldPaths = [initiativeTitlePath, initiativeDescriptionPath].filter(path => suggestions[path]);
    const taskPaths = Object.keys(suggestions).filter(path => 
      path.startsWith(`${initiativePath}.tasks.`) && !path.includes('.title') && !path.includes('.description')
    );

    // If we have field suggestions, all must be resolved
    const allFieldsResolved = initiativeFieldPaths.length === 0 || 
      initiativeFieldPaths.every(path => resolutions[path]?.isResolved === true);

    // If we have task suggestions, all must be resolved
    const allTasksResolved = taskPaths.length === 0 || 
      taskPaths.every(taskPath => isTaskResolved(taskPath));

    // Both fields AND tasks must be resolved for non-entity resolution
    if (initiativeFieldPaths.length > 0 || taskPaths.length > 0) {
      return allFieldsResolved && allTasksResolved;
    }

    // If only entity suggestion exists, check if it's resolved (accepted or rejected)
    if (hasEntitySuggestion) {
      return resolutions[initiativeEntityPath]?.isResolved === true;
    }

    // If no suggestions exist for this initiative, consider it resolved
    return true;
  }, [suggestions, resolutions, isTaskResolved]);

  // Check if paths are fully resolved with clear logic for each path type
  const isFullyResolved = useCallback((pathPrefix?: string): boolean => {
    // Validate the pathPrefix
    try {
      validatePathPrefix(pathPrefix);
    } catch (error) {
      console.error('Invalid pathPrefix in isFullyResolved:', error);
      return false;
    }

    // Identify the path type
    const pathType = identifyPathType(pathPrefix);

    // Handle each path type with specific logic
    if (pathType === 'task') {
      // Single task resolution
      return isTaskResolved(pathPrefix!);
    }

    if (pathType === 'initiative') {
      // Single initiative resolution
      return isInitiativeResolved(pathPrefix!);
    }

    if (pathType === 'multiple') {
      // Multiple initiatives - check all initiatives are resolved
      const initiativePaths = new Set<string>();
      
      // Collect all unique initiative paths
      Object.keys(suggestions).forEach(path => {
        const initiativeMatch = path.match(/^initiative\.([^.]+)/);
        if (initiativeMatch) {
          initiativePaths.add(`initiative.${initiativeMatch[1]}`);
        }
      });

      if (initiativePaths.size === 0) return true;

      // Check that all initiatives are resolved
      return Array.from(initiativePaths).every(initiativePath => 
        isInitiativeResolved(initiativePath)
      );
    }

    return false;
  }, [suggestions, resolutions, validatePathPrefix, identifyPathType, isTaskResolved, isInitiativeResolved]);

  // Get all accepted changes for saving - aggregates field-level suggestions into complete models
  const getAcceptedChanges = useCallback((): ManagedInitiativeModel[] => {
    const result: ManagedInitiativeModel[] = [];
    
    // Group suggestions by initiative entity identifier
    const initiativeGroups: Record<string, {
      entitySuggestion?: UnifiedSuggestion;
      entityResolution?: ResolutionState;
      fieldSuggestions: Record<string, UnifiedSuggestion>;
      fieldResolutions: Record<string, ResolutionState>;
      taskEntitySuggestions: Record<string, UnifiedSuggestion>;
      taskEntityResolutions: Record<string, ResolutionState>;
      taskFieldSuggestions: Record<string, Record<string, UnifiedSuggestion>>;
      taskFieldResolutions: Record<string, Record<string, ResolutionState>>;
    }> = {};

    // Organize all suggestions by initiative
    Object.entries(suggestions).forEach(([path, suggestion]) => {
      const initiativeMatch = path.match(/^initiative\.([^.]+)/);
      if (!initiativeMatch) return;
      
      const initiativeId = initiativeMatch[1];
      if (!initiativeGroups[initiativeId]) {
        initiativeGroups[initiativeId] = {
          fieldSuggestions: {},
          fieldResolutions: {},
          taskEntitySuggestions: {},
          taskEntityResolutions: {},
          taskFieldSuggestions: {},
          taskFieldResolutions: {}
        };
      }
      
      const group = initiativeGroups[initiativeId];
      const resolution = resolutions[path];

      // Initiative entity-level suggestion (initiative.X)
      if (path.match(/^initiative\.[^.]+$/)) {
        if (suggestion.type === 'entity') {
          group.entitySuggestion = suggestion;
          group.entityResolution = resolution;
        }
      }
      // Initiative field-level suggestion (initiative.X.field)
      else if (path.match(/^initiative\.[^.]+\.(title|description)$/)) {
        if (suggestion.type === 'field') {
          group.fieldSuggestions[suggestion.fieldName!] = suggestion;
          group.fieldResolutions[suggestion.fieldName!] = resolution;
        }
      }
      // Task entity-level suggestion (initiative.X.tasks.Y)
      else if (path.match(/^initiative\.[^.]+\.tasks\.[^.]+$/)) {
        if (suggestion.type === 'entity') {
          const taskMatch = path.match(/^initiative\.[^.]+\.tasks\.([^.]+)$/);
          if (taskMatch) {
            const taskId = taskMatch[1];
            group.taskEntitySuggestions[taskId] = suggestion;
            group.taskEntityResolutions[taskId] = resolution;
          }
        }
      }
      // Task field-level suggestion (initiative.X.tasks.Y.field)
      else if (path.match(/^initiative\.[^.]+\.tasks\.[^.]+\.(title|description)$/)) {
        if (suggestion.type === 'field') {
          const taskMatch = path.match(/^initiative\.[^.]+\.tasks\.([^.]+)\./);
          if (taskMatch) {
            const taskId = taskMatch[1];
            if (!group.taskFieldSuggestions[taskId]) {
              group.taskFieldSuggestions[taskId] = {};
              group.taskFieldResolutions[taskId] = {};
            }
            group.taskFieldSuggestions[taskId][suggestion.fieldName!] = suggestion;
            group.taskFieldResolutions[taskId][suggestion.fieldName!] = resolution;
          }
        }
      }
    });

    // Process each initiative group
    Object.entries(initiativeGroups).forEach(([initiativeId, group]) => {
      // Priority 1: If entity-level suggestion exists and is accepted, use it
      if (group.entitySuggestion && group.entityResolution?.isAccepted) {
        result.push(group.entityResolution.resolvedValue);
        return;
      }

      // Priority 2: Aggregate field-level and task suggestions
      const hasAcceptedFields = Object.entries(group.fieldResolutions).some(([_, res]) => res?.isAccepted);
      const hasAcceptedTasks = Object.keys(group.taskEntitySuggestions).some(taskId => 
        group.taskEntityResolutions[taskId]?.isAccepted
      ) || Object.keys(group.taskFieldSuggestions).some(taskId =>
        Object.values(group.taskFieldResolutions[taskId] || {}).some(res => res?.isAccepted)
      );

      // Only create aggregated model if we have at least one accepted suggestion
      if (hasAcceptedFields || hasAcceptedTasks) {
        const aggregatedModel: any = {
          action: 'UPDATE',
          identifier: initiativeId
        };

        // Add accepted initiative fields
        Object.entries(group.fieldResolutions).forEach(([fieldName, resolution]) => {
          if (resolution?.isAccepted) {
            aggregatedModel[fieldName] = resolution.resolvedValue;
          }
        });

        // Add accepted tasks
        const acceptedTasks: ManagedTaskModel[] = [];
        
        // Process task entity suggestions
        Object.entries(group.taskEntityResolutions).forEach(([taskId, resolution]) => {
          if (resolution?.isAccepted) {
            acceptedTasks.push(resolution.resolvedValue);
          }
        });

        // Process task field suggestions (group by task)
        Object.entries(group.taskFieldSuggestions).forEach(([taskId, taskFields]) => {
          const taskFieldResolutions = group.taskFieldResolutions[taskId] || {};
          const acceptedTaskFields: Record<string, any> = {};
          let hasAcceptedTaskField = false;

          Object.entries(taskFields).forEach(([fieldName, suggestion]) => {
            const resolution = taskFieldResolutions[fieldName];
            if (resolution?.isAccepted) {
              acceptedTaskFields[fieldName] = resolution.resolvedValue;
              hasAcceptedTaskField = true;
            }
          });

          if (hasAcceptedTaskField) {
            acceptedTasks.push({
              action: ManagedEntityAction.UPDATE,
              identifier: taskId,
              ...acceptedTaskFields
            } as UpdateTaskModel);
          }
        });

        if (acceptedTasks.length > 0) {
          aggregatedModel.tasks = acceptedTasks;
        }

        result.push(aggregatedModel);
      }
    });

    return result;
  }, [resolutions, suggestions]);

  // Bulk operations
  const acceptAll = useCallback((pathPrefix?: string) => {
    const relevantPaths = pathPrefix
      ? Object.keys(suggestions).filter(path => path.startsWith(pathPrefix))
      : Object.keys(suggestions);

    setResolutions(prev => {
      const newResolutions = { ...prev };
      relevantPaths.forEach(path => {
        newResolutions[path] = {
          isResolved: true,
          isAccepted: true,
          resolvedValue: suggestions[path]?.suggestedValue || null
        };
      });
      return newResolutions;
    });
  }, [suggestions]);

  const rejectAll = useCallback((pathPrefix?: string) => {
    const relevantPaths = pathPrefix
      ? Object.keys(suggestions).filter(path => path.startsWith(pathPrefix))
      : Object.keys(suggestions);

    setResolutions(prev => {
      const newResolutions = { ...prev };
      relevantPaths.forEach(path => {
        newResolutions[path] = {
          isResolved: true,
          isAccepted: false,
          resolvedValue: null
        };
      });
      return newResolutions;
    });
  }, [suggestions]);

  const rollbackAll = useCallback((pathPrefix?: string) => {
    const relevantPaths = pathPrefix
      ? Object.keys(suggestions).filter(path => path.startsWith(pathPrefix))
      : Object.keys(suggestions);

    setResolutions(prev => {
      const newResolutions = { ...prev };
      relevantPaths.forEach(path => {
        delete newResolutions[path];
      });
      return newResolutions;
    });
  }, [suggestions]);

  return {
    resolutions,
    resolve,
    rollback,
    acceptAll,
    rejectAll,
    rollbackAll,
    getResolutionState,
    isFullyResolved,
    getAcceptedChanges
  };
}