import { z } from 'zod';
import { getPostgrestClient, withApiCall } from './api-utils';
import { AgentMode, AiImprovementJobResult, AiImprovementJobResultSchema, AiJobChatMessage, InitiativeDto, LENS, TaskDto } from '#types';

/**
 * Request parameters for the AI improvement API
 */
export interface AiImprovementRequest {
    /** ID of the initiative to improve (optional if taskId is provided) */
    initiativeId?: string;
    /** ID of the task to improve (optional if initiativeId is provided) */
    taskId?: string;
    /** Additional data to provide to the AI (optional) */
    inputData: (InitiativeDto | TaskDto)[];
    /** Custom message to guide the AI improvement (optional) */
    messages?: AiJobChatMessage[];
    /** Lens of the input data */
    lens: LENS;
    /** ID of the thread to improve */
    threadId: string;
    /** Agent mode to use for the improvement */
    mode?: string;
}

/**
 * Response schema for AI improvement API
 */
const AiImprovementResponseSchema = z.object({
    job_id: z.string(),
    status: z.string()
});

/**
 * Response type for AI improvement API
 */
export type AiImprovementResponse = z.infer<typeof AiImprovementResponseSchema>;

/**
 * Error class for AI API related errors
 */
export class AiApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = 'AiApiError';
        this.status = status;
    }
}


/**
 * Gets all AI improvements for an initiative or task
 * 
 * @param {string} [initiativeId] - InitiativeId of the initiative to get improvements for
 * @param {string} [taskId] - Optional taskId of the task to get improvements for
 * @param {LENS} [lens] - Optional lens to filter by
 * @returns {Promise<AiImprovementJobResult>} Response containing the job ID and status
 * @throws {AiApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getAiImprovements = async (lens: LENS, taskId?: string, initiativeId?: string): Promise<AiImprovementJobResult | null> => {
    return withApiCall(async () => {
        try {
            const response = await getPostgrestClient()
                .from('ai_improvement_job')
                .select('*')
                .neq('status', 'RESOLVED')

            if (response.error) {
                console.error('Error fetching AI improvements', response.error);
                throw new AiApiError(response.error.message, response.status);
            }

            if (!response.data) {
                throw new Error('No AI improvements found for the provided identifiers');
            }

            if (response.data.length == 0) {
                return null;
            }

            let filteredData: AiImprovementJobResult[] = response.data.filter((job) => job.lens === lens);

            if (filteredData.length == 0) {
                return null;
            }

            const validated_data = AiImprovementJobResultSchema.parse(filteredData[0]);
            return validated_data as AiImprovementJobResult;
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            throw new Error(`Error fetching AI improvements: ${(error as Error).message}`);
        }
    })
};

/**
 * Gets all AI improvements for an thread id
 * 
 * @param {string} [threadId] - The message thread id to get improvements for
 * @returns {Promise<AiImprovementJobResult[]>} Response containing the retrieved jobs
 * @throws {AiApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const getAiImprovementsByThreadId = async (threadId: string): Promise<AiImprovementJobResult[]> => {
    return withApiCall(async () => {
        try {
            const response = await getPostgrestClient()
                .from('ai_improvement_job')
                .select('*')
                .eq('thread_id', threadId)
                .neq('status', 'RESOLVED')

            if (response.error) {
                console.error('Error fetching AI improvements', response.error);
                throw new AiApiError(response.error.message, response.status);
            }

            if (!response.data) {
                throw new Error('No AI improvements found for the provided identifiers');
            }

            if (response.data.length == 0) {
                return [];
            }

            const validated_data = AiImprovementJobResultSchema.array().parse(response.data);

            return validated_data as AiImprovementJobResult[];
        } catch (error) {
            if (error instanceof z.ZodError) {
                throw new Error(`Invalid response format: ${error.message}`);
            }
            throw new Error(`Error fetching AI improvements: ${(error as Error).message}`);
        }
    })
};

/**
 * Requests an AI improvement for an initiative or task
 * 
 * @param {AiImprovementRequest} params - Parameters for the AI improvement request
 * @returns {Promise<AiImprovementResponseSchema>} Response containing the job ID and status
 * @throws {AiApiError} On API errors
 * @throws {Error} On validation or other errors
 */
export const requestAiImprovement = async (
    { inputData, messages, lens, threadId, mode=AgentMode.EDIT }: AiImprovementRequest
): Promise<AiImprovementResponse> => {
    // Validate that at least one ID is provided
    // if (!params.initiativeId && !params.taskId) {
    //     throw new Error('Either initiativeId or taskId must be provided');
    // }

    const response = await fetch('/api/ai-improvement', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            input_data: inputData,
            messages: messages,
            lens: lens,
            thread_id: threadId,
            mode: mode
        }),
    });

    if (!response.ok) {
        // Handle HTTP errors
        const errorText = await response.text();
        throw new AiApiError(
            `Failed to request AI improvement: ${errorText}`,
            response.status
        );
    }

    // Parse and validate response with Zod
    const data = await response.json();
    const validatedData = AiImprovementResponseSchema.parse(data);

    return validatedData;
};

/**
 * Marks an AI improvement job as resolved by its ID
 *
 * @param {string} jobId - The ID of the job to mark as resolved
 * @returns {Promise<void>} A promise that resolves when the job is marked as resolved
 * @throws {AiApiError} On API errors
 * @throws {Error} On other errors
 */
export const markAiImprovementJobAsResolved = async (jobId: string): Promise<void> => {
    if (!jobId) {
        throw new Error('Job ID is required');
    }

    withApiCall(async () => {
        try {
            await getPostgrestClient()
                .from('ai_improvement_job')
                .update({ status: 'RESOLVED' })
                .eq('id', jobId)
                .then(
                    response => {
                        if (response.error) {
                            console.error('Error marking AI improvement job as resolved', response.error);
                            throw new AiApiError(response.error.message, response.status);
                        }
                    }
                )
        } catch (error) {
            // Re-throw AiApiError as is
            if (error instanceof AiApiError) {
                throw error;
            }

            // Handle other errors
            throw new Error(`Error marking AI improvement job as resolved: ${(error as Error).message}`);
        }
    })
};

/**
 * Updates an existing AI improvement job, typically with user feedback or choices.
 * @param jobId The ID of the job to update.
 * @param updates The data to update the job with (e.g., selected suggestions, feedback).
 * @returns The updated job result.
 */
export const updateAiImprovement = async (
    job: AiImprovementJobResult
): Promise<AiImprovementJobResult> => {
    return withApiCall(async () => {
        const client = getPostgrestClient();
        // This is a placeholder endpoint and structure.
        // Adjust 'ai_improvement_jobs' and the update logic as needed.
        const { data, error } = await client
            .from('ai_improvement_jobs')
            .update(job)
            .eq('id', job.id)
            .select()
            .single();

        if (error) {
            console.error('Error updating AI improvement job:', error);
            throw new Error(`Failed to update AI job ${job.id}: ${error.message}`);
        }
        if (!data) {
            throw new Error(`AI job ${job.id} not found after update.`);
        }
        return data as AiImprovementJobResult;
    });
};

