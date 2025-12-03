import React from 'react';
import { useParams } from '#hooks/useParams';
import { useStrategicInitiative } from '#hooks/useStrategicInitiative';
import ItemView from '#components/reusable/ItemView';
import { Button, NoBorderButton, CompactButton } from '#components/reusable/Button';
import StakesConflictSection from '#components/StakesConflictSection';
import TasksList from '#components/TasksList';
import { statusDisplay, TaskStatus, InitiativeStatus, HeroDto, VillainDto } from '#types';
import { Pencil, ExternalLink, Plus, Sparkles } from 'lucide-react';

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
 * Gets the status badge styling based on initiative status
 * @param {string} status - The initiative status
 * @returns {string} Tailwind CSS classes for the badge
 */
const getStatusBadgeStyle = (status: string | undefined): string => {
  switch (status) {
    case InitiativeStatus.IN_PROGRESS:
      return 'bg-status-in-progress border-status-in-progress text-status-in-progress-foreground';
    case InitiativeStatus.DONE:
      return 'bg-status-done border-status-done text-status-done-foreground';
    case InitiativeStatus.BLOCKED:
      return 'bg-destructive border-destructive text-destructive-foreground';
    case InitiativeStatus.TO_DO:
      return 'bg-status-todo border-status-todo text-status-todo-foreground';
    case InitiativeStatus.BACKLOG:
      return 'bg-muted border-muted text-muted-foreground';
    default:
      return 'bg-muted border-muted text-muted-foreground';
  }
};

/**
 * ProgressBar component for showing initiative completion progress
 */
interface ProgressBarProps {
  progress: number;
  completed: number;
  total: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, completed, total }) => (
  <div className="border-b border-border px-6 py-2.5">
    <div className="flex items-center gap-4">
      <div className="flex-1 flex flex-col gap-2">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Progress</span>
          <span className="text-foreground font-medium">{progress}%</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      <div className="text-sm text-muted-foreground whitespace-nowrap">
        Scenes: <span className="text-foreground font-medium">{completed} / {total}</span> complete
      </div>
    </div>
  </div>
);

/**
 * HeroCard component for displaying hero information with primary color styling
 */
interface HeroCardProps {
  hero: HeroDto;
}

const HeroCard: React.FC<HeroCardProps> = ({ hero }) => (
  <div className="bg-primary/10 border border-primary/20 rounded-lg p-3">
    <p className="text-sm font-medium text-foreground">{hero.name}</p>
    {hero.description && (
      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
        Core Promise: "{hero.description}"
      </p>
    )}
    <CompactButton
      onClick={() => {}}
      className="text-primary font-medium mt-2"
    >
      
      View Hero Detail
    </CompactButton>
  </div>
);

/**
 * VillainCard component for displaying villain information with accent/warning styling
 */
interface VillainCardProps {
  villain: VillainDto;
}

const VillainCard: React.FC<VillainCardProps> = ({ villain }) => (
  <div className="bg-accent/20 border border-accent/40 rounded-lg p-3">
    <div className="flex items-start gap-2">
      <span className="text-accent-foreground">⚠</span>
      <div className="flex-1">
        <p className="text-sm font-medium text-foreground">{villain.name}</p>
        {villain.description && (
          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
            {villain.description}
          </p>
        )}
        <p className="text-xs text-muted-foreground mt-0.5">
          Severity: {villain.severity}/5
        </p>
        <CompactButton
          onClick={() => {}}
          className="text-accent-foreground font-medium mt-2"
        >
          
          View Villain Detail
        </CompactButton>
      </div>
    </div>
  </div>
);

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
          <span
            className={`px-3 py-1 text-xs font-medium rounded-lg border ${getStatusBadgeStyle(initiative?.status)}`}
          >
            {statusDisplay(initiative?.status as any)}
          </span>
        </div>

        {/* Progress Bar */}
        <ProgressBar
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
              {/* What This Initiative Does Section - NEW */}
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

              {/* Scenes (Tasks) Section */}
              <div className="border border-border rounded-lg p-6 bg-background">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-normal text-foreground">
                    Scenes ({scenesCount.total})
                  </h2>
                  <div className="flex items-center gap-2">
                    <Button onClick={() => {}} className="text-sm">
                      <Plus size={16} />
                      Add Scene
                    </Button>
                    <Button
                      onClick={() => {}}
                      className="text-sm bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                      <Sparkles size={16} />
                      Decompose
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
                      No scenes (tasks) have been defined yet
                    </p>
                  </div>
                )}

                {tasks.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-border">
                    <NoBorderButton
                      onClick={() => {}}
                      className="w-full py-2 text-sm font-medium"
                    >
                      View All Scenes in Planning Board
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
