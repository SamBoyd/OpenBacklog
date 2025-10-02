import React, { useCallback, useMemo, useState } from 'react';
import OnboardingStep from '../OnboardingStep';
import { useOpenbacklogToken } from '#hooks/useOpenbacklogToken';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { PrimaryButton, SecondaryButton } from '#components/reusable/Button';

/**
 * Step component for Claude Code MCP setup during onboarding
 * Generates API token and provides MCP installation command
 * @returns {React.ReactElement} The Claude Code setup step component
 */
const ClaudeCodeSetupStep: React.FC = () => {
  const { token, isGenerating, error, generateToken, clearToken } = useOpenbacklogToken();
  const { currentWorkspace } = useWorkspaces();

  // Track which item was copied for visual feedback
  const [copiedItem, setCopiedItem] = useState<'token' | 'command' | null>(null);

  // Get MCP server domain from current origin
  const mcpServerDomain = window.location.origin;

  /**
   * Copies text to clipboard with visual feedback
   */
  const handleCopy = async (text: string, item: 'token' | 'command') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItem(item);
      setTimeout(() => setCopiedItem(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  /**
   * Generates the MCP command with current workspace and token
   */
  const mcpCommand = useMemo((): string => {
    if (!token || !currentWorkspace) return '';

    return `claude mcp add \\
  -H"Authorization: Bearer ${token}" \\
  -H"X-Workspace-Id: ${currentWorkspace.id}" \\
  --transport=http \\
  openbacklog \\
  ${mcpServerDomain}/mcp/`;
  }, [token, currentWorkspace, mcpServerDomain]);

  /**
   * Generates a redacted version of the token for display
   */
  const redactedToken = useMemo((): string => {
    if (!token) return '';
    const start = token.substring(0, 8);
    const end = token.substring(token.length - 4);
    return `${start}...${end}`;
  }, [token]);

  /**
   * Generates a redacted version of the MCP command for display
   */
  const redactedMcpCommand = useMemo((): string => {
    if (!mcpCommand) return '';
    return `claude mcp add -H"Authorization: Bearer ***" ...`;
  }, [mcpCommand]);

  /**
   * Renders the copy button with visual feedback
   */
  const CopyButton: React.FC<{ onClick: () => void; copied: boolean }> = ({ onClick, copied }) => (
    <button
      onClick={onClick}
      className="absolute top-2 right-2 p-1.5 bg-background rounded transition-colors"
      title={copied ? 'Copied!' : 'Copy'}
    >
      {copied ? (
        <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-5 h-5 text-muted-foreground hover:text-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );

  return (
    <OnboardingStep
      title="Add OpenBacklog to Claude Code"
      description="Generate an API token to connect Claude Code with your workspace."
      icon="🤖"
      content={
        <div className="max-w-xs sm:max-w-md mx-auto">
          <div className="space-y-4 sm:space-y-6">
            {/* Pre-Generation State */}
            {!token && !isGenerating && !error && (
              <div className="bg-background border rounded-lg p-4 sm:p-6">
                <h3 className="text-muted-foreground font-semibold mb-3 text-sm sm:text-base">
                  Get started with Claude Code integration
                </h3>
                <p className="text-muted-foreground mb-4 text-sm sm:text-base">
                  You'll need a personal access token to connect Claude Code. We'll generate one and give you the command to run.
                </p>

                <div className="flex justify-center">
                  <PrimaryButton
                    onClick={generateToken}
                    className="w-full sm:w-auto text-xs sm:text-sm px-4 sm:px-6 py-2 sm:py-3"
                  >
                    Generate token
                  </PrimaryButton>
                </div>
              </div>
            )}

            {/* Generating State */}
            {isGenerating && (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                  <span className="text-sm text-muted-foreground">Generating token...</span>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && !isGenerating && (
              <div className="bg-background border border-destructive rounded-lg p-4 sm:p-6">
                <div className="flex items-center mb-3">
                  <svg className="h-5 w-5 text-destructive mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="text-destructive font-medium text-sm sm:text-base">
                    Failed to generate token
                  </h3>
                </div>
                <p className="text-muted-foreground mb-4 text-sm">
                  {error.message || 'An error occurred. Please try again.'}
                </p>
                <div className="flex justify-center">
                  <PrimaryButton
                    onClick={generateToken}
                    className="w-full sm:w-auto text-xs sm:text-sm px-4 py-2"
                  >
                    Try again
                  </PrimaryButton>
                </div>
              </div>
            )}

            {/* Post-Generation State - Token Display */}
            {token && !isGenerating && (
              <div className="bg-background border rounded-lg p-4 sm:p-6">
                {/* <h3 className="text-foreground font-semibold mb-2 text-sm sm:text-base">
                  Your new token
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Copy this token now. For security, it won't be shown again.
                </p> */}

                {/* Token Display */}
                {/* <div className="mb-4">
                  <label className="block text-xs font-medium text-muted-foreground mb-2">
                    Personal access token
                  </label>
                  <div className="bg-background p-3 rounded-md relative group">
                    <code className="text-xs break-all text-foreground font-mono">{redactedToken}</code>
                    <CopyButton
                      onClick={() => handleCopy(token, 'token')}
                      copied={copiedItem === 'token'}
                    />
                  </div>
                </div> */}

                {/* MCP Command Display */}
                <div className="mb-4">
                  <label className="block text-xs font-medium text-muted-foreground mb-2">
                    Add to Claude Code
                  </label>
                  <p className="text-xs text-muted-foreground mb-2">
                    Run this command in your terminal:
                  </p>
                  <div className="bg-background p-3 rounded-md relative group">
                    <code className="text-xs break-all text-foreground font-mono whitespace-pre-wrap">
                      {redactedMcpCommand}
                    </code>
                    <CopyButton
                      onClick={() => handleCopy(mcpCommand, 'command')}
                      copied={copiedItem === 'command'}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      }
    />
  );
};

export default ClaudeCodeSetupStep;
