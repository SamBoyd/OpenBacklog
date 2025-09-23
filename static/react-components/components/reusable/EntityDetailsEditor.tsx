// New file contents for EntityDetailsEditor.tsx
import React, { useEffect, useState, useRef } from 'react';
import { EntityType, statusDisplay } from '#types';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions';
import { UnsetFieldsSection, SetFieldsSection, StatusField, CoreFieldsSection } from '#components/entityField/FieldsDisplayComponents';
import FieldDefinitionsDropdown from '#components/entityField/FieldDefinitionsDropdown';
import { ChevronDown, ChevronUp } from 'lucide-react';

/**
 * Props for the EntityDetailsEditor component
 * @typedef {Object} EntityDetailsEditorProps
 * @property {Record<string, any>} data - The entity data to edit
 * @property {(field: string, value: any) => void} onFieldChange - Callback when a field value changes
 * @property {(field: string, value: string) => void} onAddField - Callback when a new field is added
 * @property {(field: string) => void} onDeleteField - Callback when a field is deleted
 * @property {boolean} loading - Whether the data is loading
 * @property {string FieldDefinitionDto, | null} error - Error message if any
 * @property {Record<string, string[]>} fieldOptions - Options for select fields (e.g. type options)
 */
type EntityDetailsEditorProps = {
    entityType: EntityType;
    data: Record<string, any> | null;
    onFieldChange: (field: string, value: any) => void;
    onPropertyChange: (field_definition_id: string, value: any) => void;
    onAddField: (field: string, value: string) => void;
    onDeleteField: (field: string) => void;
    loading: boolean;
    error: string | null;
    fieldOptions?: Record<string, string[]>;
};

/**
 * A reusable component for editing entity details (Task or Initiative)
 * @param {EntityDetailsEditorProps} props - Component props
 * @returns {React.ReactElement} The EntityDetailsEditor component
 */
const EntityDetailsEditor: React.FC<EntityDetailsEditorProps> = ({
    entityType,
    data,
    onFieldChange,
    onPropertyChange,
    onAddField,
    onDeleteField,
    loading = false,
    error,
    fieldOptions = {},
}) => {
    const [newFieldKey, setNewFieldKey] = useState<string>('');
    const [newFieldValue, setNewFieldValue] = useState<string>('');
    const [showUnsetFields, setShowUnsetFields] = useState<boolean>(false);
    const [initialPropertyKeys, setInitialPropertyKeys] = useState<Set<string>>(new Set());
    const prevDataIdRef = useRef<string | undefined>(undefined);

    const {
        fieldDefinitions,
    } = useFieldDefinitions({
        initiativeId: entityType === EntityType.INITIATIVE ? data?.id : undefined,
        taskId: entityType === EntityType.TASK ? data?.id : undefined
    });

    useEffect(() => {
        // Update initial keys only when data loads initially or the entity ID changes
        if (data && prevDataIdRef.current !== data.id) {
            setInitialPropertyKeys(new Set(Object.keys(data.properties || {})));
            prevDataIdRef.current = data.id;
        } else if (!data && prevDataIdRef.current) {
            // Reset if data becomes null (e.g., navigating away)
            setInitialPropertyKeys(new Set());
            prevDataIdRef.current = undefined;
        }
    }, [data]);

    useEffect(() => {
        handleSave();
    }, [newFieldKey, newFieldValue]);

    const handleSave = () => {
        if (newFieldKey && newFieldValue) {
            onAddField(newFieldKey, newFieldValue);
            setNewFieldKey('');
            setNewFieldValue('');
        }
    };

    const toggleUnsetFields = () => {
        setShowUnsetFields(prev => !prev);
    };

    // Check if there are any unset fields to display the toggle
    const hasUnsetFields = fieldDefinitions?.some(
        (fieldDefinition) => !initialPropertyKeys.has(fieldDefinition.id) && !fieldDefinition.is_core
    );

    return (
        <div id="details" className='relative'>
            {/* Addition dropdown for unset fields */}
            {!error && !loading && (
                <div id="new-field-dropdown" className="absolute right-0 top-0 opacity-60 hover:opacity-100 transition-opacity">
                    <FieldDefinitionsDropdown
                        entityType={entityType}
                        initiativeId={entityType === EntityType.INITIATIVE ? data?.id : undefined}
                        taskId={entityType === EntityType.TASK ? data?.id : undefined}
                    />
                </div>
            )}

            {/* Integrated fields container with all sections */}
            <div className="relative flex flex-row w-full">
                <div className="flex flex-col gap-1.5 text-muted-foreground mr-auto" data-testid="detail-table">
                    <StatusField
                        fieldDefinition={fieldDefinitions.find(fieldDefinition => fieldDefinition.key === 'status')}
                        status={data?.status || ''}
                        onStatusChange={(value) => onFieldChange('status', value)}
                        disabled={loading}
                    />

                    <CoreFieldsSection
                        fieldDefinition={fieldDefinitions.find(fieldDefinition => fieldDefinition.key === 'type')}
                        data={data}
                        onFieldChange={onFieldChange}
                        onDeleteField={onDeleteField}
                    />

                    <SetFieldsSection
                        properties={data?.properties}
                        fieldDefinitions={fieldDefinitions}
                        initialPropertyKeys={initialPropertyKeys}
                        onDeleteField={onDeleteField}
                        onUpdateField={onPropertyChange}
                    />

                    {/* Toggle button for unset fields */}
                    {hasUnsetFields && (
                        <div className="w-full my-1.5">
                            <div
                                className="relative flex items-center justify-center cursor-pointer group"
                                onClick={loading ? undefined : toggleUnsetFields}
                            >
                                <hr className="w-full border-t border-muted" />
                                <div className="absolute px-1.5 bg-background rounded-full border border-muted text-muted-foreground hover:text-foreground transition-colors text-xs">
                                    {showUnsetFields ?
                                        <ChevronUp className="h-3 w-3" /> :
                                        <ChevronDown className="h-3 w-3" />
                                    }
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Unset fields section with animation */}
                    <div
                        className={`overflow-hidden transition-all duration-300 ease-in-out ${showUnsetFields ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
                            }`}
                    >
                        <UnsetFieldsSection
                            fieldDefinitions={fieldDefinitions}
                            properties={data?.properties}
                            initialPropertyKeys={initialPropertyKeys}
                            onDeleteField={onDeleteField}
                            onUpdateField={onPropertyChange}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EntityDetailsEditor;