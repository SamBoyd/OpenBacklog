import React, { useMemo, useState } from 'react';

/**
 * Standalone MCP setup page for onboarding
 * Generates API token and provides MCP installation command
 * @returns {React.ReactElement} The MCP setup page component
 */
const MCPSetupPage: React.FC = () => {
  // Track which item was copied for visual feedback
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  // Get MCP server domain from current origin
  const mcpServerDomain = window.location.origin;

  /**
   * Copies text to clipboard with visual feedback
   */
  const handleCopy = async (text: string, item: string) => {
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
  OpenBacklog \\
  ${mcpServerDomain}/mcp/`;
  }, [mcpServerDomain]);

  /**
   * Renders the copy button with visual feedback
   */
  const CopyButton: React.FC<{ onClick: () => void; copied: boolean }> = ({ onClick, copied }) => (
    <button
      onClick={onClick}
      className="absolute top-3 right-3 p-1.5 rounded transition-colors hover:bg-muted"
      title={copied ? 'Copied!' : 'Copy'}
      aria-label={copied ? 'Copied to clipboard' : 'Copy to clipboard'}
    >
      {copied ? (
        <svg className="w-5 h-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-5 h-5 text-muted-foreground hover:text-foreground transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );

  /**
   * Renders a code block with copy functionality
   */
  const CodeBlock: React.FC<{ code: string; language?: string; onCopy: () => void; copied: boolean }> = ({
    code,
    onCopy,
    copied
  }) => (
    <div className="relative bg-[#1e1e1e] rounded-md overflow-hidden">
      <pre className="p-4 overflow-x-auto text-sm">
        <code className="text-[#d4d4d4] font-mono whitespace-pre">{code}</code>
      </pre>
      <CopyButton onClick={onCopy} copied={copied} />
    </div>
  );

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            Connect OpenBacklog
          </h1>
          <p className="text-base text-muted-foreground">
            Set up the MCP server to manage your backlog with Claude
          </p>
        </div>

        {/* Setup Steps */}
        <div className="relative">
          <div className="absolute left-5 top-10 bottom-10 w-0.5 bg-border/50"></div>
          <div className="space-y-12">
            {/* Step 1: Install MCP Server */}
            <div>
              <div className="flex items-start gap-4 mb-4">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-background flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center font-bold text-foreground">
                    1
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-semibold text-foreground mb-3">
                    Install MCP Server
                  </h2>
                  <p className="text-base text-muted-foreground mb-4">
                    Run this command in your terminal:
                  </p>
                  <CodeBlock
                    code={mcpCommand}
                    onCopy={() => handleCopy(mcpCommand, 'command')}
                    copied={copiedItem === 'command'}
                  />
                </div>
              </div>
            </div>

            {/* Step 2: Authenticate MCP Server */}
            <div>
              <div className="flex items-start gap-4 mb-4">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-background flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center font-bold text-foreground">
                    2
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-semibold text-foreground mb-3">
                    Authenticate MCP Server
                  </h2>
                  <p className="text-base text-muted-foreground mb-4">
                    In Claude Code, authenticate the MCP server:
                  </p>
                  <CodeBlock
                    code={'/mcp'}
                    onCopy={() => handleCopy('/mcp', 'mcp')}
                    copied={copiedItem === 'mcp'}
                  />
                  <p className="text-base text-muted-foreground mt-3 mb-4">
                    Then select "<b>OpenBacklog</b>" from the list and then "<b>Authenticate</b>".
                  </p>
                </div>
              </div>
            </div>

            {/* Step 3: Create Workspace and Initiative */}
            <div>
              <div className="flex items-start gap-4 mb-4">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-background flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center font-bold text-foreground">
                    3
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-semibold text-foreground mb-3">
                    Create Workspace & Initiative
                  </h2>
                  <p className="text-base text-muted-foreground mb-4">
                    In Claude Code, ask to create your workspace and first initiative:
                  </p>
                  <div className="space-y-3">
                    <CodeBlock
                      code="Create a workspace called [name] in OpenBacklog"
                      onCopy={() => handleCopy("Create a workspace called [name] in OpenBacklog", 'workspace')}
                      copied={copiedItem === 'workspace'}
                    />
                    <CodeBlock
                      code="Create an initiative for [feature] in OpenBacklog"
                      onCopy={() => handleCopy("Create an initiative for [feature] in OpenBacklog", 'initiative')}
                      copied={copiedItem === 'initiative'}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Step 4: Access Web UI */}
            <div>
              <div className="flex items-start gap-4">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-background flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center font-bold text-foreground">
                    4
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-semibold text-foreground mb-3">
                    Access Web UI
                  </h2>
                  <span className="loading loading-dots loading-sm"></span>
                  <p className="text-base text-muted-foreground">
                    After creating your first initiative, the web interface unlocks automatically for visualizing your backlog and roadmap.
                  </p>

                  <div className="mt-5 border border-border/50 rounded-md flex items-center justify-center py-20">
                    <span className="text-sm text-muted-foreground animate-pulse">Waiting for new initiatives...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Note */}
        {/* <div className="mt-16 pt-8 border-t border-border">
          <p className="text-sm text-muted-foreground">
            Need help? See our{' '}
            <a href="/docs" className="text-primary hover:underline font-medium">
              documentation
            </a>
            .
          </p>
        </div> */}
      </div>
    </div>
  );
};

export default MCPSetupPage;
