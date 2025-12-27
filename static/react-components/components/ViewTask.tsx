import React, { useEffect } from 'react';
import { GrList } from 'react-icons/gr';
import { useParams } from 'react-router';

import { EntityType, TaskDto, TaskStatus } from '#types';

import { useActiveEntity } from '#hooks/useActiveEntity';

import { useTasksContext } from '#contexts/TasksContext';
import ItemView from '#components/reusable/ItemView';
import EntityDetailsEditor from '#components/reusable/EntityDetailsEditor';

import DescriptionSection from './DescriptionSection';
import ChecklistItemsInput from './reusable/ChecklistItemsInput';
import TitleInput from './reusable/TitleInput';

/**
 * ViewTask component for displaying and editing task details
 * @returns {React.ReactElement} The ViewTask component
 */
const ViewTask = () => {
    const { taskId } = useParams();
    const {
        tasks,
        error,
        shouldShowSkeleton,
        updateTask,
        deleteTask,
        setTaskId,
        reloadTasks,
        isPolling,
        startPolling,
        stopPolling,
        updateChecklistItem,
        updateChecklistItemDebounced,
        addChecklistItem,
        removeChecklistItem,
        reorderChecklistItems,
    } = useTasksContext();

    // Update the context when taskId changes
    React.useEffect(() => {
        setTaskId(taskId || null);
    }, [taskId, setTaskId]);

    const { setActiveTask } = useActiveEntity();

    const task = tasks?.[0] || null;
    
    // State to manage overlay bypass for manual checklist editing
    const [manualChecklistEdit, setManualChecklistEdit] = React.useState(false);

    // Set this task as the active task when component mounts
    React.useEffect(() => {
        if (taskId) {
            setActiveTask(taskId);
            startPolling(5000);
        }

        return () => {
            setActiveTask(null);
        };
    }, [taskId, setActiveTask]);

    useEffect(() => {
        return () => {
            // Stop polling when component unmounts
            stopPolling();
        };
    }, [stopPolling])

    React.useEffect(() => {
        console.log('[ViewTask] isPolling', isPolling);
    }, [isPolling])

    /**
     * Whenever a field changes, update localData and mark as changed.
     */
    const handleFieldChange = async <K extends keyof TaskDto>(field: K, value: TaskDto[K]) => {
        const newValue = value !== '' ? value : null;
        const updated = { ...task, [field]: newValue };
        try {
            await updateTask({ ...updated, updated_at: new Date().toISOString() });
        } catch (err) {
            console.error('Failed to save changes', err);
        }
    };

    /**
     * Whenever a property changes, update localData and mark as changed.
     */
    const handlePropertyChange = async <K extends keyof TaskDto>(field_definition_id: string, value: TaskDto[K]) => {
        const prevProperties = task?.properties || {};
        const updatedProperties = { ...prevProperties, [field_definition_id]: value };
        const updated = { ...task, properties: updatedProperties };

        try {
            await updateTask({ ...updated, updated_at: new Date().toISOString() });
        } catch (err) {
            console.error('Failed to save changes', err);
        }
    };

    const handleDeleteTask = async () => {
        await deleteTask(taskId || '');
    };

    return (
        <ItemView
            identifier={task?.identifier}
            status={task?.status ? TaskStatus[task.status as unknown as keyof typeof TaskStatus] : ''}
            loading={shouldShowSkeleton}
            error={error}
            createdAt={task?.created_at}
            updatedAt={task?.updated_at}
            onDelete={handleDeleteTask}
            onRefresh={reloadTasks}
            isEntityLocked={false}
            dataTestId="view-task"
        >

            {/* --- Content --- */}
            <div
                className={`mt-4 p-4 border border-border rounded bg-background bg-opacity-80`}
                data-testid="content"
            >
                <TitleInput
                    value={task?.title || ''}
                    onChange={(value) => handleFieldChange('title', value)}
                    loading={shouldShowSkeleton}
                    placeholder="Title of your task"
                    maxLength={200}
                    showCharCount={true}
                />

                {/* --- Details Section --- */}
                <EntityDetailsEditor
                    entityType={EntityType.TASK}
                    data={task}
                    onFieldChange={(field, value) => handleFieldChange(field as keyof TaskDto, value)}
                    onPropertyChange={handlePropertyChange}
                    onAddField={(field, value) => {
                        handleFieldChange(field as keyof TaskDto, value);
                    }}
                    onDeleteField={(field) => {
                        handleFieldChange(field as keyof TaskDto, null);
                    }}
                    loading={shouldShowSkeleton}
                    error={error}
                    fieldOptions={{
                        status: [TaskStatus.TO_DO, TaskStatus.IN_PROGRESS, TaskStatus.DONE],
                        type: ['CODING', 'TESTING', 'DOCUMENTATION', 'DESIGN'],
                    }}
                />

                <DescriptionSection
                    description={task?.description || ''}
                    loading={shouldShowSkeleton}
                />

                <div className="mb-8 flex flex-col gap-4" data-testid="description-section">
                    <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light text-foreground">
                        <GrList />
                        <span className="ml-2">Checklist</span>
                    </div>
                    <ChecklistItemsInput
                        items={task?.checklist || []}
                        disabled={shouldShowSkeleton}
                        showOverlay={!manualChecklistEdit}
                        onOverlayManualEdit={() => setManualChecklistEdit(true)}
                        documentationUrl="https://docs.anthropic.com/en/docs/claude-code"
                        taskId={task?.id || ''}
                        onUpdateItem={updateChecklistItem}
                        onUpdateItemDebounced={updateChecklistItemDebounced}
                        onAddItem={addChecklistItem}
                        onRemoveItem={removeChecklistItem}
                        onReorderItems={reorderChecklistItems}
                    />
                </div>
            </div>
        </ItemView>
    );
};

export default ViewTask;
