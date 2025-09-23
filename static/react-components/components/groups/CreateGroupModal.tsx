import React, { useState } from 'react';
import { GroupDto, GroupType, InitiativeDto } from '#types';
import { Button, PrimaryButton } from '#components/reusable/Button';
import { Toggle } from '#components/reusable/Input';
import { ArrowLeft, X } from 'lucide-react';
import CreateNewExplicitGroup from './CreateNewExplicitGroup';
import CreateNewSmartGroup from './CreateNewSmartGroup';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';

type CreateGroupModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onGroupCreated: (group: GroupDto) => void;
};

/**
 * A modal component for creating new groups (either explicit or smart).
 * It handles the display of the modal and the selection between group creation types.
 */
const CreateGroupModal: React.FC<CreateGroupModalProps> = ({
    isOpen,
    onClose,
    onGroupCreated,
}) => {
    const { createNewExplicitGroup, createNewSmartGroup, error: createGroupError } = useInitiativeGroups();
    const [createMode, setCreateMode] = useState<'explicit' | 'smart'>('explicit');
    const [newGroup, setNewGroup] = useState<Partial<GroupDto>>({});
    const [isSaving, setIsSaving] = useState(false);

    if (!isOpen) {
        return null;
    }

    const handleCreateExplicitGroup = async () => {
        if (!newGroup || !newGroup.name) return;

        setIsSaving(true);
        await createNewExplicitGroup(
            {
                name: newGroup.name,
                description: newGroup.description || null,
            },
            newGroup.initiatives as InitiativeDto[] || []
        ).then((group) => {
            setNewGroup({
                name: '',
                description: '',
                initiatives: [],
            });
            onClose();
            onGroupCreated(group);
        }).catch((error) => {
            console.error('Failed to create explicit group:', error);
        }).finally(() => {
            setIsSaving(false);
        });
    };

    const handleCreateSmartGroup = async () => {
        if (!newGroup || !newGroup.name) return;

        setIsSaving(true);

        const groupPayload: Partial<GroupDto> = {
            name: newGroup.name,
            description: newGroup.description || null,
            group_type: GroupType.SMART,
            query_criteria: newGroup.query_criteria,
        };
        await createNewSmartGroup(groupPayload as GroupDto).then((group) => {
            setNewGroup({
                name: '',
                description: '',
                query_criteria: {},
            });
            onClose();
            onGroupCreated(group);
        }).catch((error) => {
            console.error('Failed to create smart group:', error);
        }).finally(() => {
            setIsSaving(false);
        });
    };


    return (
        <>
            <div
                className="fixed inset-0 z-20"
                role="dialog"
                aria-modal="true"
                onClick={onClose}
            >
            </div>

            {/* Catches clicks on the modal */}
            <div className="absolute w-[470px] right-4 top-0 p-6 z-30  bg-card rounded-lg shadow-xl" onClick={(e) => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4 p-1 border-b border-border">
                    <button
                        onClick={onClose}
                        className="p-1 text-muted-foreground hover:text-foreground"
                        aria-label="Close"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <h2 className="text-muted-foreground">New group</h2>


                    <PrimaryButton 
                        onClick={createMode === 'explicit' ? handleCreateExplicitGroup : handleCreateSmartGroup} 
                        className="w-auto px-3 py-1 text-sm"
                        disabled={isSaving}
                    >
                        {isSaving ? 'Creating...' : 'Create'}
                    </PrimaryButton>
                </div>

                {/* Toggle for choosing group type */}
                <div className="flex items-center justify-center space-x-4 mb-6">
                    <span
                        className={`cursor-pointer font-medium ${createMode === 'explicit' ? 'text-primary' : 'text-muted-foreground'}`}
                        onClick={() => setCreateMode('explicit')}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => e.key === 'Enter' && setCreateMode('explicit')}
                    >
                        Explicit Group
                    </span>
                    <Toggle
                        isEnabled={createMode === 'smart'}
                        onChange={(isSmart: boolean) => setCreateMode(isSmart ? 'smart' : 'explicit')}
                        size="md"
                        aria-label={createMode === 'smart' ? "Switch to create explicit group" : "Switch to create smart group"}
                    />
                    <span
                        className={`cursor-pointer font-medium ${createMode === 'smart' ? 'text-primary' : 'text-muted-foreground'}`}
                        onClick={() => setCreateMode('smart')}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => e.key === 'Enter' && setCreateMode('smart')}
                    >
                        Smart Group
                    </span>
                </div>

                {createMode === 'explicit' && (
                    <CreateNewExplicitGroup
                        onClose={onClose} // Pass onClose to allow child to close modal on success/cancel
                        onGroupChanged={setNewGroup}
                    />
                )}
                {createMode === 'smart' && (
                    <CreateNewSmartGroup
                        onClose={onClose} // Pass onClose to allow child to close modal on success/cancel
                        onGroupChanged={setNewGroup}
                    />
                )}

                {createGroupError && (
                    <div className="text-red-500 text-sm">
                        {createGroupError}
                    </div>
                )}
            </div>
        </>
    );
};

export default CreateGroupModal; 