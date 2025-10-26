import React from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useThemePrioritization } from '#hooks/useThemePrioritization';

/**
 * Sidebar component displaying prioritized and unprioritized roadmap themes
 *
 * This component fetches and displays themes using the Roadmap Intelligence Context.
 * Themes are automatically separated into:
 * - Prioritized: Themes currently being actively worked on
 * - Unprioritized: Themes in the backlog
 *
 * The component manages its own data fetching via hooks and displays loading/error states.
 */
const ThemeSidebar: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const {
    prioritizedThemes,
    unprioritizedThemes,
    isLoading,
    prioritizedError,
    unprioritizedError,
    prioritizeTheme,
    isPrioritizing,
    deprioritizeTheme,
    isDeprioritizing,
    reorderPrioritizedThemes,
    isReordering,
  } = useThemePrioritization(currentWorkspace?.id || '');

  const error = prioritizedError || unprioritizedError;

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
      <div className="w-60 flex-shrink-0 border-r border-border bg-card">
        <div className="flex flex-col h-full items-center justify-center p-4">
          <p className="text-sm text-destructive text-center">
            Failed to load themes
          </p>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="w-60 flex-shrink-0 border-r border-border bg-card">
        <div className="flex flex-col h-full items-center justify-center p-4">
          <p className="text-sm text-muted-foreground">Loading themes...</p>
        </div>
      </div>
    );
  }

  const isDragDisabled = isLoading || isPrioritizing || isDeprioritizing || isReordering;

  return (
    <div className="w-60 flex-shrink-0 border-r border-border bg-card">
      <div className="flex flex-col h-full">
        <DragDropContext onDragEnd={handleDragEnd}>
          {/* Prioritized Themes Section */}
          {(prioritizedThemes.length > 0 || unprioritizedThemes.length > 0) && (
            <div className="px-4 py-3">
              <h3 className="text-sm font-semibold text-muted-foreground mb-2">
                Prioritized Themes
              </h3>
              <Droppable droppableId="prioritized">
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className={`min-h-[3rem] space-y-1 ${
                      snapshot.isDraggingOver ? 'bg-primary/5 rounded-md' : ''
                    }`}
                  >
                    {prioritizedThemes.length === 0 ? (
                      <div className="flex items-center justify-center h-[3rem] border-2 border-dashed border-border/50 rounded-md">
                        <span className="text-xs text-muted-foreground">
                          {snapshot.isDraggingOver ? 'Drop here to prioritize' : 'Drag themes here'}
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
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className={`px-3 py-2 rounded-md transition-all ${
                                snapshot.isDragging
                                  ? 'opacity-60 rotate-1 shadow-lg bg-accent'
                                  : 'hover:bg-accent'
                              } ${
                                isDragDisabled
                                  ? 'opacity-50 cursor-not-allowed'
                                  : 'cursor-grab active:cursor-grabbing'
                              }`}
                            >
                              <div className="text-sm font-medium text-foreground">
                                {theme.name}
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          )}

          {/* Divider between prioritized and unprioritized */}
          {(prioritizedThemes.length > 0 || unprioritizedThemes.length > 0) && (
            <div className="border-t border-border" />
          )}

          {/* Unprioritized Themes Section */}
          {(prioritizedThemes.length > 0 || unprioritizedThemes.length > 0) && (
            <div className="px-4 py-3">
              <h3 className="text-sm font-semibold text-muted-foreground mb-2">
                Unprioritized
              </h3>
              <Droppable droppableId="unprioritized">
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className={`min-h-[3rem] space-y-1 ${
                      snapshot.isDraggingOver ? 'bg-primary/5 rounded-md' : ''
                    }`}
                  >
                    {unprioritizedThemes.length === 0 ? (
                      <div className="flex items-center justify-center h-[3rem] border-2 border-dashed border-border/50 rounded-md">
                        <span className="text-xs text-muted-foreground">
                          {snapshot.isDraggingOver ? 'Drop here to deprioritize' : 'Drag themes here'}
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
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              className={`px-3 py-2 rounded-md transition-all opacity-70 ${
                                snapshot.isDragging
                                  ? 'opacity-40 rotate-1 shadow-lg bg-accent'
                                  : 'hover:bg-accent'
                              } ${
                                isDragDisabled
                                  ? 'opacity-30 cursor-not-allowed'
                                  : 'cursor-grab active:cursor-grabbing'
                              }`}
                            >
                              <div className="text-sm font-medium text-foreground">
                                {theme.name}
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          )}

          {/* Empty state */}
          {prioritizedThemes.length === 0 && unprioritizedThemes.length === 0 && (
            <div className="flex flex-col h-full items-center justify-center p-4">
              <p className="text-sm text-muted-foreground text-center">
                No themes yet
              </p>
            </div>
          )}
        </DragDropContext>
      </div>
    </div>
  );
};

export default ThemeSidebar;
