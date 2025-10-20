import React, { useState } from 'react';
import { useProductOutcomes } from '#hooks/useProductOutcomes';
import { OutcomeForm } from './OutcomeForm';

interface ProductOutcomesProps {
  workspaceId: string;
  availablePillars: Array<{ id: string; name: string }>;
}

export const ProductOutcomes: React.FC<ProductOutcomesProps> = ({
  workspaceId,
  availablePillars,
}) => {
  const {
    outcomes,
    isLoading: isOutcomesLoading,
    error: outcomesError,
    createOutcome,
    isCreating: isCreatingOutcome,
    createError: createOutcomeError,
  } = useProductOutcomes(workspaceId);

  const [isAddingOutcome, setIsAddingOutcome] = useState(false);

  const handleSaveOutcome = (data: {
    name: string;
    description?: string | null;
    metrics?: string | null;
    time_horizon_months?: number | null;
    pillar_ids?: string[];
  }) => {
    createOutcome(data, {
      onSuccess: () => {
        setIsAddingOutcome(false);
      },
    });
  };

  const handleCancelOutcome = () => {
    setIsAddingOutcome(false);
  };

  const maxOutcomesReached = outcomes.length >= 10;

  return (
    <div className="bg-card rounded-lg border border-border p-6 mt-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-foreground">
          Product Outcomes
        </h2>
        {!isAddingOutcome && (
          <button
            onClick={() => setIsAddingOutcome(true)}
            disabled={maxOutcomesReached}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            title={
              maxOutcomesReached
                ? 'Maximum of 10 outcomes reached'
                : 'Add a new product outcome'
            }
          >
            Add Outcome
          </button>
        )}
      </div>

      {isAddingOutcome && (
        <div className="mb-6">
          <OutcomeForm
            availablePillars={availablePillars}
            onSave={handleSaveOutcome}
            onCancel={handleCancelOutcome}
            isSaving={isCreatingOutcome}
          />
        </div>
      )}

      {createOutcomeError && (
        <p className="text-destructive mb-4">
          {(createOutcomeError as Error).message}
        </p>
      )}

      {isOutcomesLoading ? (
        <p className="text-muted-foreground">Loading outcomes...</p>
      ) : outcomesError ? (
        <p className="text-destructive">Error loading outcomes</p>
      ) : outcomes.length === 0 ? (
        <p className="text-muted-foreground">
          No product outcomes defined yet. Product outcomes are measurable
          results that signal strategic progress.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {outcomes.map((outcome) => (
            <div
              key={outcome.id}
              className="bg-background border border-border rounded-lg p-4"
            >
              <h3 className="text-lg font-semibold text-foreground mb-2">
                {outcome.name}
              </h3>
              {outcome.description && (
                <p className="text-foreground text-sm mb-2">
                  {outcome.description}
                </p>
              )}
              {outcome.metrics && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    Metrics:
                  </p>
                  <p className="text-sm text-foreground">{outcome.metrics}</p>
                </div>
              )}
              {outcome.time_horizon_months && (
                <p className="text-xs text-muted-foreground mt-2">
                  Time Horizon: {outcome.time_horizon_months} months
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {maxOutcomesReached && (
        <p className="text-sm text-muted-foreground mt-4">
          Maximum of 10 product outcomes reached.
        </p>
      )}
    </div>
  );
};

