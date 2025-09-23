import React from 'react';
import { ManagedTaskModel, ChecklistItemDto, CreateTaskModel } from '#types';
import ResizingTextInput from '#components/reusable/ResizingTextInput';
import EntityDescriptionEditor from '#components/EntityDescriptionEditor';
import ChecklistItemsInput from '#components/reusable/ChecklistItemsInput';
import { Button } from '#components/reusable/Button';
import { CheckCheck, RotateCcw, X } from 'lucide-react';
import { GrList } from 'react-icons/gr';
import { SingleActionButton } from './reusable/ActionButtons';

interface CreateTaskDiffViewProps {
    /** The proposed data for the new task. */
    taskData: CreateTaskModel;
    /** Callback function when the user accepts the creation of this task. */
    onAccept: () => void;
    /** Callback function when the user rejects the creation of this task. */
    onReject: () => void;
    /** Indicates whether the decision for this task has been made. */
    isResolved: boolean;
    /** Indicates if this specific task creation was accepted (true) or rejected (false), only relevant if isResolved is true. */
    accepted?: boolean;
    onRollback: () => void;
}

/**
 * Displays the details of a proposed new task (from AI suggestions)
 * and allows the user to accept or reject its creation.
 * @param {CreateTaskDiffViewProps} props - The component props.
 * @returns {React.ReactElement} The CreateTaskDiffView component.
 */
const CreateTaskDiffView: React.FC<CreateTaskDiffViewProps> = ({
    taskData,
    onAccept,
    onReject,
    isResolved,
    accepted,
    onRollback
}) => {
    const [checklistItems, setChecklistItems] = React.useState<Partial<ChecklistItemDto>[]>(taskData.checklist || []);

    // Helper to display checklist items (can be customized)
    const renderChecklist = () => {
        if (!taskData.checklist || taskData.checklist.length === 0) {
            return <p className="text-[var(--diff-text-color)] text-sm italic">No checklist items proposed.</p>;
        }
        
        return <ChecklistItemsInput
            items={checklistItems}
            disabled={true}
            taskId={''}
            onUpdateItem={function (taskId: string, itemId: string, updates: Partial<ChecklistItemDto>): Promise<ChecklistItemDto> {
                throw new Error('Function not implemented.');
            }}
            onUpdateItemDebounced={function (taskId: string, itemId: string, updates: Partial<ChecklistItemDto>, debounceMs?: number): Promise<ChecklistItemDto> {
                throw new Error('Function not implemented.');
            }}
            onAddItem={function (taskId: string, item: Omit<ChecklistItemDto, 'id' | 'task_id'>): Promise<ChecklistItemDto> {
                throw new Error('Function not implemented.');
            }}
            onRemoveItem={function (taskId: string, itemId: string): Promise<void> {
                throw new Error('Function not implemented.');
            }}
            onReorderItems={function (taskId: string, items: Array<Partial<ChecklistItemDto>>): Promise<Partial<ChecklistItemDto>[]> {
                throw new Error('Function not implemented.');
            }}
        />;
    };

    return (
        <div className={`relative mx-auto rounded w-full`}>
            {/* --- Content --- */}
            <div
                className={`mt-4 p-4 border border-border rounded bg-background text-[var(--diff-text-color)]`}
                data-testid="content"
            >

                {/* Display proposed title */}
                <div className="flex items-center gap-2 w-full justify-between text-foreground ">
                    <h3 className='text-foreground'>Create: <span className="font-semibold">{taskData.title}</span></h3>
                    <div className="absolute -top-5 right-2 w-fit float-right space-x-1 flex flex-row">
                        <SingleActionButton
                            actionLabel="Task"
                            isResolved={isResolved}
                            accepted={accepted || false}
                            onReject={onReject}
                            onAccept={onAccept}
                            onRollback={onRollback}
                        />
                    </div>
                </div>

                {/* Display proposed description */}
                <EntityDescriptionEditor
                    description={taskData.description || ''}
                    onChange={() => { }} // Read-only
                    testId={`create-task-desc-${taskData.title}`}
                    disabled={true}
                />

                {/* Display proposed checklist */}
                <div className="mt-2 mb-8" data-testid="description-section">
                    <div className="flex items-baseline w-fit text-foreground h-8">
                        <GrList />
                        <span className="ml-2">Checklist</span>
                    </div>
                    {renderChecklist()}
                </div>
            </div>
        </div >
    );
};

export default CreateTaskDiffView;