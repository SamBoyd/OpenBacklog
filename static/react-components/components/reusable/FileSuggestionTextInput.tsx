import React, { useEffect, useRef, useState, useCallback } from 'react';

import { Skeleton } from './Skeleton';
import { FilepathSuggestionDropdown } from './FilepathSuggestionDropdown';
import { useFilepathSuggestionFetching } from '#hooks/useFilepathSuggestionFetching';

interface FileSuggestionTextInputProps {
    id?: string;
    value: string;
    onChange: (value: string) => void;
    loading?: boolean;
    className?: string;
    placeholder?: string;
    testId?: string;
    initialRows?: number;
    disabled?: boolean;
    useRef?: React.RefObject<HTMLTextAreaElement>;
    submitOnEnter?: boolean;
    onKeyDown?: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
    onBlur?: () => void;
}

/**
 * Interface representing the filepath suggestion context
 */
interface FilepathSuggestionContext {
    /** The search query after the @ symbol */
    searchQuery: string;
    /** Start position of the @ symbol in the text */
    startPosition: number;
    /** End position of the current search (cursor position) */
    endPosition: number;
}

/**
 * Detects if the cursor is in filepath suggestion mode (after @ symbol)
 * @param text - The full text content
 * @param cursorPosition - Current cursor position
 * @returns Filepath suggestion context or null if not in suggestion mode
 */
const detectFilepathMode = (text: string, cursorPosition: number): FilepathSuggestionContext | null => {
    // Find last @ symbol before cursor
    const beforeCursor = text.substring(0, cursorPosition);
    const lastAtIndex = beforeCursor.lastIndexOf('@');

    if (lastAtIndex === -1) return null;

    // Extract text after @ until whitespace or end of text
    const afterAt = text.substring(lastAtIndex + 1, cursorPosition);
    const hasWhitespace = /\s/.test(afterAt);

    return hasWhitespace ? null : {
        searchQuery: afterAt,
        startPosition: lastAtIndex,
        endPosition: cursorPosition
    };
};

/**
 * Calculates the position for the dropdown relative to the textarea cursor
 * @param textAreaRef - Reference to the textarea element
 * @param atPosition - Position of the @ symbol in the text
 * @returns Position object with top and left coordinates
 */
const calculateDropdownPosition = (
    textAreaRef: React.RefObject<HTMLTextAreaElement>,
    atPosition: number
): { top: number; left: number } => {
    if (!textAreaRef.current) {
        return { top: 0, left: 0 };
    }

    const textarea = textAreaRef.current;
    const textBeforeAt = textarea.value.substring(0, atPosition);

    // Create a temporary element to measure text dimensions
    const tempElement = document.createElement('div');
    tempElement.style.cssText = window.getComputedStyle(textarea).cssText;
    tempElement.style.position = 'absolute';
    tempElement.style.visibility = 'hidden';
    tempElement.style.height = 'auto';
    tempElement.style.width = textarea.clientWidth + 'px';
    tempElement.style.whiteSpace = 'pre-wrap';
    tempElement.style.wordWrap = 'break-word';
    tempElement.textContent = textBeforeAt;

    document.body.appendChild(tempElement);

    const textareaRect = textarea.getBoundingClientRect();
    const tempRect = tempElement.getBoundingClientRect();

    // Calculate position
    const top = textareaRect.top + tempRect.height + window.scrollY + 25; // Add some padding
    const left = textareaRect.left + window.scrollX;

    document.body.removeChild(tempElement);

    return { top, left };
};

