import React, { useEffect, useState } from 'react';
import { EntityType, FieldDefinitionDto, FieldType, statusDisplay } from '#types';
import { GrStatusPlaceholder, GrTerminal } from 'react-icons/gr';
import { DateInput, Input, NumberInput, CheckboxInput } from '../reusable/Input';
import { SelectBox } from '../reusable/Selectbox';
import dayjs from 'dayjs';
import { Phone, Mail, Link2, CheckSquare, Calendar, CheckCircle, ListChecks, Hash, Settings, Type, Tag } from 'lucide-react';
import PanelExistingFieldSettings from './PanelExistingFieldSettings';

/**
 * Returns the icon for a given field type
 * @param {FieldType} fieldType - The field type to get the icon for
 * @returns {React.ReactNode} The icon for the field type
 */
const getIconForField = (fieldType: FieldType) => {
    switch (fieldType) {
        case FieldType.TEXT:
            return <Type size={16} />;
        case FieldType.NUMBER:
            return <Hash size={16} />;
        case FieldType.SELECT:
            return <Tag size={16} />;
        case FieldType.MULTI_SELECT:
            return <ListChecks size={16} />;
        case FieldType.STATUS:
            return <CheckCircle size={16} />;
        case FieldType.DATE:
            return <Calendar size={16} />;
        case FieldType.CHECKBOX:
            return <CheckSquare size={16} />;
        case FieldType.URL:
            return <Link2 size={16} />;
        case FieldType.EMAIL:
            return <Mail size={16} />;
        case FieldType.PHONE:
            return <Phone size={16} />;
    }
};

/**
 * Gets the display value for a field type
 */
const getDisplayValue = (fieldType: FieldType, value: any): string => {
    switch (fieldType) {
        case FieldType.TEXT:
        case FieldType.URL:
        case FieldType.EMAIL:
        case FieldType.PHONE:
            return value as string;
        case FieldType.NUMBER:
            return (value as number)?.toString() || '';
        case FieldType.SELECT:
            return (value as string) || '';
        case FieldType.STATUS:
            return statusDisplay(value as string) || '';
        case FieldType.DATE:
            return value ? dayjs(value as string).format("DD-MM-YYYY") : '';
        default:
            return '';
    }
};

/**
 * Returns the appropriate input component for a given field type
 */
const getInputComponentForFieldType = (
    type: FieldType,
    value: any,
    onChange: (value: any) => void,
    options?: string[],
    onBlur?: () => void,
    updateDontSave?: (value: any) => void,
): JSX.Element => {
    switch (type) {
        case FieldType.TEXT:
            return <Input type="text" value={value} onChange={(e) => updateDontSave?.(e.target.value)} onBlur={onBlur} />;
        case FieldType.NUMBER:
            return <NumberInput value={value} onChange={(e) => onChange(e.target.value)} />;
        case FieldType.SELECT:
        case FieldType.MULTI_SELECT:
        case FieldType.STATUS:
            const selectOptions = options?.map((option: string) => ({
                value: option,
                label: option,
            })) || [{ value: '', label: '' }];
            return <SelectBox value={value || ''} onChange={onChange} options={selectOptions} variant="subtle" />;
        case FieldType.CHECKBOX:
            return <CheckboxInput checked={!!value} onChange={(e) => onChange(e.target.checked)} />;
        case FieldType.URL:
            return <Input type="url" value={value} onChange={(e) => updateDontSave?.(e.target.value)} onBlur={onBlur} />;
        case FieldType.DATE:
            return <DateInput value={value} onChange={(e) => updateDontSave?.(e.target.value)} onBlur={onBlur} />;
        case FieldType.EMAIL:
            return <Input type="email" value={value} onChange={(e) => updateDontSave?.(e.target.value)} onBlur={onBlur} />;
        case FieldType.PHONE:
            return <Input type="tel" value={value} onChange={(e) => updateDontSave?.(e.target.value)} onBlur={onBlur} />;
        default:
            return <></>;
    }
};

/**
 * Component to display set fields from properties
 */
type SetFieldsSectionProps = {
    properties: Record<string, any> | undefined;
    fieldDefinitions: FieldDefinitionDto[];
    initialPropertyKeys: Set<string>;
    onDeleteField: (field: string) => void;
    onUpdateField: (field_definition_id: string, value: any) => void;
};

