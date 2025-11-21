import React, { useMemo, useState } from 'react';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useConflicts } from '#hooks/useConflicts';
import { ConflictStatus } from '#types';
import ConflictCard from '#components/Narrative/ConflictCard';
import { Skeleton } from '#components/reusable/Skeleton';

/**
 * Conflicts page component - displays all narrative tensions between heroes and villains.
 * This is a read-only page. Conflict creation/editing happens via MCP.
 * @returns {React.ReactElement} The conflicts list page
 */
const Conflicts: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const workspaceId = currentWorkspace?.id || '';

  const [selectedStatus, setSelectedStatus] = useState<ConflictStatus | 'all'>('all');
  const [groupByStatus, setGroupByStatus] = useState(false);

  const filters = {
    ...(selectedStatus !== 'all' && { status: selectedStatus as ConflictStatus }),
  };

  const { conflicts, isLoading, error } = useConflicts(filters);

  // Group conflicts by status if toggled
  const groupedConflicts = useMemo(() => {
    if (!conflicts || !groupByStatus) {
      return null;
    }

    return conflicts.reduce((acc: Record<ConflictStatus, typeof conflicts>, conflict: typeof conflicts[number]) => {
      if (!acc[conflict.status]) {
        acc[conflict.status] = [];
      }
      acc[conflict.status].push(conflict);
      return acc;
    }, {} as Record<ConflictStatus, typeof conflicts>);
  }, [conflicts, groupByStatus]);

  const conflictSkeletons = Array.from({ length: 3 }, (_, i) => i);

  const statusOptions = [
    { value: 'all', label: 'All Statuses' },
    { value: ConflictStatus.OPEN, label: 'Open' },
    { value: ConflictStatus.ESCALATING, label: 'Escalating' },
    { value: ConflictStatus.RESOLVING, label: 'Resolving' },
    { value: ConflictStatus.RESOLVED, label: 'Resolved' },
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-foreground mb-2">
        Conflicts
      </h1>
      <p className="text-muted-foreground mb-6">
        Narrative tensions between heroes and villains. Create and edit conflicts via Claude Code.
      </p>

      {error && (
        <div
          className="mb-6 p-4 rounded bg-destructive/10 text-destructive border border-destructive/20"
          data-testid="conflicts-error"
        >
          Failed to load conflicts. Please try again.
        </div>
      )}

      {/* Filter bar */}
      <div className="mb-6 flex flex-wrap gap-4" data-testid="conflicts-filters">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-muted-foreground">Status:</label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value as ConflictStatus | 'all')}
            className="px-3 py-1 text-sm rounded border border-border bg-background text-foreground"
            data-testid="conflict-status-filter"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => setGroupByStatus(!groupByStatus)}
          className={`px-3 py-1 text-sm rounded border ${
            groupByStatus
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border bg-background text-muted-foreground hover:bg-muted/50'
          }`}
          data-testid="group-by-status-toggle"
        >
          {groupByStatus ? 'Grouped by Status' : 'Group by Status'}
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-4" data-testid="conflicts-skeleton">
          {conflictSkeletons.map((i) => (
            <div key={i} className="border border-border p-4 rounded">
              <div className="flex items-center justify-between mb-3">
                <div className="flex gap-2">
                  <Skeleton type="text" width="w-12" height="h-4" />
                  <Skeleton type="text" width="w-16" height="h-4" />
                </div>
              </div>
              <div className="flex items-center gap-3 mb-3">
                <Skeleton type="text" width="w-20" height="h-4" />
                <Skeleton type="text" width="w-6" height="h-4" />
                <Skeleton type="text" width="w-20" height="h-4" />
              </div>
              <Skeleton type="paragraph" />
            </div>
          ))}
        </div>
      ) : !conflicts || conflicts.length === 0 ? (
        <div
          className="p-12 text-center border border-dashed border-border rounded bg-muted/20"
          data-testid="conflicts-empty-state"
        >
          <p className="text-muted-foreground mb-2">No conflicts created yet</p>
          <p className="text-sm text-muted-foreground">
            Use Claude Code to create hero-villain conflicts with: <code className="bg-muted px-2 py-1 rounded">/create_conflict</code>
          </p>
        </div>
      ) : groupedConflicts ? (
        <div className="space-y-8" data-testid="conflicts-grouped-list">
          {Object.entries(groupedConflicts).map(([status, statusConflicts]: [string, typeof conflicts]) => (
            <div key={status}>
              <h2 className="text-lg font-semibold text-foreground mb-4 capitalize">
                {status.toLowerCase().replace(/_/g, ' ')}
                <span className="ml-2 text-muted-foreground text-sm font-normal">
                  ({statusConflicts.length})
                </span>
              </h2>
              <div className="space-y-4">
                {statusConflicts.map((conflict: typeof conflicts[number]) => (
                  <ConflictCard
                    key={conflict.id}
                    conflict={conflict}
                    dataTestId={`conflict-card-${conflict.identifier}`}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4" data-testid="conflicts-list">
          {conflicts && conflicts.map((conflict: typeof conflicts[number]) => (
            <ConflictCard
              key={conflict.id}
              conflict={conflict}
              dataTestId={`conflict-card-${conflict.identifier}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Conflicts;
