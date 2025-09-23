/**
 * Utility functions for drag-and-drop operations
 */

export interface OrderingIds {
    beforeId: string | null;
    afterId: string | null;
}

/**
 * Computes the beforeId and afterId for drag-and-drop ordering operations.
 * This utility encapsulates the common logic used across multiple components
 * for determining where an item should be positioned relative to other items.
 * 
 * @param items - Array of items that the dragged item will be positioned among
 * @param currentItemId - ID of the item being moved (will be filtered out)
 * @param newIndex - The target index position for the item
 * @returns Object containing beforeId and afterId for ordering
 */
export function computeOrderingIds<T extends { id: string | number }>(
    items: T[],
    currentItemId: string | number,
    newIndex: number
): OrderingIds {
    // Filter out the item being moved
    const filteredItems = items.filter(item => item.id !== currentItemId);
    
    // If no other items exist, no positioning needed
    if (filteredItems.length === 0) {
        return { beforeId: null, afterId: null };
    }
    
    let beforeId: string | null = null;
    let afterId: string | null = null;
    
    if (newIndex === 0) {
        // Moving to the beginning - set beforeId to first item
        beforeId = filteredItems[0].id.toString();
    } else if (newIndex >= filteredItems.length) {
        // Moving to the end - set afterId to last item
        afterId = filteredItems[filteredItems.length - 1].id.toString();
    } else {
        // Moving to middle - set both beforeId and afterId
        afterId = filteredItems[newIndex - 1].id.toString();
        beforeId = filteredItems[newIndex].id.toString();
    }
    
    return { beforeId, afterId };
}