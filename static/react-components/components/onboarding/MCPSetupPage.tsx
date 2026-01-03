import React, { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useOnboardingPolling, FoundationProgress } from '#hooks/useOnboardingPolling';

/**
 * Progress item for the strategic foundation checklist
 */
interface ProgressItemProps {
  label: string;
  completed: boolean;
  isActive: boolean;
}

/**
 * Renders a single progress checklist item
 */
const ProgressItem: React.FC<ProgressItemProps> = ({ label, completed, isActive }) => (
  <div className={`flex items-center gap-3 py-1.5 ${isActive && !completed ? 'animate-pulse' : ''}`}>
    {completed ? (
      <svg className="w-5 h-5 text-success flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ) : (
      <div className={`w-5 h-5 rounded-full border-2 flex-shrink-0 ${isActive ? 'border-primary' : 'border-muted-foreground/30'}`} />
    )}
    <span className={`text-sm ${completed ? 'text-success' : isActive ? 'text-foreground' : 'text-muted-foreground/50'}`}>
      {label}
    </span>
  </div>
);

/**
 * Calculates which progress item is currently active based on foundation progress
 */
function getActiveStep(progress: FoundationProgress): string {
  if (!progress.hasVision) return 'vision';
  if (!progress.hasHeroes) return 'heroes';
  if (!progress.hasVillains) return 'villains';
  if (!progress.hasPillars) return 'pillars';
  if (!progress.hasOutcomes) return 'outcomes';
  if (!progress.hasThemes) return 'themes';
  if (!progress.hasInitiative) return 'initiative';
  return 'complete';
}

/**
 * Standalone MCP setup page for onboarding
 * Generates API token and provides MCP installation command
 * Polls for workspace and strategic foundation creation to unlock the web interface
 * @returns {React.ReactElement} The MCP setup page component
 */
