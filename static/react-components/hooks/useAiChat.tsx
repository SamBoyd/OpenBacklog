import React, { useState, useEffect, useMemo } from 'react';
import { AiImprovementJobResult, AiImprovementJobStatus, InitiativeDto, LENS, TaskDto, AiJobChatMessage, AgentMode } from '#types';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';
import { useUserPreferences } from '#hooks/useUserPreferences';
import { useBillingUsage } from './useBillingUsage';
import { hasActiveSubscription } from '#constants/userAccountStatus';

const CONTEXT_STORAGE_KEY = 'chatDialog_currentContext';

/**
 * Loads the current context from localStorage
 * @returns {(InitiativeDto | TaskDto)[]} The loaded context array or empty array if none found
 */
const loadContextFromStorage = (): (InitiativeDto | TaskDto)[] => {
    try {
        const storedContext = localStorage.getItem(CONTEXT_STORAGE_KEY);
        if (storedContext) {
            return JSON.parse(storedContext);
        }
    } catch (error) {
        console.error('Failed to load context from localStorage:', error);
    }
    return [];
};

/**
 * Saves the current context to localStorage
 * @param {(InitiativeDto | TaskDto)[]} context - The context array to save
 */
const saveContextToStorage = (context: (InitiativeDto | TaskDto)[]): void => {
    try {
        localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(context));
    } catch (error) {
        console.error('Failed to save context to localStorage:', error);
    }
};


export interface useAiChatReturn {
    jobResult: AiImprovementJobResult | null;
    error: string | null;
    chatDisabled: boolean;
    sendMessage: (threadId: string, messages: AiJobChatMessage[], lens: LENS, mode: AgentMode) => void;
    clearChat: () => void;
    currentContext: (InitiativeDto | TaskDto)[];
    setCurrentContext: React.Dispatch<React.SetStateAction<(InitiativeDto | TaskDto)[]>>;
    removeEntityFromContext: (entityId: string) => void;
}

export interface useAiChatProps {
    lens: LENS;
    currentEntity: InitiativeDto | TaskDto | null;
}

/**
 * Hook to manage AI chat communication
 * @param lens The current lens (TASK, INITIATIVE, etc.)
 * @param currentEntity The current initiative or task entity
 * @returns State and methods for interacting with AI, including context management
 */
export const useAiChat = ({ lens, currentEntity }: useAiChatProps): useAiChatReturn => {
    const { preferences } = useUserPreferences();
    const {
        jobResult,
        error,
        requestImprovement,
        markJobAsResolved
    } = useAiImprovementsContext();

    const [chatDisabled, setChatDisabled] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [storedContext, setStoredContext] = useState<(InitiativeDto | TaskDto)[]>(() =>
        loadContextFromStorage()
    );

    // Check subscription status
    const { userAccountDetails } = useBillingUsage();
    const hasSubscription = userAccountDetails ? hasActiveSubscription(userAccountDetails.status) : false;

    // Save context to localStorage whenever stored context changes
    useEffect(() => {
        saveContextToStorage(storedContext);
    }, [storedContext]);

    // Compute effective context that includes current entity if available
    const effectiveContext = useMemo(() => {
        if (!currentEntity) {
            return storedContext;
        }

        // Check if current entity is already in stored context
        const isAlreadyInContext = storedContext.some(entity => entity.id === currentEntity.id);

        if (isAlreadyInContext) {
            return storedContext;
        }

        // Add current entity to the beginning of the context
        return [currentEntity, ...storedContext];
    }, [currentEntity, storedContext]);

    /**
     * Removes an entity from the stored context by its ID
     * @param entityId The ID of the entity to remove
     */
    const removeEntityFromContext = (entityId: string) => {
        setStoredContext(prevContext => prevContext.filter(entity => entity.id !== entityId));
    };

    // Update chat state based on job result
    useEffect(() => {
        if (lens === LENS.TASKS && !preferences.filterTasksToInitiative) {
            setChatDisabled(true);
            return;
        }

        if (!jobResult) {
            setChatDisabled(false);
            return;
        }

        if (jobResult.status === AiImprovementJobStatus.COMPLETED) {
            setChatDisabled(false);
        } else if (jobResult.status === AiImprovementJobStatus.FAILED) {
            setErrorMessage(jobResult.error_message || 'There\'s been an error. Please try again.');
            markJobAsResolved(jobResult.id);
            setChatDisabled(false);
        } else if (jobResult.status === AiImprovementJobStatus.CANCELED) {
            setChatDisabled(false);
            markJobAsResolved(jobResult.id);
        } else {
            setChatDisabled(false);
        }
    }, [lens, preferences.filterTasksToInitiative, jobResult, markJobAsResolved]);

    /**
     * Send messages to the AI improvement service
     * @param messages The array of messages to send
     * @param lens The current lens
     */
    const sendMessage = (threadId: string, messages: AiJobChatMessage[], lens: LENS, mode: AgentMode) => {
        // Check subscription before sending message
        if (!hasSubscription) {
            setErrorMessage("AI chat requires a subscription. Subscribe to unlock AI features.");
            setChatDisabled(true);
            return;
        }

        setErrorMessage(null);

        if (jobResult?.id) {
            markJobAsResolved(jobResult.id);
        }

        requestImprovement(effectiveContext, lens, threadId, mode, messages);
    };

    /**
     * Clear the current chat state
     */
    const clearChat = () => {
        setErrorMessage(null);
        setChatDisabled(false);
        if (jobResult?.id) {
            markJobAsResolved(jobResult.id);
        }
    };

    return {
        jobResult,
        error: error || errorMessage,
        chatDisabled,
        sendMessage,
        clearChat,
        currentContext: effectiveContext,
        setCurrentContext: setStoredContext,
        removeEntityFromContext
    };
};

export default useAiChat;