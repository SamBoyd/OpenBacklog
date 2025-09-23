import React, { useMemo } from 'react';

import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';
import { AgentMode, AiImprovementJobStatus, InitiativeLLMResponse, LENS, ManagedEntityAction, ManagedInitiativeModel, ManagedTaskModel, TaskLLMResponse } from '#types';

export interface useSuggestedImprovementsReturn {
    initiativeImprovements: Record<string, ManagedInitiativeModel>;
    taskImprovements: Record<string, ManagedTaskModel>;
};


export const useSuggestedImprovements = (): useSuggestedImprovementsReturn => {
    const { jobResult } = useAiImprovementsContext();

    const initiativeImprovements: Record<string, ManagedInitiativeModel> = useMemo(() => {
        if (!jobResult) return {};

        if (jobResult.status !== AiImprovementJobStatus.COMPLETED) {
            return {};
        }

        if (jobResult.mode !== AgentMode.EDIT) {
            return {};
        }

        if (typeof (
            jobResult.result_data as InitiativeLLMResponse).managed_initiatives === 'undefined'
            ||
            !Array.isArray((jobResult.result_data as InitiativeLLMResponse).managed_initiatives
            )) {
            console.error('Invalid managed initiatives: ', jobResult);
            return {};
        }

        const result: Record<string, ManagedInitiativeModel> = {};

        let newCounter = 0
        if (jobResult.lens === LENS.INITIATIVES || jobResult.lens === LENS.INITIATIVE) {
            const managedInitiatives = (jobResult.result_data as InitiativeLLMResponse).managed_initiatives;

            for (const initiative of managedInitiatives) {
                if (initiative.action === ManagedEntityAction.CREATE) {
                    result[`new-${newCounter}`] = initiative;
                    newCounter++;
                }

                if (initiative.action === ManagedEntityAction.DELETE) {
                    result[initiative.identifier] = initiative;
                }

                if (initiative.action === ManagedEntityAction.UPDATE) {
                    result[initiative.identifier] = initiative;
                }
            }
        }

        return result;
    }, [jobResult]);

    const taskImprovements: Record<string, ManagedTaskModel> = useMemo(() => {
        if (!jobResult) return {};
        if (jobResult.status !== AiImprovementJobStatus.COMPLETED) {
            return {};
        }

        const result: Record<string, ManagedTaskModel> = {};

        let newCounter = 0
        if (jobResult.lens === LENS.TASKS || jobResult.lens === LENS.TASK) {
            const managedTasks = (jobResult.result_data as TaskLLMResponse).managed_tasks;

            for (const task of managedTasks) {
                if (task.action === ManagedEntityAction.CREATE) {
                    result[`new-${newCounter}`] = task;
                    newCounter++;
                }

                if (task.action === ManagedEntityAction.DELETE) {
                    result[task.identifier] = task;
                }

                if (task.action === ManagedEntityAction.UPDATE) {
                    result[task.identifier] = task;
                }
            }
        }

        return result;
    }, [jobResult]);

    return {
        initiativeImprovements,
        taskImprovements,
    }
}
