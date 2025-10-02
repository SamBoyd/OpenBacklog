import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { useCallback, useMemo, useState } from 'react';
import { createOpenBacklogToken, OpenBacklogTokenResponse } from '#api/openbacklogTokens';

/**
 * Interface for the return value of useOpenbacklogToken hook
 */
export interface OpenbacklogTokenHookResult {
    /** Generated token (full value, or null if not generated) */
    token: string | null;
    /** Token metadata (if generated) */
    tokenMetadata: Omit<OpenBacklogTokenResponse, 'token'> | null;
    /** Whether token generation is in progress */
    isGenerating: boolean;
    /** Error that occurred during generation, if any */
    error: Error | null;
    /** Function to generate a new token */
    generateToken: () => void;
    /** Function to clear the generated token from state */
    clearToken: () => void;
}

/**
 * Custom hook for managing OpenBacklog Personal Access Token generation
 * Token is stored in state and only shown once - user must copy it before clearing
 *
 * @returns {OpenbacklogTokenHookResult} Object containing token, generation state, and operations
 */
export const useOpenbacklogToken = (): OpenbacklogTokenHookResult => {
    // Store the generated token in component state (not in query cache)
    // This ensures it's only available once and cleared when component unmounts
    const [generatedToken, setGeneratedToken] = useState<OpenBacklogTokenResponse | null>(null);

    // Mutation for token creation
    const tokenMutation: UseMutationResult<OpenBacklogTokenResponse, Error, void> = useMutation({
        mutationFn: createOpenBacklogToken,
        onSuccess: (data) => {
            // Store the token in state immediately after successful generation
            setGeneratedToken(data);
        },
        throwOnError: false, // Ensure errors are captured in error state
    });

    const generateToken = useCallback(() => {
        // Clear any existing token before generating new one
        setGeneratedToken(null);
        tokenMutation.mutate();
    }, [tokenMutation]);

    const clearToken = useCallback(() => {
        // Clear the token from state
        setGeneratedToken(null);
        // Reset mutation state
        tokenMutation.reset();
    }, [tokenMutation]);

    // Memoize the return value to prevent unnecessary re-renders
    return useMemo(() => ({
        token: generatedToken?.token ?? null,
        tokenMetadata: generatedToken ? {
            message: generatedToken.message,
            token_id: generatedToken.token_id,
            redacted_key: generatedToken.redacted_key,
            created_at: generatedToken.created_at,
        } : null,
        isGenerating: tokenMutation.isPending,
        error: tokenMutation.error,
        generateToken,
        clearToken,
    }), [
        generatedToken,
        tokenMutation.isPending,
        tokenMutation.error,
        generateToken,
        clearToken,
    ]);
};
