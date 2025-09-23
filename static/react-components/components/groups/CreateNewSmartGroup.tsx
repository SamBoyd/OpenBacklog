import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
    GroupDto,
    FieldDefinitionDto,
    FieldType,
    EntityType,
    InitiativeDto,
    GroupType,
    InitiativeStatus,
    statusDisplay
} from '#types';
import { Button, NoBorderButton, PrimaryButton, SecondaryButton } from '#components/reusable/Button';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { Input } from '#components/reusable/Input';
import ResizingTextInput from '#components/reusable/ResizingTextInput';
import { ArrowLeft } from 'lucide-react';
import SmartGroupQueryCriteria from './SmartGroupQueryCriteria';
import SmartGroupPreview from './SmartGroupPreview';

// Mock current user and workspace for creating groups - replace with actual data source if available
const MOCK_USER_ID = 'mock-user-id-123';
const MOCK_WORKSPACE_ID = 'mock-workspace-id-456';

type CreateNewSmartGroupProps = {
    onClose: () => void;
    onGroupChanged: (group: Partial<GroupDto>) => void;
};

/**
 * A dialog component for creating a new smart group.
 * It allows users to specify a name, description, and query criteria based on field definitions,
 * and previews matching initiatives.
 */
const CreateNewSmartGroup: React.FC<CreateNewSmartGroupProps> = ({
    onClose,
    onGroupChanged,
}) => {
    const { fieldDefinitions: allFieldDefinitions,  loading: fieldDefsLoading, error: fieldDefsError  } = useFieldDefinitions({});
    const [groupName, setGroupName] = useState('');
    const [groupDescription, setGroupDescription] = useState('');
    const [selectedCriteria, setSelectedCriteria] = useState<Record<string, any>>({});
    const [debouncedCriteria, setDebouncedCriteria] = useState<Record<string, any>>({});
    const [activeCriteriaFields, setActiveCriteriaFields] = useState<FieldDefinitionDto[]>([]);
    const [filteredPreviewInitiatives, setFilteredPreviewInitiatives] = useState<InitiativeDto[] | undefined>(undefined);
    const [keywords, setKeywords] = useState('');

    const prevGroupNameRef = useRef(groupName);
    const prevGroupDescriptionRef = useRef(groupDescription);
    const prevSelectedCriteriaRef = useRef(selectedCriteria);

    const filteredFieldDefinitions = useMemo(() => {
        return allFieldDefinitions.filter(fd => fd.entity_type === EntityType.INITIATIVE);
    }, [allFieldDefinitions]);

    // Debounce selectedCriteria for fetching preview
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedCriteria(selectedCriteria);
        }, 500);

        return () => {
            clearTimeout(handler);
        };
    }, [selectedCriteria]);


    useEffect(() => {
        const groupNameChanged = groupName !== prevGroupNameRef.current;
        const groupDescriptionChanged = groupDescription !== prevGroupDescriptionRef.current;
        const selectedCriteriaChanged = selectedCriteria !== prevSelectedCriteriaRef.current; // Simplified comparison for objects, consider deep equality if needed

        if (groupNameChanged || groupDescriptionChanged || selectedCriteriaChanged) {
            onGroupChanged({
                name: groupName,
                description: groupDescription,
                query_criteria: selectedCriteria,
            });
        }

        prevGroupNameRef.current = groupName;
        prevGroupDescriptionRef.current = groupDescription;
        prevSelectedCriteriaRef.current = selectedCriteria;
    }, [groupName, groupDescription, selectedCriteria, onGroupChanged]);

    // TODO: useInitiativesContext hook needs to accept a generic filter object (Record<string, any>) for its first argument.
    // The current InitiativeFilters is { id?: string; status?: string[] }.
    // This will require changes in useInitiativesContext and potentially the getAllInitiatives API.
    const { initiativesData: previewInitiatives, shouldShowSkeleton: previewLoading, error: previewError } = useInitiativesContext();

    useEffect(() => {
        if (!previewInitiatives) {
            setFilteredPreviewInitiatives(undefined);
            return;
        }

        const lowerCaseKeywords = keywords.trim().toLowerCase().split(' ').filter(k => k);

        if (Object.keys(debouncedCriteria).length === 0 && lowerCaseKeywords.length === 0) {
            setFilteredPreviewInitiatives(previewInitiatives);
            return;
        }

        // If criteria exist but no field definitions are loaded (e.g., during initial load or error),
        // treat as no matches, as criteria cannot be interpreted.
        // Similarly, if keywords are present but there are no initiatives to filter, it's an empty result.
        if ((filteredFieldDefinitions.length === 0 && Object.keys(debouncedCriteria).length > 0) || (lowerCaseKeywords.length > 0 && previewInitiatives.length === 0)) {
            setFilteredPreviewInitiatives([]);
            return;
        }

        const filteredByKeywordsAndCriteria = previewInitiatives.filter(initiative => {
            // Keyword Search (Title and Description)
            let matchesKeywords = true;
            if (lowerCaseKeywords.length > 0) {
                const titleMatch = lowerCaseKeywords.every(kw => initiative.title?.toLowerCase().includes(kw));
                const descriptionMatch = lowerCaseKeywords.every(kw => initiative.description?.toLowerCase().includes(kw));
                matchesKeywords = titleMatch || descriptionMatch;
            }
            if (!matchesKeywords) return false;

            // Existing Criteria Search
            if (Object.keys(debouncedCriteria).length === 0) return true; // No criteria to check, keyword match is enough

            return Object.entries(debouncedCriteria).every(([fieldKey, criterionValue]) => {
                // If criterionValue is empty, it doesn't restrict this initiative for this field.
                if (criterionValue === undefined || criterionValue === null || criterionValue === '' || (Array.isArray(criterionValue) && criterionValue.length === 0)) {
                    return true;
                }

                const fieldDef = filteredFieldDefinitions.find(fd => fd.key === fieldKey);
                // If field definition not found for a criterion key, this criterion cannot be evaluated.
                // Treat as non-match if a value is expected by the criterion.
                if (!fieldDef) return false;

                let initiativeValue: any;

                // Standard, directly accessible InitiativeDto properties
                if (fieldKey === 'status') {
                    initiativeValue = initiative.status;
                } else if (fieldKey === 'type') {
                    initiativeValue = initiative.type;
                } else if (fieldKey === 'title') {
                    initiativeValue = initiative.title;
                } else if (fieldKey === 'identifier') {
                    initiativeValue = initiative.identifier;
                } else if (initiative.properties && initiative.properties.hasOwnProperty(fieldDef.id)) {
                    // Custom fields accessed by fieldDef.id
                    initiativeValue = initiative.properties[fieldDef.id];
                } else {
                    // Field not found on initiative (neither standard known nor in custom_fields)
                    // Since criterionValue is not empty, this is a non-match.
                    return false;
                }

                // If initiative has no value for the field, but criterion expects one.
                if (initiativeValue === undefined || initiativeValue === null) {
                    return false;
                }

                // "Crude" comparison logic
                switch (fieldDef.field_type) {
                    case FieldType.MULTI_SELECT:
                        const filterValues = (Array.isArray(criterionValue) ? criterionValue : [criterionValue]).map(v => String(v).toLowerCase());
                        const actualValues = (Array.isArray(initiativeValue) ? initiativeValue : [initiativeValue]).map(v => String(v).toLowerCase());
                        return filterValues.some(fv => actualValues.includes(fv));
                    case FieldType.CHECKBOX:
                        // Ensure boolean comparison handles string "true"/"false" or actual booleans
                        const critBool = typeof criterionValue === 'string' ? criterionValue.toLowerCase() === 'true' : Boolean(criterionValue);
                        const initBool = typeof initiativeValue === 'string' ? initiativeValue.toLowerCase() === 'true' : Boolean(initiativeValue);
                        return initBool === critBool;
                    default:
                        return String(initiativeValue).toLowerCase().includes(String(criterionValue).toLowerCase());
                }
            });
        });
        setFilteredPreviewInitiatives(filteredByKeywordsAndCriteria);
    }, [previewInitiatives, debouncedCriteria, filteredFieldDefinitions, keywords]);

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

    return (
        <div className="p-2 bg-background text-foreground rounded-lg shadow max-w-md mx-auto flex flex-col h-full">
            <div className="space-y-2 mb-4 flex-grow pr-1">
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
                allFieldDefinitions={filteredFieldDefinitions}
                activeCriteriaFields={activeCriteriaFields}
                selectedCriteria={selectedCriteria}
                onAddField={handleAddFieldToCriteria}
                onRemoveField={handleRemoveFieldFromCriteria}
                onCriteriaChange={handleCriteriaChange}
                fieldDefsLoading={fieldDefsLoading}
                fieldDefsError={fieldDefsError}
                entityTypeForCriteria="Initiative" // Example, make dynamic if needed
            />

            <SmartGroupPreview
                filteredPreviewInitiatives={filteredPreviewInitiatives}
                previewLoading={previewLoading}
                previewError={previewError}
                debouncedCriteria={debouncedCriteria}
                keywords={keywords}
                previewInitiatives={previewInitiatives === null ? undefined : previewInitiatives}
            />
        </div>
    );
};

export default CreateNewSmartGroup;

