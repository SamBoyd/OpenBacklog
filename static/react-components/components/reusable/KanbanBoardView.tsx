import React, { useCallback, useEffect } from 'react';
import {
    DragDropContext,
    Droppable,
    Draggable,
    DropResult,
} from '@hello-pangea/dnd';

import { ChecklistItemDto, InitiativeDto, TaskDto, TaskStatus, statusDisplay } from '#types';
import KanbanColumnHeader from './KanbanColumnHeader';
import ErrorToast from './ErrorToast';
import LoadingKanbanCard from './LoadingKanbanCard';
import UniversalKanbanCard from './UniversalKanbanCard';
import { OrderedEntity } from '#hooks/useOrderings';

const DEFAULT_COLUMN_LENGTH_LIMIT = 10;

type KanbanItem = InitiativeDto | TaskDto;

interface KanbanBoardViewProps<T extends KanbanItem> {
    data: OrderedEntity<T>[] | undefined;
    loading: boolean;
    error: Error | null;
    onCardClick: (item: OrderedEntity<T>) => void;
    onItemDrag: (item: OrderedEntity<T>, dropIndex: number) => void;
    type: 'task' | 'initiative';
    showBlocked?: boolean;
    disabled?: boolean;
    disabledMessage?: string;
    filterToStatus: string[];
}

