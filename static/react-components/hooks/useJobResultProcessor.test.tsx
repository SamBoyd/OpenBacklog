import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest';
import { useJobResultProcessor } from './useJobResultProcessor';
import { LENS, TaskDto, InitiativeDto, TaskLLMResponse, InitiativeLLMResponse, ManagedEntityAction } from '#types';
import { Message } from '#components/ChatDialog/ChatDialog';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';

// Mock the useAiImprovementsContext hook
vi.mock('#contexts/AiImprovementsContext', () => ({
    useAiImprovementsContext: vi.fn(),
}));

// Mock Date.now() for consistent timestamps
const mockDateNow = 1678886400000; // A fixed timestamp
vi.spyOn(Date, 'now').mockImplementation(() => mockDateNow);
vi.useFakeTimers();
vi.setSystemTime(new Date(mockDateNow));

describe('useJobResultProcessor', () => {
    let mockDeleteJob = vi.fn();
    let mockOnMessageReady = vi.fn();

    const mockTask: TaskDto = {
        id: 'task-1', identifier: 'T-1', user_id: 'user-1', initiative_id: 'init-1', title: 'Test Task',
        description: "task mock", created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
        status: 'TO_DO', type: null, checklist: [], has_pending_job: false, workspace: { id: 'ws-1', name: 'Test WS', description: null, icon: null }
    };

    const mockInitiative: InitiativeDto = {
        id: 'init-1', identifier: 'I-1', user_id: 'user-1', title: 'Test Initiative',
        description: "initiative mock", created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
        status: 'TO_DO', type: null, tasks: [], has_pending_job: false, workspace: { id: 'ws-1', name: 'Test WS', description: null, icon: null }
    };

    beforeEach(() => {
        mockDeleteJob = vi.fn();
        mockOnMessageReady = vi.fn();
        (useAiImprovementsContext as Mock).mockReturnValue({ deleteJob: mockDeleteJob });
        vi.setSystemTime(new Date(mockDateNow));
    });

    afterEach(() => {
        vi.clearAllMocks();
        vi.useRealTimers();
    });

    it('should create assistant message when job completes for task', () => {
        const jobResult = {
            id: 'job-1',
            status: 'COMPLETED',
            result_data: {
                message: 'Task analysis complete',
                managed_tasks: [{ action: ManagedEntityAction.UPDATE, identifier: 'T-1', title: 'Updated Task', description: 'Updated description' }]
            } as TaskLLMResponse,
            lens: LENS.TASK,
            error_message: null,
        };

        renderHook(() => useJobResultProcessor({
            jobResult,
            currentEntity: mockTask,
            onMessageReady: mockOnMessageReady
        }));

        expect(mockOnMessageReady).toHaveBeenCalledWith({
            id: 'job-1reply',
            text: 'Task analysis complete',
            sender: 'assistant',
            timestamp: new Date(mockDateNow),
            lens: LENS.TASK,
            suggested_changes: [{ action: ManagedEntityAction.UPDATE, identifier: 'T-1', title: 'Updated Task', description: 'Updated description' }],
            entityId: mockTask.id,
            entityTitle: mockTask.title,
            entityIdentifier: mockTask.identifier,
        });
    });

    it('should create assistant message when job completes for initiative', () => {
        const jobResult = {
            id: 'job-2',
            status: 'COMPLETED',
            result_data: {
                message: 'Initiative analysis complete',
                managed_initiatives: [{ action: ManagedEntityAction.CREATE, title: 'New Initiative', description: 'New initiative description', workspace_identifier: 'ws-1' }]
            } as InitiativeLLMResponse,
            lens: LENS.INITIATIVE,
            error_message: null,
        };

        renderHook(() => useJobResultProcessor({
            jobResult,
            currentEntity: mockInitiative,
            onMessageReady: mockOnMessageReady
        }));

        expect(mockOnMessageReady).toHaveBeenCalledWith({
            id: 'job-2reply',
            text: 'Initiative analysis complete',
            sender: 'assistant',
            timestamp: new Date(mockDateNow),
            lens: LENS.INITIATIVE,
            suggested_changes: [{ action: ManagedEntityAction.CREATE, title: 'New Initiative', description: 'New initiative description', workspace_identifier: 'ws-1' }],
            entityId: mockInitiative.id,
            entityTitle: mockInitiative.title,
            entityIdentifier: mockInitiative.identifier,
        });
    });

    it('should delete job when completed with no changes for task', () => {
        const jobResult = {
            id: 'job-no-changes',
            status: 'COMPLETED',
            result_data: {
                message: 'No changes needed',
                managed_tasks: [] // Empty array indicates no changes
            } as TaskLLMResponse,
            lens: LENS.TASK,
            error_message: null,
        };

        renderHook(() => useJobResultProcessor({
            jobResult,
            currentEntity: mockTask,
            onMessageReady: mockOnMessageReady
        }));

        expect(mockDeleteJob).toHaveBeenCalledWith('job-no-changes');
        expect(mockOnMessageReady).toHaveBeenCalled(); // Message should still be created
    });

    it('should delete job when completed with no changes for initiative', () => {
        const jobResult = {
            id: 'job-no-changes-init',
            status: 'COMPLETED',
            result_data: {
                message: 'No changes needed',
                managed_initiatives: [] // Empty array indicates no changes
            } as InitiativeLLMResponse,
            lens: LENS.INITIATIVE,
            error_message: null,
        };

        renderHook(() => useJobResultProcessor({
            jobResult,
            currentEntity: mockInitiative,
            onMessageReady: mockOnMessageReady
        }));

        expect(mockDeleteJob).toHaveBeenCalledWith('job-no-changes-init');
        expect(mockOnMessageReady).toHaveBeenCalled(); // Message should still be created
    });

    it('should handle null entity gracefully', () => {
        const jobResult = {
            id: 'job-null-entity',
            status: 'COMPLETED',
            result_data: {
                message: 'Analysis complete',
                managed_tasks: []
            } as TaskLLMResponse,
            lens: LENS.TASK,
            error_message: null,
        };

        renderHook(() => useJobResultProcessor({
            jobResult,
            currentEntity: null,
            onMessageReady: mockOnMessageReady
        }));

        expect(mockOnMessageReady).toHaveBeenCalledWith({
            id: 'job-null-entityreply',
            text: 'Analysis complete',
            sender: 'assistant',
            timestamp: new Date(mockDateNow),
            lens: LENS.TASK,
            suggested_changes: [],
            entityId: null,
            entityTitle: null,
            entityIdentifier: null,
        });
    });

    it('should not process incomplete jobs', () => {
        const jobResult = {
            id: 'job-pending',
            status: 'PENDING',
            result_data: null,
            lens: LENS.TASK,
            error_message: null,
        };

        renderHook(() => useJobResultProcessor({
            jobResult,
            currentEntity: mockTask,
            onMessageReady: mockOnMessageReady
        }));

        expect(mockOnMessageReady).not.toHaveBeenCalled();
        expect(mockDeleteJob).not.toHaveBeenCalled();
    });

    it('should handle empty message with fallback text', () => {
        const jobResult = {
            id: 'job-empty-message',
            status: 'COMPLETED',
            result_data: {
                message: '', // Empty message
                managed_tasks: []
            } as TaskLLMResponse,
            lens: LENS.TASK,
            error_message: null,
        };

        renderHook(() => useJobResultProcessor({
            jobResult,
            currentEntity: mockTask,
            onMessageReady: mockOnMessageReady
        }));

        expect(mockOnMessageReady).toHaveBeenCalledWith(
            expect.objectContaining({
                text: 'No message from AI'
            })
        );
    });
});