const FileSuggestionTextInput: React.FC<FileSuggestionTextInputProps> = ({
    id,
    value,
    onChange,
    loading = false,
    className,
    placeholder = "",
    testId = "title-input",
    initialRows = null,
    disabled = false,
    useRef: providedRef,
    onKeyDown,
    submitOnEnter = false,
    onBlur,
}) => {
    const textAreaRef = useRef<HTMLTextAreaElement>(null);
    const activeTextAreaRef = providedRef ?? textAreaRef;

    // Filepath suggestion state
    const [filepathContext, setFilepathContext] = useState<FilepathSuggestionContext | null>(null);
    const [dropdownPosition, setDropdownPosition] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
    const [highlightedIndex, setHighlightedIndex] = useState<number>(0);
    const [cursorPosition, setCursorPosition] = useState<number>(0);

    // Get filepath suggestions when in suggestion mode
    const { suggestions, isLoading: suggestionsLoading, error } = useFilepathSuggestionFetching({
        searchQuery: filepathContext?.searchQuery || ''
    });

    // Auto-resize textarea
    const autoResize = useCallback((element: HTMLTextAreaElement) => {
        element.style.height = 'auto';
        element.style.height = (element.scrollHeight + 10) + 'px';
    }, []);

    useEffect(() => {
        if (activeTextAreaRef.current) {
            autoResize(activeTextAreaRef.current);
        }
    }, [value, activeTextAreaRef, autoResize]);

    // Update cursor position and check for filepath mode
    const updateCursorContext = useCallback(() => {
        if (!activeTextAreaRef.current) return;

        const textarea = activeTextAreaRef.current;
        const newCursorPosition = textarea.selectionStart;
        setCursorPosition(newCursorPosition);

        const context = detectFilepathMode(value, newCursorPosition);
        setFilepathContext(context);

        if (context) {
            const position = calculateDropdownPosition(activeTextAreaRef, context.startPosition);
            setDropdownPosition(position);
        }
    }, [value, activeTextAreaRef]);

    if (loading) {
        return <Skeleton type="text" />;
    }

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newValue = e.currentTarget.value;
        onChange(newValue);

        // Auto-resize
        autoResize(e.currentTarget);

        // Update cursor context after state update
        setTimeout(updateCursorContext, 0);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        // Handle dropdown navigation when in filepath suggestion mode
        if (filepathContext && suggestions.length > 0) {
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    setHighlightedIndex(prev =>
                        prev < suggestions.length - 1 ? prev + 1 : 0
                    );
                    return;

                case 'ArrowUp':
                    e.preventDefault();
                    setHighlightedIndex(prev =>
                        prev > 0 ? prev - 1 : suggestions.length - 1
                    );
                    return;

                case 'Enter':
                    e.preventDefault();
                    if (suggestions[highlightedIndex]) {
                        handleSuggestionSelect(suggestions[highlightedIndex]);
                        setHighlightedIndex(0);
                    }
                    return;

                case 'Escape':
                    e.preventDefault();
                    setHighlightedIndex(0);
                    setFilepathContext(null);
                    return;
            }
        }

        // Handle original keydown logic
        if (submitOnEnter && e.key === 'Enter') {
            e.preventDefault();
        }

        if (onKeyDown) {
            onKeyDown(e);
        }
    };

    const handleSuggestionSelect = (suggestion: string) => {
        if (!filepathContext) return;

        // Replace the @searchQuery with the selected suggestion
        const beforeAt = value.substring(0, filepathContext.startPosition);
        const afterCursor = value.substring(filepathContext.endPosition);
        const newValue = beforeAt + suggestion + afterCursor;

        onChange(newValue);
        setFilepathContext(null);

        // Position cursor after the inserted suggestion
        setTimeout(() => {
            if (activeTextAreaRef.current) {
                const newCursorPos = beforeAt.length + suggestion.length;
                activeTextAreaRef.current.setSelectionRange(newCursorPos, newCursorPos);
                activeTextAreaRef.current.focus();
            }
        }, 0);
    };

    const handleBlur = () => {
        // Close dropdown on blur with slight delay to allow clicks
        setTimeout(() => {
            setFilepathContext(null);
        }, 150);

        if (onBlur) {
            onBlur();
        }
    };

    return (
        <div className="relative">
            <textarea
                id={id}
                ref={activeTextAreaRef}
                data-testid={testId}
                className={
                    `my-4 w-full rounded py-2 px-4 resize-none ${className || ''}
                    border border-primary/20 text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent focus:bg-background/80
                    sm:text-sm/6 bg-muted/5 selected:bg-background/80
                    `
                }
                rows={initialRows ?? undefined}
                style={{ overflow: 'hidden' }}
                value={value || ''}
                placeholder={placeholder}
                onChange={handleInput}
                disabled={disabled}
                onKeyDown={handleKeyDown}
                onKeyUp={updateCursorContext}
                onClick={updateCursorContext}
                onFocus={updateCursorContext}
                onBlur={handleBlur}
            />

            <FilepathSuggestionDropdown
                suggestions={suggestions}
                isLoading={suggestionsLoading}
                error={error}
                isVisible={!!filepathContext && (suggestions.length > 0 || suggestionsLoading)}
                highlightedIndex={highlightedIndex}
                onSelect={handleSuggestionSelect}
                onClose={() => setFilepathContext(null)}
                onHighlightChange={setHighlightedIndex}
                position={dropdownPosition}
                searchQuery={filepathContext?.searchQuery || ''}
            />
        </div>
    );
};

export default FileSuggestionTextInput;
