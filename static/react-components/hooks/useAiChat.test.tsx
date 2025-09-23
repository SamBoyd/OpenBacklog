import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach, Mock } from 'vitest';
import { useAiChat } from './useAiChat';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';
import { useTasksContext } from '#contexts/TasksContext';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useUserPreferences } from '#hooks/useUserPreferences';
import { useBillingUsage } from './useBillingUsage';
import { AiImprovementJobResult, AiImprovementJobStatus, LENS, TaskDto, InitiativeDto, WorkspaceDto, TaskStatus, ManagedEntityAction, AiJobChatMessage, AgentMode } from '#types';

// Mock dependencies
vi.mock('#contexts/AiImprovementsContext');
vi.mock('#contexts/TasksContext');
vi.mock('#contexts/InitiativesContext');
vi.mock('#hooks/useUserPreferences');
vi.mock('./useBillingUsage');

// Default mock implementations
const mockRequestImprovement = vi.fn();
const mockDeleteJob = vi.fn();
const mockUseAiImprovements = useAiImprovementsContext as Mock;
const mockUseTasksContext = useTasksContext as Mock;
const mockUseInitiatives = useInitiativesContext as Mock;
const mockUseUserPreferences = useUserPreferences as Mock;
const mockUseBillingUsage = useBillingUsage as Mock;

const mockWorkspace: WorkspaceDto = {
    id: 'workspace1',
    name: 'Test Workspace',
    description: 'This is a test workspace',
    icon: 'test-icon',
};

// Mock data
const mockTask: TaskDto = {
    id: 'task1', title: 'Test Task', initiative_id: 'init1',
    identifier: 'TASK-1',
    user_id: 'user1',
    description: 'This is a test task',
    created_at: '2021-01-01',
    updated_at: '2021-01-01',
    status: TaskStatus.TO_DO,
    type: null,
    checklist: [],
    has_pending_job: false,
    workspace: mockWorkspace
};
const mockInitiative: InitiativeDto = {
    id: 'init1', title: 'Test Initiative',
    identifier: 'INIT-1',
    user_id: 'user1',
    description: 'This is a test initiative',
    created_at: '2021-01-01',
    updated_at: '2021-01-01',
    status: TaskStatus.TO_DO,
    type: null,
    tasks: [],
    has_pending_job: false,
    workspace: mockWorkspace
};
const mockTasks: TaskDto[] = [mockTask];
const mockInitiatives: InitiativeDto[] = [mockInitiative];




