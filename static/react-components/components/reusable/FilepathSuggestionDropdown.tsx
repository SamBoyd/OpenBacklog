import React, { useEffect, useRef } from 'react';

/**
 * Props interface for the FilepathSuggestionDropdown component
 */
interface FilepathSuggestionDropdownProps {
    /** Array of filepath suggestions to display */
    suggestions: string[];
    /** Whether suggestions are currently loading */
    isLoading: boolean;
    /** Error state if suggestion fetching failed */
    error: Error | null;
    /** Whether the dropdown should be visible */
    isVisible: boolean;
    /** Index of the currently highlighted suggestion */
    highlightedIndex: number;
    /** Callback when a suggestion is selected */
    onSelect: (suggestion: string) => void;
    /** Callback when the dropdown should be closed */
    onClose: () => void;
    /** Callback when the highlighted index should be updated */
    onHighlightChange: (index: number) => void;
    /** Position for the dropdown relative to the textarea */
    position: {
        top: number;
        left: number;
    };
    /** Search query to highlight within suggestions */
    searchQuery: string;
}

/**
 * Highlights the search query within a filepath suggestion
 * @param suggestion - The full filepath suggestion
 * @param query - The search query to highlight
 * @returns JSX with highlighted text
 */
const highlightSearchQuery = (suggestion: string, query: string): React.ReactNode => {
    if (!query.trim()) {
        return suggestion;
    }

    const parts = suggestion.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) =>
        part.toLowerCase() === query.toLowerCase() ? (
            <span key={index} className="bg-primary/30 text-primary-foreground rounded-sm px-0.5">
                {part}
            </span>
        ) : (
            part
        )
    );
};

/**
 * A specialized dropdown component for displaying filepath suggestions
 *
 * This component provides:
 * - Keyboard navigation (arrows, enter, escape)
 * - Click-outside-to-close behavior
 * - Proper positioning relative to textarea cursor
 * - Search query highlighting
 * - Loading and error states
 *
 * @param props - Component props
 * @returns The FilepathSuggestionDropdown component
 */
export const FilepathSuggestionDropdown: React.FC<FilepathSuggestionDropdownProps> = ({
    suggestions,
    isLoading,
    error,
    isVisible,
    highlightedIndex,
    onSelect,
    onClose,
    onHighlightChange,
    position,
    searchQuery,
}) => {
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                onClose();
            }
        };

        if (isVisible) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => {
                document.removeEventListener('mousedown', handleClickOutside);
            };
        }

        // Return empty cleanup function when not visible
        return () => {};
    }, [isVisible, onClose]);

    // Scroll highlighted item into view
    useEffect(() => {
        if (isVisible && highlightedIndex >= 0 && dropdownRef.current) {
            const highlightedElement = dropdownRef.current.querySelector(
                `[data-suggestion-index="${highlightedIndex}"]`
            ) as HTMLElement;

            if (highlightedElement) {
                highlightedElement.scrollIntoView({
                    block: 'nearest',
                    behavior: 'smooth'
                });
            }
        }
    }, [isVisible, highlightedIndex]);

    if (!isVisible) {
        return null;
    }

    return (
        <div
            ref={dropdownRef}
            className="fixed z-50 w-96 h-64 border border-red flex flex-col justify-between bg-background border border-border rounded-md shadow-lg overflow-hidden"
            style={{
                top: position.top,
                left: position.left,
            }}
        >
            {/* Loading state */}
            {isLoading && (
                <div className="px-3 py-2 text-sm text-muted-foreground flex items-center">
                    <div className="animate-pulse mr-2">Loading...</div>
                </div>
            )}

            {/* Error state */}
            {error && !isLoading && (
                <div className="px-3 py-2 text-sm text-destructive">
                    Failed to load file suggestions
                </div>
            )}

            {/* Suggestions list */}
            {!isLoading && !error && suggestions.length > 0 && (
                <div className="h-58 overflow-y-auto">
                    {suggestions.map((suggestion, index) => (
                        <div
                            key={`${suggestion}-${index}`}
                            data-suggestion-index={index}
                            className={`
                                px-3 py-2 cursor-pointer text-sm border-b border-border/30 last:border-b-0
                                transition-colors duration-150
                                ${index === highlightedIndex
                                    ? 'bg-primary text-primary-foreground'
                                    : 'hover:bg-muted text-foreground'
                                }
                            `}
                            onClick={() => onSelect(suggestion)}
                            onMouseEnter={() => onHighlightChange(index)}
                        >
                            <div className="font-mono text-xs break-all">
                                {highlightSearchQuery(suggestion, searchQuery)}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Empty state */}
            {!isLoading && !error && suggestions.length === 0 && searchQuery.trim() && (
                <div className="px-3 py-2 text-sm text-muted-foreground">
                    No files found matching "{searchQuery}"
                </div>
            )}

            {/* Help text */}
            {!isLoading && !error && suggestions.length > 0 && (
                <div className="px-3 py-1 text-xs text-muted-foreground bg-muted/30 border-t border-border/30">
                    ↑↓ navigate • Enter select • Esc close
                </div>
            )}
        </div>
    );
};

export default FilepathSuggestionDropdown;