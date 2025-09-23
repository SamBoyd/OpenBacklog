import React, { createContext, useCallback, useContext, useMemo, ReactNode, useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { deleteAiImprovementJob, getAiImprovements, getAiImprovementsByThreadId, requestAiImprovement, updateAiImprovement } from '#api/ai';
import { useActiveEntity } from '#hooks/useActiveEntity';

import { AiImprovementJobResult, AiImprovementJobStatus, InitiativeDto, LENS, TaskDto, AiJobChatMessage, ManagedInitiativeModel, ManagedTaskModel, TaskLLMResponse, InitiativeLLMResponse, ManagedEntityAction, CreateInitiativeModel, UpdateInitiativeModel, AgentMode } from '#types';


// --- Context Definition ------------------------------------------------------------

interface AiImprovementsContextType {
  threadId: string | null;
  setThreadId: (threadId: string) => void;
  isRequestingImprovement: boolean;
  isDeletingJob: boolean;
  isUpdatingJob: boolean;
  jobResult: AiImprovementJobResult | null;
  initiativeImprovements: Record<string, ManagedInitiativeModel>;
  taskImprovements: Record<string, ManagedTaskModel>;
  loading: boolean;
  error: string | null;
  isEntityLocked: boolean;
  deleteJob: (jobId: string) => void;
  requestImprovement: (inputData: (InitiativeDto | TaskDto)[], lens: LENS, threadId: string, mode: AgentMode, messages?: AiJobChatMessage[]) => void;
  updateImprovement: (job: AiImprovementJobResult) => void;
  resetError: () => void;
}

const AiImprovementsContext = createContext<AiImprovementsContextType | undefined>(undefined);

const queryKey = ['ai-improvements'];


export interface AiImprovementsContextProviderProps {
  children: ReactNode;
}

/**
 * Provider component for managing AI improvement job state and interactions.
 * This should wrap the part of the application where AI improvements are relevant.
 * @param {AiImprovementsContextProviderProps} props - Component props.
 * @returns {React.ReactElement} The provider component.
 */
export const AiImprovementsContextProvider: React.FC<AiImprovementsContextProviderProps> = ({ children }) => {
  const queryClient = useQueryClient();
  const { activeInitiativeId, activeTaskId } = useActiveEntity();

  const [threadId, setThreadId] = useState<string | null>(null);

  // Mutation for requesting an improvement
  const {
    mutate: requestImprovementMutate,
    isPending: isRequestingImprovement,
    error: requestError
  } = useMutation({
    mutationFn: ({ inputData, lens, threadId, mode, messages }: { inputData: (InitiativeDto | TaskDto)[], lens: LENS, threadId: string, mode: AgentMode, messages?: AiJobChatMessage[] }) => {
      return requestAiImprovement({
        initiativeId: activeInitiativeId ?? undefined,
        taskId: activeTaskId ?? undefined,
        inputData,
        lens,
        threadId,
        messages,
        mode
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKey });
    },
    onError: (error) => {
      console.error('Failed to request AI improvement:', error);
    }
  });

  // Mutation for deleting a job
  const {
    mutate: deleteJobMutate,
    isPending: isDeletingJob,
    error: deleteError
  } = useMutation({
    mutationFn: deleteAiImprovementJob,
    onSuccess: (_, jobId) => {
      queryClient.setQueryData(queryKey, (oldData: AiImprovementJobResult[] | undefined) => {
        if (!oldData) return [];
        return oldData.filter(job => job.id !== jobId);
      });

      // Optionally still invalidate after a delay to ensure consistency
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: queryKey });
      }, 500);
    },
    onError: (error) => {
      console.error('Error deleting AI improvement job:', error);
    }
  });

  // Mutation for updating a job
  const {
    mutate: updateJobMutate,
    isPending: isUpdatingJob,
    error: updateError,
  } = useMutation({
    mutationFn: updateAiImprovement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKey });
    },
    onError: (error) => {
      console.error('Error updating AI improvement job:', error);
    }
  });

  // Query for fetching job data
  const {
    data: jobResult,
    error: queryError,
    isPending: isPendingJob,
    isFetching: isFetchingJob,
    refetch
  } = useQuery({
    queryKey: queryKey,
    queryFn: () => threadId ? getAiImprovementsByThreadId(threadId) : [],
    enabled: !!threadId,
    refetchInterval: (query) => {
      const data = query.state.data as AiImprovementJobResult[];
      if (!data || data.length === 0) {
        return false;
      }
      const status = data[0]?.status;
      const isInProgress = status && ['PENDING', 'IN_PROGRESS', 'PROCESSING'].includes(status);
      return isInProgress ? 2000 : false;
    },
    refetchOnWindowFocus: false
  });

  useEffect(() => {
    refetch();
  }, [threadId, refetch]);

  const latestJob = jobResult && jobResult.length > 0 ? jobResult[0] : null;

  // Handle multiple jobs case
  useEffect(() => {
    if (jobResult && jobResult.length > 1) {
      console.error('Multiple jobs found for thread', threadId);
      jobResult.slice(1).forEach((job) => deleteJobMutate(job.id));
    }
  }, [jobResult, threadId, deleteJobMutate]);

  const jobIsPendingOrProcessing = latestJob && (latestJob.status === AiImprovementJobStatus.PENDING || latestJob.status === AiImprovementJobStatus.PROCESSING);

  const error = queryError?.message || requestError?.message || deleteError?.message || updateError?.message ? String(queryError?.message || requestError?.message || deleteError?.message || updateError?.message) : null;
  const loading = isFetchingJob || isPendingJob || isRequestingImprovement || isDeletingJob || isUpdatingJob;
  const isEntityLocked = jobIsPendingOrProcessing ?? false;

  // Wrap mutation functions to match the expected interfaces
  const requestImprovement = useCallback((inputData: (InitiativeDto | TaskDto)[], lens: LENS, threadId: string, mode: AgentMode, messages?: AiJobChatMessage[]) => {
    requestImprovementMutate({ inputData, lens, threadId, mode, messages });
  }, [requestImprovementMutate]);

  const deleteJob = useCallback((jobId: string) => {
    deleteJobMutate(jobId);
  }, [deleteJobMutate]);

  const updateImprovement = useCallback((job: AiImprovementJobResult) => {
    updateJobMutate(job);
  }, [updateJobMutate]);

  const resetError = useCallback(() => {
    queryClient.resetQueries({ queryKey: queryKey });
  }, [queryClient]);

  const initiativeImprovements: Record<string, ManagedInitiativeModel> = useMemo(() => {
    if (!latestJob) return {};

    if (latestJob.status !== AiImprovementJobStatus.COMPLETED) {
      return {};
    }

    if (latestJob.mode !== AgentMode.EDIT) {
      return {};
    }

    if (typeof (latestJob.result_data as InitiativeLLMResponse).managed_initiatives === 'undefined' || !Array.isArray((latestJob.result_data as InitiativeLLMResponse).managed_initiatives)) {
      console.error('Invalid managed initiatives: ', latestJob);
      return {};
    }

    const result: Record<string, ManagedInitiativeModel> = {};

    let newCounter = 0
    if (latestJob.lens === LENS.INITIATIVES || latestJob.lens === LENS.INITIATIVE) {
      const managedInitiatives = (latestJob.result_data as InitiativeLLMResponse).managed_initiatives;

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
  }, [latestJob]);

  const taskImprovements: Record<string, ManagedTaskModel> = useMemo(() => {
    if (!latestJob) return {};
    if (latestJob.status !== AiImprovementJobStatus.COMPLETED) {
      return {};
    }

    const result: Record<string, ManagedTaskModel> = {};

    let newCounter = 0
    if (latestJob.lens === LENS.TASKS || latestJob.lens === LENS.TASK) {
      const managedTasks = (latestJob.result_data as TaskLLMResponse).managed_tasks;

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
  }, [latestJob]);

  const contextValue = useMemo(() => ({
    threadId,
    setThreadId,
    isRequestingImprovement,
    isDeletingJob,
    isUpdatingJob,
    jobResult: latestJob,
    initiativeImprovements,
    taskImprovements,
    loading,
    error,
    isEntityLocked,
    deleteJob,
    requestImprovement,
    updateImprovement,
    resetError,
  }), [
    threadId,
    setThreadId,
    isRequestingImprovement,
    isDeletingJob,
    isUpdatingJob,
    latestJob,
    initiativeImprovements,
    taskImprovements,
    loading,
    error,
    isEntityLocked,
    deleteJob,
    requestImprovement,
    updateImprovement,
    resetError,
  ]);

  return (
    <AiImprovementsContext.Provider value={contextValue}>
      {children}
    </AiImprovementsContext.Provider>
  );
};



// --- Consumer Hook ------------------------------------------------------------

// Define the return type for the consumer hook
export interface useAiImprovementsContextReturn {
  setThreadId: (threadId: string) => void;
  jobResult: AiImprovementJobResult | null;
  initiativeImprovements: Record<string, ManagedInitiativeModel>;
  taskImprovements: Record<string, ManagedTaskModel>;
  loading: boolean;
  error: string | null;
  isEntityLocked: boolean;
  deleteJob: (jobId: string) => void;
  requestImprovement: (inputData: (InitiativeDto | TaskDto)[], lens: LENS, threadId: string, mode: AgentMode, messages?: AiJobChatMessage[]) => void;
  updateImprovement: (job: AiImprovementJobResult) => void;
  resetError: () => void;
}

/**
 * Hook to interact with the AI Improvements Context.
 * @returns {useAiImprovementsContextReturn} Object containing AI improvement state and functions.
 */
export function useAiImprovementsContext(): useAiImprovementsContextReturn {
  const context = useContext(AiImprovementsContext);
  if (context === undefined) {
    throw new Error('useAiImprovementsContext must be used within an AiImprovementsContextProvider');
  }

  return context;
}
