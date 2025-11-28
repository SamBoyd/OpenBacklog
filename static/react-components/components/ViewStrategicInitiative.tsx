import React from 'react';
import { useParams } from '#hooks/useParams';
import { useStrategicInitiative } from '#hooks/useStrategicInitiative';
import ItemView from '#components/reusable/ItemView';
import NarrativeContextBar from '#components/NarrativeContextBar';
import StakesConflictSection from '#components/StakesConflictSection';
import TasksList from '#components/TasksList';
import { statusDisplay, TaskStatus } from '#types';

/**
 * Calculates the progress percentage from tasks
 * @param {any[]} tasks - Array of tasks with status field
 * @returns {number} Progress percentage (0-100)
 */
const calculateProgress = (tasks: any[] | undefined): number => {
  if (!tasks || tasks.length === 0) return 0;
  const completedTasks = tasks.filter((task: any) => task.status === 'DONE').length;
  return Math.round((completedTasks / tasks.length) * 100);
};

/**
 * ViewStrategicInitiative displays a strategic initiative with full narrative context
 * Shows heroes, villains, conflicts, and tasks as "scenes"
 * @returns {React.ReactElement} The ViewStrategicInitiative component
 */
const ViewStrategicInitiative: React.FC = () => {
  const { initiativeId } = useParams();
  const { strategicInitiative, isLoading, error } = useStrategicInitiative(
    initiativeId || ''
  );

  if (!initiativeId) {
    return <div className="p-6">Initiative ID not found</div>;
  }

  if (isLoading) {
    return (
      <ItemView
        loading={true}
        identifier=""
        status=""
        isEntityLocked={false}
        error={null}
        onDelete={() => { }}
      >
        <div className="animate-pulse">Loading strategic initiative...</div>
      </ItemView>
    );
  }

  if (error || !strategicInitiative) {
    return (
      <ItemView
        loading={false}
        identifier=""
        status=""
        isEntityLocked={false}
        error={error ? (error as Error).message : 'Strategic initiative not found'}
        onDelete={() => { }}
      >
        <div className="text-center py-8">
          <p className="text-muted-foreground">
            This initiative doesn't have strategic context defined yet.
          </p>
        </div>
      </ItemView>
    );
  }

  const initiative = strategicInitiative.initiative;
  const tasks = initiative?.tasks || [];
  const progress = calculateProgress(tasks);
  const scenesCount = {
    total: tasks.length,
    completed: tasks.filter((t: any) => t.status === 'DONE').length,
  };

  return (
    <>
      <ItemView
        identifier={initiative?.identifier}
        status={initiative?.status ? statusDisplay(initiative.status) : ''}
        loading={isLoading}
        error={error ? (error as Error).message : null}
        isEntityLocked={false}
        onDelete={() => { }}
        createdAt={initiative?.created_at}
        updatedAt={initiative?.updated_at}
        dataTestId="view-strategic-initiative"
      >
        {/* Narrative Context Bar */}
        <NarrativeContextBar
          parentArc={strategicInitiative.theme}
          heroes={strategicInitiative.heroes || []}
          villains={strategicInitiative.villains || []}
          progress={progress}
          scenesCount={scenesCount}
        />

        {/* Main Content */}
        <div className="mt-6 pb-6">
          {/* Two-column layout */}
          <div className="flex flex-row w-full space-x-6">
            {/* Left Column - Content */}
            <div className="space-y-6 flex-grow">
              {/* Why This Beat Matters Section */}
              <div className="border border-border rounded-lg p-6 bg-background/50">
                <h2 className="text-xl font-semibold text-foreground mb-3">
                  Why This Beat Matters
                </h2>

                {/* Description */}
                {strategicInitiative.description && (
                  <div className="mb-4">
                    <p className="text-sm text-muted-foreground font-semibold mb-2">
                      CONTEXT
                    </p>
                    <p className="text-base text-foreground">
                      {strategicInitiative.description}
                    </p>
                  </div>
                )}

                {/* Narrative Intent */}
                {strategicInitiative.narrative_intent && (
                  <div>
                    <p className="text-sm text-muted-foreground font-semibold mb-2">
                      NARRATIVE INTENT
                    </p>
                    <p className="text-base text-foreground italic">
                      {strategicInitiative.narrative_intent}
                    </p>
                  </div>
                )}

                {!strategicInitiative.description &&
                  !strategicInitiative.narrative_intent && (
                    <p className="text-sm text-muted-foreground italic">
                      No narrative context provided
                    </p>
                  )}
              </div>

              {/* Scenes (Tasks) Section */}
              <div className="border border-border rounded-lg p-6 bg-background/50">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-foreground">Scenes</h2>
                  <span className="text-sm text-muted-foreground">
                    {scenesCount.completed}/{scenesCount.total} completed
                  </span>
                </div>

                {tasks.length > 0 ? (
                  <TasksList
                    initiativeId={initiativeId}
                    reloadCounter={0}
                    filterToStatus={[TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]}
                  />
                ) : (
                  <div className="text-center py-8">
                    <p className="text-sm text-muted-foreground">
                      No scenes (tasks) have been defined yet
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Right Sidebar - Narrative Connections */}
            <div className='max-w-[450px]'>
              <div className="sticky top-24 space-y-6">
                {/* Narrative Connections Card */}
                <div className="border border-border rounded-lg p-4 bg-background/50">
                  <p className="text-xs text-muted-foreground font-semibold mb-4">
                    NARRATIVE CONNECTIONS
                  </p>

                  {/* Pillar */}
                  {strategicInitiative.pillar && (
                    <div className="mb-4">
                      <p className="text-xs text-muted-foreground font-semibold mb-2">
                        STRATEGIC PILLAR
                      </p>
                      <h3 className="text-base font-semibold text-foreground mb-2">
                        {strategicInitiative.pillar.name}
                      </h3>
                      {strategicInitiative.pillar.description && (
                        <p className="text-xs text-muted-foreground">
                          {strategicInitiative.pillar.description}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Parent Arc / Theme */}
                  {strategicInitiative.theme && (
                    <div className="mb-4">
                      <p className="text-xs text-muted-foreground font-semibold mb-2">
                        STORY ARC
                      </p>
                      <h3 className="text-base font-semibold text-foreground mb-2">
                        {strategicInitiative.theme.name}
                      </h3>
                      {strategicInitiative.theme.description && (
                        <p className="text-xs text-muted-foreground">
                          {strategicInitiative.theme.description}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Hero */}
                  {strategicInitiative.heroes?.[0] && (
                    <div className="mb-4">
                      <p className="text-xs text-muted-foreground font-semibold mb-2">
                        HERO
                      </p>
                      <p className="text-sm font-medium text-foreground">
                        {strategicInitiative.heroes[0].name}
                      </p>
                      {strategicInitiative.heroes[0].is_primary && (
                        <p className="text-xs text-primary font-semibold">
                          Primary
                        </p>
                      )}
                    </div>
                  )}

                  {/* Villain */}
                  {strategicInitiative.villains?.[0] && (
                    <div>
                      <p className="text-xs text-muted-foreground font-semibold mb-2">
                        OBSTACLE
                      </p>
                      <p className="text-sm font-medium text-foreground">
                        {strategicInitiative.villains[0].name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Severity: {strategicInitiative.villains[0].severity}/5
                      </p>
                    </div>
                  )}
                </div>

                {/* Stakes & Conflict Section */}
                <StakesConflictSection
                  conflicts={strategicInitiative.conflicts || []}
                />

                {/* Related Lore Section */}
                <div className="border border-border rounded-lg p-4 bg-background/50">
                  <p className="text-xs text-muted-foreground font-semibold mb-2">
                    RELATED LORE
                  </p>
                  <p className="text-sm text-muted-foreground italic">
                    No related lore linked yet
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ItemView>
    </>
  );
};

export default ViewStrategicInitiative;
