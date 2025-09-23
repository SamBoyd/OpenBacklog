import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocation, useParams } from 'react-router';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useTasksContext } from '../contexts/TasksContext';
import { useEntityFromUrl } from './useEntityFromUrl';
import { LENS, InitiativeDto, TaskDto } from '#types';

// Mock dependencies
vi.mock('react-router', async (importOriginal) => {
    const actual = await importOriginal() as typeof import('react-router');
    return {
        ...actual,
        useLocation: vi.fn(),
        useParams: vi.fn(),
    };
});
vi.mock('#contexts/InitiativesContext');
vi.mock('#contexts/TasksContext');

// Mock return types
const mockUseLocation = useLocation as Mock;
const mockUseParams = useParams as Mock;
const mockUseInitiatives = useInitiativesContext as Mock;
const mockUseTasksContext = useTasksContext as Mock;

// Sample data
const mockInitiative: InitiativeDto = {
    id: 'init-123',
    identifier: 'I-1',
    user_id: 'user-1',
    title: 'Mock Initiative',
    description: 'Description',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    status: 'TO_DO',
    type: null,
    tasks: [],
    has_pending_job: false,
    workspace: { id: 'ws-1', name: 'Test WS', description: null, icon: null },
};

const mockTask: TaskDto = {
    id: 'task-456',
    identifier: 'T-1',
    user_id: 'user-1',
    initiative_id: 'init-123',
    title: 'Mock Task',
    description: 'Task Description',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    status: 'TO_DO',
    type: null,
    checklist: [],
    has_pending_job: false,
    workspace: { id: 'ws-1', name: 'Test WS', description: null, icon: null },
};


describe.skip('useEntityFromUrl', () => {
    beforeEach(() => {
        // Reset mocks before each test
        vi.resetAllMocks();

        // Default mock implementations
        mockUseLocation.mockReturnValue({ pathname: '/' });
        mockUseParams.mockReturnValue({});
        mockUseInitiatives.mockReturnValue({ initiativesData: null, isLoading: false });
        mockUseTasksContext.mockReturnValue({ tasks: null, isLoading: false });
    });

    it('should return default values when no params or specific path', () => {
        const { result } = renderHook(() => useEntityFromUrl());

        expect(result.current.lens).toBe(LENS.NONE);
        expect(result.current.initiativeId).toBeNull();
        expect(result.current.taskId).toBeNull();
        expect(result.current.initiativeData).toBeNull();
        expect(result.current.taskData).toBeNull();
        expect(result.current.currentEntity).toBeNull();
    });

    it('should identify LENS.TASKS for /workspace/tasks path', () => {
        mockUseLocation.mockReturnValue({ pathname: '/workspace/tasks' });
        const { result } = renderHook(() => useEntityFromUrl());
        expect(result.current.lens).toBe(LENS.TASKS);
    });

    it('should identify LENS.INITIATIVES for /workspace/initiatives path', () => {
        mockUseLocation.mockReturnValue({ pathname: '/workspace/initiatives' });
        const { result } = renderHook(() => useEntityFromUrl());
        expect(result.current.lens).toBe(LENS.INITIATIVES);
    });

    it('should identify LENS.INITIATIVE and return initiative data when initiativeId is present', () => {
        const initiativeId = 'init-123';
        mockUseParams.mockReturnValue({ initiativeId });
        mockUseInitiatives.mockReturnValue({ initiativesData: [mockInitiative], isLoading: false });

        const { result } = renderHook(() => useEntityFromUrl());

        expect(mockUseInitiatives).toHaveBeenCalledWith(initiativeId);
        expect(result.current.lens).toBe(LENS.INITIATIVE);
        expect(result.current.initiativeId).toBe(initiativeId);
        expect(result.current.taskId).toBeNull();
        expect(result.current.initiativeData).toEqual(mockInitiative);
        expect(result.current.taskData).toBeNull();
        expect(result.current.currentEntity).toEqual(mockInitiative);
    });

    it('should identify LENS.TASK and return task data when taskId is present', () => {
        const initiativeId = 'init-123';
        const taskId = 'task-456';
        mockUseParams.mockReturnValue({ initiativeId, taskId }); // Include initiativeId as it might be in the route
        mockUseTasksContext.mockReturnValue({ tasks: [mockTask], isLoading: false });
        // Mock useInitiativesContext as well, though its data shouldn't be the primary entity
        mockUseInitiatives.mockReturnValue({ initiativesData: [mockInitiative], isLoading: false });


        const { result } = renderHook(() => useEntityFromUrl());

        expect(mockUseTasksContext).toHaveBeenCalledWith(taskId);
        // It might still call useInitiativesContext depending on implementation, verify if needed
        expect(mockUseInitiatives).toHaveBeenCalledWith(initiativeId);

        expect(result.current.lens).toBe(LENS.TASK);
        expect(result.current.initiativeId).toBe(initiativeId); // It still extracts initiativeId
        expect(result.current.taskId).toBe(taskId);
        expect(result.current.initiativeData).toEqual(mockInitiative); // Initiative data is still fetched
        expect(result.current.taskData).toEqual(mockTask);
        expect(result.current.currentEntity).toEqual(mockTask); // Current entity is the task
    });

    it('should prioritize LENS.TASK when both taskId and initiativeId are present', () => {
        const initiativeId = 'init-123';
        const taskId = 'task-456';
        mockUseParams.mockReturnValue({ initiativeId, taskId });
        mockUseTasksContext.mockReturnValue({ tasks: [mockTask], isLoading: false });
        mockUseInitiatives.mockReturnValue({ initiativesData: [mockInitiative], isLoading: false });

        const { result } = renderHook(() => useEntityFromUrl());

        expect(result.current.lens).toBe(LENS.TASK);
        expect(result.current.currentEntity).toEqual(mockTask);
    });

    it('should handle cases where data fetching hooks return null', () => {
        const initiativeId = 'init-not-found';
        mockUseParams.mockReturnValue({ initiativeId });
        mockUseInitiatives.mockReturnValue({ initiativesData: null, isLoading: false }); // No initiative found

        const { result } = renderHook(() => useEntityFromUrl());

        expect(result.current.lens).toBe(LENS.INITIATIVE); // Lens is set based on param
        expect(result.current.initiativeId).toBe(initiativeId);
        expect(result.current.initiativeData).toBeNull();
        expect(result.current.currentEntity).toBeNull();
    });

    it('should update lens when location pathname changes', () => {
        const { result, rerender } = renderHook(() => useEntityFromUrl());

        // Initial state
        expect(result.current.lens).toBe(LENS.NONE);

        // Change path to tasks view
        act(() => {
            mockUseLocation.mockReturnValue({ pathname: '/workspace/tasks' });
        });
        rerender(); // Rerender the hook with new context
        expect(result.current.lens).toBe(LENS.TASKS);


        // Change path to an initiative view
        act(() => {
            mockUseLocation.mockReturnValue({ pathname: '/workspace/initiatives/init-abc' });
            mockUseParams.mockReturnValue({ initiativeId: 'init-abc' });
        });
        rerender();
        expect(result.current.lens).toBe(LENS.INITIATIVE);

        // Change path to a task view
        act(() => {
            mockUseLocation.mockReturnValue({ pathname: '/workspace/initiatives/init-abc/tasks/task-xyz' });
            mockUseParams.mockReturnValue({ initiativeId: 'init-abc', taskId: 'task-xyz' });
        });
        rerender();
        expect(result.current.lens).toBe(LENS.TASK);
    });
});