import React from 'react';
import { TaskStatus, statusDisplay } from '#types';
import { Button } from '#components/reusable/Button';

/**
 * Props for the StatusFilter component.
 * @param {string[]} availableStatuses - All possible statuses to filter by.
 * @param {string[]} selectedStatuses - The currently selected statuses.
 * @param {(status: string) => void} onStatusToggle - Function called when a status is toggled.
 * @param {() => void} onClose - Function to close the filter view.
 */
interface StatusFilterProps {
    availableStatuses: string[];
    selectedStatuses: string[];
    onStatusToggle: (status: string) => void;
    onClose: () => void;
}

/**
 * A component to display filtering options for Initiatives, starting with TaskStatus.
 * Renders as a popover/card when active.
 * @param {StatusFilterProps} props - The component props.
 * @returns {React.ReactElement} The filter component.
 */
const StatusFilter: React.FC<StatusFilterProps> = ({
    availableStatuses,
    selectedStatuses,
    onStatusToggle,
    onClose,
}) => {
    const handleToggle = (status: string) => {
        onStatusToggle(status);
    };

    return (
        <>
            <div onClick={onClose} className="fixed inset-0 z-20 w-full h-full"> </div>
            <div className="absolute top-full right-0 mt-2 z-30 w-64 shadow-lg rounded border border-border bg-background text-card-foreground">
                <div className="p-4">
                    <div className="flex justify-between items-center mb-3">
                        <h3 className="text-foreground">Status</h3>
                        <Button onClick={onClose} className="p-1 h-auto" title="Close filter">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                            </svg>
                        </Button>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {availableStatuses.map((status) => {
                            const isSelected = selectedStatuses.includes(status);
                            return (
                                <button
                                    key={status}
                                    onClick={() => handleToggle(status)}
                                    className={`
                                    px-3 py-1 rounded-full text-sm border
                                    ${isSelected
                                            ? 'bg-background text-foreground border-border'
                                            : 'bg-muted/5 text-muted-foreground border-border/10 hover:bg-primary/90 hover:text-accent-foreground'
                                        }
                                    transition-colors duration-150 ease-in-out
                                `}
                                    aria-pressed={isSelected}
                                    data-testid={`filter-status-${status}`}
                                >
                                    {statusDisplay(status)}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </div>
        </>
    );
};

export default StatusFilter;
