import { useState, useCallback, Dispatch, SetStateAction } from 'react';
import { useUserPreferences } from './useUserPreferences';

interface UseTextRewriteProps {
    existingDescription?: string;
}

interface UseTextRewriteReturn {
    rewriteText: (text: string) => Promise<string>;
    isRewriting: boolean;
    error: string | null;
    isRewriteEnabled: boolean;
    setIsRewriteEnabled: (isEnabled: boolean) => void;
}

export const useTextRewrite = ({ existingDescription }: UseTextRewriteProps = {}): UseTextRewriteReturn => {
    const [isRewriting, setIsRewriting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { preferences, updateIsRewriteEnabled } = useUserPreferences();
    const isRewriteEnabled = preferences.isRewriteEnabled;

    const rewriteText = useCallback(async (text: string): Promise<string> => {
        if (!isRewriteEnabled) {
            return text;
        }

        setIsRewriting(true);
        setError(null);

        try {
            const requestBody = {
                text,
                existing_description: existingDescription,
            };

            const response = await fetch('/api/rewrite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                let errorMessage = `Rewriting failed: ${response.status} ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorData.error || errorMessage;
                } catch (e) { /* Failed to parse JSON */ }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            if (!result.rewritten_text) {
                throw new Error('Rewriting successful, but no rewritten text was returned.');
            }

            return result.rewritten_text;
        } catch (e: any) {
            console.error('Rewriting error:', e);
            setError(e.message || 'An unknown error occurred during rewriting.');
            throw e;
        } finally {
            setIsRewriting(false);
        }
    }, [isRewriteEnabled, existingDescription]);

    return {
        rewriteText,
        isRewriting,
        error,
        isRewriteEnabled,
        setIsRewriteEnabled: updateIsRewriteEnabled,
    };
}; 