import { describe, it, expect } from 'vitest';
import {
    groupInitiativeSuggestionsByIdentifier,
    selectEntitySuggestionForBasePath,
    hasTaskSuggestionsUnderPath,
    hasAnySuggestionsUnderPath,
} from './grouping';

describe('grouping utilities', () => {
    const mockSuggestions = [
        {
            path: 'initiative.INIT-123',
            type: 'entity',
            action: 'UPDATE',
            suggestedValue: { title: 'Updated Initiative' }
        },
        {
            path: 'initiative.INIT-123.title',
            type: 'field',
            fieldName: 'title',
            suggestedValue: 'New Title'
        },
        {
            path: 'initiative.INIT-123.description',
            type: 'field',
            fieldName: 'description',
            suggestedValue: 'New Description'
        },
        {
            path: 'initiative.INIT-123.tasks.TASK-1',
            type: 'entity',
            action: 'CREATE',
            suggestedValue: { title: 'New Task' }
        },
        {
            path: 'initiative.INIT-123.tasks.TASK-1.title',
            type: 'field',
            fieldName: 'title',
            suggestedValue: 'Task Title'
        },
        {
            path: 'initiative.INIT-456',
            type: 'entity',
            action: 'DELETE'
        },
        {
            path: 'initiative.INIT-456.tasks.TASK-2',
            type: 'entity',
            action: 'UPDATE',
            suggestedValue: { description: 'Updated Task' }
        },
        {
            path: 'non-initiative.path',
            type: 'entity',
            action: 'CREATE'
        }
    ];

    describe('groupInitiativeSuggestionsByIdentifier', () => {
        it('should group suggestions by initiative identifier', () => {
            const result = groupInitiativeSuggestionsByIdentifier(mockSuggestions);

            expect(Object.keys(result)).toEqual(['INIT-123', 'INIT-456']);
            expect(result['INIT-123'].identifier).toBe('INIT-123');
            expect(result['INIT-456'].identifier).toBe('INIT-456');
        });

        it('should separate entity suggestions correctly', () => {
            const result = groupInitiativeSuggestionsByIdentifier(mockSuggestions);

            expect(result['INIT-123'].entitySuggestion).toEqual({
                path: 'initiative.INIT-123',
                type: 'entity',
                action: 'UPDATE',
                suggestedValue: { title: 'Updated Initiative' }
            });

            expect(result['INIT-456'].entitySuggestion).toEqual({
                path: 'initiative.INIT-456',
                type: 'entity',
                action: 'DELETE'
            });
        });

        it('should separate field suggestions correctly', () => {
            const result = groupInitiativeSuggestionsByIdentifier(mockSuggestions);

            expect(result['INIT-123'].fieldSuggestions).toEqual({
                title: {
                    path: 'initiative.INIT-123.title',
                    type: 'field',
                    fieldName: 'title',
                    suggestedValue: 'New Title'
                },
                description: {
                    path: 'initiative.INIT-123.description',
                    type: 'field',
                    fieldName: 'description',
                    suggestedValue: 'New Description'
                }
            });

            expect(result['INIT-456'].fieldSuggestions).toEqual({});
        });

        it('should separate task suggestions correctly', () => {
            const result = groupInitiativeSuggestionsByIdentifier(mockSuggestions);

            expect(result['INIT-123'].taskSuggestions).toEqual({
                'TASK-1': {
                    path: 'initiative.INIT-123.tasks.TASK-1',
                    type: 'entity',
                    action: 'CREATE',
                    suggestedValue: { title: 'New Task' }
                },
                'TASK-1.title': {
                    path: 'initiative.INIT-123.tasks.TASK-1.title',
                    type: 'field',
                    fieldName: 'title',
                    suggestedValue: 'Task Title'
                }
            });

            expect(result['INIT-456'].taskSuggestions).toEqual({
                'TASK-2': {
                    path: 'initiative.INIT-456.tasks.TASK-2',
                    type: 'entity',
                    action: 'UPDATE',
                    suggestedValue: { description: 'Updated Task' }
                }
            });
        });

        it('should skip non-initiative suggestions', () => {
            const result = groupInitiativeSuggestionsByIdentifier(mockSuggestions);

            expect(Object.keys(result)).not.toContain('non-initiative');
        });

        it('should handle empty suggestions array', () => {
            const result = groupInitiativeSuggestionsByIdentifier([]);

            expect(result).toEqual({});
        });

        it('should handle undefined/null suggestions', () => {
            expect(() => groupInitiativeSuggestionsByIdentifier(undefined as any)).not.toThrow();
            expect(() => groupInitiativeSuggestionsByIdentifier(null as any)).not.toThrow();
            expect(groupInitiativeSuggestionsByIdentifier(undefined as any)).toEqual({});
            expect(groupInitiativeSuggestionsByIdentifier(null as any)).toEqual({});
        });

        it('should skip invalid paths', () => {
            const invalidSuggestions = [
                { path: 'initiative', type: 'entity' }, // Missing identifier
                { path: 'initiative.', type: 'entity' }, // Empty identifier
                { path: 'initiative..invalid', type: 'entity' } // Double dot
            ];

            const result = groupInitiativeSuggestionsByIdentifier(invalidSuggestions);

            expect(Object.keys(result)).toHaveLength(0);
        });

        it('should handle field suggestions without fieldName', () => {
            const suggestions = [
                { path: 'initiative.INIT-123', type: 'entity' },
                { path: 'initiative.INIT-123.title', type: 'field' } // Missing fieldName
            ];

            const result = groupInitiativeSuggestionsByIdentifier(suggestions);

            expect(result['INIT-123'].fieldSuggestions).toEqual({});
        });

        it('should initialize all required properties', () => {
            const suggestions = [
                { path: 'initiative.INIT-789', type: 'entity' }
            ];

            const result = groupInitiativeSuggestionsByIdentifier(suggestions);

            expect(result['INIT-789']).toEqual({
                entitySuggestion: { path: 'initiative.INIT-789', type: 'entity' },
                fieldSuggestions: {},
                taskSuggestions: {},
                identifier: 'INIT-789'
            });
        });
    });

    describe('selectEntitySuggestionForBasePath', () => {
        it('should return entity suggestion for valid base path', () => {
            const result = selectEntitySuggestionForBasePath(mockSuggestions, 'initiative.INIT-123');

            expect(result).toEqual({
                path: 'initiative.INIT-123',
                type: 'entity',
                action: 'UPDATE',
                suggestedValue: { title: 'Updated Initiative' }
            });
        });

        it('should return undefined for non-entity suggestion at base path', () => {
            const result = selectEntitySuggestionForBasePath(mockSuggestions, 'initiative.INIT-123.title');

            expect(result).toBeUndefined();
        });

        it('should return undefined for non-existent base path', () => {
            const result = selectEntitySuggestionForBasePath(mockSuggestions, 'initiative.NOT-FOUND');

            expect(result).toBeUndefined();
        });

        it('should return undefined for empty base path', () => {
            const result = selectEntitySuggestionForBasePath(mockSuggestions, '');

            expect(result).toBeUndefined();
        });

        it('should return undefined for null/undefined inputs', () => {
            expect(selectEntitySuggestionForBasePath(null as any, 'initiative.INIT-123')).toBeUndefined();
            expect(selectEntitySuggestionForBasePath(mockSuggestions, null as any)).toBeUndefined();
            expect(selectEntitySuggestionForBasePath(undefined as any, undefined as any)).toBeUndefined();
        });

        it('should handle suggestions without type property', () => {
            const suggestions = [
                { path: 'initiative.INIT-123', action: 'UPDATE' } // Missing type
            ];

            const result = selectEntitySuggestionForBasePath(suggestions, 'initiative.INIT-123');

            expect(result).toBeUndefined();
        });
    });

    describe('hasTaskSuggestionsUnderPath', () => {
        it('should return true when task suggestions exist under path', () => {
            const result = hasTaskSuggestionsUnderPath(mockSuggestions, 'initiative.INIT-123');

            expect(result).toBe(true);
        });

        it('should return false when no task suggestions exist under path', () => {
            const suggestionsWithoutTasks = [
                { path: 'initiative.INIT-123', type: 'entity' },
                { path: 'initiative.INIT-123.title', type: 'field' }
            ];

            const result = hasTaskSuggestionsUnderPath(suggestionsWithoutTasks, 'initiative.INIT-123');

            expect(result).toBe(false);
        });

        it('should return false for non-existent base path', () => {
            const result = hasTaskSuggestionsUnderPath(mockSuggestions, 'initiative.NOT-FOUND');

            expect(result).toBe(false);
        });

        it('should return false for empty base path', () => {
            const result = hasTaskSuggestionsUnderPath(mockSuggestions, '');

            expect(result).toBe(false);
        });

        it('should return false for null/undefined inputs', () => {
            expect(hasTaskSuggestionsUnderPath(null as any, 'initiative.INIT-123')).toBe(false);
            expect(hasTaskSuggestionsUnderPath(mockSuggestions, null as any)).toBe(false);
            expect(hasTaskSuggestionsUnderPath(undefined as any, undefined as any)).toBe(false);
        });

        it('should handle deeply nested task paths', () => {
            const suggestions = [
                { path: 'initiative.INIT-123.tasks.TASK-1.checklist.item-1', type: 'field' }
            ];

            const result = hasTaskSuggestionsUnderPath(suggestions, 'initiative.INIT-123');

            expect(result).toBe(true);
        });
    });

    describe('hasAnySuggestionsUnderPath', () => {
        it('should return true when suggestions exist at the exact path', () => {
            const result = hasAnySuggestionsUnderPath(mockSuggestions, 'initiative.INIT-123');

            expect(result).toBe(true);
        });

        it('should return true when suggestions exist under the path', () => {
            const result = hasAnySuggestionsUnderPath(mockSuggestions, 'initiative.INIT-123');

            expect(result).toBe(true);
        });

        it('should return false when no suggestions exist at or under path', () => {
            const result = hasAnySuggestionsUnderPath(mockSuggestions, 'initiative.NOT-FOUND');

            expect(result).toBe(false);
        });

        it('should return false for empty base path', () => {
            const result = hasAnySuggestionsUnderPath(mockSuggestions, '');

            expect(result).toBe(false);
        });

        it('should return false for null/undefined inputs', () => {
            expect(hasAnySuggestionsUnderPath(null as any, 'initiative.INIT-123')).toBe(false);
            expect(hasAnySuggestionsUnderPath(mockSuggestions, null as any)).toBe(false);
            expect(hasAnySuggestionsUnderPath(undefined as any, undefined as any)).toBe(false);
        });

        it('should handle partial path matches correctly', () => {
            const suggestions = [
                { path: 'initiative.INIT-123-OTHER', type: 'entity' },
                { path: 'initiative.INIT-123', type: 'entity' }
            ];

            const result = hasAnySuggestionsUnderPath(suggestions, 'initiative.INIT-123');

            expect(result).toBe(true);
        });

        it('should not match partial path prefixes incorrectly', () => {
            const suggestions = [
                { path: 'initiative.INIT-123-OTHER', type: 'entity' }
            ];

            const result = hasAnySuggestionsUnderPath(suggestions, 'initiative.INIT-123');

            expect(result).toBe(false);
        });

        it('should handle empty suggestions array', () => {
            const result = hasAnySuggestionsUnderPath([], 'initiative.INIT-123');

            expect(result).toBe(false);
        });
    });

    describe('Integration scenarios', () => {
        it('should handle complex nested suggestion structure', () => {
            const complexSuggestions = [
                { path: 'initiative.INIT-123', type: 'entity' },
                { path: 'initiative.INIT-123.title', type: 'field', fieldName: 'title' },
                { path: 'initiative.INIT-123.tasks.TASK-1', type: 'entity' },
                { path: 'initiative.INIT-123.tasks.TASK-1.title', type: 'field' },
                { path: 'initiative.INIT-123.tasks.TASK-2.description', type: 'field' },
                { path: 'initiative.INIT-456.description', type: 'field', fieldName: 'description' }
            ];

            const groups = groupInitiativeSuggestionsByIdentifier(complexSuggestions);

            expect(Object.keys(groups)).toHaveLength(2);
            expect(groups['INIT-123'].fieldSuggestions).toHaveProperty('title');
            expect(groups['INIT-123'].taskSuggestions).toHaveProperty('TASK-1');
            expect(groups['INIT-123'].taskSuggestions).toHaveProperty('TASK-1.title');
            expect(groups['INIT-456'].fieldSuggestions).toHaveProperty('description');
        });

        it('should maintain consistency across all utility functions', () => {
            const basePath = 'initiative.INIT-123';
            
            const groups = groupInitiativeSuggestionsByIdentifier(mockSuggestions);
            const entitySuggestion = selectEntitySuggestionForBasePath(mockSuggestions, basePath);
            const hasTaskSuggestions = hasTaskSuggestionsUnderPath(mockSuggestions, basePath);
            const hasAnySuggestions = hasAnySuggestionsUnderPath(mockSuggestions, basePath);

            expect(groups['INIT-123']).toBeDefined();
            expect(entitySuggestion).toBeDefined();
            expect(hasTaskSuggestions).toBe(true);
            expect(hasAnySuggestions).toBe(true);
        });
    });
});