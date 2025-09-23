import React, { useEffect, useState } from 'react';

import { FileData } from 'react-diff-view';
import FieldDiffView from './FieldDiffView';
import { GrDocumentText } from 'react-icons/gr';

interface DescriptionDiffViewProps {
    originalValue: string | null;
    changedValue: string | null;
    diff: FileData[] | null;
    isResolved: boolean,
    resolvedValue: string | null,
    onAccept: () => void,
    onReject: () => void,
    onRollback: () => void,
}

const DescriptionDiffView = ({
    originalValue,
    changedValue,
    diff,
    isResolved = false,
    resolvedValue = null,
    onAccept,
    onReject,
    onRollback,
}: DescriptionDiffViewProps) => {
    const [resolvedValueState, setResolvedValueState] = useState<string | null>(resolvedValue);
    const [isResolvedState, setIsResolvedState] = useState(isResolved);

    useEffect(() => {
        setIsResolvedState(isResolved);
    }, [isResolved]);

    useEffect(() => {
        setResolvedValueState(resolvedValue);
    }, [resolvedValue]);

    const handleAccept = () => {
        setIsResolvedState(true);
        setResolvedValueState(changedValue);
        onAccept();
    }

    const handleReject = () => {
        setIsResolvedState(true);
        setResolvedValueState(originalValue);
        onReject();
    }

    const handleRollback = () => {
        setIsResolvedState(false);
        setResolvedValueState(null);
        onRollback();
    }

    return (
        <div className="text-foreground flex flex-col gap-4">
            <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light">
                <GrDocumentText />
                <span className="ml-2.5">Description</span>
            </div>

            <FieldDiffView
                fieldName="description"
                originalValue={originalValue || ''}
                changedValue={changedValue || ''}
                isResolved={isResolvedState}
                resolvedValue={resolvedValueState}
                onAccept={handleAccept}
                onReject={handleReject}
                onRollback={handleRollback}
                diff={diff}
            />
        </div>
    )
}

export default DescriptionDiffView;
