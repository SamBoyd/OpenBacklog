import React from 'react'

import { TaskDto } from "#types"


interface TaskProgressBarProps {
    items: { title: string; is_complete: boolean }[]
    maxDots?: number
}

/**
 * TaskProgressBar component displays progress dots for checklist items.
 * @param {object} props - The component props
 * @param {Array} props.items - Array of checklist items with title and completion status
 * @param {number} [props.maxDots=6] - Maximum number of dots to display to prevent overflow
 * @returns {React.ReactElement|null} The progress bar component or null if no items
 */
const TaskProgressBar = ({ items, maxDots = 6 }: TaskProgressBarProps) => {

    if (!items || items.length === 0) {
        return null;
    }

    const totalItems = items.length;
    const completedItems = items.filter(item => item.is_complete).length;

    // Determine how many dots to show and how many should be completed
    const dotsToShow = Math.min(totalItems, maxDots);
    const completedDots = totalItems <= maxDots
        ? completedItems
        : Math.floor((completedItems / totalItems) * maxDots);

    return (
        <nav aria-label="Progress" className="flex items-center justify-center">
            <ol role="list" className="flex items-center space-x-5 px-2">
                {[...Array(dotsToShow)].map((_, i) => (
                    <li key={i}>
                        {i < completedDots ? (
                            <div className="block h-2 w-2 border rounded-full border-primary bg-primary" >
                                <span className="sr-only">Step {i + 1} of {dotsToShow}</span>
                            </div>
                        ) : (
                            <div className="block h-2 w-2 border border-muted rounded-full">
                                <span className="sr-only">Step {i + 1} of {dotsToShow}</span>
                            </div>
                        )}
                    </li>
                ))}
            </ol>
        </nav>
    )
}


export default TaskProgressBar;
