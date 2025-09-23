import React, { useState } from 'react';
import {
    InitiativeDto,
    TaskDto,
    ManagedInitiativeModel,
    ManagedTaskModel,
    ManagedEntityAction
} from '#types';
import { SingleActionButton } from './reusable/ActionButtons';
import { Skeleton } from '../reusable/Skeleton';
import { ResolutionState, UnifiedSuggestion } from '#contexts/SuggestionsToBeResolvedContext';

export type ListItemProps<T extends InitiativeDto | TaskDto, M extends ManagedInitiativeModel | ManagedTaskModel> = {
    entityType: 'initiative' | 'task';
    suggestion: UnifiedSuggestion;
    resolution: ResolutionState;
    accept: () => void;
    reject: () => void;
    rollback: () => void;
};

/**
 * Truncates an array of strings or objects with a 'title' property to a cumulative max length.
 * Returns the items that fit and the remaining char count.
 */
function truncateArrayByChars<T>(arr: T[], getText: (item: T) => string, maxChars: number): T[] {
    let total = 0;
    const result: T[] = [];
    for (const item of arr) {
        const text = getText(item);
        if (total + text.length > maxChars) break;
        result.push(item);
        total += text.length;
    }
    return result;
}

/**
 * Truncates a string to a maximum length, appending '…' if truncated.
 */
const truncateText = (text: string, maxLength: number = 200): string => {
    if (!text) return '';
    return text.length > maxLength ? text.slice(0, maxLength) + '…' : text;
};

