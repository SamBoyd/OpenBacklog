import React, { useState } from "react";
import { EntityType, FieldDefinitionDto, FieldType } from "#types";
import { Button } from "../reusable/Button";
import {
    NumberFieldSettings,
    SelectFieldSettings,
    StatusFieldSettings,
    DateFieldSettings,
    UrlFieldSettings,
    FieldSettings
} from ".";
import { useFieldDefinitions } from "#hooks/useFieldDefinitions";
import BasicFieldSettings from "./fieldTypeSettings/BasicFieldSettings";
import PanelFieldType from "./PanelFieldType";
import PanelFieldSettings from "./PanelFieldSettings";

/**
 * Props for the FieldDefinitionsDropdown component
 * @interface AddFieldDefinitionProps
 * @property {EntityType} entityType - The type of entity (TASK or INITIATIVE) this field is being added to
 * @property {Function} [onAddField] - Callback function called when a new field is added
 */
interface AddFieldDefinitionProps {
    entityType: EntityType;
    initiativeId?: string;
    taskId?: string;
    disabled?: boolean;
    onAddField?: (fieldDefinition: {
        name: string;
        field_type: FieldType;
        entity_type: EntityType;
        settings?: FieldSettings;
    }) => void;
}

/**
 * Component for adding a new field definition to a task or initiative
 * Displays a button that opens a dropdown panel to select field type and name
 * 
 * @param {object} props - Component props
 * @param {EntityType} props.entityType - The type of entity this field is being added to
 * @param {Function} [props.onAddField] - Callback function called when a new field is added
 * @returns {React.ReactElement} The FieldDefinitionsDropdown component
 */