export const SetFieldsSection: React.FC<SetFieldsSectionProps> = ({ properties, fieldDefinitions, initialPropertyKeys, onDeleteField, onUpdateField }) => {
    const [hoveredField, setHoveredField] = useState<string | null>(null);
    const [showSettings, setShowSettings] = useState<FieldDefinitionDto | null>(null);

    const onFieldChange = (field_definition_id: string, value: any): void => {
        onUpdateField(field_definition_id, value);
    }

    const settingsIcon = <Settings size={16} />;

    // Filter based on initialPropertyKeys
    const setFieldDefinitions = fieldDefinitions.filter(fd => initialPropertyKeys.has(fd.id));

    return (
        <>
            {showSettings && (
                <>
                    <div className='absolute inset-0 z-20' onClick={() => setShowSettings(null)}> </div>
                    <div className="absolute right-0 top-10 z-30">
                        <PanelExistingFieldSettings
                            fieldDefinition={showSettings}
                            onBack={() => setShowSettings(null)}
                            onClose={() => setShowSettings(null)}
                            onSubmit={() => setShowSettings(null)}
                        />
                    </div>
                </>
            )}

            {setFieldDefinitions.map((fieldDefinition) => {
                const id = fieldDefinition.id;
                const value = properties ? properties[id] : undefined;

                const fieldType = fieldDefinition.field_type;
                let displayValue: string = '';
                let inputComponent = <></>;

                displayValue = getDisplayValue(fieldType, value);
                inputComponent = getInputComponentForFieldType(fieldType, value, (val) => onFieldChange(id, val), fieldDefinition.config.options);

                return (
                    <div
                        className="flex flex-row w-full justify-start items-center space-x-4 hover:bg-muted/5 transition-colors duration-200"
                        key={id}
                        onMouseEnter={() => setHoveredField(id)}
                        onMouseLeave={() => setHoveredField(null)}
                    >
                        <div
                            className="flex flex-row gap-2 min-w-[13rem] font-light cursor-pointer text-muted-foreground"
                            onClick={() => setShowSettings(fieldDefinition)}
                        >
                            <div className="relative w-4 h-4">
                                <div className={`absolute inset-0 transform transition-all duration-300 ${hoveredField === id ? 'rotate-y-180 opacity-0' : 'rotate-y-0 opacity-100'}`}>
                                    {getIconForField(fieldDefinition.field_type)}
                                </div>
                                <div className={`absolute inset-0 transform transition-all duration-300 ${hoveredField === id ? 'rotate-y-0 opacity-100' : 'rotate-y-180 opacity-0'}`}>
                                    {settingsIcon}
                                </div>
                            </div>
                            <span className="ml-2.5">{fieldDefinition.name}</span>
                        </div>
                        <div className="w-full">
                            {inputComponent}
                        </div>
                    </div>
                );
            })}
        </>
    );
};

/**
 * Component to display unset fields
 */
type UnsetFieldsSectionProps = {
    fieldDefinitions: FieldDefinitionDto[];
    properties: Record<string, any> | undefined;
    initialPropertyKeys: Set<string>;
    onDeleteField: (field: string) => void;
    onUpdateField: (field_definition_id: string, value: any) => void;
};

