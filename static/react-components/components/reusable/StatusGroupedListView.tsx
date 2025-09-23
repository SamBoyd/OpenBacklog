import React, { ReactNode, useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { InitiativeDto, InitiativeStatus, TaskDto, TaskStatus, statusDisplay } from '#types';
import ErrorToast from './ErrorToast';
import Card from './Card';
import { OrderedEntity } from '#hooks/useOrderings';
import { LexoRank } from 'lexorank';
import { computeOrderingIds } from '#utils/dragDropUtils';

export interface GroupHeaderProps {
    status: TaskStatus;
    itemCount: number;
}

export interface StatusGroupedListViewProps<T extends InitiativeDto | TaskDto> {
    items: OrderedEntity<T>[] | null | undefined;
    loading: boolean;
    error: string | null;
    emptyStateMessage: string;
    showEmptyState: boolean;
    renderItem: (item: any, onItemClick: (id: string) => void) => ReactNode;
    renderLoadingItem: () => ReactNode;
    onItemClick: (id: string) => void;
    selectedStatuses: string[];
    dataTestId?: string;
    onOrderChange?: (updatedEntity: OrderedEntity<T>, afterId: string | null, beforeId: string | null) => void;
    onStatusChange?: (updatedEntity: OrderedEntity<T>, newStatus: InitiativeStatus, afterId: string | null, beforeId: string | null) => void;
}

/**
 * A reusable component for displaying lists grouped by status with drag and drop support
 * 
 * @param {StatusGroupedListViewProps} props - The component props
 * @returns {React.ReactElement} The rendered list view
 */
export default function StatusGroupedListView<T extends InitiativeDto | TaskDto>({
    items,
    loading,
    error,
    emptyStateMessage,
    showEmptyState,
    renderItem,
    renderLoadingItem,
    onItemClick,
    selectedStatuses,
    dataTestId = 'status-grouped-list',
    onOrderChange,
    onStatusChange
}: StatusGroupedListViewProps<T>) {

    const [orderedItems, setOrderedItems] = useState<OrderedEntity<T>[]>(items || []);

    // Update orderedItems when items prop changes
    useEffect(() => {
        setOrderedItems(items || []);
    }, [items]);

    /**
     * Handles the end of a drag operation
     * @param {DropResult} result - The drag result from @hello-pangea/dnd
     */
    const handleDragEnd = (result: DropResult) => {
        if (!result.destination) return;

        const { source, destination } = result;
        if (source.droppableId === destination.droppableId && source.index === destination.index) return;

        const sourceStatus = source.droppableId as InitiativeStatus;
        const destinationStatus = destination.droppableId as InitiativeStatus;

        // Get all items for manipulation
        const allItems = [...orderedItems];

        if (allItems.length === 1) {
            return
        }

        // Find the item being moved
        const sourceItems = allItems.filter(item => item.status === sourceStatus);
        const movedItem = sourceItems[source.index];

        if (!movedItem) return;

        // Get destination items for the target status
        const orderedItemsInStatus = allItems.filter(
            item => item.status === destinationStatus
        );

        const newIndex = destination.index;
        const { beforeId, afterId } = computeOrderingIds(orderedItemsInStatus, movedItem.id, newIndex);

        if (sourceStatus !== destinationStatus && onStatusChange) {
            onStatusChange(movedItem, destinationStatus, afterId, beforeId);
        }
        if (onOrderChange) {
            onOrderChange(movedItem, afterId, beforeId);
        }
    };

    const GroupHeader = ({ status, itemCount }: GroupHeaderProps) => (
        <div
            className={`
                text-sm rounded bg-transparent py-1.5 px-3 text-foreground mt-4
                focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent focus:bg-background/80
                bg-gradient-to-br from-primary/10 via-transparent to-transparent
                `}
            data-testid={`group-header-${status}`}
        >
            {statusDisplay(status)} {itemCount > 0 && `(${itemCount})`}
        </div>
    );

    if (showEmptyState && !loading && !error && items?.length === 0) {
        return (
            <div className="h-full w-full flex-grow flex flex-col justify-between gap-2 rounded-lg">
                {/* Empty State */}
                {showEmptyState && !loading && !error && items?.length === 0 && (
                    <Card
                        dataTestId="empty-state"
                        className="w-full px-3 py-10 flex flex-row justify-center border border-muted-foreground/20 rounded "
                    >
                        <span className="text-muted-foreground/20">
                            {emptyStateMessage}
                        </span>
                    </Card>
                )}
            </div>
        );
    }

    return (
        <div className="h-full w-full flex-grow flex flex-col justify-between gap-2 rounded-lg mb-4">
            {/* Items List */}
            <nav
                aria-label="Items Directory"
                className="h-full"
                data-testid={dataTestId}
            >
                <DragDropContext onDragEnd={handleDragEnd}>
                    {selectedStatuses.map((groupStatus) => {
                        const itemsInGroup = orderedItems?.filter(
                            (item) => item.status === groupStatus
                        ) || [];

                        return (
                            <div key={groupStatus} data-testid={`group-${groupStatus}`}>
                                <GroupHeader status={groupStatus as TaskStatus} itemCount={itemsInGroup.length} />

                                {(loading || error) ? (
                                    <div
                                        role="list"
                                        className="gap-2"
                                        data-testid="loading-group"
                                    >
                                        {renderLoadingItem()}
                                        {renderLoadingItem()}
                                    </div>
                                ) : (
                                    <Droppable droppableId={groupStatus}>
                                        {(provided, snapshot) => (
                                            <div
                                                role="list"
                                                className={`min-h-[2rem] ${snapshot.isDraggingOver ? 'bg-primary/5' : ''}`}
                                                data-testid="group-list"
                                                ref={provided.innerRef}
                                                {...provided.droppableProps}
                                            >
                                                {itemsInGroup.length === 0 ? (
                                                    <div className="h-[3rem] rounded my-2 flex items-center justify-center border-2 border-dashed border-transparent">
                                                        <span className="text-muted-foreground text-sm">
                                                            {snapshot.isDraggingOver ? 'Drop here' : 'No items in this status'}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    itemsInGroup.map((item, index) => (
                                                        <Draggable
                                                            key={item.id}
                                                            draggableId={item.id.toString()}
                                                            index={index}
                                                            isDragDisabled={loading || !!error}
                                                        >
                                                            {(draggableProvided, draggableSnapshot) => (
                                                                <div
                                                                    ref={draggableProvided.innerRef}
                                                                    {...draggableProvided.draggableProps}
                                                                    {...draggableProvided.dragHandleProps}
                                                                    className={`${draggableSnapshot.isDragging ? 'opacity-70' : ''
                                                                        } ${!loading && !error ? 'cursor-move' : ''}`}
                                                                >
                                                                    {renderItem(item, onItemClick)}
                                                                </div>
                                                            )}
                                                        </Draggable>
                                                    ))
                                                )}
                                                {provided.placeholder}
                                            </div>
                                        )}
                                    </Droppable>
                                )}
                            </div>
                        );
                    })}
                </DragDropContext>
            </nav>

            {/* Error Toast */}
            <ErrorToast error={error} />
        </div>
    );
} 