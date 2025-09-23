import React from 'react';
import { Skeleton } from './Skeleton';

interface ChecklistSkeletonProps {
    itemCount?: number;
    className?: string;
    animated?: boolean;
}

/**
 * Skeleton loading component that displays placeholder checklist items
 * to preview what a populated checklist would look like.
 * @param {object} props - The component props
 * @param {number} [props.itemCount=3] - Number of skeleton items to display
 * @param {string} [props.className] - Additional CSS classes
 * @param {boolean} [props.animated=true] - Whether to animate with pulse effect
 * @returns {React.ReactElement} The skeleton checklist component
 */
const ChecklistSkeleton: React.FC<ChecklistSkeletonProps> = ({
    itemCount = 3,
    className = '',
    animated = true
}) => {
    const items = Array.from({ length: itemCount }, (_, index) => index);
    const pulseClass = animated ? ' animate-pulse' : '';

    return (
        <div className={`space-y-2 opacity-50 ${className}`} data-testid="checklist-skeleton">
            {items.map((index) => (
                <div key={index} className="w-full flex flex-row items-center gap-2">
                    {/* Checkbox skeleton */}
                    <div className="flex-shrink-0">
                        <div className={`size-6 rounded border border-muted bg-muted/20${pulseClass}`} />
                    </div>
                    
                    {/* Text skeleton with varying widths for natural look */}
                    <div className="flex-1">
                        <Skeleton 
                            type="text" 
                            width={
                                index === 0 ? 'w-3/4' : 
                                index === 1 ? 'w-full' : 
                                index === 2 ? 'w-5/6' : 
                                'w-4/5'
                            }
                            height="h-4"
                            animated={animated}
                        />
                    </div>
                    
                    {/* Delete button skeleton */}
                    <div className="flex-shrink-0">
                        <div className={`size-6 rounded border border-muted bg-muted/20${pulseClass}`} />
                    </div>
                </div>
            ))}
            
            {/* "Add new item" skeleton */}
            <div className="w-full flex flex-row items-center gap-2 opacity-60">
                <div className="flex-shrink-0">
                    <div className={`size-6 rounded border border-muted bg-muted/20${pulseClass}`} />
                </div>
                <div className="flex-1">
                    <Skeleton type="text" width="w-1/2" height="h-4" animated={animated} />
                </div>
                <div className="flex-shrink-0">
                    <div className={`size-6 rounded border border-muted bg-muted/20${pulseClass} opacity-30`} />
                </div>
            </div>
        </div>
    );
};

export default ChecklistSkeleton;