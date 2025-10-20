import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useProductVision } from '#hooks/useProductVision';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { VisionEditor } from '#components/product-strategy/VisionEditor';
import { PillarForm } from '#components/product-strategy/PillarForm';

/**
 * ProductStrategy page component for managing workspace product vision
 * @returns {React.ReactElement} The product strategy page
 */
const ProductStrategy: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const workspaceId = currentWorkspace?.id || '';

  const {
    vision,
    isLoading,
    error,
    upsertVision,
    isUpserting,
    upsertError,
  } = useProductVision(workspaceId);

  const {
    pillars,
    isLoading: isPillarsLoading,
    error: pillarsError,
    createPillar,
    isCreating,
    createError,
    updatePillar,
    isUpdating,
    updateError,
    deletePillar,
    isDeleting,
    deleteError,
    reorderPillars,
    isReordering,
    reorderError,
  } = useStrategicPillars(workspaceId);

  const [isEditingVision, setIsEditingVision] = useState(false);
  const [isAddingPillar, setIsAddingPillar] = useState(false);
  const [editingPillar, setEditingPillar] = useState<string | null>(null);

  const handleSaveVision = (text: string) => {
    upsertVision(
      { vision_text: text },
      {
        onSuccess: () => {
          setIsEditingVision(false);
        },
      }
    );
  };

  const handleCancelVision = () => {
    setIsEditingVision(false);
  };

  const handleSavePillar = (data: {
    name: string;
    description?: string | null;
    anti_strategy?: string | null;
  }) => {
    createPillar(data, {
      onSuccess: () => {
        setIsAddingPillar(false);
      },
    });
  };

  const handleCancelPillar = () => {
    setIsAddingPillar(false);
    setEditingPillar(null);
  };

  const handleEditPillar = (pillarId: string) => {
    setEditingPillar(pillarId);
    setIsAddingPillar(false);
  };

  const handleUpdatePillar = (data: {
    name: string;
    description?: string | null;
    anti_strategy?: string | null;
  }) => {
    if (!editingPillar) return;

    updatePillar(
      { pillarId: editingPillar, request: data },
      {
        onSuccess: () => {
          setEditingPillar(null);
        },
      }
    );
  };

  const handleDeletePillar = (pillarId: string, pillarName: string) => {
    if (window.confirm(`Are you sure you want to delete the pillar "${pillarName}"? This action cannot be undone.`)) {
      deletePillar(pillarId);
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

    // Create a copy of the pillars array
    const reorderedPillars = Array.from(pillars);

    // Remove the dragged item from its original position
    const [removed] = reorderedPillars.splice(sourceIndex, 1);

    // Insert the dragged item at its new position
    reorderedPillars.splice(destinationIndex, 0, removed);

    // Build the reorder request with updated display_order values
    const pillarOrders = reorderedPillars.map((pillar, index) => ({
      id: pillar.id,
      display_order: index,
    }));

    // Call reorder mutation
    reorderPillars({ pillars: pillarOrders });
  };

  const maxPillarsReached = pillars.length >= 5;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-destructive">Error loading vision</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-foreground mb-6">
        Product Strategy
      </h1>

      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Product Vision
        </h2>

        {!isEditingVision && (
          <div>
            {vision ? (
              <div className="space-y-4">
                <p className="text-foreground whitespace-pre-wrap">
                  {vision.vision_text}
                </p>
                <button
                  onClick={() => setIsEditingVision(true)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  Edit Vision
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-muted-foreground">
                  No vision defined yet. Define your product vision to guide
                  your strategic planning.
                </p>
                <button
                  onClick={() => setIsEditingVision(true)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  Define Vision
                </button>
              </div>
            )}
          </div>
        )}

        {isEditingVision && (
          <VisionEditor
            initialText={vision?.vision_text || ''}
            onSave={handleSaveVision}
            onCancel={handleCancelVision}
            isSaving={isUpserting}
          />
        )}

        {upsertError && (
          <p className="text-destructive mt-4">
            {(upsertError as Error).message}
          </p>
        )}
      </div>

      {/* Strategic Pillars Section */}
      <div className="bg-card rounded-lg border border-border p-6 mt-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-foreground">
            Strategic Pillars
          </h2>
          {!isAddingPillar && (
            <button
              onClick={() => setIsAddingPillar(true)}
              disabled={maxPillarsReached}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              title={
                maxPillarsReached
                  ? 'Maximum of 5 pillars reached'
                  : 'Add a new strategic pillar'
              }
            >
              Add Pillar
            </button>
          )}
        </div>

        {isAddingPillar && (
          <div className="mb-6">
            <PillarForm
              onSave={handleSavePillar}
              onCancel={handleCancelPillar}
              isSaving={isCreating}
            />
          </div>
        )}

        {createError && (
          <p className="text-destructive mb-4">
            {(createError as Error).message}
          </p>
        )}

        {isPillarsLoading ? (
          <p className="text-muted-foreground">Loading pillars...</p>
        ) : pillarsError ? (
          <p className="text-destructive">Error loading pillars</p>
        ) : pillars.length === 0 ? (
          <p className="text-muted-foreground">
            No strategic pillars defined yet. Strategic pillars represent
            enduring ways to win that guide your initiatives.
          </p>
        ) : (
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="pillars-grid">
              {(provided) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className="grid grid-cols-1 md:grid-cols-2 gap-4"
                >
                  {pillars.map((pillar, index) => {
                    const isEditing = editingPillar === pillar.id;

                    if (isEditing) {
                      return (
                        <div key={pillar.id} className="md:col-span-2">
                          <PillarForm
                            mode="edit"
                            initialData={{
                              name: pillar.name,
                              description: pillar.description,
                              anti_strategy: pillar.anti_strategy,
                            }}
                            onSave={handleUpdatePillar}
                            onCancel={handleCancelPillar}
                            isSaving={isUpdating}
                          />
                          {updateError && (
                            <p className="text-destructive mt-2">
                              {(updateError as Error).message}
                            </p>
                          )}
                        </div>
                      );
                    }

                    return (
                      <Draggable
                        key={pillar.id}
                        draggableId={pillar.id}
                        index={index}
                        isDragDisabled={isReordering || isAddingPillar || editingPillar !== null}
                      >
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className={`bg-background border border-border rounded-lg p-4 ${
                              snapshot.isDragging ? 'opacity-60 rotate-2 shadow-lg' : ''
                            } ${
                              isReordering || isAddingPillar || editingPillar !== null
                                ? 'opacity-50 cursor-not-allowed'
                                : 'cursor-grab active:cursor-grabbing'
                            } transition-all duration-200`}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <h3 className="text-lg font-semibold text-foreground">
                                {pillar.name}
                              </h3>
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleEditPillar(pillar.id)}
                                  className="text-muted-foreground hover:text-foreground"
                                  title="Edit pillar"
                                  disabled={isReordering}
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handleDeletePillar(pillar.id, pillar.name)}
                                  className="text-muted-foreground hover:text-destructive"
                                  title="Delete pillar"
                                  disabled={isDeleting || isReordering}
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                  </svg>
                                </button>
                              </div>
                            </div>
                            {pillar.description && (
                              <p className="text-foreground text-sm mb-2">
                                {pillar.description}
                              </p>
                            )}
                            {pillar.anti_strategy && (
                              <div className="mt-2 pt-2 border-t border-border">
                                <p className="text-xs font-medium text-muted-foreground mb-1">
                                  Anti-Strategy:
                                </p>
                                <p className="text-sm text-foreground">
                                  {pillar.anti_strategy}
                                </p>
                              </div>
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

        {deleteError && (
          <p className="text-destructive mt-4">
            {(deleteError as Error).message}
          </p>
        )}

        {reorderError && (
          <p className="text-destructive mt-4">
            {(reorderError as Error).message}
          </p>
        )}

        {maxPillarsReached && (
          <p className="text-sm text-muted-foreground mt-4">
            Maximum of 5 strategic pillars reached.
          </p>
        )}
      </div>
    </div>
  );
};

export default ProductStrategy;
