import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useChatMessages } from './useChatMessages';
import { LENS, TaskDto, InitiativeDto } from '#types';
import { Message } from '#components/ChatDialog/ChatDialog';


// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => {
            store[key] = value.toString();
        },
        removeItem: (key: string) => {
            delete store[key];
        },
        clear: () => {
            store = {};
        },
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
});

// Mock Date.now() for consistent message IDs
const mockDateNow = 1678886400000; // A fixed timestamp
vi.spyOn(Date, 'now').mockImplementation(() => mockDateNow);
vi.useFakeTimers();
vi.setSystemTime(new Date(mockDateNow));


describe('useChatMessages', () => {

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
        localStorageMock.clear();
        vi.setSystemTime(new Date(mockDateNow)); // Reset time for each test
    });

    afterEach(() => {
        vi.clearAllMocks();
        vi.useRealTimers(); // Restore real timers after each test
    });

    it('should return messages from local storage on mount', () => {
        const initialMessages = [
            { id: '1', text: 'Hello', sender: 'user', timestamp: new Date(mockDateNow - 1000).toISOString(), entityId: null, entityTitle: null, entityIdentifier: null, lens: LENS.NONE },
            { id: '2', text: 'Hi', sender: 'assistant', timestamp: new Date(mockDateNow - 500).toISOString(), entityId: null, entityTitle: null, entityIdentifier: null, lens: LENS.NONE },
        ];
        localStorageMock.setItem('chat_messages', JSON.stringify(initialMessages));

        const { result } = renderHook(() => useChatMessages());

        expect(result.current.messages).toEqual(initialMessages.map(msg => ({ ...msg, timestamp: new Date(msg.timestamp) })));
    });

    it('should persist messages to localStorage when they change', () => {
        const setItemSpy = vi.spyOn(localStorageMock, 'setItem');
        
        const { result } = renderHook(() => useChatMessages());

        act(() => {
            result.current.addUserMessage('Test message', LENS.TASK, mockTask);
        });

        expect(setItemSpy).toHaveBeenCalledWith('chat_messages', JSON.stringify(result.current.messages));
    });

    it('should add user message with correct properties', () => {
        const { result } = renderHook(() => useChatMessages());

        act(() => {
            result.current.addUserMessage('Hello world', LENS.TASK, mockTask);
        });

        expect(result.current.messages).toHaveLength(1);
        const message = result.current.messages[0];
        expect(message.text).toBe('Hello world');
        expect(message.sender).toBe('user');
        expect(message.lens).toBe(LENS.TASK);
        expect(message.entityId).toBe(mockTask.id);
        expect(message.entityTitle).toBe(mockTask.title);
        expect(message.entityIdentifier).toBe(mockTask.identifier);
        expect(message.timestamp).toEqual(new Date(mockDateNow));
    });

    it('should add user message with initiative properties', () => {
        const { result } = renderHook(() => useChatMessages());

        act(() => {
            result.current.addUserMessage('Initiative message', LENS.INITIATIVE, mockInitiative);
        });

        expect(result.current.messages).toHaveLength(1);
        const message = result.current.messages[0];
        expect(message.entityId).toBe(mockInitiative.id);
        expect(message.entityTitle).toBe(mockInitiative.title);
        expect(message.entityIdentifier).toBe(mockInitiative.identifier);
    });

    it('should add user message with null entity properties when no entity provided', () => {
        const { result } = renderHook(() => useChatMessages());

        act(() => {
            result.current.addUserMessage('No entity message', LENS.NONE, null);
        });

        expect(result.current.messages).toHaveLength(1);
        const message = result.current.messages[0];
        expect(message.entityId).toBeNull();
        expect(message.entityTitle).toBeNull();
        expect(message.entityIdentifier).toBeNull();
    });

    it('should add generic message via addMessage', () => {
        const { result } = renderHook(() => useChatMessages());
        
        const customMessage: Message = {
            id: 'custom-1',
            text: 'Custom assistant message',
            sender: 'assistant',
            timestamp: new Date(),
            entityId: 'entity-1',
            entityTitle: 'Custom Entity',
            entityIdentifier: 'CE-1',
            lens: LENS.TASK,
            suggested_changes: []
        };

        act(() => {
            result.current.addMessage(customMessage);
        });

        expect(result.current.messages).toHaveLength(1);
        expect(result.current.messages[0]).toEqual(customMessage);
    });

    it('should generate and persist thread ID', () => {
        const setItemSpy = vi.spyOn(localStorageMock, 'setItem');
        const { result } = renderHook(() => useChatMessages());

        expect(result.current.threadId).toBeDefined();
        expect(setItemSpy).toHaveBeenCalledWith('thread_id', result.current.threadId);
    });

    it('should load existing thread ID from localStorage', () => {
        const existingThreadId = 'existing-thread-123';
        localStorageMock.setItem('thread_id', existingThreadId);

        const { result } = renderHook(() => useChatMessages());

        expect(result.current.threadId).toBe(existingThreadId);
    });

    it('should start new thread and clear messages', () => {
        const setItemSpy = vi.spyOn(localStorageMock, 'setItem');
        
        const { result } = renderHook(() => useChatMessages());
        
        // Add a message first
        act(() => {
            result.current.addUserMessage('Test message', LENS.TASK, mockTask);
        });
        
        expect(result.current.messages).toHaveLength(1);
        const originalThreadId = result.current.threadId;

        // Start new thread
        act(() => {
            result.current.startNewThread();
        });

        expect(result.current.messages).toHaveLength(0);
        expect(result.current.threadId).not.toBe(originalThreadId);
        expect(setItemSpy).toHaveBeenCalledWith('thread_id', expect.any(String));
        expect(setItemSpy).toHaveBeenCalledWith('chat_messages', "[]");
    });

    it('should save the new thread ID to localStorage when starting new thread', () => {
        const { result } = renderHook(() => useChatMessages());
        const originalThreadId = result.current.threadId;

        // Clear any previous localStorage calls and spy on setItem
        const setItemSpy = vi.spyOn(localStorageMock, 'setItem');
        setItemSpy.mockClear();

        // Start new thread
        act(() => {
            result.current.startNewThread();
        });

        const newThreadId = result.current.threadId;
        
        // Verify that the new thread ID (not the old one) was saved to localStorage
        expect(newThreadId).not.toBe(originalThreadId);
        expect(setItemSpy).toHaveBeenCalledWith('thread_id', newThreadId);
        
        // Verify that the new thread ID was saved (should be the first call after clearing)
        const threadIdCalls = setItemSpy.mock.calls.filter(call => call[0] === 'thread_id');
        expect(threadIdCalls).toHaveLength(1);
        expect(threadIdCalls[0][1]).toBe(newThreadId);
    });

    it('should handle localStorage errors gracefully', () => {
        // Mock localStorage to throw an error
        const originalSetItem = localStorageMock.setItem;
        localStorageMock.setItem = vi.fn().mockImplementation(() => {
            throw new Error('localStorage error');
        });
        
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        
        const { result } = renderHook(() => useChatMessages());

        act(() => {
            result.current.addUserMessage('Test message', LENS.TASK, mockTask);
        });

        expect(consoleSpy).toHaveBeenCalledWith('Error saving messages to localStorage:', expect.any(Error));
        
        // Restore original method
        localStorageMock.setItem = originalSetItem;
        consoleSpy.mockRestore();
    });
});