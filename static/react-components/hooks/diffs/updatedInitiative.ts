import { useMemo } from 'react';
import type { InitiativeDto, UpdateInitiativeModel, ManagedTaskModel } from '#types';
import { applyTaskOperations } from './applyTaskOperations';

/**
 * Pure utility function that derives an updated initiative DTO by applying field updates
 * and task operations to an existing initiative.
 * 
 * @param initiative - The original initiative data, or null if not available
 * @param updateModel - The update model containing field changes and task operations, or null if no updates
 * @param applyTaskOperationsFunc - Function to apply task operations to existing tasks
 * @returns The updated initiative DTO, or null if the original initiative is null/undefined
 */
export function deriveUpdatedInitiativeDto(
    initiative: InitiativeDto | null | undefined,
    updateModel: UpdateInitiativeModel | null | undefined,
    applyTaskOperationsFunc: (originalTasks: any[], taskOps: ManagedTaskModel[]) => any[]
): InitiativeDto | null {
    // Return null if no initiative provided
    if (!initiative) {
        return null;
    }

    // Return original initiative if no update model provided
    if (!updateModel) {
        return initiative;
    }

    // Start with a copy of the original initiative
    const updated: InitiativeDto = { ...initiative };

    // Apply field updates if they are defined in the update model
    if (updateModel.title !== undefined) {
        updated.title = updateModel.title ?? '';
    }

    if (updateModel.description !== undefined) {
        updated.description = updateModel.description ?? '';
    }

    // Apply task operations if they exist in the update model
    if (updateModel.tasks !== undefined) {
        const originalTasks = initiative.tasks || [];
        updated.tasks = applyTaskOperationsFunc(originalTasks, updateModel.tasks);
    }

    return updated;
}

/**
 * React hook that derives an updated initiative DTO by applying field updates
 * and task operations from an update model to an existing initiative.
 * 
 * Uses memoization to avoid unnecessary recalculations when inputs haven't changed.
 * 
 * @param initiativeData - The original initiative data, or null if not available
 * @param currentInitiativeUpdate - The update model containing changes, or null if no updates
 * @returns The updated initiative DTO, or null if the original initiative is null
 */
export function useUpdatedInitiative(
    initiativeData: InitiativeDto | null,
    currentInitiativeUpdate: UpdateInitiativeModel | null
): InitiativeDto | null {
    return useMemo(() => {
        return deriveUpdatedInitiativeDto(
            initiativeData,
            currentInitiativeUpdate,
            applyTaskOperations
        );
    }, [initiativeData, currentInitiativeUpdate]);
}