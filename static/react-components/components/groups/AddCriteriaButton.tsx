import React from 'react';
import { FieldDefinitionDto } from '#types';
import { SelectBox } from '#components/reusable/Selectbox'; // Import SelectBox

type AddCriteriaButtonProps = {
    allFieldDefinitions: FieldDefinitionDto[];
    activeFieldKeys: string[];
    onAddField: (field: FieldDefinitionDto) => void;
};

const AddCriteriaButton: React.FC<AddCriteriaButtonProps> = ({
    allFieldDefinitions,
    activeFieldKeys,
    onAddField
}) => {
    const availableFields = allFieldDefinitions.filter(
        field => !activeFieldKeys.includes(field.key)
    );

    if (availableFields.length === 0) {
        return null; // Don't render if no fields can be added
    }

    const selectOptions = availableFields.map(field => ({
        value: field.key,
        label: field.name
    }));

    const handleSelectField = (selectedValue: string) => {
        // selectedValue is field.key
        const fieldToAdd = allFieldDefinitions.find(f => f.key === selectedValue);
        if (fieldToAdd) {
            onAddField(fieldToAdd);
        }
        // SelectBox handles its own open/close state
    };

    return (
        // The SelectBox component has its own relative positioning for the dropdown
        <SelectBox
            options={selectOptions}
            onChange={handleSelectField}
            placeholder="+ Add Criteria Field"
            // Pass undefined or an empty string for value to always show placeholder,
            // as selection triggers an add action rather than setting a persistent state here.
            value={undefined}
            className="w-full h-full" // Make it full width or adjust as needed
        />
    );
};

export default AddCriteriaButton; 