import { useState, useEffect } from 'react';
import { Message } from '#components/ChatDialog/ChatDialog';
import { InitiativeDto, LENS, TaskDto } from '#types';
import { v4 as uuidv4 } from 'uuid';

// Define a constant key for localStorage
const CHAT_MESSAGES_STORAGE_KEY = 'chat_messages';
const THREAD_ID_STORAGE_KEY = 'thread_id';

export interface UseChatMessagesReturn {
    threadId: string;
    messages: Message[];
    addMessage: (message: Message) => void;
    addUserMessage: (messageText: string, lens: LENS, entity: InitiativeDto | TaskDto | null) => void;
    startNewThread: () => void;
}

/**
 * Hook to manage chat messages including persistence
 * @returns State and methods for managing messages
 */
export const useChatMessages = (): UseChatMessagesReturn => {

    const [threadId, setThreadId] = useState<string>(uuidv4());
    const [messages, setMessages] = useState<Message[]>([]);


    // Load messages from localStorage on mount
    useEffect(() => {
        try {
            const savedMessages = localStorage.getItem(CHAT_MESSAGES_STORAGE_KEY);
            if (savedMessages) {
                let parsedMessages = JSON.parse(savedMessages);

                // Handle the case where parsedMessages might still be a string (double stringified)
                if (typeof parsedMessages === 'string') {
                    parsedMessages = JSON.parse(parsedMessages);
                }

                // Convert string dates back to Date objects
                const messagesWithDates = parsedMessages.map((msg: any) => ({
                    ...msg,
                    timestamp: new Date(msg.timestamp)
                }));
                setMessages(messagesWithDates);
            }

            const savedThreadId = localStorage.getItem(THREAD_ID_STORAGE_KEY);
            if (savedThreadId) {
                setThreadId(savedThreadId);
            } else {
                localStorage.setItem(THREAD_ID_STORAGE_KEY, threadId);
            }
        } catch (error) {
            console.error('Error loading messages from localStorage:', error);
        }
    }, []);

    // Persist messages to localStorage when they change
    useEffect(() => {
        if (messages.length > 0) {
            try {
                console.log("Saving messages to localStorage:", messages);
                localStorage.setItem(CHAT_MESSAGES_STORAGE_KEY, JSON.stringify(messages));
            } catch (error) {
                console.error('Error saving messages to localStorage:', error);
            }
        }
    }, [messages]);


    /**
     * Add a message to the chat
     * @param message The message to add
     */
    const addMessage = (message: Message) => {
        setMessages(prev => [...prev, message]);
    };

    /**
     * Add a user message to the chat
     * @param messageText The text of the message
     * @param lens The lens context for the message
     * @param entity The entity (task or initiative) to associate with the message
     */
    const addUserMessage = (messageText: string, lens: LENS, entity: InitiativeDto | TaskDto | null) => {
        const userMessage: Message = {
            id: Date.now().toString(),
            text: messageText.trim(),
            sender: 'user',
            timestamp: new Date(),
            entityId: entity?.id || null,
            entityTitle: entity?.title || null,
            entityIdentifier: entity ? 'identifier' in entity ? entity.identifier : null : null,
            lens: lens,
        };

        setMessages(prev => [...prev, userMessage]);
    };

    /**
     * Clear all messages
     */
    const clearMessages = () => {
        setMessages([]);
        localStorage.setItem(CHAT_MESSAGES_STORAGE_KEY, JSON.stringify([]));
    };

    const startNewThread = () => {
        const newThreadId = uuidv4();
        setThreadId(newThreadId);
        localStorage.setItem(THREAD_ID_STORAGE_KEY, newThreadId);
        clearMessages();
    };

    return {
        threadId,
        messages,
        addMessage,
        addUserMessage,
        startNewThread,
    };
};

export default useChatMessages;