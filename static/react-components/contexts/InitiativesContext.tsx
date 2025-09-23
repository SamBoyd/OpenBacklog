import React, { createContext, useContext, ReactNode } from 'react';
import { useInitiativesContext } from '#hooks/initiatives';
import { InitiativesContextType, InitiativeFilters } from '#hooks/initiatives';

// Create the context with undefined as default value
const InitiativesContext = createContext<InitiativesContextType | undefined>(undefined);

/**
 * Props for the InitiativesProvider component
 */
interface InitiativesProviderProps {
  children: ReactNode;
  filters?: InitiativeFilters;
}

/**
 * Provider component that makes initiatives data and operations available to its children
 * @param {InitiativesProviderProps} props - The component props
 * @returns {React.ReactElement} The provider component
 */
export function InitiativesProvider({ children, filters }: InitiativesProviderProps) {
  // Use the composed hook that contains all the logic
  const value = useInitiativesContext(filters);

  return (
    <InitiativesContext.Provider value={value}>
      {children}
    </InitiativesContext.Provider>
  );
}

/**
 * Custom hook to access the initiatives context
 * @returns {InitiativesContextType} The initiatives context value
 * @throws {Error} If used outside of InitiativesProvider
 */
export function useInitiativesContextProvider(): InitiativesContextType {
  const context = useContext(InitiativesContext);

  if (context === undefined) {
    throw new Error('useInitiativesContextProvider must be used within an InitiativesProvider');
  }

  return context;
}

// Re-export types and filters for backward compatibility
export type { InitiativeFilters, InitiativesContextType };

// Re-export the main hook for backward compatibility
export { useInitiativesContext } from '#hooks/initiatives';
