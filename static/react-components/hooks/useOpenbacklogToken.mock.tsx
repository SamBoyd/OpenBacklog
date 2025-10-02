// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useOpenbacklogToken';

export const useOpenbacklogToken = fn(actual.useOpenbacklogToken).mockName('useOpenbacklogToken');

/**
 * Default mock return value for useOpenbacklogToken hook (no token generated)
 */
export const mockUseOpenbacklogTokenReturn = {
    token: null,
    tokenMetadata: null,
    isGenerating: false,
    error: null,
    generateToken: () => {},
    clearToken: () => {},
};

/**
 * Mock return value for generating/loading state
 */
export const mockUseOpenbacklogTokenGeneratingReturn = {
    token: null,
    tokenMetadata: null,
    isGenerating: true,
    error: null,
    generateToken: () => {},
    clearToken: () => {},
};

/**
 * Mock return value for successful token generation
 */
export const mockUseOpenbacklogTokenGeneratedReturn = {
    token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDU2NzgiLCJleHAiOjE3MDk4NTYwMDB9.test_signature_here',
    tokenMetadata: {
        message: 'OpenBacklog token created successfully',
        token_id: '12345678-1234-1234-1234-123456789abc',
        redacted_key: 'eyJhbG***here',
        created_at: '2025-01-15T12:00:00.000Z',
    },
    isGenerating: false,
    error: null,
    generateToken: () => {},
    clearToken: () => {},
};

/**
 * Mock return value for error state
 */
export const mockUseOpenbacklogTokenErrorReturn = {
    token: null,
    tokenMetadata: null,
    isGenerating: false,
    error: new Error('Failed to generate token. Please try again.'),
    generateToken: () => {},
    clearToken: () => {},
};
