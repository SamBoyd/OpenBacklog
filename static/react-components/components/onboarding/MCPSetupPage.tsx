import React, { useMemo, useState } from 'react';
import { useOpenbacklogToken } from '#hooks/useOpenbacklogToken';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { PrimaryButton } from '#components/reusable/Button';

/**
 * Standalone MCP setup page for onboarding
 * Generates API token and provides MCP installation command
 * @returns {React.ReactElement} The MCP setup page component
 */
const MCPSetupPage: React.FC = () => {
  // Track which item was copied for visual feedback
  const [copiedItem, setCopiedItem] = useState<'command' | null>(null);

  // Get MCP server domain from current origin
  const mcpServerDomain = window.location.origin;

  /**
   * Copies text to clipboard with visual feedback
   */
  const handleCopy = async (text: string, item: 'command') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItem(item);
      setTimeout(() => setCopiedItem(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  /**
   * Generates the MCP command
   */
  const mcpCommand = useMemo((): string => {
    return `claude mcp add \\
  --transport=http \\
  openbacklog \\
  ${mcpServerDomain}/mcp/`;
  }, [mcpServerDomain]);

  /**
   * Renders the copy button with visual feedback
   */
  const CopyButton: React.FC<{ onClick: () => void; copied: boolean }> = ({ onClick, copied }) => (
    <button
      onClick={onClick}
      className="p-1.5 bg-background text-foreground rounded transition-colors hover:bg-background"
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
    <div className="flex items-center justify-center min-h-screen bg-background p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-3">
            Get Started with OpenBacklog
          </h1>
          <p className="text-lg text-muted-foreground">
            Connect Claude Code to start managing your backlog with AI
          </p>
        </div>

        {/* Setup Steps */}
        <div className="space-y-8">
          {/* Step 1: Install MCP Server */}
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-start mb-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold mr-3">
                1
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-foreground mb-2">
                  Install the OpenBacklog MCP Server
                </h2>
                <p className="text-muted-foreground">
                  First, run this command in your terminal to install the OpenBacklog MCP Server:
                </p>
                <div className="bg-background p-3 rounded-md">
                  <code className="text-sm text-foreground">
                    {mcpCommand}
                  </code>
                </div>
                <CopyButton
                  onClick={() => handleCopy(mcpCommand, 'command')}
                  copied={copiedItem === 'command'}
                />
              </div>
            </div>
          </div>

          {/* Step 2: Create Workspace and Initiative */}
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-start mb-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold mr-3">
                2
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-foreground mb-2">
                  Create Your Workspace and First Initiative
                </h2>
                <p className="text-muted-foreground mb-4">
                  In Claude Code, say:
                </p>
                <div className="space-y-2">
                  <div className="bg-background p-3 rounded-md">
                    <code className="text-sm text-foreground">
                      "Create a workspace called [name] in OpenBacklog"
                    </code>
                  </div>
                  <div className="bg-background p-3 rounded-md">
                    <code className="text-sm text-foreground">
                      "Create an initiative for [feature] in OpenBacklog"
                    </code>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Access Web UI */}
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold mr-3">
                3
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-foreground mb-2">
                  Web UI Will Unlock Automatically
                </h2>
                <p className="text-muted-foreground">
                  Once you create your first initiative via Claude Code, the web interface will unlock automatically. You'll be able to visualize your backlog, roadmap, and product strategy.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-8 text-center text-sm text-muted-foreground">
          Need help? Check out our{' '}
          <a href="/docs" className="text-primary hover:underline">
            documentation
          </a>
        </div>
      </div>
    </div>
  );
};

export default MCPSetupPage;