describe('useAiChat', () => {
    let mockJobResult: AiImprovementJobResult | null = null;
    let mockError: string | null = null;
    let mockFilterTasksToInitiative: string | null | undefined = 'init1';

    beforeEach(() => {
        // Reset mocks before each test
        mockRequestImprovement.mockClear();
        mockDeleteJob.mockClear();
        mockError = null;
        mockFilterTasksToInitiative = 'init1'; // Default to having a filter
        
        // Mock localStorage
        const localStorageMock = {
            getItem: vi.fn(),
            setItem: vi.fn(),
            removeItem: vi.fn(),
            clear: vi.fn(),
        };
        Object.defineProperty(window, 'localStorage', {
            value: localStorageMock,
            writable: true,
        });

        // Default complete mock job result
        mockJobResult = {
            id: 'job1',
            status: AiImprovementJobStatus.COMPLETED,
            lens: LENS.TASK,
            mode: AgentMode.EDIT,
            input_data: mockTasks,
            result_data: {
                message: 'This is a test summary of changes',
                managed_tasks: [{ action: ManagedEntityAction.UPDATE, ...mockTask, description: mockTask.description ?? '' }],
            },
            thread_id: 'thread1',
            messages: [],
            error_message: null,
            created_at: '2021-01-01',
            updated_at: '2021-01-01',
            user_id: 'user1',
        };

        mockUseAiImprovements.mockReturnValue({
            jobResult: mockJobResult,
            error: mockError,
            requestImprovement: mockRequestImprovement,
            deleteJob: mockDeleteJob,
        });
        mockUseTasksContext.mockReturnValue({ tasks: mockTasks });
        mockUseInitiatives.mockReturnValue({ initiativesData: mockInitiatives });
        mockUseUserPreferences.mockReturnValue({
            preferences: { filterTasksToInitiative: mockFilterTasksToInitiative },
        });
        mockUseBillingUsage.mockReturnValue({
            userAccountDetails: { status: 'ACTIVE' },
            invalidateUserAccountDetails: vi.fn(),
        });
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    const renderTestHook = (props: { lens: LENS; currentEntity: InitiativeDto | TaskDto | null }) => {
        // Need to re-assign mock return values inside the hook render scope
        mockUseAiImprovements.mockReturnValue({
            jobResult: mockJobResult,
            error: mockError,
            requestImprovement: mockRequestImprovement,
            deleteJob: mockDeleteJob,
        });
        mockUseUserPreferences.mockReturnValue({
            preferences: { filterTasksToInitiative: mockFilterTasksToInitiative },
        });
        mockUseBillingUsage.mockReturnValue({
            userAccountDetails: { status: 'ACTIVE' },
            invalidateUserAccountDetails: vi.fn(),
        });
        mockUseTasksContext.mockReturnValue({ tasks: mockTasks });
        mockUseInitiatives.mockReturnValue({ initiativesData: mockInitiatives });

        return renderHook(() => useAiChat(props));
    };

    it('should return the ai job result from useAiImprovementsContext', () => {
        const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
        expect(result.current.jobResult).toEqual(mockJobResult);
    });

    it('should expose currentContext and setCurrentContext', () => {
        window.localStorage.getItem = vi.fn().mockReturnValue(null);
        const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
        expect(result.current.currentContext).toEqual([mockTask]);
        expect(typeof result.current.setCurrentContext).toBe('function');
    });

    it('should expose removeEntityFromContext function', () => {
        const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
        expect(typeof result.current.removeEntityFromContext).toBe('function');
    });

    it('should return the error from useAiImprovementsContext', () => {
        mockError = 'API Error';
        const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
        expect(result.current.error).toBe('API Error');
    });

    describe('Context Management', () => {
        it('should load context from localStorage on initialization', () => {
            const mockContext = [mockInitiative];
            window.localStorage.getItem = vi.fn().mockReturnValue(JSON.stringify(mockContext));
            
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            // Should include currentEntity at the beginning since it's not in stored context
            expect(result.current.currentContext).toEqual([mockTask, mockInitiative]);
        });

        it('should save context to localStorage when context changes', () => {
            const setItemSpy = vi.spyOn(window.localStorage, 'setItem');
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            
            act(() => {
                result.current.setCurrentContext([mockTask]);
            });
            
            expect(setItemSpy).toHaveBeenCalledWith('chatDialog_currentContext', JSON.stringify([mockTask]));
        });

        it('should remove entity from context by ID', () => {
            window.localStorage.getItem = vi.fn().mockReturnValue(JSON.stringify([mockTask, mockInitiative]));
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: null });
            
            act(() => {
                result.current.removeEntityFromContext('task1');
            });
            
            expect(result.current.currentContext).toEqual([mockInitiative]);
        });

        it('should handle localStorage errors gracefully', () => {
            window.localStorage.getItem = vi.fn().mockImplementation(() => {
                throw new Error('localStorage error');
            });
            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
            
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            // Should still include currentEntity even if localStorage fails
            expect(result.current.currentContext).toEqual([mockTask]);
            expect(consoleSpy).toHaveBeenCalled();
            
            consoleSpy.mockRestore();
        });

        it('should return empty array when no context in localStorage and no currentEntity', () => {
            window.localStorage.getItem = vi.fn().mockReturnValue(null);
            
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: null });
            expect(result.current.currentContext).toEqual([]);
        });

        it('should include currentEntity in context when provided', () => {
            window.localStorage.getItem = vi.fn().mockReturnValue(JSON.stringify([]));
            
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.currentContext).toEqual([mockTask]);
        });

        it('should not duplicate currentEntity if already in stored context', () => {
            window.localStorage.getItem = vi.fn().mockReturnValue(JSON.stringify([mockTask, mockInitiative]));
            
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.currentContext).toEqual([mockTask, mockInitiative]);
        });

        it('should add currentEntity at beginning if not in stored context', () => {
            window.localStorage.getItem = vi.fn().mockReturnValue(JSON.stringify([mockInitiative]));
            
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.currentContext).toEqual([mockTask, mockInitiative]);
        });
    });


    describe('chat disabled', () => {
        it('should set chatDisabled to true when lens is TASKS and filterTasksToInitiative is null', () => {
            mockFilterTasksToInitiative = null;
            const { result } = renderTestHook({ lens: LENS.TASKS, currentEntity: null });
            expect(result.current.chatDisabled).toBe(true);
        });

        it('should set the chat disabled to false when the job status is COMPLETED', () => {
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.chatDisabled).toBe(false);
        });

        it('should set the chat disabled to false when the job status is FAILED', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.FAILED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: null,
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.chatDisabled).toBe(false);
        });

        it('should set the chat disabled to false when the job status is CANCELED', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.CANCELED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: null,
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.chatDisabled).toBe(false);
        });

        it('should set the chat disabled to false when the job status is PROCESSING', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.PROCESSING,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: null,
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            // The effect updates based on jobResult, initially it might be false, let's check after potential update
            // Initially false, then effect runs based on jobResult
            expect(result.current.chatDisabled).toBe(false); // Based on logic: !COMPLETED -> false initially
        });

        it('should set the chat disabled to false when there is no job result', () => {
            mockJobResult = null;
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.chatDisabled).toBe(false);
        });


    });

    describe('error message', () => {
        it('should set the error message when the job status is FAILED', () => {
            const errorMessage = 'Job failed miserably';
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.FAILED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: errorMessage,
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.error).toBe(errorMessage);
        });

        it('should use default error message if job result error message is empty', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.FAILED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: null,
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.error).toBe('There\'s been an error. Please try again.');
        });

        it('should call deleteJob when the job status is FAILED', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.FAILED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: 'fail',
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(mockDeleteJob).toHaveBeenCalledWith('job1');
        });

        it('should call deleteJob when the job status is CANCELED', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.CANCELED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: null,
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(mockDeleteJob).toHaveBeenCalledWith('job1');
        });

        it('should clear the error message when a message is sent', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.FAILED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: 'Previous Error',
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result, rerender } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });

            // Expect initial error
            expect(result.current.error).toBe('Previous Error');

            // Send message
            act(() => {
                result.current.sendMessage('thread1', [{ role: 'user', content: 'New message', suggested_changes: [] }], LENS.TASK, AgentMode.EDIT);
            });

            // Re-render might be needed if state updates async, but sendMessage sets error directly
            rerender();

            // Expect error to be cleared
            expect(result.current.error).toBeNull();
        });

        it('should clear the error message when clearChat is called', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.FAILED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: 'Some Error',
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });

            expect(result.current.error).toBe('Some Error');

            act(() => {
                result.current.clearChat();
            });

            expect(result.current.error).toBeNull();
        });
    });

    describe('sendMessage', () => {
        it('should request an improvement when the lens is TASK and current entity is a task', () => {
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            const messagesToSend: AiJobChatMessage[] = [{ role: 'user', content: 'Improve this task' }];
            act(() => {
                result.current.sendMessage('thread1', messagesToSend, LENS.TASK, AgentMode.EDIT);
            });
            expect(mockRequestImprovement).toHaveBeenCalledWith([mockTask], LENS.TASK, 'thread1', AgentMode.EDIT, messagesToSend);
        });

        it('should request an improvement when the lens is INITIATIVE and current entity is an initiative', () => {
            const { result } = renderTestHook({ lens: LENS.INITIATIVE, currentEntity: mockInitiative });
            const messagesToSend: AiJobChatMessage[] = [{ role: 'user', content: 'Improve this initiative' }];
            act(() => {
                result.current.sendMessage('thread1', messagesToSend, LENS.INITIATIVE, AgentMode.EDIT);
            });
            expect(mockRequestImprovement).toHaveBeenCalledWith([mockInitiative], LENS.INITIATIVE, 'thread1', AgentMode.EDIT, messagesToSend);
        });

        it('should request an improvement with current context when lens is TASKS', () => {
            const { result } = renderTestHook({ lens: LENS.TASKS, currentEntity: null });
            const messagesToSend: AiJobChatMessage[] = [{ role: 'user', content: 'Improve these tasks' }];

            act(() => {
                result.current.sendMessage('thread1', messagesToSend, LENS.TASKS, AgentMode.EDIT);
            });

            // Should call with empty context since no currentEntity and no stored context
            expect(mockRequestImprovement).toHaveBeenCalledWith([], LENS.TASKS, 'thread1', AgentMode.EDIT, messagesToSend);
        });

        it('should request improvement even when lens is TASKS and filterTasksToInitiative is not set', () => {
            mockFilterTasksToInitiative = null;
            const { result } = renderTestHook({ lens: LENS.TASKS, currentEntity: null });
            const messagesToSend: AiJobChatMessage[] = [{ role: 'user', content: 'Improve these tasks' }];
            act(() => {
                result.current.sendMessage('thread1', messagesToSend, LENS.TASKS, AgentMode.EDIT);
            });
            // The hook should always call requestImprovement with current context
            expect(mockRequestImprovement).toHaveBeenCalledWith([], LENS.TASKS, 'thread1', AgentMode.EDIT, messagesToSend);
        });

        it('should request an improvement with current context when lens is INITIATIVES', () => {
            const { result } = renderTestHook({ lens: LENS.INITIATIVES, currentEntity: null });
            const messagesToSend: AiJobChatMessage[] = [{ role: 'user', content: 'Improve initiatives' }];
            act(() => {
                result.current.sendMessage('thread1', messagesToSend, LENS.INITIATIVES, AgentMode.EDIT);
            });
            // Should call with empty context since no currentEntity and no stored context
            expect(mockRequestImprovement).toHaveBeenCalledWith([], LENS.INITIATIVES, 'thread1', AgentMode.EDIT, messagesToSend);
        });
    });

    describe('clearChat', () => {
        it('should clear the error message', () => {
            mockJobResult = {
                id: 'job1',
                status: AiImprovementJobStatus.FAILED,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: 'Error to clear',
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            expect(result.current.error).toBe('Error to clear');
            act(() => {
                result.current.clearChat();
            });
            expect(result.current.error).toBeNull();
        });

        it('should call deleteJob if there is a current jobResult id', () => {
            mockJobResult = {
                id: 'job123',
                status: AiImprovementJobStatus.PROCESSING,
                lens: LENS.TASK,
                thread_id: 'thread1',
                mode: AgentMode.EDIT,
                result_data: null,
                error_message: null,
                input_data: mockTasks,
                messages: null,
                created_at: '2021-01-01',
                updated_at: '2021-01-01',
                user_id: 'user1'
            };
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            act(() => {
                result.current.clearChat();
            });
            expect(mockDeleteJob).toHaveBeenCalledWith('job123');
        });

        it('should not call deleteJob if there is no current jobResult id', () => {
            mockJobResult = null;
            const { result } = renderTestHook({ lens: LENS.TASK, currentEntity: mockTask });
            act(() => {
                result.current.clearChat();
            });
            expect(mockDeleteJob).not.toHaveBeenCalled();
        });
    });
});