export const ListItem = <T extends InitiativeDto | TaskDto, M extends ManagedInitiativeModel | ManagedTaskModel>({
    entityType,
    resolution,

    suggestion,
    accept,
    reject,
    rollback
}: ListItemProps<T, M>) => {

    const {
        path,
        type,
        action,
        originalValue,
        suggestedValue,
        entityIdentifier,
    } = suggestion;

    // Determine title and action label based on type
    let title = entityType === 'initiative' ? 'Untitled Initiative' : 'Untitled Task';
    let actionLabel = '';
    let badgeColorClass = '';
    let content = null;
    let backgroundColor = '';

    // Single expand/collapse state for the whole details section
    const [expanded, setExpanded] = useState(false);

    // Helper to check if any section (desc, tasks, checklist) is over 200 chars
    const hasLongSection = (entity: any): boolean => {
        const desc = 'description' in entity ? (entity.description ?? '') : '';
        if (desc.length > 200) return true;
        if ('tasks' in entity && Array.isArray(entity.tasks)) {
            let total = 0;
            for (const task of entity.tasks) {
                total += (task?.title?.length || 0) + (task?.description?.length || 0);
                if (total > 200) return true;
            }
        }
        if ('checklist' in entity && Array.isArray(entity.checklist)) {
            let total = 0;
            for (const item of entity.checklist) {
                total += (item?.title?.length || 0);
                if (total > 200) return true;
            }
        }
        return false;
    };

    // Helper to render checklist items (cumulative 200 chars)
    const renderChecklist = (checklist: any[] | undefined) => {
        if (!checklist || checklist.length === 0) return null;
        let itemsToShow = checklist;
        if (!expanded) {
            itemsToShow = truncateArrayByChars(checklist, (item) => item.title || '', 200);
        }
        return (
            <ul className="pl-4 list-disc space-y-1">
                {itemsToShow.map((item: any) => (
                    <li key={item.id || item.title} className="text-xs text-muted-foreground">
                        {item.title}
                    </li>
                ))}
                {!expanded && itemsToShow.length < checklist.length && <li className="text-xs text-muted-foreground">…</li>}
            </ul>
        );
    };

    // Helper to render tasks (cumulative 200 chars for all titles+descriptions)
    const renderTasks = (tasks: any[] | undefined) => {
        if (!tasks || tasks.length === 0) return null;
        let itemsToShow = tasks;
        if (!expanded) {
            let total = 0;
            itemsToShow = [];
            for (const task of tasks) {
                const len = (task?.title?.length || 0) + (task?.description?.length || 0);
                if (total + len > 200) break;
                itemsToShow.push(task);
                total += len;
            }
        }
        if (itemsToShow.length === 0) return null;
        return (
            <div className="mt-2">
                <div className="font-semibold text-xs text-foreground mb-1">Tasks:</div>
                <ul className="pl-4 list-decimal space-y-1">
                    {itemsToShow.map((task: any) => (
                        <li key={task.id || task.title} className="text-xs text-muted-foreground">
                            <div>
                                <span className="font-medium">{task.title}</span>
                            </div>
                            {task.description && (
                                <div className="text-xs text-muted-foreground">{task.description}</div>
                            )}
                            {renderChecklist(task.checklist)}
                        </li>
                    ))}
                    {!expanded && itemsToShow.length < tasks.length && <li className="text-xs text-muted-foreground">…</li>}
                </ul>
            </div>
        );
    };

    // Helper to render details for the entity
    const renderDetails = (entity: any) => {
        const desc = entity.description || 'No description';
        const tasks = entity.tasks || undefined;
        const checklist = entity.checklist || undefined;
        const showExpand = hasLongSection(entity);
        let descToShow = desc;
        if (!expanded && desc.length > 200) descToShow = truncateText(desc, 200);
        return (
            <div className="text-sm space-y-2">
                <div>
                    <span className="font-semibold text-xs text-foreground">Description:</span>
                    <p className="text-muted-foreground text-pretty">{descToShow}</p>
                </div>
                {tasks && tasks.length > 0 && renderTasks(tasks)}
                {checklist && checklist.length > 0 && (
                    <div className="mt-2">
                        <div className="font-semibold text-xs text-foreground mb-1">Checklist:</div>
                        {renderChecklist(checklist)}
                    </div>
                )}
                {showExpand && (
                    <button
                        className="mt-2 text-xs text-primary underline hover:no-underline focus:outline-none"
                        onClick={() => setExpanded(e => !e)}
                        type="button"
                    >
                        {expanded ? 'Show less' : 'Show more'}
                    </button>
                )}
            </div>
        );
    };

    // Render details for the appropriate entity type
    switch (action) {
        case ManagedEntityAction.CREATE:
            actionLabel = 'Create';
            badgeColorClass = 'bg-action-create text-action-create-foreground';
            title = (suggestedValue as any).title || title;
            content = (
                <div>
                    {renderDetails(suggestedValue as any)}
                </div>
            );
            backgroundColor = 'var(--diff-code-insert-background-color)';
            break;
        case ManagedEntityAction.UPDATE:
            actionLabel = 'Update';
            badgeColorClass = 'bg-action-update text-action-update-foreground';
            title = (suggestedValue as any).title || (originalValue as any)?.title || title;
            content = (
                <div className="grid grid-cols-1 gap-4">
                    {originalValue ? 
                        renderDetails(suggestedValue as any) 
                        : <span className="text-sm text-muted-foreground">Suggestion details missing</span>}
                </div>
            );
            backgroundColor = 'var(--diff-code-insert-edit-background-color)';
            break;
        case ManagedEntityAction.DELETE:
            actionLabel = 'Delete';
            badgeColorClass = 'bg-action-delete text-action-delete-foreground';
            title = (originalValue as any)?.title || title;
            content = (
                <div>
                    <p className="text-sm text-muted-foreground">This {entityType} will be removed.</p>
                </div>
            );
            backgroundColor = 'var(--diff-code-delete-background-color)';
            break;
    }

    // Determine border color based on resolution
    let resolutionBorderClass = 'border-border';
    if (resolution.isAccepted) {
        resolutionBorderClass = 'border-approve';
    } else if (!resolution.isAccepted) {
        resolutionBorderClass = 'border-reject';
    }

    return (
        <li
            data-testid={`suggestion-card-${path}-${action}`}
            className={`border rounded-lg shadow-sm mb-4 bg-card ${resolutionBorderClass}`}
        >
            <div className="relative flex items-center justify-between border-b rounded-t-lg border-border">
                <div className={
                    `rounded-t-lg px-2 py-2 flex items-center w-full
                    bg-gradient-to-r from-[${backgroundColor}] to-background rounded-t
                    `
                }>
                    <span className={`px-2 py-0.5 rounded-full text-foreground font-medium`}>
                        {actionLabel}:
                    </span>
                    <h3 className="text-sm font-semibold text-foreground truncate">{title}</h3>
                </div>
                <div className="flex space-x-1 flex-shrink-0">
                    <div className="absolute -top-1 right-4 flex space-x-2">
                        <SingleActionButton
                            actionLabel={actionLabel}
                            isResolved={resolution.isResolved}
                            accepted={resolution.isAccepted}
                            onReject={reject}
                            onAccept={accept}
                            onRollback={rollback}
                        />
                    </div>
                </div>
            </div>

            <div className="p-4">
                {content}
            </div>
        </li>
    );
};

export const LoadingListItem = () => (
    <li
        data-testid="loading-list-item"
        className="flex flex-col justify-center gap-y-2 px-4 py-3 border border-border rounded mb-4 bg-card"
    >
        <div className="flex flex-row justify-between items-center">
            <div className="flex flex-row gap-2 items-center">
                <Skeleton type="text" width='w-12' height='h-4' />
                <Skeleton type="text" width='w-32' height='h-4'/>
            </div>
            <div className="flex flex-row gap-1 items-center">
                <Skeleton type="image" width='w-6' height='h-6' />
                <Skeleton type="image" width='w-6' height='h-6' />
            </div>
        </div>
        <Skeleton type="text" width='w-full' height='h-4' />
        <Skeleton type="text" width='w-full' height='h-4' />
    </li>
);
