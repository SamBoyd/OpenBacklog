import React from 'react';
import { CreateInitiativeModel, ManagedInitiativeModel } from '#types';
import ResizingTextInput from '#components/reusable/ResizingTextInput';
import EntityDescriptionEditor from '#components/EntityDescriptionEditor';
import { Button } from '#components/reusable/Button';
import { CheckCheck, RotateCcw, X } from 'lucide-react';
import { SingleActionButton } from './reusable/ActionButtons';

interface CreateInitiativeDiffViewProps {
    /** The proposed data for the new initiative. */
    initiativeData: CreateInitiativeModel;
    /** Callback function when the user accepts the creation of this initiative. */
    onAccept: () => void;
    /** Callback function when the user rejects the creation of this initiative. */
    onReject: () => void;
    /** Indicates whether the decision for this initiative has been made. */
    isResolved: boolean;
    /** Indicates if this specific initiative creation was accepted (true) or rejected (false), only relevant if isResolved is true. */
    accepted?: boolean;
    onRollback: () => void;
}

/**
 * Displays the details of a proposed new initiative (from AI suggestions)
 * and allows the user to accept or reject its creation.
 * @param {CreateInitiativeDiffViewProps} props - The component props.
 * @returns {React.ReactElement} The CreateInitiativeDiffView component.
 */
const CreateInitiativeDiffView: React.FC<CreateInitiativeDiffViewProps> = ({
    initiativeData,
    onAccept,
    onReject,
    isResolved,
    accepted,
    onRollback
}) => {
    return (
        <div className={`mt-4 p-4 border border-border rounded bg-background`}>
            {/* --- Content --- */}
            <div className="relative flex justify-between items-center">
                <h3>Create: <span className="font-semibold">{initiativeData.title}</span></h3>
                <div className="absolute -top-5 right-2 w-fit float-right space-x-1 flex flex-row">
                        <SingleActionButton
                            actionLabel="Initiative"
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
                description={initiativeData.description || ''}
                onChange={() => { }} // Read-only
                testId={`create-initiative-desc-${initiativeData.title}`}
                disabled={true}
            />
        </div>
    );
};

export default CreateInitiativeDiffView;