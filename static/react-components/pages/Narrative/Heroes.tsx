import React from 'react';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useHeroes } from '#hooks/useHeroes';
import HeroCard from '#components/Narrative/HeroCard';
import { Skeleton } from '#components/reusable/Skeleton';

/**
 * Heroes page component - displays all user personas (heroes) for the workspace.
 * This is a read-only page. Hero creation/editing happens via MCP.
 * @returns {React.ReactElement} The heroes list page
 */
const Heroes: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const workspaceId = currentWorkspace?.id || '';
  const { heroes, isLoading, error } = useHeroes(workspaceId);

  const heroSkeletons = Array.from({ length: 3 }, (_, i) => i);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-foreground mb-2">
        Heroes
      </h1>
      <p className="text-muted-foreground mb-6">
        User personas you're building for. Create and edit heroes via Claude Code.
      </p>

      {error && (
        <div
          className="mb-6 p-4 rounded bg-destructive/10 text-destructive border border-destructive/20"
          data-testid="heroes-error"
        >
          Failed to load heroes. Please try again.
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="heroes-skeleton">
          {heroSkeletons.map((i) => (
            <div key={i} className="border border-border p-4 rounded">
              <div className="flex items-start justify-between mb-2">
                <Skeleton type="text" width="w-12" height="h-4" />
              </div>
              <Skeleton type="text" width="w-3/4" height="h-5" className="mb-2" />
              <Skeleton type="paragraph" />
            </div>
          ))}
        </div>
      ) : heroes.length === 0 ? (
        <div
          className="p-12 text-center border border-dashed border-border rounded bg-muted/20"
          data-testid="heroes-empty-state"
        >
          <p className="text-muted-foreground mb-2">No heroes defined yet</p>
          <p className="text-sm text-muted-foreground">
            Use Claude Code to define your first hero with: <code className="bg-muted px-2 py-1 rounded">/get_hero_definition_framework</code>
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="heroes-grid">
          {heroes.map((hero: typeof heroes[number]) => (
            <HeroCard
              key={hero.id}
              hero={hero}
              dataTestId={`hero-card-${hero.identifier}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Heroes;
