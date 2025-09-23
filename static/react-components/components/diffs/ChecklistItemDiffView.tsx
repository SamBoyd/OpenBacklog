import React from 'react';
import { ChecklistItemDto } from '#types';
import { Button } from '#components/reusable/Button';
import { CheckCheck, X, Plus, Minus, RotateCcw } from 'lucide-react';
import { SingleActionButton } from './reusable/ActionButtons';

/**
 * Component for displaying an added checklist item
 */
interface AddedChecklistItemProps {
    item: ChecklistItemDto;
}



const AddedChecklistItem: React.FC<AddedChecklistItemProps> = ({ item }) => (
    <div className="flex items-center space-x-2 py-1.5 pl-2 bg-[var(--diff-code-insert-background-color)] text-[var(--diff-text-color)]">
        <Plus className="h-4 w-4 flex-shrink-0" />
        <input
            type="checkbox"
            checked={item.is_complete}
            readOnly
            className="h-4 w-4 border-border rounded"
            aria-label={`Added item: ${item.title}`}
        />
        <span>{item.title}</span>
    </div>
);

/**
 * Component for displaying a removed checklist item
 */
interface RemovedChecklistItemProps {
    item: ChecklistItemDto;
}

const RemovedChecklistItem: React.FC<RemovedChecklistItemProps> = ({ item }) => (
    <div className="flex py-1.5 pl-2 items-center space-x-2 bg-[var(--diff-code-delete-background-color)] text-[var(--diff-text-color)]">
        <Minus className="h-4 w-4 flex-shrink-0" />
        <input
            type="checkbox"
            checked={item.is_complete}
            readOnly
            className="h-4 w-4 border-border rounded bg-[var(--diff-code-delete-background-color)] text-[var(--diff-text-color)]"
            aria-label={`Removed item: ${item.title}`}
        />
        <span className="line-through">{item.title}</span>
    </div>
);

/**
 * Component for displaying an unchanged checklist item
 */
interface UnchangedChecklistItemProps {
    item: ChecklistItemDto;
}

const UnchangedChecklistItem: React.FC<UnchangedChecklistItemProps> = ({ item }) => (
    <div className="flex items-center space-x-2 py-1.5 pl-2">
        <div className="h-4 w-4"></div>
        <input
            type="checkbox"
            checked={item.is_complete}
            readOnly
            className="h-4 w-4 text-foreground focus:ring-foreground border-border rounded"
            aria-label={`Unchanged item: ${item.title}`}
        />
        <span className='text-foreground'>{item.title}</span>
    </div>
);

/**
 * Component for displaying a modified checklist item
 */
interface ModifiedChecklistItemProps {
    originalItem: ChecklistItemDto;
    changedItem: ChecklistItemDto;
}

const ModifiedChecklistItem: React.FC<ModifiedChecklistItemProps> = ({ originalItem, changedItem }) => (
    <div className="space-y-1 border-l-2 border-blue-500 pl-3 py-1.5 pl-2">
        {/* Original (as removed) */}
        <div className="flex items-center space-x-2 bg-[var(--diff-code-delete-background-color)] text-[var(--diff-text-color)]">
            <Minus className="h-4 w-4 flex-shrink-0" />
            <input
                type="checkbox"
                checked={originalItem.is_complete}
                readOnly
                className="h-4 w-4 border-border rounded"
                aria-label={`Original state of modified item: ${originalItem.title}`}
            />
            <span className="line-through">{originalItem.title}</span>
        </div>
        {/* Changed (as added) */}
        <div className="flex items-center space-x-2 bg-[var(--diff-code-insert-background-color)] text-[var(--diff-text-color)]">
            <Plus className="h-4 w-4 flex-shrink-0" />
            <input
                type="checkbox"
                checked={changedItem.is_complete}
                readOnly
                className="h-4 w-4 border-border rounded"
                aria-label={`New state of modified item: ${changedItem.title}`}
            />
            <span className='text-[var(--diff-text-color)]'>{changedItem.title}</span>
        </div>
    </div>
);

