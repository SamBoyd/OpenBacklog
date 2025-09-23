import { TaskDto } from "#types";
import { Button } from "@headlessui/react";
import { RotateCcw, Plus, Minus } from "lucide-react";
import { GrDocumentText } from "react-icons/gr";
import { SingleActionButton } from './reusable/ActionButtons';

/**
 * Wrapper component for Task diff list
 */
export interface TaskDiffViewProps {
    isResolved: boolean;
    rejectAll: () => void;
    acceptAll: () => void;
    rollbackAll: () => void;
    children: React.ReactNode;
}
export const TaskDiffView: React.FC<TaskDiffViewProps> = ({ isResolved, rejectAll, acceptAll, rollbackAll, children }) => {
    return (
        <div className='flex flex-col gap-2 text-foreground'>
            <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light">
                <GrDocumentText />
                <span className="ml-2.5">Tasks</span>
            </div>

            <div className="relative mb-6 border border-border rounded-md bg-background">
                {/* Header and Action Buttons */}
                <div className="absolute -top-5 right-2 w-fit float-right space-x-1 flex flex-row">
                    <SingleActionButton
                        actionLabel="Tasks"
                        isResolved={isResolved}
                        accepted={false}
                        onReject={rejectAll}
                        onAccept={acceptAll}
                        onRollback={rollbackAll}
                    />
                </div>

                {/* Diff Content Area */}
                <div className="p-4 text-sm">
                    {children}
                </div>
            </div>
        </div>
    );
}


/**
 * Component for displaying resolved tasks
 */
export interface ResolvedTasksProps {
    finalTasks: Partial<TaskDto>[];
    onRollback: () => void;
}
export const ResolvedTasks: React.FC<ResolvedTasksProps> = ({ finalTasks, onRollback }) => {
    return (
        <div className='flex flex-col gap-2 text-foreground'>
            <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light">
                <GrDocumentText />
                <span className="ml-2.5">Tasks</span>
            </div>
            <div className="relative pl-3 m-2 rounded-md overflow-visible">
                <div className="absolute right-4 -top-1">
                    <Button onClick={onRollback} aria-label="Rollback task changes" className='bg-background border-border'>
                        <RotateCcw size={12} />
                    </Button>
                </div>
                <div className="p-4">
                    {finalTasks.length > 0 ? (
                        <ul className="space-y-2">
                            {finalTasks.map(task => (
                                <li key={task.id || Math.random()} className="p-2 border-b border-border last:border-b-0">
                                    <span className="">{task.title || 'Untitled Task'}</span>
                                    {task.description && <p className="text-sm text-muted-foreground mt-1">{task.description}</p>}
                                    {/* Display other relevant task details */}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-sm text-foreground italic">No final tasks.</p>
                    )}
                </div>
            </div>
        </div>
    );
}


/**
 * Component for displaying an unresolved task create
 */
export interface UnresolvedTaskCreateProps {
    task: Partial<TaskDto>;
}
export const UnresolvedTaskCreate: React.FC<UnresolvedTaskCreateProps> = ({ task }) => (
    <div className="flex items-start space-x-2 bg-[var(--diff-code-insert-background-color)] text-[var(--diff-text-color)] p-2 rounded">
        <Plus className="h-4 w-4 flex-shrink-0 mt-1" />
        <div>
            <span className="font-semibold">{task.title || 'Untitled Task'}</span>
            {/* Add other relevant task details if needed */}
            {task.description && <p className="text-sm opacity-80">{task.description}</p>}
        </div>
    </div>
);


/**
 * Component for displaying an unresolved task delete
 */
export interface UnresolvedTaskDeleteProps {
    task: Partial<TaskDto>;
}
export const UnresolvedTaskDelete: React.FC<UnresolvedTaskDeleteProps> = ({ task }) => (
    <div className="flex items-start space-x-2 bg-[var(--diff-code-delete-background-color)] text-[var(--diff-text-color)] p-2 rounded opacity-80">
        <Minus className="h-4 w-4 flex-shrink-0 mt-1" />
        <div>
            <span className="font-semibold line-through">{task.title || 'Untitled Task'}</span>
            {/* Add other relevant task details if needed */}
            {task.description && <p className="text-sm opacity-80 line-through">{task.description}</p>}
        </div>
    </div>
);


/**
 * Component for displaying an unresolved task update
 */
export interface UnresolvedTaskUpdateProps {
    originalTask: Partial<TaskDto>;
    changedTask: Partial<TaskDto>;
}
export const UnresolvedTaskUpdate: React.FC<UnresolvedTaskUpdateProps> = ({ originalTask, changedTask }) => (
    <div className="space-y-1 border-l-2 border-blue-500 pl-3 my-2">
        {/* Original (as removed) */}
        <div className="flex items-start space-x-2 bg-[var(--diff-code-delete-background-color)] text-[var(--diff-text-color)] p-1 rounded opacity-80">
            <Minus className="h-4 w-4 flex-shrink-0 mt-1" />
            <div>
                <span className="font-semibold line-through">{originalTask.title || 'Untitled Task'}</span>
                {originalTask.description && <p className="text-sm opacity-80 line-through">{originalTask.description}</p>}
                {/* Display other original fields */}
            </div>
        </div>
        {/* Changed (as added) */}
        <div className="flex items-start space-x-2 bg-[var(--diff-code-insert-background-color)] text-[var(--diff-text-color)] p-1 rounded">
            <Plus className="h-4 w-4 flex-shrink-0 mt-1" />
            <div>
                <span className="font-semibold">{changedTask.title || 'Untitled Task'}</span>
                {changedTask.description && <p className="text-sm opacity-80">{changedTask.description}</p>}
                {/* Display other changed fields */}
            </div>
        </div>
    </div>
);


/**
 * Component for displaying an unchanged task
 */
export interface UnchangedTaskProps {
    task: Partial<TaskDto>;
}
export const UnchangedTask: React.FC<UnchangedTaskProps> = ({ task }) => (
    <div className="flex items-start space-x-2 p-2 rounded text-foreground">
        <div className="h-4 w-4 flex-shrink-0 mt-1"></div> {/* Placeholder for icon */}
        <div>
            <span className="font-semibold">{task.title || 'Untitled Task'}</span>
            {/* Add other relevant task details if needed */}
            {task.description && <p className="text-sm text-foreground">{task.description}</p>}
        </div>
    </div>
);
