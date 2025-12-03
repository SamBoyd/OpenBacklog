import React from 'react';

import { useParams } from '#hooks/useParams';
import { useStrategicInitiative } from '#hooks/useStrategicInitiative';
import { useInitiativesContext } from '#contexts/InitiativesContext';

import ViewStrategicInitiative from '#components/ViewStrategicInitiative';
import ViewInitiative from '#components/ViewInitiative';

/**
 * Wrapper component that intelligently routes between ViewInitiative and ViewStrategicInitiative
 * Checks if an initiative exists and whether it has strategic context
 * @returns {React.ReactElement} The appropriate initiative view or error message
 */
const ViewInitiativeWrapper: React.FC = () => {
  const { initiativeId } = useParams();
  const { initiativesData, shouldShowSkeleton } = useInitiativesContext();
  const { strategicInitiative, isLoading: strategicLoading } = useStrategicInitiative(
    initiativeId || ''
  );

  const initiativeData = initiativesData?.find(i => i.id === initiativeId);
  const isLoading = shouldShowSkeleton || strategicLoading;

  // Show loading state while fetching
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-pulse">
          <div className="h-12 w-64 bg-muted rounded mb-4"></div>
          <div className="h-96 w-96 bg-muted rounded"></div>
        </div>
      </div>
    );
  }

  // Show error if initiative doesn't exist
  if (!initiativeData) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground mb-2">Initiative not found</h1>
          <p className="text-muted-foreground">
            The initiative you're looking for doesn't exist or has been deleted.
          </p>
        </div>
      </div>
    );
  }

  // Show strategic view if strategic initiative exists
  if (strategicInitiative) {
    return <ViewStrategicInitiative />;
  }

  // Show regular view as fallback
  return <ViewInitiative />;
};

export default ViewInitiativeWrapper;
