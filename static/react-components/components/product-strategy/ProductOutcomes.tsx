import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
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
    updateOutcome,
    isUpdating: isUpdatingOutcome,
    updateError: updateOutcomeError,
    deleteOutcome,
    isDeleting: isDeletingOutcome,
    deleteError: deleteOutcomeError,
    reorderOutcomes,
    isReordering: isReorderingOutcomes,
    reorderError: reorderOutcomeError,
  } = useProductOutcomes(workspaceId);

  const [isAddingOutcome, setIsAddingOutcome] = useState(false);
  const [editingOutcome, setEditingOutcome] = useState<string | null>(null);

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
    setEditingOutcome(null);
  };

  const handleEditOutcome = (outcomeId: string) => {
    setEditingOutcome(outcomeId);
    setIsAddingOutcome(false);
  };

  const handleUpdateOutcome = (data: {
    name: string;
    description?: string | null;
    metrics?: string | null;
    time_horizon_months?: number | null;
    pillar_ids?: string[];
  }) => {
    if (!editingOutcome) return;

    updateOutcome(
      { outcomeId: editingOutcome, request: data },
      {
        onSuccess: () => {
          setEditingOutcome(null);
        },
      }
    );
  };

  const handleDeleteOutcome = (outcomeId: string, outcomeName: string) => {
    if (window.confirm(`Are you sure you want to delete the outcome "${outcomeName}"? This action cannot be undone.`)) {
      deleteOutcome(outcomeId);
    }
  };

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) {
      return;
    }

    const sourceIndex = result.source.index;
    const destinationIndex = result.destination.index;

    if (sourceIndex === destinationIndex) {
      return;
    }

    const reorderedOutcomes = Array.from(outcomes);
    const [removed] = reorderedOutcomes.splice(sourceIndex, 1);
    reorderedOutcomes.splice(destinationIndex, 0, removed);

    const outcomeOrders = reorderedOutcomes.map((outcome, index) => ({
      id: outcome.id,
      display_order: index,
    }));

    reorderOutcomes({ outcomes: outcomeOrders });
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
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="outcomes-grid">
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className="grid grid-cols-1 gap-4"
              >
                {outcomes.map((outcome, index) => {
                  const isEditing = editingOutcome === outcome.id;

                  if (isEditing) {
                    return (
                      <div key={outcome.id} className="col-span-1">
                        <OutcomeForm
                          mode="edit"
                          initialData={{
                            name: outcome.name,
                            description: outcome.description,
                            metrics: outcome.metrics,
                            time_horizon_months: outcome.time_horizon_months,
                            pillar_ids: [],
                          }}
                          availablePillars={availablePillars}
                          onSave={handleUpdateOutcome}
                          onCancel={handleCancelOutcome}
                          isSaving={isUpdatingOutcome}
                        />
                        {updateOutcomeError && (
                          <p className="text-destructive mt-2">
                            {(updateOutcomeError as Error).message}
                          </p>
                        )}
                      </div>
                    );
                  }

                  return (
                    <Draggable
                      key={outcome.id}
                      draggableId={outcome.id}
                      index={index}
                      isDragDisabled={isReorderingOutcomes || isAddingOutcome || editingOutcome !== null}
                    >
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className={`bg-background border border-border rounded-lg p-4 ${
                            snapshot.isDragging ? 'opacity-60 rotate-2 shadow-lg' : ''
                          } ${
                            isReorderingOutcomes || isAddingOutcome || editingOutcome !== null
                              ? 'opacity-50 cursor-not-allowed'
                              : 'cursor-grab active:cursor-grabbing'
                          } transition-all duration-200`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h3 className="text-lg font-semibold text-foreground">
                              {outcome.name}
                            </h3>
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleEditOutcome(outcome.id)}
                                className="text-muted-foreground hover:text-foreground"
                                title="Edit outcome"
                                disabled={isReorderingOutcomes}
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => handleDeleteOutcome(outcome.id, outcome.name)}
                                className="text-muted-foreground hover:text-destructive"
                                title="Delete outcome"
                                disabled={isDeletingOutcome || isReorderingOutcomes}
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                              </button>
                            </div>
                          </div>
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
                      )}
                    </Draggable>
                  );
                })}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      )}

      {deleteOutcomeError && (
        <p className="text-destructive mt-4">
          {(deleteOutcomeError as Error).message}
        </p>
      )}

      {reorderOutcomeError && (
        <p className="text-destructive mt-4">
          {(reorderOutcomeError as Error).message}
        </p>
      )}

      {maxOutcomesReached && (
        <p className="text-sm text-muted-foreground mt-4">
          Maximum of 10 product outcomes reached.
        </p>
      )}
    </div>
  );
};

