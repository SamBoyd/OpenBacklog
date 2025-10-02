import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import ClaudeCodeSetupStep from '#components/onboarding/steps/ClaudeCodeSetupStep';
import { useOpenbacklogToken } from '#hooks/useOpenbacklogToken.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';

const meta: Meta<typeof ClaudeCodeSetupStep> = {
  title: 'Components/Onboarding/ClaudeCodeSetupStep',
  component: ClaudeCodeSetupStep,
  parameters: {
    layout: 'centered',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#f8fafc' },
        { name: 'dark', value: '#0f172a' },
      ],
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default state - pre-generation, ready to generate token
 */
export const Default: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Default state before token generation. Shows explanation and "Generate token" button.',
      },
    },
  },
  beforeEach: () => {
    useOpenbacklogToken.mockImplementation(() => ({
      token: null,
      tokenMetadata: null,
      isGenerating: false,
      error: null,
      generateToken: () => {},
      clearToken: () => {},
    }));
    useWorkspaces.mockImplementation(() => ({
      workspaces: [
        {
          id: '12345678-1234-1234-1234-123456789abc',
          name: 'My Project',
          description: 'Test workspace',
          icon: null,
        },
      ],
      currentWorkspace: {
        id: '12345678-1234-1234-1234-123456789abc',
        name: 'My Project',
        description: 'Test workspace',
        icon: null,
      },
      isLoading: false,
      isProcessing: false,
      error: null,
      changeWorkspace: async () => {},
      addWorkspace: async () => ({ id: '', name: '', description: '', icon: null }),
      refresh: () => {},
    }));
  },
};

/**
 * Generating state - token creation in progress
 */
export const Generating: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Shows loading spinner while token is being generated.',
      },
    },
  },
  beforeEach: () => {
    useOpenbacklogToken.mockImplementation(() => ({
      token: null,
      tokenMetadata: null,
      isGenerating: true,
      error: null,
      generateToken: () => {},
      clearToken: () => {},
    }));
    useWorkspaces.mockImplementation(() => ({
      workspaces: [
        {
          id: '12345678-1234-1234-1234-123456789abc',
          name: 'My Project',
          description: 'Test workspace',
          icon: null,
        },
      ],
      currentWorkspace: {
        id: '12345678-1234-1234-1234-123456789abc',
        name: 'My Project',
        description: 'Test workspace',
        icon: null,
      },
      isLoading: false,
      isProcessing: false,
      error: null,
      changeWorkspace: async () => {},
      addWorkspace: async () => ({ id: '', name: '', description: '', icon: null }),
      refresh: () => {},
    }));
  },
};

/**
 * Token generated - shows token and MCP command
 */
export const TokenGenerated: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Shows the generated token and MCP installation command with copy buttons.',
      },
    },
  },
  beforeEach: () => {
    useOpenbacklogToken.mockImplementation(() => ({
      token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDU2NzgiLCJleHAiOjE3MDk4NTYwMDB9.test_signature_here_for_demo_purposes',
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
    }));
    useWorkspaces.mockImplementation(() => ({
      workspaces: [
        {
          id: '12345678-1234-1234-1234-123456789abc',
          name: 'My Project',
          description: 'Test workspace',
          icon: null,
        },
      ],
      currentWorkspace: {
        id: '12345678-1234-1234-1234-123456789abc',
        name: 'My Project',
        description: 'Test workspace',
        icon: null,
      },
      isLoading: false,
      isProcessing: false,
      error: null,
      changeWorkspace: async () => {},
      addWorkspace: async () => ({ id: '', name: '', description: '', icon: null }),
      refresh: () => {},
    }));
  },
};

/**
 * Error state - token generation failed
 */
export const Error: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Shows error message when token generation fails, with retry button.',
      },
    },
  },
  beforeEach: () => {
    useOpenbacklogToken.mockImplementation(() => ({
      token: null,
      tokenMetadata: null,
      isGenerating: false,
      error: new Error('Failed to generate token. Please try again.'),
      generateToken: () => {},
      clearToken: () => {},
    }));
    useWorkspaces.mockImplementation(() => ({
      workspaces: [
        {
          id: '12345678-1234-1234-1234-123456789abc',
          name: 'My Project',
          description: 'Test workspace',
          icon: null,
        },
      ],
      currentWorkspace: {
        id: '12345678-1234-1234-1234-123456789abc',
        name: 'My Project',
        description: 'Test workspace',
        icon: null,
      },
      isLoading: false,
      isProcessing: false,
      error: null,
      changeWorkspace: async () => {},
      addWorkspace: async () => ({ id: '', name: '', description: '', icon: null }),
      refresh: () => {},
    }));
  },
};
