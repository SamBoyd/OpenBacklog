import React, { useState, useEffect, useRef } from 'react';
import { ContextType, EntityType, GroupDto, InitiativeDto } from '#types';
import { PrimaryButton } from '#components/reusable/Button';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { Input } from '#components/reusable/Input';
import ResizingTextInput from '#components/reusable/ResizingTextInput';
import { ArrowLeft } from 'lucide-react';
import SelectInitiativesToAdd from './SelectInitiativesToAdd';
import { useUserPreferences } from '#hooks/useUserPreferences';

type EditExplicitGroupProps = {
    groupToEdit: GroupDto;
    onClose: () => void;
    onGroupUpdated: () => void;
    onGroupDeleted: () => void;
};

/**
 * A dialog component for editing an existing explicit group.
 * It allows users to update its name, description, selected initiatives, and to delete the group.
 */
const EditExplicitGroup: React.FC<EditExplicitGroupProps> = ({
    groupToEdit,
    onClose,
    onGroupUpdated,
    onGroupDeleted,
}) => {
    const { preferences, updateSelectedGroups: updatePrefs } = useUserPreferences();

    const [groupName, setGroupName] = useState('');
    const [groupDescription, setGroupDescription] = useState('');
    const [selectedInitiatives, setSelectedInitiatives] = useState<InitiativeDto[]>([]);
    const [isSaving, setIsSaving] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const { 
        deleteGroup: deleteExplicitGroup, 
        addInitiativeToExplicitGroup,
        removeInitiativeFromExplicitGroup,
    } = useInitiativeGroups();
    // Ordering is now handled automatically by the API layer

    const previousInitiatives = useRef<InitiativeDto[]>([]);

    useEffect(() => {
        if (groupToEdit) {
            setGroupName(groupToEdit.name);
            setGroupDescription(groupToEdit.description || '');
            setSelectedInitiatives(groupToEdit.initiatives as InitiativeDto[]);
            previousInitiatives.current = groupToEdit.initiatives as InitiativeDto[];
        }
    }, [groupToEdit]);

    const handleUpdate = async () => {
        if (!groupToEdit) {
            console.error('Group to edit is not set.');
            return;
        }

        if (!groupName.trim()) {
            console.error('Group name is required.');
            return;
        }

        setIsSaving(true);
        
        try {
            const updatedGroup = {
                ...groupToEdit,
                name: groupName,
                description: groupDescription,
                updated_at: new Date().toISOString(),
            };
            
            const addedInitiatives = selectedInitiatives.filter(initiative => !previousInitiatives.current.includes(initiative));
            for (const initiative of addedInitiatives) {
                await addInitiativeToExplicitGroup(initiative, updatedGroup);
            }
            const removedInitiatives = previousInitiatives.current.filter(initiative => !selectedInitiatives.includes(initiative));
            for (const initiative of removedInitiatives) {
                await removeInitiativeFromExplicitGroup(initiative, updatedGroup);
            }
            
            // Update the ref to track current initiatives for future diff calculations if needed
            previousInitiatives.current = selectedInitiatives;
            
            onGroupUpdated();
            onClose();
        } catch (error) {
            console.error('Failed to update explicit group:', error);
            setIsSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!window.confirm(`Are you sure you want to delete the group "${groupToEdit.name}"? This action cannot be undone.`)) {
            return;
        }
        setIsDeleting(true);
        try {
            await deleteExplicitGroup(groupToEdit);
            updatePrefs(preferences.selectedGroupIds.filter(id => id !== groupToEdit.id));
            onGroupDeleted();
            onClose();
        } catch (error) {
            console.error('Failed to delete explicit group:', error);
            setIsDeleting(false);
        }
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

            <div className="absolute right-0 top-0 px-2 py-1 z-30 bg-card rounded-lg shadow-xl w-md " onClick={(e) => e.stopPropagation()}>
                <div className="space-y-4">
                    <div className="flex justify-between items-center mb-4 p-1 border-b border-border">
                        <button
                            onClick={onClose}
                            className="p-1 text-muted-foreground hover:text-foreground"
                            aria-label="Close"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <h2 className="text-muted-foreground">{groupToEdit.name}</h2>


                        <PrimaryButton
                            onClick={handleUpdate}
                            className="w-auto px-3 py-1 text-sm"
                            disabled={isSaving}
                        >
                            {isSaving ? 'Saving...' : 'Save'}
                        </PrimaryButton>
                    </div>

                    <Input
                        type="text"
                        placeholder="Explicit Group Name"
                        value={groupName}
                        onChange={(e) => setGroupName(e.target.value)}
                        className="w-full p-2 border rounded bg-input text-foreground"
                    />

                    <ResizingTextInput
                        placeholder="Explicit Group Description (Optional)"
                        value={groupDescription}
                        onChange={(e) => setGroupDescription(e)}
                        className="w-full p-2 border rounded bg-input text-foreground"
                    />

                    <SelectInitiativesToAdd
                        selectedInitiatives={selectedInitiatives}
                        onInitiativesChange={setSelectedInitiatives}
                        idPrefix={`edit-group-${groupToEdit.id}`}
                    />
                </div>

                <div className="flex justify-end items-center py-2">
                    <div
                        onClick={!isDeleting ? handleDelete : undefined}
                        className={`text-sm text-destructive px-2 py-1 rounded ${!isDeleting ? 'hover:bg-destructive hover:text-destructive-foreground cursor-pointer' : 'opacity-50 cursor-not-allowed'} transition-colors duration-200`}
                    >
                        {isDeleting ? 'Deleting...' : 'Delete Group'}
                    </div>
                </div>
            </div>
        </>
    );
};

export default EditExplicitGroup; 