export const UnsetFieldsSection: React.FC<UnsetFieldsSectionProps> = ({ fieldDefinitions, properties, initialPropertyKeys, onDeleteField, onUpdateField }) => {
    const [hoveredField, setHoveredField] = useState<string | null>(null);
    const [showSettings, setShowSettings] = useState<FieldDefinitionDto | null>(null);
    const [localProperties, setLocalProperties] = useState<Record<string, any> | undefined>(properties);

    useEffect(() => {
        setLocalProperties(properties);
    }, [properties]);

    const unsetFields = fieldDefinitions.filter((fieldDefinition) =>
        !initialPropertyKeys.has(fieldDefinition.id) && !fieldDefinition.is_core
    );

    if (unsetFields.length === 0) return null;

    const onFieldChange = (field_definition_id: string, value: any): void => {
        onUpdateField(field_definition_id, value);
    }


    const updateLocalProperty = (index: number) => (value: string) => {
        const newProperties = { ...localProperties };
        newProperties[index] = value;
        setLocalProperties(newProperties);
    }

    const saveLocalProperty = (index: number) => () => {
        onUpdateField(fieldDefinitions[index].id, localProperties?.[index] || '');
    }

    const settingsIcon = <Settings size={16} />;

    return (
        <div className=''>
            <span className='text-muted-foreground text-xs'>Unset fields</span>

            {showSettings && (
                <>
                    <div className='absolute inset-0 z-20' onClick={() => setShowSettings(null)}> </div>
                    <div className="absolute top-10 right-0 z-30">
                        <PanelExistingFieldSettings
                            fieldDefinition={showSettings}
                            onBack={() => setShowSettings(null)}
                            onClose={() => setShowSettings(null)}
                            onSubmit={() => setShowSettings(null)}
                        />
                    </div>
                </>
            )}

            {unsetFields.map((fieldDefinition, index) => {
                const id = fieldDefinition.id;
                const value = localProperties ? localProperties[index] : undefined;
                const fieldType = fieldDefinition.field_type;
                let inputComponent = <></>;

                inputComponent = getInputComponentForFieldType(
                    fieldType,
                    value || '',
                    (val) => onFieldChange(id, val),
                    fieldDefinition.config.options,
                    saveLocalProperty(index),
                    updateLocalProperty(index),
                );

                return (
                    <div
                        className="flex flex-row w-full justify-start items-center space-x-4 hover:bg-muted/5 transition-colors duration-200"
                        key={fieldDefinition.id}
                        onMouseEnter={() => setHoveredField(id)}
                        onMouseLeave={() => setHoveredField(null)}
                    >
                        <div
                            className="flex flex-row gap-2 min-w-[13rem] font-light cursor-pointer text-muted-foreground"
                            onClick={() => setShowSettings(fieldDefinition)}
                        >
                            <div className="relative w-4 h-4">
                                <div className={`absolute inset-0 transform transition-all duration-300 ${hoveredField === id ? 'rotate-y-180 opacity-0' : 'rotate-y-0 opacity-100'}`}>
                                    {getIconForField(fieldDefinition.field_type)}
                                </div>
                                <div className={`absolute inset-0 transform transition-all duration-300 ${hoveredField === id ? 'rotate-y-0 opacity-100' : 'rotate-y-180 opacity-0'}`}>
                                    {settingsIcon}
                                </div>
                            </div>
                            <span className="ml-2.5">{fieldDefinition.name}</span>
                        </div>
                        <div className="w-full">
                            {inputComponent}
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

/**
 * Component to display existing/core fields
 */
export type CoreFieldsSectionProps = {
    fieldDefinition?: FieldDefinitionDto;
    data: Record<string, any> | null;
    onFieldChange: (field: string, value: any) => void;
    onDeleteField: (field: string) => void;
};

export const CoreFieldsSection: React.FC<CoreFieldsSectionProps> = ({ fieldDefinition, data, onFieldChange, onDeleteField }) => {
    if (!data) return null;
    if (!fieldDefinition) return null;

    const typeOptions = fieldDefinition.config.options?.map((option: string) => ({
        value: option,
        label: option,
    })) || [];

    return (
        <div className="flex flex-row w-full justify-start items-center space-x-4">
            <div className="flex flex-row gap-2 min-w-[13rem] font-light text-muted-foreground">
                {getIconForField(fieldDefinition.field_type)}
                <span className="ml-2.5">{fieldDefinition.name}</span>
            </div>
            <div className="w-full">
                <SelectBox
                    value={data[fieldDefinition.column_name || ''] || ''}
                    onChange={value => onFieldChange(fieldDefinition.column_name || '', value)}
                    options={typeOptions}
                    variant="subtle"
                />
            </div>
        </div>
    );
};

/**
 * Component for the status field which is shown at the top
 */
export type StatusFieldProps = {
    fieldDefinition?: FieldDefinitionDto;
    status: string;
    disabled?: boolean;
    onStatusChange: (value: string) => void;
};

export const StatusField: React.FC<StatusFieldProps> = ({ fieldDefinition, status, onStatusChange, disabled = false }) => {
    if (!fieldDefinition) return null;

    const statusOptions = fieldDefinition.config.options.map((option: string) => ({
        value: option,
        label: option,
    }));

    return (
        <div className="flex flex-row gap-4 w-full justify-start items-center" data-testid="status-select">
            <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light text-muted-foreground">
                <GrStatusPlaceholder />
                <span className="ml-2.5">Status</span>
            </div>
            <div className="w-full">
                <SelectBox
                    value={status}
                    onChange={onStatusChange}
                    disabled={disabled}
                    className=""
                    data-testid="status-select"
                    options={statusOptions}
                    variant="subtle"
                />
            </div>
            <div className="flex flex-row gap-2 min-w-[13rem]">
                {/* Space for alignment with the inputs below */}
            </div>
        </div>
    );
};
