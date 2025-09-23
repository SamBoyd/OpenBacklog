import EntityDescriptionEditor from '#components/EntityDescriptionEditor';
import { Button } from '#components/reusable/Button';
import { DeleteInitiativeModel, InitiativeDto } from '#types';
import { CheckCheck, RotateCcw, X } from 'lucide-react';
import React from 'react';
import { GrDocumentText } from 'react-icons/gr';
import { SingleActionButton } from './reusable/ActionButtons';


// Add a new component for displaying deletion suggestions
export interface DeleteInitiativeDiffViewProps {
    initiativeData: InitiativeDto;
    onAccept: () => void;
    onReject: () => void;
    onRollback: () => void;
    isResolved: boolean;
    accepted: boolean | null;
}

export const DeleteInitiativeDiffView: React.FC<DeleteInitiativeDiffViewProps> = ({
    initiativeData,
    onAccept,
    onReject,
    onRollback,
    isResolved,
    accepted,
}) => {
    return (
        <div className="mt-4 p-4 border border-border rounded bg-diffred/50">
            <div className="relative flex justify-between items-center ">
                <h3 className='text-foreground'>Delete: <span className="font-semibold line-through">{initiativeData.title}</span></h3>
                <div className="absolute -top-5 right-2 w-fit float-right space-x-1 flex flex-row">
                    <SingleActionButton
                        actionLabel="Deletion"
                        isResolved={isResolved}
                        accepted={false}
                        onReject={onReject}
                        onAccept={onAccept}
                        onRollback={onRollback}
                    />
                </div>
            </div>
            <div className="mt-2">
                <div className={`mt-2 text-foreground`}>
                    {initiativeData.description && (
                        <EntityDescriptionEditor
                            description={initiativeData.description || ''}
                            onChange={() => { }} // Read-only
                            testId={`create-initiative-desc-${initiativeData.title}`}
                            disabled={true}
                            className="line-through"
                        />
                    )}
                </div>
            </div>
        </div>
    );
};
