import { useMemo } from 'react';
import { createPatch } from 'diff';
import { parseDiff, FileData } from 'react-diff-view';
import { TaskDto, ChecklistItemDto, UpdateTaskModel } from '#types';

/**
 * Return type for the useTaskDiff hook
 */
export interface TaskDiffResult {
    /** Parsed diff for the title field */
    titleDiff: FileData[] | null;
    /** Parsed diff for the description field */
    descriptionDiff: FileData[] | null;
    /** Whether the title has changed */
    titleChanged: boolean;
    /** Whether the description has changed */
    descriptionChanged: boolean;
    /** Whether there are actual changes in the parsed title diff */
    hasTitleChanges: boolean;
    /** Whether there are actual changes in the parsed description diff */
    hasDescriptionChanges: boolean;
    /** Whether the checklist items have changed */
    checklistItemsChanged: boolean;
    /** The original checklist items */
    originalChecklistItems: ChecklistItemDto[];
    /** The changed checklist items */
    changedChecklistItems: ChecklistItemDto[];
}


/**
 * Custom hook to generate and manage diffs between two tasks
 * @param {TaskDto} originalTask - The original task
 * @param {UpdateTaskModel} changedTask - The modified task
 * @returns {TaskDiffResult} An object containing diffs and change status
 */
export const useTaskDiff = (originalTask: TaskDto, changedTask: UpdateTaskModel): TaskDiffResult => {
    if (!!!originalTask || !!!changedTask) {
        return {
            titleDiff: null,
            descriptionDiff: null,
            titleChanged: false,
            descriptionChanged: false,
            hasTitleChanges: false,
            hasDescriptionChanges: false,
            checklistItemsChanged: false,
            originalChecklistItems: [],
            changedChecklistItems: []
        }
    }

    // Create unified diff strings for title and description
    const createDiffString = (oldText: string | null, newText: string | null, fieldName: string): string => {
        // Ensure we're comparing strings and they're actually different
        const oldString = String(oldText || '');
        const newString = String(newText || '');

        // Don't create diff if strings are identical
        if (oldString === newString) {
            return '';
        }

        // Ensure both strings end with a newline to prevent diff parsing issues
        const normalizeText = (text: string): string => {
            return text.endsWith('\n') ? text : `${text}\n`;
        };

        try {
            const patch = createPatch(
                fieldName,                // File name
                normalizeText(oldString), // Old text content
                normalizeText(newString), // New text content
                '',
                '',
                { context: 3 }
            );
            return patch.split('\n').slice(2).join('\n');
        } catch (error) {
            console.error(`Error creating diff for ${fieldName}:`, error);
            return '';
        }
    };

    // Check if fields have changed
    const titleChanged = originalTask.title !== changedTask.title;
    const descriptionChanged = originalTask.description !== changedTask.description;
    
    // If the changed task has null values, we don't want to show a diff - treat as no change
    const shouldShowTitleDiff = titleChanged && changedTask.title !== null;
    const shouldShowDescriptionDiff = descriptionChanged && changedTask.description !== null;
    
    // Process checklist items
    const originalChecklistItems = originalTask.checklist as ChecklistItemDto[] || [];
    const changedChecklistItems = changedTask.checklist as ChecklistItemDto[] || [];
    
    // Determine if checklist items have changed by comparing them
    const checklistItemsChanged = useMemo(() => {
        if (originalChecklistItems.length !== changedChecklistItems.length) return true;
        
        // Create maps for faster lookup, using titles instead of IDs
        const originalMap = new Map(originalChecklistItems.map(item => [item.title, item]));
        const changedMap = new Map(changedChecklistItems.map(item => [item.title, item]));
        
        // Check for added or removed items
        for (const title of originalMap.keys()) {
            if (!changedMap.has(title)) return true;
        }
        
        for (const title of changedMap.keys()) {
            if (!originalMap.has(title)) return true;
        }
        
        // Check for modified items
        for (const [title, originalItem] of originalMap.entries()) {
            const changedItem = changedMap.get(title);
            if (!changedItem) continue;
            
            if (
                originalItem.is_complete !== changedItem.is_complete ||
                originalItem.order !== changedItem.order
            ) {
                return true;
            }
        }
        
        return false;
    }, [originalChecklistItems, changedChecklistItems]);

    // Create diff strings only when we should show diffs
    const titleDiffString = useMemo(() =>
        shouldShowTitleDiff ? createDiffString(
            originalTask.title,
            changedTask.title,
            'title'
        ) : '',
        [shouldShowTitleDiff, originalTask.title, changedTask.title]);

    const descriptionDiffString = useMemo(() =>
        shouldShowDescriptionDiff ? createDiffString(
            originalTask.description,
            changedTask.description,
            'description'
        ) : '',
        [shouldShowDescriptionDiff, originalTask.description, changedTask.description]);

    // Parse the diff strings safely
    const titleDiff: FileData[] | null = useMemo(() => {
        if (!titleDiffString) return null;

        try {
            const parsed: FileData[] = parseDiff(titleDiffString);
            return parsed && parsed.length > 0 && parsed[0].hunks && parsed[0].hunks.length > 0 ? parsed : null;
        } catch (error) {
            console.error('Error parsing title diff:', error);
            return null;
        }
    }, [titleDiffString]);

    const descriptionDiff: FileData[] | null = useMemo(() => {
        if (!descriptionDiffString) return null;

        try {
            const parsed: FileData[] = parseDiff(descriptionDiffString);
            return parsed && parsed.length > 0 && parsed[0].hunks && parsed[0].hunks.length > 0 ? parsed : null;
        } catch (error) {
            console.error('Error parsing description diff:', error);
            return null;
        }
    }, [descriptionDiffString]);

    // Check if there are actual changes in the parsed diffs
    const hasTitleChanges = Boolean(titleDiff);
    const hasDescriptionChanges = Boolean(descriptionDiff);

    return {
        titleDiff,
        descriptionDiff,
        titleChanged: hasTitleChanges,
        descriptionChanged: hasDescriptionChanges,
        hasTitleChanges,
        hasDescriptionChanges,
        checklistItemsChanged,
        originalChecklistItems,
        changedChecklistItems
    };
};
