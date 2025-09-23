import React, { useEffect, useRef, useState, useCallback } from 'react';

import { Skeleton } from './Skeleton';
import { useAutoResizeTextarea } from './hooks/useAutoResizeTextarea';
import { useCaretPosition } from './hooks/useCaretPosition';
import { useSuggestionFetching } from './hooks/useSuggestionFetching';
import { useOverlaySync } from './hooks/useOverlaySync';

interface AutocompleteTextInputProps {
    id?: string;
    value: string;
    loading?: boolean;
    className?: string;
    placeholder?: string;
    testId?: string;
    initialRows?: number;
    disabled?: boolean;
    submitOnEnter?: boolean;
    onChange: (value: string) => void;
    onKeyDown?: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
    onBlur?: () => void;
}

/**
 * A text input component with autocomplete suggestions that appear as ghost text.
 * It supports dynamic height adjustment based on content, debounced suggestion fetching,
 * and keyboard navigation for accepting or dismissing suggestions.
 * @param {AutocompleteTextInputProps} props - The component props.
 * @returns {React.ReactElement} The AutocompleteTextInput component.
 */
const AutocompleteTextInput: React.FC<AutocompleteTextInputProps> = ({
    id,
    value,
    loading = false,
    className,
    placeholder = "",
    testId = "title-input",
    initialRows = null,
    disabled = false,
    submitOnEnter = false,
    onChange,
    onKeyDown,
    onBlur
}) => {
    const [suggestionDisplay, setSuggestionDisplay] = useState<boolean>(false);
    const textAreaRef = useRef<HTMLTextAreaElement>(null);
    const caretMeasureRef = useRef<HTMLDivElement>(null);
    const suggestionOverlayRef = useRef<HTMLDivElement>(null);

    const {
        suggestion,
        setSuggestion,
        loadingSuggestion,
        fetchSuggestion,
        debounceTimerRef,
    } = useSuggestionFetching({ value, textAreaRef });

    const { updateCaretPosition } = useCaretPosition({
        textAreaRef,
        caretMeasureRef,
        value,
        setSuggestionDisplay,
    });

    useAutoResizeTextarea({
        textAreaRef,
        suggestionOverlayRef,
        value,
        suggestion,
        suggestionDisplay,
        loadingSuggestion,
    });

    useOverlaySync({
        textAreaRef,
        suggestionOverlayRef,
        suggestion,
    });


    useEffect(() => {
        if (suggestion && document.activeElement === textAreaRef.current) {
            setSuggestionDisplay(true);
        } else {
            setSuggestionDisplay(false);
        }
    }, [suggestion]);


    const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newValue = e.currentTarget.value;
        onChange(newValue);
        setSuggestion('');
        requestAnimationFrame(updateCaretPosition);

        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        debounceTimerRef.current = setTimeout(() => {
            if (
                newValue.trim().length > 10 &&
                textAreaRef.current &&
                textAreaRef.current.selectionStart === newValue.length
            ) {
                fetchSuggestion(newValue);
            }
        }, 1000);
    }, [onChange, setSuggestion, updateCaretPosition, debounceTimerRef, fetchSuggestion]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (submitOnEnter && e.key === 'Enter') {
            e.preventDefault();
            // Potentially submit form or trigger action if needed
        }

        if (e.key === 'Tab' && suggestion && suggestionDisplay) {
            e.preventDefault();
            const textToAppend = suggestion;
            onChange(value + textToAppend);
            setSuggestion('');
            setSuggestionDisplay(false);
            // It might be good to move caret to the end after accepting suggestion
            requestAnimationFrame(() => {
                if (textAreaRef.current) {
                    textAreaRef.current.selectionStart = textAreaRef.current.selectionEnd = (value + textToAppend).length;
                }
                updateCaretPosition(); // Re-evaluate caret position after update
            });
        }

        if (e.key === 'Escape' && suggestionDisplay) { // Only hide if suggestion is displayed
            e.preventDefault();
            setSuggestionDisplay(false);
        }

        if (onKeyDown) {
            onKeyDown(e);
        }
    }, [submitOnEnter, suggestion, suggestionDisplay, value, onChange, setSuggestion, onKeyDown, updateCaretPosition]);

    const handleCaretUpdate = useCallback(() => {
        requestAnimationFrame(updateCaretPosition);
    }, [updateCaretPosition]);


    const handleBlur = useCallback(() => {
        if (onBlur) {
            onBlur();
        }

        // cancel the debounce timer
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        // clear the suggestion
        setSuggestion('');
        setSuggestionDisplay(false);
    }, [onBlur]);

    if (loading) {
        return <Skeleton type="text" />;
    }

    return (
        <div className="relative">
            <div
                ref={caretMeasureRef}
                aria-hidden="true"
                className="absolute top-0 left-0 overflow-hidden opacity-0 pointer-events-none"
                style={{
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word',
                    visibility: 'hidden',
                    position: 'absolute',
                    height: 0 // Ensures it doesn't interfere with layout
                }}
            />

            <textarea
                id={id}
                ref={textAreaRef}
                data-testid={testId}
                className={
                    `my-4 w-full rounded py-2 px-4 resize-none ${className || ''}
                    border border-primary/20 focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent focus:bg-background/80
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
                onKeyUp={handleCaretUpdate}
                onClick={handleCaretUpdate}
                onFocus={handleCaretUpdate}
                onBlur={handleBlur}
            />

            <div
                ref={suggestionOverlayRef}
                aria-hidden="true"
                className={
                    `absolute top-0 left-0 pointer-events-none overflow-auto whitespace-pre-wrap break-words
                     my-4 w-full rounded
                     text-foreground
                     border border-transparent
                     ${className || ''}
                    `
                }
                style={{
                    backgroundColor: 'transparent',
                    // Other styles like font, padding, height, scroll are synced by useOverlaySync
                }}
            >
                <span>{value}</span>
                {suggestion && suggestionDisplay && !loadingSuggestion && (
                    <span className="text-muted-foreground">{suggestion}</span>
                )}
            </div>

            {!loadingSuggestion && suggestion && suggestionDisplay && (
                <div className="absolute bottom-2 right-2 text-xs text-muted-foreground/80 bg-background/90 border border-border/30 p-1 px-1.5 rounded-md shadow-sm cursor-default">
                    accept: tab
                </div>
            )}

            {loadingSuggestion && (
                <div className="absolute bottom-2 right-2 text-xs text-muted-foreground bg-background/90 p-1 px-1.5 rounded-md animate-pulse shadow-sm">
                    Generating...
                </div>
            )}
        </div>
    );
};

export default AutocompleteTextInput; 