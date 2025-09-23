import React, { createContext, useContext, useMemo, ReactNode } from 'react';

import { ManagedInitiativeModel } from '#types';
import { useUnifiedSuggestions, UnifiedSuggestion } from '#hooks/diffs/useUnifiedSuggestions';
import { useResolutionOperations, ResolutionState, ResolutionMap } from '#hooks/diffs/useResolutionOperations';
import { useSaveSuggestions } from '#hooks/diffs/useSaveSuggestions';

// Re-export types for convenience
export type { UnifiedSuggestion, ResolutionState, ResolutionMap };

// -- Context Interface -----------

interface SuggestionsToBeResolvedContextType {
  /** All suggestions mapped by path */
  suggestions: Record<string, UnifiedSuggestion>;
  /** Resolution state for all paths */
  resolutions: ResolutionMap;
  /** Whether all suggestions are resolved */
  allResolved: boolean;
  /** Core resolution operation */
  resolve: (path: string, accepted: boolean, value?: any) => void;
  /** Rollback a specific resolution */
  rollback: (path: string) => void;
  /** Accept all suggestions at path or globally */
  acceptAll: (pathPrefix?: string) => void;
  /** Reject all suggestions at path or globally */
  rejectAll: (pathPrefix?: string) => void;
  /** Rollback all resolutions at path or globally */
  rollbackAll: (pathPrefix?: string) => void;
  /** Get resolution state for a specific path */
  getResolutionState: (path: string) => ResolutionState;
  /** Check if a path or all paths are fully resolved */
  isFullyResolved: (pathPrefix?: string) => boolean;
  /** Get all accepted changes for saving */
  getAcceptedChanges: () => ManagedInitiativeModel[];
}


// --- Context Definition ------------------------------------------------------------

const SuggestionsToBeResolvedContext = createContext<SuggestionsToBeResolvedContextType | undefined>(undefined);

export interface SuggestionsToBeResolvedContextProviderProps {
  children: ReactNode;
}

/**
 * Context provider that manages the resolution state of AI-suggested changes.
 * Combines field-level and entity-level resolution into a unified interface.
 * @param {SuggestionsToBeResolvedContextProviderProps} props - Component props.
 * @returns {React.ReactElement} The provider component.
 */
export const SuggestionsToBeResolvedContextProvider: React.FC<SuggestionsToBeResolvedContextProviderProps> = ({ children }) => {
  // Get unified suggestions from transformation hook
  const suggestions = useUnifiedSuggestions();

  // Get resolution operations and state
  const {
    resolutions,
    resolve,
    rollback,
    acceptAll,
    rejectAll,
    rollbackAll,
    getResolutionState,
    isFullyResolved,
    getAcceptedChanges
  } = useResolutionOperations(suggestions);

  // Calculate allResolved
  const allResolved = useMemo(() => isFullyResolved(), [isFullyResolved]);

  const contextValue = useMemo(() => ({
    suggestions,
    resolutions,
    allResolved,
    resolve,
    rollback,
    acceptAll,
    rejectAll,
    rollbackAll,
    getResolutionState,
    isFullyResolved,
    getAcceptedChanges
  }), [
    suggestions,
    resolutions,
    allResolved,
    resolve,
    rollback,
    acceptAll,
    rejectAll,
    rollbackAll,
    getResolutionState,
    isFullyResolved,
    getAcceptedChanges
  ]);

  return (
    <SuggestionsToBeResolvedContext.Provider value={contextValue}>
      {children}
    </SuggestionsToBeResolvedContext.Provider>
  );
};



// --- Consumer Hook ------------------------------------------------------------

/**
 * Hook to interact with the SuggestionsToBeResolved Context.
 * @returns {SuggestionsToBeResolvedContextType} Object containing suggestion resolution state and operations.
 */
export function useSuggestionsToBeResolvedContext(): SuggestionsToBeResolvedContextType {
  const context = useContext(SuggestionsToBeResolvedContext);
  if (context === undefined) {
    throw new Error('useSuggestionsToBeResolvedContext must be used within an SuggestionsToBeResolvedContextProvider');
  }
  return context;
}

// -- Convenience Hook -----------

/**
 * Convenience hook that provides filtered suggestions and typed operations.
 * This is the main hook components should use.
 */
export interface UseSuggestionsToBeResolvedReturn {
  /** All suggestions as array */
  suggestions: UnifiedSuggestion[];
  /** Field-level suggestions (title, description, tasks) */
  fieldSuggestions: UnifiedSuggestion[];
  /** Entity-level suggestions (create, delete) */
  entitySuggestions: UnifiedSuggestion[];
  /** Resolution state map */
  resolutions: ResolutionMap;
  /** Whether all suggestions are resolved */
  allResolved: boolean;
  /** Core operations */
  resolve: (path: string, accepted: boolean, value?: any) => void;
  rollback: (path: string) => void;
  acceptAll: (pathPrefix?: string) => void;
  rejectAll: (pathPrefix?: string) => void;
  rollbackAll: (pathPrefix?: string) => void;
  /** Utilities */
  getResolutionState: (path: string) => ResolutionState;
  isFullyResolved: (pathPrefix?: string) => boolean;
  getAcceptedChanges: () => ManagedInitiativeModel[];
  /** Save suggestions */
  saveSuggestions: () => Promise<void>;
}

/**
 * Main hook for consuming suggestion resolution functionality.
 * Provides filtered views and convenient access to all operations.
 */
export function useSuggestionsToBeResolved(): UseSuggestionsToBeResolvedReturn {
  const context = useSuggestionsToBeResolvedContext();

  const allSuggestions = useMemo(() => Object.values(context.suggestions), [context.suggestions]);

  const fieldSuggestions = useMemo(() =>
    allSuggestions.filter(s => s.type === 'field'), [allSuggestions]
  );

  const entitySuggestions = useMemo(() =>
    allSuggestions.filter(s => s.type === 'entity'), [allSuggestions]
  );

  const { saveSuggestions } = useSaveSuggestions();

  return {
    suggestions: allSuggestions,
    fieldSuggestions,
    entitySuggestions,
    resolutions: context.resolutions,
    allResolved: context.allResolved,
    resolve: context.resolve,
    rollback: context.rollback,
    acceptAll: context.acceptAll,
    rejectAll: context.rejectAll,
    rollbackAll: context.rollbackAll,
    getResolutionState: context.getResolutionState,
    isFullyResolved: context.isFullyResolved,
    getAcceptedChanges: context.getAcceptedChanges,
    saveSuggestions
  };
}
