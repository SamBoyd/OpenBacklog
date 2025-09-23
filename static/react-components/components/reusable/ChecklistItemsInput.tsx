import React, { useEffect, useState, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { ChecklistItemDto } from '../../types';
import { Button } from './Button';
import { Input } from './Input';
import ChecklistOverlay from './ChecklistOverlay';
import ChecklistSkeleton from './ChecklistSkeleton';
import { GripVertical } from 'lucide-react';

type ChecklistItemsInputProps = {
    items: Partial<ChecklistItemDto>[];
    disabled?: boolean;
    showOverlay?: boolean;
    onOverlayManualEdit?: () => void;
    documentationUrl?: string;
    
    // Granular operations (required)
    taskId: string;
    onUpdateItem: (taskId: string, itemId: string, updates: Partial<ChecklistItemDto>) => Promise<ChecklistItemDto>;
    onUpdateItemDebounced: (taskId: string, itemId: string, updates: Partial<ChecklistItemDto>, debounceMs?: number) => Promise<ChecklistItemDto>;
    onAddItem: (taskId: string, item: Omit<ChecklistItemDto, 'id' | 'task_id'>) => Promise<ChecklistItemDto>;
    onRemoveItem: (taskId: string, itemId: string) => Promise<void>;
    onReorderItems: (taskId: string, items: Array<Partial<ChecklistItemDto>>) => Promise<Partial<ChecklistItemDto>[]>;
};


const Checkbox = (props: { checked: boolean, disabled: boolean, onChange: (event: any) => void }) => (
    <div className="flex gap-3">
        <div className="flexshrink-0 items-center">
            <div className="group grid size-6 grid-cols-1">
                <input
                    id="comments"
                    name="comments"
                    type="checkbox"
                    aria-describedby="comments-description"
                    size={20}
                    className={
                        `col-start-1 row-start-1 appearance-none rounded border cursor-pointer
                         bg-background focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2
                       focus-visible:outline-indigo-600 disabled:border-muted disabled:text-muted
                         `}
                    {...props}
                />
                <svg
                    fill="none"
                    viewBox="0 0 14 14"
                    className={
                        `pointer-events-none col-start-1 row-start-1 size-3.5 self-center justify-self-center 
                         stroke-foreground group-has-[:disabled]:stroke-muted`
                    }
                >
                    <path
                        d="M3 8L6 11L11 3.5"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="opacity-0 group-has-[:checked]:opacity-100"
                    />
                    <path
                        d="M3 7H11"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="opacity-0 group-has-[:indeterminate]:opacity-100"
                    />
                </svg>
            </div>
        </div>
    </div >
)

interface DeleteButtonProps {
    onClick: (event: React.MouseEvent) => void;
    disabled?: boolean;
}
const DeleteButton = ({ onClick, disabled }: DeleteButtonProps) => (
    <Button
        onClick={onClick}
        disabled={disabled}
        className='h-full stroke-foreground'
    >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} className="size-3.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
    </Button>
)

