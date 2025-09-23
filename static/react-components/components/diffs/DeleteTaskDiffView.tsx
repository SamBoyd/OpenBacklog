import EntityDescriptionEditor from '#components/EntityDescriptionEditor';
import { TaskDto } from '#types';
import React from 'react';
import { SingleActionButton } from './reusable/ActionButtons';


// Add a new component for displaying deletion suggestions
export interface DeleteTaskDiffViewProps {
    taskData: TaskDto;
    onAccept: () => void;
    onReject: () => void;
    onRollback: () => void;
    isResolved: boolean;
    accepted: boolean | null;
}

export const DeleteTaskDiffView: React.FC<DeleteTaskDiffViewProps> = ({
    taskData,
    onAccept,
    onReject,
    onRollback,
    isResolved,
    accepted,
}) => {
    return (
        <div className="mt-4 p-4 border border-border rounded bg-diffred/50">
            <div className="flex justify-between items-center">
                <h3 className='text-foreground'>Delete: <span className="font-semibold line-through">{taskData.title}</span></h3>
                <SingleActionButton
                    actionLabel="Deletion"
                    isResolved={isResolved}
                    accepted={accepted ?? false}
                    onReject={onReject}
                    onAccept={onAccept}
                    onRollback={onRollback}
                />
            </div>

            <div className="mt-2">
                <div className={`mt-2 text-foreground`}>
                    {taskData.description && (
                        <EntityDescriptionEditor
                            description={taskData.description || ''}
                            onChange={() => { }} // Read-only
                            testId={`create-task-desc-${taskData.title}`}
                            disabled={true}
                            className="line-through"
                        />
                    )}
                </div>
            </div>
        </div>
    );
};
