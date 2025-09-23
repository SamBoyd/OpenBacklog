import { useState, useRef, useCallback, useEffect } from 'react';

interface UseSuggestionFetchingProps {
    value: string;
    textAreaRef: React.RefObject<HTMLTextAreaElement>;
}

/**
 * Custom hook for fetching text completion suggestions.
 * @param {UseSuggestionFetchingProps} props - The properties for the hook.
 * @returns {{ suggestion: string; setSuggestion: (suggestion: string) => void; loadingSuggestion: boolean; fetchSuggestion: (text: string) => Promise<void>; debounceTimerRef: React.MutableRefObject<NodeJS.Timeout | null> }}
 */
export const useSuggestionFetching = ({
    value,
    textAreaRef,
}: UseSuggestionFetchingProps) => {
    const [suggestion, setSuggestion] = useState<string>('');
    const [loadingSuggestion, setLoadingSuggestion] = useState<boolean>(false);
    const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
    const cacheRef = useRef<Map<string, string>>(new Map());

    const fetchSuggestionCallback = useCallback(async (text: string) => {
        if (!text.trim()) return;

        if (cacheRef.current.has(text)) {
            setSuggestion(cacheRef.current.get(text)!);
            return;
        }

        try {
            setLoadingSuggestion(true);
            setSuggestion(''); // Clear previous suggestion

            const response = await fetch('/api/text-completion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: `Complete this partially written description: ${text}`,
                    stream: true,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("text/event-stream")) {
                const reader = response.body?.getReader();
                if (!reader) {
                    throw new Error("Response body is not readable");
                }
                let accumulatedSuggestion = "";
                let sseBuffer = ""; // Buffer for raw decoded chunks
                const decoder = new TextDecoder();
                // eslint-disable-next-line no-constant-condition
                while (true) {
                    const { done, value: chunkValue } = await reader.read();
                    if (done) break;

                    sseBuffer += decoder.decode(chunkValue, { stream: true });
                    let eolIndex; // End-of-line index for a message block

                    // Process all complete message blocks in the buffer
                    while ((eolIndex = sseBuffer.indexOf('\n\n')) >= 0) {
                        const messageBlock = sseBuffer.slice(0, eolIndex);
                        sseBuffer = sseBuffer.slice(eolIndex + 2); // Remove processed message block from buffer (+2 for \n\n)

                        const lines = messageBlock.split('\n');
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                accumulatedSuggestion += line.substring('data: '.length);
                            } else if (line.startsWith('data:')) { // Handle case where there's no space after 'data:'
                                accumulatedSuggestion += line.substring('data:'.length);
                            }
                            // Other SSE lines like 'event:', 'id:', or comments (':') are ignored for text accumulation
                        }
                    }
                    // Update suggestion after processing all full messages in the current buffer
                    setSuggestion(accumulatedSuggestion);
                }
                // Final trim and set, in case of any remaining partial data or just as a cleanup
                setSuggestion(accumulatedSuggestion.trim());
                cacheRef.current.set(text, accumulatedSuggestion.trim());
            } else {
                const data = await response.json();
                let finalSuggestion = '';
                if (data.text) {
                    finalSuggestion = data.text;
                } else if (data.response) {
                    finalSuggestion = data.response;
                }
                setSuggestion(finalSuggestion);
                cacheRef.current.set(text, finalSuggestion);
            }
        } catch (error) {
            console.error('Error fetching suggestion:', error);
            setSuggestion(''); // Clear suggestion on error
        } finally {
            setLoadingSuggestion(false);
        }
    }, []);

    // Cleanup debounce timer on unmount
    useEffect(() => {
        return () => {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
        };
    }, []);

    return {
        suggestion,
        setSuggestion,
        loadingSuggestion,
        fetchSuggestion: fetchSuggestionCallback,
        debounceTimerRef,
    };
}; 