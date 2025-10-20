import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes';
import { ThemeForm } from './ThemeForm';

interface RoadmapThemesProps {
  workspaceId: string;
  availableOutcomes: Array<{ id: string; name: string }>;
}

/**
 * RoadmapThemes component for managing workspace roadmap themes
 * @param {RoadmapThemesProps} props - Component props
 * @returns {React.ReactElement} The roadmap themes component
 */
export const RoadmapThemes: React.FC<RoadmapThemesProps> = ({
  workspaceId,
  availableOutcomes,
}) => {
  const {
    themes,
    isLoading: isThemesLoading,
    error: themesError,
    createTheme,
    isCreating: isCreatingTheme,
    createError: createThemeError,
    updateTheme,
    isUpdating: isUpdatingTheme,
    updateError: updateThemeError,
    deleteTheme,
    isDeleting: isDeletingTheme,
    deleteError: deleteThemeError,
    reorderThemes,
    isReordering: isReorderingThemes,
    reorderError: reorderThemeError,
  } = useRoadmapThemes(workspaceId);

  const [isAddingTheme, setIsAddingTheme] = useState(false);
  const [editingTheme, setEditingTheme] = useState<string | null>(null);

  const handleSaveTheme = (data: {
    name: string;
    problem_statement: string;
    hypothesis?: string | null;
    indicative_metrics?: string | null;
    time_horizon_months?: number | null;
    outcome_ids?: string[];
  }) => {
    createTheme(data, {
      onSuccess: () => {
        setIsAddingTheme(false);
      },
    });
  };

  const handleCancelTheme = () => {
    setIsAddingTheme(false);
    setEditingTheme(null);
  };

  const handleEditTheme = (themeId: string) => {
    setEditingTheme(themeId);
    setIsAddingTheme(false);
  };

  const handleUpdateTheme = (data: {
    name: string;
    problem_statement: string;
    hypothesis?: string | null;
    indicative_metrics?: string | null;
    time_horizon_months?: number | null;
    outcome_ids?: string[];
  }) => {
    if (!editingTheme) return;

    updateTheme(
      { themeId: editingTheme, request: data },
      {
        onSuccess: () => {
          setEditingTheme(null);
        },
      }
    );
  };

  const handleDeleteTheme = (themeId: string, themeName: string) => {
    if (window.confirm(`Are you sure you want to delete the theme "${themeName}"? This action cannot be undone.`)) {
      deleteTheme(themeId);
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

    const reorderedThemes = Array.from(themes);
    const [removed] = reorderedThemes.splice(sourceIndex, 1);
    reorderedThemes.splice(destinationIndex, 0, removed);

    const themeOrders = reorderedThemes.map((theme, index) => ({
      id: theme.id,
      display_order: index,
    }));

    reorderThemes({ themes: themeOrders });
  };

  const maxThemesReached = themes.length >= 5;

  return (
    <div className="bg-card rounded-lg border border-border p-6 mt-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-foreground">
          Roadmap Themes
        </h2>
        {!isAddingTheme && (
          <button
            onClick={() => setIsAddingTheme(true)}
            disabled={maxThemesReached}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            title={
              maxThemesReached
                ? 'Maximum of 5 themes reached'
                : 'Add a new roadmap theme'
            }
          >
            Add Theme
          </button>
        )}
      </div>

      {isAddingTheme && (
        <div className="mb-6">
          <ThemeForm
            availableOutcomes={availableOutcomes}
            onSave={handleSaveTheme}
            onCancel={handleCancelTheme}
            isSaving={isCreatingTheme}
          />
        </div>
      )}

      {createThemeError && (
        <p className="text-destructive mb-4">
          {(createThemeError as Error).message}
        </p>
      )}

      {isThemesLoading ? (
        <p className="text-muted-foreground">Loading themes...</p>
      ) : themesError ? (
        <p className="text-destructive">Error loading themes</p>
      ) : themes.length === 0 ? (
        <p className="text-muted-foreground">
          No roadmap themes defined yet. Roadmap themes represent 6-12 month
          strategic bets that advance your product outcomes.
        </p>
      ) : (
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="themes-grid">
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className="grid grid-cols-1 gap-4"
              >
                {themes.map((theme, index) => {
                  const isEditing = editingTheme === theme.id;

                  if (isEditing) {
                    return (
                      <div key={theme.id} className="col-span-1">
                        <ThemeForm
                          mode="edit"
                          initialData={{
                            name: theme.name,
                            problem_statement: theme.problem_statement,
                            hypothesis: theme.hypothesis,
                            indicative_metrics: theme.indicative_metrics,
                            time_horizon_months: theme.time_horizon_months,
                            outcome_ids: theme.outcome_ids,
                          }}
                          availableOutcomes={availableOutcomes}
                          onSave={handleUpdateTheme}
                          onCancel={handleCancelTheme}
                          isSaving={isUpdatingTheme}
                        />
                        {updateThemeError && (
                          <p className="text-destructive mt-2">
                            {(updateThemeError as Error).message}
                          </p>
                        )}
                      </div>
                    );
                  }

                  return (
                    <Draggable
                      key={theme.id}
                      draggableId={theme.id}
                      index={index}
                      isDragDisabled={isReorderingThemes || isAddingTheme || editingTheme !== null}
                    >
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className={`bg-background border border-border rounded-lg p-4 ${snapshot.isDragging ? 'opacity-60 rotate-2 shadow-lg' : ''
                            } ${isReorderingThemes || isAddingTheme || editingTheme !== null
                              ? 'opacity-50 cursor-not-allowed'
                              : 'cursor-grab active:cursor-grabbing'
                            } transition-all duration-200`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h3 className="text-lg font-semibold text-foreground">
                              {theme.name}
                            </h3>
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleEditTheme(theme.id)}
                                className="text-muted-foreground hover:text-foreground"
                                title="Edit theme"
                                disabled={isReorderingThemes}
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => handleDeleteTheme(theme.id, theme.name)}
                                className="text-muted-foreground hover:text-destructive"
                                title="Delete theme"
                                disabled={isDeletingTheme || isReorderingThemes}
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                              </button>
                            </div>
                          </div>
                          <div className="mt-2">
                            <p className="text-xs font-medium text-muted-foreground mb-1">
                              Problem Statement:
                            </p>
                            <p className="text-sm text-foreground mb-2">
                              {theme.problem_statement}
                            </p>
                          </div>
                          {theme.hypothesis && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                Hypothesis:
                              </p>
                              <p className="text-sm text-foreground">{theme.hypothesis}</p>
                            </div>
                          )}
                          {theme.indicative_metrics && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                Indicative Metrics:
                              </p>
                              <p className="text-sm text-foreground">{theme.indicative_metrics}</p>
                            </div>
                          )}
                          {theme.time_horizon_months !== null && (
                            <p className="text-xs text-muted-foreground mt-2">
                              Time Horizon: {theme.time_horizon_months} months
                            </p>
                          )}
                          {theme.outcome_ids.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                Product Outcomes:
                              </p>
                              {theme.outcome_ids.map(outcome_id => (
                                <p key={outcome_id} className="text-sm text-foreground">{availableOutcomes.find(availableOutcome => availableOutcome.id == outcome_id)?.name}</p>
                              ))}
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

      {deleteThemeError && (
        <p className="text-destructive mt-4">
          {(deleteThemeError as Error).message}
        </p>
      )}

      {reorderThemeError && (
        <p className="text-destructive mt-4">
          {(reorderThemeError as Error).message}
        </p>
      )}

      {maxThemesReached && (
        <p className="text-sm text-muted-foreground mt-4">
          Maximum of 5 roadmap themes reached.
        </p>
      )}
    </div>
  );
};
