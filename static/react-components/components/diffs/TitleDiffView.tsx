import React, { useState, useEffect } from 'react';

import { FileData } from 'react-diff-view';
import FieldDiffView from './FieldDiffView';

interface TitleDiffViewProps {
    originalValue: string | null;
    changedValue: string | null;
    diff: FileData[] | null;
    isResolved: boolean;
    resolvedValue: string | null;
    onAccept: () => void;
    onReject: () => void;
    onRollback: () => void;
}

const TitleDiffView = ({
    originalValue,
    changedValue,
    diff,
    isResolved = false,
    resolvedValue = null,
    onAccept,
    onReject,
    onRollback,
}: TitleDiffViewProps) => {
    const [resolvedValueState, setResolvedValueState] = useState<string | null>(resolvedValue);
    const [isResolvedState, setIsResolvedState] = useState(isResolved);

    // Update local state when props change
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
        <FieldDiffView
            fieldName="title"
            originalValue={originalValue || ''}
            changedValue={changedValue || ''}
            isResolved={isResolvedState}
            resolvedValue={resolvedValueState}
            onAccept={handleAccept}
            onReject={handleReject}
            onRollback={handleRollback}
            diff={diff}
        />
    )
}

export default TitleDiffView;
