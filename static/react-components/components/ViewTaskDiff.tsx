import React, { useEffect, useMemo } from 'react';

import { TaskDto, ManagedEntityAction, UpdateTaskModel, ChecklistItemDto, DeleteTaskModel, TaskStatus } from '#types';
import { UnifiedSuggestion, useSuggestionsToBeResolved } from '#contexts/SuggestionsToBeResolvedContext';

import { useTaskDiff } from '#hooks/diffs/useTaskDiff';


import UpdateTaskDiffView from './UpdateTaskDiffView';
import { buildBasePath } from '#hooks/diffs/basePath';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { DeleteTaskDiffView } from './diffs/DeleteTaskDiffView';
import DiffItemView from './reusable/DiffItemView';


interface ViewTaskDiffProps {
    task: TaskDto;
}

/**
 * ViewTaskDiff component for displaying task details with AI-suggested changes
 * @returns {React.ReactElement} The ViewTaskDiff component
 */
const ViewTaskDiff: React.FC<ViewTaskDiffProps> = ({ task }) => {
    const { initiativesData } = useInitiativesContext();

    const {
        entitySuggestions,
        resolutions,
        resolve,
        rollback,
        acceptAll,
        rejectAll,
        rollbackAll,
        getResolutionState,
        isFullyResolved,
        saveSuggestions,
    } = useSuggestionsToBeResolved();

    const initiative = useMemo(() => (initiativesData || []).find(i => i.id === task.initiative_id) || null, [initiativesData, task]);
    const basePath = buildBasePath(initiative?.identifier!, task.identifier)

    const taskEntitySuggestion: UnifiedSuggestion | undefined = entitySuggestions.find(s => s.path === basePath);

    const taskEntityResolution = getResolutionState(taskEntitySuggestion?.path!)

    if (!task || !taskEntitySuggestion) {
        return null;
    }

    if (taskEntitySuggestion.action === ManagedEntityAction.DELETE) {
        return (
            <DiffItemView
                identifier={task?.identifier}
                status={task?.status ? TaskStatus[task.status as unknown as keyof typeof TaskStatus] : ''}
                loading={false}
                hasChanged={true} // Combine manual change and resolution status
                error={null}
                createdAt={task?.created_at}
                updatedAt={task?.updated_at}
                allResolved={isFullyResolved(taskEntitySuggestion.path)}
                onAcceptAll={() => acceptAll(taskEntitySuggestion.path)}
                onRejectAll={() => rejectAll(taskEntitySuggestion.path)}
                onRollbackAll={() => rollbackAll(taskEntitySuggestion.path)}
                onSave={saveSuggestions}
                dataTestId="view-task-diff"
            >
                <DeleteTaskDiffView
                    taskData={task}
                    onAccept={() => resolve(taskEntitySuggestion.path, true)}
                    onReject={() => resolve(taskEntitySuggestion.path, false)}
                    onRollback={() => rollback(taskEntitySuggestion.path)}
                    isResolved={taskEntityResolution.isResolved}
                    accepted={taskEntityResolution.isAccepted}
                />
            </DiffItemView>
        )
    }

    if (taskEntitySuggestion.action === ManagedEntityAction.CREATE) {
        // there is no way for the user to navigate to the
        // new task since it doesnt have an id yet and we
        // rely on that for url navigation.
        return (
            <div>
                Can't navigate to the new task.
            </div>
        );
    }

    const {
        titleDiff,
        descriptionDiff,
        hasTitleChanges,
        hasDescriptionChanges,
        titleChanged,
        descriptionChanged,
        checklistItemsChanged,
        originalChecklistItems,
        changedChecklistItems
    } = useTaskDiff(
        task as TaskDto,
        taskEntitySuggestion.suggestedValue as UpdateTaskModel // Assume updatedTask is TaskDto here for diffing
    );

    const isUpdateFullyResolved = useMemo(() => {
        return isFullyResolved(taskEntitySuggestion.path);
    }, [taskEntitySuggestion.path, isFullyResolved]);

    return (
        <UpdateTaskDiffView
            task={task}
            entitySuggestion={taskEntitySuggestion}
            resolutions={resolutions}

            taskDiff={{
                titleDiff,
                descriptionDiff,
                hasTitleChanges,
                hasDescriptionChanges,
                titleChanged,
                descriptionChanged,
                checklistItemsChanged,
                originalChecklistItems: originalChecklistItems as ChecklistItemDto[], // Cast here
                changedChecklistItems: changedChecklistItems as ChecklistItemDto[], // Cast here
            }}

            callbacks={{
                onSave: saveSuggestions,

                onAcceptField: (field) => resolve(`${taskEntitySuggestion.path}.${field}`, true),
                onRejectField: (field) => resolve(`${taskEntitySuggestion.path}.${field}`, false),
                onRollbackField: (field) => rollbackAll(`${taskEntitySuggestion.path}.${field}`),

                onAcceptEntity: () => acceptAll(taskEntitySuggestion.path),
                onRejectEntity: () => rejectAll(taskEntitySuggestion.path),
                onRollbackEntity: () => rollbackAll(taskEntitySuggestion.path),
            }}

            allResolved={isUpdateFullyResolved}
        />
    );
};

export default ViewTaskDiff;
