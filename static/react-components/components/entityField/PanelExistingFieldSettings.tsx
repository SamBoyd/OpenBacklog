import React, { useState, useEffect } from "react";
import { FieldDefinitionDto, FieldType } from "#types";
import FieldNameInput from "./PanelFieldSettings";
import NumberFieldSettings from "./fieldTypeSettings/NumberFieldSettings";
import SelectFieldSettings from "./fieldTypeSettings/SelectFieldSettings";
import StatusFieldSettings from "./fieldTypeSettings/StatusFieldSettings";
import DateFieldSettings from "./fieldTypeSettings/DateFieldSettings";
import UrlFieldSettings from "./fieldTypeSettings/UrlFieldSettings";
import BasicFieldSettings from "./fieldTypeSettings/BasicFieldSettings";
import { FieldSettings } from ".";
import { useFieldDefinitions } from "#hooks/useFieldDefinitions";
import { useActiveEntity } from "#hooks/useActiveEntity";


interface PanelExistingFieldSettingsProps {
    fieldDefinition: FieldDefinitionDto;
    initiativeId?: string;
    taskId?: string;
    onBack: () => void;
    onClose: () => void;
    onSubmit: () => void;
};

/**
 * Component for editing existing field definitions
 */
const PanelExistingFieldSettings = ({
    fieldDefinition,
    onBack,
    onClose,
}: PanelExistingFieldSettingsProps) => {
    const { activeInitiativeId, activeTaskId } = useActiveEntity();
    const { updateFieldDefinition, deleteFieldDefinition } = useFieldDefinitions({ initiativeId: activeInitiativeId ?? undefined, taskId: activeTaskId ?? undefined });

    const [editedFieldDefinition, setEditedFieldDefinition] = useState<FieldDefinitionDto>({ ...fieldDefinition });
    const [fieldName, setFieldName] = useState(fieldDefinition.name);
    const [hasChanges, setHasChanges] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        // Check if there are changes compared to the original fieldDefinition
        const nameChanged = fieldName !== fieldDefinition.name;
        const configChanged = JSON.stringify(editedFieldDefinition.config) !== JSON.stringify(fieldDefinition.config);

        setHasChanges(nameChanged || configChanged);
    }, [fieldName, editedFieldDefinition.config, fieldDefinition]);

    const updateFieldSettings = (settings: Partial<FieldSettings>) => {
        setEditedFieldDefinition(prev => ({
            ...prev,
            config: {
                ...prev.config,
                ...settings
            }
        }));
    };

    const handleNameChange = (name: string) => {
        setFieldName(name);
        setEditedFieldDefinition(prev => ({
            ...prev,
            name
        }));
    };

    const handleSubmit = async () => {
        if (!hasChanges) return;

        try {
            setIsSaving(true);
            await updateFieldDefinition(editedFieldDefinition);
        } catch (error) {
            console.error("Failed to update field definition:", error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleDelete = async () => {
        try {
            await deleteFieldDefinition(editedFieldDefinition.id);
            onClose();
        } catch (error) {
            console.error("Failed to delete field definition:", error);
        }
    };

    /**
     * Renders the appropriate settings component based on field type
     */
    const renderFieldSettings = () => {
        if (!editedFieldDefinition.field_type) return null;

        switch (editedFieldDefinition.field_type) {
            case FieldType.NUMBER:
                return <NumberFieldSettings entityType={editedFieldDefinition.entity_type} settings={editedFieldDefinition.config} onUpdate={updateFieldSettings} />;
            case FieldType.SELECT:
            case FieldType.MULTI_SELECT:
                return <SelectFieldSettings entityType={editedFieldDefinition.entity_type} settings={editedFieldDefinition.config} onUpdate={updateFieldSettings} />;
            case FieldType.STATUS:
                return <StatusFieldSettings entityType={editedFieldDefinition.entity_type} settings={editedFieldDefinition.config} onUpdate={updateFieldSettings} />;
            case FieldType.DATE:
                return <DateFieldSettings entityType={editedFieldDefinition.entity_type} settings={editedFieldDefinition.config} onUpdate={updateFieldSettings} />;
            case FieldType.URL:
                return <UrlFieldSettings entityType={editedFieldDefinition.entity_type} settings={editedFieldDefinition.config} onUpdate={updateFieldSettings} />;
            default:
                return <BasicFieldSettings entityType={editedFieldDefinition.entity_type} settings={editedFieldDefinition.config} onUpdate={updateFieldSettings} />;
        }
    };
    return (
        <div>
            <FieldNameInput
                title='Edit Field'
                fieldName={fieldName}
                onNameChange={handleNameChange}
                onBack={onBack}
                onClose={onClose}
                onSubmit={handleSubmit}
                onDelete={handleDelete}
                hasSettings={true}
                submitButtonText={hasChanges ? "Save changes" : "No changes"}
                submitButtonDisabled={!hasChanges}
                isLoading={isSaving}
            >
                {renderFieldSettings()}
            </FieldNameInput>
        </div>
    );
}

export default PanelExistingFieldSettings;
