import React from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useRoadmapWithInitiatives } from '#hooks/useRoadmapWithInitiatives';
import RoadmapThemeCard from '#components/roadmap/RoadmapThemeCard';

/**
 * Roadmap page component for viewing and prioritizing themes with their initiatives
 * @returns {React.ReactElement} The roadmap page
 */
const Roadmap: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const {
    prioritizedThemes,
    unprioritizedThemes,
    isLoading,
    isLoadingInitiatives,
    error,
    prioritizeTheme,
    isPrioritizing,
    deprioritizeTheme,
    isDeprioritizing,
    reorderPrioritizedThemes,
    isReordering,
  } = useRoadmapWithInitiatives(currentWorkspace?.id || '');

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const { source, destination } = result;

    // No change
    if (source.droppableId === destination.droppableId && source.index === destination.index) {
      return;
    }

    const themeId = result.draggableId;

    // Case 1: Move from unprioritized to prioritized
    if (source.droppableId === 'unprioritized' && destination.droppableId === 'prioritized') {
      prioritizeTheme({ themeId, position: destination.index });
    }
    // Case 2: Move from prioritized to unprioritized
    else if (source.droppableId === 'prioritized' && destination.droppableId === 'unprioritized') {
      deprioritizeTheme(themeId);
    }
    // Case 3: Reorder within prioritized
    else if (source.droppableId === 'prioritized' && destination.droppableId === 'prioritized') {
      const reordered = Array.from(prioritizedThemes);
      const [removed] = reordered.splice(source.index, 1);
      reordered.splice(destination.index, 0, removed);

      const themeOrders = reordered.map((theme, index) => ({
        id: theme.id,
        display_order: index,
      }));

      reorderPrioritizedThemes({ themes: themeOrders });
    }
    // Case 4: Within unprioritized - no action needed (no ordering in backlog)
  };

  // Don't render if no workspace is selected
  if (!currentWorkspace) {
    return null;
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <p className="text-sm text-destructive text-center">
          Failed to load roadmap themes
        </p>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <p className="text-sm text-muted-foreground">Loading roadmap...</p>
      </div>
    );
  }

  const isDragDisabled = isLoading || isPrioritizing || isDeprioritizing || isReordering;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border bg-card">
        <h1 className="text-2xl font-bold text-foreground">Roadmap</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Prioritize themes and view associated initiatives
        </p>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <DragDropContext onDragEnd={handleDragEnd}>
          <div className="h-full grid grid-cols-2 gap-4 p-6">
            {/* Prioritized Themes Column */}
            <div className="flex flex-col">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Prioritized Themes
              </h2>
              <Droppable droppableId="prioritized">
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className={`flex-1 overflow-y-auto rounded-lg p-4 ${
                      snapshot.isDraggingOver ? 'bg-primary/5' : 'bg-muted/20'
                    }`}
                  >
                    {prioritizedThemes.length === 0 ? (
                      <div className="flex items-center justify-center h-32 border-2 border-dashed border-border/50 rounded-md">
                        <span className="text-sm text-muted-foreground">
                          {snapshot.isDraggingOver ? 'Drop here to prioritize' : 'Drag themes here to prioritize'}
                        </span>
                      </div>
                    ) : (
                      prioritizedThemes.map((theme, index) => (
                        <Draggable
                          key={theme.id}
                          draggableId={theme.id}
                          index={index}
                          isDragDisabled={isDragDisabled}
                        >
                          {(provided, snapshot) => (
                            <RoadmapThemeCard
                              theme={theme}
                              provided={provided}
                              snapshot={snapshot}
                              isDragDisabled={isDragDisabled}
                            />
                          )}
                        </Draggable>
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>

            {/* Unprioritized Themes Column */}
            <div className="flex flex-col">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                Unprioritized Themes
              </h2>
              <Droppable droppableId="unprioritized">
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className={`flex-1 overflow-y-auto rounded-lg p-4 ${
                      snapshot.isDraggingOver ? 'bg-primary/5' : 'bg-muted/20'
                    }`}
                  >
                    {unprioritizedThemes.length === 0 ? (
                      <div className="flex items-center justify-center h-32 border-2 border-dashed border-border/50 rounded-md">
                        <span className="text-sm text-muted-foreground">
                          {snapshot.isDraggingOver ? 'Drop here to deprioritize' : 'All themes are prioritized'}
                        </span>
                      </div>
                    ) : (
                      unprioritizedThemes.map((theme, index) => (
                        <Draggable
                          key={theme.id}
                          draggableId={theme.id}
                          index={index}
                          isDragDisabled={isDragDisabled}
                        >
                          {(provided, snapshot) => (
                            <RoadmapThemeCard
                              theme={theme}
                              provided={provided}
                              snapshot={snapshot}
                              isDragDisabled={isDragDisabled}
                            />
                          )}
                        </Draggable>
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          </div>
        </DragDropContext>
      </div>

      {/* Empty State */}
      {prioritizedThemes.length === 0 && unprioritizedThemes.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center p-8">
          <p className="text-sm text-muted-foreground text-center">
            No roadmap themes yet. Create themes in the Product Strategy page.
          </p>
        </div>
      )}

      {/* Loading Initiatives Indicator */}
      {isLoadingInitiatives && (
        <div className="fixed bottom-4 right-4 bg-card border border-border rounded-md px-4 py-2 shadow-lg">
          <p className="text-xs text-muted-foreground">Loading initiatives...</p>
        </div>
      )}
    </div>
  );
};

export default Roadmap;
