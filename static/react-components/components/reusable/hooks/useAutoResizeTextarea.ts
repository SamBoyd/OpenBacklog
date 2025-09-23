import { useEffect, RefObject } from 'react';

interface UseAutoResizeTextareaProps {
    textAreaRef: RefObject<HTMLTextAreaElement>;
    suggestionOverlayRef: RefObject<HTMLDivElement>;
    value: string;
    suggestion: string;
    suggestionDisplay: boolean;
    loadingSuggestion: boolean;
}

/**
 * Custom hook to automatically resize a textarea based on its content and an optional suggestion overlay.
 * @param {UseAutoResizeTextareaProps} props - The properties for the hook.
 * @returns {void}
 */
export const useAutoResizeTextarea = ({
    textAreaRef,
    suggestionOverlayRef,
    value,
    suggestion,
    suggestionDisplay,
    loadingSuggestion,
}: UseAutoResizeTextareaProps): void => {
    useEffect(() => {
        const textarea = textAreaRef.current;
        const overlay = suggestionOverlayRef.current;

        if (textarea) {
            // Ensure textarea can shrink by first setting height to a minimal value,
            // then to 'auto'. This forces the browser to re-evaluate scrollHeight
            // correctly when content reduces.
            textarea.style.height = '1px';
            textarea.style.height = 'auto';

            let newCalculatedHeight = textarea.scrollHeight;

            // If a suggestion is actively displayed and its content requires more height, adjust.
            // Ensure overlay exists, suggestion text is present, it's meant to be displayed, and not currently loading.
            if (overlay && suggestion && suggestionDisplay && !loadingSuggestion) {
                const overlayContentHeight = overlay.scrollHeight;
                if (overlayContentHeight > newCalculatedHeight) {
                    newCalculatedHeight = overlayContentHeight;
                }
            }

            textarea.style.height = newCalculatedHeight + 'px';
        }
    }, [value, suggestion, suggestionDisplay, loadingSuggestion, textAreaRef, suggestionOverlayRef]);
}; 