const ResolvedChecklistItemDiffView = ({ finalItems, onRollback }: { finalItems: ChecklistItemDto[], onRollback: () => void }) => {
    return (
        <div className="relative border border-border pl-3 m-2 rounded-md overflow-visible">
            <div className="absolute right-4 -top-1">
                <Button onClick={onRollback} aria-label="Rollback checklist changes" className='bg-background border-border'>
                    <RotateCcw size={16} />
                </Button>
            </div>
            <div className="p-4">
                {finalItems.length > 0 ? (
                    <ul className="space-y-2">
                        {finalItems.map((item, index) => (
                            <div key={'final-item-' + index} className="flex items-center space-x-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={item.is_complete}
                                    readOnly
                                    className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
                                    aria-label={`Checkbox for ${item.title}`}
                                />
                                <span className={`text-[var(--diff-text-color)] ${item.is_complete ? 'line-through' : ''}`}>
                                    {item.title}
                                </span>
                            </div>
                        ))}
                    </ul>
                ) : (
                    <p className="text-sm text-[var(--diff-text-color)] italic">No checklist items.</p>
                )}
            </div>
        </div>
    );
}

interface ChecklistItemDiffViewProps {
    originalItems: ChecklistItemDto[];
    changedItems: ChecklistItemDto[];
    isResolved: boolean;
    resolvedItems: ChecklistItemDto[] | null;
    onAccept: () => void;
    onReject: () => void;
    onRollback: () => void;
}

// Helper function to find the Longest Common Subsequence (LCS) based on item IDs
function findLCS<T extends { id: string }>(a: T[], b: T[]): T[] {
    const m = a.length;
    const n = b.length;
    const dp: number[][] = Array(m + 1).fill(0).map(() => Array(n + 1).fill(0));

    // Build the DP table
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (a[i - 1].id === b[j - 1].id) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    // Reconstruct the LCS sequence (using items from `a` for consistency)
    const lcs: T[] = [];
    let i = m;
    let j = n;
    while (i > 0 && j > 0) {
        if (a[i - 1].id === b[j - 1].id) {
            lcs.unshift(a[i - 1]); // Add the common item from `a`
            i--;
            j--;
        } else if (dp[i - 1][j] > dp[i][j - 1]) {
            i--;
        } else {
            j--;
        }
    }
    return lcs;
}

/**
 * Component for displaying differences between two versions of a checklist.
 */
