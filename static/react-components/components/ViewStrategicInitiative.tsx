import React from 'react';
import { useParams } from '#hooks/useParams';
import { useNavigate } from 'react-router';
import { useStrategicInitiative } from '#hooks/useStrategicInitiative';
import ItemView from '#components/reusable/ItemView';
import { Button, NoBorderButton, CompactButton } from '#components/reusable/Button';
import InitiativeProgressBar from '#components/reusable/InitiativeProgressBar';
import InitiativeStatusBadge from '#components/reusable/InitiativeStatusBadge';
import HeroCard from '#components/reusable/HeroCard';
import VillainCard from '#components/reusable/VillainCard';
import StakesConflictSection from '#components/StakesConflictSection';
import InitiativeTasksList from '#components/InitiativeTasksList';
import MarkdownPreview from '#components/reusable/MarkdownPreview';
import { statusDisplay, TaskStatus } from '#types';
import { Compass, Pencil, Plus, Skull, Sparkles, Target, User } from 'lucide-react';

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
  const navigate = useNavigate();
  const { strategicInitiative, isLoading, error } = useStrategicInitiative(
    initiativeId || ''
  );

  /**
   * Handles navigation to task detail view
   * @param {string} taskId - The ID of the task to view
   */
  const handleTaskClick = (taskId: string) => {
    if (initiativeId) {
      navigate(`/workspace/initiatives/${initiativeId}/tasks/${taskId}`);
    }
  };

  const handleViewTheme = (themeId: string) => {
    if (initiativeId) {
      navigate(`/workspace/story-bible/theme/${themeId}`);
    }
  };

  const handleViewPillar = (pillarId: string) => {
    if (initiativeId) {
      navigate(`/workspace/story-bible/pillar/${pillarId}`);
    }
  };

  const handleViewHero = (heroId: string) => {
    if (initiativeId) {
      navigate(`/workspace/story-bible?tab=heroes`);
    }
  };

  const handleViewVillain = (villainId: string) => {
    if (initiativeId) {
      navigate(`/workspace/story-bible?tab=villains`);
    }
  };

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
                    <NoBorderButton disabled={true} onClick={() => { }} className="p-2">
                      <Pencil size={16} className="text-muted-foreground" />
                    </NoBorderButton>
                  </div>
                  <MarkdownPreview
                    content={initiative.description}
                    showHeader={false}
                    className="text-base text-muted-foreground"
                  />
                </div>
              )}

              {/* Why This Beat Matters Section */}
              <div className="border border-border rounded-lg p-6 bg-background">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-normal text-foreground">
                    Why This Beat Matters
                  </h2>
                  <NoBorderButton disabled={true} onClick={() => { }} className="p-2">
                    <Pencil size={16} className="text-muted-foreground" />
                  </NoBorderButton>
                </div>

                {strategicInitiative.description && (
                  <div className="mb-4">
                    <MarkdownPreview
                      content={strategicInitiative.description}
                      showHeader={false}
                      className="text-base text-muted-foreground"
                    />
                  </div>
                )}

                {strategicInitiative.narrative_intent && (
                  <div>
                    <MarkdownPreview
                      content={strategicInitiative.narrative_intent}
                      showHeader={false}
                      className="text-base text-muted-foreground italic"
                    />
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
                    <Button onClick={() => { }} className="text-sm" disabled={true}>
                      <Plus size={16} />
                      Add Task
                    </Button>
                    <Button
                      onClick={() => { }}
                      className="text-sm bg-primary text-primary-foreground hover:bg-primary/90"
                      disabled={true}
                    >
                      <Sparkles size={16} />
                      Decompose Task
                    </Button>
                  </div>
                </div>

                <InitiativeTasksList
                  tasks={tasks}
                  onTaskClick={handleTaskClick}
                />
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
                    <NoBorderButton disabled={true} onClick={() => { }} className="p-2">
                      <Pencil size={16} className="text-muted-foreground" />
                    </NoBorderButton>
                  </div>

                  <div className="space-y-4">
                    {/* Roadmap Theme */}
                    {strategicInitiative.theme && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-muted-foreground">
                            <Target className="w-4 h-4"/>
                          </span>
                          <p className="text-xs text-muted-foreground font-medium">ROADMAP THEME</p>
                        </div>
                        <div className="border border-border rounded-lg p-3">
                          <p className="text-sm font-medium text-foreground">
                            {strategicInitiative.theme.name}
                          </p>
                          {strategicInitiative.theme.status && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {strategicInitiative.theme.status}
                            </p>
                          )}
                          {strategicInitiative.theme.description && (
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {strategicInitiative.theme.description}
                            </p>
                          )}
                          <CompactButton
                            onClick={() => handleViewTheme(strategicInitiative.theme.id)}
                            className="font-medium mt-2 text-foreground"
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
                          <span className="text-muted-foreground">
                            <Compass className="w-4 h-4"/>
                          </span>
                          <p className="text-xs text-muted-foreground font-medium">STRATEGIC PILLAR</p>
                        </div>
                        <div className="border border-border rounded-lg p-3">
                          <p className="text-sm font-medium text-foreground">
                            {strategicInitiative.pillar.name}
                          </p>
                          {strategicInitiative.pillar.description && (
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                              {strategicInitiative.pillar.description}
                            </p>
                          )}
                          <CompactButton
                            onClick={() => handleViewPillar(strategicInitiative.pillar.id)}
                            className="font-medium mt-2 text-foreground"
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
                          <span className="text-primary"><User size={16} /></span>
                          <p className="text-xs text-muted-foreground font-medium">HERO</p>
                        </div>
                        <HeroCard 
                          hero={heroes[0]}
                          onViewDetail={() => handleViewHero(heroes[0].id)}
                        />
                      </div>
                    )}

                    {/* Villains */}
                    {villains.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Skull className="w-4 h-4 text-destructive" />
                          <p className="text-xs text-muted-foreground font-medium">
                            VILLAINS ({villains.length})
                          </p>
                        </div>
                        <div className="space-y-2">
                          {villains.map((villain) => (
                            <VillainCard 
                              key={villain.id} 
                              villain={villain} 
                              onViewDetail={() => handleViewVillain(villain.id)}
                            />
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
                    <NoBorderButton disabled={true} onClick={() => { }} className="p-2">
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
