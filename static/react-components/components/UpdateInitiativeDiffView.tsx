import React, { useEffect, useState } from 'react';
import { FileData } from 'react-diff-view';

import {
    InitiativeDto,
    TaskStatus,
    InitiativeStatus,
    EntityType,
} from '#types';

import { ResolutionMap, UnifiedSuggestion } from '#contexts/SuggestionsToBeResolvedContext';

import TitleDiffView from '#components/diffs/TitleDiffView';
import DescriptionDiffView from '#components/diffs/DescriptionDiffView';
import InitiativeTasksDiffView from '#components/diffs/InitiativeTasksDiffView';
import TasksList from '#components/TasksList';
import EntityDescriptionEditor from '#components/EntityDescriptionEditor';
import EntityDetailsEditor from '#components/reusable/EntityDetailsEditor';
import DiffItemView from '#components/reusable/DiffItemView';
import TitleInput from './reusable/TitleInput';
import { useUserPreferences } from '#hooks/useUserPreferences';

const noOpHandler = () => { };

interface UpdateInitiativeDiffViewProps {

    // Data props
    initiative: InitiativeDto;
    suggestion: UnifiedSuggestion;
    resolutions: ResolutionMap;

    // Diff data
    titleDiff: FileData[] | null;
    descriptionDiff: FileData[] | null;
    shouldShowTitleDiff: boolean;
    shouldShowDescriptionDiff: boolean;
    hasTasksDiff: boolean;

    allResolved: boolean;
    loading: boolean;

    // Field handlers
    onAcceptField: (field: string) => void;
    onRejectField: (field: string) => void;
    onRollbackField: (field: string) => void;

    // Combined handlers
    onAcceptAll: () => void;
    onRejectAll: () => void;
    onRollbackAll: () => void;
    onSave: () => void;
}

/**
 * ViewInitiativeDiff presentational component for displaying initiative diffs
 * @param props - Component props
 * @returns The ViewInitiativeDiff component
 */
const UpdateInitiativeDiffView: React.FC<UpdateInitiativeDiffViewProps> = ({
    // Data props
    initiative,
    suggestion,
    resolutions,

    // Diff data
    titleDiff,
    descriptionDiff,

    shouldShowTitleDiff,
    shouldShowDescriptionDiff,

    hasTasksDiff,

    // State props
    allResolved,
    loading,

    // Field handlers
    onAcceptField,
    onRejectField,
    onRollbackField,

    // Combined handlers
    onAcceptAll,
    onRejectAll,
    onRollbackAll,
    onSave
}) => {
    const [tasksReloadCounter, setTasksReloadCounter] = useState(0);
    const { preferences } = useUserPreferences();
    // Reload tasks handler
    const reloadTasks = () => {
        setTasksReloadCounter(prev => prev + 1);
    };

    const titleResolution = resolutions[`${suggestion.path}.title`];
    const descriptionResolution = resolutions[`${suggestion.path}.description`];

    return (
        <DiffItemView
            identifier={initiative?.identifier}
            status={initiative?.status ? InitiativeStatus[initiative.status as unknown as keyof typeof InitiativeStatus] : ''}
            loading={loading}
            hasChanged={true}
            error={null}
            createdAt={initiative?.created_at}
            updatedAt={initiative?.updated_at}
            allResolved={allResolved}
            onAcceptAll={onAcceptAll}
            onRejectAll={onRejectAll}
            onRollbackAll={onRollbackAll}
            onSave={allResolved ? onSave : () => { }}
            dataTestId="view-initiative-diff"
        >
            <div className="flex flex-col gap-4 p-4 mt-2 bg-background rounded border border-border">
                {/* Title - Conditionally render TitleDiffView or ResizingTextInput */}
                {shouldShowTitleDiff ? (
                    <TitleDiffView
                        originalValue={suggestion.originalValue?.title || ''}
                        changedValue={suggestion.suggestedValue?.title || ''}
                        diff={titleDiff || null}
                        isResolved={titleResolution?.isResolved || false}
                        resolvedValue={titleResolution?.resolvedValue}
                        onAccept={() => onAcceptField('title')}
                        onReject={() => onRejectField('title')}
                        onRollback={() => onRollbackField('title')}
                    />
                ) : (
                    <TitleInput
                        value={suggestion.originalValue?.title || ''}
                        onChange={noOpHandler}
                        disabled={true}
                    />
                )}

                {/* --- Details Section --- */}
                <EntityDetailsEditor
                    entityType={EntityType.INITIATIVE}
                    data={suggestion.originalValue}
                    onFieldChange={noOpHandler}
                    onPropertyChange={noOpHandler}
                    onAddField={noOpHandler}
                    onDeleteField={noOpHandler}
                    loading={false}
                    error={null}
                    fieldOptions={{
                        status: [InitiativeStatus.BACKLOG, InitiativeStatus.TO_DO, InitiativeStatus.IN_PROGRESS, InitiativeStatus.DONE],
                        type: ['FEATURE', 'BUGFIX', 'RESEARCH', 'CHORE'],
                    }}
                />


                {/* Description - Conditionally render DescriptionDiffView or EntityDescriptionEditor */}
                {shouldShowDescriptionDiff ? (
                    <DescriptionDiffView
                        originalValue={suggestion.originalValue?.description || ''}
                        changedValue={suggestion.suggestedValue?.description || ''}
                        diff={descriptionDiff || null}
                        isResolved={descriptionResolution?.isResolved || false}
                        resolvedValue={descriptionResolution?.resolvedValue}
                        onAccept={() => onAcceptField('description')}
                        onReject={() => onRejectField('description')}
                        onRollback={() => onRollbackField('description')}
                    />
                ) : (
                    <EntityDescriptionEditor
                        description={suggestion.originalValue?.description || ''}
                        onChange={noOpHandler}
                        testId="initiative-description-section"
                        disabled={true}
                    />
                )}

                {/* Tasks view */}
                {hasTasksDiff ? (
                    <InitiativeTasksDiffView
                        initiative={initiative}
                    />
                ) : (
                    <TasksList
                        initiativeId={initiative?.id || ''}
                        reloadCounter={tasksReloadCounter}
                        onUpdate={reloadTasks}
                        filterToStatus={preferences.selectedTaskStatuses as TaskStatus[]}
                    />
                )}
            </div>
        </DiffItemView>
    );
};

export default UpdateInitiativeDiffView;
