import React, { useState } from 'react';
import { Navigate } from 'react-router';
import { useBillingUsage } from '#hooks/useBillingUsage';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { UserAccountStatus } from '#constants/userAccountStatus';
import WorkspaceCreateModal from '#components/WorkspaceSwitcher/WorkspaceCreateModal';

interface AppGuardProps {
  children: React.ReactNode;
}

/**
 * Guard component that handles both onboarding and workspace validation
 * Ensures user is onboarded and has a valid workspace before rendering protected content
 * 
 * Features optimizations for fast loading:
 * - Uses cached user account details to minimize loading screens
 * - Shows loading states only when no cached data is available
 * - Provides user-friendly error states and retry mechanisms
 */
const AppGuard: React.FC<AppGuardProps> = ({ children }) => {
  const { isAccountDetailsLoading, userIsOnboarded, userAccountDetails } = useBillingUsage();
  const {
    workspaces,
    currentWorkspace,
    isLoading: workspaceLoading,
    isProcessing: workspaceProcessing,
    error: workspaceError,
    addWorkspace
  } = useWorkspaces();

  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);

  console.log('userAccountDetails', userAccountDetails);

  // Stage 1: Check if billing/onboarding data is still loading
  // With caching, this should rarely show since we'll have cached data
  if (isAccountDetailsLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your account...</p>
        </div>
      </div>
    );
  }

  // Stage 2: Check if user needs onboarding
  if (!userIsOnboarded) {
    return <Navigate to="/workspace/onboarding" replace />;
  }
  
  // Stage 3: Check if workspace data is still loading
  if (workspaceLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading workspace...</p>
        </div>
      </div>
    );
  }

  // Stage 4: Handle workspace errors
  if (workspaceError) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <div className="text-center">
          <p className="text-destructive mb-4">Error loading workspace: {workspaceError.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Stage 5: Check if user has no workspaces - show creation modal
  const hasNoWorkspaces = !workspaceLoading && workspaces.length === 0;
  const needsWorkspaceCreation = hasNoWorkspaces || (!currentWorkspace && !isCreatingWorkspace);

  /**
   * Handles workspace creation from the modal
   */
  const handleWorkspaceCreation = async (name: string) => {
    try {
      setIsCreatingWorkspace(true);
      await addWorkspace({
        name,
        icon: null,
        description: null
      });
      setIsCreatingWorkspace(false);
    } catch (error) {
      setIsCreatingWorkspace(false);
      console.error('Failed to create workspace:', error);
    }
  };

  if (needsWorkspaceCreation) {
    return (
      <WorkspaceCreateModal
        isOpen={true}
        onClose={() => { }} // Non-dismissible modal
        onSubmit={handleWorkspaceCreation}
        isProcessing={workspaceProcessing || isCreatingWorkspace}
        isEnabled={true}
      />
    );
  }

  // Stage 6: All validations passed - render protected content
  return <>{children}</>;
};

export default AppGuard;