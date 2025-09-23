import { Button } from '#components/reusable/Button';
import { CheckCheck, RotateCcw, Save, X } from 'lucide-react';
import React from 'react';

interface ResolveAllButtonsProps {
    loading: boolean;
    hasAnyResolution: boolean;
    allSuggestionsResolved: boolean;
    acceptAllSuggestions: () => void;
    rejectAllSuggestions: () => void;
    rollbackAllSuggestions: () => void;
    onSaveChanges: () => void;
}

export const ResolveAllButtons = ({
    loading,
    hasAnyResolution,
    allSuggestionsResolved,
    acceptAllSuggestions,
    rejectAllSuggestions,
    rollbackAllSuggestions,
    onSaveChanges
}: ResolveAllButtonsProps) => {
    return (
        <div className="w-fit float-right space-x-1 flex flex-row">

            {!allSuggestionsResolved && (
                <>
                    <Button
                        onClick={rejectAllSuggestions}
                        className='text-xs bg-background'
                    >
                        Reject All
                    </Button>
                    <Button
                        onClick={acceptAllSuggestions}
                        className='text-xs bg-background'
                    >
                        Accept All
                    </Button>
                </>
            )}
            
            {allSuggestionsResolved && (
                <>
                    <Button
                        onClick={rollbackAllSuggestions}
                        disabled={loading}
                        className="text-xs px-2 py-1 bg-background"
                    >
                        <RotateCcw size={14} className="mr-1" /> Rollback All
                    </Button>
                    <Button
                        onClick={onSaveChanges}
                        disabled={loading}
                        className="text-xs px-2 py-1 bg-background"
                    >
                        <Save size={14} className="mr-1" /> Save Changes
                    </Button>
                </>
            )}
        </div>
    )
}


interface SingleActionButtonProps {
    actionLabel: string;
    isResolved: boolean;
    accepted: boolean;
    onReject: () => void;
    onAccept: () => void;
    onRollback: () => void;
}
export const SingleActionButton = ({
    actionLabel,
    isResolved,
    accepted,
    onReject,
    onAccept,
    onRollback,
}: SingleActionButtonProps) => {
    return (
        <div className="flex space-x-2">
            {!isResolved ? (
                <>
                    <Button
                        onClick={onReject}
                        data-testid="reject-delete-task-btn"
                    >
                        <X size={12} />
                    </Button>

                    <Button
                        onClick={onAccept}
                        data-testid="accept-delete-task-btn"
                    >
                        <CheckCheck size={12} />

                    </Button>
                </>
            ) : (
                <div className="flex items-center gap-2 w-fit">
                    <span className={`text-sm font-normal px-2 rounded ${accepted ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                       {actionLabel} {accepted ? 'Accepted' : 'Rejected'}
                    </span>
                    <Button
                        onClick={onRollback}
                    >
                        <RotateCcw size={12} />
                    </Button>
                </div>
            )}
        </div>
    )
}