import React, { useState } from 'react';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useVillains } from '#hooks/useVillains';
import { VillainType } from '#types';
import VillainCard from '#components/Narrative/VillainCard';
import { Skeleton } from '#components/reusable/Skeleton';

/**
 * Villains page component - displays all problems/obstacles (villains) for the workspace.
 * This is a read-only page. Villain creation/editing happens via MCP.
 * @returns {React.ReactElement} The villains list page
 */
const Villains: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const workspaceId = currentWorkspace?.id || '';

  const [selectedType, setSelectedType] = useState<VillainType | 'all'>('all');
  const [showDefeated, setShowDefeated] = useState(false);

  const filters = {
    ...(selectedType !== 'all' && { villainType: selectedType as VillainType }),
    ...(showDefeated === false && { isDefeated: false }),
  };

  const { villains, isLoading, error } = useVillains(workspaceId, filters);

  const villainSkeletons = Array.from({ length: 3 }, (_, i) => i);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-foreground mb-2">
        Villains
      </h1>
      <p className="text-muted-foreground mb-6">
        Problems and obstacles your product must overcome. Create and edit villains via Claude Code.
      </p>

      {error && (
        <div
          className="mb-6 p-4 rounded bg-destructive/10 text-destructive border border-destructive/20"
          data-testid="villains-error"
        >
          Failed to load villains. Please try again.
        </div>
      )}

      {/* Filter bar */}
      <div className="mb-6 flex flex-wrap gap-4" data-testid="villains-filters">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-muted-foreground">Type:</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as VillainType | 'all')}
            className="px-3 py-1 text-sm rounded border border-border bg-background text-foreground"
            data-testid="villain-type-filter"
          >
            <option value="all">All Types</option>
            <option value={VillainType.EXTERNAL}>External</option>
            <option value={VillainType.INTERNAL}>Internal</option>
            <option value={VillainType.TECHNICAL}>Technical</option>
            <option value={VillainType.WORKFLOW}>Workflow</option>
            <option value={VillainType.OTHER}>Other</option>
          </select>
        </div>

        <button
          onClick={() => setShowDefeated(!showDefeated)}
          className={`px-3 py-1 text-sm rounded border ${
            showDefeated
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border bg-background text-muted-foreground hover:bg-muted/50'
          }`}
          data-testid="show-defeated-toggle"
        >
          {showDefeated ? 'Showing Defeated' : 'Show Defeated'}
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="villains-skeleton">
          {villainSkeletons.map((i) => (
            <div key={i} className="border border-border p-4 rounded">
              <div className="flex items-start justify-between mb-2">
                <Skeleton type="text" width="w-12" height="h-4" />
              </div>
              <Skeleton type="text" width="w-3/4" height="h-5" className="mb-2" />
              <div className="flex gap-2 mb-3">
                <Skeleton type="text" width="w-16" height="h-4" />
                <Skeleton type="text" width="w-12" height="h-4" />
              </div>
              <Skeleton type="paragraph" />
            </div>
          ))}
        </div>
      ) : villains.length === 0 ? (
        <div
          className="p-12 text-center border border-dashed border-border rounded bg-muted/20"
          data-testid="villains-empty-state"
        >
          <p className="text-muted-foreground mb-2">No villains identified yet</p>
          <p className="text-sm text-muted-foreground">
            Use Claude Code to identify obstacles with: <code className="bg-muted px-2 py-1 rounded">/get_villain_definition_framework</code>
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="villains-grid">
          {villains.map((villain) => (
            <VillainCard
              key={villain.id}
              villain={villain}
              dataTestId={`villain-card-${villain.identifier}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Villains;
