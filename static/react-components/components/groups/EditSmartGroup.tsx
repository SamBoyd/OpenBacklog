import React, { useState, useEffect, useCallback } from 'react';
import {
    GroupDto,
    FieldDefinitionDto,
    FieldType,
    InitiativeDto,
    InitiativeStatus,
    statusDisplay,
    EntityType
} from '#types';
import { NoBorderButton, PrimaryButton } from '#components/reusable/Button';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { Input } from '#components/reusable/Input';
import ResizingTextInput from '#components/reusable/ResizingTextInput';
import { ArrowLeft } from 'lucide-react';
import { useInitiativeGroups, applySmartGroupCriteria } from '#hooks/useInitiativeGroups';
import SmartGroupQueryCriteria from './SmartGroupQueryCriteria';
import SmartGroupPreview from './SmartGroupPreview';
import { useUserPreferences } from '#hooks/useUserPreferences';

type EditSmartGroupProps = {
    groupToEdit: GroupDto;
    onClose: () => void;
    onGroupUpdated: (group: Partial<GroupDto>) => void;
    onGroupDeleted: () => void;
};

/**
 * A dialog component for creating a new smart group.
 * It allows users to specify a name, description, and query criteria based on field definitions,
 * and previews matching initiatives.
 */
const EditSmartGroup: React.FC<EditSmartGroupProps> = ({
    groupToEdit,
    onClose,
    onGroupUpdated,
    onGroupDeleted,
}) => {
    const { preferences, updateSelectedGroups: updatePrefs } = useUserPreferences();
    const { updateGroup: updateSmartGroup, deleteGroup: deleteSmartGroup } = useInitiativeGroups();

    const [groupName, setGroupName] = useState(groupToEdit.name);
    const [groupDescription, setGroupDescription] = useState(groupToEdit.description || '');
    const [selectedCriteria, setSelectedCriteria] = useState<Record<string, any>>(groupToEdit.query_criteria || {});
    const [debouncedCriteria, setDebouncedCriteria] = useState<Record<string, any>>(groupToEdit.query_criteria || {});
    const [isSaving, setIsSaving] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [activeCriteriaFields, setActiveCriteriaFields] = useState<FieldDefinitionDto[]>([]);
    const [filteredPreviewInitiatives, setFilteredPreviewInitiatives] = useState<InitiativeDto[] | undefined>(undefined);
    const [keywords, setKeywords] = useState(groupToEdit.query_criteria?._keywords || '');
    // TODO: The useFieldDefinitions hook currently requires initiativeId or taskId.
    // It needs to be extended to fetch all field definitions for a workspace and entity type.
    // Example: useFieldDefinitions({ workspaceId: MOCK_WORKSPACE_ID, entityType: EntityType.INITIATIVE });
    // For now, using placeholder data for initiative field definitions.
    const { fieldDefinitions: allFieldDefinitions, loading: fieldDefsLoading, error: fieldDefsError } = useFieldDefinitions({});

    // Debounce selectedCriteria for fetching preview
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedCriteria(selectedCriteria);
        }, 500);

        return () => {
            clearTimeout(handler);
        };
    }, [selectedCriteria]);

    // UseEffect to set active criteria fields
    useEffect(() => {
        const newActiveFieldDefinitions = allFieldDefinitions.filter(fd => groupToEdit.query_criteria?.hasOwnProperty(fd.key) && fd.entity_type === EntityType.INITIATIVE);
        setActiveCriteriaFields(currentActiveFields => {
            const currentIdsString = currentActiveFields.map(f => f.id).sort().join(',');
            const newIdsString = newActiveFieldDefinitions.map(f => f.id).sort().join(',');
            if (currentActiveFields.length === newActiveFieldDefinitions.length && currentIdsString === newIdsString) {
                return currentActiveFields;
            }
            return newActiveFieldDefinitions;
        });
    }, [groupToEdit, allFieldDefinitions]);

    // TODO: useInitiativesContext hook needs to accept a generic filter object (Record<string, any>) for its first argument.
    // The current InitiativeFilters is { id?: string; status?: string[] }.
    // This will require changes in useInitiativesContext and potentially the getAllInitiatives API.
    const { initiativesData: previewInitiatives, shouldShowSkeleton: previewLoading, error: previewError } =
        useInitiativesContext(); // Using 'as any' for now due to filter type mismatch.

    // UseEffect to filter preview initiatives based on keywords and criteria
    useEffect(() => {
        const updateFilteredPreview = (newValues: InitiativeDto[] | undefined) => {
            setFilteredPreviewInitiatives(currentFiltered => {
                // Handle cases where one or both are undefined
                if (currentFiltered === undefined && newValues === undefined) return currentFiltered; // Both undefined, no change
                if (currentFiltered === undefined || newValues === undefined) return newValues; // One is undefined, change to the defined one (or back to undefined)

                // Both are defined arrays, compare by content (IDs)
                const currentIdsString = currentFiltered.map(i => i.id).sort().join(',');
                const newIdsString = newValues.map(i => i.id).sort().join(',');

                if (currentFiltered.length === newValues.length && currentIdsString === newIdsString) {
                    return currentFiltered; // Arrays are effectively the same
                }
                return newValues; // Arrays are different
            });
        };

        if (!previewInitiatives || !allFieldDefinitions) {
            updateFilteredPreview(undefined);
            return;
        }

        const combinedCriteria = { ...debouncedCriteria, _keywords: keywords || undefined };
        const filtered = applySmartGroupCriteria(previewInitiatives, combinedCriteria, allFieldDefinitions);
        updateFilteredPreview(filtered);

    }, [debouncedCriteria, allFieldDefinitions, keywords, previewInitiatives]);

    const handleCriteriaChange = useCallback((fieldKey: string, value: any) => {
        setSelectedCriteria(prev => {
            const updatedCriteria = { ...prev };
            if (value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0)) {
                delete updatedCriteria[fieldKey];
            } else {
                updatedCriteria[fieldKey] = value;
            }
            return updatedCriteria;
        });
    }, []);

    const handleAddFieldToCriteria = useCallback((field: FieldDefinitionDto) => {
        if (!activeCriteriaFields.find(f => f.id === field.id)) {
            setActiveCriteriaFields(prev => [...prev, field]);
        }
    }, [activeCriteriaFields]);

    const handleRemoveFieldFromCriteria = useCallback((fieldKey: string) => {
        setActiveCriteriaFields(prev => prev.filter(f => f.key !== fieldKey));
        // Also remove from selectedCriteria
        setSelectedCriteria(prev => {
            const updatedCriteria = { ...prev };
            delete updatedCriteria[fieldKey];
            return updatedCriteria;
        });
    }, []);

    const handleDelete = async () => {
        if (!window.confirm(`Are you sure you want to delete the group "${groupToEdit.name}"? This action cannot be undone.`)) {
            return;
        }
        setIsDeleting(true);
        await deleteSmartGroup(groupToEdit).catch(error => {
            console.error('Failed to delete smart group:', error);
            setIsDeleting(false);
        });
        updatePrefs(preferences.selectedGroupIds.filter(id => id !== groupToEdit.id));
        onGroupDeleted();
        onClose();
    };

    const handleUpdate = async () => {
        setIsSaving(true);

        const updatedGroup = {
            ...groupToEdit,
            name: groupName,
            description: groupDescription,
            query_criteria: { ...selectedCriteria, _keywords: keywords || undefined },
            updated_at: new Date().toISOString(),
        };
        await updateSmartGroup(updatedGroup).catch(error => {
            console.error('Failed to update smart group:', error);
            alert(`Failed to update smart group: ${error instanceof Error ? error.message : String(error)}`);
            setIsSaving(false);
        });
        onGroupUpdated(updatedGroup);
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



                    <div>
                        <label htmlFor="groupName" className="block text-sm font-medium mb-0.5">Smart Group Name</label>
                        <Input
                            id="groupName"
                            type="text"
                            placeholder="E.g., High Priority Projects"
                            value={groupName}
                            onChange={(e) => setGroupName(e.target.value)}
                            className="w-full p-2 border rounded bg-input text-foreground"
                        />
                    </div>
                    <div>
                        <label htmlFor="groupDescription" className="block text-sm font-medium mb-0.5">Description (Optional)</label>
                        <ResizingTextInput
                            id="groupDescription"
                            placeholder="E.g., All initiatives currently in progress and due this quarter"
                            value={groupDescription}
                            onChange={(value) => setGroupDescription(value)}
                            className="w-full p-2 border rounded bg-input text-foreground h-20"
                        />
                    </div>
                    <div>
                        <label htmlFor="keywords" className="block text-sm font-medium mb-0.5">Keywords (Optional)</label>
                        <Input
                            id="keywords"
                            type="text"
                            placeholder="E.g., search term1 term2"
                            value={keywords}
                            onChange={(e) => setKeywords(e.target.value)}
                            className="w-full p-2 border rounded bg-input text-foreground"
                        />
                    </div>
                </div>

                {/* query criteria section */}
                <SmartGroupQueryCriteria
                    allFieldDefinitions={allFieldDefinitions.filter(fd => fd.entity_type === EntityType.INITIATIVE)} // All the options for selection
                    activeCriteriaFields={activeCriteriaFields} // The FieldDefinitions that are currently selected
                    selectedCriteria={selectedCriteria} // The values of the selected criteria
                    onAddField={handleAddFieldToCriteria}
                    onRemoveField={handleRemoveFieldFromCriteria}
                    onCriteriaChange={handleCriteriaChange}
                    fieldDefsLoading={fieldDefsLoading}
                    fieldDefsError={fieldDefsError}
                    entityTypeForCriteria="Initiative"
                />

                <SmartGroupPreview
                    filteredPreviewInitiatives={filteredPreviewInitiatives}
                    previewLoading={previewLoading}
                    previewError={previewError}
                    debouncedCriteria={debouncedCriteria}
                    keywords={keywords}
                    previewInitiatives={previewInitiatives === null ? undefined : previewInitiatives}
                />

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

export default EditSmartGroup;

