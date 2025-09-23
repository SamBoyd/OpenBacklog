import React from 'react';
import { FieldDefinitionDto, FieldType, InitiativeStatus, statusDisplay } from '#types';
import { CheckboxInput, Input } from '#components/reusable/Input';
import { SelectBox } from '#components/reusable/Selectbox';

type RenderFieldInputProps = {
    fieldDef: FieldDefinitionDto;
    selectedCriteria: Record<string, any>;
    handleCriteriaChange: (fieldKey: string, value: any) => void;
};

/**
 * Renders the appropriate input control based on the field definition's type.
 * @param {RenderFieldInputProps} props - The properties for rendering the field input.
 * @param {FieldDefinitionDto} props.fieldDef - The definition of the field.
 * @param {Record<string, any>} props.selectedCriteria - The currently selected criteria values.
 * @param {(fieldKey: string, value: any) => void} props.handleCriteriaChange - Callback for when the criteria value changes.
 * @returns {React.ReactElement} The input control for the field.
 */
export const renderFieldInput = ({ fieldDef, selectedCriteria, handleCriteriaChange }: RenderFieldInputProps): React.ReactElement => {
    const commonProps = {
        id: `criteria-${fieldDef.key}`,
        className: "w-full p-2 border rounded bg-input text-foreground",
    };

    const onChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
        handleCriteriaChange(fieldDef.key, e.target.value);

    switch (fieldDef.field_type) {
        case FieldType.TEXT:
        case FieldType.EMAIL:
        case FieldType.URL:
        case FieldType.PHONE:
            return <Input type="text" {...commonProps} value={selectedCriteria[fieldDef.key] || ''} onChange={onChange} />;
        case FieldType.NUMBER:
            return <Input type="number" {...commonProps} value={selectedCriteria[fieldDef.key] || ''} onChange={onChange} />;
        case FieldType.SELECT:
            const options = fieldDef.key === 'status' ? Object.values(InitiativeStatus) : (fieldDef.config?.options as string[] || []);
            return (
                <SelectBox
                    {...commonProps}
                    value={selectedCriteria[fieldDef.key] || ''}
                    options={options.map(opt => ({ label: fieldDef.key === 'status' ? statusDisplay(opt) : opt, value: opt }))}
                    onChange={(value: string) => handleCriteriaChange(fieldDef.key, value)}
                />
            );
        case FieldType.MULTI_SELECT:
            return (
                <select multiple {...commonProps}
                    value={selectedCriteria[fieldDef.key] || []}
                    onChange={(e) => {
                        const values = Array.from(e.target.selectedOptions, option => option.value);
                        handleCriteriaChange(fieldDef.key, values);
                    }}
                >
                    {(fieldDef.config?.options as string[] || []).map((opt, index) => (
                        <option key={`option-${opt}-${index}`} value={opt}>{opt}</option>
                    ))}
                </select>
            );
        case FieldType.DATE:
            return <Input type="date" {...commonProps} value={selectedCriteria[fieldDef.key] || ''} onChange={onChange} />;
        case FieldType.CHECKBOX:
            return (
                <CheckboxInput
                    id={`criteria-${fieldDef.key}`}
                    className="p-2 h-6 w-6 border rounded bg-input text-foreground" // Adjusted size
                    checked={selectedCriteria[fieldDef.key]}
                    onChange={(e) => handleCriteriaChange(fieldDef.key, e.target.checked)}
                />
            );
        default:
            return <p className="text-sm text-muted-foreground">Unsupported field type: {fieldDef.field_type}</p>;
    }
}; 