const ChecklistItemsInput: React.FC<ChecklistItemsInputProps> = ({
    items,
    disabled,
    showOverlay = true,
    onOverlayManualEdit,
    documentationUrl,
    taskId,
    onUpdateItem,
    onUpdateItemDebounced,
    onAddItem,
    onRemoveItem,
    onReorderItems
}) => {
    const [newChecklistItem, setNewChecklistItem] = useState({ title: '', order: 0, is_complete: false });
    const [localTitles, setLocalTitles] = useState(items.map(item => item.title));

    // Create a sorted copy without mutating the original array
    const sortedItems: Partial<ChecklistItemDto>[] = [...items].sort((a, b) => {
        const orderA = a.order ?? 0;
        const orderB = b.order ?? 0;
        return orderA - orderB;
    });

    // Calculate the next order value for new items
    const getNextOrder = useCallback(() => {
        if (sortedItems.length === 0) return 0;
        const maxOrder = Math.max(...sortedItems.map(item => item.order ?? 0));
        return maxOrder + 1;
    }, [sortedItems]);

    // Rebalance order values to ensure sequential ordering
    const rebalanceOrders = useCallback((itemsToRebalance: Partial<ChecklistItemDto>[]): Partial<ChecklistItemDto>[] => {
        return itemsToRebalance.map((item, index) => ({
            ...item,
            order: index
        }));
    }, []);

    useEffect(() => {
        setLocalTitles(sortedItems.map(item => item.title));
    }, [items]);

    const handleItemChange = async (index: number, key: string, value: string | number | boolean) => {
        const itemToUpdate = sortedItems[index];
        
        if (itemToUpdate.id) {
            try {
                await onUpdateItem(taskId, itemToUpdate.id, { ...itemToUpdate, [key]: value });
                console.log('[ChecklistItemsInput] onUpdateItem completed successfully');
            } catch (error) {
                console.error('Failed to update checklist item:', error);
            }
        }
    };

    const handleRemoveItem = async (index: number) => {
        const itemToRemove = sortedItems[index];
        
        if (itemToRemove.id) {
            try {
                await onRemoveItem(taskId, itemToRemove.id);
            } catch (error) {
                console.error('Failed to remove checklist item:', error);
            }
        }
    };

    const handleBlur = async (index: number) => {
        // Blur on new checklist item
        if (index === sortedItems.length - 1 && newChecklistItem.title.trim() !== '') {
            try {
                const nextOrder = getNextOrder();
                await onAddItem(taskId, {
                    title: newChecklistItem.title,
                    order: nextOrder,
                    is_complete: newChecklistItem.is_complete
                });
                setNewChecklistItem({ title: '', order: nextOrder + 1, is_complete: false });
            } catch (error) {
                console.error('Failed to add checklist item:', error);
            }
        } else if (index < sortedItems.length) {
            // Blur on existing checklist item - use debounced update for title changes
            const itemToUpdate = sortedItems[index];
            const newTitle = localTitles[index];
            
            if (itemToUpdate.id && newTitle !== itemToUpdate.title) {
                try {
                    await onUpdateItemDebounced(taskId, itemToUpdate.id, { title: newTitle });
                } catch (error) {
                    console.error('Failed to update checklist item title:', error);
                }
            }
        }
    };

    const handleKeyDown = async (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && newChecklistItem.title.trim() !== '') {
            try {
                const nextOrder = getNextOrder();
                await onAddItem(taskId, {
                    title: newChecklistItem.title,
                    order: nextOrder,
                    is_complete: newChecklistItem.is_complete
                });
                setNewChecklistItem({ title: '', order: nextOrder + 1, is_complete: false });
            } catch (error) {
                console.error('Failed to add checklist item:', error);
            }
        }
    };

    const handleNewChecklistItemChange = (key: string, value: string | number | boolean) => {
        setNewChecklistItem({ ...newChecklistItem, [key]: value });
    };

    // Drag and drop handler for reordering using @hello-pangea/dnd
    const handleDragEnd = async (result: DropResult) => {
        if (!result.destination) {
            return;
        }

        const sourceIndex = result.source.index;
        const destinationIndex = result.destination.index;

        if (sourceIndex === destinationIndex) {
            return;
        }

        const newItems: Partial<ChecklistItemDto>[] = [...sortedItems];
        const draggedItem = newItems[sourceIndex];

        // Remove the dragged item
        newItems.splice(sourceIndex, 1);

        // Insert at the new position
        newItems.splice(destinationIndex, 0, draggedItem);

        // Rebalance orders
        const rebalancedItems: Partial<ChecklistItemDto>[] = rebalanceOrders(newItems);

        try {
            const reorderData: Partial<ChecklistItemDto>[] = rebalancedItems.map((item, index) => ({
                ...item,
                order: index
            })).filter(item => item.id); // Filter out items without IDs
            
            await onReorderItems(taskId, reorderData);
        } catch (error) {
            console.error('Failed to reorder checklist items:', error);
        }
    };

    // Show overlay when no items exist and overlay is enabled
    if (items.length === 0 && showOverlay && onOverlayManualEdit) {
        return (
            <div className="relative">
                <ChecklistOverlay
                    onManualEdit={onOverlayManualEdit}
                    documentationUrl={documentationUrl}
                />
                <div className="p-4 absolute inset-0">
                    <ChecklistSkeleton itemCount={10} animated={false} />
                </div>
            </div>
        );
    }

    return (
        <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="checklist-items">
                {(provided, snapshot) => (
                    <div
                        {...provided.droppableProps}
                        ref={provided.innerRef}
                        className="flex flex-col gap-2"
                    >
                        {sortedItems.map((item, index) => (
                            <Draggable
                                key={item.id || index}
                                draggableId={item.id?.toString() || index.toString()}
                                index={index}
                                isDragDisabled={disabled}
                            >
                                {(provided, snapshot) => (
                                    <div
                                        ref={provided.innerRef}
                                        {...provided.draggableProps}
                                        className={`w-full flex flex-row items-center gap-2 rounded-md transition-colors ${snapshot.isDragging ? 'opacity-50 bg-muted' : 'hover:bg-muted/50'
                                            } ${disabled ? 'cursor-not-allowed' : 'cursor-move'}`}
                                    >

                                        <div className="flex items-center gap-2">
                                            {!disabled && (
                                                <div
                                                    {...provided.dragHandleProps}
                                                    className="text-muted-foreground cursor-move"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} className="size-4">
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                                                    </svg>
                                                </div>
                                            )}

                                            <Checkbox
                                                checked={item.is_complete || false}
                                                onChange={(e) => handleItemChange(index, 'is_complete', e.target.checked)}
                                                disabled={disabled || false}
                                            />
                                        </div>
                                        <Input
                                            type="text"
                                            value={localTitles[index] || ''}
                                            onChange={(e) => setLocalTitles(prev => {
                                                const newTitles = [...prev];
                                                newTitles[index] = e.target.value;
                                                return newTitles;
                                            })}
                                            onBlur={() => {
                                                handleBlur(index)
                                            }}
                                            onKeyDown={handleKeyDown}
                                            disabled={disabled}
                                            className="flex-1"
                                        />
                                        <DeleteButton onClick={() => handleRemoveItem(index)} disabled={disabled} />
                                    </div>
                                )}
                            </Draggable>
                        ))}

                        {provided.placeholder}

                        <div className="w-full flex flex-row items-center gap-2 rounded-md hover:bg-muted/30 transition-colors">
                            <div className="flex items-center gap-2">
                                <div className="w-4"></div>
                                <Checkbox
                                    checked={newChecklistItem.is_complete}
                                    onChange={(e) => handleNewChecklistItemChange('is_complete', e.target.checked)}
                                    disabled={disabled || false}
                                />
                            </div>
                            <Input
                                type="text"
                                value={newChecklistItem.title || ''}
                                onChange={(e) => handleNewChecklistItemChange('title', e.target.value)}
                                onBlur={() => handleBlur(items.length - 1)}
                                onKeyDown={handleKeyDown}
                                placeholder="Add new item"
                                disabled={disabled}
                                className="flex-1"
                            />
                            <DeleteButton onClick={() => { }} disabled />
                        </div>
                    </div>
                )}
            </Droppable>
        </DragDropContext>
    );
};

export default ChecklistItemsInput;
