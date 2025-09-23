import React from 'react';
import { FieldDefinitionDto } from '#types';
import AddCriteriaButton from './AddCriteriaButton';
import { NoBorderButton } from '#components/reusable/Button';
import { renderFieldInput } from './renderFieldInput';

type SmartGroupQueryCriteriaProps = {
    allFieldDefinitions: FieldDefinitionDto[];
    activeCriteriaFields: FieldDefinitionDto[];
    selectedCriteria: Record<string, any>;
    onAddField: (field: FieldDefinitionDto) => void;
    onRemoveField: (fieldKey: string) => void;
    onCriteriaChange: (fieldKey: string, value: any) => void;
    fieldDefsLoading: boolean;
    fieldDefsError: string | null;
    entityTypeForCriteria: string; // e.g. "Initiative"
};

/**
 * Component for managing and displaying query criteria for a smart group.
 * It allows adding, removing, and editing criteria based on available field definitions.
 */
const SmartGroupQueryCriteria: React.FC<SmartGroupQueryCriteriaProps> = ({
    allFieldDefinitions,
    activeCriteriaFields,
    selectedCriteria,
    onAddField,
    onRemoveField,
    onCriteriaChange,
    fieldDefsLoading,
    fieldDefsError,
    entityTypeForCriteria
}) => {
    return (
        <div className="mb-4">
            <h3 className="font-semibold mb-2 text-base">Query Criteria</h3>
            {fieldDefsLoading && <p className="text-xs">Loading field definitions...</p>}
            {fieldDefsError && <p className="text-red-500 text-xs">Error loading field definitions</p>}

            {!fieldDefsLoading && !fieldDefsError && allFieldDefinitions.length === 0 && (
                <p className="text-xs text-muted-foreground">No {entityTypeForCriteria.toLowerCase()} field definitions found to build criteria.</p>
            )}

            <div className="space-y-2">
                {activeCriteriaFields.map(fieldDef => (
                    <div key={fieldDef.id} className="col-span-2 flex items-center space-x-1">
                        <label htmlFor={`criteria-${fieldDef.key}`} className="font-medium text-xs col-span-1 truncate" title={fieldDef.name}>
                            {fieldDef.name}
                        </label>
                        <div className="flex-grow">
                            {renderFieldInput({ fieldDef, selectedCriteria, handleCriteriaChange: onCriteriaChange })}
                        </div>
                        <NoBorderButton
                            onClick={() => onRemoveField(fieldDef.key)}
                            className="p-0.5 text-muted-foreground hover:text-foreground"
                            title={`Remove ${fieldDef.name} criterion`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </NoBorderButton>
                    </div>
                ))}
            </div>
            {!fieldDefsLoading && !fieldDefsError && allFieldDefinitions.length > 0 && (
                <div className="mt-2">
                    <AddCriteriaButton
                        allFieldDefinitions={allFieldDefinitions}
                        activeFieldKeys={activeCriteriaFields.map(f => f.key)}
                        onAddField={onAddField}
                    />
                </div>
            )}
        </div>
    );
};

export default SmartGroupQueryCriteria; 