const KanbanBoardView = <T extends KanbanItem>({
    data,
    loading,
    error,
    onCardClick,
    onItemDrag,
    type,
    disabled = false,
    disabledMessage,
    showBlocked = false,
    filterToStatus
}: KanbanBoardViewProps<OrderedEntity<T>>) => {
    const [reloadCounter, setReloadCounter] = React.useState(0);
    const [columnLimits, setColumnLimits] = React.useState<Record<string, number>>(() => {
        // Initialize each column with the default limit
        const limits: Record<string, number> = {};
        filterToStatus.forEach(status => {
            limits[status] = DEFAULT_COLUMN_LENGTH_LIMIT;
        });
        return limits;
    });

    useEffect(() => {
        setReloadCounter(prev => prev + 1);
    }, [data]);

    const handleCardClick = (item: OrderedEntity<T>) => {
        if (loading || error) return;
        onCardClick(item);
    };

    const handleDragEnd = (result: DropResult) => {
        if (!result.destination) return;
        
        const { source, destination } = result;
        if (source.droppableId === destination.droppableId && source.index === destination.index) return;

        // Find the dragged item
        const draggedItemId = result.draggableId;
        const draggedItem = data?.find(item => item.id.toString() === draggedItemId);
        
        if (!draggedItem) return;

        // Create updated item with new status
        const updatedItem = {
            ...draggedItem,
            status: destination.droppableId
        };

        onItemDrag(updatedItem, destination.index);
    };

    /**
     * Converts initiative tasks to checklist format for progress display
     */
    const convertTasksToChecklist = (tasks: Partial<TaskDto>[]): ChecklistItemDto[] => {
        return tasks.map((task, index) => ({
            id: task.id || `task-${index}`,
            title: task.title || 'Untitled task',
            is_complete: task.status === TaskStatus.DONE,
            task_id: task.id || '',
            order: index,
        }));
    };

    const renderCard = (item: T, index: number) => {
        if (item === null || item === undefined) {
            return <div key={`empty-${index}`}></div>;
        }

        let checklist: ChecklistItemDto[] = [];

        if (type === 'initiative') {
            // For initiatives, convert tasks to checklist format for progress display
            const initiative = item as unknown as InitiativeDto;
            if (initiative.tasks && initiative.tasks.length > 0) {
                checklist = convertTasksToChecklist(initiative.tasks);
            }
        } else if (type === 'task') {
            // For tasks, use their actual checklist items
            const task = item as unknown as TaskDto;
            if (task.checklist && task.checklist.length > 0) {
                checklist = task.checklist.map((checklistItem, index) => ({
                    id: checklistItem.id || '',
                    title: checklistItem.title || '',
                    is_complete: checklistItem.is_complete || false,
                    task_id: checklistItem.task_id || task.id,
                    order: checklistItem.order || index,
                }));
            }
        }

        return (
            <UniversalKanbanCard
                key={item.id}
                identifier={item.identifier}
                title={item.title}
                status={item.status as TaskStatus}
                checklist={checklist}
            />
        );
    };

    // Function to handle loading more cards for a specific column
    const handleLoadMore = (status: string) => {
        setColumnLimits(prev => ({
            ...prev,
            [status]: prev[status] + DEFAULT_COLUMN_LENGTH_LIMIT
        }));
    };

    // Filter data based on column limits
    const getFilteredDataForColumn = useCallback((status: string): OrderedEntity<T>[] => {
        if (loading || error) {
            // Return empty array for loading/error state - loading cards will be rendered separately
            return [];
        }
        if (!data) return [];

        // Get items for this status and apply column limit
        const statusItems = data.filter(item => item.status === status);
        return statusItems.slice(0, columnLimits[status]);
    }, [data, columnLimits, loading, error]);

    // Render a "Load more" button for a column if needed
    const renderLoadMoreButton = (status: string) => {
        if (loading || error) return null;

        const statusItems = data?.filter(item => item.status === status) || [];
        const hasMore = statusItems.length > columnLimits[status];

        if (!hasMore) return null;

        return (
            <div
                className={`
                    px-2 py-1 text-center cursor-pointer bg-transparent text-muted-foreground rounded-md
                    hover:bg-primary/5 hover:text-primary-foreground
                    transition-colors duration-200
                    text-xs mt-2
                `}
                onClick={() => handleLoadMore(status)}
            >
                Load more
            </div>
        );
    };

    const renderColumn = (status: string, index: number) => {
        const columnItems = getFilteredDataForColumn(status);
        const allStatusItems = data?.filter(item => item.status === status) || [];

        return (
            <div
                key={status}
                className="flex flex-col flex-1 min-w-0"
                data-testid={`kanban-column-${status}`}
            >
                {/* Column Header */}
                <KanbanColumnHeader
                    isFirstColumn={index==0}
                    isLastColumn={index==filterToStatus.length-1}
                    headerText={statusDisplay(status as TaskStatus)}
                    numberOfTasks={allStatusItems.length}
                />

                {/* Column Content */}
                <Droppable droppableId={status}>
                    {(provided, snapshot) => (
                        <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            className={`
                                flex-1 min-h-[200px] p-2 rounded-lg
                                ${snapshot.isDraggingOver ? 'bg-primary/5' : 'bg-transparent'}
                                transition-colors duration-200
                            `}
                        >
                            {loading || error ? (
                                // Loading/Error state
                                <>
                                    <LoadingKanbanCard />
                                    <LoadingKanbanCard />
                                </>
                            ) : (
                                // Normal state
                                <>
                                    {columnItems.map((item, itemIndex) => (
                                        <Draggable
                                            key={item.id}
                                            draggableId={item.id.toString()}
                                            index={itemIndex}
                                            isDragDisabled={disabled || loading || !!error}
                                        >
                                            {(provided, snapshot) => (
                                                <div
                                                    ref={provided.innerRef}
                                                    {...provided.draggableProps}
                                                    {...provided.dragHandleProps}
                                                    className={`
                                                        mb-3 cursor-pointer
                                                        ${snapshot.isDragging ? 'opacity-60 rotate-2' : ''}
                                                        ${disabled ? 'opacity-50' : ''}
                                                        transition-all duration-200
                                                    `}
                                                    onClick={() => handleCardClick(item as OrderedEntity<T>)}
                                                >
                                                    {renderCard(item as T, itemIndex)}
                                                </div>
                                            )}
                                        </Draggable>
                                    ))}
                                    
                                    {/* Empty state for column */}
                                    {columnItems.length === 0 && (
                                        <div className="text-center py-8 text-muted-foreground text-sm">
                                            {snapshot.isDraggingOver ? 'Drop here' : 'No items'}
                                        </div>
                                    )}
                                </>
                            )}
                            {provided.placeholder}
                        </div>
                    )}
                </Droppable>

                {/* Load More Button */}
                {renderLoadMoreButton(status)}
            </div>
        );
    };

    return (
        <div data-testid={`${type}-kanban-board`} className="mb-4">
            <DragDropContext onDragEnd={handleDragEnd}>
                <div className="flex overflow-x-auto">
                    {filterToStatus.map((status, index) => renderColumn(status, index))}
                </div>
            </DragDropContext>

            <ErrorToast error={error?.message || null} />
        </div>
    );
};

export default KanbanBoardView;