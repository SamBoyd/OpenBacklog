import React, { useEffect, useRef, useState } from 'react';

import { Skeleton } from './Skeleton';

interface TabCompleteTextInputProps {
    id?: string;
    value: string;
    onChange: (value: string) => void;
    loading?: boolean;
    className?: string;
    placeholder?: string;
    testId?: string;
    initialRows?: number;
    disabled?: boolean;
    submitOnEnter?: boolean;
    onKeyDown?: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
}

const TabCompleteTextInput: React.FC<TabCompleteTextInputProps> = ({
    id,
    value,
    onChange,
    loading = false,
    className,
    placeholder = "",
    testId = "title-input",
    initialRows = null,
    disabled = false,
    onKeyDown,
    submitOnEnter = false,
}) => {
    const [suggestion, setSuggestion] = useState<string>('');
    const [suggestionDisplay, setSuggestionDisplay] = useState<boolean>(false);
    const [loadingSuggestion, setLoadingSuggestion] = useState<boolean>(false);
    const [caretPosition, setCaretPosition] = useState<{ top: number; left: number; lineHeight: number; bottom: number }>({ top: 0, left: 0, lineHeight: 0, bottom: 0 });
    const textAreaRef = useRef<HTMLTextAreaElement>(null);
    const caretMeasureRef = useRef<HTMLDivElement>(null);
    const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);


    useEffect(() => {
        console.log(suggestion);
        console.log(loadingSuggestion);
    }, [suggestion, loadingSuggestion]);

    // Show suggestion when it's available
    useEffect(() => {
        if (suggestion) {
            setSuggestionDisplay(true);
        } else {
            setSuggestionDisplay(false);
        }
    }, [suggestion]);


    // Update textarea height based on content
    useEffect(() => {
        const interval = setInterval(() => {
            if (textAreaRef.current) {
                textAreaRef.current.style.height = 'auto';
                textAreaRef.current.style.height = textAreaRef.current.scrollHeight + 'px';
            }
        }, 100)

        return () => {
            clearInterval(interval);
        };
    }, [textAreaRef.current]);

    // Clean up debounce timer
    useEffect(() => {
        return () => {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
        };
    }, []);

    // Update caret position whenever value changes or on click/keyup
    const updateCaretPosition = () => {
        const textarea = textAreaRef.current;
        if (!textarea) return;

        setSuggestionDisplay(false);

        const caretPos = textarea.selectionStart;

        // Create a div to measure text dimensions
        if (!caretMeasureRef.current) return;

        const measure = caretMeasureRef.current;
        // Copy the textarea's styling
        const style = window.getComputedStyle(textarea);
        measure.style.width = style.width;
        measure.style.fontSize = style.fontSize;
        measure.style.fontFamily = style.fontFamily;
        measure.style.padding = style.padding;
        measure.style.letterSpacing = style.letterSpacing;

        // Create text content up to caret position
        const textBeforeCaret = value.substring(0, caretPos);
        // Add a span at the end where we'll measure position
        measure.innerHTML = textBeforeCaret.replace(/\n/g, '<br>') + '<span id="caretMark"></span>';

        // Get position of the caret mark
        const caretMark = measure.querySelector('#caretMark');
        if (caretMark) {
            const rect = caretMark.getBoundingClientRect();
            const measureRect = measure.getBoundingClientRect();
            const textareaRect = textarea.getBoundingClientRect();

            // Calculate position relative to textarea
            const top = rect.top - measureRect.top + textarea.scrollTop;
            const left = rect.left - measureRect.left + textarea.scrollLeft;
            const lineHeight = parseInt(style.lineHeight || '1.2', 10);
            const bottom = textareaRect.height - (top + lineHeight);

            console.log(top, left, lineHeight, bottom);

            setCaretPosition({ top, left, lineHeight, bottom });
        }
    };

    const fetchSuggestion = async (text: string) => {
        if (!text.trim()) return;

        try {
            setLoadingSuggestion(true);

            const response = await fetch('/api/text-completion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: `Complete this description with 2-3 more sentences: ${text}`,
                    stream: true
                })
            });

            const data = await response.json();
            if (data.text) {
                setSuggestion(data.text);
            }
        } catch (error) {
            console.error('Error fetching suggestion:', error);
        } finally {
            setLoadingSuggestion(false);
        }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newValue = e.currentTarget.value;
        onChange(newValue);
        setSuggestion(''); // Clear previous suggestion

        // Update caret position
        updateCaretPosition();

        // Cancel any pending debounce timer
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        // Set a new debounce timer to fetch suggestions after 1 second of inactivity
        debounceTimerRef.current = setTimeout(() => {
            if (newValue.trim().length > 10) { // Only get suggestions for substantial text
                fetchSuggestion(newValue);
            }
        }, 1000);
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (submitOnEnter && e.key === 'Enter') {
            e.preventDefault();
        }

        // Accept suggestion with Tab key
        if (e.key === 'Tab' && suggestion && suggestionDisplay) {
            e.preventDefault();
            onChange(value + suggestion);
            setSuggestion('');
            setSuggestionDisplay(false);
        }

        // Hide suggestion on Escape key
        if (e.key === 'Escape' && suggestion) {
            e.preventDefault();
            setSuggestionDisplay(false);
        }

        if (onKeyDown) {
            onKeyDown(e);
        }
    }

    // Update caret position on key up, click, or focus change
    const handleCaretUpdate = () => {
        // Use requestAnimationFrame to ensure DOM measurements are accurate
        requestAnimationFrame(updateCaretPosition);
    };

    if (loading) {
        return <Skeleton type="text" />;
    }

    const MIN_WIDTH = 300;

    let sugestionPosition: {
        top: number | null;
        bottom: number | null;
        left: number | null;
        right: number | null;
        width: number | null;
    } = {
        top: null,
        bottom: null,
        left: null,
        right: null,
        width: 450
    }

    if (textAreaRef?.current) {
        // If the caret is in the top half of the textarea, show the suggestion above the caret
        if (caretPosition.top < textAreaRef?.current?.scrollHeight / 2) {
            sugestionPosition.top = caretPosition.top + 1.5 * caretPosition.lineHeight;
            sugestionPosition.bottom = null;
        }
        // If the caret is in the bottom half of the textarea, show the suggestion below the caret
        if (caretPosition.top > textAreaRef?.current?.scrollHeight / 2) {
            sugestionPosition.top = null;
            sugestionPosition.bottom = caretPosition.bottom + 1 * caretPosition.lineHeight;
        }
    }

    return (
        <div className="relative">
            {/* Hidden div for measuring caret position */}
            <div
                ref={caretMeasureRef}
                aria-hidden="true"
                className="absolute top-0 left-0 overflow-hidden opacity-0 pointer-events-none"
                style={{
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word',
                    visibility: 'hidden',
                    position: 'absolute',
                    height: 0
                }}
            />

            <textarea
                id={id}
                ref={textAreaRef}
                data-testid={testId}
                className={
                    `my-4 w-full rounded py-2 px-4 resize-none ${className}
                    border border-primary/20 text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent focus:bg-background/80
                    sm:text-sm/6 bg-muted/5 selected:bg-background/80
                    `
                }
                rows={initialRows ?? undefined}
                style={{ overflow: 'hidden' }}
                value={value || ''}
                placeholder={placeholder}
                onInput={(e) => {
                    const target = e.currentTarget;
                    target.style.height = 'auto';
                    target.style.height = (target.scrollHeight + 10) + 'px';
                }}
                onChange={handleInput}
                disabled={disabled}
                onKeyDown={handleKeyDown}
                onKeyUp={handleCaretUpdate}
                onClick={handleCaretUpdate}
                onFocus={handleCaretUpdate}
            />

            {/* Inline suggestion overlay */}
            {suggestion && suggestionDisplay && (
                <div className="absolute pointer-events-none "
                    style={{
                        top: sugestionPosition.top ? sugestionPosition.top + 'px' : undefined,
                        bottom: sugestionPosition.bottom ? sugestionPosition.bottom + 'px' : undefined,
                        left: sugestionPosition.left ? sugestionPosition.left + 'px' : undefined,
                        right: sugestionPosition.right ? sugestionPosition.right + 'px' : undefined,
                        width: sugestionPosition.width ? sugestionPosition.width + 'px' : undefined,
                    }}
                >
                    <span
                        className="bg-background text-muted-foreground border-border border rounded-md p-2"
                        style={{
                            display: 'inline-block',
                            fontFamily: textAreaRef.current ?
                                window.getComputedStyle(textAreaRef.current).fontFamily : 'inherit',
                            fontSize: textAreaRef.current ?
                                window.getComputedStyle(textAreaRef.current).fontSize : 'inherit'
                        }}
                    >
                        {suggestion}
                    </span>

                    {!loadingSuggestion && suggestion && suggestionDisplay && (
                        <div className="absolute -bottom-2 right-2 text-xs text-muted/50 bg-background/80 border border-border/15 p-1 rounded">
                            Tab to accept or Esc to dismiss
                        </div>
                    )}
                </div>
            )}

            {loadingSuggestion && (
                <div className="absolute bottom-2 right-2 text-xs text-muted-foreground bg-background/80 p-1 rounded">
                    Generating...
                </div>
            )}

        </div>
    );
};

export default TabCompleteTextInput; 