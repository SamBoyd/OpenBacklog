import React, { useMemo } from 'react';

import { InitiativeDto, UpdateInitiativeModel } from '#types';
import { createPatch } from 'diff';
import { parseDiff, FileData } from 'react-diff-view';

/**
 * Return type for the useInitiativeDiff hook
 */
export interface InitiativeDiffResult {
    /** Parsed diff for the title field */
    titleDiff: FileData[] | null;
    /** Parsed diff for the description field */
    descriptionDiff: FileData[] | null;
    /** Whether there are meaningful changes in the title that can be displayed */
    hasTitleDiff: boolean;
    /** Whether there are meaningful changes in the description that can be displayed */
    hasDescriptionDiff: boolean;
}

/**
 * Calculates the differences between two InitiativeDto objects for specific fields.
 * @param {InitiativeDto | null} originalInitiative - The original initiative data.
 * @param {InitiativeDto | null} changedInitiative - The changed initiative data (e.g., from AI suggestion).
 * @returns {InitiativeDiffResult} An object containing diff data and change flags for title and description.
 */
export const useInitiativeDiff = (
    originalInitiative: InitiativeDto | null,
    changedInitiative: UpdateInitiativeModel | null
): InitiativeDiffResult => {
    // Helper to create diff string like in useTaskDiff
    const createDiffString = (oldText: string | null, newText: string | null, fieldName: string): string => {
        const oldString = String(oldText ?? '');
        const newString = String(newText ?? '');

        if (oldString === newString) {
            return '';
        }

        const normalizeText = (text: string): string => {
            return text.endsWith('\n') ? text : `${text}\n`;
        };

        try {
            const patch = createPatch(
                fieldName,
                normalizeText(oldString),
                normalizeText(newString),
                '',
                '',
                { context: 3 }
            );
            // Return the patch content, excluding the header lines
            return patch.split('\n').slice(2).join('\n');
        } catch (error) {
            console.error(`Error creating diff for ${fieldName}:`, error);
            return '';
        }
    };

    // Create diff strings using the helper
    const titleDiffString = useMemo(() =>
        createDiffString(
            originalInitiative?.title ?? null,
            changedInitiative?.title ?? null,
            'title'
        ),
        [originalInitiative?.title, changedInitiative?.title]);

    const descriptionDiffString = useMemo(() =>
        createDiffString(
            originalInitiative?.description ?? null,
            changedInitiative?.description ?? null,
            'description'
        ),
        [originalInitiative?.description, changedInitiative?.description]);

    // Parse the diff strings safely, similar to useTaskDiff
    const titleDiff: FileData[] | null = useMemo(() => {
        if (!titleDiffString) return null;
        try {
            const parsed = parseDiff(titleDiffString);
            // Ensure the parsed diff is valid and has content
            return parsed?.[0]?.hunks?.length > 0 ? parsed : null;
        } catch (error) {
            console.error('Error parsing title diff:', error);
            return null;
        }
    }, [titleDiffString]);

    const descriptionDiff: FileData[] | null = useMemo(() => {
        if (!descriptionDiffString) return null;
        try {
            const parsed = parseDiff(descriptionDiffString);
            // Ensure the parsed diff is valid and has content
            return parsed?.[0]?.hunks?.length > 0 ? parsed : null;
        } catch (error) {
            console.error('Error parsing description diff:', error);
            return null;
        }
    }, [descriptionDiffString]);

    // Determine if there are meaningful diff changes that can be displayed
    const hasTitleDiff = changedInitiative?.title ? Boolean(titleDiff) : false;
    const hasDescriptionDiff = changedInitiative?.description ? Boolean(descriptionDiff) : false;

    return {
        titleDiff,
        descriptionDiff,
        hasTitleDiff,
        hasDescriptionDiff,
    };
};