const FieldDefinitionsDropdown: React.FC<AddFieldDefinitionProps> = ({
    entityType,
    initiativeId,
    taskId,
    disabled = false,
}) => {
    const { fieldDefinitions, createFieldDefinition } = useFieldDefinitions({ initiativeId, taskId });

    const [isOpen, setIsOpen] = useState(false);
    const [selectedFieldType, setSelectedFieldType] = useState<FieldType | null>(null);
    const [selectedFieldDefinition, setSelectedFieldDefinition] = useState<FieldDefinitionDto | null>(null);
    const [fieldName, setFieldName] = useState("");
    const [panel, setPanel] = useState<"type" | "name" | null>(null);
    const [fieldSettings, setFieldSettings] = useState<FieldSettings>({});


    const fieldSettingsToRecord = (fieldSettings: FieldSettings) => {
        return Object.entries(fieldSettings).reduce((acc: Record<string, any>, [key, value]) => {
            acc[key] = value;
            return acc;
        }, {});
    };

    /**
     * Handles the initial button click to open the field type selection panel
     */
    const handleButtonClick = () => {
        setIsOpen(true);
        setPanel("type");
    };

    /**
     * Handles the selection of a field type
     * @param {FieldType} fieldType - The selected field type
     */
    const handleFieldTypeSelect = (fieldType: FieldType) => {
        setSelectedFieldType(fieldType);
        setPanel("name");

        // Initialize default settings based on field type
        const defaultSettings: FieldSettings = {
            aiAutofill: false,
            addToAllInitiatives: false,
        };

        switch (fieldType) {
            case FieldType.NUMBER:
                defaultSettings.numberFormat = 'plain';
                defaultSettings.decimalPlaces = 0;
                defaultSettings.displayAs = 'number';
                break;
            case FieldType.SELECT:
                defaultSettings.isMultiSelect = false;
                defaultSettings.sortType = 'manual';
                defaultSettings.aiAutofill = false;
                defaultSettings.options = [];
                break;
            case FieldType.MULTI_SELECT:
                defaultSettings.isMultiSelect = true;
                defaultSettings.sortType = 'manual';
                defaultSettings.aiAutofill = false;
                defaultSettings.options = [];
                break;
            case FieldType.STATUS:
                defaultSettings.statusOptions = [];
                defaultSettings.sortType = 'manual';
                break;
            case FieldType.DATE:
                defaultSettings.dateFormat = 'MM/DD/YYYY';
                defaultSettings.timeFormat = '12h';
                break;
            case FieldType.URL:
                defaultSettings.showFullUrl = true;
                break;
        }

        setFieldSettings(defaultSettings);
    };


    const checkIfFieldKeyExists = (key: string) => {
        return fieldDefinitions.some(fieldDefinition => fieldDefinition.key === key);
    };
    /**
     * Handles the final submission with all field data
     */
    const handleSubmit = () => {
        if (selectedFieldType) {
            // If selected type was SELECT but isMultiSelect is true, change to MULTI_SELECT
            let finalFieldType = selectedFieldType;
            if (selectedFieldType === FieldType.SELECT && fieldSettings.isMultiSelect) {
                finalFieldType = FieldType.MULTI_SELECT;
            } else if (selectedFieldType === FieldType.MULTI_SELECT && !fieldSettings.isMultiSelect) {
                finalFieldType = FieldType.SELECT;
            }

            let fieldKey = fieldName.trim().replace(/\s+/g, '_').toLowerCase();
            let i = 0;
            while (checkIfFieldKeyExists(fieldKey)) {
                fieldKey = `${fieldKey}_${i}`;
                i++;
            }

            createFieldDefinition({
                key: fieldKey,
                name: fieldName.trim(),
                field_type: finalFieldType,
                entity_type: entityType,
                initiative_id: fieldSettings.addToAllInitiatives ? undefined : initiativeId,
                task_id: fieldSettings.addToAllTasks ? undefined : taskId,
                config: hasSettings(selectedFieldType) ? fieldSettingsToRecord(fieldSettings) : {},
            });
            handleClose();
        } else {
            console.error("No field type selected");
        }
    };

    /**
     * Determines if a field type has customizable settings
     */
    const hasSettings = (fieldType: FieldType): boolean => {
        return true;
    };

    /**
     * Update settings for a field
     */
    const updateFieldSettings = (settingUpdate: Partial<FieldSettings>) => {
        setFieldSettings((prev: FieldSettings) => ({
            ...prev,
            ...settingUpdate
        }));
    };

    /**
     * Closes the dropdown panel and resets all states
     */
    const handleClose = () => {
        setIsOpen(false);
        setSelectedFieldType(null);
        setFieldName("");
        setPanel(null);
        setFieldSettings({});
    };

    /**
     * Renders the appropriate settings component based on field type
     */
    const renderFieldSettings = () => {
        if (!selectedFieldType) return null;

        switch (selectedFieldType) {
            case FieldType.NUMBER:
                return <NumberFieldSettings entityType={entityType} settings={fieldSettings} onUpdate={updateFieldSettings} />;
            case FieldType.SELECT:
            case FieldType.MULTI_SELECT:
                return <SelectFieldSettings entityType={entityType} settings={fieldSettings} onUpdate={updateFieldSettings} />;
            case FieldType.STATUS:
                return <StatusFieldSettings entityType={entityType} settings={fieldSettings} onUpdate={updateFieldSettings} />;
            case FieldType.DATE:
                return <DateFieldSettings entityType={entityType} settings={fieldSettings} onUpdate={updateFieldSettings} />;
            case FieldType.URL:
                return <UrlFieldSettings entityType={entityType} settings={fieldSettings} onUpdate={updateFieldSettings} />;
            default:
                return <BasicFieldSettings entityType={entityType} settings={fieldSettings} onUpdate={updateFieldSettings} />;
        }
    };

    return (
        <div className="relative z-10">
            <Button onClick={handleButtonClick} disabled={disabled}>
                <svg role="presentation" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-6">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
            </Button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-0"
                        onClick={handleClose}
                    />
                    <div className="absolute -left-64 w-72 flex z-10 mt-1 bg-background text-foreground border border-border rounded-md">
                        {panel === "type" && (
                            <PanelFieldType
                                onSelectFieldType={handleFieldTypeSelect}
                            />
                        )}

                        {panel === "name" && (
                            <PanelFieldSettings
                                title={`New ${selectedFieldType?.toLowerCase()} field`}
                                fieldName={fieldName}
                                onNameChange={setFieldName}
                                onBack={() => setPanel("type")}
                                onClose={handleClose}
                                onSubmit={handleSubmit}
                                hasSettings={selectedFieldType ? hasSettings(selectedFieldType) : false}
                            >
                                {renderFieldSettings()}
                            </PanelFieldSettings>
                        )}
                    </div>

                </>
            )}
        </div>
    );
};

export default FieldDefinitionsDropdown;