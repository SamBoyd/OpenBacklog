import React from 'react';
import { useParams } from '#hooks/useParams';
import { useStrategicInitiative } from '#hooks/useStrategicInitiative';
import ItemView from '#components/reusable/ItemView';
import { Button, NoBorderButton, CompactButton } from '#components/reusable/Button';
import InitiativeProgressBar from '#components/reusable/InitiativeProgressBar';
import InitiativeStatusBadge from '#components/reusable/InitiativeStatusBadge';
import HeroCard from '#components/reusable/HeroCard';
import VillainCard from '#components/reusable/VillainCard';
import StakesConflictSection from '#components/StakesConflictSection';
import TasksList from '#components/TasksList';
import { statusDisplay, TaskStatus } from '#types';
import { Pencil, Plus, Sparkles } from 'lucide-react';

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
 * Shows the initiative title prominently, along with heroes, villains, conflicts, and tasks as "scenes"
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
  const heroes = strategicInitiative.heroes || [];
  const villains = strategicInitiative.villains || [];

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
        {/* Initiative Title Section - PRIMARY FOCUS */}
        <div className="flex items-center justify-between px-6 py-10 gap-4">
          <h1 className="text-2xl font-bold text-foreground flex-1">
            {initiative?.identifier}: {initiative?.title}
          </h1>
          <InitiativeStatusBadge status={initiative?.status} />
        </div>

        {/* Progress Bar */}
        <InitiativeProgressBar
          progress={progress}
          completed={scenesCount.completed}
          total={scenesCount.total}
        />

        {/* Main Content */}
        <div className="mt-6 pb-6 px-6">
          {/* Two-column layout */}
          <div className="flex flex-row w-full gap-8">
            {/* Left Column - Content */}
            <div className="space-y-6 flex-grow">
              {/* What This Initiative Does Section */}
              {initiative?.description && (
                <div className="border border-border rounded-lg p-6 bg-background">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-base font-normal text-foreground">
                      What This Initiative Does
                    </h2>
                    <NoBorderButton onClick={() => {}} className="p-2">
                      <Pencil size={16} className="text-muted-foreground" />
                    </NoBorderButton>
                  </div>
                  <p className="text-base text-muted-foreground leading-6">
                    {initiative.description}
                  </p>
                </div>
              )}

              {/* Why This Beat Matters Section */}
              <div className="border border-border rounded-lg p-6 bg-background">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-normal text-foreground">
                    Why This Beat Matters
                  </h2>
                  <NoBorderButton onClick={() => {}} className="p-2">
                    <Pencil size={16} className="text-muted-foreground" />
                  </NoBorderButton>
                </div>

                {strategicInitiative.description && (
                  <div className="mb-4">
                    <p className="text-base text-muted-foreground leading-6">
                      {strategicInitiative.description}
                    </p>
                  </div>
                )}

                {strategicInitiative.narrative_intent && (
                  <div>
                    <p className="text-base text-muted-foreground leading-6 italic">
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

              {/* Tasks Section */}
              <div className="border border-border rounded-lg p-6 bg-background">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-normal text-foreground">
                    Tasks ({scenesCount.total})
                  </h2>
                  <div className="flex items-center gap-2">
                    <Button onClick={() => {}} className="text-sm">
                      <Plus size={16} />
                      Add Task
                    </Button>
                    <Button
                      onClick={() => {}}
                      className="text-sm bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                      <Sparkles size={16} />
                      Decompose Task
                    </Button>
                  </div>
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
                      No tasks have been defined yet
                    </p>
                  </div>
                )}

                {tasks.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-border">
                    <NoBorderButton
                      onClick={() => {}}
                      className="w-full py-2 text-sm font-medium"
                    >
                      View All Tasks in Planning Board
                    </NoBorderButton>
                  </div>
                )}
              </div>
            </div>

            {/* Right Sidebar - Narrative Connections */}
            <div className="w-[400px] flex-shrink-0">
              <div className="sticky top-24 space-y-6">
                {/* Narrative Connections Card */}
                <div className="border border-border rounded-lg p-5 bg-background">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-normal text-foreground">
                      Narrative Connections
                    </h3>
                    <NoBorderButton onClick={() => {}} className="p-2">
                      <Pencil size={16} className="text-muted-foreground" />
                    </NoBorderButton>
                  </div>

                  <div className="space-y-4">
                    {/* Roadmap Theme */}
                    {strategicInitiative.theme && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-muted-foreground">📖</span>
                          <p className="text-xs text-muted-foreground font-medium">ROADMAP THEME</p>
                        </div>
                        <div className="bg-muted/50 border border-border rounded-lg p-3">
                          <p className="text-sm font-medium text-foreground">
                            {strategicInitiative.theme.name}
                          </p>
                          {strategicInitiative.theme.status && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {strategicInitiative.theme.status}
                            </p>
                          )}
                          <CompactButton
                            onClick={() => {}}
                            className="font-medium mt-2"
                          >
                            View Theme Detail
                          </CompactButton>
                        </div>
                      </div>
                    )}

                    {/* Strategic Pillar */}
                    {strategicInitiative.pillar && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-muted-foreground">🏛</span>
                          <p className="text-xs text-muted-foreground font-medium">STRATEGIC PILLAR</p>
                        </div>
                        <div className="bg-muted/50 border border-border rounded-lg p-3">
                          <p className="text-sm font-medium text-foreground">
                            {strategicInitiative.pillar.name}
                          </p>
                          {strategicInitiative.pillar.description && (
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {strategicInitiative.pillar.description}
                            </p>
                          )}
                          <CompactButton
                            onClick={() => {}}
                            className="font-medium mt-2"
                          >
                            View Pillar Detail
                          </CompactButton>
                        </div>
                      </div>
                    )}

                    {/* Hero */}
                    {heroes.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-primary">👤</span>
                          <p className="text-xs text-muted-foreground font-medium">HERO</p>
                        </div>
                        <HeroCard hero={heroes[0]} />
                      </div>
                    )}

                    {/* Villains */}
                    {villains.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-accent-foreground">⚔️</span>
                          <p className="text-xs text-muted-foreground font-medium">
                            VILLAINS ({villains.length})
                          </p>
                        </div>
                        <div className="space-y-2">
                          {villains.map((villain) => (
                            <VillainCard key={villain.id} villain={villain} />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Stakes & Conflict Section */}
                <div className="border border-border rounded-lg p-5 bg-background">
                  <StakesConflictSection
                    conflicts={strategicInitiative.conflicts || []}
                  />
                </div>

                {/* Related Lore Section */}
                <div className="border border-border rounded-lg p-5 bg-background">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-normal text-foreground">
                      Related Lore
                    </h3>
                    <NoBorderButton onClick={() => {}} className="p-2">
                      <Pencil size={16} className="text-muted-foreground" />
                    </NoBorderButton>
                  </div>
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
