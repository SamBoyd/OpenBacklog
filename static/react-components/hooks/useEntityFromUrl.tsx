import { useState, useEffect } from 'react';
import { useLocation, useParams } from 'react-router';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useTasksContext } from '#contexts/TasksContext';
import { InitiativeDto, LENS, TaskDto } from '#types';



export interface useEntityFromUrlReturn {
    lens: LENS;
    initiativeId: string | null;
    taskId: string | null;
    initiativeData: InitiativeDto | null;
    taskData: TaskDto | null;
    currentEntity: InitiativeDto | TaskDto | null;
}

/**
 * Hook to extract initiative and task IDs from the URL using React Router params and fetch the corresponding entities
 * @returns Object containing initiative data, task data, and the current entity
 */
export const useEntityFromUrl = (): useEntityFromUrlReturn => {
    const location = useLocation();
    // Assuming your routes are configured with params like :initiativeId and :taskId
    const { initiativeId, taskId } = useParams();

    const { initiativesData } = useInitiativesContext();
    const { tasks, setTaskId } = useTasksContext();
    
    // Update the context when taskId changes
    useEffect(() => {
        setTaskId(taskId || '');
    }, [taskId, setTaskId]);

    const taskData = tasks?.[0] || null;
    const initiativeData = initiativesData?.find(i => i.id === initiativeId) || null;

    // The current entity is either the task or the initiative
    let currentEntity;
    let lens;

    const path = location.pathname;

    if (taskId) {
        currentEntity = taskData;
        lens = LENS.TASK;
    } else if (initiativeId) {
        currentEntity = initiativeData;
        lens = LENS.INITIATIVE;
    } else if (path === '/workspace/tasks') {
        currentEntity = null;
        lens = LENS.TASKS;
    } else {
        currentEntity = null;
        lens = LENS.INITIATIVES;
    }
    
    return {
        lens: lens,
        initiativeId: lens === LENS.INITIATIVE || lens === LENS.TASK ? initiativeId || null : null,
        taskId: lens === LENS.TASK ? taskId || null : null,
        initiativeData: lens === LENS.INITIATIVE || lens === LENS.TASK ? initiativesData?.[0] || null : null,
        taskData: lens === LENS.TASK ? taskData || null : null,
        currentEntity: currentEntity
    };
};
