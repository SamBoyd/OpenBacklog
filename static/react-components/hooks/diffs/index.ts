/**
 * Initiative diff utilities for refactoring diff adapters into smaller, composable pieces.
 * 
 * This module provides pure utilities and hooks for handling initiative suggestions,
 * task operations, and resolution states in a testable, reusable way.
 */

// Pure utilities (no React dependencies)
export { applyTaskOperations } from './applyTaskOperations';
export { buildBasePath } from './basePath';
export {
    groupInitiativeSuggestionsByIdentifier,
    selectEntitySuggestionForBasePath,
    hasTaskSuggestionsUnderPath,
    hasAnySuggestionsUnderPath,
    type InitiativeSuggestionGroup
} from './grouping';
export { deriveUpdatedInitiativeDto, useUpdatedInitiative } from './updatedInitiative';