const MCPSetupPage: React.FC = () => {
  const [copiedItem, setCopiedItem] = useState<string | null>(null);
  const navigate = useNavigate();
  const { status, hasWorkspace, initiativeCount, foundationProgress } = useOnboardingPolling();

  useEffect(() => {
    if (status === 'complete') {
      const timer = setTimeout(() => {
        navigate('/workspace/initiatives');
      }, 2000);

      return () => {
        clearTimeout(timer);
      };
    }
    return undefined;
  }, [status, navigate]);

  const mcpServerDomain = window.location.origin;

  const handleCopy = async (text: string, item: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItem(item);
      setTimeout(() => setCopiedItem(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const executionCommand = useMemo((): string => {
    return `claude mcp add \\
  --transport=http \\
  OpenBacklogCoding \\
  ${mcpServerDomain}/mcp/execution/`;
  }, [mcpServerDomain]);

  const strategyCommand = useMemo((): string => {
    return `claude mcp add \\
  --transport=http \\
  OpenBacklogPlanning \\
  ${mcpServerDomain}/mcp/planning/`;
  }, [mcpServerDomain]);

  const CopyButton: React.FC<{ onClick: (e: React.MouseEvent) => void; copied: boolean }> = ({ onClick, copied }) => (
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

  const CodeBlock: React.FC<{ code: string; onCopy: () => void; copied: boolean }> = ({
    code,
    onCopy,
    copied
  }) => (
    <div 
      className="relative bg-[#1e1e1e] rounded-md overflow-hidden cursor-pointer group"
      onClick={onCopy}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onCopy(); }}
    >
      <pre className="p-4 overflow-x-auto text-sm">
        <code className="text-[#d4d4d4] font-mono whitespace-pre group-hover:text-white transition-colors">{code}</code>
      </pre>
      <CopyButton onClick={(e) => { e.stopPropagation(); onCopy(); }} copied={copied} />
    </div>
  );

  const activeStep = getActiveStep(foundationProgress);
  const isPollingFoundation = status === 'polling-foundation';

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
            {/* Step 1: Install MCP Servers */}
            <div>
              <div className="flex items-start gap-4 mb-4">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-background flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center font-bold text-foreground">
                    1
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-semibold text-foreground mb-3">
                    Install MCP Servers
                  </h2>
                  <p className="text-base text-muted-foreground mb-4">
                    OpenBacklog provides two MCP servers optimized for different workflows. Run both commands in your terminal:
                  </p>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium text-foreground">Strategy Server</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">35+ tools</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        Full toolset for strategic planning, vision, heroes, villains, and roadmap management.
                      </p>
                      <CodeBlock
                        code={strategyCommand}
                        onCopy={() => handleCopy(strategyCommand, 'strategy')}
                        copied={copiedItem === 'strategy'}
                      />
                    </div>

                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium text-foreground">Execution Server</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-success/10 text-success">5 tools</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        Minimal toolset for coding workflows. Uses less context, leaving more room for code.
                      </p>
                      <CodeBlock
                        code={executionCommand}
                        onCopy={() => handleCopy(executionCommand, 'execution')}
                        copied={copiedItem === 'execution'}
                      />
                    </div>

                    <div className="mt-4 p-3 rounded-lg bg-muted/10 border border-border/50">
                      <p className="text-sm text-muted-foreground">
                        <span className="font-medium text-foreground">Why two servers?</span> Tool definitions consume context tokens. When coding, use the execution server to maximize context for your code. Switch to strategy when planning.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 2: Authenticate MCP Servers */}
            <div>
              <div className="flex items-start gap-4 mb-4">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-background flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center font-bold text-foreground">
                    2
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-semibold text-foreground mb-3">
                    Authenticate MCP Servers
                  </h2>
                  <p className="text-base text-muted-foreground mb-4">
                    In Claude Code, authenticate both MCP servers:
                  </p>
                  <CodeBlock
                    code={'/mcp'}
                    onCopy={() => handleCopy('/mcp', 'mcp')}
                    copied={copiedItem === 'mcp'}
                  />
                  <p className="text-base text-muted-foreground mt-3 mb-4">
                    Select each server (<b>OpenBacklogPlanning</b> and <b>OpenBacklogCoding</b>) and choose "<b>Authenticate</b>".
                  </p>
                  <div className="rounded-lg text-muted-foreground">
                    <p className="text-base text-muted-foreground">
                      Optional: Skip tool approval prompts: Type
                      <code className="px-1.5 py-0.5 bg-muted/10 rounded font-mono">/permissions</code> and add <code className="px-1.5 py-0.5 bg-muted/10 rounded font-mono">mcp__OpenBacklogCoding</code> and <code className="px-1.5 py-0.5 bg-muted/10 rounded font-mono">mcp__OpenBacklogPlanning</code> to the allow list.
                    </p>
                  </div>

                  <div className="mt-4 p-3 rounded-lg bg-primary/5 border border-primary/20">
                    <p className="text-sm text-muted-foreground">
                      <span className="font-medium text-primary">For onboarding:</span> Disable <b>OpenBacklogCoding</b> until you complete strategic planning. Use <code className="px-1.5 py-0.5 bg-muted/10 rounded font-mono">/mcp</code> → select <b>OpenBacklogCoding</b> → <b>Disable</b>. You can re-enable it when you start coding.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 3: Create Workspace */}
            <div>
              <div className="flex items-start gap-4 mb-4">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-background flex items-center justify-center">
                  <div className="w-8 h-8 rounded-full bg-card border border-border flex items-center justify-center font-bold text-foreground">
                    3
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-semibold text-foreground mb-3">
                    Create Workspace
                  </h2>
                  <p className="text-base text-muted-foreground mb-4">
                    In Claude Code, ask to create your workspace:
                  </p>
                  <div className="space-y-3">
                    <CodeBlock
                      code="Create a workspace in OpenBacklog called {your workspace name}"
                      onCopy={() => handleCopy("Create a workspace in OpenBacklog called ", 'workspace')}
                      copied={copiedItem === 'workspace'}
                    />
                  </div>
                  {status === 'polling-workspace' && (
                    <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                      <span>Waiting for workspace creation...</span>
                    </div>
                  )}
                  {hasWorkspace && (
                    <div className="mt-4 flex items-center gap-2 text-sm text-success">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Workspace created! Claude will now guide your strategic planning.</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Step 4: Build Strategic Foundation */}
            <div>
              <div className="flex items-start gap-4">
                <div className="relative z-10 flex-shrink-0 w-10 h-10 rounded-full bg-background flex items-center justify-center">
                  <div className={`w-8 h-8 rounded-full bg-card border flex items-center justify-center font-bold ${
                    status === 'polling-workspace' ? 'border-border/50 text-muted-foreground' : 'border-border text-foreground'
                  }`}>
                    4
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className={`text-2xl font-semibold mb-3 ${
                    status === 'polling-workspace' ? 'text-muted-foreground' : 'text-foreground'
                  }`}>
                    Build Your Strategic Foundation
                  </h2>
                  <p className={`text-base mb-2 ${
                    status === 'polling-workspace' ? 'text-muted-foreground/50' : 'text-muted-foreground'
                  }`}>
                    Claude guides you through a ~10-15 minute conversation to define your product strategy: vision, who you're building for, their challenges, and your approach.
                  </p>
                  <p className={`text-sm mb-4 ${
                    status === 'polling-workspace' ? 'text-muted-foreground/50' : 'text-muted-foreground'
                  }`}>
                    Just follow Claude's questions naturally. The web interface unlocks when complete.
                  </p>

                  {/* Progress Tracker */}
                  <div className={`mt-4 border rounded-lg p-5 ${
                    status === 'polling-workspace' ? 'border-border/30 bg-muted/5' : 'border-border/50 bg-card/50'
                  }`}>
                    {status === 'polling-workspace' && (
                      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground/50">
                        <span className="text-sm">Complete Step 3 first</span>
                      </div>
                    )}

                    {isPollingFoundation && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between mb-4">
                          <span className="text-sm font-medium text-foreground">Strategic Planning Progress</span>
                          <span className="text-xs text-muted-foreground">~10-15 min</span>
                        </div>
                        <ProgressItem 
                          label="Vision defined" 
                          completed={foundationProgress.hasVision} 
                          isActive={activeStep === 'vision'}
                        />
                        <ProgressItem 
                          label="Hero identified" 
                          completed={foundationProgress.hasHeroes} 
                          isActive={activeStep === 'heroes'}
                        />
                        <ProgressItem 
                          label="Challenge captured" 
                          completed={foundationProgress.hasVillains} 
                          isActive={activeStep === 'villains'}
                        />
                        <ProgressItem 
                          label="Strategy pillars set" 
                          completed={foundationProgress.hasPillars} 
                          isActive={activeStep === 'pillars'}
                        />
                        <ProgressItem 
                          label="Success outcomes defined" 
                          completed={foundationProgress.hasOutcomes} 
                          isActive={activeStep === 'outcomes'}
                        />
                        <ProgressItem 
                          label="Focus area selected" 
                          completed={foundationProgress.hasThemes} 
                          isActive={activeStep === 'themes'}
                        />
                        <ProgressItem 
                          label="First initiative created" 
                          completed={foundationProgress.hasInitiative} 
                          isActive={activeStep === 'initiative'}
                        />
                      </div>
                    )}

                    {status === 'complete' && (
                      <div className="flex flex-col items-center gap-3 py-4">
                        <svg className="w-12 h-12 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <div className="text-center">
                          <p className="text-base font-semibold text-success mb-1">
                            {initiativeCount} {initiativeCount === 1 ? 'initiative' : 'initiatives'} created!
                          </p>
                          <p className="text-sm text-muted-foreground">Redirecting to web interface...</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MCPSetupPage;
