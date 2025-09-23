import { Button } from '#components/reusable/Button';
import { CheckCheck, RotateCcw, X } from 'lucide-react';
import React from 'react';
import { Diff, Hunk, parseDiff } from 'react-diff-view';

import '#styles/field_diff_styles.css';
import { SingleActionButton } from './reusable/ActionButtons';
/**
 * Renders a diff file with its hunks
 * @param {object} file - The diff file object from parseDiff
 * @returns {React.ReactElement | null} The rendered diff or null if invalid
 */
function renderFile(file: any) {
    if (!file || !file.hunks || file.hunks.length === 0) return null;

    return (
        <Diff
            key={`${file.oldRevision}-${file.newRevision}`}
            viewType="unified"
            diffType={file.type}
            hunks={file.hunks}
            hunkClassName=""
            lineClassName=""
            gutterClassName=""
            codeClassName=""
            gutterType='none'

        >
            {hunks => hunks.map(hunk => (
                <Hunk
                    key={hunk.content}
                    hunk={hunk}
                />
            ))}
        </Diff>
    );
}

interface FieldDiffProps {
    fieldName: 'title' | 'description';
    originalValue: string;
    changedValue: string;
    diff: ReturnType<typeof parseDiff> | null;
    isResolved: boolean;
    resolvedValue: string | null;
    onAccept: () => void;
    onReject: () => void;
    onRollback: () => void;
}

/**
 * Presentational component for displaying a field diff with action buttons
 */
const FieldDiffView: React.FC<FieldDiffProps> = ({
    fieldName,
    originalValue,
    changedValue,
    diff,
    isResolved,
    resolvedValue,
    onAccept,
    onReject,
    onRollback
}) => {
    // If this field is already resolved, show the resolved state
    if (isResolved) {
        const finalValue = resolvedValue || originalValue;
        const acceptedChange = finalValue === changedValue;

        return (
            <div className="relative mb-6 border border-border rounded-md">
                <div className="p-4 text-foreground">
                    <span className="whitespace-pre-wrap">{finalValue}</span>
                </div>

                <div className="absolute z-10 -top-1 right-4 w-fit float-right space-x-2 flex flex-row">
                    <Button
                        onClick={onRollback}
                        dataTestId={`reject-${fieldName}-button`}
                        className='bg-background'
                    >
                        <RotateCcw size={12} />
                    </Button>
                </div>
            </div>
        );
    }

    // Otherwise show the diff with action buttons
    if (!diff || diff.length === 0) return null;

    return (
        <div className="relative mb-6 border border-border rounded-md overflow-visible">
            <div className="p-2">
                {diff.map(file => renderFile(file))}
            </div>
            <div className="absolute -top-5 right-2 w-fit float-right space-x-1 flex flex-row">
                <SingleActionButton
                    actionLabel={''}
                    isResolved={isResolved}
                    accepted={false}
                    onReject={onReject}
                    onAccept={onAccept}
                    onRollback={onRollback}
                />
            </div>
        </div>
    );
};

export default FieldDiffView;
