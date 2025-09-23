import { InitiativeDto, ManagedEntityAction } from '#types';
import React from 'react';
import { 
    ResolutionState, 
    UnifiedSuggestion, 
    useSuggestionsToBeResolved 
} from '#contexts/SuggestionsToBeResolvedContext';
import { 
    ResolvedTasks,
    UnresolvedTaskDelete, 
    UnresolvedTaskUpdate, 
    UnchangedTask, 
    UnresolvedTaskCreate, 
    TaskDiffView 
} from './InitiativeTasksDiffViewComponents';

interface InitiativeTasksDiffViewProps {
    initiative: InitiativeDto;
}

// --- Main Diff View Component ---
const InitiativeTasksDiffView: React.FC<InitiativeTasksDiffViewProps> = ({
    initiative,
}) => {

    const {
        entitySuggestions,
        acceptAll,
        rejectAll,
        rollbackAll,
        getResolutionState
    } = useSuggestionsToBeResolved();

    const taskSuggestions: UnifiedSuggestion[] = entitySuggestions.filter(s => s.path.startsWith(`initiative.${initiative.identifier}.tasks`));
    const isFullyResolved = taskSuggestions.map(s => getResolutionState(s.path)).every(r => r.isResolved);

    // 1. Handle Resolved State
    if (isFullyResolved) {
        const newlyCreatedTasks = taskSuggestions
            .filter(s => s.action === ManagedEntityAction.CREATE)
            .filter(s => getResolutionState(s.path).isAccepted)
            .map(s => s.suggestedValue);
        const updatedTasks = initiative.tasks.map(task => {

            const updateSuggestion = taskSuggestions.find(s => s.path === `initiative.${initiative.identifier}.tasks.${task.identifier}`);

            if (!updateSuggestion) {
                return task;
            }

            const resolutionKey = `initiative.${initiative.identifier}.tasks.${task.identifier}`;
            const resolution = getResolutionState(resolutionKey);

            if (resolution?.isAccepted && updateSuggestion.action === ManagedEntityAction.UPDATE) {
                return { ...task, ...resolution.resolvedValue };
            }

            if (resolution?.isAccepted && updateSuggestion.action === ManagedEntityAction.DELETE) {
                return null;
            }

            return task;
        })

        const finalTasks = [...updatedTasks, ...newlyCreatedTasks].filter(t => t !== null);

        return <ResolvedTasks
            finalTasks={finalTasks}
            onRollback={() => rollbackAll(`initiative.${initiative.identifier}.tasks`)}
        />;
    }


    // 2. Render Diff Items
    const updatedTasks = initiative.tasks.map(task => {
        if (!task.identifier) return;

        const suggestion = taskSuggestions.find(s => s.path === `initiative.${initiative.identifier}.tasks.${task.identifier}`);

        if (suggestion?.action === ManagedEntityAction.DELETE) {
            return <UnresolvedTaskDelete key={`removed-${task.identifier}`} task={task} />;

        } else if (suggestion?.action === ManagedEntityAction.UPDATE) {
            return (
                <UnresolvedTaskUpdate
                    key={`modified-${task.identifier}`}
                    originalTask={task}
                    changedTask={suggestion.suggestedValue}
                />
            );

        } else {
            return <UnchangedTask key={`unchanged-${task.identifier}`} task={task} />
        }
    }).filter(
        t => t !== null
    );


    const createdTasks = taskSuggestions.filter(s => s.action === ManagedEntityAction.CREATE).map((suggestion, index) => {
        return <UnresolvedTaskCreate key={`new-${index}`} task={suggestion.suggestedValue} />
    });

    const hasChanges = taskSuggestions.length > 0;

    return (
        <TaskDiffView
            isResolved={isFullyResolved}
            rejectAll={() => rejectAll(`initiative.${initiative.identifier}.tasks`)}
            acceptAll={() => acceptAll(`initiative.${initiative.identifier}.tasks`)}
            rollbackAll={() => rollbackAll(`initiative.${initiative.identifier}.tasks`)}
        >
            {!hasChanges && initiative.tasks.length > 0 ? (
                <div className="flex flex-col space-y-2">
                    {/* If no changes, show all original tasks as unchanged */}
                    {initiative.tasks.map(task => task.identifier ? // Check if task and task.identifier exist
                        <UnchangedTask key={`unchanged-${task.identifier}`} task={task} />
                        : null // Optionally handle tasks without identifiers if necessary
                    )}
                </div>
            ) : !hasChanges && initiative.tasks.length === 0 ? (
                <p className="text-foreground italic">No original tasks and no changes proposed.</p>
            ) : (
                <div className="flex flex-col space-y-2">
                    {updatedTasks}
                    {createdTasks}
                </div>
            )}
        </TaskDiffView>
    );
};

export default InitiativeTasksDiffView;
