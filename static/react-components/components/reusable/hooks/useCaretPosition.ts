import { useState, RefObject, useCallback } from 'react';

interface CaretPosition {
    top: number;
    left: number;
    lineHeight: number;
    bottom: number;
}

interface UseCaretPositionProps {
    textAreaRef: RefObject<HTMLTextAreaElement>;
    caretMeasureRef: RefObject<HTMLDivElement>;
    value: string;
    setSuggestionDisplay: (display: boolean) => void;
}

/**
 * Custom hook to calculate and update the caret position within a textarea.
 * @param {UseCaretPositionProps} props - The properties for the hook.
 * @returns {{ caretPosition: CaretPosition; updateCaretPosition: () => void }}
 */
export const useCaretPosition = ({
    textAreaRef,
    caretMeasureRef,
    value,
    setSuggestionDisplay,
}: UseCaretPositionProps) => {
    const [caretPosition, setCaretPosition] = useState<CaretPosition>({ top: 0, left: 0, lineHeight: 0, bottom: 0 });

    const updateCaretPosition = useCallback(() => {
        const textarea = textAreaRef.current;
        if (!textarea) return;

        setSuggestionDisplay(false);

        const caretPos = textarea.selectionStart;

        if (!caretMeasureRef.current) return;

        const measure = caretMeasureRef.current;
        const style = window.getComputedStyle(textarea);
        measure.style.width = style.width;
        measure.style.fontSize = style.fontSize;
        measure.style.fontFamily = style.fontFamily;
        measure.style.padding = style.padding;
        measure.style.letterSpacing = style.letterSpacing;

        const textBeforeCaret = value.substring(0, caretPos);
        measure.innerHTML = textBeforeCaret.replace(/\n/g, '<br>') + '<span id="caretMark"></span>';

        const caretMark = measure.querySelector('#caretMark');
        if (caretMark) {
            const rect = caretMark.getBoundingClientRect();
            const measureRect = measure.getBoundingClientRect();
            const textareaRect = textarea.getBoundingClientRect();

            const top = rect.top - measureRect.top + textarea.scrollTop;
            const left = rect.left - measureRect.left + textarea.scrollLeft;
            const lineHeight = parseInt(style.lineHeight || '1.2', 10) * parseFloat(style.fontSize || '16px'); // More robust lineHeight
            const bottom = textareaRect.height - (top + lineHeight);

            setCaretPosition({ top, left, lineHeight, bottom });
        }
    }, [textAreaRef, caretMeasureRef, value, setSuggestionDisplay]);

    return { caretPosition, updateCaretPosition };
}; 