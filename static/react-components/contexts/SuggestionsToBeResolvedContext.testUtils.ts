import React from 'react';

import { renderHook } from '@testing-library/react';

import { ManagedEntityAction } from '#types';
import {
  SuggestionsToBeResolvedContextProvider,
  useSuggestionsToBeResolved
} from './SuggestionsToBeResolvedContext';
import { useSuggestedImprovements } from '#hooks/diffs/useSuggestedImprovements';
import { useTasksContext } from '#contexts/TasksContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';

// Mock setup functions
export function setupDefaultMocks() {
  // Default mock for TasksContext
  (useTasksContext as any).mockReturnValue({
    tasks: []
  });

  // Default mock for InitiativesContext
  (useInitiativesContext as any).mockReturnValue({
    initiativesData: []
  });
}

export function setupEmptyImprovements() {
  (useSuggestedImprovements as any).mockReturnValue({
    initiativeImprovements: {},
    taskImprovements: {}
  });
}

export function setupTasksContextWith(tasks: any[]) {
  (useTasksContext as any).mockReturnValue({ tasks });
}

export function setupInitiativesContextWith(initiativesData: any[]) {
  (useInitiativesContext as any).mockReturnValue({ initiativesData });
}

export function setupInitiativeImprovement(identifier: string, improvement: any) {
  (useSuggestedImprovements as any).mockReturnValue({
    initiativeImprovements: {
      [identifier]: improvement
    },
    taskImprovements: {}
  });
}

export function setupTaskImprovement(identifier: string, improvement: any) {
  (useSuggestedImprovements as any).mockReturnValue({
    initiativeImprovements: {},
    taskImprovements: {
      [identifier]: improvement
    }
  });
}

export function setupMixedImprovements(initiativeImprovements: any, taskImprovements: any) {
  (useSuggestedImprovements as any).mockReturnValue({
    initiativeImprovements,
    taskImprovements
  });
}

// Common test wrapper
export function createWrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(
    SuggestionsToBeResolvedContextProvider,
    null,
    children
  );
}

// Render hook with wrapper
export function renderSuggestionsHook() {
  return renderHook(() => useSuggestionsToBeResolved(), { wrapper: createWrapper });
}

// Common test data factories
export const testInitiativeData = {
  createInitiative: {
    action: ManagedEntityAction.CREATE,
    title: 'New Initiative',
    description: 'A new initiative to create',
    workspace_identifier: 'workspace-1'
  },
  deleteInitiative: {
    action: ManagedEntityAction.DELETE,
    identifier: 'INIT-123'
  },
  updateInitiative: {
    action: ManagedEntityAction.UPDATE,
    identifier: 'INIT-123',
    title: 'Updated Initiative Title',
    description: 'Updated description content'
  },
  updateInitiativeWithTitleOnly: {
    action: ManagedEntityAction.UPDATE,
    identifier: 'INIT-456',
    title: 'Only Title Updated'
  },
  updateInitiativeWithDescriptionOnly: {
    action: ManagedEntityAction.UPDATE,
    identifier: 'INIT-789',
    description: 'Only Description Updated'
  }
};

export const testTaskData = {
  createTask: {
    action: ManagedEntityAction.CREATE,
    title: 'New Task for Initiative',
    description: 'Task description',
    initiative_identifier: 'INIT-123'
  },
  createTaskWithoutInitiative: {
    action: ManagedEntityAction.CREATE,
    title: 'New Task',
    description: 'Task description',
    initiative_identifier: null
  },
  updateTask: {
    action: ManagedEntityAction.UPDATE,
    identifier: 'TASK-456',
    title: 'Updated Task Title',
    description: 'Updated description'
  },
  deleteTask: {
    action: ManagedEntityAction.DELETE,
    identifier: 'TASK-456'
  }
};

export const testContextData = {
  existingInitiative: {
    id: 'uuid-123',
    identifier: 'INIT-123',
    title: 'Original Initiative Title',
    description: 'Original initiative description'
  },
  existingTask: {
    id: 'uuid-task-456',
    identifier: 'TASK-456',
    initiative_id: 'INIT-123',
    title: 'Current Task Title in Context',
    description: 'Current task description in context'
  }
};

// Common assertion helpers
export function expectSuggestionStructure(suggestion: any, expectedPath: string, expectedType: 'entity' | 'field') {
  expect(suggestion.path).toBe(expectedPath);
  expect(suggestion.type).toBe(expectedType);
}

export function expectFieldSuggestionStructure(suggestion: any, expectedPath: string, fieldName: string, suggestedValue: any, entityIdentifier: string) {
  expectSuggestionStructure(suggestion, expectedPath, 'field');
  expect(suggestion.fieldName).toBe(fieldName);
  expect(suggestion.suggestedValue).toBe(suggestedValue);
  expect(suggestion.entityIdentifier).toBe(entityIdentifier);
}

export function expectEntitySuggestionStructure(suggestion: any, expectedPath: string, action: ManagedEntityAction, entityIdentifier: string) {
  expectSuggestionStructure(suggestion, expectedPath, 'entity');
  expect(suggestion.action).toBe(action);
  expect(suggestion.entityIdentifier).toBe(entityIdentifier);
}

export function expectResolutionState(resolutionState: any, isResolved: boolean, isAccepted: boolean, resolvedValue?: any) {
  expect(resolutionState?.isResolved).toBe(isResolved);
  expect(resolutionState?.isAccepted).toBe(isAccepted);
  if (resolvedValue !== undefined) {
    if (resolvedValue === null) {
      // Allow both null and undefined for rejected values
      expect(resolutionState?.resolvedValue == null).toBe(true);
    } else {
      expect(resolutionState?.resolvedValue).toEqual(resolvedValue);
    }
  }
}