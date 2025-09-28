import { useEffect } from 'react';
import { Message } from '#components/ChatDialog/ChatDialog';
import { InitiativeDto, InitiativeLLMResponse, LENS, ManagedInitiativeModel, ManagedTaskModel, TaskDto, TaskLLMResponse } from '#types';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';

interface EntityInfo {
    entityId: string | null;
    entityTitle: string | null;
    entityIdentifier: string | null;
}

export interface UseJobResultProcessorProps {
    jobResult: any;
    currentEntity: TaskDto | InitiativeDto | null;
    onMessageReady: (message: Message) => void;
}

/**
 * Hook to process job results and convert them to chat messages
 * @param jobResult The current AI job result
 * @param currentEntity The current task or initiative
 * @param onMessageReady Callback when a message is ready to be added
 */
export const useJobResultProcessor = ({
    jobResult,
    currentEntity,
    onMessageReady
}: UseJobResultProcessorProps) => {
    const { markJobAsResolved } = useAiImprovementsContext();

    // Process job result when it completes
    useEffect(() => {
        if (jobResult && jobResult.status === 'COMPLETED') {
            const entityInfo = getEntityInfo(currentEntity);

            // Extract the summary of changes from the job result
            const summary = (jobResult.result_data as TaskLLMResponse)?.message || '';

            // Create assistant message
            let suggestedChanges: ManagedTaskModel[] | ManagedInitiativeModel[] | null = null;

            if (jobResult.lens === LENS.TASK || jobResult.lens === LENS.TASKS) {
                suggestedChanges = (jobResult.result_data as TaskLLMResponse)?.managed_tasks;
            } else if (jobResult.lens === LENS.INITIATIVE || jobResult.lens === LENS.INITIATIVES) {
                suggestedChanges = (jobResult.result_data as InitiativeLLMResponse)?.managed_initiatives;
            }

            const assistantMessage: Message = {
                id: jobResult.id + 'reply',
                text: summary || 'No message from AI',
                sender: 'assistant' as const,
                timestamp: new Date(),
                lens: jobResult.lens,
                suggested_changes: suggestedChanges || undefined,
                ...entityInfo,
            };

            onMessageReady(assistantMessage);

            // If the job is completed and there are no changes, mark the job as resolved
            if (
                jobResult.status === 'COMPLETED' &&
                jobResult.error_message === null &&
                (
                    (jobResult.lens === LENS.INITIATIVE && (jobResult.result_data as InitiativeLLMResponse)?.managed_initiatives?.length === 0) ||
                    (jobResult.lens === LENS.TASK && (jobResult.result_data as TaskLLMResponse)?.managed_tasks?.length === 0)
                )
            ) {
                markJobAsResolved(jobResult.id);
            }
        }
    }, [jobResult, currentEntity, onMessageReady, markJobAsResolved]);

    /**
     * Helper function to get entity info for a message
     */
    const getEntityInfo = (
        currentEntity: TaskDto | InitiativeDto | null
    ): EntityInfo => {
        if (currentEntity) {
            return {
                entityId: currentEntity.id,
                entityTitle: currentEntity.title,
                entityIdentifier: currentEntity.identifier,
            };
        } else {
            return {
                entityId: null,
                entityTitle: null,
                entityIdentifier: null,
            };
        }
    };
};

export default useJobResultProcessor;