import React, { useRef, useEffect, useLayoutEffect, useState } from 'react';

import { Skeleton } from './Skeleton';


interface TitleInputProps {
    id?: string;
    value: string;
    onChange: (value: string) => void;
    loading?: boolean;
    placeholder?: string;
    disabled?: boolean;
    multiline?: boolean;
    maxLength?: number;
    showCharCount?: boolean;
}

const TitleInput: React.FC<TitleInputProps> = ({
    id,
    value,
    onChange,
    loading = false,
    placeholder = "",
    disabled = false,
    multiline = false,
    maxLength,
    showCharCount = false,
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const spanRef = useRef<HTMLSpanElement>(null);
    const [localValue, setLocalValue] = useState(value);
    const [clickPosition, setClickPosition] = useState<number | null>(null);

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newValue = e.currentTarget.value;
        
        // Apply maxLength constraint if provided
        if (maxLength && newValue.length > maxLength) {
            return; // Don't update if exceeds max length
        }
        
        setLocalValue(newValue);
    }

    useEffect(() => {
        setLocalValue(value);
    }, [value]);

    // Use useLayoutEffect to ensure height is calculated before browser paint
    useEffect(() => {
        setTimeout(() => {
            if (textareaRef.current) {
                textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
            }
        }, 100);
    }, [isEditing]);

    const adjustHeight = (e: React.SyntheticEvent<HTMLTextAreaElement>) => {
        const target = e.currentTarget;
        target.style.height = 'auto';
        target.style.height = target.scrollHeight + 'px';
    };

    /**
     * Calculate the text position closest to where the user clicked
     */
    const getClickPosition = (event: React.MouseEvent, text: string): number => {
        if (!spanRef.current || !text) return 0;

        const span = spanRef.current;
        const rect = span.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const clickY = event.clientY - rect.top;
        
        // Create a temporary canvas to measure text
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        if (!context) return 0;

        // Apply the same font styling as the span
        const computedStyle = window.getComputedStyle(span);
        context.font = `${computedStyle.fontSize} ${computedStyle.fontFamily}`;
        
        const fontSize = parseFloat(computedStyle.fontSize);
        const lineHeight = parseFloat(computedStyle.lineHeight) || fontSize * 1.2;
        const spanWidth = rect.width;
        
        // Split text into words and simulate line wrapping
        const words = text.split(' ');
        const lines: string[] = [];
        let currentLine = '';
        
        for (const word of words) {
            const testLine = currentLine + (currentLine ? ' ' : '') + word;
            const testWidth = context.measureText(testLine).width;
            
            if (testWidth > spanWidth && currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        }
        if (currentLine) {
            lines.push(currentLine);
        }
        
        // Determine which line was clicked
        const clickedLineIndex = Math.floor(clickY / lineHeight);
        const targetLineIndex = Math.max(0, Math.min(clickedLineIndex, lines.length - 1));
        
        // Calculate character offset up to the target line
        let characterOffset = 0;
        for (let i = 0; i < targetLineIndex; i++) {
            characterOffset += lines[i].length;
            if (i < targetLineIndex) characterOffset += 1; // Add space between words
        }
        
        // Find the closest character position within the clicked line
        const targetLine = lines[targetLineIndex];
        if (!targetLine) return characterOffset;
        
        let bestPosition = 0;
        let minDistance = Infinity;
        
        for (let i = 0; i <= targetLine.length; i++) {
            const textUpToPosition = targetLine.substring(0, i);
            const textWidth = context.measureText(textUpToPosition).width;
            const distance = Math.abs(clickX - textWidth);
            
            if (distance < minDistance) {
                minDistance = distance;
                bestPosition = i;
            }
        }
        
        return characterOffset + bestPosition;
    };

    useEffect(() => {
        // Focus the textarea when switching to edit mode and set cursor position
        if (isEditing && textareaRef.current) {
            const textarea = textareaRef.current;
            textarea.focus();
            
            // Set cursor position if we have a click position
            if (clickPosition !== null) {
                setTimeout(() => {
                    textarea.setSelectionRange(clickPosition, clickPosition);
                }, 0);
                setClickPosition(null); // Reset after use
            }
        }
    }, [isEditing, clickPosition]);

    const handleBlur = () => {
        setIsEditing(false);
        onChange(multiline ? localValue : localValue.replace(/\n/g, ''));
    };

    if (loading) {
        return <Skeleton type="text" />;
    }

    const handleSpanClick = (event: React.MouseEvent) => {
        if (disabled) return;
        
        const textToUse = localValue || placeholder;
        if (textToUse && localValue) { // Only calculate position for actual content, not placeholder
            const position = getClickPosition(event, textToUse);
            setClickPosition(position);
        }
        setIsEditing(true);
    };

    const characterCount = localValue?.length || 0;
    const isNearLimit = maxLength && characterCount > maxLength * 0.8;
    const isAtLimit = maxLength && characterCount >= maxLength;

    if (!isEditing) {
        return (
            <div className="w-full">
                <span
                    ref={spanRef}
                    className="my-4 py-2 px-4 block w-full text-lg text-foreground cursor-pointer"
                    onClick={handleSpanClick}
                >
                    {localValue || placeholder}
                </span>
            </div>
        );
    }

    return (
        <div className="w-full flex flex-col">
            <textarea
                id={id}
                ref={textareaRef}
                className={
                    `my-4 py-2 px-4 w-full bg-transparent 
                    focus:border focus:border-primary
                    focus:outline-none rounded resize-none
                    text-foreground text-lg ${
                        isAtLimit ? 'border-destructive' : ''
                    }`
                }
                style={{ overflow: 'hidden' }}
                value={localValue || ''}
                placeholder={placeholder}
                onInput={adjustHeight}
                onChange={(e) => {
                    handleInput(e);
                    adjustHeight(e);
                }}
                onBlur={handleBlur}
                disabled={disabled}
                maxLength={maxLength}
            />
            {showCharCount && maxLength && (
                <div className={`text-sm px-4 -mt-2 mb-2 self-end ${
                    isAtLimit ? 'text-destructive' : 
                    isNearLimit ? 'text-orange-500' : 
                    'text-muted-foreground'
                }`}>
                    {characterCount}/{maxLength}
                </div>
            )}
        </div>
    );
};

export default TitleInput;
