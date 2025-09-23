import React, { createContext, useState, useCallback, useContext, useMemo, ReactNode, useEffect } from 'react';

// --- Context Definition ---

interface ActiveEntityContextType {
    activeInitiativeId: string | null;
    activeTaskId: string | null;
    recentInitiatives: string[];
    setActiveInitiative: (initiativeId: string | null) => void;
    setActiveTask: (taskId: string | null) => void;
    clearActiveEntity: () => void;
}

const STORAGE_KEY = 'recent_initiatives';
const MAX_RECENT_INITIATIVES = 10;

const ActiveEntityContext = createContext<ActiveEntityContextType | undefined>(undefined);

// --- Provider Component ---

export interface ActiveEntityProviderProps {
    children: ReactNode;
}

/**
 * Provider component for managing the currently active entity (Initiative or Task).
 * This should wrap parts of the application that need to track the active entity.
 * @param {ActiveEntityProviderProps} props - Component props.
 * @returns {React.ReactElement} The provider component.
 */
export const ActiveEntityProvider: React.FC<ActiveEntityProviderProps> = ({ children }) => {
    const [activeInitiativeId, setActiveInitiativeId] = useState<string | null>(null);
    const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
    const [recentInitiatives, setRecentInitiatives] = useState<string[]>(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch {
            return [];
        }
    });

    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(recentInitiatives));
    }, [recentInitiatives]);

    /**
     * Updates the recent initiatives list with a new initiative ID
     * @param {string} initiativeId - The initiative ID to add to history
     */
    const updateRecentInitiatives = useCallback((initiativeId: string) => {
        setRecentInitiatives(prev => {
            const filtered = prev.filter(id => id !== initiativeId);
            return [initiativeId, ...filtered].slice(0, MAX_RECENT_INITIATIVES);
        });
    }, []);

    /**
     * Sets the active initiative ID and clears the active task ID.
     * @param {string | null} initiativeId - The initiative ID to set, or null to clear.
     */
    const setActiveInitiative = useCallback((initiativeId: string | null) => {
        if (initiativeId !== activeInitiativeId) {
            setActiveInitiativeId(initiativeId);
            setActiveTaskId(null);
            if (initiativeId) {
                updateRecentInitiatives(initiativeId);
            }
        }
    }, [activeInitiativeId, updateRecentInitiatives]);

    /**
     * Sets the active task ID and clears the active initiative ID.
     * @param {string | null} taskId - The task ID to set, or null to clear.
     */
    const setActiveTask = useCallback((taskId: string | null) => {
        if (taskId !== activeTaskId) {
            setActiveTaskId(taskId);
            setActiveInitiativeId(null);
        }
    }, [activeTaskId]);

    /**
     * Clears both active initiative and task IDs.
     */
    const clearActiveEntity = useCallback(() => {
        if (activeInitiativeId || activeTaskId) {
            setActiveInitiativeId(null);
            setActiveTaskId(null);
        }
    }, [activeInitiativeId, activeTaskId]);

    const contextValue = useMemo(() => ({
        activeInitiativeId,
        activeTaskId,
        recentInitiatives,
        setActiveInitiative,
        setActiveTask,
        clearActiveEntity,
    }), [
        activeInitiativeId,
        activeTaskId,
        recentInitiatives,
        setActiveInitiative,
        setActiveTask,
        clearActiveEntity
    ]);

    return (
        <ActiveEntityContext.Provider value={contextValue}>
            {children}
        </ActiveEntityContext.Provider>
    );
};

// --- Consumer Hook ---

export interface UseActiveEntityReturn {
    activeInitiativeId: string | null;
    activeTaskId: string | null;
    recentInitiatives: string[];
    setActiveInitiative: (initiativeId: string | null) => void;
    setActiveTask: (taskId: string | null) => void;
    clearActiveEntity: () => void;
}

/**
 * Hook to interact with the Active Entity Context.
 * Provides access to the currently active initiative/task ID and functions to update it.
 * @returns {UseActiveEntityReturn} Object containing active entity state and functions.
 */
export function useActiveEntity(): UseActiveEntityReturn {
    const context = useContext(ActiveEntityContext);
    if (context === undefined) {
        throw new Error('useActiveEntity must be used within an ActiveEntityProvider');
    }
    return context;
}
