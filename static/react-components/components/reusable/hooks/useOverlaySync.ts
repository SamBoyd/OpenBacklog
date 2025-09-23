import { useEffect, RefObject } from 'react';

interface UseOverlaySyncProps {
    textAreaRef: RefObject<HTMLTextAreaElement>;
    suggestionOverlayRef: RefObject<HTMLDivElement>;
    // Add any other dependencies that should trigger a re-sync if they change.
    // For example, if the suggestion text itself could influence layout, add it here.
    suggestion?: string; 
}

/**
 * Custom hook to synchronize the style and scroll position of a suggestion overlay with a textarea.
 * @param {UseOverlaySyncProps} props - The properties for the hook.
 * @returns {void}
 */
export const useOverlaySync = ({
    textAreaRef,
    suggestionOverlayRef,
    suggestion, // Added suggestion as a dependency
}: UseOverlaySyncProps): void => {
    useEffect(() => {
        const textarea = textAreaRef.current;
        const overlay = suggestionOverlayRef.current;

        if (textarea && overlay) {
            const syncProperties = () => {
                const computedStyle = window.getComputedStyle(textarea);

                overlay.style.fontFamily = computedStyle.fontFamily;
                overlay.style.fontSize = computedStyle.fontSize;
                overlay.style.fontWeight = computedStyle.fontWeight;
                overlay.style.lineHeight = computedStyle.lineHeight;
                overlay.style.letterSpacing = computedStyle.letterSpacing;
                overlay.style.textAlign = computedStyle.textAlign;
                overlay.style.paddingTop = computedStyle.paddingTop;
                overlay.style.paddingRight = computedStyle.paddingRight;
                overlay.style.paddingBottom = computedStyle.paddingBottom;
                overlay.style.paddingLeft = computedStyle.paddingLeft;

                overlay.style.height = textarea.style.height; // Height is now managed by useAutoResizeTextarea

                overlay.scrollTop = textarea.scrollTop;
                overlay.scrollLeft = textarea.scrollLeft;
            };

            syncProperties(); // Initial sync

            const observer = new MutationObserver(syncProperties);
            observer.observe(textarea, { attributes: true, attributeFilter: ['style', 'class'] });

            textarea.addEventListener('scroll', syncProperties);
            window.addEventListener('resize', syncProperties);

            return () => {
                observer.disconnect();
                textarea.removeEventListener('scroll', syncProperties);
                window.removeEventListener('resize', syncProperties);
            };
        }

        return () => {}; // Return an empty function if refs are not available
    // Added suggestion to dependency array to re-run effect if suggestion changes, which might affect layout.
    }, [textAreaRef, suggestionOverlayRef, suggestion]); 
}; 