const ChecklistItemDiffView: React.FC<ChecklistItemDiffViewProps> = ({
    originalItems,
    changedItems,
    isResolved,
    resolvedItems,
    onAccept,
    onReject,
    onRollback,
}) => {
    // 1. Handle the resolved state first
    if (isResolved) {
        const finalItems = resolvedItems ?? originalItems;
        return (
            <ResolvedChecklistItemDiffView finalItems={finalItems} onRollback={onRollback} />
        );
    }

    // 2. Calculate differences and status map (remains the same)
    const originalItemsMap = new Map(originalItems.map(item => [item.id, item]));
    const changedItemsMap = new Map(changedItems.map(item => [item.id, item]));
    const itemStatusMap = new Map<string, { type: 'unchanged' | 'modified' | 'added' | 'removed', original?: ChecklistItemDto, changed?: ChecklistItemDto }>();

    changedItems.forEach(changedItem => {
        const originalItem = originalItemsMap.get(changedItem.id);
        if (!originalItem) {
            itemStatusMap.set(changedItem.id, { type: 'added', changed: changedItem });
        } else if (
            originalItem.title !== changedItem.title ||
            originalItem.is_complete !== changedItem.is_complete
        ) {
            itemStatusMap.set(changedItem.id, { type: 'modified', original: originalItem, changed: changedItem });
        } else {
            itemStatusMap.set(changedItem.id, { type: 'unchanged', original: originalItem, changed: changedItem });
        }
    });

    originalItems.forEach(originalItem => {
        if (!changedItemsMap.has(originalItem.id)) {
            itemStatusMap.set(originalItem.id, { type: 'removed', original: originalItem });
        }
    });

    const hasChanges = Array.from(itemStatusMap.values()).some(status => status.type !== 'unchanged');

    // New rendering logic using LCS
    const renderDiffItems = () => {
        const lcs = findLCS(originalItems, changedItems);
        const result: React.ReactNode[] = [];
        let originalIndex = 0;
        let changedIndex = 0;
        let lcsIndex = 0;

        while (lcsIndex < lcs.length) {
            const lcsItem = lcs[lcsIndex];

            // Process removals before the current LCS item
            while (originalIndex < originalItems.length && originalItems[originalIndex].id !== lcsItem.id) {
                const removedItem = originalItems[originalIndex];
                // Double-check it was actually removed (should always be true here)
                if (itemStatusMap.get(removedItem.id)?.type === 'removed') {
                    result.push(<RemovedChecklistItem key={`rem-${originalIndex}`} item={removedItem} />);
                }
                originalIndex++;
            }

            // Process additions before the current LCS item
            while (changedIndex < changedItems.length && changedItems[changedIndex].id !== lcsItem.id) {
                const addedItem = changedItems[changedIndex];
                // Double-check it was actually added (should always be true here)
                if (itemStatusMap.get(addedItem.id)?.type === 'added') {
                    result.push(<AddedChecklistItem key={`add-${changedIndex}`} item={addedItem} />);
                }
                changedIndex++;
            }

            // Process the LCS item (must be modified or unchanged)
            const status = itemStatusMap.get(lcsItem.id);
            if (status?.type === 'modified') {
                result.push(
                    <ModifiedChecklistItem
                        key={`mod-${lcsItem.id}`}
                        originalItem={status.original!}
                        changedItem={status.changed!}
                    />
                );
            } else if (status?.type === 'unchanged') {
                result.push(<UnchangedChecklistItem key={`unchanged-${lcsItem.id}`} item={status.changed!} />);
            }

            // Advance all pointers past the processed LCS item
            lcsIndex++;
            originalIndex++;
            changedIndex++;
        }

        // Process remaining removals after the last LCS item
        while (originalIndex < originalItems.length) {
            const removedItem = originalItems[originalIndex];
            if (itemStatusMap.get(removedItem.id)?.type === 'removed') {
                result.push(<RemovedChecklistItem key={`removed-${originalIndex}`} item={removedItem} />);
            }
            originalIndex++;
        }

        // Process remaining additions after the last LCS item
        while (changedIndex < changedItems.length) {
            const addedItem = changedItems[changedIndex];
            if (itemStatusMap.get(addedItem.id)?.type === 'added') {
                result.push(<AddedChecklistItem key={`added-${changedIndex}`} item={addedItem} />);
            }
            changedIndex++;
        }

        return result.length > 0
            ? result
            : <p className="text-muted-foreground italic">No checklist items found or no changes proposed.</p>;
    };

    // 3. Render the diff view for the unresolved state
    return (
        <div className="relative mb-6 border border-border rounded-md bg-background">
            {/* Header and Action Buttons */}
            <div className="absolute -top-5 right-2 w-fit float-right space-x-1 flex flex-row">
                <SingleActionButton
                    actionLabel=""
                    isResolved={isResolved}
                    accepted={false}
                    onReject={onReject}
                    onAccept={onAccept}
                    onRollback={onRollback}
                />
            </div>

            {/* Diff Content Area */}
            <div className="p-4 text-sm">
                {!hasChanges && originalItems.length > 0 ? (
                    <div className="flex flex-col space-y-3">
                        {/* If no changes, show all original items as unchanged */}
                        {originalItems.map(item => (
                            <UnchangedChecklistItem key={`original-${item.title.replace(/ /g, '-')}`} item={item} />
                        ))}
                    </div>
                ) : !hasChanges ? (
                    <p className="text-muted-foreground italic">No changes proposed for checklist items.</p>
                ) : (
                    <div className="flex flex-col">
                        {renderDiffItems()}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChecklistItemDiffView;
