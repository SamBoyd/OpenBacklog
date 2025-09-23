import React, { useEffect, useRef } from 'react';

import { Skeleton } from './Skeleton';


interface ResizingTextInputProps {
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

const ResizingTextInput: React.FC<ResizingTextInputProps> = ({
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

    useEffect(() => {
        if (textAreaRef.current) {
            textAreaRef.current.style.height = 'auto';
            textAreaRef.current.style.height = textAreaRef.current.scrollHeight + 'px';
        }
    }, [textAreaRef.current])

    useEffect(() => {
        if (textAreaRef.current) {
            textAreaRef.current.style.height = 'auto';
            textAreaRef.current.style.height = textAreaRef.current.scrollHeight + 'px';
        }
    }, [textAreaRef.current?.clientWidth])

    useEffect(() => {
        if (providedRef?.current) {
            providedRef.current.style.height = 'auto';
            providedRef.current.style.height = providedRef.current.scrollHeight + 'px';
        }
    }, [providedRef?.current])

    if (loading) {
        return <Skeleton type="text" />;
    }

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const value = e.currentTarget.value;
        const trimmedValue = value
        onChange(trimmedValue);
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (submitOnEnter && e.key === 'Enter') {
            e.preventDefault();
        }

        if (onKeyDown) {
            onKeyDown(e);
        }
    }

    return (
        <textarea
            id={id}
            ref={providedRef ?? textAreaRef}
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
            onChange={e => handleInput(e)}
            disabled={disabled}
            onKeyDown={handleKeyDown}
            onBlur={onBlur}
        />
    );
};

export default ResizingTextInput;
