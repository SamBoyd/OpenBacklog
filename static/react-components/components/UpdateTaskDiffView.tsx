import React from 'react';
import { GrList } from 'react-icons/gr';
import { FileData } from 'react-diff-view';

import { TaskDto, TaskStatus, ChecklistItemDto, EntityType } from '#types';

import DiffItemView from './reusable/DiffItemView';
import EntityDetailsEditor from '#components/reusable/EntityDetailsEditor';

import DescriptionDiffView from './diffs/DescriptionDiffView';
import TitleDiffView from './diffs/TitleDiffView';

import TitleInput from './reusable/TitleInput';
import EntityDescriptionEditor from './EntityDescriptionEditor';
import { UnifiedSuggestion } from '#hooks/diffs/useUnifiedSuggestions';
import { ResolutionMap } from '#hooks/diffs/useResolutionOperations';

// --- Grouped Prop Interfaces ---

interface TaskDiffProps {
    titleDiff: FileData[] | null;
    descriptionDiff: FileData[] | null;
    hasTitleChanges: boolean;
    hasDescriptionChanges: boolean;
    titleChanged: boolean;
    descriptionChanged: boolean;
    checklistItemsChanged: boolean;
    originalChecklistItems: ChecklistItemDto[]; // Use specific type
    changedChecklistItems: ChecklistItemDto[]; // Use specific type
}

interface CallbackProps {
    onSave: () => void;
    onAcceptField: (field: keyof TaskDto) => void;
    onRejectField: (field: keyof TaskDto) => void;
    onRollbackField: (field: keyof TaskDto) => void;
    onAcceptEntity: () => void;
    onRejectEntity: () => void;
    onRollbackEntity: () => void;
}

// --- Main Prop Interface using grouped props ---
export interface UpdateTaskDiffViewProps {
    task: TaskDto;
    entitySuggestion: UnifiedSuggestion;
    resolutions: ResolutionMap;

    // legacy props
    taskDiff: TaskDiffProps;
    callbacks: CallbackProps;
    allResolved: boolean; // Keep combined state separate or add to a 'combinedState' group? Keeping separate for now.
}

const UpdateTaskDiffView: React.FC<UpdateTaskDiffViewProps> = ({
    task,
    entitySuggestion,
    resolutions,

    // legacy props
    taskDiff,
    callbacks,
    allResolved,
}) => {
    // Destructure props within the component


    const {
        titleDiff,
        descriptionDiff,
        hasTitleChanges,
        hasDescriptionChanges,
        titleChanged,
        descriptionChanged,
        checklistItemsChanged,
        originalChecklistItems,
        changedChecklistItems,
    } = taskDiff;


    const {
        onSave,
        onAcceptField,
        onRejectField,
        onRollbackField,
        onAcceptEntity,
        onRejectEntity,
        onRollbackEntity,
    } = callbacks;


    // A no-op handler for inputs that should be read-only in this context
    const noOpHandler = () => { };

    const titleResolution = resolutions[`${entitySuggestion.path}.title`];
    const descriptionResolution = resolutions[`${entitySuggestion.path}.description`];

    const DiffItem = ({ children }: { children: React.ReactNode }) => <DiffItemView
        identifier={task?.identifier}
        status={task?.status ? TaskStatus[task.status as unknown as keyof typeof TaskStatus] : ''}
        loading={false}
        hasChanged={true} // Combine manual change and resolution status
        error={null}
        createdAt={task?.created_at}
        updatedAt={task?.updated_at}
        allResolved={allResolved}
        onAcceptAll={onAcceptEntity}
        onRejectAll={onRejectEntity}
        onRollbackAll={onRollbackEntity}
        onSave={onSave}
        dataTestId="view-task-diff"
    >
        {children}
    </DiffItemView>


    // --- JSX structure will be moved here ---
    return (
        <DiffItem >
            <div
                className={
                    `mt-4 p-4 border border-border bg-background rounded flex flex-col gap-4`
                }
                data-testid="content"
            >
                {/* Title */}
                {(hasTitleChanges || titleChanged) ? (
                    <TitleDiffView
                        originalValue={entitySuggestion?.originalValue?.title || ''}
                        changedValue={entitySuggestion?.suggestedValue?.title || ''}
                        diff={titleDiff || null}
                        isResolved={titleResolution?.isResolved || false}
                        resolvedValue={titleResolution?.resolvedValue}
                        onAccept={() => onAcceptField?.('title')}
                        onReject={() => onRejectField?.('title')}
                        onRollback={() => onRollbackField?.('title')}
                    />
                ) : (
                    <TitleInput
                        value={task.title}
                        onChange={noOpHandler}
                        loading={false}
                        placeholder="Title of your task"
                        disabled={true}
                    />
                )}

                {/* --- Details Section --- */}
                <EntityDetailsEditor
                    entityType={EntityType.TASK}
                    data={task}
                    onFieldChange={noOpHandler}
                    onPropertyChange={noOpHandler}
                    onAddField={noOpHandler}
                    onDeleteField={noOpHandler}
                    loading={false}
                    error={null}
                    fieldOptions={{
                        status: [TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.DONE],
                        type: ['CODING', 'TESTING', 'DOCUMENTATION', 'DESIGN'],
                    }}
                />

                {/* Description */}
                {(hasDescriptionChanges || descriptionChanged) ? (
                    <DescriptionDiffView
                        originalValue={entitySuggestion?.originalValue?.description || ''}
                        changedValue={entitySuggestion?.suggestedValue?.description || ''}
                        diff={descriptionDiff || null}
                        isResolved={descriptionResolution?.isResolved || false}
                        resolvedValue={descriptionResolution?.resolvedValue}
                        onAccept={() => onAcceptField?.('description')}
                        onReject={() => onRejectField?.('description')}
                        onRollback={() => onRollbackField?.('description')}
                    />
                ) : (
                    <EntityDescriptionEditor
                        description={task?.description || ''}
                        onChange={(value: string) => { }}
                        loading={false}
                        className='border'
                        disabled={true}
                    />
                )}

                <div className="mt-2 mb-8" data-testid="checklist-section">
                    <div className="flex items-baseline w-fit text-foreground h-8">
                        <GrList />
                        <span className="ml-2">Checklist</span>
                    </div>

                    {/* Checklist */}
                    <ul className="list-disc pl-5 mt-2 space-y-1">
                        {task.checklist.map((item, index) => (
                            <li key={index} className={`text-foreground ${item.is_complete ? 'line-through' : ''}`}>
                                {item.title}
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </DiffItem>
    );
};

export default UpdateTaskDiffView;
